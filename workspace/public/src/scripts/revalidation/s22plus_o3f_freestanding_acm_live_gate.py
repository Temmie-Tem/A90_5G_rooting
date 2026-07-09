#!/usr/bin/env python3
"""Guarded S22+ O3F freestanding single-PID1 generic-ACM live gate."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import s22plus_o3_minimal_acm_live_gate as base


LIVE_ACK_TOKEN = "S22PLUS-O3F-FREESTANDING-ACM-LIVE-GATE"
ROLLBACK_ACK_TOKEN = "S22PLUS-O3F-FREESTANDING-ACM-ROLLBACK-FROM-DOWNLOAD"
ACTIVE_EXCEPTION_HEADING = (
    "**Narrow operator-authorized exception (2026-07-10, S22+ O3F freestanding "
    "single-PID1 generic-ACM boot-only live gate):**"
)

EXPECTED_TARGET = "SM-S906N/g0q/S906NKSS7FYG8"
EXPECTED_SCHEMA = "s22plus_o3f_freestanding_acm_live_v1"
EXPECTED_BUILD_SCHEMA = "s22plus_o3f_freestanding_acm_build_v1"
EXPECTED_MEMBER = "boot.img.lz4"
EXPECTED_BASE_BOOT_SHA256 = "2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e"
EXPECTED_PLAN_COUNT = 59
EXPECTED_GATE_COUNT = 8
EXPECTED_PLAN_TSV_SHA256 = "a34ebbad3b5d770f133e37a450cc3007e4a84ab831788484680e88aad6b3d534"
EXPECTED_PLAN_HEADER_SHA256 = "45727cff30952096d9604682a3ba3d284807a75e6622ed4c8ae57bc153d5b863"
EXPECTED_SOURCE_SHA256 = "2018eacff28dd6e897e9d6f4d6eabd712b74f076ecdbb6192f03c59455ccfa38"
EXPECTED_PROTOCOL_SHA256 = "3a53ebb9788b0ff23982ca2ed2bfc19cd27c5504f650660877868b588651403a"
EXPECTED_LOADER_SHA256 = "c4f5dd0f1bac4e4d614ae683b1bab7f1908dd337f5c0e244cab424c4cea556e8"
EXPECTED_INIT_SHA256 = "d181cee7818cdf0566a8f618d1f861b0bdabb36501ca95e87ad3681a370d2a16"
EXPECTED_RAMDISK_SHA256 = "db95044ab34ce088befb51ba934400059071c73be534be89249e64853d1052cd"
EXPECTED_BOOT_SHA256 = "c09ef0e8cbcb3b53c8ba22d76fce47cc03607ad416b0b8f2faf2adf1f18e9f70"
EXPECTED_BOOT_LZ4_SHA256 = "b25fff7af1d07fd0fd7799aac4ad1c8076f4fed7b7d8c64974cba5a2f5ecc922"
EXPECTED_AP_TAR_SHA256 = "067c658a3651239ba7b645ffb9fcfc674200e917bcacf9b1babfa7ceffda6c2c"
EXPECTED_AP_SHA256 = "73d0a03c066b236e8ebea07c03affda4c5b94633cc34dd2ca413ce8697eb8725"
EXPECTED_KERNEL_SHA256 = "bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff"
EXPECTED_USB_SERIAL = "S22O3FACM01"
EXPECTED_MARKER = "S22_NATIVE_INIT_O3F_FREESTANDING_ACM"

EXPECTED_MAGISK_AP_SHA256 = base.EXPECTED_MAGISK_AP_SHA256
EXPECTED_STOCK_BOOT_AP_SHA256 = base.EXPECTED_STOCK_BOOT_AP_SHA256
EXPECTED_STOCK_BOOT_RAW_SHA256 = base.EXPECTED_STOCK_BOOT_RAW_SHA256

DEFAULT_O3_ROOT = Path("workspace/private/outputs/s22plus_native_init/o3f_freestanding_acm_v0_1")
DEFAULT_O3_AP = DEFAULT_O3_ROOT / "odin4/AP.tar.md5"
DEFAULT_O3_MANIFEST = DEFAULT_O3_ROOT / "manifest.json"
REQUIRED_TIMELINE_PHASES = list(base.REQUIRED_TIMELINE_PHASES)


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def resolve_run_dir(root: Path, requested: Path | None) -> Path:
    if requested is not None:
        run_dir = base.resolve(root, requested)
        run_dir.mkdir(parents=True, exist_ok=False)
        return run_dir
    parent = base.resolve(root, base.DEFAULT_RUN_ROOT)
    candidate = parent / f"s22plus_o3f_freestanding_acm_live_gate_{utc_stamp()}"
    for suffix in range(100):
        run_dir = candidate if suffix == 0 else Path(f"{candidate}_{suffix:02d}")
        try:
            run_dir.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            continue
        return run_dir
    raise SystemExit(f"could not allocate run directory under {parent}")


def active_exception_segment(text: str) -> str:
    start = text.find(ACTIVE_EXCEPTION_HEADING)
    if start < 0:
        return ""
    end = text.find("\n   **", start + len(ACTIVE_EXCEPTION_HEADING))
    return text[start:] if end < 0 else text[start:end]


def policy_markers() -> list[str]:
    return [
        "S22+ O3F freestanding single-PID1 generic-ACM boot-only",
        "workspace/public/src/scripts/revalidation/s22plus_o3f_freestanding_acm_live_gate.py",
        LIVE_ACK_TOKEN,
        ROLLBACK_ACK_TOKEN,
        EXPECTED_TARGET,
        EXPECTED_AP_SHA256,
        EXPECTED_BOOT_SHA256,
        EXPECTED_INIT_SHA256,
        EXPECTED_SOURCE_SHA256,
        EXPECTED_PROTOCOL_SHA256,
        EXPECTED_PLAN_TSV_SHA256,
        EXPECTED_BASE_BOOT_SHA256,
        EXPECTED_MAGISK_AP_SHA256,
        EXPECTED_STOCK_BOOT_AP_SHA256,
        EXPECTED_STOCK_BOOT_RAW_SHA256,
        "128-request framed O0 protocol",
        "host close/reopen",
        "O3 STATUS",
        "mandatory boot-only rollback",
        "manual Download-mode entry",
        "a600000.ssusb/mode=peripheral",
        "a600000.dwc3",
        "no non-boot partition write",
    ]


def verify_agents_exception(root: Path, log_path: Path, *, allow_consumed: bool = False) -> None:
    segment = active_exception_segment((root / "AGENTS.md").read_text(encoding="utf-8"))
    normalized = " ".join(segment.split())
    missing = [marker for marker in policy_markers() if marker not in normalized]
    consumed = "Consumed exception" in segment or "Consumed/retired" in segment
    base.append_log(log_path, f"o3f_agents_exception_present={int(bool(segment))}")
    base.append_log(log_path, f"o3f_agents_exception_consumed={int(consumed)}")
    base.append_log(log_path, f"o3f_agents_exception_missing={missing}")
    if not segment or (consumed and not allow_consumed):
        raise SystemExit("active O3F AGENTS.md exception is absent or consumed")
    if missing:
        raise SystemExit(f"O3F AGENTS.md exception missing markers: {missing}")


def verify_manifest(path: Path, log_path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SystemExit(f"O3F manifest missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    hashes = data.get("hashes") or {}
    safety = data.get("safety") or {}
    plan = data.get("plan") or {}
    ramdisk = data.get("ramdisk") or {}
    expected_hashes = {
        "source": EXPECTED_SOURCE_SHA256,
        "protocol_header": EXPECTED_PROTOCOL_SHA256,
        "loader_header": EXPECTED_LOADER_SHA256,
        "base_boot": EXPECTED_BASE_BOOT_SHA256,
        "nochange_repack_boot": EXPECTED_BASE_BOOT_SHA256,
        "plan_tsv": EXPECTED_PLAN_TSV_SHA256,
        "plan_header": EXPECTED_PLAN_HEADER_SHA256,
        "o3f_init": EXPECTED_INIT_SHA256,
        "ramdisk_after": EXPECTED_RAMDISK_SHA256,
        "kernel": EXPECTED_KERNEL_SHA256,
        "boot_img": EXPECTED_BOOT_SHA256,
        "boot_img_lz4": EXPECTED_BOOT_LZ4_SHA256,
        "ap_tar": EXPECTED_AP_TAR_SHA256,
        "ap_tar_md5": EXPECTED_AP_SHA256,
    }
    for key, expected in expected_hashes.items():
        if hashes.get(key) != expected:
            raise SystemExit(f"O3F manifest hash mismatch {key}: {hashes.get(key)!r}")
    required_safety = {
        "boot_only": True,
        "host_only_build": True,
        "live_flash_authorized": False,
        "requires_new_sha_pinned_agents_exception_before_flash": True,
        "base_is_known_booting_magisk_boot": True,
        "kernel_changed": False,
        "mkbootimg_from_scratch": False,
        "runtime": "freestanding-raw-syscall",
        "glibc_static_startup": False,
        "protocol_in_pid1": True,
        "daemon_exec": False,
        "no_android_or_magisk_handoff": True,
        "auto_reboot": False,
        "reboot_syscall": False,
        "persistent_partition_mount": False,
        "block_device_writes": False,
        "module_binary_injection": False,
        "module_source": "stock vendor_boot /lib/modules",
        "configfs_runtime_gadget": "one generic acm.usb0 function",
        "udc_binding": "a600000.dwc3 only",
        "sysfs_write_allowlist": ["/sys/devices/platform/soc/a600000.ssusb/mode=peripheral"],
        "eud_enable": False,
        "sec_debug_trigger": False,
        "pmic_typec_power_write": False,
    }
    for key, expected in required_safety.items():
        if safety.get(key) != expected:
            raise SystemExit(f"O3F manifest safety mismatch {key}: {safety.get(key)!r}")
    if data.get("schema") != EXPECTED_BUILD_SCHEMA or data.get("target") != EXPECTED_TARGET:
        raise SystemExit("O3F manifest schema/target mismatch")
    if data.get("tar_members") != [EXPECTED_MEMBER]:
        raise SystemExit("O3F manifest is not a single-member boot AP")
    if plan.get("module_count") != EXPECTED_PLAN_COUNT or plan.get("tsv_sha256") != EXPECTED_PLAN_TSV_SHA256:
        raise SystemExit("O3F manifest module plan mismatch")
    if ramdisk.get("replaced_entry") != "init" or ramdisk.get("added_entries") != []:
        raise SystemExit("O3F manifest ramdisk delta mismatch")
    if ramdisk.get("module_files_injected") != 0:
        raise SystemExit("O3F manifest unexpectedly injects module binaries")
    base.append_log(log_path, f"o3f_manifest_hashes={json.dumps(hashes, sort_keys=True)}")
    return data


def verify_artifacts(
    *,
    root: Path,
    out_root: Path,
    candidate_ap: Path,
    manifest_path: Path,
    magisk_rollback_ap: Path,
    stock_rollback_ap: Path,
    log_path: Path,
) -> dict[str, Any]:
    base.verify_ap(candidate_ap, EXPECTED_AP_SHA256, "o3f_candidate", log_path)
    manifest = verify_manifest(manifest_path, log_path)
    base.verify_ap(magisk_rollback_ap, EXPECTED_MAGISK_AP_SHA256, "magisk_boot_rollback", log_path)
    base.verify_ap(stock_rollback_ap, EXPECTED_STOCK_BOOT_AP_SHA256, "stock_boot_fallback", log_path)
    files = {
        "boot_img": (out_root / "boot.img", EXPECTED_BOOT_SHA256),
        "boot_img_lz4": (out_root / "odin4/boot.img.lz4", EXPECTED_BOOT_LZ4_SHA256),
        "ap_tar": (out_root / "odin4/AP.tar", EXPECTED_AP_TAR_SHA256),
        "o3f_init": (out_root / "build/init", EXPECTED_INIT_SHA256),
        "plan_tsv": (out_root / "build/plan/module-plan.tsv", EXPECTED_PLAN_TSV_SHA256),
        "plan_header": (out_root / "build/plan/module-plan.generated.h", EXPECTED_PLAN_HEADER_SHA256),
        "source": (
            root / "workspace/public/src/native-init/s22plus_init_o3f_freestanding_acm.c",
            EXPECTED_SOURCE_SHA256,
        ),
        "protocol": (
            root / "workspace/public/src/native-init/s22plus_o3_freestanding_protocol.h",
            EXPECTED_PROTOCOL_SHA256,
        ),
    }
    for label, (artifact, expected) in files.items():
        if not artifact.is_file() or base.sha256_file(artifact) != expected:
            raise SystemExit(f"O3F artifact mismatch {label}: {artifact}")
    return manifest


def status_reasons(values: dict[str, str]) -> list[str]:
    expected = {
        "marker": EXPECTED_MARKER,
        "version": "0.2",
        "phase": "control-ready",
        "result": "ready",
        "rc": "0",
        "plan_count": str(EXPECTED_PLAN_COUNT),
        "module_attempted": str(EXPECTED_PLAN_COUNT),
        "module_failed": "0",
        "proc_registration_rc": "0",
        "proc_eof": "1",
        "proc_found": str(EXPECTED_PLAN_COUNT),
        "gate_mask": "0xff",
        "gate_count": str(EXPECTED_GATE_COUNT),
        "configfs_rc": "0",
        "ssusb_mode_write_rc": "0",
        "ssusb_mode_readback_ok": "1",
        "udc_bind_rc": "0",
        "udc_readback_ok": "1",
        "ttyGS0_ready": "1",
        "gadget_function": "acm.usb0",
        "udc": "a600000.dwc3",
        "protocol_result": "pass",
        "protocol_handled": "128",
        "protocol_invalid": "0",
        "protocol_crc_errors": "0",
        "protocol_seq_errors": "0",
    }
    reasons = [
        f"{key}-mismatch:{values.get(key)!r}"
        for key, expected_value in expected.items()
        if values.get(key) != expected_value
    ]
    try:
        if int(values.get("module_loaded", "-1")) + int(values.get("module_eexist", "-1")) != EXPECTED_PLAN_COUNT:
            reasons.append("module-loaded-plus-eexist-mismatch")
    except ValueError:
        reasons.append("module-loaded-or-eexist-not-integer")
    return reasons


def configure_base() -> None:
    replacements = {
        "LIVE_ACK_TOKEN": LIVE_ACK_TOKEN,
        "ROLLBACK_ACK_TOKEN": ROLLBACK_ACK_TOKEN,
        "ACTIVE_EXCEPTION_HEADING": ACTIVE_EXCEPTION_HEADING,
        "EXPECTED_TARGET": EXPECTED_TARGET,
        "EXPECTED_SCHEMA": EXPECTED_SCHEMA,
        "EXPECTED_BASE_BOOT_SHA256": EXPECTED_BASE_BOOT_SHA256,
        "EXPECTED_PLAN_COUNT": EXPECTED_PLAN_COUNT,
        "EXPECTED_GATE_COUNT": EXPECTED_GATE_COUNT,
        "EXPECTED_PLAN_TSV_SHA256": EXPECTED_PLAN_TSV_SHA256,
        "EXPECTED_PLAN_HEADER_SHA256": EXPECTED_PLAN_HEADER_SHA256,
        "EXPECTED_INIT_SHA256": EXPECTED_INIT_SHA256,
        "EXPECTED_BOOT_SHA256": EXPECTED_BOOT_SHA256,
        "EXPECTED_BOOT_LZ4_SHA256": EXPECTED_BOOT_LZ4_SHA256,
        "EXPECTED_AP_SHA256": EXPECTED_AP_SHA256,
        "EXPECTED_KERNEL_SHA256": EXPECTED_KERNEL_SHA256,
        "EXPECTED_USB_SERIAL": EXPECTED_USB_SERIAL,
        "EXPECTED_MARKER": EXPECTED_MARKER,
        "DEFAULT_O3_ROOT": DEFAULT_O3_ROOT,
        "DEFAULT_O3_AP": DEFAULT_O3_AP,
        "DEFAULT_O3_MANIFEST": DEFAULT_O3_MANIFEST,
        "REQUIRED_TIMELINE_PHASES": REQUIRED_TIMELINE_PHASES,
        "resolve_run_dir": resolve_run_dir,
        "policy_markers": policy_markers,
        "verify_agents_exception": verify_agents_exception,
        "verify_manifest": verify_manifest,
        "verify_artifacts": verify_artifacts,
        "status_reasons": status_reasons,
    }
    for name, value in replacements.items():
        setattr(base, name, value)


def validate_live_tokens(args: argparse.Namespace) -> None:
    configure_base()
    base.validate_live_tokens(args)


def main(argv: list[str]) -> int:
    configure_base()
    return base.main(argv)


configure_base()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
