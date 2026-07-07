#!/usr/bin/env python3
"""Guarded S22+ M19 C000 checkpoint/download native-init live gate.

Dry-run is the default. Live mode requires a fresh SHA-pinned AGENTS.md
exception and an explicit ack token.

M19 C000 is the floor checkpoint from the M19 dependency-closed matrix: it
mounts only runtime virtual filesystems, emits its marker, skips all module
loads, then requests Samsung download mode. A later Odin endpoint after the
original post-flash Odin endpoint disconnects is the only positive proof.
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
    adb_shell,
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


LIVE_ACK_TOKEN = "S22PLUS-M19-C000-CHECKPOINT-LIVE-GATE"
ROLLBACK_ACK_TOKEN = "S22PLUS-M19-C000-ROLLBACK-FROM-DOWNLOAD"

EXPECTED_TARGET = "SM-S906N/g0q/S906NKSS7FYG8"
EXPECTED_M19_C000_LABEL = "C000"
EXPECTED_M19_C000_PREFIX_COUNT = 0
EXPECTED_M19_C000_AP_SHA256 = "d712840f1aa7d4ef9d07a7be404b29e5f5dd8065701db7f3d39d76c71296b9d4"
EXPECTED_M19_C000_BOOT_SHA256 = "0ae71d30257dafdc453db252bd77b11b554202f27c458e3b538d13c61df98ebb"
EXPECTED_M19_BASE_BOOT_SHA256 = "2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e"
EXPECTED_M19_KERNEL_SHA256 = "bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff"
EXPECTED_M19_C000_INIT_SHA256 = "7d4f7c8fb30af6aa1e21fe1fe6b24a6597c7385424f5d90e3bf6309a68441135"
EXPECTED_M19_MODULE_LIST_SHA256 = "c92bb69fd5605cba0ff0aafa44a1ee9f3ac0a66f7e3f1390a19363760e04c94f"
EXPECTED_M19_SOURCE_SHA256 = "4c83607d102006b045c32edb0dbb58b1ff14822febc01e8a9da281561522e9af"
EXPECTED_M19_MARKER = "S22_NATIVE_INIT_M19_CLOSED_CHECKPOINT"
EXPECTED_M19_MODULE_FILE = "s22plus_m19_closed_usb.modules"
EXPECTED_M19_CLOSED_COUNT = 150
EXPECTED_M19_ADDED_COUNT = 9

DEFAULT_M19_C000_AP = Path(
    "workspace/private/outputs/s22plus_native_init/"
    "inplace_m19_closed_checkpoint_download_v0_1/C000/odin4/AP.tar.md5"
)
DEFAULT_M19_C000_MANIFEST = Path(
    "workspace/private/outputs/s22plus_native_init/"
    "inplace_m19_closed_checkpoint_download_v0_1/C000/manifest.json"
)


def resolve_run_dir(root: Path, requested: Path | None) -> Path:
    if requested is not None:
        run_dir = resolve(root, requested)
        run_dir.mkdir(parents=True, exist_ok=False)
        return run_dir
    stamp = utc_now().replace("-", "").replace(":", "").replace("Z", "Z")
    base = resolve(root, DEFAULT_RUN_ROOT / f"s22plus_m19_c000_checkpoint_live_gate_{stamp}")
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
        "S22+ M19 C000 dependency-closed checkpoint/download native-init boot-only",
        EXPECTED_M19_C000_AP_SHA256,
        EXPECTED_M19_C000_BOOT_SHA256,
        EXPECTED_M19_BASE_BOOT_SHA256,
        EXPECTED_M19_KERNEL_SHA256,
        EXPECTED_M19_C000_INIT_SHA256,
        EXPECTED_M19_MODULE_LIST_SHA256,
        EXPECTED_M19_SOURCE_SHA256,
        LIVE_ACK_TOKEN,
        ROLLBACK_ACK_TOKEN,
        "C000",
        "prefix_count=0",
        "modules_prefix_skipped",
        "checkpoint-download",
        "no ACM",
        "no configfs",
        "no USB role force",
        "host-observed self-download means checkpoint reached",
        "manual download-mode rollback",
    ]
    missing = [item for item in required if item not in normalized]
    append_log(log_path, f"agents_exception_missing={missing}")
    if missing:
        raise SystemExit(f"AGENTS.md missing M19 C000 live authorization markers: {missing}")


def verify_m19_manifest(path: Path, log_path: Path) -> None:
    if not path.is_file():
        raise SystemExit(f"M19 C000 manifest missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    hashes = data.get("hashes", {})
    safety = data.get("safety", {})
    prefix = data.get("prefix", {})
    closed = data.get("closed_modules", {})
    ramdisk = data.get("ramdisk", {})
    m19_init = data.get("m19_init", {})
    tar_members_seen = data.get("tar_members")
    append_log(log_path, f"m19_c000_manifest_path={path}")
    append_log(log_path, f"m19_c000_manifest_hashes={json.dumps(hashes, sort_keys=True)}")
    append_log(log_path, f"m19_c000_manifest_safety={json.dumps(safety, sort_keys=True)}")
    append_log(log_path, f"m19_c000_manifest_prefix={json.dumps(prefix, sort_keys=True)}")
    append_log(log_path, f"m19_c000_manifest_closed={json.dumps(closed, sort_keys=True)}")

    required_hashes = {
        "ap_tar_md5": EXPECTED_M19_C000_AP_SHA256,
        "boot_img": EXPECTED_M19_C000_BOOT_SHA256,
        "base_boot": EXPECTED_M19_BASE_BOOT_SHA256,
        "kernel": EXPECTED_M19_KERNEL_SHA256,
        "m19_init": EXPECTED_M19_C000_INIT_SHA256,
        "m19_closed_modules": EXPECTED_M19_MODULE_LIST_SHA256,
        "source": EXPECTED_M19_SOURCE_SHA256,
    }
    for key, expected in required_hashes.items():
        if hashes.get(key) != expected:
            raise SystemExit(f"M19 C000 manifest hash {key} mismatch: {hashes.get(key)!r} != {expected!r}")
    if tar_members_seen != [EXPECTED_MEMBER]:
        raise SystemExit(f"M19 C000 manifest tar members mismatch: {tar_members_seen!r}")

    if prefix.get("label") != EXPECTED_M19_C000_LABEL:
        raise SystemExit(f"M19 C000 prefix label mismatch: {prefix.get('label')!r}")
    if prefix.get("count") != EXPECTED_M19_C000_PREFIX_COUNT:
        raise SystemExit(f"M19 C000 prefix count mismatch: {prefix.get('count')!r}")
    if prefix.get("expected_loaded_count") != 0 or prefix.get("expected_loaded_modules") != []:
        raise SystemExit(f"M19 C000 expected loaded module set mismatch: {prefix!r}")
    if prefix.get("module_after_prefix") != "sec_class.ko":
        raise SystemExit(f"M19 C000 next module mismatch: {prefix.get('module_after_prefix')!r}")

    if closed.get("closed_count") != EXPECTED_M19_CLOSED_COUNT:
        raise SystemExit(f"M19 closed module count mismatch: {closed.get('closed_count')!r}")
    if closed.get("added_count") != EXPECTED_M19_ADDED_COUNT:
        raise SystemExit(f"M19 added module count mismatch: {closed.get('added_count')!r}")
    if closed.get("unresolved_nonblocked") != {}:
        raise SystemExit(f"M19 unresolved non-reset dependency edges remain: {closed.get('unresolved_nonblocked')!r}")

    required_safety: dict[str, Any] = {
        "boot_only": True,
        "host_only_build": True,
        "live_flash_authorized": False,
        "requires_new_sha_pinned_agents_exception_before_flash": True,
        "base_is_known_booting_magisk_boot": True,
        "construction": "magiskboot unpack/repack; replace ramdisk /init and add one text module list",
        "runtime": "freestanding-raw-syscall",
        "glibc_static_startup": False,
        "mkbootimg_from_scratch": False,
        "no_android_or_magisk_handoff": True,
        "auto_reboot": True,
        "intended_reboot_syscall": True,
        "reboot_request": "download",
        "persistent_partition_mount": False,
        "block_device_writes": False,
        "module_binary_injection": False,
        "module_list_path": f"/{EXPECTED_M19_MODULE_FILE}",
        "module_prefix_count": 0,
        "configfs_runtime_gadget": False,
        "usb_role_force": False,
        "acm": False,
        "observation_model": "host-observed self-download means checkpoint reached",
    }
    for key, expected in required_safety.items():
        if safety.get(key) != expected:
            raise SystemExit(f"M19 C000 manifest safety {key} mismatch: {safety.get(key)!r} != {expected!r}")

    if ramdisk.get("replaced_entry") != "init":
        raise SystemExit("M19 C000 manifest did not replace /init")
    if ramdisk.get("added_subset_entry") != EXPECTED_M19_MODULE_FILE:
        raise SystemExit("M19 C000 manifest did not add the expected module-list file")
    if ramdisk.get("module_files_injected_into_boot_ramdisk") != 0:
        raise SystemExit("M19 C000 must not inject module binaries into boot ramdisk")
    if ramdisk.get("module_list_files_injected_into_boot_ramdisk") != 1:
        raise SystemExit("M19 C000 must inject exactly one module-list text file")

    required_strings = set(m19_init.get("required_strings", []))
    for required in [
        EXPECTED_M19_MARKER,
        "version=0.1",
        "runtime=freestanding",
        "raw_syscalls=1",
        "prefix_label=C000",
        "prefix_limit=0",
        f"/{EXPECTED_M19_MODULE_FILE}",
        "module_count=150",
        "module_list=boot_ramdisk_closed_usb",
        "module_source=stock_vendor_boot_ramdisk",
        "module_injection=list_only",
        "observation=checkpoint-download",
        "no_android_handoff=1",
        "no_configfs=1",
        "no_acm=1",
        "reboot_request=download",
        "download",
        "modules_prefix_skipped",
    ]:
        if required not in required_strings:
            raise SystemExit(f"M19 C000 required string missing from manifest: {required}")

    objdump = str(m19_init.get("objdump", ""))
    reboot_nr_lines = [
        line
        for line in objdump.splitlines()
        if "mov" in line and "x8" in line and "#0x8e" in line and "// #142" in line
    ]
    if not reboot_nr_lines:
        raise SystemExit("M19 C000 /init does not load arm64 __NR_reboot (142)")


def verify_current_boot_hash(log_path: Path, serial: str) -> None:
    result = adb_shell(
        "su -c 'dd if=/dev/block/by-name/boot bs=4096 2>/dev/null | sha256sum'",
        serial=serial,
        timeout=45.0,
    )
    text = result.stdout + result.stderr
    append_log(log_path, f"current_boot_hash_rc={result.returncode}")
    append_log(log_path, text)
    if result.returncode != 0 or EXPECTED_M19_BASE_BOOT_SHA256 not in text:
        raise SystemExit("current boot hash does not match known-booting Magisk baseline")


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
        label = f"m19_c000_self_download_{iteration:03d}"
        host_snapshot(run_dir, log_path, label, odin)
        devices = odin_devices(odin, log_path, f"{label}-extra")
        if len(devices) == 1:
            append_log(log_path, f"m19_c000_self_download_seen=1 device={devices[0]}")
            return devices[0]
        if len(devices) > 1:
            raise SystemExit(f"refusing ambiguous Odin devices during M19 C000 observation: {devices}")
        rows = adb_rows(log_path, f"{label}-extra")
        if rows:
            append_log(log_path, f"m19_c000_candidate_adb_rows={rows}")
        time.sleep(1.0)
    append_log(log_path, "m19_c000_self_download_seen=0")
    return None


def rollback_from_download(
    odin: Path,
    rollback_ap: Path,
    run_dir: Path,
    log_path: Path,
    rollback_target: str,
    android_wait_sec: int,
) -> int:
    devices = odin_devices(odin, log_path, "rollback-only")
    if len(devices) != 1:
        raise SystemExit(f"rollback-only requires exactly one Odin device, got {devices}")
    rollback_rc = flash_ap(odin, rollback_ap, devices[0], log_path, f"{rollback_target}_rollback")
    if rollback_rc != 0:
        return rollback_rc or 5
    serial = poll_android(log_path, android_wait_sec, expect_root=rollback_target == ROLLBACK_MAGISK)
    if serial is None:
        return 6
    collect_android_pstore(run_dir, log_path, "post_rollback", serial, marker=EXPECTED_M19_MARKER)
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m19-ap", type=Path, default=DEFAULT_M19_C000_AP)
    parser.add_argument("--m19-manifest", type=Path, default=DEFAULT_M19_C000_MANIFEST)
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
    log_path = run_dir / "s22plus_m19_c000_checkpoint_live_gate.txt"
    append_log(log_path, f"=== {utc_now()} s22plus m19 c000 checkpoint live gate ===")
    append_log(log_path, f"target={EXPECTED_TARGET}")

    odin = resolve(root, args.odin)
    m19_ap = resolve(root, args.m19_ap)
    m19_manifest = resolve(root, args.m19_manifest)
    magisk_rollback_ap = resolve(root, args.magisk_rollback_ap)
    stock_rollback_ap = resolve(root, args.stock_rollback_ap)
    rollback_ap = magisk_rollback_ap if args.rollback_target == ROLLBACK_MAGISK else stock_rollback_ap
    if not odin.is_file():
        raise SystemExit(f"odin4 missing: {odin}")

    verify_agents_exception(root, log_path)
    verify_ap(m19_ap, EXPECTED_M19_C000_AP_SHA256, "m19_c000_candidate", log_path)
    verify_m19_manifest(m19_manifest, log_path)
    verify_ap(magisk_rollback_ap, EXPECTED_MAGISK_AP_SHA256, "magisk_boot_rollback", log_path)
    verify_ap(stock_rollback_ap, EXPECTED_STOCK_BOOT_AP_SHA256, "stock_boot_fallback", log_path)

    if args.offline_check:
        print(f"offline-check ok: M19 C000 candidate and rollback APs verified; no device action; log={log_path}")
        return 0

    if args.rollback_from_download:
        if args.ack != ROLLBACK_ACK_TOKEN:
            raise SystemExit(f"--rollback-from-download requires --ack {ROLLBACK_ACK_TOKEN}")
        rc = rollback_from_download(odin, rollback_ap, run_dir, log_path, args.rollback_target, args.android_wait_sec)
        print(f"M19 C000 rollback-from-download completed rc={rc}; log={log_path}")
        return rc

    selected_serial = require_current_android(log_path, args.serial)
    verify_current_boot_hash(log_path, selected_serial)
    host_snapshot(run_dir, log_path, "dryrun_current", odin)

    if not args.live:
        print(
            "dry-run ok: M19 C000 candidate, rollback APs, AGENTS exception, "
            f"current boot hash, and Android preflight verified; log={log_path}"
        )
        return 0
    if args.ack != LIVE_ACK_TOKEN:
        raise SystemExit(f"--live requires --ack {LIVE_ACK_TOKEN}")

    reboot = run(["adb", "-s", selected_serial, "reboot", "download"], timeout=20.0)
    append_log(log_path, f"adb_reboot_download_rc={reboot.returncode}")
    append_log(log_path, reboot.stdout + reboot.stderr)
    odin_device = wait_for_odin(odin, log_path, "candidate-wait", args.odin_wait_sec)
    if odin_device is None:
        print("download mode did not appear for M19 C000 candidate flash", file=sys.stderr)
        return 2

    candidate_rc = flash_ap(odin, m19_ap, odin_device, log_path, "candidate")
    if candidate_rc != 0:
        print(f"M19 C000 candidate Odin flash failed rc={candidate_rc}; log={log_path}", file=sys.stderr)
        return candidate_rc or 3

    left_download = wait_for_odin_absent(
        odin,
        log_path,
        "post-candidate-disconnect",
        args.post_flash_disconnect_wait_sec,
    )
    if not left_download:
        print(
            "M19 C000 candidate flash completed but the original Odin device did not disconnect; "
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
        append_log(log_path, "m19_c000_result=no-proof-original-download-never-disconnected")
        collect_android_pstore(
            run_dir,
            log_path,
            "post_rollback_no_disconnect",
            post_rollback_serial,
            marker=EXPECTED_M19_MARKER,
        )
        return 7

    print("M19 C000 candidate flashed. Waiting for checkpoint-triggered download mode.")
    rollback_device = observe_until_odin(run_dir, log_path, args.self_download_wait_sec, odin)
    if rollback_device is None:
        print(
            "M19 C000 self-download did not appear. Enter download mode manually "
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
    collect_android_pstore(run_dir, log_path, "post_rollback", post_rollback_serial, marker=EXPECTED_M19_MARKER)
    print(f"M19 C000 live gate completed with self-download and rollback ok; log={log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
