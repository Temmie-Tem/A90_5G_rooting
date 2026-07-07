#!/usr/bin/env python3
"""Build a host-only S22+ vendor_boot candidate that enables ramoops.

This script does not flash, reboot, or touch a connected device.

It patches the stock FYG8 vendor_boot DTB directly by adding
`status = "okay"` to every `/reserved-memory/ramoops_region` node. The stock
vendor_boot DTB has the node in four concatenated FDT blobs but has no status
property there; the earlier DTBO attempt patched an overlay instead.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import shutil
import struct
import subprocess
import tarfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from build_s22plus_direct_p3_boot import (
    DEFAULT_ODIN,
    display_path,
    lz4_frame_store,
    lz4_frame_store_decode,
    md5_file,
    repo_root,
    resolve,
    run,
    sha256_file,
    tar_members,
)
from build_s22plus_inplace_m4t1_magiskboot import (
    DEFAULT_MAGISK_APK,
    DEFAULT_MAGISKBOOT,
    ensure_magiskboot,
    run_in_dir,
)
from build_s22plus_ramoops_dtbo_enable import (
    FDT_BEGIN_NODE,
    FDT_END,
    FDT_END_NODE,
    FDT_MAGIC,
    FDT_NOP,
    FDT_PROP,
    align4,
    iter_fdt_blobs,
    parse_fdt_props,
)


DEFAULT_OUT = Path("workspace/private/outputs/s22plus_ramoops_vendor_boot_enable_v0_1")
DEFAULT_VENDOR_BOOT = Path("workspace/private/inputs/s22plus_firmware/S906NKSS7FYG8_SKC/extracted-images/raw/vendor_boot.img")
EXPECTED_VENDOR_BOOT_SHA256 = "096e433e049fb088cd956e083d5a1039b33cdf0ca907e713bba7feaaf1b080b7"
TARGET_NODE = "/reserved-memory/ramoops_region"
STATUS_NAME = "status"
STATUS_OKAY = b"okay\0"


@dataclass(frozen=True)
class InsertTarget:
    blob_index: int
    node_path: str
    insert_offset_in_blob: int
    nameoff: int
    old_has_status: bool


def read_c_string(data: bytes, offset: int) -> tuple[str, int]:
    end = data.find(b"\0", offset)
    if end < 0:
        raise ValueError("unterminated FDT node name")
    return data[offset:end].decode("ascii", errors="strict"), align4(end + 1)


def read_string_table(data: bytes, offset: int) -> str:
    end = data.find(b"\0", offset)
    if end < 0:
        raise ValueError("unterminated FDT string-table entry")
    return data[offset:end].decode("ascii", errors="strict")


def node_path(stack: list[str]) -> str:
    if not stack:
        return "/"
    return "/" + "/".join(stack)


def find_string_nameoff(blob: bytes, name: str) -> int:
    header = struct.unpack_from(">10I", blob, 0)
    _magic, _totalsize, _off_struct, off_strings, _off_mem, _version, _last_comp, _boot_cpuid, size_strings, _size_struct = header
    table = blob[off_strings : off_strings + size_strings]
    needle = name.encode("ascii") + b"\0"
    cursor = 0
    while True:
        found = table.find(needle, cursor)
        if found < 0:
            raise ValueError(f"FDT string table does not contain {name!r}")
        if found == 0 or table[found - 1] == 0:
            return found
        cursor = found + 1


def find_insert_target(blob: bytes, blob_index: int) -> InsertTarget:
    header = struct.unpack_from(">10I", blob, 0)
    magic, totalsize, off_struct, off_strings, _off_mem, _version, _last_comp, _boot_cpuid, size_strings, size_struct = header
    if magic != FDT_MAGIC:
        raise ValueError(f"FDT blob {blob_index} bad magic")
    struct_end = off_struct + size_struct
    strings_end = off_strings + size_strings
    if totalsize != len(blob) or struct_end > len(blob) or strings_end > len(blob):
        raise ValueError(f"FDT blob {blob_index} inconsistent header")

    nameoff = find_string_nameoff(blob, STATUS_NAME)
    stack: list[str] = []
    target_depth: int | None = None
    insert_offset: int | None = None
    old_has_status = False
    pos = off_struct
    while pos + 4 <= struct_end:
        token_pos = pos
        token = struct.unpack_from(">I", blob, pos)[0]
        pos += 4
        if token == FDT_BEGIN_NODE:
            name, pos = read_c_string(blob, pos)
            if name:
                stack.append(name)
            current = node_path(stack)
            if current == TARGET_NODE:
                target_depth = len(stack)
                insert_offset = pos
        elif token == FDT_END_NODE:
            if target_depth is not None and len(stack) == target_depth:
                if insert_offset is None:
                    raise ValueError(f"target node {TARGET_NODE} had no insertion point")
                return InsertTarget(blob_index, TARGET_NODE, insert_offset, nameoff, old_has_status)
            if stack:
                stack.pop()
        elif token == FDT_PROP:
            if pos + 8 > struct_end:
                raise ValueError(f"FDT blob {blob_index} truncated property header")
            length, prop_nameoff = struct.unpack_from(">II", blob, pos)
            pos += 8
            prop_name = read_string_table(blob, off_strings + prop_nameoff)
            current = node_path(stack)
            if current == TARGET_NODE:
                if prop_name == STATUS_NAME:
                    old_has_status = True
                insert_offset = align4(pos + length)
            pos = align4(pos + length)
        elif token == FDT_NOP:
            continue
        elif token == FDT_END:
            break
        else:
            raise ValueError(f"FDT blob {blob_index} unknown token {token} at 0x{token_pos:x}")
    raise ValueError(f"target node {TARGET_NODE} not found in FDT blob {blob_index}")


def patch_one_fdt_blob(blob: bytes, blob_index: int) -> tuple[bytes, dict[str, Any]]:
    target = find_insert_target(blob, blob_index)
    if target.old_has_status:
        raise SystemExit(f"{TARGET_NODE} already has status in blob {blob_index}")
    value_len = len(STATUS_OKAY)
    value_pad_len = align4(value_len)
    insert = (
        struct.pack(">III", FDT_PROP, value_len, target.nameoff)
        + STATUS_OKAY
        + b"\0" * (value_pad_len - value_len)
    )

    header = list(struct.unpack_from(">10I", blob, 0))
    totalsize = header[1]
    off_struct = header[2]
    off_strings = header[3]
    size_strings = header[8]
    size_struct = header[9]
    if target.insert_offset_in_blob < off_struct or target.insert_offset_in_blob > off_struct + size_struct:
        raise ValueError("target insertion offset outside structure block")

    patched = bytearray(blob[: target.insert_offset_in_blob] + insert + blob[target.insert_offset_in_blob :])
    delta = len(insert)
    header[1] = totalsize + delta
    header[3] = off_strings + delta
    header[9] = size_struct + delta
    struct.pack_into(">10I", patched, 0, *header)

    return bytes(patched), {
        "blob_index": blob_index,
        "target_node": target.node_path,
        "insert_offset_in_blob_hex": f"0x{target.insert_offset_in_blob:x}",
        "status_nameoff": target.nameoff,
        "insert_len": delta,
        "insert_value_hex": STATUS_OKAY.hex(),
        "old_has_status": target.old_has_status,
    }


def patch_concatenated_dtb(data: bytes) -> tuple[bytes, dict[str, Any]]:
    blobs = iter_fdt_blobs(data)
    if len(blobs) != 4:
        raise SystemExit(f"expected 4 vendor_boot DTB blobs, found {len(blobs)}")

    patched_parts: list[bytes] = []
    cursor = 0
    applied: list[dict[str, Any]] = []
    for blob in blobs:
        patched_parts.append(data[cursor : blob.offset])
        patched_blob, item = patch_one_fdt_blob(blob.data, blob.index)
        patched_parts.append(patched_blob)
        applied.append(item)
        cursor = blob.offset + blob.totalsize
    patched_parts.append(data[cursor:])
    patched = b"".join(patched_parts)

    status_after: list[dict[str, Any]] = []
    for blob in iter_fdt_blobs(patched):
        for prop in parse_fdt_props(blob):
            if prop.path == TARGET_NODE and prop.name == STATUS_NAME:
                status_after.append(
                    {
                        "blob_index": blob.index,
                        "length": prop.length,
                        "value_hex": prop.value.hex(),
                        "value": prop.value.rstrip(b"\0").decode("ascii", errors="replace"),
                    }
                )
    if len(status_after) != len(blobs):
        raise SystemExit(f"expected status in every vendor DTB blob, found {status_after!r}")
    if any(item["value"] != "okay" for item in status_after):
        raise SystemExit(f"unexpected status values after patch: {status_after!r}")
    return patched, {
        "blob_count": len(blobs),
        "applied": applied,
        "status_after": status_after,
        "input_size": len(data),
        "output_size": len(patched),
        "size_delta": len(patched) - len(data),
    }


def count_changed_bytes(left: bytes, right: bytes) -> int:
    return sum(1 for a, b in zip(left, right) if a != b) + abs(len(left) - len(right))


def write_lz4_store(raw: Path, out_lz4: Path) -> None:
    data = raw.read_bytes()
    frame = lz4_frame_store(data)
    if lz4_frame_store_decode(frame) != data:
        raise SystemExit(f"LZ4 roundtrip failed for {raw}")
    out_lz4.write_bytes(frame)


def write_single_member_tar_md5(member: Path, member_name: str, ap_tar: Path, ap_md5: Path) -> None:
    payload = member.read_bytes()
    with tarfile.open(ap_tar, "w") as tar:
        info = tarfile.TarInfo(member_name)
        info.size = len(payload)
        info.mode = 0o644
        info.mtime = 0
        tar.addfile(info, fileobj=io.BytesIO(payload))
    trailer = f"{md5_file(ap_tar)}  AP.tar\n".encode("ascii")
    ap_md5.write_bytes(ap_tar.read_bytes() + trailer)


def run_odin_parse_gate(odin: Path, ap_md5: Path) -> str:
    if not odin.exists():
        return "odin4_missing_parse_gate_skipped"
    result = subprocess.run(
        [str(odin), "-a", str(ap_md5), "-d", "/dev/bus/usb/999/999"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return (result.stdout + result.stderr).decode("utf-8", errors="replace")


def repack_vendor_boot(magiskboot: Path, source_vendor_boot: Path, work_dir: Path, output: Path, *, patched_dtb: bytes | None) -> dict[str, Any]:
    work_dir.mkdir(parents=True, exist_ok=True)
    unpack = subprocess.run(
        [str(magiskboot), "unpack", "-n", "-h", str(source_vendor_boot)],
        cwd=work_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    unpack_text = unpack.stdout + unpack.stderr
    if unpack.returncode != 3:
        raise SystemExit(f"vendor_boot unpack -n expected rc=3, got rc={unpack.returncode}\n{unpack_text}")
    stock_dtb = work_dir / "dtb"
    if not stock_dtb.is_file():
        raise SystemExit(f"magiskboot did not unpack vendor_boot dtb in {work_dir}")
    stock_dtb_sha = sha256_file(stock_dtb)
    if patched_dtb is not None:
        stock_dtb.write_bytes(patched_dtb)
    repack_text = run_in_dir([magiskboot, "repack", "-n", source_vendor_boot, output], work_dir, "vendor_boot repack -n")
    return {
        "unpack_output": unpack_text,
        "repack_output": repack_text,
        "unpacked_stock_dtb_sha256": stock_dtb_sha,
        "output_sha256": sha256_file(output),
        "output_size": output.stat().st_size,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--vendor-boot", type=Path, default=DEFAULT_VENDOR_BOOT)
    parser.add_argument("--magiskboot", type=Path, default=DEFAULT_MAGISKBOOT)
    parser.add_argument("--magisk-apk", type=Path, default=DEFAULT_MAGISK_APK)
    parser.add_argument("--odin", type=Path, default=DEFAULT_ODIN)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--no-odin-parse-gate", action="store_true")
    args = parser.parse_args(argv)

    root = repo_root()
    out_dir = resolve(root, args.out)
    vendor_boot = resolve(root, args.vendor_boot)
    magiskboot = resolve(root, args.magiskboot)
    magisk_apk = resolve(root, args.magisk_apk)
    odin = resolve(root, args.odin)

    if out_dir.exists():
        if not args.force:
            raise SystemExit(f"output directory exists; pass --force to replace: {out_dir}")
        shutil.rmtree(out_dir)
    build_dir = out_dir / "build"
    nochange_dir = out_dir / "nochange-repack"
    patched_dir = out_dir / "patched-repack"
    candidate_odin_dir = out_dir / "candidate_odin4"
    rollback_odin_dir = out_dir / "stock_rollback_odin4"
    for directory in (build_dir, nochange_dir, patched_dir, candidate_odin_dir, rollback_odin_dir):
        directory.mkdir(parents=True)

    ensure_magiskboot(magiskboot, magisk_apk)
    vendor_boot_sha = sha256_file(vendor_boot)
    if vendor_boot_sha != EXPECTED_VENDOR_BOOT_SHA256:
        raise SystemExit(f"stock vendor_boot SHA mismatch: {vendor_boot_sha}")

    source_unpack_dir = out_dir / "source-unpack"
    source_unpack_dir.mkdir()
    source_info = repack_vendor_boot(magiskboot, vendor_boot, source_unpack_dir, build_dir / "source_repack_probe.img", patched_dtb=None)
    source_dtb = source_unpack_dir / "dtb"
    source_dtb_bytes = source_dtb.read_bytes()
    patched_dtb_bytes, dtb_patch = patch_concatenated_dtb(source_dtb_bytes)
    patched_dtb_path = build_dir / "dtb.ramoops_status_okay"
    patched_dtb_path.write_bytes(patched_dtb_bytes)

    nochange_boot = build_dir / "vendor_boot.nochange_repack.img"
    nochange_info = repack_vendor_boot(magiskboot, vendor_boot, nochange_dir, nochange_boot, patched_dtb=None)
    patched_boot = build_dir / "vendor_boot.ramoops_status_okay.img"
    patched_info = repack_vendor_boot(magiskboot, vendor_boot, patched_dir, patched_boot, patched_dtb=patched_dtb_bytes)
    if nochange_boot.stat().st_size != vendor_boot.stat().st_size or patched_boot.stat().st_size != vendor_boot.stat().st_size:
        raise SystemExit("vendor_boot repack changed partition image size")

    candidate_lz4 = candidate_odin_dir / "vendor_boot.img.lz4"
    rollback_lz4 = rollback_odin_dir / "vendor_boot.img.lz4"
    write_lz4_store(patched_boot, candidate_lz4)
    write_lz4_store(vendor_boot, rollback_lz4)
    candidate_ap_tar = candidate_odin_dir / "AP.tar"
    candidate_ap_md5 = candidate_odin_dir / "AP.tar.md5"
    rollback_ap_tar = rollback_odin_dir / "AP.tar"
    rollback_ap_md5 = rollback_odin_dir / "AP.tar.md5"
    write_single_member_tar_md5(candidate_lz4, "vendor_boot.img.lz4", candidate_ap_tar, candidate_ap_md5)
    write_single_member_tar_md5(rollback_lz4, "vendor_boot.img.lz4", rollback_ap_tar, rollback_ap_md5)
    candidate_members = tar_members(candidate_ap_md5)
    rollback_members = tar_members(rollback_ap_md5)
    if candidate_members != ["vendor_boot.img.lz4"] or rollback_members != ["vendor_boot.img.lz4"]:
        raise SystemExit(f"AP tar member mismatch: candidate={candidate_members} rollback={rollback_members}")

    candidate_parse_gate = ""
    rollback_parse_gate = ""
    if not args.no_odin_parse_gate:
        candidate_parse_gate = run_odin_parse_gate(odin, candidate_ap_md5)
        rollback_parse_gate = run_odin_parse_gate(odin, rollback_ap_md5)
        (candidate_odin_dir / "parse_dry_run_invalid_device.txt").write_text(candidate_parse_gate, encoding="utf-8")
        (rollback_odin_dir / "parse_dry_run_invalid_device.txt").write_text(rollback_parse_gate, encoding="utf-8")

    stock_bytes = vendor_boot.read_bytes()
    nochange_bytes = nochange_boot.read_bytes()
    patched_bytes = patched_boot.read_bytes()
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "target": "SM-S906N/g0q/S906NKSS7FYG8",
        "purpose": "host-only vendor_boot DTB direct patch to enable ramoops status=okay",
        "safety": {
            "host_only": True,
            "touches_connected_device": False,
            "live_flash_authorized": False,
            "partition_scope_if_later_authorized": "vendor_boot only",
            "requires_new_sha_pinned_vendor_boot_exception_before_flash": True,
            "current_agents_does_not_authorize_this_live_flash": True,
            "forbidden_partitions_touched": False,
            "rollback_ap_built": True,
            "stock_vendor_boot_available": True,
            "nochange_repack_byte_identical": nochange_info["output_sha256"] == vendor_boot_sha,
            "nochange_repack_not_byte_identical_warning": nochange_info["output_sha256"] != vendor_boot_sha,
        },
        "paths": {
            "out_dir": display_path(root, out_dir),
            "stock_vendor_boot": display_path(root, vendor_boot),
            "patched_vendor_boot": display_path(root, patched_boot),
            "patched_dtb": display_path(root, patched_dtb_path),
            "candidate_ap_tar_md5": display_path(root, candidate_ap_md5),
            "rollback_ap_tar_md5": display_path(root, rollback_ap_md5),
        },
        "hashes": {
            "stock_vendor_boot": vendor_boot_sha,
            "source_dtb": sha256_file(source_dtb),
            "patched_dtb": sha256_file(patched_dtb_path),
            "nochange_repack_vendor_boot": sha256_file(nochange_boot),
            "patched_vendor_boot": sha256_file(patched_boot),
            "candidate_vendor_boot_lz4": sha256_file(candidate_lz4),
            "candidate_ap_tar": sha256_file(candidate_ap_tar),
            "candidate_ap_tar_md5": sha256_file(candidate_ap_md5),
            "rollback_vendor_boot_lz4": sha256_file(rollback_lz4),
            "rollback_ap_tar": sha256_file(rollback_ap_tar),
            "rollback_ap_tar_md5": sha256_file(rollback_ap_md5),
        },
        "sizes": {
            "stock_vendor_boot": vendor_boot.stat().st_size,
            "source_dtb": len(source_dtb_bytes),
            "patched_dtb": len(patched_dtb_bytes),
            "dtb_size_delta": len(patched_dtb_bytes) - len(source_dtb_bytes),
            "nochange_repack_vendor_boot": nochange_boot.stat().st_size,
            "patched_vendor_boot": patched_boot.stat().st_size,
            "candidate_vendor_boot_lz4": candidate_lz4.stat().st_size,
            "candidate_ap_tar_md5": candidate_ap_md5.stat().st_size,
            "rollback_vendor_boot_lz4": rollback_lz4.stat().st_size,
            "rollback_ap_tar_md5": rollback_ap_md5.stat().st_size,
        },
        "evidence": {
            "dtb_patch": dtb_patch,
            "source_unpack": source_info,
            "nochange_repack": nochange_info,
            "patched_repack": patched_info,
            "nochange_repack_changed_byte_count": count_changed_bytes(stock_bytes, nochange_bytes),
            "patched_vs_nochange_changed_byte_count": count_changed_bytes(nochange_bytes, patched_bytes),
            "candidate_tar_members": candidate_members,
            "rollback_tar_members": rollback_members,
            "odin_parse_gate_candidate": candidate_parse_gate,
            "odin_parse_gate_rollback": rollback_parse_gate,
        },
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
