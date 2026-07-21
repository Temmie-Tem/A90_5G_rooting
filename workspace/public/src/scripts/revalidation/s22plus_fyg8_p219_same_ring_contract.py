#!/usr/bin/env python3
"""Validate the FYG8 P2.19 same-ring implementation host-only."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import s22plus_fyg8_p218_same_ring_discriminator as design  # noqa: E402
import s22plus_fyg8_p219_same_ring_decoder as decoder  # noqa: E402
import s22plus_fyg8_r4w1b_patch_check as shared  # noqa: E402


SCHEMA = "s22plus_fyg8_p219_same_ring_contract_v1"
VERDICT = "PASS_P219_SAME_RING_IMPLEMENTATION_HOST_ONLY"
TARGET = shared.TARGET
CONFIG = "CONFIG_S22PLUS_FYG8_PID1_SAME_RING_DISCRIMINATOR"
DEFAULT_SOURCE = shared.DEFAULT_SOURCE
DEFAULT_PATCH = Path(
    "workspace/public/src/patches/"
    "s22plus_fyg8_p219_same_ring_discriminator.patch"
)
PATCH_SHA256 = "6bf03ca0d3448e0a707b03815e94d8ef5c059e9aaa14f3612a0bb953f3758c44"
PATCHED_FILES = {
    "kernel_platform/common/init/main.c": (
        "4e4658f083f12543c43112e79fe55241f70be5788cd5456e6d564aca18c78499"
    ),
    "kernel_platform/common/init/Kconfig": (
        "064f48fb37f8f835c27b8f69b381e14f20774de8e31b29c4eed4d6e3322561b3"
    ),
    "kernel_platform/common/arch/arm64/configs/gki_defconfig": (
        "b696b4da1514d2a7afab2335d400641fced9f08453d257e69aae1002c0414722"
    ),
}

CONTRACT_PREIMAGE = decoder.CONTRACT_PREIMAGE
CONTRACT_BYTES = decoder.CONTRACT_BYTES
CONTRACT_SHA256 = decoder.CONTRACT_SHA256
CONTRACT_ID = decoder.CONTRACT_ID
RECORDS = design.build_records(CONTRACT_BYTES)
ENTRY_PROOF = decoder.ENTRY_PROOF
USERSPACE_PROOF = decoder.USERSPACE_PROOF
UNSAT_PROOF = decoder.UNSAT_PROOF
REQUEST = bytes.fromhex(
    "53323251010110000000000064554e8469385878c5bf8d57c44edeeafd118a62"
)
OLD_E0_ENTRY_PROOF = b"\n[[S22P1U|ba234c7de4105b2a23222436284605f2]]\n"
OLD_E0_USERSPACE_PROOF = b"\n[[S22P1U|ec8d029b05288644bbe7b5f7c7af190c]]\n"


class CheckError(ValueError):
    pass


def _added_lines(text: str) -> list[str]:
    return [
        line[1:]
        for line in text.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    ]


def _function(text: str, start: str, end: str) -> str:
    try:
        begin = text.index(start)
        finish = text.index(end, begin)
    except ValueError as exc:
        raise CheckError(f"required source boundary missing: {start}") from exc
    return text[begin:finish]


def _initializer(added_text: str, name: str) -> bytes:
    match = re.search(
        rf"{name}\[[A-Z0-9_]+\] = \{{(.*?)\n\}};",
        added_text,
        flags=re.DOTALL,
    )
    if match is None:
        raise CheckError(f"byte initializer missing: {name}")
    return bytes(
        int(value, 16)
        for value in re.findall(r"0x([0-9a-fA-F]{2})", match.group(1))
    )


def check_record_derivation() -> dict[str, Any]:
    if TARGET != decoder.TARGET:
        raise CheckError("candidate target differs across the fixed contract")
    if CONTRACT_SHA256 != (
        "a01800f437cf129e693f32b7199ea6a613dd2366fff82ca45083f2098fd13bae"
    ):
        raise CheckError("candidate contract preimage changed")
    if RECORDS.contract_sha256 != CONTRACT_SHA256:
        raise CheckError("record derivation is not bound to the contract")
    if (
        RECORDS.entry != ENTRY_PROOF
        or RECORDS.userspace != USERSPACE_PROOF
        or RECORDS.unsat != UNSAT_PROOF
    ):
        raise CheckError("candidate-bound record bytes changed")
    return {
        "contract_id": CONTRACT_ID.hex(),
        "contract_sha256": CONTRACT_SHA256,
        "entry_hex": ENTRY_PROOF.hex(),
        "userspace_hex": USERSPACE_PROOF.hex(),
        "unsat_hex": UNSAT_PROOF.hex(),
        "binding_bits": design.BINDING_BITS,
        "verified": True,
    }


def check_patch(patch: Path) -> dict[str, Any]:
    if patch.is_symlink() or not patch.is_file():
        raise CheckError("P2.19 patch missing or indirect")
    actual = shared.sha256_file(patch)
    if actual != PATCH_SHA256:
        raise CheckError(f"P2.19 patch SHA256 mismatch: {actual}")
    text = patch.read_text(encoding="ascii")
    targets = re.findall(r"^\+\+\+ b/(.+)$", text, flags=re.MULTILINE)
    if set(targets) != set(shared.BASE_FILES) or len(targets) != len(
        shared.BASE_FILES
    ):
        raise CheckError(f"unexpected patch targets: {targets}")
    added = _added_lines(text)
    added_text = "\n".join(added)
    configs = {
        symbol
        for line in added
        for symbol in re.findall(r"CONFIG_[A-Z0-9_]+", line)
    }
    if configs != {CONFIG}:
        raise CheckError(f"unexpected config symbols: {sorted(configs)}")
    forbidden = (
        "panic(",
        "emergency_restart",
        "kernel_restart",
        "reboot(",
        "filp_open",
        "kernel_write",
        "blkdev_get",
        "submit_bio",
        "ioremap(",
        "sec_log_buf",
    )
    hits = [token for token in forbidden if token in added_text]
    if hits:
        raise CheckError(f"forbidden operation or owner-module use: {hits}")
    metadata_writes = re.findall(
        r"head->(?:magic|idx|prev_idx|boot_cnt)\s*=", added_text
    )
    if metadata_writes:
        raise CheckError(f"retained header write found: {metadata_writes}")
    required = (
        ENTRY_PROOF.decode("ascii").strip(),
        USERSPACE_PROOF.decode("ascii").strip(),
        'of_find_node_by_path("/")',
        'strcmp(model, "Samsung G0Q PROJECT (board-id,12)")',
        '"samsung,kernel_log_buf"',
        '"sec,strategy"',
        "of_address_to_resource(log_node, 0, &resource)",
        "resource.start != S22PLUS_FYG8_P1S_LOG_BASE",
        "resource_size(&resource) != S22PLUS_FYG8_P1S_LOG_SIZE",
        "seed_idx >= S22PLUS_FYG8_P1S_ENTRY_SIZE",
        "seed_idx >= S22PLUS_FYG8_P1S_UNSAT_SIZE",
        "if (!arm_userspace)",
        'proc_create("s22_checkpoint", 0200',
    )
    missing = [token for token in required if token not in added_text]
    if missing:
        raise CheckError(f"required implementation tokens missing: {missing}")
    if added_text.count("[[S22P1U|") != 2:
        raise CheckError("long record family cardinality mismatch")
    if _initializer(added_text, "s22plus_fyg8_p1s_unsat") != UNSAT_PROOF:
        raise CheckError("kernel UNSAT bytes differ from the contract")
    if _initializer(added_text, "s22plus_fyg8_p1s_request") != REQUEST:
        raise CheckError("kernel request bytes differ from the exact runtime")
    return {
        "path": str(patch),
        "sha256": actual,
        "targets": targets,
        "config": CONFIG,
        "forbidden_hits": hits,
        "header_metadata_writes": metadata_writes,
        "verified": True,
    }


def apply_and_check(source: Path, patch: Path) -> dict[str, Any]:
    shared.check_base_files(source)
    with tempfile.TemporaryDirectory(prefix="s22plus-p219-") as temp_name:
        temporary = Path(temp_name)
        for relative in shared.BASE_FILES:
            destination = temporary / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / relative, destination)
        completed = subprocess.run(
            ["patch", "--batch", "--forward", "-p1", "-i", str(patch)],
            cwd=temporary,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        if completed.returncode != 0:
            raise CheckError(f"patch application failed: {completed.stdout[-2000:]}")
        hashes = {
            relative: shared.sha256_file(temporary / relative)
            for relative in shared.BASE_FILES
        }
        if hashes != PATCHED_FILES:
            raise CheckError(f"patched file identities mismatch: {hashes}")
        main = (temporary / "kernel_platform/common/init/main.c").read_text(
            encoding="ascii"
        )
        target = _function(
            main,
            "static struct s22plus_fyg8_p1s_log_head *s22plus_fyg8_p1s_head",
            "static bool s22plus_fyg8_p1s_header_matches",
        )
        target_order = (
            'of_find_node_by_path("/")',
            'of_property_read_string(root, "model", &model)',
            'strcmp(model, "Samsung G0Q PROJECT (board-id,12)")',
            "of_find_compatible_node",
            'of_property_read_u32(log_node, "sec,strategy", &strategy)',
            "of_address_to_resource(log_node, 0, &resource)",
            "resource.start != S22PLUS_FYG8_P1S_LOG_BASE",
            "resource_size(&resource) != S22PLUS_FYG8_P1S_LOG_SIZE",
            "phys_to_virt((phys_addr_t)resource.start)",
        )
        entry = _function(
            main,
            "static void s22plus_fyg8_p1s_record_entry",
            "static ssize_t s22plus_fyg8_p1s_write",
        )
        entry_order = (
            'strcmp(init_filename, "/init")',
            "task_pid_nr(current) != 1",
            "s22plus_fyg8_p1s_head()",
            "READ_ONCE(head->magic) != S22PLUS_FYG8_P1S_LOG_MAGIC",
            "seed_idx >= S22PLUS_FYG8_P1S_ENTRY_SIZE",
            "seed_idx >= S22PLUS_FYG8_P1S_UNSAT_SIZE",
            "s22plus_fyg8_p1s_header_matches(head, seed_idx, seed_boot_cnt)",
            "s22plus_fyg8_p1s_store(head, proof_pos, proof, proof_size)",
            "if (!arm_userspace)",
            "s22plus_fyg8_p1s_state.ready = true",
        )
        writer = _function(
            main,
            "static ssize_t s22plus_fyg8_p1s_write",
            "static const struct proc_ops s22plus_fyg8_p1s_ops",
        )
        writer_order = (
            "task_pid_nr(current) != 1",
            "!s22plus_fyg8_p1s_state.ready",
            "copy_from_user(request, buffer, sizeof(request))",
            "memcmp(request, s22plus_fyg8_p1s_request, sizeof(request))",
            "s22plus_fyg8_p1s_head()",
            "memcmp(slot, s22plus_fyg8_p1s_entry",
            "s22plus_fyg8_p1s_store(head",
            "s22plus_fyg8_p1s_state.userspace_proven = true",
        )
        for label, body, tokens in (
            ("target", target, target_order),
            ("entry", entry, entry_order),
            ("writer", writer, writer_order),
        ):
            positions = [body.index(token) for token in tokens]
            if positions != sorted(positions):
                raise CheckError(f"{label} guard order mismatch")
        if entry.count("s22plus_fyg8_p1s_header_matches(") != 2:
            raise CheckError("entry does not have exact pre/post header checks")
        if writer.count("s22plus_fyg8_p1s_header_matches(") != 2:
            raise CheckError("writer does not have exact pre/post header checks")
        edge = _function(main, "if (ramdisk_execute_command)", "/*\n\t * We try")
        expected_edge = (
            "ret = run_init_process(ramdisk_execute_command);\n"
            "\t\tif (!ret) {\n"
            "\t\t\ts22plus_fyg8_p1s_record_entry(ramdisk_execute_command);"
        )
        if (
            expected_edge not in edge
            or main.count("s22plus_fyg8_p1s_record_entry(") != 3
        ):
            raise CheckError("record hook is not on the unique exec-success edge")
        return {
            "patched_files": hashes,
            "target_layout_guard": True,
            "pre_post_header_checks": True,
            "source_semantics": True,
            "verified": True,
        }


def classify_compiled_blob(blob: bytes, label: str) -> dict[str, Any]:
    counts = {
        "entry_count": blob.count(ENTRY_PROOF),
        "userspace_count": blob.count(USERSPACE_PROOF),
        "unsat_count": blob.count(UNSAT_PROOF),
        "long_family_count": blob.count(design.ENTRY_FAMILY),
        "unsat_family_count": blob.count(design.UNSAT_FAMILY),
        "old_e0_entry_count": blob.count(OLD_E0_ENTRY_PROOF),
        "old_e0_userspace_count": blob.count(OLD_E0_USERSPACE_PROOF),
    }
    expected = {
        "entry_count": 1,
        "userspace_count": 1,
        "unsat_count": 1,
        "long_family_count": 2,
        "unsat_family_count": 1,
        "old_e0_entry_count": 0,
        "old_e0_userspace_count": 0,
    }
    if counts != expected:
        raise CheckError(f"{label} record cardinality mismatch: {counts}")
    return {
        "label": label,
        "size": len(blob),
        "sha256": hashlib.sha256(blob).hexdigest(),
        **counts,
        "verified": True,
    }


def verify_extracted_artifact_closure(
    *,
    image: bytes,
    vmlinux: bytes,
    boot_image: bytes,
    extracted_boot_kernel: bytes,
    ap_members: list[dict[str, Any]],
) -> dict[str, Any]:
    image_result = classify_compiled_blob(image, "Image")
    vmlinux_result = classify_compiled_blob(vmlinux, "vmlinux")
    if extracted_boot_kernel != image:
        raise CheckError("boot-extracted kernel differs from the checked Image")
    if ap_members != [{"name": "boot.img.lz4", "type": "regular"}]:
        raise CheckError("AP is not an exact one-member boot-only archive")
    return {
        "image": image_result,
        "vmlinux": vmlinux_result,
        "boot_image": {
            "size": len(boot_image),
            "sha256": hashlib.sha256(boot_image).hexdigest(),
        },
        "boot_kernel": {
            "size": len(extracted_boot_kernel),
            "sha256": hashlib.sha256(extracted_boot_kernel).hexdigest(),
            "equals_image": True,
        },
        "ap_members": ap_members,
        "boot_only_ap": True,
        "verified": True,
    }


def run(source: Path, patch: Path) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "target": TARGET,
        "record_contract": check_record_derivation(),
        "patch": check_patch(patch),
        "source": apply_and_check(source, patch),
        "artifact_checker": {
            "implemented": True,
            "requires_independently_extracted_image_vmlinux_boot_and_ap_inventory": True,
            "candidate_artifacts_verified": False,
        },
        "safety": {
            "host_only": True,
            "device_contact": False,
            "device_write": False,
            "kernel_build": False,
            "image_created": False,
            "manifest_created": False,
            "flash": False,
            "live_authorized": False,
        },
        "verdict": VERDICT,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--patch", type=Path, default=DEFAULT_PATCH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = shared.repo_root()
    source = shared.resolve(root, args.source)
    patch = shared.resolve(root, args.patch)
    try:
        result = run(source, patch)
    except (CheckError, design.ContractError, shared.CheckError) as exc:
        print(json.dumps({"schema": SCHEMA, "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
