#!/usr/bin/env python3
"""Guarded S22+ M8 timed-download module-bisect native-init live gate.

Default dry-run and live modes require a SHA-pinned AGENTS.md exception plus a
recovered rooted Android baseline. --offline-check verifies only the host-built
M8 package and rollback APs without touching any device.

M8 is not an ACM proof. The expected live proof is automatic return to Samsung
download mode after native PID1 attempts the first 18 modules from the M7-only
delta. The helper must not count the original candidate Odin endpoint as proof:
it waits for the original endpoint to disconnect, then treats a later Odin
endpoint as the candidate's self-download result.
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
    verify_android_stability,
    verify_current_boot_hash,
)


LIVE_ACK_TOKEN = "S22PLUS-M8-TIMED-DOWNLOAD-LIVE-GATE"
ROLLBACK_ACK_TOKEN = "S22PLUS-M8-ROLLBACK-FROM-DOWNLOAD"

EXPECTED_TARGET = "SM-S906N/g0q/S906NKSS7FYG8"
EXPECTED_M8_AP_SHA256 = "59433518e7bea2d16f5efb62ee226c190f6a3af8673336310a2ef0fff7bee36b"
EXPECTED_M8_BOOT_SHA256 = "3c10c9232b8579b552d791d24e65b7b4dd8ec3625941766894a08725a7abae52"
EXPECTED_M8_BASE_BOOT_SHA256 = "2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e"
EXPECTED_M8_KERNEL_SHA256 = "bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff"
EXPECTED_M8_INIT_SHA256 = "5c8591023d0ad801155535e9b535993fb3122c4d3e4c86139d36a819ee72c3b2"
EXPECTED_M8_SOURCE_SHA256 = "823acdff96838af78f2111267d156c88c307974f71bf2292fc69c6ac85e1316f"
EXPECTED_M8_BATCH_SHA256 = "6831a24ac12ddf0bfdb9b5695dcd3aada7f200aa4a998864874c207efa31bc9d"
EXPECTED_M8_VENDOR_RAMDISK_SHA256 = "41b2481b779ff48863c300250dabf1b3dcc45c7f58fab421fcf6df1245145193"
EXPECTED_M8_M5_MANIFEST_SHA256 = "1c22c93496e03a7df6dd74959511797b6d033b74361d3d3733d7be8269a5fa05"
EXPECTED_M8_MARKER = "S22_NATIVE_INIT_M8_TIMED_DOWNLOAD"
EXPECTED_M8_BATCH_COUNT = 18
EXPECTED_M8_BATCH_BYTES = 255
EXPECTED_M7_ONLY_COUNT = 36
EXPECTED_M7_OVERLAP_WITH_M5_COUNT = 17
EXPECTED_M5_ONLY_NOT_IN_M7_COUNT = 9
EXPECTED_M7_SUBSET_COUNT = 53
EXPECTED_VENDOR_KO_COUNT = 441

EXPECTED_M8_BATCH = [
    "abc.ko",
    "clk-rpmh.ko",
    "gcc-waipio.ko",
    "icc-rpmh.ko",
    "qcom_ipc_logging.ko",
    "rpmh-regulator.ko",
    "clk-dummy.ko",
    "clk-qcom.ko",
    "cmd-db.ko",
    "debug-regulator.ko",
    "gdsc-regulator.ko",
    "icc-bcm-voter.ko",
    "icc-debug.ko",
    "minidump.ko",
    "phy-generic.ko",
    "proxy-consumer.ko",
    "qcom_rpmh.ko",
    "qcom-scm.ko",
]
EXPECTED_WATCHDOG_BLOCKLIST = {
    "gh_virt_wdt.ko",
    "qcom_wdt_core.ko",
    "qcom_soc_wdt.ko",
    "sec_qc_qcom_wdt_core.ko",
}

DEFAULT_M8_AP = Path("workspace/private/outputs/s22plus_native_init/inplace_m8_timed_download_bisect_v0_1/odin4/AP.tar.md5")
DEFAULT_M8_MANIFEST = Path("workspace/private/outputs/s22plus_native_init/inplace_m8_timed_download_bisect_v0_1/manifest.json")


def resolve_run_dir(root: Path, requested: Path | None) -> Path:
    if requested is not None:
        run_dir = requested
        run_dir = resolve(root, run_dir)
        run_dir.mkdir(parents=True, exist_ok=False)
        return run_dir
    stamp = utc_now().replace("-", "").replace(":", "").replace("Z", "Z")
    base = resolve(root, DEFAULT_RUN_ROOT / f"s22plus_m8_timed_download_live_gate_{stamp}")
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
        "S22+ M8 timed-download module-bisect native-init boot-only",
        EXPECTED_M8_AP_SHA256,
        EXPECTED_M8_BOOT_SHA256,
        EXPECTED_M8_BASE_BOOT_SHA256,
        EXPECTED_M8_KERNEL_SHA256,
        EXPECTED_M8_INIT_SHA256,
        EXPECTED_M8_BATCH_SHA256,
        EXPECTED_M8_VENDOR_RAMDISK_SHA256,
        LIVE_ACK_TOKEN,
        ROLLBACK_ACK_TOKEN,
        "s22plus_m8_delta_batch.modules",
        "first 18 modules from the M7-only delta",
        "automatic Samsung download-mode return",
        "wait for the original Odin endpoint to disconnect",
        "no ACM",
        "no configfs",
        "manual download-mode rollback",
    ]
    missing = [item for item in required if item not in normalized]
    append_log(log_path, f"agents_exception_missing={missing}")
    if missing:
        raise SystemExit(f"AGENTS.md missing M8 live authorization markers: {missing}")


def verify_m8_manifest(path: Path, log_path: Path) -> None:
    if not path.is_file():
        raise SystemExit(f"M8 manifest missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    hashes = data.get("hashes", {})
    safety = data.get("safety", {})
    ramdisk = data.get("ramdisk", {})
    batch = data.get("m8_batch", {})
    vendor = data.get("vendor_ramdisk", {})
    init_info = data.get("m8_init", {})
    tar_members_seen = data.get("tar_members")
    append_log(log_path, f"m8_manifest_path={path}")
    append_log(log_path, f"m8_manifest_hashes={json.dumps(hashes, sort_keys=True)}")
    append_log(log_path, f"m8_manifest_safety={json.dumps(safety, sort_keys=True)}")
    append_log(log_path, f"m8_manifest_ramdisk={json.dumps(ramdisk, sort_keys=True)}")
    append_log(log_path, f"m8_manifest_batch={json.dumps(batch, sort_keys=True)}")

    expected_hashes = {
        "ap_tar_md5": EXPECTED_M8_AP_SHA256,
        "boot_img": EXPECTED_M8_BOOT_SHA256,
        "base_boot": EXPECTED_M8_BASE_BOOT_SHA256,
        "kernel": EXPECTED_M8_KERNEL_SHA256,
        "m8_init": EXPECTED_M8_INIT_SHA256,
        "source": EXPECTED_M8_SOURCE_SHA256,
        "m8_delta_batch": EXPECTED_M8_BATCH_SHA256,
        "vendor_ramdisk": EXPECTED_M8_VENDOR_RAMDISK_SHA256,
        "m5_module_bundle_manifest": EXPECTED_M8_M5_MANIFEST_SHA256,
        "nochange_repack_boot": EXPECTED_M8_BASE_BOOT_SHA256,
    }
    for key, expected in expected_hashes.items():
        if hashes.get(key) != expected:
            raise SystemExit(f"M8 manifest hash {key} mismatch: {hashes.get(key)!r} != {expected!r}")
    if tar_members_seen != [EXPECTED_MEMBER]:
        raise SystemExit(f"M8 manifest tar members mismatch: {tar_members_seen!r}")

    expected_safety: dict[str, Any] = {
        "boot_only": True,
        "host_only_build": True,
        "live_flash_authorized": False,
        "requires_new_sha_pinned_agents_exception_before_flash": True,
        "base_is_known_booting_magisk_boot": True,
        "construction": "magiskboot unpack/repack; replace ramdisk /init and add one module-list text file",
        "runtime": "freestanding-raw-syscall",
        "glibc_static_startup": False,
        "mkbootimg_from_scratch": False,
        "no_android_or_magisk_handoff": True,
        "auto_reboot": "download-after-bounded-module-batch",
        "host_commanded_reboot_download": False,
        "persistent_partition_mount": False,
        "block_device_writes": False,
        "module_insertions": "boot ramdisk gets text list only; runtime uses stock vendor_boot /lib/modules",
        "module_binary_injection": False,
        "module_list_path": "/s22plus_m8_delta_batch.modules",
        "module_subset": "first 18 modules from M7-only delta relative to M5, in M7 recovery order",
        "configfs_runtime_gadget": False,
        "udc_binding": False,
        "usb_role_force": False,
        "watchdog": "not-touched-by-init-source; watchdog modules excluded from inherited M7 subset",
    }
    for key, expected in expected_safety.items():
        if safety.get(key) != expected:
            raise SystemExit(f"M8 manifest safety {key} mismatch: {safety.get(key)!r} != {expected!r}")

    if ramdisk.get("replaced_entry") != "init":
        raise SystemExit("M8 manifest did not replace /init")
    if ramdisk.get("added_batch_entry") != "s22plus_m8_delta_batch.modules":
        raise SystemExit("M8 manifest did not add M8 batch list")
    if ramdisk.get("module_files_injected_into_boot_ramdisk") != 0:
        raise SystemExit("M8 must not inject vendor module binaries into boot ramdisk")
    if ramdisk.get("module_list_files_injected_into_boot_ramdisk") != 1:
        raise SystemExit("M8 must inject exactly one module-list text file into boot ramdisk")

    if batch.get("strategy") != "m7_only_first_half":
        raise SystemExit("M8 batch strategy mismatch")
    if batch.get("batch") != EXPECTED_M8_BATCH:
        raise SystemExit("M8 batch contents mismatch")
    if batch.get("batch_count") != EXPECTED_M8_BATCH_COUNT:
        raise SystemExit("M8 batch count mismatch")
    if batch.get("batch_bytes") != EXPECTED_M8_BATCH_BYTES:
        raise SystemExit("M8 batch byte count mismatch")
    if batch.get("m7_only_count") != EXPECTED_M7_ONLY_COUNT:
        raise SystemExit("M8 M7-only count mismatch")
    if batch.get("m7_overlap_with_m5_count") != EXPECTED_M7_OVERLAP_WITH_M5_COUNT:
        raise SystemExit("M8 overlap count mismatch")
    if batch.get("m5_only_not_in_m7_count") != EXPECTED_M5_ONLY_NOT_IN_M7_COUNT:
        raise SystemExit("M8 M5-only count mismatch")
    watchdogs = set(batch.get("watchdog_blocklist", []))
    if watchdogs != EXPECTED_WATCHDOG_BLOCKLIST:
        raise SystemExit("M8 watchdog blocklist mismatch")
    if sorted(EXPECTED_WATCHDOG_BLOCKLIST.intersection(batch.get("batch", []))):
        raise SystemExit("M8 batch contains watchdog module")

    if vendor.get("ko_count") != EXPECTED_VENDOR_KO_COUNT:
        raise SystemExit("M8 vendor .ko count mismatch")
    subset = vendor.get("m7_usb_subset", {})
    if not isinstance(subset, dict) or subset.get("subset_count") != EXPECTED_M7_SUBSET_COUNT:
        raise SystemExit("M8 inherited M7 subset count mismatch")
    if subset.get("blocked_from_closure") != ["qc_usb_audio.ko"]:
        raise SystemExit("M8 inherited M7 blocklist result changed")
    if subset.get("blocked_watchdogs_present_in_closure") != []:
        raise SystemExit("M8 inherited M7 closure unexpectedly contains watchdogs")

    required_strings = set(init_info.get("required_strings", []))
    for required in [
        EXPECTED_M8_MARKER,
        "version=0.1",
        "/s22plus_m8_delta_batch.modules",
        "batch_strategy=m7_only_first_half",
        "expected_module_count=18",
        "no_usb_acm=1",
        "no_configfs=1",
        "auto_reboot_download_after_batch=1",
        "phase=timed_download",
        "download",
    ]:
        if required not in required_strings:
            raise SystemExit(f"M8 required string missing from manifest: {required}")
    forbidden_strings = set(init_info.get("forbidden_strings", []))
    for forbidden in ["ttyGS0", "ss_acm.0", "usb_gadget", "/config", "ld-linux", "libc.so"]:
        if forbidden not in forbidden_strings:
            raise SystemExit(f"M8 forbidden-string gate missing from manifest: {forbidden}")


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
        label = f"m8_self_download_{iteration:03d}"
        host_snapshot(run_dir, log_path, label, odin)
        devices = odin_devices(odin, log_path, f"{label}-extra")
        if len(devices) == 1:
            append_log(log_path, f"m8_self_download_seen=1 device={devices[0]}")
            return devices[0]
        if len(devices) > 1:
            raise SystemExit(f"refusing ambiguous Odin devices during M8 observation: {devices}")
        rows = adb_rows(log_path, f"{label}-extra")
        if rows:
            append_log(log_path, f"m8_candidate_adb_rows={rows}")
        time.sleep(1.0)
    append_log(log_path, "m8_self_download_seen=0")
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
    collect_android_pstore(run_dir, log_path, "post_rollback", serial, marker=EXPECTED_M8_MARKER)
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m8-ap", type=Path, default=DEFAULT_M8_AP)
    parser.add_argument("--m8-manifest", type=Path, default=DEFAULT_M8_MANIFEST)
    parser.add_argument("--magisk-rollback-ap", type=Path, default=DEFAULT_MAGISK_ROLLBACK_AP)
    parser.add_argument("--stock-rollback-ap", type=Path, default=DEFAULT_STOCK_ROLLBACK_AP)
    parser.add_argument("--odin", type=Path, default=DEFAULT_ODIN)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--serial", help="ADB serial to pin before live flashing")
    parser.add_argument("--self-download-wait-sec", type=int, default=60)
    parser.add_argument("--post-flash-disconnect-wait-sec", type=int, default=20)
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
    log_path = run_dir / "s22plus_m8_timed_download_live_gate.txt"
    append_log(log_path, f"=== {utc_now()} s22plus m8 timed-download live gate ===")
    append_log(log_path, f"target={EXPECTED_TARGET}")

    odin = resolve(root, args.odin)
    m8_ap = resolve(root, args.m8_ap)
    m8_manifest = resolve(root, args.m8_manifest)
    magisk_rollback_ap = resolve(root, args.magisk_rollback_ap)
    stock_rollback_ap = resolve(root, args.stock_rollback_ap)
    rollback_ap = magisk_rollback_ap if args.rollback_target == ROLLBACK_MAGISK else stock_rollback_ap
    if not odin.is_file():
        raise SystemExit(f"odin4 missing: {odin}")

    verify_ap(m8_ap, EXPECTED_M8_AP_SHA256, "m8_candidate", log_path)
    verify_m8_manifest(m8_manifest, log_path)
    verify_ap(magisk_rollback_ap, EXPECTED_MAGISK_AP_SHA256, "magisk_boot_rollback", log_path)
    verify_ap(stock_rollback_ap, EXPECTED_STOCK_BOOT_AP_SHA256, "stock_boot_fallback", log_path)

    if args.offline_check:
        append_log(log_path, "offline_check=ok device_action=0 agents_exception_checked=0 android_checked=0")
        print(f"offline-check ok: M8 candidate and rollback APs verified; no device action; log={log_path}")
        return 0

    verify_agents_exception(root, log_path)

    if args.rollback_from_download:
        if args.ack != ROLLBACK_ACK_TOKEN:
            raise SystemExit(f"--rollback-from-download requires --ack {ROLLBACK_ACK_TOKEN}")
        rc = rollback_from_download(odin, rollback_ap, run_dir, log_path, args.rollback_target, args.android_wait_sec)
        print(f"M8 rollback-from-download completed rc={rc}; log={log_path}")
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
        print(
            "dry-run ok: M8 candidate, rollback APs, AGENTS exception, Android stability, "
            f"and boot hash verified; log={log_path}"
        )
        return 0
    if args.ack != LIVE_ACK_TOKEN:
        raise SystemExit(f"--live requires --ack {LIVE_ACK_TOKEN}")

    reboot = run(["adb", "-s", selected_serial, "reboot", "download"], timeout=20.0)
    append_log(log_path, f"adb_reboot_download_rc={reboot.returncode}")
    append_log(log_path, reboot.stdout + reboot.stderr)
    odin_device = wait_for_odin(odin, log_path, "candidate-wait", args.odin_wait_sec)
    if odin_device is None:
        print("download mode did not appear for M8 candidate flash", file=sys.stderr)
        return 2

    candidate_rc = flash_ap(odin, m8_ap, odin_device, log_path, "candidate")
    if candidate_rc != 0:
        print(f"M8 candidate Odin flash failed rc={candidate_rc}; log={log_path}", file=sys.stderr)
        return candidate_rc or 3

    left_download = wait_for_odin_absent(odin, log_path, "post-candidate-disconnect", args.post_flash_disconnect_wait_sec)
    if not left_download:
        print(
            "M8 candidate flash completed but the original Odin device did not disconnect; "
            "rolling back without claiming self-download proof.",
            file=sys.stderr,
        )
        rollback_device = wait_for_odin(odin, log_path, "rollback-still-download-wait", 5)
        if rollback_device is None:
            print(f"rollback download mode unavailable after no-disconnect; manual recovery required. log={log_path}", file=sys.stderr)
            return 4
        rollback_rc = flash_ap(odin, rollback_ap, rollback_device, log_path, f"{args.rollback_target}_rollback_no_disconnect")
        if rollback_rc != 0:
            return rollback_rc or 5
        post_rollback_serial = poll_android(log_path, args.android_wait_sec, expect_root=args.rollback_target == ROLLBACK_MAGISK)
        if post_rollback_serial is None:
            return 6
        append_log(log_path, "m8_result=no-proof-original-download-never-disconnected")
        collect_android_pstore(run_dir, log_path, "post_rollback_no_disconnect", post_rollback_serial, marker=EXPECTED_M8_MARKER)
        return 7

    print("M8 candidate flashed. Waiting for timed-download self-return.")
    rollback_device = observe_until_odin(run_dir, log_path, args.self_download_wait_sec, odin)
    if rollback_device is None:
        print("M8 self-download did not appear; enter download mode manually and run --rollback-from-download.", file=sys.stderr)
        return 4

    rollback_rc = flash_ap(odin, rollback_ap, rollback_device, log_path, f"{args.rollback_target}_rollback")
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
    collect_android_pstore(run_dir, log_path, "post_rollback", post_rollback_serial, marker=EXPECTED_M8_MARKER)
    print(f"M8 live gate completed with timed-download self-return and rollback ok; log={log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
