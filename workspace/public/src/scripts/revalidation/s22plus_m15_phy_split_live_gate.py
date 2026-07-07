#!/usr/bin/env python3
"""Guarded S22+ M15 PHY-split add-back native-init live gate.

Default dry-run and live modes require a SHA-pinned AGENTS.md exception plus a
recovered rooted Android baseline. --offline-check verifies only the host-built
M15 package and rollback APs without touching any device.

M15 deliberately has no reboot beacon and no ACM-triggered download command.
If M15 parks or exposes ACM, rollback requires operator manual download-mode
entry followed by --rollback-from-download.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

from s22plus_m3_observable_live_gate import (
    DEFAULT_MAGISK_ROLLBACK_AP,
    DEFAULT_ODIN,
    DEFAULT_RUN_ROOT,
    DEFAULT_STOCK_ROLLBACK_AP,
    EXPECTED_MAGISK_AP_SHA256,
    EXPECTED_MEMBER,
    EXPECTED_STOCK_BOOT_AP_SHA256,
    ROLLBACK_MAGISK,
    ROLLBACK_STOCK,
    adb_rows,
    append_log,
    collect_android_pstore,
    flash_ap,
    host_snapshot,
    odin_devices,
    poll_android,
    repo_root,
    require_current_android,
    resolve,
    run,
    utc_now,
    verify_ap,
    wait_for_odin,
)
from s22plus_m5_usb_acm_live_gate import (
    acm_devices,
    read_acm_banner,
    verify_android_stability,
    verify_current_boot_hash,
)


LIVE_ACK_TOKEN = "S22PLUS-M15-PHY-SPLIT-LIVE-GATE"
ROLLBACK_ACK_TOKEN = "S22PLUS-M15-ROLLBACK-FROM-DOWNLOAD"

EXPECTED_TARGET = "SM-S906N/g0q/S906NKSS7FYG8"
EXPECTED_M15_AP_SHA256 = "16a4d526bbc0cb09bc63d61f4743d17dddb26c34047127fe610b1f677bddced2"
EXPECTED_M15_BOOT_SHA256 = "adaee20d490748aa1be555cdc7aa6828b9bc553185355a60183bd722119b5812"
EXPECTED_M15_BASE_BOOT_SHA256 = "2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e"
EXPECTED_M15_KERNEL_SHA256 = "bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff"
EXPECTED_M15_INIT_SHA256 = "5897fee141921dffc2848fb3eb3515a9b2d75d41e0c286448c4f0add06ab8558"
EXPECTED_M15_MODULE_LIST_SHA256 = "f3afe268a05c47492107227b224185c65f7757c004806c4c24d23231bd19e217"
EXPECTED_M15_SOURCE_SHA256 = "ac57cb1ece2dcc65bf5a8cbfc3fa0a077b006c757a4615298ee00d115b1fdd13"
EXPECTED_M15_MARKER = "S22_NATIVE_INIT_USB_ACM_M15"
EXPECTED_M15_USB_VENDOR = "04e8"
EXPECTED_M15_USB_PRODUCT = "685d"
EXPECTED_M15_USB_SERIAL = "S22M15ACM0001"
EXPECTED_M15_MODULES = [
    "phy-msm-ssusb-qmp.ko",
    "phy-msm-snps-eusb2.ko",
]

DEFAULT_M15_AP = Path("workspace/private/outputs/s22plus_native_init/inplace_m15_phy_split_v0_1/odin4/AP.tar.md5")
DEFAULT_M15_MANIFEST = Path("workspace/private/outputs/s22plus_native_init/inplace_m15_phy_split_v0_1/manifest.json")


def resolve_run_dir(root: Path, requested: Path | None) -> Path:
    if requested is not None:
        run_dir = resolve(root, requested)
        run_dir.mkdir(parents=True, exist_ok=False)
        return run_dir
    stamp = utc_now().replace("-", "").replace(":", "").replace("Z", "Z")
    base = resolve(root, DEFAULT_RUN_ROOT / f"s22plus_m15_phy_split_live_gate_{stamp}")
    for suffix in range(100):
        run_dir = base if suffix == 0 else Path(f"{base}_{suffix:02d}")
        try:
            run_dir.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            continue
        return run_dir
    raise SystemExit(f"could not allocate unique run directory under {base.parent}")


def verify_agents_exception(root: Path, log_path: Path) -> None:
    agents = (root / "AGENTS.md").read_text(encoding="utf-8")
    normalized = " ".join(agents.split())
    required = [
        "S22+ M15 PHY-split add-back native-init boot-only",
        EXPECTED_M15_AP_SHA256,
        EXPECTED_M15_BOOT_SHA256,
        EXPECTED_M15_BASE_BOOT_SHA256,
        EXPECTED_M15_KERNEL_SHA256,
        EXPECTED_M15_INIT_SHA256,
        EXPECTED_M15_MODULE_LIST_SHA256,
        EXPECTED_M15_SOURCE_SHA256,
        LIVE_ACK_TOKEN,
        ROLLBACK_ACK_TOKEN,
        "two PHY-side modules",
        "module_group=phy_split",
        "module_count=2",
        "s22plus_m15_phy_split.modules",
        *EXPECTED_M15_MODULES,
        "configfs",
        "role-force",
        "ss_acm.0",
        "a600000.dwc3",
        "never dummy_udc.0",
        "no reboot beacon",
        "park-vs-loop",
        "manual download-mode rollback",
    ]
    missing = [item for item in required if item not in normalized]
    append_log(log_path, f"agents_exception_missing={missing}")
    if missing:
        raise SystemExit(f"AGENTS.md missing M15 live authorization markers: {missing}")


def verify_m15_manifest(path: Path, log_path: Path) -> None:
    if not path.is_file():
        raise SystemExit(f"M15 manifest missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    hashes = data.get("hashes", {})
    safety = data.get("safety", {})
    ramdisk = data.get("ramdisk", {})
    m15_init = data.get("m15_init", {})
    tar_members_seen = data.get("tar_members")
    append_log(log_path, f"m15_manifest_path={path}")
    append_log(log_path, f"m15_manifest_hashes={json.dumps(hashes, sort_keys=True)}")
    append_log(log_path, f"m15_manifest_safety={json.dumps(safety, sort_keys=True)}")
    append_log(log_path, f"m15_manifest_ramdisk={json.dumps(ramdisk, sort_keys=True)}")

    if hashes.get("ap_tar_md5") != EXPECTED_M15_AP_SHA256:
        raise SystemExit("M15 manifest AP hash mismatch")
    if hashes.get("boot_img") != EXPECTED_M15_BOOT_SHA256:
        raise SystemExit("M15 manifest boot image hash mismatch")
    if hashes.get("base_boot") != EXPECTED_M15_BASE_BOOT_SHA256:
        raise SystemExit("M15 manifest base boot hash mismatch")
    if hashes.get("kernel") != EXPECTED_M15_KERNEL_SHA256:
        raise SystemExit("M15 manifest kernel hash mismatch")
    if hashes.get("m15_init") != EXPECTED_M15_INIT_SHA256:
        raise SystemExit("M15 manifest init hash mismatch")
    if hashes.get("m15_phy_split") != EXPECTED_M15_MODULE_LIST_SHA256:
        raise SystemExit("M15 manifest module-list hash mismatch")
    if hashes.get("source") != EXPECTED_M15_SOURCE_SHA256:
        raise SystemExit("M15 manifest source hash mismatch")
    if tar_members_seen != [EXPECTED_MEMBER]:
        raise SystemExit(f"M15 manifest tar members mismatch: {tar_members_seen!r}")

    required_safety: dict[str, Any] = {
        "boot_only": True,
        "host_only_build": True,
        "live_flash_authorized": False,
        "requires_new_sha_pinned_agents_exception_before_flash": True,
        "base_is_known_booting_magisk_boot": True,
        "construction": "magiskboot unpack/repack; replace ramdisk /init only",
        "runtime": "freestanding-raw-syscall",
        "glibc_static_startup": False,
        "mkbootimg_from_scratch": False,
        "no_android_or_magisk_handoff": True,
        "auto_reboot": False,
        "reboot_syscall": False,
        "host_commanded_reboot_download": False,
        "persistent_partition_mount": False,
        "block_device_writes": False,
        "module_insertions": "boot ramdisk gets text list only; runtime uses stock vendor_boot /lib/modules",
        "module_binary_injection": False,
        "module_list_path": "/s22plus_m15_phy_split.modules",
        "module_subset": "two-module PHY-side split from the failed M14 core group: phy-msm-ssusb-qmp, phy-msm-snps-eusb2",
        "configfs_runtime_gadget": "ss_acm.0 only",
        "udc_binding": "a600000.dwc3 only; never dummy_udc.0",
        "usb_role_force": "attempt /sys/class/usb_role/*/role=device",
        "watchdog": "not-touched-by-init-source; watchdog modules absent from M15 PHY-split subset",
        "observation_model": "park-vs-loop plus host ACM enumeration; no reboot beacon",
    }
    for key, expected in required_safety.items():
        if safety.get(key) != expected:
            raise SystemExit(f"M15 manifest safety {key} mismatch: {safety.get(key)!r} != {expected!r}")
    if ramdisk.get("replaced_entry") != "init":
        raise SystemExit("M15 manifest did not replace /init")
    if ramdisk.get("added_subset_entry") != "s22plus_m15_phy_split.modules":
        raise SystemExit("M15 manifest did not add the expected PHY-split module-list file")
    if ramdisk.get("module_list_files_injected_into_boot_ramdisk") != 1:
        raise SystemExit("M15 must inject exactly one module-list text file into boot ramdisk")
    if ramdisk.get("module_files_injected_into_boot_ramdisk") != 0:
        raise SystemExit("M15 must not inject vendor modules into boot ramdisk")

    phy_split = data.get("vendor_ramdisk", {}).get("m15_phy_split", {})
    if phy_split.get("subset_count") != 2:
        raise SystemExit(f"M15 module subset count mismatch: {phy_split.get('subset_count')!r}")
    if phy_split.get("subset") != EXPECTED_M15_MODULES:
        raise SystemExit(f"M15 module subset mismatch: {phy_split.get('subset')!r}")

    required_strings = set(m15_init.get("required_strings", []))
    for required in [
        EXPECTED_M15_MARKER,
        "/s22plus_m15_phy_split.modules",
        "module_list=boot_ramdisk_phy_split",
        "module_group=phy_split",
        "module_count=2",
        "module_source=stock_vendor_boot_ramdisk",
        "module_injection=list_only",
        "no_reboot_beacon=1",
        "acm_cmd_status=1",
        "a600000.dwc3",
        "role_force=device",
        "ss_acm.0",
        "ttyGS0",
        EXPECTED_M15_USB_SERIAL,
        "S22_NATIVE_INIT_USB_ACM_M15 READY",
        "S22_NATIVE_INIT_USB_ACM_M15 ACK status park",
    ]:
        if required not in required_strings:
            raise SystemExit(f"M15 required string missing from manifest: {required}")

    objdump = str(m15_init.get("objdump", ""))
    reboot_nr_lines = [
        line
        for line in objdump.splitlines()
        if "mov" in line and "x8" in line and "#0x8e" in line and "// #142" in line
    ]
    if reboot_nr_lines:
        raise SystemExit(f"M15 /init unexpectedly loads arm64 __NR_reboot: {reboot_nr_lines}")
    finit_nr_lines = [
        line
        for line in objdump.splitlines()
        if "mov" in line and "#0x111" in line and "// #273" in line
    ]
    if not finit_nr_lines:
        raise SystemExit("M15 /init must load arm64 __NR_finit_module (273)")

    init_path = path.parent / "build" / "s22plus_init_usb_acm_m15"
    if init_path.is_file():
        binary = init_path.read_bytes()
        for forbidden in (
            b"download",
            b"modules.load",
            b"modules.load.recovery",
            b"s22plus_m12_m5_floor.modules",
            b"s22plus_m11_park_usb.modules",
            b"/vendor_dlkm",
            b"ld-linux",
            b"libc.so",
        ):
            if forbidden in binary:
                raise SystemExit(f"M15 /init contains forbidden string: {forbidden!r}")
        append_log(log_path, f"m15_init_binary_checked={init_path}")


def is_m15_acm(device: dict[str, Any]) -> bool:
    model = str(device.get("model", ""))
    return (
        device.get("vendor") == EXPECTED_M15_USB_VENDOR
        and device.get("product") == EXPECTED_M15_USB_PRODUCT
    ) or device.get("serial") == EXPECTED_M15_USB_SERIAL or "S22_Native_Init_M15_ACM" in model


def observe_m15_acm(run_dir: Path, log_path: Path, seconds: int, odin: Path) -> tuple[str, str | None]:
    host_snapshot(run_dir, log_path, "after_candidate_flash", odin)
    deadline = time.monotonic() + seconds
    iteration = 0
    while time.monotonic() < deadline:
        iteration += 1
        label = f"m15_acm_observe_{iteration:03d}"
        if iteration == 1 or iteration % 5 == 0:
            host_snapshot(run_dir, log_path, label, odin)
        for device in acm_devices(log_path, label):
            if is_m15_acm(device):
                path = str(device["path"])
                payload = read_acm_banner(path, log_path)
                append_log(log_path, f"m15_acm_seen=1 path={path} banner_found={int(EXPECTED_M15_MARKER.encode('ascii') in payload)}")
                return ("acm", path)
        devices = odin_devices(odin, log_path, f"{label}-odin")
        if len(devices) == 1:
            append_log(log_path, f"m15_odin_returned=1 device={devices[0]}")
            return ("odin", devices[0])
        if len(devices) > 1:
            raise SystemExit(f"refusing ambiguous Odin devices during M15 observation: {devices}")
        rows = adb_rows(log_path, f"{label}-adb")
        usable = [row for row in rows if row[1] == "device"]
        if len(usable) == 1:
            append_log(log_path, f"m15_adb_returned=1 serial={usable[0][0]}")
            return ("adb", usable[0][0])
        if len(usable) > 1:
            raise SystemExit(f"refusing ambiguous ADB devices during M15 observation: {usable}")
        time.sleep(1.0)
    append_log(log_path, "m15_acm_seen=0")
    return ("none", None)


def rollback_from_download(odin: Path, rollback_ap: Path, run_dir: Path, log_path: Path, rollback_target: str, android_wait_sec: int) -> int:
    devices = odin_devices(odin, log_path, "rollback-only")
    if len(devices) != 1:
        raise SystemExit(f"rollback-only requires exactly one Odin device, got {devices}")
    rollback_rc = flash_ap(odin, rollback_ap, devices[0], log_path, f"{rollback_target}_rollback")
    if rollback_rc != 0:
        return rollback_rc or 5
    serial = poll_android(log_path, android_wait_sec, expect_root=rollback_target == ROLLBACK_MAGISK)
    if serial is None:
        return 6
    collect_android_pstore(run_dir, log_path, "post_rollback", serial, marker=EXPECTED_M15_MARKER)
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m15-ap", type=Path, default=DEFAULT_M15_AP)
    parser.add_argument("--m15-manifest", type=Path, default=DEFAULT_M15_MANIFEST)
    parser.add_argument("--magisk-rollback-ap", type=Path, default=DEFAULT_MAGISK_ROLLBACK_AP)
    parser.add_argument("--stock-rollback-ap", type=Path, default=DEFAULT_STOCK_ROLLBACK_AP)
    parser.add_argument("--odin", type=Path, default=DEFAULT_ODIN)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--serial", help="ADB serial to pin before live flashing")
    parser.add_argument("--acm-wait-sec", type=int, default=120)
    parser.add_argument("--odin-wait-sec", type=int, default=90)
    parser.add_argument("--android-wait-sec", type=int, default=300)
    parser.add_argument("--android-stability-samples", type=int, default=4)
    parser.add_argument("--android-stability-interval-sec", type=float, default=3.0)
    parser.add_argument("--rollback-target", choices=[ROLLBACK_MAGISK, ROLLBACK_STOCK], default=ROLLBACK_MAGISK)
    parser.add_argument("--offline-check", action="store_true")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--rollback-from-download", action="store_true")
    parser.add_argument("--ack")
    args = parser.parse_args(argv)

    modes = sum(1 for enabled in (args.offline_check, args.live, args.rollback_from_download) if enabled)
    if modes > 1:
        raise SystemExit("--offline-check, --live, and --rollback-from-download are mutually exclusive")

    root = repo_root()
    run_dir = resolve_run_dir(root, args.run_dir)
    log_path = run_dir / "s22plus_m15_phy_split_live_gate.txt"
    append_log(log_path, f"=== {utc_now()} s22plus m15 PHY-split live gate ===")
    append_log(log_path, f"target={EXPECTED_TARGET}")

    odin = resolve(root, args.odin)
    m15_ap = resolve(root, args.m15_ap)
    m15_manifest = resolve(root, args.m15_manifest)
    magisk_rollback_ap = resolve(root, args.magisk_rollback_ap)
    stock_rollback_ap = resolve(root, args.stock_rollback_ap)
    rollback_ap = magisk_rollback_ap if args.rollback_target == ROLLBACK_MAGISK else stock_rollback_ap
    if not odin.is_file():
        raise SystemExit(f"odin4 missing: {odin}")

    verify_ap(m15_ap, EXPECTED_M15_AP_SHA256, "m15_candidate", log_path)
    verify_m15_manifest(m15_manifest, log_path)
    verify_ap(magisk_rollback_ap, EXPECTED_MAGISK_AP_SHA256, "magisk_boot_rollback", log_path)
    verify_ap(stock_rollback_ap, EXPECTED_STOCK_BOOT_AP_SHA256, "stock_boot_fallback", log_path)

    if args.offline_check:
        append_log(log_path, "offline_check=ok device_action=0 agents_exception_checked=0 android_checked=0")
        print(f"offline-check ok: M15 candidate and rollback APs verified; no device action; log={log_path}")
        return 0

    verify_agents_exception(root, log_path)

    if args.rollback_from_download:
        if args.ack != ROLLBACK_ACK_TOKEN:
            raise SystemExit(f"--rollback-from-download requires --ack {ROLLBACK_ACK_TOKEN}")
        rc = rollback_from_download(odin, rollback_ap, run_dir, log_path, args.rollback_target, args.android_wait_sec)
        print(f"M15 rollback-from-download completed rc={rc}; log={log_path}")
        return rc

    selected_serial = require_current_android(log_path, args.serial)
    verify_android_stability(
        log_path,
        selected_serial,
        args.android_stability_samples,
        args.android_stability_interval_sec,
    )
    verify_current_boot_hash(log_path, selected_serial)
    host_snapshot(run_dir, log_path, "dryrun_current", odin)

    if not args.live:
        print(f"dry-run ok: M15 candidate, rollback APs, AGENTS exception, Android stability, and boot hash verified; log={log_path}")
        return 0
    if args.ack != LIVE_ACK_TOKEN:
        raise SystemExit(f"--live requires --ack {LIVE_ACK_TOKEN}")

    reboot = run(["adb", "-s", selected_serial, "reboot", "download"], timeout=20.0)
    append_log(log_path, f"adb_reboot_download_rc={reboot.returncode}")
    append_log(log_path, reboot.stdout + reboot.stderr)
    odin_device = wait_for_odin(odin, log_path, "candidate-wait", args.odin_wait_sec)
    if odin_device is None:
        print("download mode did not appear for M15 candidate flash", file=sys.stderr)
        return 2

    candidate_rc = flash_ap(odin, m15_ap, odin_device, log_path, "candidate")
    if candidate_rc != 0:
        print(f"M15 candidate Odin flash failed rc={candidate_rc}; log={log_path}", file=sys.stderr)
        return candidate_rc or 3

    print("M15 candidate flashed. Waiting for PHY-split ACM/park signal. No reboot beacon exists.")
    observed, endpoint = observe_m15_acm(run_dir, log_path, args.acm_wait_sec, odin)
    if observed == "acm" and endpoint:
        append_log(log_path, f"m15_result=acm_seen_manual_download_required endpoint={endpoint}")
        print(
            "M15 ACM appeared. This is the target signal, but M15 has no reboot/download command path; "
            "enter download mode manually and run --rollback-from-download.",
            file=sys.stderr,
        )
        return 4
    if observed == "odin":
        odin_device = endpoint
    elif observed == "adb" and endpoint:
        append_log(log_path, f"m15_unexpected_adb_returned={endpoint}")
        reboot_back = run(["adb", "-s", endpoint, "reboot", "download"], timeout=20.0)
        append_log(log_path, f"m15_unexpected_adb_reboot_download_rc={reboot_back.returncode}")
        append_log(log_path, reboot_back.stdout + reboot_back.stderr)
        odin_device = wait_for_odin(odin, log_path, "m15-unexpected-adb-rollback-wait", args.odin_wait_sec)
    else:
        append_log(log_path, "m15_result=no_acm_no_transport_manual_download_required")
        print("M15 ACM did not appear. Enter download mode manually and run --rollback-from-download.", file=sys.stderr)
        return 4
    if odin_device is None:
        print("M15 download mode did not appear; manual download rollback required.", file=sys.stderr)
        return 4

    rollback_rc = flash_ap(odin, rollback_ap, odin_device, log_path, f"{args.rollback_target}_rollback")
    if rollback_rc != 0 and args.rollback_target == ROLLBACK_MAGISK:
        append_log(log_path, "magisk_rollback_failed_attempting_stock_fallback=1")
        fallback_device = wait_for_odin(odin, log_path, "stock-fallback-wait", 30)
        if fallback_device:
            rollback_rc = flash_ap(odin, stock_rollback_ap, fallback_device, log_path, "stock_fallback")
    if rollback_rc != 0:
        return rollback_rc or 5

    post_rollback_serial = poll_android(log_path, args.android_wait_sec, expect_root=args.rollback_target == ROLLBACK_MAGISK)
    if post_rollback_serial is None:
        return 6
    collect_android_pstore(run_dir, log_path, "post_rollback", post_rollback_serial, marker=EXPECTED_M15_MARKER)
    print(f"M15 live gate completed and rollback ok; log={log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
