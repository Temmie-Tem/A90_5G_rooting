#!/usr/bin/env python3
"""Guarded S22+ M34 S10A module-load download-beacon live gate.

Dry-run is the default. Live mode requires a fresh SHA-pinned AGENTS.md
exception and an explicit ack token.

S10A keeps the S9 89-module runtime recipe but changes the one-bit beacon:
after module load it checks /proc/modules for core substrate and max77705
modules. HIT self-enters Download mode; MISS parks and requires manual
Download rollback.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
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
    append_log,
    flash_ap,
    host_snapshot,
    odin_devices,
    poll_android,
    repo_root,
    require_current_android,
    resolve,
    run,
    sha256_file,
    verify_ap,
    wait_for_odin,
)
from s22plus_m25_hs_only_usb2_acm_live_gate import record_timeline_event, verify_partition_hash
from build_s22plus_m34_runtime_gadget_split import M34_S10A_PROC_MODULES_CORE_NAMES
from s22plus_m5_usb_acm_live_gate import verify_android_stability


LIVE_ACK_TOKEN = "S22PLUS-M34-S10A-MODULE-LOAD-BEACON-LIVE-GATE"
ROLLBACK_ACK_TOKEN = "S22PLUS-M34-S10A-MODULE-LOAD-BEACON-ROLLBACK-FROM-DOWNLOAD"

EXPECTED_TARGET = "SM-S906N/g0q/S906NKSS7FYG8"
EXPECTED_STAGE = "S10A"
EXPECTED_M34_MARKER = "S22_NATIVE_INIT_M34_RUNTIME_GADGET_SPLIT_S10A"
EXPECTED_M34_AP_SHA256 = "064cc0431e649eb78bc8c8d1d89fcd16d09426f898120edb3c31c375275e3182"
EXPECTED_M34_BOOT_SHA256 = "a1ca7a4bf64ec8ecfc56d28d3f5e8511e6045bb1b2513fbafdb4249f75e15217"
EXPECTED_M34_INIT_SHA256 = "f8ad5df4ef3ff5db7229b3c7f55f2453bc8fe5a72260ca539534e9cddbbdc4e8"
EXPECTED_M34_MODULE_LIST_SHA256 = "c07425f4c738b53822e9f6783a142a2b5eafd72a15bd34c06fb3b49357c8fe26"
EXPECTED_M34_TEMPLATE_SOURCE_SHA256 = "f5e116e65f7e0075a304c8ef36610fc1604055310ca28d7fad97eb1b5457b772"
EXPECTED_M34_KERNEL_SHA256 = "bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff"
EXPECTED_M34_BASE_BOOT_SHA256 = "2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e"
EXPECTED_MODULE_COUNT = 89
EXPECTED_MEMBER = "boot.img.lz4"
EXPECTED_MODULE_ENTRY = "s22plus_m34_s10a_runtime_gadget_split.modules"
EXPECTED_PROBE = "proc_modules_core_loaded"
EXPECTED_SCHEMA = "s22plus_m34_s10a_result_v1"
DISPLAY_SERIAL_REDACTED = "<S22_SERIAL_REDACTED>"

DEFAULT_M34_AP = Path("workspace/private/outputs/s22plus_native_init/m34_runtime_gadget_split_v0_11/S10A/odin4/AP.tar.md5")
DEFAULT_M34_MANIFEST = Path("workspace/private/outputs/s22plus_native_init/m34_runtime_gadget_split_v0_11/manifest.json")


@dataclass(frozen=True)
class RollbackResult:
    rc: int
    android_serial: str | None
    rollback_target: str
    rollback_device: str


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def resolve_run_dir(root: Path, requested: Path | None) -> Path:
    if requested is not None:
        run_dir = resolve(root, requested)
        run_dir.mkdir(parents=True, exist_ok=False)
        return run_dir
    base = resolve(root, DEFAULT_RUN_ROOT / f"s22plus_m34_s10a_module_load_beacon_live_gate_{utc_stamp()}")
    for suffix in range(100):
        run_dir = base if suffix == 0 else Path(f"{base}_{suffix:02d}")
        try:
            run_dir.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            continue
        return run_dir
    raise SystemExit(f"could not allocate unique run directory under {base.parent}")


def policy_required_markers() -> list[str]:
    return [
        "S22+ M34 S10A module-load download-beacon native-init boot-only",
        "workspace/public/src/scripts/revalidation/s22plus_m34_s10a_module_load_beacon_live_gate.py",
        LIVE_ACK_TOKEN,
        ROLLBACK_ACK_TOKEN,
        EXPECTED_TARGET,
        EXPECTED_STAGE,
        EXPECTED_M34_MARKER,
        EXPECTED_M34_AP_SHA256,
        EXPECTED_M34_BOOT_SHA256,
        EXPECTED_M34_INIT_SHA256,
        EXPECTED_M34_MODULE_LIST_SHA256,
        EXPECTED_M34_TEMPLATE_SOURCE_SHA256,
        EXPECTED_M34_KERNEL_SHA256,
        EXPECTED_M34_BASE_BOOT_SHA256,
        "module_load_probe=proc_modules_core_loaded",
        "s10a_module_load_probe=1",
        "proc_modules=1",
        "core_module_count=8",
        "both_graphs_closure=1",
        "devlink_supplier_closure=1",
        "substrate_load_set=waipio_devlink",
        "driver_load_only=1",
        "manual_power_write=0",
        "configfs_gadget=0",
        "udc_bind=0",
        "role_write_discriminator=0",
        "typec_readback=0",
        "functionfs=0",
        "stock_composite=0",
        "true_action=reboot_download",
        "false_action=park",
        "download-beacon-hit",
        "download-beacon-miss-parked-manual-download-required",
        *M34_S10A_PROC_MODULES_CORE_NAMES,
    ]


def missing_policy_markers(text: str) -> list[str]:
    normalized = " ".join(text.split())
    return [marker for marker in policy_required_markers() if marker not in normalized]


def verify_agents_exception(root: Path, log_path: Path) -> None:
    text = (root / "AGENTS.md").read_text(encoding="utf-8")
    missing = missing_policy_markers(text)
    append_log(log_path, f"agents_exception_missing={missing}")
    if missing:
        raise SystemExit(f"AGENTS.md missing S10A live authorization markers: {missing}")


def find_stage(data: dict[str, Any], label: str) -> dict[str, Any]:
    for stage in data.get("stages", []):
        if stage.get("label") == label:
            return stage
    raise SystemExit(f"M34 manifest does not contain {label} stage")


def verify_m34_manifest(path: Path, log_path: Path) -> None:
    if not path.is_file():
        raise SystemExit(f"M34 manifest missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    stage = find_stage(data, EXPECTED_STAGE)
    hashes = stage.get("hashes", {})
    safety = data.get("safety", {})
    matrix = data.get("matrix", {})
    closure = stage.get("closure", {})
    runtime_steps = stage.get("runtime_steps", {})
    init_info = stage.get("init", {})
    ramdisk = stage.get("ramdisk", {})
    append_log(log_path, f"m34_manifest_path={path}")
    append_log(log_path, f"m34_s10a_hashes={json.dumps(hashes, sort_keys=True)}")

    if data.get("target") != EXPECTED_TARGET:
        raise SystemExit(f"M34 target mismatch: {data.get('target')!r}")
    if data.get("hashes", {}).get("template_source") != EXPECTED_M34_TEMPLATE_SOURCE_SHA256:
        raise SystemExit("M34 template source hash mismatch")
    if data.get("hashes", {}).get("nochange_repack_boot") != EXPECTED_M34_BASE_BOOT_SHA256:
        raise SystemExit("M34 no-change MagiskBoot repack is not pinned to the known booting base")
    if data.get("magiskboot", {}).get("nochange_repack_byte_identical") is not True:
        raise SystemExit("M34 no-change MagiskBoot repack is not byte-identical")
    if matrix.get("host_build_order", [])[-1:] != [EXPECTED_STAGE]:
        raise SystemExit(f"M34 host-build order does not end with S10A: {matrix.get('host_build_order')!r}")
    if matrix.get("next_host_only_candidate") != EXPECTED_STAGE:
        raise SystemExit(f"M34 next host-only candidate mismatch: {matrix.get('next_host_only_candidate')!r}")
    if matrix.get("s10a_module_load_probe") != EXPECTED_PROBE:
        raise SystemExit(f"M34 S10A probe mismatch: {matrix.get('s10a_module_load_probe')!r}")
    if matrix.get("s10a_core_proc_modules") != M34_S10A_PROC_MODULES_CORE_NAMES:
        raise SystemExit(f"M34 S10A core module list mismatch: {matrix.get('s10a_core_proc_modules')!r}")
    if matrix.get("s10a_starts_from_s9_module_recipe") is not True:
        raise SystemExit("M34 S10A matrix does not prove S9 module recipe base")
    if matrix.get("s10a_skips_downstream_configfs_and_udc_to_isolate_module_load") is not True:
        raise SystemExit("M34 S10A matrix does not prove downstream USB isolation")

    expected_steps = {
        "configfs_gadget": False,
        "udc_none": False,
        "max_speed_high_speed": False,
        "usb_role_force": False,
        "ssusb_speed_high_speed": False,
        "ssusb_mode_peripheral": False,
        "udc_bind": False,
        "soft_connect": False,
        "stock_softdep_parity": True,
        "qmp_module_included": True,
        "eud_module_included": True,
        "ucsi_glink_included": True,
        "session_producer_parity": True,
        "max77705_session_modules_included": True,
        "typec_readback_markers": False,
        "geni_i2c_transport_parity": True,
        "typec_role_write_discriminator": False,
        "beacon_probe": None,
        "module_load_probe": EXPECTED_PROBE,
    }
    if runtime_steps != expected_steps:
        raise SystemExit(f"M34 S10A runtime steps mismatch: {runtime_steps!r}")

    required_hashes = {
        "ap_tar_md5": EXPECTED_M34_AP_SHA256,
        "boot_img": EXPECTED_M34_BOOT_SHA256,
        "base_boot": EXPECTED_M34_BASE_BOOT_SHA256,
        "kernel": EXPECTED_M34_KERNEL_SHA256,
        "m34_init": EXPECTED_M34_INIT_SHA256,
        "m34_modules": EXPECTED_M34_MODULE_LIST_SHA256,
    }
    for key, expected in required_hashes.items():
        if hashes.get(key) != expected:
            raise SystemExit(f"M34 S10A manifest hash {key} mismatch: {hashes.get(key)!r} != {expected!r}")
    if stage.get("stage_number") != 12:
        raise SystemExit(f"M34 S10A stage number mismatch: {stage.get('stage_number')!r}")
    if stage.get("tar_members") != [EXPECTED_MEMBER]:
        raise SystemExit(f"M34 S10A tar members mismatch: {stage.get('tar_members')!r}")
    if closure.get("module_count") != EXPECTED_MODULE_COUNT:
        raise SystemExit(f"M34 S10A module count mismatch: {closure.get('module_count')!r}")
    if closure.get("module_sha256") != EXPECTED_M34_MODULE_LIST_SHA256:
        raise SystemExit("M34 S10A module list SHA mismatch")
    if ramdisk.get("added_subset_entry") != EXPECTED_MODULE_ENTRY:
        raise SystemExit(f"M34 S10A module-list ramdisk entry mismatch: {ramdisk.get('added_subset_entry')!r}")
    if ramdisk.get("module_files_injected_into_boot_ramdisk") != 0:
        raise SystemExit("M34 S10A must not inject module binaries into boot ramdisk")

    required_strings = set(init_info.get("required_strings", []))
    for required in [
        EXPECTED_M34_MARKER,
        "version=0.9",
        "stage=S10A",
        "runtime_step=S10A",
        "module_count=89",
        "reboot_request=download",
        "download_beacon=1",
        "configfs_gadget=0",
        "udc_bind=0",
        "role_write_discriminator=0",
        "typec_readback=0",
        "devlink_supplier_closure=1",
        "both_graphs_closure=1",
        "module_load_probe=proc_modules_core_loaded",
        "s10a_module_load_probe=1",
        "phase=s10a_module_load_probe",
        "predicate=proc_modules_core_loaded",
        "expected=8",
        "/proc/modules",
        "true_action=reboot_download",
        "false_action=park",
        "phase=s10a_module_load_reboot_returned",
    ]:
        if required not in required_strings:
            raise SystemExit(f"M34 S10A required string missing from manifest: {required}")
    for forbidden in [
        "s8_beacon_probe=typec_port_or_i2c_any_0066",
        "phase=s9_b1_probe",
        "/sys/bus/i2c/devices",
        "/sys/class/typec/port0",
        "phase=configfs_done",
        "/config/usb_gadget/g1/UDC",
        "/sys/class/udc",
        "a600000.dwc3",
        "phase=udc_bind",
        "phase=typec_role_write",
    ]:
        if forbidden in required_strings:
            raise SystemExit(f"M34 S10A manifest unexpectedly requires forbidden string: {forbidden}")
    for key, expected in {
        "live_flash_authorized": False,
        "requires_new_sha_pinned_agents_exception_before_flash": True,
        "stage_s10a_no_configfs_udc_or_role_write": True,
        "stage_s10a_driver_load_only_no_manual_power_write": True,
    }.items():
        if safety.get(key) != expected:
            raise SystemExit(f"M34 S10A safety {key} mismatch: {safety.get(key)!r} != {expected!r}")


def verify_m34_artifacts(
    *,
    m34_ap: Path,
    m34_manifest: Path,
    magisk_rollback_ap: Path,
    stock_rollback_ap: Path,
    log_path: Path,
) -> None:
    verify_ap(m34_ap, EXPECTED_M34_AP_SHA256, "m34_s10a_candidate", log_path)
    verify_m34_manifest(m34_manifest, log_path)
    verify_ap(magisk_rollback_ap, EXPECTED_MAGISK_AP_SHA256, "magisk_boot_rollback", log_path)
    verify_ap(stock_rollback_ap, EXPECTED_STOCK_BOOT_AP_SHA256, "stock_boot_fallback", log_path)


def observe_download_beacon(
    *,
    run_dir: Path,
    log_path: Path,
    odin: Path,
    observe_sec: int,
    snapshot_interval_sec: float,
) -> tuple[str, str | None]:
    deadline = time.monotonic() + observe_sec
    next_snapshot = 0.0
    while time.monotonic() < deadline:
        devices = odin_devices(odin, log_path, "candidate-beacon-observe")
        if len(devices) > 1:
            raise SystemExit(f"refusing ambiguous Odin devices during S10A observation: {devices}")
        if len(devices) == 1:
            host_snapshot(run_dir, log_path, "candidate_beacon_hit", odin)
            append_log(log_path, f"s10a_result=download-beacon-hit odin_device={devices[0]}")
            return "download-beacon-hit", devices[0]
        now = time.monotonic()
        if now >= next_snapshot:
            host_snapshot(run_dir, log_path, "candidate_observe", odin)
            next_snapshot = now + snapshot_interval_sec
        time.sleep(1.0)
    append_log(log_path, "s10a_result=download-beacon-miss-parked-manual-download-required")
    return "download-beacon-miss-parked-manual-download-required", None


def wait_for_odin_absent(odin: Path, log_path: Path, label: str, wait_sec: int) -> bool:
    deadline = time.monotonic() + wait_sec
    saw_absent = False
    while time.monotonic() < deadline:
        devices = odin_devices(odin, log_path, label)
        if len(devices) == 0:
            saw_absent = True
            break
        if len(devices) > 1:
            raise SystemExit(f"refusing ambiguous Odin devices while waiting for disconnect: {devices}")
        time.sleep(1.0)
    append_log(log_path, f"{label}_odin_absent={int(saw_absent)}")
    return saw_absent


def rollback_boot_only_from_download(
    *,
    odin: Path,
    rollback_ap: Path,
    stock_boot_fallback_ap: Path,
    odin_device: str,
    run_dir: Path,
    log_path: Path,
    rollback_target: str,
    android_wait_sec: int,
    label: str,
) -> RollbackResult:
    if rollback_target not in {ROLLBACK_MAGISK, ROLLBACK_STOCK}:
        raise SystemExit(f"invalid rollback target: {rollback_target}")
    primary_target = rollback_target
    primary_ap = rollback_ap if rollback_target == ROLLBACK_MAGISK else stock_boot_fallback_ap
    fallback_target = ROLLBACK_STOCK if rollback_target == ROLLBACK_MAGISK else ROLLBACK_MAGISK
    fallback_ap = stock_boot_fallback_ap if rollback_target == ROLLBACK_MAGISK else rollback_ap

    record_timeline_event(run_dir, "rollback_flash_start")
    rc = flash_ap(odin, primary_ap, odin_device, log_path, f"{label}_{primary_target}_rollback")
    record_timeline_event(run_dir, "rollback_flash_done")
    used_target = primary_target
    used_device = odin_device
    if rc != 0:
        append_log(log_path, f"{label}_primary_rollback_failed_rc={rc}")
        retry_device = wait_for_odin(odin, log_path, f"{label}_fallback_wait", 20)
        if retry_device is None:
            return RollbackResult(rc=rc or 6, android_serial=None, rollback_target=used_target, rollback_device=used_device)
        record_timeline_event(run_dir, "rollback_flash_start")
        rc = flash_ap(odin, fallback_ap, retry_device, log_path, f"{label}_{fallback_target}_rollback")
        record_timeline_event(run_dir, "rollback_flash_done")
        used_target = fallback_target
        used_device = retry_device
    if rc != 0:
        return RollbackResult(rc=rc, android_serial=None, rollback_target=used_target, rollback_device=used_device)

    android = poll_android(log_path, android_wait_sec, expect_root=(used_target == ROLLBACK_MAGISK))
    if android is None:
        return RollbackResult(rc=5, android_serial=None, rollback_target=used_target, rollback_device=used_device)
    record_timeline_event(run_dir, "rollback_boot_ready")
    expected_boot = EXPECTED_M34_BASE_BOOT_SHA256 if used_target == ROLLBACK_MAGISK else None
    if expected_boot:
        verify_partition_hash(log_path, android, "boot", expected_boot, f"{label}_boot_restore")
    return RollbackResult(rc=0, android_serial=android, rollback_target=used_target, rollback_device=used_device)


def write_result_summary(
    run_dir: Path,
    log_path: Path,
    *,
    result: str,
    rc: int,
    rollback_target: str,
    rollback_device: str | None = None,
    android_serial: str | None = None,
    note: str | None = None,
) -> None:
    payload: dict[str, Any] = {
        "schema": EXPECTED_SCHEMA,
        "timestamp_utc": utc_now(),
        "target": EXPECTED_TARGET,
        "stage": EXPECTED_STAGE,
        "result": result,
        "rc": rc,
        "rollback_target": rollback_target,
        "candidate_ap_sha256": EXPECTED_M34_AP_SHA256,
        "candidate_boot_sha256": EXPECTED_M34_BOOT_SHA256,
        "candidate_init_sha256": EXPECTED_M34_INIT_SHA256,
        "base_boot_sha256": EXPECTED_M34_BASE_BOOT_SHA256,
    }
    if rollback_device is not None:
        payload["rollback_device"] = rollback_device
    if android_serial is not None:
        payload["android_serial"] = DISPLAY_SERIAL_REDACTED
    if note is not None:
        payload["note"] = note
    path = run_dir / "result.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    append_log(log_path, f"result_json={path}")
    append_log(log_path, f"result_summary={json.dumps(payload, sort_keys=True)}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m34-ap", type=Path, default=DEFAULT_M34_AP)
    parser.add_argument("--m34-manifest", type=Path, default=DEFAULT_M34_MANIFEST)
    parser.add_argument("--magisk-rollback-ap", type=Path, default=DEFAULT_MAGISK_ROLLBACK_AP)
    parser.add_argument("--stock-rollback-ap", type=Path, default=DEFAULT_STOCK_ROLLBACK_AP)
    parser.add_argument("--odin", type=Path, default=DEFAULT_ODIN)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--serial")
    parser.add_argument("--observe-sec", type=int, default=90)
    parser.add_argument("--snapshot-interval-sec", type=float, default=5.0)
    parser.add_argument("--post-flash-disconnect-wait-sec", type=int, default=20)
    parser.add_argument("--manual-download-wait-sec", type=int, default=300)
    parser.add_argument("--odin-wait-sec", type=int, default=90)
    parser.add_argument("--android-wait-sec", type=int, default=240)
    parser.add_argument("--android-stability-samples", type=int, default=2)
    parser.add_argument("--android-stability-interval-sec", type=float, default=2.0)
    parser.add_argument("--rollback-target", choices=[ROLLBACK_MAGISK, ROLLBACK_STOCK], default=ROLLBACK_MAGISK)
    parser.add_argument("--rollback-from-download", action="store_true")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--ack")
    args = parser.parse_args(argv)

    root = repo_root()
    run_dir = resolve_run_dir(root, args.run_dir)
    log_path = run_dir / "s22plus_m34_s10a_module_load_beacon_live_gate.txt"
    append_log(log_path, f"=== {utc_now()} s22plus M34 S10A module-load beacon live gate ===")

    m34_ap = resolve(root, args.m34_ap)
    m34_manifest = resolve(root, args.m34_manifest)
    magisk_rollback_ap = resolve(root, args.magisk_rollback_ap)
    stock_rollback_ap = resolve(root, args.stock_rollback_ap)
    odin = resolve(root, args.odin)

    verify_m34_artifacts(
        m34_ap=m34_ap,
        m34_manifest=m34_manifest,
        magisk_rollback_ap=magisk_rollback_ap,
        stock_rollback_ap=stock_rollback_ap,
        log_path=log_path,
    )
    verify_agents_exception(root, log_path)

    if args.rollback_from_download:
        if args.ack != ROLLBACK_ACK_TOKEN:
            raise SystemExit(f"--rollback-from-download requires --ack {ROLLBACK_ACK_TOKEN}")
        devices = odin_devices(odin, log_path, "rollback-only")
        if len(devices) != 1:
            raise SystemExit(f"S10A rollback requires exactly one Odin device, got {devices}")
        rollback = rollback_boot_only_from_download(
            odin=odin,
            rollback_ap=magisk_rollback_ap,
            stock_boot_fallback_ap=stock_rollback_ap,
            odin_device=devices[0],
            run_dir=run_dir,
            log_path=log_path,
            rollback_target=args.rollback_target,
            android_wait_sec=args.android_wait_sec,
            label="rollback_only",
        )
        write_result_summary(
            run_dir,
            log_path,
            result="rollback-only-no-s10a-proof",
            rc=rollback.rc,
            rollback_target=rollback.rollback_target,
            rollback_device=rollback.rollback_device,
            android_serial=rollback.android_serial,
        )
        print(f"M34 S10A rollback-from-download completed rc={rollback.rc}; log={log_path}")
        return rollback.rc

    selected_serial = require_current_android(log_path, args.serial)
    verify_android_stability(log_path, selected_serial, args.android_stability_samples, args.android_stability_interval_sec)
    verify_partition_hash(log_path, selected_serial, "boot", EXPECTED_M34_BASE_BOOT_SHA256, "current")
    host_snapshot(run_dir, log_path, "dryrun_current", odin)

    if not args.live:
        print(f"dry-run ok: M34 S10A candidate, rollback APs, AGENTS exception, Android, and boot hash verified; log={log_path}")
        return 0
    if args.ack != LIVE_ACK_TOKEN:
        raise SystemExit(f"--live requires --ack {LIVE_ACK_TOKEN}")

    record_timeline_event(run_dir, "live_session_start")
    print("M34 S10A live gate starting. HIT should self-enter Download mode if /proc/modules core set is loaded.", flush=True)
    reboot = run(["adb", "-s", selected_serial, "reboot", "download"], timeout=20.0)
    append_log(log_path, f"adb_reboot_download_rc={reboot.returncode}")
    append_log(log_path, reboot.stdout + reboot.stderr)
    odin_device = wait_for_odin(odin, log_path, "candidate-wait", args.odin_wait_sec)
    if odin_device is None:
        record_timeline_event(run_dir, "live_session_end")
        write_result_summary(run_dir, log_path, result="candidate-download-mode-missing", rc=2, rollback_target=args.rollback_target)
        print("download mode did not appear for M34 S10A candidate flash", file=sys.stderr)
        return 2

    record_timeline_event(run_dir, "candidate_flash_start")
    candidate_rc = flash_ap(odin, m34_ap, odin_device, log_path, "candidate")
    record_timeline_event(run_dir, "candidate_flash_done")
    if candidate_rc != 0:
        record_timeline_event(run_dir, "live_session_end")
        write_result_summary(run_dir, log_path, result="candidate-flash-failed", rc=candidate_rc or 3, rollback_target=args.rollback_target, rollback_device=odin_device)
        return candidate_rc or 3

    left_download = wait_for_odin_absent(odin, log_path, "post-candidate-disconnect", args.post_flash_disconnect_wait_sec)
    if not left_download:
        rollback_device = wait_for_odin(odin, log_path, "rollback-still-download-wait", 5)
        if rollback_device is None:
            record_timeline_event(run_dir, "live_session_end")
            write_result_summary(run_dir, log_path, result="no-proof-original-download-never-disconnected", rc=4, rollback_target=args.rollback_target)
            return 4
        rollback = rollback_boot_only_from_download(
            odin=odin,
            rollback_ap=magisk_rollback_ap,
            stock_boot_fallback_ap=stock_rollback_ap,
            odin_device=rollback_device,
            run_dir=run_dir,
            log_path=log_path,
            rollback_target=args.rollback_target,
            android_wait_sec=args.android_wait_sec,
            label="no_disconnect",
        )
        record_timeline_event(run_dir, "live_session_end")
        write_result_summary(run_dir, log_path, result="no-proof-original-download-never-disconnected", rc=rollback.rc or 7, rollback_target=rollback.rollback_target, rollback_device=rollback.rollback_device, android_serial=rollback.android_serial)
        return rollback.rc or 7

    record_timeline_event(run_dir, "candidate_boot_ready")
    print(f"M34 S10A candidate flashed. Observing download beacon for {args.observe_sec}s.", flush=True)
    result, rollback_device = observe_download_beacon(
        run_dir=run_dir,
        log_path=log_path,
        odin=odin,
        observe_sec=args.observe_sec,
        snapshot_interval_sec=args.snapshot_interval_sec,
    )

    if result == "download-beacon-hit":
        if rollback_device is None:
            record_timeline_event(run_dir, "live_session_end")
            write_result_summary(run_dir, log_path, result=result, rc=4, rollback_target=args.rollback_target)
            return 4
        rollback = rollback_boot_only_from_download(
            odin=odin,
            rollback_ap=magisk_rollback_ap,
            stock_boot_fallback_ap=stock_rollback_ap,
            odin_device=rollback_device,
            run_dir=run_dir,
            log_path=log_path,
            rollback_target=args.rollback_target,
            android_wait_sec=args.android_wait_sec,
            label="beacon_hit",
        )
        record_timeline_event(run_dir, "live_session_end")
        write_result_summary(run_dir, log_path, result=result, rc=rollback.rc, rollback_target=rollback.rollback_target, rollback_device=rollback.rollback_device, android_serial=rollback.android_serial)
        print(f"M34 S10A live gate completed rc={rollback.rc}; result={result}; log={log_path}")
        return rollback.rc

    print(f"M34 S10A result={result}. Enter Download mode manually for rollback now; waiting up to {args.manual_download_wait_sec}s.", flush=True)
    rollback_device = wait_for_odin(odin, log_path, "manual-rollback-wait", args.manual_download_wait_sec)
    if rollback_device is None:
        record_timeline_event(run_dir, "live_session_end")
        write_result_summary(run_dir, log_path, result=result, rc=4, rollback_target=args.rollback_target, note="manual Download rollback did not appear within bounded wait")
        print(f"M34 S10A MISS observed, but manual Download mode did not appear. Run --rollback-from-download after entering Download mode. log={log_path}", file=sys.stderr)
        return 4
    rollback = rollback_boot_only_from_download(
        odin=odin,
        rollback_ap=magisk_rollback_ap,
        stock_boot_fallback_ap=stock_rollback_ap,
        odin_device=rollback_device,
        run_dir=run_dir,
        log_path=log_path,
        rollback_target=args.rollback_target,
        android_wait_sec=args.android_wait_sec,
        label="manual_after_miss",
    )
    record_timeline_event(run_dir, "live_session_end")
    write_result_summary(run_dir, log_path, result=result, rc=rollback.rc, rollback_target=rollback.rollback_target, rollback_device=rollback.rollback_device, android_serial=rollback.android_serial)
    print(f"M34 S10A live gate completed rc={rollback.rc}; result={result}; log={log_path}")
    return rollback.rc


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
