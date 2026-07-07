#!/usr/bin/env python3
"""Guarded S22+ ramoops-DTBO + M22 sysrq-panic retained-console gate.

Default dry-run and device modes require a future SHA-pinned AGENTS.md
exception. --offline-check verifies only the pinned DTBO/M22 packages and
rollback APs without touching a connected device.

Intended live flow, once separately authorized:
1. flash the patched DTBO that enables the live ramoops overlay;
2. require Android/root to return and verify DTBO hash plus live status=okay;
3. flash the M22 boot candidate that writes /dev/kmsg and triggers sysrq-c;
4. observe for ADB/Odin/no-transport evidence;
5. roll boot back to Magisk, collect pstore/last_kmsg, then restore stock DTBO.
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
    EXPECTED_STOCK_BOOT_AP_SHA256,
    ROLLBACK_MAGISK,
    ROLLBACK_STOCK,
    adb_rows,
    adb_shell,
    append_log,
    collect_android_pstore,
    flash_ap,
    host_snapshot,
    odin_devices,
    repo_root,
    require_current_android,
    resolve,
    utc_now,
    wait_for_odin,
)
from s22plus_m5_usb_acm_live_gate import verify_android_stability
from s22plus_ramoops_dtbo_m18_capture_live_gate import (
    DEFAULT_DTBO_CANDIDATE_AP,
    DEFAULT_DTBO_MANIFEST,
    DEFAULT_DTBO_ROLLBACK_AP,
    EXPECTED_BOOT_MEMBER,
    EXPECTED_DTBO_CANDIDATE_AP_SHA256,
    EXPECTED_DTBO_ROLLBACK_AP_SHA256,
    EXPECTED_PATCHED_DTBO_RAW_SHA256,
    EXPECTED_STOCK_DTBO_RAW_SHA256,
    EXPECTED_TARGET,
    RESTORE_DTBO_ACK_TOKEN,
    reboot_android_to_download,
    verify_dtbo_manifest,
    wait_for_android_root,
)
from s22plus_ramoops_dtbo_status_live_gate import (
    read_current_dtbo_hash,
    restore_after_patched_android_failure,
    restore_after_patched_android_timeout,
    restore_dtbo_from_download,
    verify_ap_member,
    verify_current_dtbo_hash,
    verify_live_ramoops_status,
)


LIVE_ACK_TOKEN = "S22PLUS-RAMOOPS-DTBO-M22-SYSRQ-PANIC-LIVE-GATE"
ROLLBACK_BOOT_ACK_TOKEN = "S22PLUS-RAMOOPS-M22-ROLLBACK-BOOT-FROM-DOWNLOAD"

EXPECTED_M22_LABEL = "M22_KMSG_SYSRQ_PANIC"
EXPECTED_M22_AP_SHA256 = "77c17e9d3fb62319823499e0e8e7fcd485cd180dd730e40d9c2a8112308c4852"
EXPECTED_M22_BOOT_SHA256 = "c79bbe1fb1cee7d7e3c70ff4c249d6e0359760e203cc0bebb1c71d6cc0518802"
EXPECTED_M22_BASE_BOOT_SHA256 = "2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e"
EXPECTED_M22_KERNEL_SHA256 = "bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff"
EXPECTED_M22_INIT_SHA256 = "2b711b0fccf6cdd9b4c9beb5ba2f1a095d4e873b42bd03a02eb4655106873831"
EXPECTED_M22_SOURCE_SHA256 = "a48818067b6b79578bdc6cd0e327d9e7c316b10bca1be7d838605c7d7e0e6444"
EXPECTED_M22_MARKER = "S22_NATIVE_INIT_M22_KMSG_SYSRQ_PANIC"

DEFAULT_M22_AP = Path("workspace/private/outputs/s22plus_native_init/m22_kmsg_sysrq_panic_v0_1/odin4/AP.tar.md5")
DEFAULT_M22_MANIFEST = Path("workspace/private/outputs/s22plus_native_init/m22_kmsg_sysrq_panic_v0_1/manifest.json")


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


def resolve_run_dir(root: Path, requested: Path | None) -> Path:
    if requested is not None:
        run_dir = resolve(root, requested)
        run_dir.mkdir(parents=True, exist_ok=False)
        return run_dir
    stamp = utc_now().replace("-", "").replace(":", "").replace("Z", "Z")
    base = resolve(root, DEFAULT_RUN_ROOT / f"s22plus_ramoops_dtbo_m22_sysrq_panic_{stamp}")
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
        "S22+ ramoops DTBO + M22 sysrq-panic retained-console",
        "workspace/public/src/scripts/revalidation/s22plus_ramoops_dtbo_m22_sysrq_panic_live_gate.py",
        EXPECTED_DTBO_CANDIDATE_AP_SHA256,
        EXPECTED_DTBO_ROLLBACK_AP_SHA256,
        EXPECTED_PATCHED_DTBO_RAW_SHA256,
        EXPECTED_STOCK_DTBO_RAW_SHA256,
        EXPECTED_M22_AP_SHA256,
        EXPECTED_M22_BOOT_SHA256,
        EXPECTED_M22_BASE_BOOT_SHA256,
        EXPECTED_M22_KERNEL_SHA256,
        EXPECTED_M22_INIT_SHA256,
        EXPECTED_M22_SOURCE_SHA256,
        EXPECTED_MAGISK_AP_SHA256,
        EXPECTED_STOCK_BOOT_AP_SHA256,
        LIVE_ACK_TOKEN,
        ROLLBACK_BOOT_ACK_TOKEN,
        RESTORE_DTBO_ACK_TOKEN,
        "dtbo.img.lz4",
        "boot.img.lz4",
        "ramoops_region/status=okay",
        EXPECTED_M22_LABEL,
        EXPECTED_M22_MARKER,
        "intentional kernel crash",
        "sysrq-trigger-c",
        "restore stock DTBO",
        "manual download-mode",
        "no vendor_boot",
    ]
    missing = [item for item in required if item not in normalized]
    append_log(log_path, f"agents_exception_missing={missing}")
    if missing:
        raise SystemExit(f"AGENTS.md missing ramoops DTBO + M22 authorization markers: {missing}")


def verify_m22_manifest(path: Path, log_path: Path) -> None:
    if not path.is_file():
        raise SystemExit(f"M22 manifest missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    hashes = data.get("hashes", {})
    safety = data.get("safety", {})
    init_info = data.get("init", {})
    ramdisk = data.get("ramdisk", {})
    tar_members_seen = data.get("tar_members")
    append_log(log_path, f"m22_manifest_path={path}")
    append_log(log_path, f"m22_manifest_hashes={json.dumps(hashes, sort_keys=True)}")
    append_log(log_path, f"m22_manifest_safety={json.dumps(safety, sort_keys=True)}")
    append_log(log_path, f"m22_manifest_ramdisk={json.dumps(ramdisk, sort_keys=True)}")
    append_log(log_path, f"m22_manifest_init_file={init_info.get('file', '')}")

    if data.get("label") != EXPECTED_M22_LABEL:
        raise SystemExit(f"M22 manifest label mismatch: {data.get('label')!r}")
    required_hashes = {
        "ap_tar_md5": EXPECTED_M22_AP_SHA256,
        "boot_img": EXPECTED_M22_BOOT_SHA256,
        "base_boot": EXPECTED_M22_BASE_BOOT_SHA256,
        "kernel": EXPECTED_M22_KERNEL_SHA256,
        "init": EXPECTED_M22_INIT_SHA256,
        "source": EXPECTED_M22_SOURCE_SHA256,
    }
    for key, expected in required_hashes.items():
        if hashes.get(key) != expected:
            raise SystemExit(f"M22 manifest hash {key} mismatch: {hashes.get(key)!r} != {expected!r}")
    if tar_members_seen != [EXPECTED_BOOT_MEMBER]:
        raise SystemExit(f"M22 manifest tar members mismatch: {tar_members_seen!r}")

    required_safety: dict[str, Any] = {
        "boot_only": True,
        "host_only_build": True,
        "live_flash_authorized": False,
        "requires_new_sha_pinned_agents_exception_before_flash": True,
        "requires_ramoops_dtbo_enabled_before_flash": True,
        "base_is_known_booting_magisk_boot": True,
        "construction": "magiskboot unpack/repack; replace only ramdisk /init",
        "mkbootimg_from_scratch": False,
        "runtime": "freestanding-raw-syscall-c",
        "glibc_static_startup": False,
        "no_android_or_magisk_handoff": True,
        "persistent_partition_mount": False,
        "block_device_writes": False,
        "module_insertions": False,
        "module_binary_injection": False,
        "module_list_files_injected_into_boot_ramdisk": 0,
        "configfs_runtime_gadget": False,
        "udc_binding": False,
        "usb_role_force": False,
        "watchdog": "not-touched",
        "kmsg_marker_write": True,
        "procfs_writes": ["/proc/sys/kernel/sysrq", "/proc/sysrq-trigger"],
        "intentional_kernel_crash": "sysrq-trigger-c",
        "fallback_reboot": "download",
        "on_reboot_syscall_return": "infinite-park",
    }
    for key, expected in required_safety.items():
        if safety.get(key) != expected:
            raise SystemExit(f"M22 manifest safety {key} mismatch: {safety.get(key)!r} != {expected!r}")
    if ramdisk.get("replaced_entry") != "init":
        raise SystemExit("M22 manifest did not replace /init")
    if ramdisk.get("module_files_injected_into_boot_ramdisk") != 0:
        raise SystemExit("M22 must not inject module binaries into boot ramdisk")
    if ramdisk.get("module_list_files_injected_into_boot_ramdisk") != 0:
        raise SystemExit("M22 must not inject module-list files into boot ramdisk")

    required_strings = set(init_info.get("required_strings", []))
    for required in [
        EXPECTED_M22_MARKER,
        "/dev/kmsg",
        "/proc/sys/kernel/sysrq",
        "/proc/sysrq-trigger",
        "sysrq_trigger=c",
        "phase=kmsg-before-sysrq",
        "phase=sysrq-trigger-about-to-write",
        "phase=sysrq-returned",
        "download",
    ]:
        if required not in required_strings:
            raise SystemExit(f"M22 required string missing from manifest: {required}")
    if int(init_info.get("svc_count", 0)) < 8:
        raise SystemExit(f"M22 init svc count too low: {init_info.get('svc_count')!r}")
    syscalls = {(item.get("name"), item.get("nr")) for item in init_info.get("syscalls", [])}
    for required in {
        ("mknodat", 33),
        ("mkdirat", 34),
        ("mount", 40),
        ("openat", 56),
        ("close", 57),
        ("write", 64),
        ("nanosleep", 101),
        ("reboot", 142),
    }:
        if required not in syscalls:
            raise SystemExit(f"M22 syscall missing from manifest: {required}")


def verify_current_boot_hash(log_path: Path, serial: str) -> None:
    result = adb_shell(
        "su -c 'dd if=/dev/block/by-name/boot bs=4096 2>/dev/null | sha256sum'",
        serial=serial,
        timeout=45.0,
    )
    text = result.stdout + result.stderr
    append_log(log_path, f"current_boot_hash_rc={result.returncode}")
    append_log(log_path, text)
    if result.returncode != 0 or EXPECTED_M22_BASE_BOOT_SHA256 not in text:
        raise SystemExit("current boot hash does not match known-booting Magisk baseline")


def restore_stock_dtbo_from_android(
    serial: str,
    odin: Path,
    dtbo_rollback_ap: Path,
    log_path: Path,
    odin_wait_sec: int,
    android_wait_sec: int,
    label: str,
) -> int:
    reboot_android_to_download(serial, log_path, label)
    return restore_dtbo_from_download(odin, dtbo_rollback_ap, log_path, odin_wait_sec, android_wait_sec, serial)


def restore_stock_dtbo_after_m22_download_missing(
    odin: Path,
    dtbo_rollback_ap: Path,
    log_path: Path,
    odin_wait_sec: int,
    android_wait_sec: int,
) -> int:
    append_log(log_path, "m22_candidate_download_missing_attempting_dtbo_restore=1")
    try:
        restore_rc = restore_dtbo_from_download(odin, dtbo_rollback_ap, log_path, odin_wait_sec, android_wait_sec)
    except SystemExit as restore_error:
        append_log(log_path, f"m22_candidate_download_missing_dtbo_restore_exception={restore_error}")
        print(
            "download mode did not appear for M22 candidate flash and stock DTBO auto-restore could not start. "
            "Enter download mode manually and run --restore-dtbo-from-download.",
            file=sys.stderr,
        )
        return 2
    append_log(log_path, f"m22_candidate_download_missing_dtbo_restore_rc={restore_rc}")
    if restore_rc != 0:
        print(
            f"download mode did not appear for M22 candidate flash; stock DTBO restore rc={restore_rc}; log={log_path}",
            file=sys.stderr,
        )
        return restore_rc
    print(
        f"download mode did not appear for M22 candidate flash; stock DTBO restored; log={log_path}",
        file=sys.stderr,
    )
    return 12


def rollback_boot_collect_pstore(
    odin: Path,
    boot_rollback_ap: Path,
    run_dir: Path,
    log_path: Path,
    rollback_target: str,
    odin_wait_sec: int,
    android_wait_sec: int,
) -> tuple[int, str | None, bool]:
    device = wait_for_odin(odin, log_path, "m22-boot-rollback-wait", odin_wait_sec)
    if device is None:
        raise SystemExit("M22 boot rollback requires exactly one Odin device")
    rc = flash_ap(odin, boot_rollback_ap, device, log_path, f"{rollback_target}_boot_rollback")
    if rc != 0:
        return (rc or 5, None, False)
    android = wait_for_android_root(log_path, android_wait_sec)
    if android is None:
        return (6, None, False)
    marker_found = collect_android_pstore(run_dir, log_path, "post_m22_boot_rollback", android, marker=EXPECTED_M22_MARKER)
    append_log(log_path, f"m22_retained_marker_found={int(marker_found)}")
    return (0, android, marker_found)


def observe_m22_transport(run_dir: Path, log_path: Path, seconds: int, odin: Path) -> tuple[str, str | None]:
    host_snapshot(run_dir, log_path, "after_m22_candidate_flash", odin)
    deadline = time.monotonic() + seconds
    iteration = 0
    while time.monotonic() < deadline:
        iteration += 1
        label = f"m22_observe_{iteration:03d}"
        if iteration == 1 or iteration % 5 == 0:
            host_snapshot(run_dir, log_path, label, odin)
        devices = odin_devices(odin, log_path, f"{label}-odin")
        if len(devices) == 1:
            append_log(log_path, f"m22_result=odin_seen endpoint={devices[0]}")
            return "odin", devices[0]
        if len(devices) > 1:
            raise SystemExit(f"refusing ambiguous Odin devices during M22 observation: {devices}")
        rows = adb_rows(log_path, f"{label}-adb")
        usable = [row for row in rows if len(row) >= 2 and row[1] == "device"]
        if len(usable) == 1:
            append_log(log_path, f"m22_result=adb_seen serial={usable[0][0]}")
            return "adb", usable[0][0]
        if len(usable) > 1:
            raise SystemExit(f"refusing ambiguous ADB devices during M22 observation: {usable}")
        time.sleep(1.0)
    append_log(log_path, "m22_result=no_rollback_transport_manual_download_required")
    return "none", None


def print_operator_plan(
    dtbo_candidate_ap: Path,
    dtbo_rollback_ap: Path,
    m22_ap: Path,
    magisk_rollback_ap: Path,
    stock_rollback_ap: Path,
) -> None:
    script = "workspace/public/src/scripts/revalidation/s22plus_ramoops_dtbo_m22_sysrq_panic_live_gate.py"
    print("S22+ ramoops DTBO + M22 sysrq-panic retained-console plan")
    print("state: host-only plan; no device action was performed")
    print()
    print("pinned artifacts:")
    print(f"  dtbo_candidate_ap={display_path(dtbo_candidate_ap)}")
    print(f"  dtbo_rollback_ap={display_path(dtbo_rollback_ap)}")
    print(f"  m22_ap={display_path(m22_ap)}")
    print(f"  magisk_rollback_ap={display_path(magisk_rollback_ap)}")
    print(f"  stock_rollback_ap={display_path(stock_rollback_ap)}")
    print()
    print("current gate state:")
    print("  1. AGENTS policy is expected to be inactive until an inert draft is promoted.")
    print("  2. Run offline host checks:")
    print(f"     PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 {script} --offline-check")
    print("  3. After explicit operator approval, promote the inert AGENTS draft.")
    print("  4. Then run the default dry-run:")
    print(f"     PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 {script}")
    print()
    print("attended live command, only after active policy + dry-run pass:")
    print(f"  PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 {script} --live --ack {LIVE_ACK_TOKEN}")
    print()
    print("expected live sequence:")
    print("  1. flash patched DTBO")
    print("  2. require Android/root return")
    print("  3. verify patched DTBO hash and live ramoops_region/status=okay")
    print("  4. flash M22 boot positive-control")
    print(f"  5. M22 writes retained marker {EXPECTED_M22_MARKER}")
    print("  6. M22 triggers intentional kernel crash via sysrq-trigger-c")
    print("  7. observe ADB/Odin/no-transport after intentional sysrq crash")
    print("  8. roll boot back to Magisk and collect pstore/last_kmsg")
    print("  9. restore stock DTBO")
    print()
    print("manual recovery command if no rollback transport appears:")
    print(f"  PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 {script} --rollback-boot-from-download --ack {ROLLBACK_BOOT_ACK_TOKEN}")
    print()
    print("stock DTBO cleanup commands:")
    print(f"  PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 {script} --restore-dtbo-from-android --ack {RESTORE_DTBO_ACK_TOKEN}")
    print(f"  PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 {script} --restore-dtbo-from-download --ack {RESTORE_DTBO_ACK_TOKEN}")


def preflight_common(args: argparse.Namespace) -> tuple[Path, Path, Path, Path, Path, Path, Path, Path, Path]:
    root = repo_root()
    run_dir = resolve_run_dir(root, args.run_dir)
    log_path = run_dir / "s22plus_ramoops_dtbo_m22_sysrq_panic_live_gate.txt"
    append_log(log_path, f"=== {utc_now()} s22plus ramoops DTBO + M22 sysrq-panic live gate ===")
    append_log(log_path, f"target={EXPECTED_TARGET}")

    odin = resolve(root, args.odin)
    dtbo_candidate_ap = resolve(root, args.dtbo_candidate_ap)
    dtbo_rollback_ap = resolve(root, args.dtbo_rollback_ap)
    dtbo_manifest = resolve(root, args.dtbo_manifest)
    m22_ap = resolve(root, args.m22_ap)
    m22_manifest = resolve(root, args.m22_manifest)
    magisk_rollback_ap = resolve(root, args.magisk_rollback_ap)
    stock_rollback_ap = resolve(root, args.stock_rollback_ap)
    if not odin.is_file():
        raise SystemExit(f"odin4 missing: {odin}")

    verify_ap_member(dtbo_candidate_ap, EXPECTED_DTBO_CANDIDATE_AP_SHA256, "dtbo.img.lz4", "dtbo_candidate", log_path)
    verify_ap_member(dtbo_rollback_ap, EXPECTED_DTBO_ROLLBACK_AP_SHA256, "dtbo.img.lz4", "dtbo_rollback", log_path)
    verify_dtbo_manifest(dtbo_manifest, log_path)
    verify_ap_member(m22_ap, EXPECTED_M22_AP_SHA256, EXPECTED_BOOT_MEMBER, "m22_candidate", log_path)
    verify_m22_manifest(m22_manifest, log_path)
    verify_ap_member(magisk_rollback_ap, EXPECTED_MAGISK_AP_SHA256, EXPECTED_BOOT_MEMBER, "magisk_boot_rollback", log_path)
    verify_ap_member(stock_rollback_ap, EXPECTED_STOCK_BOOT_AP_SHA256, EXPECTED_BOOT_MEMBER, "stock_boot_fallback", log_path)
    return root, run_dir, log_path, odin, dtbo_candidate_ap, dtbo_rollback_ap, m22_ap, magisk_rollback_ap, stock_rollback_ap


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dtbo-candidate-ap", type=Path, default=DEFAULT_DTBO_CANDIDATE_AP)
    parser.add_argument("--dtbo-rollback-ap", type=Path, default=DEFAULT_DTBO_ROLLBACK_AP)
    parser.add_argument("--dtbo-manifest", type=Path, default=DEFAULT_DTBO_MANIFEST)
    parser.add_argument("--m22-ap", type=Path, default=DEFAULT_M22_AP)
    parser.add_argument("--m22-manifest", type=Path, default=DEFAULT_M22_MANIFEST)
    parser.add_argument("--magisk-rollback-ap", type=Path, default=DEFAULT_MAGISK_ROLLBACK_AP)
    parser.add_argument("--stock-rollback-ap", type=Path, default=DEFAULT_STOCK_ROLLBACK_AP)
    parser.add_argument("--odin", type=Path, default=DEFAULT_ODIN)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--serial", help="ADB serial to pin before live flashing")
    parser.add_argument("--m22-observe-sec", type=int, default=120)
    parser.add_argument("--odin-wait-sec", type=int, default=90)
    parser.add_argument("--android-wait-sec", type=int, default=300)
    parser.add_argument("--android-stability-samples", type=int, default=4)
    parser.add_argument("--android-stability-interval-sec", type=float, default=3.0)
    parser.add_argument("--rollback-target", choices=[ROLLBACK_MAGISK, ROLLBACK_STOCK], default=ROLLBACK_MAGISK)
    parser.add_argument("--offline-check", action="store_true")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--rollback-boot-from-download", action="store_true")
    parser.add_argument("--restore-dtbo-from-download", action="store_true")
    parser.add_argument("--restore-dtbo-from-android", action="store_true")
    parser.add_argument("--print-plan", action="store_true", help="verify pinned artifacts and print the operator live/recovery plan")
    parser.add_argument("--ack")
    args = parser.parse_args(argv)

    modes = sum(
        1
        for enabled in (
            args.offline_check,
            args.live,
            args.rollback_boot_from_download,
            args.restore_dtbo_from_download,
            args.restore_dtbo_from_android,
            args.print_plan,
        )
        if enabled
    )
    if modes > 1:
        raise SystemExit(
            "--offline-check, --live, --rollback-boot-from-download, "
            "--restore-dtbo-from-download, --restore-dtbo-from-android, and --print-plan are mutually exclusive"
        )

    (
        root,
        run_dir,
        log_path,
        odin,
        dtbo_candidate_ap,
        dtbo_rollback_ap,
        m22_ap,
        magisk_rollback_ap,
        stock_rollback_ap,
    ) = preflight_common(args)
    boot_rollback_ap = magisk_rollback_ap if args.rollback_target == ROLLBACK_MAGISK else stock_rollback_ap

    if args.print_plan:
        append_log(log_path, "print_plan=ok device_action=0 agents_exception_checked=0 android_checked=0")
        print_operator_plan(dtbo_candidate_ap, dtbo_rollback_ap, m22_ap, magisk_rollback_ap, stock_rollback_ap)
        print(f"log={display_path(log_path)}")
        return 0

    if args.offline_check:
        append_log(log_path, "offline_check=ok device_action=0 agents_exception_checked=0 android_checked=0")
        print(f"offline-check ok: DTBO/M22 candidate and rollback APs verified; no device action; log={log_path}")
        return 0

    verify_agents_exception(root, log_path)

    if args.rollback_boot_from_download:
        if args.ack != ROLLBACK_BOOT_ACK_TOKEN:
            raise SystemExit(f"--rollback-boot-from-download requires --ack {ROLLBACK_BOOT_ACK_TOKEN}")
        rc, android, marker_found = rollback_boot_collect_pstore(
            odin,
            boot_rollback_ap,
            run_dir,
            log_path,
            args.rollback_target,
            args.odin_wait_sec,
            args.android_wait_sec,
        )
        if rc != 0 or android is None:
            print(f"M22 boot rollback-from-download completed rc={rc} android={android} marker={int(marker_found)}; log={log_path}")
            return rc
        restore_rc = restore_stock_dtbo_from_android(
            android,
            odin,
            dtbo_rollback_ap,
            log_path,
            args.odin_wait_sec,
            args.android_wait_sec,
            "stock_dtbo_restore_after_m22_manual_boot_rollback",
        )
        print(
            "M22 boot rollback-from-download completed "
            f"rc={rc} android={android} marker={int(marker_found)} stock_dtbo_restore_rc={restore_rc}; log={log_path}"
        )
        return restore_rc if restore_rc != 0 else (0 if marker_found else 10)

    if args.restore_dtbo_from_download:
        if args.ack != RESTORE_DTBO_ACK_TOKEN:
            raise SystemExit(f"--restore-dtbo-from-download requires --ack {RESTORE_DTBO_ACK_TOKEN}")
        rc = restore_dtbo_from_download(odin, dtbo_rollback_ap, log_path, args.odin_wait_sec, args.android_wait_sec)
        print(f"stock DTBO restore-from-download completed rc={rc}; log={log_path}")
        return rc

    selected_serial = require_current_android(log_path, args.serial)
    verify_android_stability(
        log_path,
        selected_serial,
        args.android_stability_samples,
        args.android_stability_interval_sec,
    )
    verify_current_boot_hash(log_path, selected_serial)

    if args.restore_dtbo_from_android:
        if args.ack != RESTORE_DTBO_ACK_TOKEN:
            raise SystemExit(f"--restore-dtbo-from-android requires --ack {RESTORE_DTBO_ACK_TOKEN}")
        current_dtbo_sha = read_current_dtbo_hash(log_path, selected_serial, "pre_stock_restore")
        host_snapshot(run_dir, log_path, "restore_android_current", odin)
        if current_dtbo_sha == EXPECTED_STOCK_DTBO_RAW_SHA256:
            verify_live_ramoops_status(log_path, selected_serial, "disabled", "stock_restore_already")
            append_log(log_path, "stock_dtbo_restore_android_already_stock=1")
            print(f"stock DTBO restore-from-android already stock; log={log_path}")
            return 0
        if current_dtbo_sha != EXPECTED_PATCHED_DTBO_RAW_SHA256:
            raise SystemExit(f"refusing restore-from-android from unexpected DTBO hash {current_dtbo_sha}")
        rc = restore_stock_dtbo_from_android(
            selected_serial,
            odin,
            dtbo_rollback_ap,
            log_path,
            args.odin_wait_sec,
            args.android_wait_sec,
            "stock_dtbo_restore",
        )
        print(f"stock DTBO restore-from-android completed rc={rc}; log={log_path}")
        return rc

    verify_current_dtbo_hash(log_path, selected_serial, EXPECTED_STOCK_DTBO_RAW_SHA256, "current")
    verify_live_ramoops_status(log_path, selected_serial, "disabled", "current")
    host_snapshot(run_dir, log_path, "dryrun_current", odin)

    if not args.live:
        print(
            "dry-run ok: DTBO/M22 candidates, rollback APs, AGENTS exception, Android stability, "
            f"boot hash, stock DTBO hash, and live disabled status verified; log={log_path}"
        )
        return 0
    if args.ack != LIVE_ACK_TOKEN:
        raise SystemExit(f"--live requires --ack {LIVE_ACK_TOKEN}")

    reboot_android_to_download(selected_serial, log_path, "dtbo_candidate")
    device = wait_for_odin(odin, log_path, "dtbo-candidate-wait", args.odin_wait_sec)
    if device is None:
        print("download mode did not appear for DTBO candidate flash", file=sys.stderr)
        return 2
    rc = flash_ap(odin, dtbo_candidate_ap, device, log_path, "dtbo_candidate")
    if rc != 0:
        print(f"DTBO candidate Odin flash failed rc={rc}; log={log_path}", file=sys.stderr)
        return rc or 3

    patched_serial = wait_for_android_root(log_path, args.android_wait_sec)
    if patched_serial is None:
        return restore_after_patched_android_timeout(
            odin,
            dtbo_rollback_ap,
            log_path,
            args.odin_wait_sec,
            args.android_wait_sec,
        )
    try:
        verify_current_dtbo_hash(log_path, patched_serial, EXPECTED_PATCHED_DTBO_RAW_SHA256, "patched")
        verify_live_ramoops_status(log_path, patched_serial, "okay", "patched")
    except SystemExit as verify_error:
        return restore_after_patched_android_failure(
            odin,
            dtbo_rollback_ap,
            log_path,
            patched_serial,
            args.odin_wait_sec,
            args.android_wait_sec,
            verify_error,
        )

    reboot_android_to_download(patched_serial, log_path, "m22_candidate")
    device = wait_for_odin(odin, log_path, "m22-candidate-wait", args.odin_wait_sec)
    if device is None:
        return restore_stock_dtbo_after_m22_download_missing(
            odin,
            dtbo_rollback_ap,
            log_path,
            args.odin_wait_sec,
            args.android_wait_sec,
        )
    rc = flash_ap(odin, m22_ap, device, log_path, "m22_candidate")
    if rc != 0:
        append_log(log_path, f"m22_candidate_flash_failed_attempting_dtbo_restore_rc={rc}")
        restore_rc = restore_dtbo_from_download(odin, dtbo_rollback_ap, log_path, args.odin_wait_sec, args.android_wait_sec)
        print(f"M22 candidate Odin flash failed rc={rc}; stock DTBO restore rc={restore_rc}; log={log_path}", file=sys.stderr)
        return rc or 3

    observed, endpoint = observe_m22_transport(run_dir, log_path, args.m22_observe_sec, odin)
    if observed == "adb" and endpoint:
        append_log(log_path, f"m22_unexpected_adb_returned={endpoint}")
        reboot_android_to_download(endpoint, log_path, "m22_unexpected_adb_rollback")
        endpoint = wait_for_odin(odin, log_path, "m22-unexpected-adb-rollback-wait", args.odin_wait_sec)
        observed = "odin" if endpoint else "none"
    if observed != "odin" or endpoint is None:
        append_log(log_path, "m22_result=no_rollback_transport_manual_download_required")
        print("M22 did not expose rollback transport. Enter download mode manually and run --rollback-boot-from-download.", file=sys.stderr)
        return 4

    rc, post_boot_rollback_android, marker_found = rollback_boot_collect_pstore(
        odin,
        boot_rollback_ap,
        run_dir,
        log_path,
        args.rollback_target,
        args.odin_wait_sec,
        args.android_wait_sec,
    )
    if rc != 0 or post_boot_rollback_android is None:
        return rc

    restore_rc = restore_stock_dtbo_from_android(
        post_boot_rollback_android,
        odin,
        dtbo_rollback_ap,
        log_path,
        args.odin_wait_sec,
        args.android_wait_sec,
        "stock_dtbo_restore_after_m22_capture",
    )
    if restore_rc != 0:
        return restore_rc
    print(
        f"ramoops DTBO + M22 sysrq-panic live gate completed; retained_marker_found={int(marker_found)}; log={log_path}"
    )
    return 0 if marker_found else 10


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
