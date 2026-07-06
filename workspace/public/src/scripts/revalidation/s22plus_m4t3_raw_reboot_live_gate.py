#!/usr/bin/env python3
"""Guarded S22+ M4T3 raw reboot-download native-init live gate.

Dry-run is the default.  Live mode requires a fresh SHA-pinned AGENTS.md
exception and an explicit ack token.

M4T3 is built from the M4T2 proven raw-PID1 floor.  Its first action is one raw
arm64 reboot(2) syscall requesting "download".  If download mode reappears
after the candidate flash, the syscall path worked and rollback must run
immediately.  If no transport appears, the candidate may have parked after the
syscall returned; manual download-mode entry is then required before rollback.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

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


LIVE_ACK_TOKEN = "S22PLUS-M4T3-RAW-REBOOT-LIVE-GATE"
ROLLBACK_ACK_TOKEN = "S22PLUS-M4T3-ROLLBACK-FROM-DOWNLOAD"

EXPECTED_TARGET = "SM-S906N/g0q/S906NKSS7FYG8"
EXPECTED_M4T3_AP_SHA256 = "f0a26bb95a091070713f8d736419cbe60974195bb59509cb1fd7cc28a0b1a907"
EXPECTED_M4T3_BOOT_SHA256 = "d5e0371c6cb68af8990ce3ac4701ad4e0e487dbe54f4702dae29e21d86f4b92a"
EXPECTED_M4T3_BASE_BOOT_SHA256 = "2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e"
EXPECTED_M4T3_KERNEL_SHA256 = "bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff"
EXPECTED_M4T3_RAW_INIT_SHA256 = "e975a973395fd1bfe2fee0dccb9d47400e6746d62b508cd139b49c551b9aa67c"
EXPECTED_M4T3_MARKER = "S22_NATIVE_INIT_RAW_REBOOT_M4T3"

DEFAULT_M4T3_AP = Path("workspace/private/outputs/s22plus_native_init/inplace_m4t3_raw_reboot_v0_1/odin4/AP.tar.md5")
DEFAULT_M4T3_MANIFEST = Path("workspace/private/outputs/s22plus_native_init/inplace_m4t3_raw_reboot_v0_1/manifest.json")


def resolve_run_dir(root: Path, requested: Path | None) -> Path:
    if requested is not None:
        run_dir = requested
    else:
        stamp = utc_now().replace("-", "").replace(":", "").replace("Z", "Z")
        run_dir = DEFAULT_RUN_ROOT / f"s22plus_m4t3_raw_reboot_live_gate_{stamp}"
    run_dir = resolve(root, run_dir)
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def verify_agents_exception(root: Path, log_path: Path) -> None:
    agents = (root / "AGENTS.md").read_text(encoding="utf-8")
    normalized = " ".join(agents.split())
    required = [
        "S22+ M4T3 raw-reboot native-init boot-only",
        EXPECTED_M4T3_AP_SHA256,
        EXPECTED_M4T3_BOOT_SHA256,
        EXPECTED_M4T3_BASE_BOOT_SHA256,
        EXPECTED_M4T3_KERNEL_SHA256,
        EXPECTED_M4T3_RAW_INIT_SHA256,
        LIVE_ACK_TOKEN,
        ROLLBACK_ACK_TOKEN,
        "first candidate action is a single direct raw `reboot(..., \"download\")` syscall",
        "If that syscall returns, it must only park forever",
        "no libc startup",
        "no marker write",
    ]
    missing = [item for item in required if item not in normalized]
    append_log(log_path, f"agents_exception_missing={missing}")
    if missing:
        raise SystemExit(f"AGENTS.md missing M4T3 live authorization markers: {missing}")


def verify_m4t3_manifest(path: Path, log_path: Path) -> None:
    if not path.is_file():
        raise SystemExit(f"M4T3 manifest missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    hashes = data.get("hashes", {})
    safety = data.get("safety", {})
    ramdisk = data.get("ramdisk", {})
    raw_init = data.get("raw_init", {})
    tar_members_seen = data.get("tar_members")
    append_log(log_path, f"m4t3_manifest_path={path}")
    append_log(log_path, f"m4t3_manifest_hashes={json.dumps(hashes, sort_keys=True)}")
    append_log(log_path, f"m4t3_manifest_safety={json.dumps(safety, sort_keys=True)}")
    append_log(log_path, f"m4t3_manifest_ramdisk={json.dumps(ramdisk, sort_keys=True)}")
    append_log(log_path, f"m4t3_manifest_raw_init_file={raw_init.get('file', '')}")
    if hashes.get("ap_tar_md5") != EXPECTED_M4T3_AP_SHA256:
        raise SystemExit("M4T3 manifest AP hash does not match expected M4T3 AP")
    if hashes.get("boot_img") != EXPECTED_M4T3_BOOT_SHA256:
        raise SystemExit("M4T3 manifest boot image hash does not match expected M4T3 boot image")
    if hashes.get("base_boot") != EXPECTED_M4T3_BASE_BOOT_SHA256:
        raise SystemExit("M4T3 manifest base boot hash does not match expected known-booting Magisk boot")
    if hashes.get("kernel") != EXPECTED_M4T3_KERNEL_SHA256:
        raise SystemExit("M4T3 manifest kernel hash mismatch")
    if hashes.get("raw_reboot_init") != EXPECTED_M4T3_RAW_INIT_SHA256:
        raise SystemExit("M4T3 manifest raw init hash mismatch")
    if tar_members_seen != [EXPECTED_MEMBER]:
        raise SystemExit(f"M4T3 manifest tar members mismatch: {tar_members_seen!r}")
    required_safety = {
        "construction": "magiskboot unpack/repack; replace only ramdisk /init",
        "mkbootimg_from_scratch": False,
        "first_candidate_action": "raw-reboot-download-syscall",
        "libc": False,
        "intended_syscall_count": 1,
        "reboot_request": "download",
        "marker_write": False,
        "module_insertions": False,
        "configfs_runtime_gadget": False,
        "watchdog": "not-touched",
        "on_reboot_syscall_return": "infinite-park",
    }
    for key, expected in required_safety.items():
        if safety.get(key) != expected:
            raise SystemExit(f"M4T3 manifest {key} mismatch: {safety.get(key)!r} != {expected!r}")
    if safety.get("intended_syscalls") != ["reboot"]:
        raise SystemExit(f"M4T3 intended syscall list mismatch: {safety.get('intended_syscalls')!r}")
    if ramdisk.get("replaced_entry") != "init":
        raise SystemExit(f"M4T3 replaced ramdisk entry mismatch: {ramdisk.get('replaced_entry')!r}")


def wait_for_odin_absent(odin: Path, log_path: Path, label: str, wait_sec: int) -> bool:
    deadline = time.monotonic() + wait_sec
    while True:
        devices = odin_devices(odin, log_path, label)
        if not devices:
            append_log(log_path, f"{label}_odin_absent=1")
            return True
        if len(devices) > 1:
            raise SystemExit(f"refusing ambiguous Odin devices while waiting for disconnect: {devices}")
        if time.monotonic() >= deadline:
            append_log(log_path, f"{label}_odin_absent=0 still_present={devices}")
            return False
        time.sleep(1.0)


def observe_until_odin(run_dir: Path, log_path: Path, seconds: int, odin: Path) -> str | None:
    host_snapshot(run_dir, log_path, "after_candidate_flash", odin)
    deadline = time.monotonic() + seconds
    iteration = 0
    while time.monotonic() < deadline:
        iteration += 1
        label = f"m4t3_self_download_{iteration:03d}"
        host_snapshot(run_dir, log_path, label, odin)
        devices = odin_devices(odin, log_path, f"{label}-extra")
        if len(devices) == 1:
            append_log(log_path, f"m4t3_self_download_seen=1 device={devices[0]}")
            return devices[0]
        if len(devices) > 1:
            raise SystemExit(f"refusing ambiguous Odin devices during M4T3 observation: {devices}")
        rows = adb_rows(log_path, f"{label}-extra")
        if rows:
            append_log(log_path, f"m4t3_candidate_adb_rows={rows}")
        time.sleep(1.0)
    append_log(log_path, "m4t3_self_download_seen=0")
    return None


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
    collect_android_pstore(run_dir, log_path, "post_rollback", serial, marker=EXPECTED_M4T3_MARKER)
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m4t3-ap", type=Path, default=DEFAULT_M4T3_AP)
    parser.add_argument("--m4t3-manifest", type=Path, default=DEFAULT_M4T3_MANIFEST)
    parser.add_argument("--magisk-rollback-ap", type=Path, default=DEFAULT_MAGISK_ROLLBACK_AP)
    parser.add_argument("--stock-rollback-ap", type=Path, default=DEFAULT_STOCK_ROLLBACK_AP)
    parser.add_argument("--odin", type=Path, default=DEFAULT_ODIN)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--serial", help="ADB serial to pin before live flashing")
    parser.add_argument("--self-download-wait-sec", type=int, default=45)
    parser.add_argument("--post-flash-disconnect-wait-sec", type=int, default=20)
    parser.add_argument("--odin-wait-sec", type=int, default=90)
    parser.add_argument("--android-wait-sec", type=int, default=300)
    parser.add_argument("--rollback-target", choices=[ROLLBACK_MAGISK, ROLLBACK_STOCK], default=ROLLBACK_MAGISK)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--rollback-from-download", action="store_true")
    parser.add_argument("--ack")
    args = parser.parse_args(argv)

    if args.live and args.rollback_from_download:
        raise SystemExit("--live and --rollback-from-download are mutually exclusive")

    root = repo_root()
    run_dir = resolve_run_dir(root, args.run_dir)
    log_path = run_dir / "s22plus_m4t3_raw_reboot_live_gate.txt"
    append_log(log_path, f"=== {utc_now()} s22plus m4t3 raw-reboot live gate ===")
    append_log(log_path, f"target={EXPECTED_TARGET}")

    odin = resolve(root, args.odin)
    m4t3_ap = resolve(root, args.m4t3_ap)
    m4t3_manifest = resolve(root, args.m4t3_manifest)
    magisk_rollback_ap = resolve(root, args.magisk_rollback_ap)
    stock_rollback_ap = resolve(root, args.stock_rollback_ap)
    rollback_ap = magisk_rollback_ap if args.rollback_target == ROLLBACK_MAGISK else stock_rollback_ap
    if not odin.is_file():
        raise SystemExit(f"odin4 missing: {odin}")

    verify_agents_exception(root, log_path)
    verify_ap(m4t3_ap, EXPECTED_M4T3_AP_SHA256, "m4t3_candidate", log_path)
    verify_m4t3_manifest(m4t3_manifest, log_path)
    verify_ap(magisk_rollback_ap, EXPECTED_MAGISK_AP_SHA256, "magisk_boot_rollback", log_path)
    verify_ap(stock_rollback_ap, EXPECTED_STOCK_BOOT_AP_SHA256, "stock_boot_fallback", log_path)

    if args.rollback_from_download:
        if args.ack != ROLLBACK_ACK_TOKEN:
            raise SystemExit(f"--rollback-from-download requires --ack {ROLLBACK_ACK_TOKEN}")
        rc = rollback_from_download(odin, rollback_ap, run_dir, log_path, args.rollback_target, args.android_wait_sec)
        print(f"M4T3 rollback-from-download completed rc={rc}; log={log_path}")
        return rc

    selected_serial = require_current_android(log_path, args.serial)
    host_snapshot(run_dir, log_path, "dryrun_current", odin)

    if not args.live:
        print(f"dry-run ok: M4T3 candidate, rollback APs, AGENTS exception, and Android preflight verified; log={log_path}")
        return 0
    if args.ack != LIVE_ACK_TOKEN:
        raise SystemExit(f"--live requires --ack {LIVE_ACK_TOKEN}")

    reboot = run(["adb", "-s", selected_serial, "reboot", "download"], timeout=20.0)
    append_log(log_path, f"adb_reboot_download_rc={reboot.returncode}")
    append_log(log_path, reboot.stdout + reboot.stderr)
    odin_device = wait_for_odin(odin, log_path, "candidate-wait", args.odin_wait_sec)
    if odin_device is None:
        print("download mode did not appear for M4T3 candidate flash", file=sys.stderr)
        return 2

    candidate_rc = flash_ap(odin, m4t3_ap, odin_device, log_path, "candidate")
    if candidate_rc != 0:
        print(f"M4T3 candidate Odin flash failed rc={candidate_rc}; log={log_path}", file=sys.stderr)
        return candidate_rc or 3

    left_download = wait_for_odin_absent(odin, log_path, "post-candidate-disconnect", args.post_flash_disconnect_wait_sec)
    if not left_download:
        print(
            "M4T3 candidate flash completed but the original Odin device did not disconnect; "
            "rolling back without claiming self-download proof.",
            file=sys.stderr,
        )
        rollback_device = wait_for_odin(odin, log_path, "rollback-still-download-wait", 5)
        if rollback_device is None:
            print(f"rollback download mode unavailable after no-disconnect; manual recovery required. log={log_path}", file=sys.stderr)
            return 4
        rollback_rc = flash_ap(odin, rollback_ap, rollback_device, log_path, f"{args.rollback_target}_rollback_no_disconnect")
        if rollback_rc != 0:
            print(f"rollback Odin flash failed rc={rollback_rc}; log={log_path}", file=sys.stderr)
            return rollback_rc or 5
        post_rollback_serial = poll_android(log_path, args.android_wait_sec, expect_root=args.rollback_target == ROLLBACK_MAGISK)
        if post_rollback_serial is None:
            print(f"rollback transferred but Android/root verification failed; log={log_path}", file=sys.stderr)
            return 6
        append_log(log_path, "m4t3_result=no-proof-original-download-never-disconnected")
        collect_android_pstore(run_dir, log_path, "post_rollback_no_disconnect", post_rollback_serial, marker=EXPECTED_M4T3_MARKER)
        return 7

    print("M4T3 candidate flashed. Waiting for candidate's raw reboot-download syscall.")
    rollback_device = observe_until_odin(run_dir, log_path, args.self_download_wait_sec, odin)
    if rollback_device is None:
        print(
            "M4T3 self-download did not appear. If the device is parked, enter download mode manually "
            "and run --rollback-from-download.",
            file=sys.stderr,
        )
        return 4

    rollback_rc = flash_ap(odin, rollback_ap, rollback_device, log_path, f"{args.rollback_target}_rollback")
    if rollback_rc != 0 and args.rollback_target == ROLLBACK_MAGISK:
        append_log(log_path, "magisk_rollback_failed_attempting_stock_fallback=1")
        fallback_device = wait_for_odin(odin, log_path, "stock-fallback-wait", 30)
        if fallback_device:
            rollback_rc = flash_ap(odin, stock_rollback_ap, fallback_device, log_path, "stock_fallback")
    if rollback_rc != 0:
        print(f"rollback Odin flash failed rc={rollback_rc}; log={log_path}", file=sys.stderr)
        return rollback_rc or 5

    post_rollback_serial = poll_android(log_path, args.android_wait_sec, expect_root=args.rollback_target == ROLLBACK_MAGISK)
    if post_rollback_serial is None:
        print(f"rollback transferred but Android/root verification failed; log={log_path}", file=sys.stderr)
        return 6
    collect_android_pstore(run_dir, log_path, "post_rollback", post_rollback_serial, marker=EXPECTED_M4T3_MARKER)
    print(f"M4T3 live gate completed with self-download and rollback ok; log={log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
