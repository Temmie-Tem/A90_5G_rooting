#!/usr/bin/env python3
"""Model the bounded FYG8 same-ring discriminator host-only.

This is an executable design contract.  It has no device transport, image
builder, manifest promotion, approval, or live-run authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import s22plus_fyg8_retained_snapshot_model as retained  # noqa: E402


SCHEMA = "s22plus_fyg8_p218_same_ring_discriminator_v1"
VERDICT = "PASS_P218_SAME_RING_DISCRIMINATOR_DESIGN_HOST_ONLY"
TARGET = "SM-S906N/g0q/S906NKSS7FYG8"

ENTRY_FAMILY = b"[[S22P1U|"
UNSAT_FAMILY = b"S22UNS1|"
TAG_SIZE = 16
ENTRY_SIZE = 45
UNSAT_SIZE = len(UNSAT_FAMILY) + TAG_SIZE
BINDING_BITS = TAG_SIZE * 8

MODEL_CANDIDATE_CONTRACT = (
    b"MODEL-ONLY|S22PLUS-FYG8|P2.18|same-ring-discriminator-v1|"
    b"not-an-artifact-identity"
)


class ContractError(ValueError):
    pass


@dataclass(frozen=True)
class RecordSet:
    contract_sha256: str
    entry: bytes
    userspace: bytes
    unsat: bytes


@dataclass(frozen=True)
class WritePlan:
    state: str
    reason: str
    record: bytes | None
    position: int | None
    seed_idx: int
    seed_boot_cnt: int
    userspace_armed: bool


def _derive_tag(candidate_contract: bytes, state: bytes) -> bytes:
    if (
        not isinstance(candidate_contract, bytes)
        or not candidate_contract
        or len(candidate_contract) > 4096
    ):
        raise ContractError("candidate contract must be 1..4096 bytes")
    return hashlib.sha256(
        b"S22PLUS-FYG8-P218-RECORD-V1\x00" + state + b"\x00" + candidate_contract
    ).digest()[:TAG_SIZE]


def _long_record(tag: bytes) -> bytes:
    if len(tag) != TAG_SIZE:
        raise ContractError("record tag is not 128 bits")
    return b"\n" + ENTRY_FAMILY + tag.hex().encode("ascii") + b"]]\n"


def build_records(candidate_contract: bytes) -> RecordSet:
    entry_tag = _derive_tag(candidate_contract, b"ENTRY")
    userspace_tag = _derive_tag(candidate_contract, b"USERSPACE")
    unsat_tag = _derive_tag(candidate_contract, b"UNSAT")
    records = RecordSet(
        contract_sha256=hashlib.sha256(candidate_contract).hexdigest(),
        entry=_long_record(entry_tag),
        userspace=_long_record(userspace_tag),
        unsat=UNSAT_FAMILY + unsat_tag,
    )
    validate_records(records)
    return records


def validate_records(records: RecordSet) -> RecordSet:
    if len(records.entry) != ENTRY_SIZE or len(records.userspace) != ENTRY_SIZE:
        raise ContractError("ENTRY and USERSPACE records must remain 45 bytes")
    if len(records.unsat) != UNSAT_SIZE or UNSAT_SIZE != 24:
        raise ContractError("UNSAT record must be exactly 24 bytes")
    if records.entry == records.userspace:
        raise ContractError("ENTRY and USERSPACE records are not distinct")
    if records.entry.count(ENTRY_FAMILY) != 1:
        raise ContractError("ENTRY family cardinality is not one")
    if records.userspace.count(ENTRY_FAMILY) != 1:
        raise ContractError("USERSPACE family cardinality is not one")
    if records.unsat.count(UNSAT_FAMILY) != 1:
        raise ContractError("UNSAT family cardinality is not one")
    if UNSAT_FAMILY in records.entry or UNSAT_FAMILY in records.userspace:
        raise ContractError("UNSAT family collides with a long record")
    if ENTRY_FAMILY in records.unsat:
        raise ContractError("long-record family collides with UNSAT")
    return records


def select_write(
    *,
    records: RecordSet,
    post_exec_hook_reached: bool,
    init_filename: str,
    pid: int,
    header: retained.Header,
    payload_size: int = retained.PAYLOAD_SIZE,
) -> WritePlan:
    """Select at most one no-index-mutation write.

    The caller represented by this contract samples and revalidates the exact
    header before and after the write.  No record is allowed before the path,
    PID, physical-layout, and magic guards.
    """

    retained.validate_header(header)
    if payload_size < ENTRY_SIZE * 2:
        raise ContractError("payload must be at least twice the longest record")

    common = {
        "seed_idx": header.idx,
        "seed_boot_cnt": header.boot_cnt,
    }
    if not post_exec_hook_reached:
        return WritePlan("NONE", "post-exec hook not reached", None, None, **common,
                         userspace_armed=False)
    if init_filename != "/init" or pid != 1:
        return WritePlan("NONE", "path or PID guard rejected", None, None, **common,
                         userspace_armed=False)
    if header.magic != retained.LOG_MAGIC:
        return WritePlan("NONE", "retained magic invalid", None, None, **common,
                         userspace_armed=False)
    if header.idx >= ENTRY_SIZE:
        return WritePlan(
            "ENTRY",
            "45-byte ENTRY fits the stock-exposed snapshot",
            records.entry,
            retained.precursor_position(header.idx, payload_size, ENTRY_SIZE),
            **common,
            userspace_armed=True,
        )
    if header.idx >= UNSAT_SIZE:
        return WritePlan(
            "UNSAT",
            "valid magic but the 45-byte ENTRY does not fit",
            records.unsat,
            retained.precursor_position(header.idx, payload_size, UNSAT_SIZE),
            **common,
            userspace_armed=False,
        )
    return WritePlan(
        "NONE",
        "index is below the minimum 24-byte record size",
        None,
        None,
        **common,
        userspace_armed=False,
    )


def apply_write(
    payload: bytes,
    *,
    plan: WritePlan,
    header_before: retained.Header,
    header_after: retained.Header,
) -> bytes:
    """Apply the selected write only across a stable, exact header sample."""

    if plan.record is None:
        return payload
    if len(payload) < ENTRY_SIZE * 2:
        raise ContractError("payload must be at least twice the longest record")
    expected = (retained.LOG_MAGIC, plan.seed_idx, plan.seed_boot_cnt)
    before = (header_before.magic, header_before.idx, header_before.boot_cnt)
    after = (header_after.magic, header_after.idx, header_after.boot_cnt)
    if before != expected or after != expected:
        raise ContractError("retained header changed around the write")
    expected_position = retained.precursor_position(
        plan.seed_idx, len(payload), len(plan.record)
    )
    if plan.position != expected_position:
        raise ContractError("write position does not match the frozen cursor")

    updated = bytearray(payload)
    updated[plan.position : plan.position + len(plan.record)] = plan.record
    if bytes(updated[plan.position : plan.position + len(plan.record)]) != plan.record:
        raise ContractError("exact record readback failed")
    return bytes(updated)


def _edge_partial(payload: bytes, records: tuple[bytes, ...]) -> bool:
    for record in records:
        for length in range(4, len(record)):
            partial_head = (
                not payload.startswith(record)
                and payload.startswith(record[-length:])
            )
            partial_tail = (
                not payload.endswith(record)
                and payload.endswith(record[:length])
            )
            if partial_head or partial_tail:
                return True
    return False


def classify_observation(
    baseline: bytes,
    observed: bytes,
    records: RecordSet,
) -> dict[str, Any]:
    """Classify one complete retained read without promoting zero to proof."""

    validate_records(records)
    known = (records.entry, records.userspace, records.unsat)
    if (
        ENTRY_FAMILY in baseline
        or UNSAT_FAMILY in baseline
        or _edge_partial(baseline, known)
    ):
        raise ContractError("baseline is not clean for both record families")

    entry_count = observed.count(records.entry)
    userspace_count = observed.count(records.userspace)
    unsat_count = observed.count(records.unsat)
    long_family_count = observed.count(ENTRY_FAMILY)
    unsat_family_count = observed.count(UNSAT_FAMILY)
    partial = _edge_partial(observed, known)
    exact_total = entry_count + userspace_count + unsat_count
    integrity_issue = (
        partial
        or exact_total > 1
        or long_family_count != entry_count + userspace_count
        or unsat_family_count != unsat_count
    )

    if integrity_issue:
        classification = "AMBIGUOUS_INTEGRITY_FAILURE"
        accepted = False
    elif userspace_count == 1:
        classification = "USERSPACE_CALLBACK_REACHED"
        accepted = True
    elif entry_count == 1:
        classification = "ENTRY_ONLY"
        accepted = False
    elif unsat_count == 1:
        classification = "UNSAT_VALID_MAGIC_ENTRY_DID_NOT_FIT"
        accepted = False
    else:
        classification = "ZERO_AMBIGUOUS"
        accepted = False

    return {
        "classification": classification,
        "accepted": accepted,
        "integrity_issue": integrity_issue,
        "entry_count": entry_count,
        "userspace_count": userspace_count,
        "unsat_count": unsat_count,
        "long_family_count": long_family_count,
        "unsat_family_count": unsat_family_count,
        "partial_at_snapshot_edge": partial,
        "residual_zero_meanings": (
            [
                "candidate or post-exec hook not reached",
                "path or PID guard rejected",
                "retained magic invalid",
                "valid magic with idx below 24",
                "store, readback, or header-stability failure",
                "later overwrite, loss, or observer failure",
            ]
            if classification == "ZERO_AMBIGUOUS"
            else []
        ),
    }


def simulate(
    records: RecordSet,
    *,
    idx: int,
    magic: int = retained.LOG_MAGIC,
    post_exec_hook_reached: bool = True,
    payload_size: int = retained.PAYLOAD_SIZE,
) -> dict[str, Any]:
    header = retained.Header(boot_cnt=7, magic=magic, idx=idx, prev_idx=3)
    plan = select_write(
        records=records,
        post_exec_hook_reached=post_exec_hook_reached,
        init_filename="/init",
        pid=1,
        header=header,
        payload_size=payload_size,
    )
    payload = b"\xa5" * payload_size
    updated = apply_write(
        payload,
        plan=plan,
        header_before=header,
        header_after=header,
    )
    snapshot = retained.stock_snapshot(updated, header)
    result = classify_observation(b"", snapshot.data, records)
    return {
        "idx": idx,
        "plan_state": plan.state,
        "plan_reason": plan.reason,
        "record_size": len(plan.record) if plan.record is not None else 0,
        "position": plan.position,
        "userspace_armed": plan.userspace_armed,
        "snapshot_branch": snapshot.branch,
        "snapshot_size": len(snapshot.data),
        **result,
    }


def build_result(candidate_contract: bytes = MODEL_CANDIDATE_CONTRACT) -> dict[str, Any]:
    records = build_records(candidate_contract)
    indices = (
        0,
        UNSAT_SIZE - 1,
        UNSAT_SIZE,
        ENTRY_SIZE - 1,
        ENTRY_SIZE,
        retained.PAYLOAD_SIZE - 1,
        retained.PAYLOAD_SIZE,
        retained.PAYLOAD_SIZE + 1,
        retained.UINT32_MAX,
    )
    matrix = [simulate(records, idx=idx) for idx in indices]
    expected = {
        idx: (
            "ZERO_AMBIGUOUS"
            if idx < UNSAT_SIZE
            else "UNSAT_VALID_MAGIC_ENTRY_DID_NOT_FIT"
            if idx < ENTRY_SIZE
            else "ENTRY_ONLY"
        )
        for idx in indices
    }
    if any(row["classification"] != expected[row["idx"]] for row in matrix):
        raise ContractError("boundary matrix violates the discriminator contract")

    invalid_magic = simulate(records, idx=ENTRY_SIZE, magic=0)
    not_selected = simulate(
        records,
        idx=ENTRY_SIZE,
        post_exec_hook_reached=False,
    )
    if any(
        result["classification"] != "ZERO_AMBIGUOUS"
        for result in (invalid_magic, not_selected)
    ):
        raise ContractError("residual zero ambiguity was incorrectly removed")

    return {
        "schema": SCHEMA,
        "verdict": VERDICT,
        "target": TARGET,
        "host_only": True,
        "candidate_artifact_created": False,
        "f1_authority_created": False,
        "record_contract": {
            "entry_size": ENTRY_SIZE,
            "unsat_size": UNSAT_SIZE,
            "binding_bits": BINDING_BITS,
            "contract_sha256": records.contract_sha256,
            "model_identity_only": candidate_contract == MODEL_CANDIDATE_CONTRACT,
            "entry_hex": records.entry.hex(),
            "userspace_hex": records.userspace.hex(),
            "unsat_hex": records.unsat.hex(),
        },
        "state_partition": {
            "entry": f"valid magic and idx >= {ENTRY_SIZE}",
            "unsat": f"valid magic and {UNSAT_SIZE} <= idx < {ENTRY_SIZE}",
            "zero_ambiguous": (
                f"invalid magic, idx < {UNSAT_SIZE}, nonselection, failed store, "
                "or later loss"
            ),
        },
        "acceptance": "USERSPACE_CALLBACK_REACHED only",
        "boundary_matrix": matrix,
        "invalid_magic_control": invalid_magic,
        "candidate_nonselection_control": not_selected,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidate-contract",
        help="ASCII model contract; omitted value remains explicitly model-only",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    contract = (
        args.candidate_contract.encode("ascii")
        if args.candidate_contract is not None
        else MODEL_CANDIDATE_CONTRACT
    )
    print(json.dumps(build_result(contract), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
