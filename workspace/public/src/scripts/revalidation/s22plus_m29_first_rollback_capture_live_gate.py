#!/usr/bin/env python3
"""Guarded S22+ M29 first-rollback retained-log capture live gate.

Dry-run is the default. Live mode is inert until a fresh SHA-pinned
AGENTS.md exception is promoted.

M29 reuses the already-built M28 dependency-complete S24 candidate and the M25
DTBO high-speed cap, but changes the observation contract: after candidate
return to Download mode and boot rollback, capture retained evidence at the
FIRST post-candidate Android boot, before any stock-DTBO rollback can advance
the retained `/proc/last_kmsg` window.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import s22plus_m28_dep_complete_live_gate as m28
from s22plus_m23_dts_exact_qmp_reset_summary_live_gate import collect_reset_reason
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
    append_log,
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
from s22plus_m5_usb_acm_live_gate import verify_android_stability
from s22plus_m25_hs_only_usb2_acm_live_gate import (
    EXPECTED_BASE_BOOT_SHA256,
    EXPECTED_M25_DTBO_AP_SHA256,
    EXPECTED_M25_PATCHED_DTBO_RAW_SHA256,
    EXPECTED_M25_STOCK_DTBO_ROLLBACK_AP_SHA256,
    EXPECTED_STOCK_DTBO_RAW_SHA256,
    EXPECTED_STOCK_VENDOR_BOOT_SHA256,
    read_partition_hash,
    record_timeline_event,
    restore_dtbo_from_android,
    verify_partition_hash,
)


LIVE_ACK_TOKEN = "S22PLUS-M29-FIRST-ROLLBACK-CAPTURE-LIVE-GATE"
ROLLBACK_ACK_TOKEN = "S22PLUS-M29-FIRST-ROLLBACK-CAPTURE-ROLLBACK-FROM-DOWNLOAD"
RESTORE_DTBO_ACK_TOKEN = "S22PLUS-M29-FIRST-ROLLBACK-CAPTURE-RESTORE-STOCK-DTBO"

EXPECTED_TARGET = m28.EXPECTED_TARGET
EXPECTED_M29_MARKER = m28.EXPECTED_M28_MARKER
EXPECTED_M29_SOURCE_CANDIDATE_SHA256 = m28.EXPECTED_M28_SOURCE_SHA256
EXPECTED_M29_MODULES_RAMDISK = m28.EXPECTED_M28_MODULES_RAMDISK
EXPECTED_M29_MANIFEST_SHA256 = m28.EXPECTED_M28_MANIFEST_SHA256
EXPECTED_MODULES_DEP_SHA256 = m28.EXPECTED_MODULES_DEP_SHA256

DEFAULT_M29_MANIFEST = m28.DEFAULT_M28_MANIFEST
DEFAULT_M25_DTBO_AP = m28.DEFAULT_M25_DTBO_AP
DEFAULT_M25_STOCK_DTBO_AP = m28.DEFAULT_M25_STOCK_DTBO_AP
DEFAULT_M29_LABELS = ("S24",)

RESET_SURFACE_FILES = (
    "/proc/reset_summary",
    "/proc/reset_klog",
    "/proc/reset_history",
    "/proc/reset_tzlog",
)


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def resolve_run_dir(root: Path, requested: Path | None) -> Path:
    if requested is not None:
        run_dir = resolve(root, requested)
        run_dir.mkdir(parents=True, exist_ok=False)
        return run_dir
    base = resolve(root, DEFAULT_RUN_ROOT / f"s22plus_m29_first_rollback_capture_live_gate_{utc_stamp()}")
    for suffix in range(100):
        run_dir = base if suffix == 0 else Path(f"{base}_{suffix:02d}")
        try:
            run_dir.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            continue
        return run_dir
    raise SystemExit(f"could not allocate unique run directory under {base.parent}")


def selected_candidates(labels: list[str] | None) -> list[m28.M28Candidate]:
    if not labels:
        labels = ["S24"]
    normalized = [label.upper() for label in labels]
    if normalized != ["S24"]:
        raise SystemExit(
            "M29 first-rollback capture is scoped to exactly S24; "
            f"got={normalized}. F43 remains unauthorized until S24 failure evidence is captured."
        )
    return [m28.EXPECTED_M28_BY_LABEL["S24"]]


def policy_required_markers() -> list[str]:
    s24 = m28.EXPECTED_M28_BY_LABEL["S24"]
    return [
        "S22+ M29 first-rollback retained-log capture boot+DTBO",
        "workspace/public/src/scripts/revalidation/s22plus_m29_first_rollback_capture_live_gate.py",
        LIVE_ACK_TOKEN,
        ROLLBACK_ACK_TOKEN,
        RESTORE_DTBO_ACK_TOKEN,
        EXPECTED_TARGET,
        EXPECTED_M29_MARKER,
        EXPECTED_M29_SOURCE_CANDIDATE_SHA256,
        EXPECTED_M29_MODULES_RAMDISK,
        EXPECTED_MODULES_DEP_SHA256,
        EXPECTED_M25_DTBO_AP_SHA256,
        EXPECTED_M25_PATCHED_DTBO_RAW_SHA256,
        EXPECTED_M25_STOCK_DTBO_ROLLBACK_AP_SHA256,
        EXPECTED_BASE_BOOT_SHA256,
        EXPECTED_STOCK_DTBO_RAW_SHA256,
        EXPECTED_STOCK_VENDOR_BOOT_SHA256,
        EXPECTED_MAGISK_AP_SHA256,
        EXPECTED_STOCK_BOOT_AP_SHA256,
        "S24 only",
        "F43 remains unauthorized",
        "first rollback boot capture before stock DTBO rollback",
        "pre-candidate retained-log baseline capture",
        "compare pre-candidate and first-rollback last_kmsg sha256",
        "/proc/last_kmsg",
        *RESET_SURFACE_FILES,
        "Magisk boot rollback",
        "stock DTBO rollback after first capture",
        "manual Download contamination",
        s24.label,
        str(s24.module_count),
        s24.modules_sha256,
        s24.ap_sha256,
        s24.boot_sha256,
        s24.init_sha256,
        *s24.reincluded_hard_suppliers,
    ]


def missing_policy_markers(text: str) -> list[str]:
    normalized = " ".join(text.split())
    return [marker for marker in policy_required_markers() if marker not in normalized]


def verify_agents_exception(root: Path, log_path: Path) -> None:
    agents = (root / "AGENTS.md").read_text(encoding="utf-8")
    missing = missing_policy_markers(agents)
    append_log(log_path, f"agents_exception_missing={missing}")
    if missing:
        raise SystemExit(f"AGENTS.md missing M29 first-rollback capture authorization markers: {missing}")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(repo_root()))
    except ValueError:
        return str(path)


def retained_fingerprint(run_dir: Path, log_path: Path, label: str) -> dict[str, Any]:
    last_kmsg_path = run_dir / "android_pstore" / f"{label}_last_kmsg.bin"
    payload = last_kmsg_path.read_bytes() if last_kmsg_path.exists() else b""
    scan = {
        "label": label,
        "last_kmsg_path": display_path(last_kmsg_path) if last_kmsg_path.exists() else "",
        "last_kmsg_bytes": len(payload),
        "last_kmsg_sha256": sha256_bytes(payload),
        "m29_marker_count": payload.count(EXPECTED_M29_MARKER.encode("ascii")),
        "s22_native_count": payload.count(b"S22_NATIVE_INIT"),
        "android_reboot_download_count": payload.count(b"sys.powerctl='reboot,download'"),
        "android_really_probe_count": payload.count(b"really_probe"),
        "kernel_panic_count": payload.lower().count(b"kernel panic"),
        "watchdog_count": payload.lower().count(b"watchdog"),
        "unknown_symbol_count": payload.count(b"Unknown symbol"),
    }
    out_path = run_dir / f"{label}_last_kmsg_fingerprint.json"
    out_path.write_text(json.dumps(scan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    append_log(log_path, f"{label}_last_kmsg_fingerprint={json.dumps(scan, sort_keys=True)}")
    return scan


def collect_retained_and_reset_surfaces(
    run_dir: Path,
    log_path: Path,
    serial: str,
    label: str,
    *,
    timing: str,
) -> dict[str, Any]:
    record_timeline_event(run_dir, f"{label}_capture_start")
    marker_found = m28.collect_android_pstore(run_dir, log_path, label, serial, marker=EXPECTED_M29_MARKER)
    fingerprint = retained_fingerprint(run_dir, log_path, label)
    reset_dir = run_dir / f"{label}_reset_reason"
    reset_dir.mkdir(parents=True, exist_ok=False)
    summary = collect_reset_reason(reset_dir, serial)
    summary["run_dir"] = display_path(reset_dir)
    summary["m29_capture_timing"] = timing
    summary["m29_marker_found"] = bool(marker_found)
    summary["last_kmsg_fingerprint"] = fingerprint
    summary_path = reset_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    append_log(log_path, f"{label}_capture_marker_found={int(marker_found)}")
    append_log(log_path, f"{label}_reset_reason_result={summary.get('result')}")
    append_log(log_path, f"{label}_reset_reason_summary_path={summary_path}")
    record_timeline_event(run_dir, f"{label}_capture_done")
    return summary


def compare_retained_fingerprints(run_dir: Path, log_path: Path, before_label: str, after_label: str) -> dict[str, Any]:
    before = json.loads((run_dir / f"{before_label}_last_kmsg_fingerprint.json").read_text(encoding="utf-8"))
    after = json.loads((run_dir / f"{after_label}_last_kmsg_fingerprint.json").read_text(encoding="utf-8"))
    comparison = {
        "before_label": before_label,
        "after_label": after_label,
        "same_sha256": before.get("last_kmsg_sha256") == after.get("last_kmsg_sha256"),
        "before_sha256": before.get("last_kmsg_sha256"),
        "after_sha256": after.get("last_kmsg_sha256"),
        "before_bytes": before.get("last_kmsg_bytes"),
        "after_bytes": after.get("last_kmsg_bytes"),
        "after_m29_marker_count": after.get("m29_marker_count"),
        "after_s22_native_count": after.get("s22_native_count"),
        "after_android_reboot_download_count": after.get("android_reboot_download_count"),
        "after_watchdog_count": after.get("watchdog_count"),
        "after_kernel_panic_count": after.get("kernel_panic_count"),
        "after_unknown_symbol_count": after.get("unknown_symbol_count"),
    }
    out_path = run_dir / f"{after_label}_vs_{before_label}_last_kmsg_comparison.json"
    out_path.write_text(json.dumps(comparison, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    append_log(log_path, f"{after_label}_vs_{before_label}_last_kmsg_comparison={json.dumps(comparison, sort_keys=True)}")
    return comparison


def reboot_android_to_download(serial: str, log_path: Path, label: str) -> None:
    result = run(["adb", "-s", serial, "reboot", "download"], timeout=20.0)
    append_log(log_path, f"{label}_adb_reboot_download_rc={result.returncode}")
    append_log(log_path, result.stdout + result.stderr)
    if result.returncode != 0:
        raise SystemExit(f"{label} adb reboot download failed rc={result.returncode}")


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


def observe_self_download(run_dir: Path, log_path: Path, seconds: int, odin: Path, label: str) -> str | None:
    host_snapshot(run_dir, log_path, f"after_{label}_candidate_flash", odin)
    deadline = time.monotonic() + seconds
    iteration = 0
    while time.monotonic() < deadline:
        iteration += 1
        snap_label = f"m29_{label}_self_download_{iteration:03d}"
        host_snapshot(run_dir, log_path, snap_label, odin)
        devices = odin_devices(odin, log_path, f"{snap_label}-odin")
        if len(devices) == 1:
            append_log(log_path, f"m29_{label}_self_download_seen=1 device={devices[0]}")
            return devices[0]
        if len(devices) > 1:
            raise SystemExit(f"refusing ambiguous Odin devices during M29 {label} observation: {devices}")
        rows = adb_rows(log_path, f"{snap_label}-adb")
        usable = [row for row in rows if row[1] == "device"]
        if usable:
            append_log(log_path, f"m29_{label}_unexpected_adb_rows={usable}")
        time.sleep(1.0)
    append_log(log_path, f"m29_{label}_self_download_seen=0")
    return None


def rollback_boot_only_from_odin_device(
    *,
    odin: Path,
    boot_rollback_ap: Path,
    stock_boot_fallback_ap: Path,
    odin_device: str,
    run_dir: Path,
    log_path: Path,
    rollback_target: str,
    android_wait_sec: int,
    label: str,
) -> tuple[int, str | None]:
    record_timeline_event(run_dir, f"{label}_rollback_flash_start")
    record_timeline_event(run_dir, "rollback_flash_start")
    rollback_rc = flash_ap(odin, boot_rollback_ap, odin_device, log_path, f"{label}_{rollback_target}_boot_rollback")
    record_timeline_event(run_dir, "rollback_flash_done")
    record_timeline_event(run_dir, f"{label}_rollback_flash_done")
    if rollback_rc != 0 and rollback_target == ROLLBACK_MAGISK:
        append_log(log_path, f"m29_{label}_magisk_rollback_failed_attempting_stock_fallback=1")
        fallback_device = wait_for_odin(odin, log_path, f"{label}-stock-fallback-wait", 30)
        if fallback_device:
            record_timeline_event(run_dir, f"{label}_stock_fallback_flash_start")
            rollback_rc = flash_ap(odin, stock_boot_fallback_ap, fallback_device, log_path, f"{label}_stock_boot_fallback")
            record_timeline_event(run_dir, f"{label}_stock_fallback_flash_done")
            rollback_target = ROLLBACK_STOCK
    if rollback_rc != 0:
        return (rollback_rc or 5, None)

    android = poll_android(log_path, android_wait_sec, expect_root=rollback_target == ROLLBACK_MAGISK)
    if android is None:
        return (6, None)
    if rollback_target == ROLLBACK_MAGISK:
        verify_partition_hash(log_path, android, "boot", EXPECTED_BASE_BOOT_SHA256, f"{label}_boot_restore")
    else:
        append_log(log_path, f"m29_{label}_boot_restore_hash_check=skipped rollback_target=stock")
    record_timeline_event(run_dir, "rollback_boot_ready")
    record_timeline_event(run_dir, f"{label}_rollback_boot_ready")
    collect_retained_and_reset_surfaces(
        run_dir,
        log_path,
        android,
        f"first_post_m29_{label}_rollback",
        timing="first-post-candidate-rollback-before-stock-dtbo-rollback",
    )
    return (0, android)


def restore_stock_dtbo_if_needed(
    *,
    odin: Path,
    dtbo_rollback_ap: Path,
    run_dir: Path,
    log_path: Path,
    serial: str,
    odin_wait_sec: int,
    android_wait_sec: int,
) -> int:
    current = read_partition_hash(log_path, serial, "dtbo", "pre_final_stock_dtbo_restore")
    if current == EXPECTED_STOCK_DTBO_RAW_SHA256:
        append_log(log_path, "final_stock_dtbo_restore_already_stock=1")
        return 0
    if current != EXPECTED_M25_PATCHED_DTBO_RAW_SHA256:
        raise SystemExit(f"refusing final stock DTBO restore from unexpected DTBO hash {current}")
    return restore_dtbo_from_android(
        odin=odin,
        dtbo_rollback_ap=dtbo_rollback_ap,
        run_dir=run_dir,
        log_path=log_path,
        serial=serial,
        odin_wait_sec=odin_wait_sec,
        android_wait_sec=android_wait_sec,
    )


def run_one_candidate(
    *,
    candidate: m28.M28Candidate,
    odin: Path,
    boot_ap: Path,
    boot_rollback_ap: Path,
    stock_boot_fallback_ap: Path,
    run_dir: Path,
    log_path: Path,
    serial: str,
    rollback_target: str,
    odin_wait_sec: int,
    android_wait_sec: int,
    self_download_wait_sec: int,
    post_flash_disconnect_wait_sec: int,
) -> tuple[int, str | None, str]:
    label = candidate.label
    verify_partition_hash(log_path, serial, "boot", EXPECTED_BASE_BOOT_SHA256, f"pre_{label}")
    verify_partition_hash(log_path, serial, "dtbo", EXPECTED_M25_PATCHED_DTBO_RAW_SHA256, f"pre_{label}")
    pre_label = f"pre_m29_{label}_candidate"
    collect_retained_and_reset_surfaces(
        run_dir,
        log_path,
        serial,
        pre_label,
        timing="pre-candidate-baseline-after-dtbo-cap-before-candidate-reboot-download",
    )
    reboot_android_to_download(serial, log_path, f"m29_{label}_boot_candidate")
    odin_device = wait_for_odin(odin, log_path, f"m29-{label}-boot-candidate-wait", odin_wait_sec)
    if odin_device is None:
        return (2, None, "no-download-before-candidate")

    record_timeline_event(run_dir, f"{label}_candidate_flash_start")
    record_timeline_event(run_dir, "candidate_flash_start")
    candidate_rc = flash_ap(odin, boot_ap, odin_device, log_path, f"m29_{label}_boot_candidate")
    record_timeline_event(run_dir, "candidate_flash_done")
    record_timeline_event(run_dir, f"{label}_candidate_flash_done")
    if candidate_rc != 0:
        return (candidate_rc or 3, None, "candidate-flash-failed")

    left_download = wait_for_odin_absent(odin, log_path, f"m29-{label}-post-candidate-disconnect", post_flash_disconnect_wait_sec)
    if not left_download:
        append_log(log_path, f"m29_{label}_result=no-proof-original-download-never-disconnected")
        rollback_device = wait_for_odin(odin, log_path, f"m29-{label}-rollback-still-download-wait", 5)
        if rollback_device is None:
            return (4, None, "no-proof-and-no-rollback-odin")
        rc, android = rollback_boot_only_from_odin_device(
            odin=odin,
            boot_rollback_ap=boot_rollback_ap,
            stock_boot_fallback_ap=stock_boot_fallback_ap,
            odin_device=rollback_device,
            run_dir=run_dir,
            log_path=log_path,
            rollback_target=rollback_target,
            android_wait_sec=android_wait_sec,
            label=label,
        )
        if android:
            compare_retained_fingerprints(run_dir, log_path, pre_label, f"first_post_m29_{label}_rollback")
        return (rc or 7, android, "no-proof-original-download-never-disconnected")

    rollback_device = observe_self_download(run_dir, log_path, self_download_wait_sec, odin, label)
    if rollback_device is None:
        append_log(log_path, f"m29_{label}_result=no-self-download-manual-download-required")
        return (4, None, "manual-download-required")

    record_timeline_event(run_dir, "candidate_boot_ready")
    record_timeline_event(run_dir, f"{label}_candidate_boot_ready")
    append_log(log_path, f"m29_{label}_result=self-download")
    rc, android = rollback_boot_only_from_odin_device(
        odin=odin,
        boot_rollback_ap=boot_rollback_ap,
        stock_boot_fallback_ap=stock_boot_fallback_ap,
        odin_device=rollback_device,
        run_dir=run_dir,
        log_path=log_path,
        rollback_target=rollback_target,
        android_wait_sec=android_wait_sec,
        label=label,
    )
    if rc != 0 or android is None:
        return (rc or 6, android, "rollback-failed")
    compare_retained_fingerprints(run_dir, log_path, pre_label, f"first_post_m29_{label}_rollback")
    verify_partition_hash(log_path, android, "dtbo", EXPECTED_M25_PATCHED_DTBO_RAW_SHA256, f"post_{label}_patched")
    return (0, android, "self-download")


def apply_m25_high_speed_dtbo(
    *,
    odin: Path,
    dtbo_ap: Path,
    run_dir: Path,
    log_path: Path,
    serial: str,
    odin_wait_sec: int,
    android_wait_sec: int,
) -> tuple[int, str | None]:
    return m28.apply_m25_high_speed_dtbo(
        odin=odin,
        dtbo_ap=dtbo_ap,
        run_dir=run_dir,
        log_path=log_path,
        serial=serial,
        odin_wait_sec=odin_wait_sec,
        android_wait_sec=android_wait_sec,
    )


def rollback_from_download(
    *,
    odin: Path,
    boot_rollback_ap: Path,
    stock_boot_fallback_ap: Path,
    dtbo_rollback_ap: Path,
    run_dir: Path,
    log_path: Path,
    rollback_target: str,
    android_wait_sec: int,
    odin_wait_sec: int,
) -> int:
    record_timeline_event(run_dir, "live_session_start")
    devices = odin_devices(odin, log_path, "m29-boot-rollback")
    if len(devices) != 1:
        raise SystemExit(f"M29 rollback requires exactly one Odin device, got {devices}")
    rc, android = rollback_boot_only_from_odin_device(
        odin=odin,
        boot_rollback_ap=boot_rollback_ap,
        stock_boot_fallback_ap=stock_boot_fallback_ap,
        odin_device=devices[0],
        run_dir=run_dir,
        log_path=log_path,
        rollback_target=rollback_target,
        android_wait_sec=android_wait_sec,
        label="manual",
    )
    if rc != 0 or android is None:
        record_timeline_event(run_dir, "live_session_end")
        return rc or 6
    dtbo_rc = restore_stock_dtbo_if_needed(
        odin=odin,
        dtbo_rollback_ap=dtbo_rollback_ap,
        run_dir=run_dir,
        log_path=log_path,
        serial=android,
        odin_wait_sec=odin_wait_sec,
        android_wait_sec=android_wait_sec,
    )
    record_timeline_event(run_dir, "live_session_end")
    return dtbo_rc


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m29-manifest", type=Path, default=DEFAULT_M29_MANIFEST)
    parser.add_argument("--m25-dtbo-ap", type=Path, default=DEFAULT_M25_DTBO_AP)
    parser.add_argument("--m25-stock-dtbo-ap", type=Path, default=DEFAULT_M25_STOCK_DTBO_AP)
    parser.add_argument("--magisk-rollback-ap", type=Path, default=DEFAULT_MAGISK_ROLLBACK_AP)
    parser.add_argument("--stock-rollback-ap", type=Path, default=DEFAULT_STOCK_ROLLBACK_AP)
    parser.add_argument("--odin", type=Path, default=DEFAULT_ODIN)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--serial", help="ADB serial to pin before live flashing")
    parser.add_argument("--variant", action="append", choices=DEFAULT_M29_LABELS, help="Authorized M29 variant label to run")
    parser.add_argument("--self-download-wait-sec", type=int, default=45)
    parser.add_argument("--post-flash-disconnect-wait-sec", type=int, default=20)
    parser.add_argument("--odin-wait-sec", type=int, default=90)
    parser.add_argument("--android-wait-sec", type=int, default=300)
    parser.add_argument("--android-stability-samples", type=int, default=4)
    parser.add_argument("--android-stability-interval-sec", type=float, default=3.0)
    parser.add_argument("--rollback-target", choices=[ROLLBACK_MAGISK, ROLLBACK_STOCK], default=ROLLBACK_MAGISK)
    parser.add_argument("--offline-check", action="store_true")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--rollback-from-download", action="store_true")
    parser.add_argument("--restore-dtbo-from-android", action="store_true")
    parser.add_argument("--restore-dtbo-from-download", action="store_true")
    parser.add_argument("--ack")
    args = parser.parse_args(argv)

    modes = sum(
        1
        for enabled in (
            args.offline_check,
            args.live,
            args.rollback_from_download,
            args.restore_dtbo_from_android,
            args.restore_dtbo_from_download,
        )
        if enabled
    )
    if modes > 1:
        raise SystemExit("mode arguments are mutually exclusive")

    root = repo_root()
    run_dir = resolve_run_dir(root, args.run_dir)
    log_path = run_dir / "s22plus_m29_first_rollback_capture_live_gate.txt"
    append_log(log_path, f"=== {utc_now()} s22plus M29 first-rollback capture live gate ===")
    append_log(log_path, f"target={EXPECTED_TARGET}")

    odin = resolve(root, args.odin)
    m29_manifest = resolve(root, args.m29_manifest)
    m25_dtbo_ap = resolve(root, args.m25_dtbo_ap)
    m25_stock_dtbo_ap = resolve(root, args.m25_stock_dtbo_ap)
    magisk_rollback_ap = resolve(root, args.magisk_rollback_ap)
    stock_rollback_ap = resolve(root, args.stock_rollback_ap)
    boot_rollback_ap = magisk_rollback_ap if args.rollback_target == ROLLBACK_MAGISK else stock_rollback_ap
    candidates = selected_candidates(args.variant)

    if not odin.is_file():
        raise SystemExit(f"odin4 missing: {odin}")
    m28.verify_m28_artifacts(
        root=root,
        manifest=m29_manifest,
        candidates=candidates,
        m25_dtbo_ap=m25_dtbo_ap,
        m25_stock_dtbo_ap=m25_stock_dtbo_ap,
        magisk_rollback_ap=magisk_rollback_ap,
        stock_rollback_ap=stock_rollback_ap,
        log_path=log_path,
    )

    if args.offline_check:
        append_log(log_path, "offline_check=ok device_action=0 agents_exception_checked=0 android_checked=0")
        print(f"offline-check ok: M29 S24 capture gate artifacts verified; no device action; log={log_path}")
        return 0

    verify_agents_exception(root, log_path)

    if args.restore_dtbo_from_download:
        if args.ack != RESTORE_DTBO_ACK_TOKEN:
            raise SystemExit(f"--restore-dtbo-from-download requires --ack {RESTORE_DTBO_ACK_TOKEN}")
        record_timeline_event(run_dir, "live_session_start")
        devices = odin_devices(odin, log_path, "m29-stock-dtbo-rollback")
        if len(devices) != 1:
            raise SystemExit(f"stock DTBO rollback requires exactly one Odin device, got {devices}")
        record_timeline_event(run_dir, "dtbo_rollback_flash_start")
        rc = flash_ap(odin, m25_stock_dtbo_ap, devices[0], log_path, "stock_dtbo_rollback")
        record_timeline_event(run_dir, "dtbo_rollback_flash_done")
        if rc != 0:
            record_timeline_event(run_dir, "live_session_end")
            return rc or 5
        android = poll_android(log_path, args.android_wait_sec, expect_root=True, serial=args.serial)
        if android is None:
            record_timeline_event(run_dir, "live_session_end")
            return 6
        verify_partition_hash(log_path, android, "dtbo", EXPECTED_STOCK_DTBO_RAW_SHA256, "stock_dtbo_restore")
        record_timeline_event(run_dir, "dtbo_rollback_boot_ready")
        record_timeline_event(run_dir, "live_session_end")
        print(f"M29 stock DTBO restore-from-download completed rc=0; log={log_path}")
        return 0

    if args.rollback_from_download:
        if args.ack != ROLLBACK_ACK_TOKEN:
            raise SystemExit(f"--rollback-from-download requires --ack {ROLLBACK_ACK_TOKEN}")
        rc = rollback_from_download(
            odin=odin,
            boot_rollback_ap=boot_rollback_ap,
            stock_boot_fallback_ap=stock_rollback_ap,
            dtbo_rollback_ap=m25_stock_dtbo_ap,
            run_dir=run_dir,
            log_path=log_path,
            rollback_target=args.rollback_target,
            android_wait_sec=args.android_wait_sec,
            odin_wait_sec=args.odin_wait_sec,
        )
        print(f"M29 rollback-from-download completed rc={rc}; log={log_path}")
        return rc

    selected_serial = require_current_android(log_path, args.serial)
    verify_android_stability(
        log_path,
        selected_serial,
        args.android_stability_samples,
        args.android_stability_interval_sec,
    )
    verify_partition_hash(log_path, selected_serial, "boot", EXPECTED_BASE_BOOT_SHA256, "current")
    verify_partition_hash(log_path, selected_serial, "vendor_boot", EXPECTED_STOCK_VENDOR_BOOT_SHA256, "current")

    if args.restore_dtbo_from_android:
        if args.ack != RESTORE_DTBO_ACK_TOKEN:
            raise SystemExit(f"--restore-dtbo-from-android requires --ack {RESTORE_DTBO_ACK_TOKEN}")
        record_timeline_event(run_dir, "live_session_start")
        rc = restore_stock_dtbo_if_needed(
            odin=odin,
            dtbo_rollback_ap=m25_stock_dtbo_ap,
            run_dir=run_dir,
            log_path=log_path,
            serial=selected_serial,
            odin_wait_sec=args.odin_wait_sec,
            android_wait_sec=args.android_wait_sec,
        )
        record_timeline_event(run_dir, "live_session_end")
        print(f"M29 stock DTBO restore-from-android completed rc={rc}; log={log_path}")
        return rc

    verify_partition_hash(log_path, selected_serial, "dtbo", EXPECTED_STOCK_DTBO_RAW_SHA256, "current")
    host_snapshot(run_dir, log_path, "dryrun_current", odin)

    if not args.live:
        print(
            "dry-run ok: M29 S24 candidate, M25 DTBO cap, rollback APs, AGENTS exception, Android stability, "
            f"boot/vendor_boot/stock-DTBO hashes verified; log={log_path}"
        )
        return 0
    if args.ack != LIVE_ACK_TOKEN:
        raise SystemExit(f"--live requires --ack {LIVE_ACK_TOKEN}")

    record_timeline_event(run_dir, "live_session_start")
    rc, android = apply_m25_high_speed_dtbo(
        odin=odin,
        dtbo_ap=m25_dtbo_ap,
        run_dir=run_dir,
        log_path=log_path,
        serial=selected_serial,
        odin_wait_sec=args.odin_wait_sec,
        android_wait_sec=args.android_wait_sec,
    )
    if rc != 0 or android is None:
        record_timeline_event(run_dir, "live_session_end")
        print("M29 failed while applying DTBO high-speed cap; use DTBO restore helper if needed.", file=sys.stderr)
        return rc or 6

    last_android = android
    results: list[dict[str, str | int]] = []
    for candidate in candidates:
        boot_ap = resolve(root, candidate.ap_path)
        print(f"M29 {candidate.label} candidate flashing under patched DTBO.")
        rc, last_android, result = run_one_candidate(
            candidate=candidate,
            odin=odin,
            boot_ap=boot_ap,
            boot_rollback_ap=boot_rollback_ap,
            stock_boot_fallback_ap=stock_rollback_ap,
            run_dir=run_dir,
            log_path=log_path,
            serial=last_android,
            rollback_target=args.rollback_target,
            odin_wait_sec=args.odin_wait_sec,
            android_wait_sec=args.android_wait_sec,
            self_download_wait_sec=args.self_download_wait_sec,
            post_flash_disconnect_wait_sec=args.post_flash_disconnect_wait_sec,
        )
        results.append({"label": candidate.label, "rc": rc, "result": result})
        append_log(log_path, f"m29_{candidate.label}_final_rc={rc} result={result}")
        if rc != 0 or last_android is None:
            record_timeline_event(run_dir, "live_session_end")
            print(
                f"M29 {candidate.label} stopped with result={result} rc={rc}. "
                "If the device is not in Android, enter Download manually and run --rollback-from-download.",
                file=sys.stderr,
            )
            return rc or 4

    append_log(log_path, f"m29_batch_results={json.dumps(results, sort_keys=True)}")
    dtbo_rc = restore_stock_dtbo_if_needed(
        odin=odin,
        dtbo_rollback_ap=m25_stock_dtbo_ap,
        run_dir=run_dir,
        log_path=log_path,
        serial=last_android,
        odin_wait_sec=args.odin_wait_sec,
        android_wait_sec=args.android_wait_sec,
    )
    record_timeline_event(run_dir, "live_session_end")
    print(f"M29 live gate completed rc={dtbo_rc}; results={results}; log={log_path}")
    return dtbo_rc


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
