#!/usr/bin/env python3
"""Guarded S22+ M4T1 in-place MagiskBoot native-init live gate.

Dry-run is the default.  Live mode requires:

- the exact SHA-pinned M4T1 AGENTS.md exception;
- exact M4T1 boot-only AP hash and single `boot.img.lz4` tar member;
- exact pinned Magisk boot-only rollback AP and stock boot-only fallback AP;
- a single normal Android ADB target matching SM-S906N/g0q/S906NKSS7FYG8;
- an explicit ack token.

M4T1 preserves the known-booting Magisk boot construction path with magiskboot
and replaces only ramdisk `/init` with the instant-download native init.  If
download mode reappears after the candidate flash, the boot image was accepted,
the kernel executed custom `/init`, and rollback must run immediately.
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


ACK_TOKEN = "S22PLUS-M4T1-INPLACE-LIVE-GATE"

EXPECTED_TARGET = "SM-S906N/g0q/S906NKSS7FYG8"
EXPECTED_M4T1_AP_SHA256 = "9f5b4c48b95b710f742d5ea8c7f16ef4802cf27e78469381073d460361d0451c"
EXPECTED_M4T1_BOOT_SHA256 = "9ce597e4ba920f1331937dbe4736f923728ff5502b02c02dea8357b3a9d5b9d1"
EXPECTED_M4T1_BASE_BOOT_SHA256 = "2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e"
EXPECTED_M4T1_KERNEL_SHA256 = "bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff"
EXPECTED_M4T1_MARKER = "S22_NATIVE_INIT_INSTANT_DOWNLOAD_M4T0"

DEFAULT_M4T1_AP = Path("workspace/private/outputs/s22plus_native_init/inplace_m4t1_magiskboot_v0_1/odin4/AP.tar.md5")
DEFAULT_M4T1_MANIFEST = Path("workspace/private/outputs/s22plus_native_init/inplace_m4t1_magiskboot_v0_1/manifest.json")


def resolve_run_dir(root: Path, requested: Path | None) -> Path:
    if requested is not None:
        run_dir = requested
    else:
        stamp = utc_now().replace("-", "").replace(":", "").replace("Z", "Z")
        run_dir = DEFAULT_RUN_ROOT / f"s22plus_m4t1_inplace_live_gate_{stamp}"
    run_dir = resolve(root, run_dir)
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def verify_agents_exception(root: Path, log_path: Path) -> None:
    agents = (root / "AGENTS.md").read_text(encoding="utf-8")
    normalized = " ".join(agents.split())
    required = [
        "S22+ M4T1 in-place MagiskBoot native-init boot-only",
        EXPECTED_M4T1_AP_SHA256,
        EXPECTED_M4T1_BOOT_SHA256,
        ACK_TOKEN,
        EXPECTED_M4T1_MARKER,
        EXPECTED_M4T1_BASE_BOOT_SHA256,
        EXPECTED_M4T1_KERNEL_SHA256,
        "known-booting Magisk boot",
        "magiskboot unpack/repack",
        "first candidate action must be `reboot(..., \"download\")`",
        "no marker before the reboot syscall",
    ]
    missing = [item for item in required if item not in normalized]
    append_log(log_path, f"agents_exception_missing={missing}")
    if missing:
        raise SystemExit(f"AGENTS.md missing M4T1 live authorization markers: {missing}")


def verify_m4t1_manifest(path: Path, log_path: Path) -> None:
    if not path.is_file():
        raise SystemExit(f"M4T1 manifest missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    hashes = data.get("hashes", {})
    safety = data.get("safety", {})
    ramdisk = data.get("ramdisk", {})
    magiskboot = data.get("magiskboot", {})
    tar_members_seen = data.get("tar_members")
    append_log(log_path, f"m4t1_manifest_path={path}")
    append_log(log_path, f"m4t1_manifest_hashes={json.dumps(hashes, sort_keys=True)}")
    append_log(log_path, f"m4t1_manifest_safety={json.dumps(safety, sort_keys=True)}")
    append_log(log_path, f"m4t1_manifest_ramdisk={json.dumps(ramdisk, sort_keys=True)}")
    append_log(log_path, f"m4t1_manifest_magiskboot={json.dumps(magiskboot, sort_keys=True)}")
    if hashes.get("ap_tar_md5") != EXPECTED_M4T1_AP_SHA256:
        raise SystemExit("M4T1 manifest AP hash does not match expected M4T1 AP")
    if hashes.get("boot_img") != EXPECTED_M4T1_BOOT_SHA256:
        raise SystemExit("M4T1 manifest boot image hash does not match expected M4T1 boot image")
    if hashes.get("base_boot") != EXPECTED_M4T1_BASE_BOOT_SHA256:
        raise SystemExit("M4T1 manifest base boot hash does not match expected known-booting Magisk boot")
    if hashes.get("kernel") != EXPECTED_M4T1_KERNEL_SHA256:
        raise SystemExit("M4T1 manifest kernel hash does not match expected Magisk-patched kernel")
    if tar_members_seen != [EXPECTED_MEMBER]:
        raise SystemExit(f"M4T1 manifest tar members mismatch: {tar_members_seen!r}")
    if safety.get("construction") != "magiskboot unpack/repack; replace only ramdisk /init":
        raise SystemExit(f"M4T1 construction mismatch: {safety.get('construction')!r}")
    if safety.get("mkbootimg_from_scratch") is not False:
        raise SystemExit(f"M4T1 mkbootimg_from_scratch mismatch: {safety.get('mkbootimg_from_scratch')!r}")
    if safety.get("first_candidate_action") != "reboot-download":
        raise SystemExit(f"M4T1 first_candidate_action mismatch: {safety.get('first_candidate_action')!r}")
    if safety.get("marker_before_reboot") is not False:
        raise SystemExit(f"M4T1 manifest marker_before_reboot mismatch: {safety.get('marker_before_reboot')!r}")
    if safety.get("module_insertions") is not False:
        raise SystemExit(f"M4T1 manifest module_insertions mismatch: {safety.get('module_insertions')!r}")
    if safety.get("configfs_runtime_gadget") is not False:
        raise SystemExit(f"M4T1 manifest configfs_runtime_gadget mismatch: {safety.get('configfs_runtime_gadget')!r}")
    if safety.get("watchdog") != "not-touched":
        raise SystemExit(f"M4T1 manifest watchdog mismatch: {safety.get('watchdog')!r}")
    if ramdisk.get("replaced_entry") != "init":
        raise SystemExit(f"M4T1 replaced ramdisk entry mismatch: {ramdisk.get('replaced_entry')!r}")
    if magiskboot.get("nochange_repack_byte_identical") is not True:
        raise SystemExit("M4T1 no-change MagiskBoot repack was not byte-identical")


def observe_until_odin(run_dir: Path, log_path: Path, seconds: int, odin: Path) -> str | None:
    host_snapshot(run_dir, log_path, "after_candidate_flash", odin)
    deadline = time.monotonic() + seconds
    iteration = 0
    while time.monotonic() < deadline:
        iteration += 1
        label = f"m4t1_self_download_{iteration:03d}"
        host_snapshot(run_dir, log_path, label, odin)
        devices = odin_devices(odin, log_path, f"{label}-extra")
        if len(devices) == 1:
            append_log(log_path, f"m4t1_self_download_seen=1 device={devices[0]}")
            return devices[0]
        if len(devices) > 1:
            raise SystemExit(f"refusing ambiguous Odin devices during M4T1 observation: {devices}")
        rows = adb_rows(log_path, f"{label}-extra")
        if rows:
            append_log(log_path, f"m4t1_candidate_adb_rows={rows}")
        time.sleep(1.0)
    append_log(log_path, "m4t1_self_download_seen=0")
    return None


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


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m4t1-ap", type=Path, default=DEFAULT_M4T1_AP)
    parser.add_argument("--m4t1-manifest", type=Path, default=DEFAULT_M4T1_MANIFEST)
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
    parser.add_argument("--ack", help=f"required with --live: {ACK_TOKEN}")
    args = parser.parse_args(argv)

    root = repo_root()
    run_dir = resolve_run_dir(root, args.run_dir)
    log_path = run_dir / "s22plus_m4t1_inplace_live_gate.txt"
    append_log(log_path, f"=== {utc_now()} s22plus m4t1 in-place live gate ===")
    append_log(log_path, f"target={EXPECTED_TARGET}")

    odin = resolve(root, args.odin)
    m4t1_ap = resolve(root, args.m4t1_ap)
    m4t1_manifest = resolve(root, args.m4t1_manifest)
    magisk_rollback_ap = resolve(root, args.magisk_rollback_ap)
    stock_rollback_ap = resolve(root, args.stock_rollback_ap)
    if not odin.is_file():
        raise SystemExit(f"odin4 missing: {odin}")

    verify_agents_exception(root, log_path)
    verify_ap(m4t1_ap, EXPECTED_M4T1_AP_SHA256, "m4t1_candidate", log_path)
    verify_m4t1_manifest(m4t1_manifest, log_path)
    verify_ap(magisk_rollback_ap, EXPECTED_MAGISK_AP_SHA256, "magisk_boot_rollback", log_path)
    verify_ap(stock_rollback_ap, EXPECTED_STOCK_BOOT_AP_SHA256, "stock_boot_fallback", log_path)
    selected_serial = require_current_android(log_path, args.serial)
    host_snapshot(run_dir, log_path, "dryrun_current", odin)

    if not args.live:
        print(f"dry-run ok: M4T1 candidate, rollback APs, AGENTS exception, and Android preflight verified; log={log_path}")
        return 0
    if args.ack != ACK_TOKEN:
        raise SystemExit(f"--live requires --ack {ACK_TOKEN}")

    reboot = run(["adb", "-s", selected_serial, "reboot", "download"], timeout=20.0)
    append_log(log_path, f"adb_reboot_download_rc={reboot.returncode}")
    append_log(log_path, reboot.stdout + reboot.stderr)
    odin_device = wait_for_odin(odin, log_path, "candidate-wait", args.odin_wait_sec)
    if odin_device is None:
        print("download mode did not appear for M4T1 candidate flash", file=sys.stderr)
        return 2

    candidate_rc = flash_ap(odin, m4t1_ap, odin_device, log_path, "candidate")
    if candidate_rc != 0:
        print(f"M4T1 candidate Odin flash failed rc={candidate_rc}; log={log_path}", file=sys.stderr)
        return candidate_rc or 3

    left_download = wait_for_odin_absent(odin, log_path, "post-candidate-disconnect", args.post_flash_disconnect_wait_sec)
    if not left_download:
        print(
            "M4T1 candidate flash completed but the original Odin device did not disconnect; "
            "rolling back without claiming self-download proof.",
            file=sys.stderr,
        )
        rollback_device = wait_for_odin(odin, log_path, "rollback-still-download-wait", 5)
        if rollback_device is None:
            print(f"rollback download mode unavailable after no-disconnect; manual recovery required. log={log_path}", file=sys.stderr)
            return 4
        rollback_ap = magisk_rollback_ap if args.rollback_target == ROLLBACK_MAGISK else stock_rollback_ap
        rollback_label = f"{args.rollback_target}_rollback_no_disconnect"
        rollback_rc = flash_ap(odin, rollback_ap, rollback_device, log_path, rollback_label)
        if rollback_rc != 0:
            print(f"rollback Odin flash failed rc={rollback_rc}; log={log_path}", file=sys.stderr)
            return rollback_rc or 5
        post_rollback_serial = poll_android(log_path, args.android_wait_sec, expect_root=args.rollback_target == ROLLBACK_MAGISK)
        if post_rollback_serial is None:
            print(f"rollback transferred but Android/root verification failed; log={log_path}", file=sys.stderr)
            return 6
        append_log(log_path, "m4t1_result=no-proof-original-download-never-disconnected")
        collect_android_pstore(run_dir, log_path, "post_rollback_no_disconnect", post_rollback_serial, marker=EXPECTED_M4T1_MARKER)
        return 7

    print("M4T1 candidate flashed. Waiting for candidate's first-action download reboot.")
    rollback_device = observe_until_odin(run_dir, log_path, args.self_download_wait_sec, odin)
    if rollback_device is None:
        print(f"M4T1 self-download did not appear; manual download-mode recovery required. log={log_path}", file=sys.stderr)
        return 4

    rollback_ap = magisk_rollback_ap if args.rollback_target == ROLLBACK_MAGISK else stock_rollback_ap
    rollback_label = f"{args.rollback_target}_rollback"
    rollback_rc = flash_ap(odin, rollback_ap, rollback_device, log_path, rollback_label)
    if rollback_rc != 0 and args.rollback_target == ROLLBACK_MAGISK:
        append_log(log_path, "magisk_rollback_failed_attempting_stock_fallback=1")
        fallback_device = wait_for_odin(odin, log_path, "stock-fallback-wait", 30)
        if fallback_device:
            rollback_rc = flash_ap(odin, stock_rollback_ap, fallback_device, log_path, "stock_fallback")
    if rollback_rc != 0:
        print(f"rollback Odin flash failed rc={rollback_rc}; log={log_path}", file=sys.stderr)
        return rollback_rc or 5

    expect_root = args.rollback_target == ROLLBACK_MAGISK
    post_rollback_serial = poll_android(log_path, args.android_wait_sec, expect_root=expect_root)
    android_ok = post_rollback_serial is not None
    append_log(log_path, f"post_rollback_android_ok={int(android_ok)} expect_root={int(expect_root)}")
    if not android_ok:
        print(f"rollback transferred but Android/root verification failed; log={log_path}", file=sys.stderr)
        return 6
    collect_android_pstore(run_dir, log_path, "post_rollback", post_rollback_serial, marker=EXPECTED_M4T1_MARKER)
    print(f"M4T1 live gate completed with self-download and rollback ok; log={log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
