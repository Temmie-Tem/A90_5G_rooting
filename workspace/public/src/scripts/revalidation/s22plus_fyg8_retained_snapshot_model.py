#!/usr/bin/env python3
"""Model the exact FYG8 Samsung retained-log snapshot contract host-only.

This tool reproduces the source-matched ``sec_log_buf`` preparation and
``/proc/last_kmsg`` snapshot algorithm.  It has no device transport, image
builder, or live-run authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA = "s22plus_fyg8_retained_snapshot_model_v1"
VERDICT = "PASS_S22PLUS_FYG8_RETAINED_SNAPSHOT_MODEL_HOST_ONLY"
ROOT = Path(__file__).resolve().parents[5]

LOG_REGION_SIZE = 0x200000
HEADER_SIZE = 16
PAYLOAD_SIZE = LOG_REGION_SIZE - HEADER_SIZE
LOG_MAGIC = 0x4D474F4C
UINT32_MAX = 0xFFFFFFFF

DEFAULT_MAIN_SOURCE = ROOT / (
    "workspace/private/work/s22plus_fyg8_kernel_rebuild_r0/"
    "kernel_platform/msm-kernel/drivers/samsung/debug/log_buf/"
    "sec_log_buf_main.c"
)
DEFAULT_LAST_KMSG_SOURCE = ROOT / (
    "workspace/private/work/s22plus_fyg8_kernel_rebuild_r0/"
    "kernel_platform/msm-kernel/drivers/samsung/debug/log_buf/"
    "sec_log_buf_last_kmsg.c"
)

SOURCE_PINS = {
    "main": "296f4fc175d958feb35b92c8736faf6361ade2e7c447d9a9af5a93f59bdb97b8",
    "last_kmsg": "ba9e0f9f0832cbf666e55b51804515fc8298203fd37958ccdfb6bfbbe3524443",
}


class ModelError(ValueError):
    pass


@dataclass(frozen=True)
class Header:
    boot_cnt: int
    magic: int
    idx: int
    prev_idx: int


@dataclass(frozen=True)
class Snapshot:
    data: bytes
    branch: str
    prepared_header: Header


def _require_u32(value: int, label: str) -> int:
    if not isinstance(value, int) or value < 0 or value > UINT32_MAX:
        raise ModelError(f"{label} is not a u32: {value!r}")
    return value


def validate_header(header: Header) -> Header:
    _require_u32(header.boot_cnt, "boot_cnt")
    _require_u32(header.magic, "magic")
    _require_u32(header.idx, "idx")
    _require_u32(header.prev_idx, "prev_idx")
    return header


def prepare_header(header: Header) -> tuple[Header, bool]:
    """Apply ``__log_buf_prepare_buffer`` to the four-word header.

    The FYG8 source preserves ``boot_cnt`` when magic is invalid and resets
    only magic, idx, and prev_idx.
    """

    validate_header(header)
    if header.magic == LOG_MAGIC:
        return header, False
    return Header(header.boot_cnt, LOG_MAGIC, 0, 0), True


def stock_snapshot(payload: bytes, header: Header) -> Snapshot:
    """Reproduce ``__log_buf_copy_to_buffer`` exactly.

    The source uses a strict ``idx > payload_size`` rotation condition.  At
    ``idx == payload_size`` it takes the prefix branch and copies the complete
    payload.
    """

    prepared, reset = prepare_header(header)
    size = len(payload)
    if size == 0:
        raise ModelError("payload is empty")

    if prepared.idx > size:
        head = prepared.idx % size
        data = payload[head:] + payload[:head]
        branch = "rotated_full"
    else:
        data = payload[: prepared.idx]
        branch = "prefix"

    if reset:
        branch = "invalid_magic_reset_empty"
    return Snapshot(data=data, branch=branch, prepared_header=prepared)


def precursor_position(idx: int, payload_size: int, proof_size: int) -> int:
    """Return the exact D/E/E0 contiguous no-index-mutation placement."""

    _require_u32(idx, "idx")
    if payload_size <= 0:
        raise ModelError("payload_size must be positive")
    if proof_size <= 0 or proof_size > payload_size:
        raise ModelError("proof_size must be within the payload")
    cursor = idx % payload_size
    return cursor - proof_size if cursor >= proof_size else payload_size - proof_size


def place_precursor(payload: bytes, idx: int, proof: bytes) -> tuple[bytes, int]:
    if not proof:
        raise ModelError("proof is empty")
    position = precursor_position(idx, len(payload), len(proof))
    updated = bytearray(payload)
    updated[position : position + len(proof)] = proof
    return bytes(updated), position


def analyze_visibility(
    *, idx: int, proof: bytes, payload_size: int = PAYLOAD_SIZE
) -> dict[str, Any]:
    """Place one unique proof and report its exact stock snapshot visibility."""

    if not proof:
        raise ModelError("proof is empty")
    if len(proof) > payload_size:
        raise ModelError("proof exceeds payload")
    filler = b"\xa5" * payload_size
    if proof in filler:
        raise ModelError("proof must be unique relative to the filler")

    updated, position = place_precursor(filler, idx, proof)
    snapshot = stock_snapshot(
        updated,
        Header(boot_cnt=7, magic=LOG_MAGIC, idx=idx, prev_idx=0x12345678),
    )
    count = snapshot.data.count(proof)
    offset = snapshot.data.find(proof)
    return {
        "idx": idx,
        "cursor": idx % payload_size,
        "position": position,
        "source_branch": snapshot.branch,
        "snapshot_size": len(snapshot.data),
        "proof_count": count,
        "proof_offset": offset if offset >= 0 else None,
        "proof_visible": count == 1,
        "legacy_full_saturation_gate": idx >= payload_size,
        "minimal_full_proof_visibility_gate": idx >= len(proof),
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _normalize_source(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise ModelError(f"source is not a direct regular file: {path}")
    return " ".join(path.read_text(encoding="utf-8").split())


def audit_sources(main_source: Path, last_kmsg_source: Path) -> dict[str, Any]:
    paths = {"main": main_source, "last_kmsg": last_kmsg_source}
    actual = {label: _sha256(path) for label, path in paths.items()}
    for label, expected in SOURCE_PINS.items():
        if actual[label] != expected:
            raise ModelError(
                f"{label} source SHA256 mismatch: {actual[label]} != {expected}"
            )

    main = _normalize_source(main_source)
    last = _normalize_source(last_kmsg_source)
    required_main = (
        "idx = s_log_buf->idx % sec_log_buf_size;",
        "s_log_buf->idx += (uint32_t)count;",
        "if (log_buf_head->idx > max_size)",
        "head = (size_t)log_buf_head->idx % log_buf_size;",
        "__log_buf_memcpy_fromio(buf, log_buf_head->buf, log_buf_head->idx);",
        "s_log_buf->magic = SEC_LOG_MAGIC;",
        "s_log_buf->idx = 0;",
        "s_log_buf->prev_idx = 0;",
    )
    required_last = (
        "last_kmsg->size = __log_buf_copy_to_buffer(buf);",
        "err = crypto_comp_decompress(last_kmsg->tfm, last_kmsg->buf_comp, "
        "size_comp, buf, &size);",
        "last_kmsg->buf = buf;",
        "copy_to_user(buf, last_kmsg->buf + pos, count)",
    )
    missing = [token for token in required_main if token not in main]
    missing.extend(token for token in required_last if token not in last)
    if missing:
        raise ModelError(f"source contract mismatch: {missing}")

    copy_start = main.find("size_t __log_buf_copy_to_buffer(void *buf)")
    copy_end = main.find("static int __log_buf_parse_dt_strategy", copy_start)
    if copy_start < 0 or copy_end < 0:
        raise ModelError("could not isolate snapshot-copy function")
    copy_body = main[copy_start:copy_end]
    if "boot_cnt" in copy_body or "prev_idx" in copy_body:
        raise ModelError("snapshot unexpectedly depends on boot_cnt or prev_idx")

    ordered = (
        "DEVICE_BUILDER(__log_buf_prepare_buffer, NULL)",
        "DEVICE_BUILDER(__last_kmsg_alloc_buffer, __last_kmsg_free_buffer)",
        "DEVICE_BUILDER(__last_kmsg_pull_last_log, NULL)",
        "DEVICE_BUILDER(__last_kmsg_procfs_create, __last_kmsg_procfs_remove)",
        "DEVICE_BUILDER(__log_buf_pull_early_buffer, NULL)",
        "DEVICE_BUILDER(__log_buf_logger_init, __log_buf_logger_exit)",
    )
    positions = [main.find(token) for token in ordered]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        raise ModelError("snapshot/logger probe order mismatch")

    return {
        "sha256": actual,
        "strict_rotation_condition": "idx > payload_size",
        "invalid_magic_resets": ["magic", "idx", "prev_idx"],
        "invalid_magic_preserves": ["boot_cnt", "payload_bytes"],
        "snapshot_ignores": ["boot_cnt", "prev_idx"],
        "snapshot_frozen_before_current_logger": True,
        "proc_open_restores_optional_compressed_snapshot": True,
    }


def build_result(main_source: Path, last_kmsg_source: Path, proof_size: int) -> dict[str, Any]:
    if proof_size <= 0 or proof_size > PAYLOAD_SIZE:
        raise ModelError("proof_size is outside the FYG8 payload")
    proof = b"[[S22MODEL|" + b"P" * max(0, proof_size - 14) + b"]]"
    proof = proof[:proof_size]
    if len(proof) != proof_size:
        proof = (b"S22M" * ((proof_size + 3) // 4))[:proof_size]

    boundary_indices = (
        0,
        proof_size - 1,
        proof_size,
        PAYLOAD_SIZE - 1,
        PAYLOAD_SIZE,
        PAYLOAD_SIZE + 1,
        PAYLOAD_SIZE + proof_size - 1,
        PAYLOAD_SIZE * 2,
        UINT32_MAX,
    )
    matrix = [
        analyze_visibility(idx=idx, proof=proof, payload_size=PAYLOAD_SIZE)
        for idx in boundary_indices
    ]
    invalid = stock_snapshot(
        b"\xa5" * PAYLOAD_SIZE,
        Header(boot_cnt=9, magic=0, idx=PAYLOAD_SIZE + 1, prev_idx=4),
    )

    return {
        "schema": SCHEMA,
        "verdict": VERDICT,
        "source_audit": audit_sources(main_source, last_kmsg_source),
        "constants": {
            "log_region_size": LOG_REGION_SIZE,
            "header_size": HEADER_SIZE,
            "payload_size": PAYLOAD_SIZE,
            "log_magic": f"0x{LOG_MAGIC:08x}",
            "proof_size": proof_size,
        },
        "boundary_matrix": matrix,
        "invalid_magic_case": {
            "source_branch": invalid.branch,
            "snapshot_size": len(invalid.data),
            "prepared_header": invalid.prepared_header.__dict__,
        },
        "decision": {
            "full_saturation_required": False,
            "sufficient_visibility_condition": "valid magic and idx >= proof_size",
            "idx_below_proof_size": "full unchanged-index proof is not exposed",
            "boot_cnt_affects_visibility": False,
            "prev_idx_affects_visibility": False,
            "live_authorized": False,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--main-source", type=Path, default=DEFAULT_MAIN_SOURCE)
    parser.add_argument(
        "--last-kmsg-source", type=Path, default=DEFAULT_LAST_KMSG_SOURCE
    )
    parser.add_argument("--proof-size", type=int, default=45)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = build_result(args.main_source, args.last_kmsg_source, args.proof_size)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
