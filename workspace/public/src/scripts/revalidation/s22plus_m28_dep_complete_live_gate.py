#!/usr/bin/env python3
"""Guarded S22+ M28 dependency-complete download-beacon live gate.

Dry-run is the default.  Live mode is inert until a fresh SHA-pinned
AGENTS.md exception is promoted.

M28 rebuilds the M25 HS-only USB2 closure with modules.dep hard suppliers
restored, keeps the M25 DTBO high-speed cap, then requests Samsung Download
mode if a candidate reaches its checkpoint.  A candidate is counted only if
the original Odin endpoint disconnects after the candidate flash and a later
Odin endpoint appears without operator manual Download contamination.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
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
    sha256_file,
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
    EXPECTED_MEMBER_DTBO,
    EXPECTED_STOCK_DTBO_RAW_SHA256,
    EXPECTED_STOCK_VENDOR_BOOT_SHA256,
    read_partition_hash,
    record_timeline_event,
    restore_dtbo_from_android,
    verify_ap_member,
    verify_partition_hash,
)


LIVE_ACK_TOKEN = "S22PLUS-M28-DEP-COMPLETE-LIVE-GATE"
ROLLBACK_ACK_TOKEN = "S22PLUS-M28-DEP-COMPLETE-ROLLBACK-FROM-DOWNLOAD"
RESTORE_DTBO_ACK_TOKEN = "S22PLUS-M28-RESTORE-STOCK-DTBO"

EXPECTED_TARGET = "SM-S906N/g0q/S906NKSS7FYG8"
EXPECTED_M28_MARKER = "S22_NATIVE_INIT_M28_DEP_COMPLETE_DOWNLOAD"
EXPECTED_M28_SOURCE_SHA256 = "0c029dd3de42074c3c942efa23266fb383522750d1ffd9d826c67898db6bde6c"
EXPECTED_M28_MODULES_RAMDISK = "s22plus_m28_dep_complete.modules"
EXPECTED_M28_MANIFEST_SHA256 = "4986940e214dcb32916f5e06806f0cb2342479e82347abec0244edb2a09a250e"
EXPECTED_MODULES_DEP_SHA256 = "21eae389f1d8b0a9fc93cec0b12d36e736cfac656d91ae55055c793f2ed67b27"

DEFAULT_M28_ROOT = Path("workspace/private/outputs/s22plus_native_init/m28_dep_complete_download_v0_1")
DEFAULT_M28_MANIFEST = DEFAULT_M28_ROOT / "manifest.json"
DEFAULT_M25_DTBO_AP = Path("workspace/private/outputs/s22plus_native_init/m25_hs_only_usb2_acm_v0_1/dtbo_candidate_odin4/AP.tar.md5")
DEFAULT_M25_STOCK_DTBO_AP = Path("workspace/private/outputs/s22plus_native_init/m25_hs_only_usb2_acm_v0_1/dtbo_stock_rollback_odin4/AP.tar.md5")


@dataclass(frozen=True)
class M28Candidate:
    label: str
    module_count: int
    modules_sha256: str
    ap_sha256: str
    boot_sha256: str
    init_sha256: str
    reincluded_hard_suppliers: tuple[str, ...]

    @property
    def ap_path(self) -> Path:
        return DEFAULT_M28_ROOT / self.label / "odin4" / "AP.tar.md5"

    @property
    def manifest_path(self) -> Path:
        return DEFAULT_M28_ROOT / self.label / "manifest.json"


EXPECTED_M28_BATCH: tuple[M28Candidate, ...] = (
    M28Candidate(
        label="S24",
        module_count=26,
        modules_sha256="8c605e2c69aad74f80191bdbc1843b002539d22d49bcffa86bb85bbcb343e5e4",
        ap_sha256="c684f6a21bcc9aa50b066b447f4356958fe6d7bfed93edf0ac1b7dcaae8ce75f",
        boot_sha256="a1459931001bfd6e17593dd329fc682f00ab61f4841b6543791f5349dd012cd0",
        init_sha256="5c04a2023b2b56ef98746da6f7168121b62d7859cee81c756b80d1a382c1964e",
        reincluded_hard_suppliers=("sec_debug.ko", "minidump.ko"),
    ),
    M28Candidate(
        label="F43",
        module_count=43,
        modules_sha256="430050d648d85dd6c3fea459a6cd627a58fd234afe1b485820ccc1f2eb65f87b",
        ap_sha256="003ea5760d9e33402750afd7a52b6b95727e4b4cff3f4d3cf66c559eabbb38d1",
        boot_sha256="6453b8f2dd685757148056ba8767c2820b0547123f4e5e5e423c4adb0c70496c",
        init_sha256="68de58cd3f05fd77af00984027948ad5ab953ae128dc4133d336e0a521cd588f",
        reincluded_hard_suppliers=("sec_debug.ko", "minidump.ko", "abc.ko"),
    ),
)

EXPECTED_M28_BY_LABEL = {candidate.label: candidate for candidate in EXPECTED_M28_BATCH}
DEFAULT_BATCH_LABELS = tuple(candidate.label for candidate in EXPECTED_M28_BATCH)


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def resolve_run_dir(root: Path, requested: Path | None) -> Path:
    if requested is not None:
        run_dir = resolve(root, requested)
        run_dir.mkdir(parents=True, exist_ok=False)
        return run_dir
    base = resolve(root, DEFAULT_RUN_ROOT / f"s22plus_m28_dep_complete_live_gate_{utc_stamp()}")
    for suffix in range(100):
        run_dir = base if suffix == 0 else Path(f"{base}_{suffix:02d}")
        try:
            run_dir.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            continue
        return run_dir
    raise SystemExit(f"could not allocate unique run directory under {base.parent}")


def selected_candidates(labels: list[str] | None) -> list[M28Candidate]:
    if not labels:
        labels = list(DEFAULT_BATCH_LABELS)
    seen: set[str] = set()
    result: list[M28Candidate] = []
    for label in labels:
        normalized = label.upper()
        if normalized in seen:
            raise SystemExit(f"duplicate M28 candidate label: {label}")
        seen.add(normalized)
        candidate = EXPECTED_M28_BY_LABEL.get(normalized)
        if candidate is None:
            raise SystemExit(
                f"M28 candidate {label!r} is not authorized by this first-live batch; "
                f"allowed={','.join(DEFAULT_BATCH_LABELS)}"
            )
        result.append(candidate)
    expected_order_prefix = list(DEFAULT_BATCH_LABELS[: len(result)])
    if [candidate.label for candidate in result] != expected_order_prefix:
        raise SystemExit(
            "M28 live selection must be the ordered sequence S24 or S24,F43; "
            f"got={[candidate.label for candidate in result]}"
        )
    return result


def policy_required_markers() -> list[str]:
    markers = [
        "S22+ M28 dependency-complete native-init boot+DTBO batch",
        "workspace/public/src/scripts/revalidation/s22plus_m28_dep_complete_live_gate.py",
        LIVE_ACK_TOKEN,
        ROLLBACK_ACK_TOKEN,
        RESTORE_DTBO_ACK_TOKEN,
        EXPECTED_TARGET,
        EXPECTED_M28_MARKER,
        EXPECTED_M28_SOURCE_SHA256,
        EXPECTED_M28_MODULES_RAMDISK,
        EXPECTED_MODULES_DEP_SHA256,
        EXPECTED_M25_DTBO_AP_SHA256,
        EXPECTED_M25_PATCHED_DTBO_RAW_SHA256,
        EXPECTED_M25_STOCK_DTBO_ROLLBACK_AP_SHA256,
        EXPECTED_BASE_BOOT_SHA256,
        EXPECTED_STOCK_DTBO_RAW_SHA256,
        EXPECTED_STOCK_VENDOR_BOOT_SHA256,
        EXPECTED_MAGISK_AP_SHA256,
        EXPECTED_STOCK_BOOT_AP_SHA256,
        "M28 dependency-complete live batch is limited to S24/F43",
        "S24 first",
        "do not run F43 if S24 fails",
        "stop on first no-hit",
        "DTBO high-speed cap",
        "stock DTBO rollback",
        "Magisk boot rollback",
        "manual download-mode rollback",
        "wait for the original Odin endpoint to disconnect",
        "later Odin endpoint as the candidate self-download proof",
        "boot.img.lz4",
        "dtbo.img.lz4",
        "no ACM",
        "no configfs",
        "no module binary injection",
        "no EUD sysfs write",
        "manual Download contamination",
    ]
    for candidate in EXPECTED_M28_BATCH:
        markers.extend(
            [
                candidate.label,
                str(candidate.module_count),
                candidate.modules_sha256,
                candidate.ap_sha256,
                candidate.boot_sha256,
                candidate.init_sha256,
            ]
        )
        markers.extend(candidate.reincluded_hard_suppliers)
    return markers


def missing_policy_markers(text: str) -> list[str]:
    normalized = " ".join(text.split())
    return [marker for marker in policy_required_markers() if marker not in normalized]


def verify_agents_exception(root: Path, log_path: Path) -> None:
    agents = (root / "AGENTS.md").read_text(encoding="utf-8")
    missing = missing_policy_markers(agents)
    append_log(log_path, f"agents_exception_missing={missing}")
    if missing:
        raise SystemExit(f"AGENTS.md missing M28 dependency-complete live authorization markers: {missing}")


def verify_m28_top_manifest(path: Path, log_path: Path) -> None:
    if not path.is_file():
        raise SystemExit(f"M28 matrix manifest missing: {path}")
    manifest_sha = sha256_file(path)
    append_log(log_path, f"m28_manifest_sha256={manifest_sha}")
    if manifest_sha != EXPECTED_M28_MANIFEST_SHA256:
        raise SystemExit(f"M28 matrix manifest SHA mismatch: {manifest_sha}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("target") != EXPECTED_TARGET:
        raise SystemExit(f"M28 target mismatch: {data.get('target')!r}")
    safety = data.get("safety", {})
    if safety.get("host_only_build") is not True or safety.get("live_flash_authorized") is not False:
        raise SystemExit(f"M28 manifest must be host-only/live-false, got {safety!r}")
    if safety.get("requires_fresh_sha_pinned_agents_exception_before_any_live_flash") is not True:
        raise SystemExit("M28 manifest must require a fresh SHA-pinned AGENTS exception")

    vendor = data.get("vendor", {})
    if vendor.get("metadata_hashes", {}).get("modules.dep") != EXPECTED_MODULES_DEP_SHA256:
        raise SystemExit(f"M28 modules.dep SHA mismatch: {vendor.get('metadata_hashes', {}).get('modules.dep')!r}")
    policy = data.get("policy", {})
    if policy.get("reincluded_hard_suppliers") != ["sec_debug.ko", "minidump.ko", "abc.ko"]:
        raise SystemExit(f"M28 reincluded supplier policy mismatch: {policy.get('reincluded_hard_suppliers')!r}")
    for forbidden in ("phy-msm-ssusb-qmp.ko", "eud.ko", "ucsi_glink.ko", "qcom_wdt_core.ko", "gh_virt_wdt.ko"):
        if forbidden not in policy.get("excluded_modules", []) and forbidden not in policy.get("watchdog_excluded", []):
            raise SystemExit(f"M28 policy excluded modules missing {forbidden}")
    m25_context = data.get("m25_context", {})
    dtbo = m25_context.get("dtbo", {})
    expected_dtbo = {
        "candidate_ap_tar_md5_sha256": EXPECTED_M25_DTBO_AP_SHA256,
        "patched_dtbo_raw_sha256": EXPECTED_M25_PATCHED_DTBO_RAW_SHA256,
        "stock_dtbo_raw_sha256": EXPECTED_STOCK_DTBO_RAW_SHA256,
        "stock_dtbo_rollback_ap_tar_md5_sha256": EXPECTED_M25_STOCK_DTBO_ROLLBACK_AP_SHA256,
    }
    for key, expected in expected_dtbo.items():
        if dtbo.get(key) != expected:
            raise SystemExit(f"M28 DTBO context {key} mismatch: {dtbo.get(key)!r} != {expected!r}")

    variants = {entry.get("label"): entry for entry in data.get("variants", [])}
    for candidate in EXPECTED_M28_BATCH:
        entry = variants.get(candidate.label)
        if not entry:
            raise SystemExit(f"M28 manifest missing authorized variant {candidate.label}")
        expected = {
            "module_count": candidate.module_count,
            "modules_sha256": candidate.modules_sha256,
            "ap_tar_md5_sha256": candidate.ap_sha256,
            "boot_img_sha256": candidate.boot_sha256,
            "init_sha256": candidate.init_sha256,
            "tar_members": [EXPECTED_MEMBER],
            "reincluded_hard_suppliers": list(candidate.reincluded_hard_suppliers),
        }
        for key, value in expected.items():
            if entry.get(key) != value:
                raise SystemExit(f"M28 manifest {candidate.label} {key} mismatch: {entry.get(key)!r} != {value!r}")


def verify_m28_variant_manifest(root: Path, candidate: M28Candidate, log_path: Path) -> None:
    path = resolve(root, candidate.manifest_path)
    if not path.is_file():
        raise SystemExit(f"M28 {candidate.label} manifest missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    hashes = data.get("hashes", {})
    safety = data.get("safety", {})
    closure = data.get("closure", {})
    ramdisk = data.get("ramdisk", {})
    append_log(log_path, f"m28_{candidate.label}_manifest_hashes={json.dumps(hashes, sort_keys=True)}")
    if data.get("target") != EXPECTED_TARGET:
        raise SystemExit(f"M28 {candidate.label} target mismatch")
    expected_hashes = {
        "ap_tar_md5": candidate.ap_sha256,
        "boot_img": candidate.boot_sha256,
        "base_boot": EXPECTED_BASE_BOOT_SHA256,
        "kernel": "bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff",
        "m28_init": candidate.init_sha256,
        "m28_dep_complete_modules": candidate.modules_sha256,
        "source": EXPECTED_M28_SOURCE_SHA256,
        "nochange_repack_boot": EXPECTED_BASE_BOOT_SHA256,
    }
    for key, expected in expected_hashes.items():
        if hashes.get(key) != expected:
            raise SystemExit(f"M28 {candidate.label} hash {key} mismatch: {hashes.get(key)!r} != {expected!r}")
    expected_safety = {
        "boot_only": True,
        "host_only_build": True,
        "live_flash_authorized": False,
        "dtbo_high_speed_cap_required": True,
        "module_binary_injection": False,
        "configfs_runtime_gadget": False,
        "acm": False,
        "reboot_request": "download",
    }
    for key, expected in expected_safety.items():
        if safety.get(key) != expected:
            raise SystemExit(f"M28 {candidate.label} safety {key} mismatch: {safety.get(key)!r} != {expected!r}")
    if data.get("variant") != candidate.label:
        raise SystemExit(f"M28 {candidate.label} variant metadata mismatch: {data.get('variant')!r}")
    if closure.get("module_count") != candidate.module_count:
        raise SystemExit(f"M28 {candidate.label} closure module count mismatch: {closure.get('module_count')!r}")
    if closure.get("module_sha256") != candidate.modules_sha256:
        raise SystemExit(f"M28 {candidate.label} closure module SHA mismatch: {closure.get('module_sha256')!r}")
    if closure.get("reincluded_hard_suppliers") != list(candidate.reincluded_hard_suppliers):
        raise SystemExit(f"M28 {candidate.label} reincluded suppliers mismatch: {closure.get('reincluded_hard_suppliers')!r}")
    if set(closure.get("modules", [])) & {"qcom_wdt_core.ko", "gh_virt_wdt.ko", "phy-msm-ssusb-qmp.ko", "eud.ko", "ucsi_glink.ko"}:
        raise SystemExit(f"M28 {candidate.label} closure contains excluded module")
    if ramdisk.get("replaced_entry") != "init":
        raise SystemExit(f"M28 {candidate.label} did not replace /init")
    if ramdisk.get("added_subset_entry") != EXPECTED_M28_MODULES_RAMDISK:
        raise SystemExit(f"M28 {candidate.label} ramdisk module-list entry mismatch")
    if ramdisk.get("module_files_injected_into_boot_ramdisk") != 0:
        raise SystemExit(f"M28 {candidate.label} must not inject module binaries")


def verify_m28_artifacts(
    *,
    root: Path,
    manifest: Path,
    candidates: list[M28Candidate],
    m25_dtbo_ap: Path,
    m25_stock_dtbo_ap: Path,
    magisk_rollback_ap: Path,
    stock_rollback_ap: Path,
    log_path: Path,
) -> None:
    verify_m28_top_manifest(manifest, log_path)
    for candidate in candidates:
        verify_ap(resolve(root, candidate.ap_path), candidate.ap_sha256, f"m28_{candidate.label}_boot_candidate", log_path)
        verify_m28_variant_manifest(root, candidate, log_path)
    verify_ap_member(m25_dtbo_ap, EXPECTED_M25_DTBO_AP_SHA256, EXPECTED_MEMBER_DTBO, "m25_dtbo_candidate", log_path)
    verify_ap_member(m25_stock_dtbo_ap, EXPECTED_M25_STOCK_DTBO_ROLLBACK_AP_SHA256, EXPECTED_MEMBER_DTBO, "m25_stock_dtbo_rollback", log_path)
    verify_ap(magisk_rollback_ap, EXPECTED_MAGISK_AP_SHA256, "magisk_boot_rollback", log_path)
    verify_ap(stock_rollback_ap, EXPECTED_STOCK_BOOT_AP_SHA256, "stock_boot_fallback", log_path)


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
        snap_label = f"m28_{label}_self_download_{iteration:03d}"
        host_snapshot(run_dir, log_path, snap_label, odin)
        devices = odin_devices(odin, log_path, f"{snap_label}-odin")
        if len(devices) == 1:
            append_log(log_path, f"m28_{label}_self_download_seen=1 device={devices[0]}")
            return devices[0]
        if len(devices) > 1:
            raise SystemExit(f"refusing ambiguous Odin devices during M28 {label} observation: {devices}")
        rows = adb_rows(log_path, f"{snap_label}-adb")
        usable = [row for row in rows if row[1] == "device"]
        if usable:
            append_log(log_path, f"m28_{label}_unexpected_adb_rows={usable}")
        time.sleep(1.0)
    append_log(log_path, f"m28_{label}_self_download_seen=0")
    return None


def capture_post_boot_m28_surfaces(run_dir: Path, log_path: Path, serial: str, label: str) -> None:
    marker_found = collect_android_pstore(run_dir, log_path, f"post_m28_{label}_rollback", serial, marker=EXPECTED_M28_MARKER)
    append_log(log_path, f"m28_{label}_capture_marker_found={int(marker_found)}")


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
        append_log(log_path, f"m28_{label}_magisk_rollback_failed_attempting_stock_fallback=1")
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
        append_log(log_path, f"m28_{label}_boot_restore_hash_check=skipped rollback_target=stock")
    record_timeline_event(run_dir, "rollback_boot_ready")
    record_timeline_event(run_dir, f"{label}_rollback_boot_ready")
    capture_post_boot_m28_surfaces(run_dir, log_path, android, label)
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
    current = read_partition_hash(log_path, serial, "dtbo", "pre_m28_dtbo_apply")
    if current == EXPECTED_M25_PATCHED_DTBO_RAW_SHA256:
        append_log(log_path, "m28_dtbo_apply_already_patched=1")
        return (0, serial)
    if current != EXPECTED_STOCK_DTBO_RAW_SHA256:
        raise SystemExit(f"refusing M28 DTBO cap apply from unexpected DTBO hash {current}")
    reboot_android_to_download(serial, log_path, "m28_dtbo_candidate")
    dtbo_odin_device = wait_for_odin(odin, log_path, "m28-dtbo-candidate-wait", odin_wait_sec)
    if dtbo_odin_device is None:
        return (2, None)
    record_timeline_event(run_dir, "dtbo_candidate_flash_start")
    rc = flash_ap(odin, dtbo_ap, dtbo_odin_device, log_path, "m28_dtbo_candidate")
    record_timeline_event(run_dir, "dtbo_candidate_flash_done")
    if rc != 0:
        return (rc or 3, None)
    android = poll_android(log_path, android_wait_sec, expect_root=True, serial=serial)
    if android is None:
        return (6, None)
    verify_partition_hash(log_path, android, "dtbo", EXPECTED_M25_PATCHED_DTBO_RAW_SHA256, "m28_dtbo_patched")
    record_timeline_event(run_dir, "dtbo_candidate_boot_ready")
    return (0, android)


def run_one_candidate(
    *,
    candidate: M28Candidate,
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
    reboot_android_to_download(serial, log_path, f"m28_{label}_boot_candidate")
    odin_device = wait_for_odin(odin, log_path, f"m28-{label}-boot-candidate-wait", odin_wait_sec)
    if odin_device is None:
        return (2, None, "no-download-before-candidate")

    record_timeline_event(run_dir, f"{label}_candidate_flash_start")
    record_timeline_event(run_dir, "candidate_flash_start")
    candidate_rc = flash_ap(odin, boot_ap, odin_device, log_path, f"m28_{label}_boot_candidate")
    record_timeline_event(run_dir, "candidate_flash_done")
    record_timeline_event(run_dir, f"{label}_candidate_flash_done")
    if candidate_rc != 0:
        return (candidate_rc or 3, None, "candidate-flash-failed")

    left_download = wait_for_odin_absent(odin, log_path, f"m28-{label}-post-candidate-disconnect", post_flash_disconnect_wait_sec)
    if not left_download:
        append_log(log_path, f"m28_{label}_result=no-proof-original-download-never-disconnected")
        rollback_device = wait_for_odin(odin, log_path, f"m28-{label}-rollback-still-download-wait", 5)
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
        return (rc or 7, android, "no-proof-original-download-never-disconnected")

    rollback_device = observe_self_download(run_dir, log_path, self_download_wait_sec, odin, label)
    if rollback_device is None:
        append_log(log_path, f"m28_{label}_result=no-self-download-manual-download-required")
        return (4, None, "manual-download-required")

    record_timeline_event(run_dir, "candidate_boot_ready")
    record_timeline_event(run_dir, f"{label}_candidate_boot_ready")
    append_log(log_path, f"m28_{label}_result=self-download")
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
    verify_partition_hash(log_path, android, "dtbo", EXPECTED_M25_PATCHED_DTBO_RAW_SHA256, f"post_{label}_patched")
    return (0, android, "self-download")


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
    devices = odin_devices(odin, log_path, "m28-boot-rollback")
    if len(devices) != 1:
        raise SystemExit(f"M28 rollback requires exactly one Odin device, got {devices}")
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
    parser.add_argument("--m28-manifest", type=Path, default=DEFAULT_M28_MANIFEST)
    parser.add_argument("--m25-dtbo-ap", type=Path, default=DEFAULT_M25_DTBO_AP)
    parser.add_argument("--m25-stock-dtbo-ap", type=Path, default=DEFAULT_M25_STOCK_DTBO_AP)
    parser.add_argument("--magisk-rollback-ap", type=Path, default=DEFAULT_MAGISK_ROLLBACK_AP)
    parser.add_argument("--stock-rollback-ap", type=Path, default=DEFAULT_STOCK_ROLLBACK_AP)
    parser.add_argument("--odin", type=Path, default=DEFAULT_ODIN)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--serial", help="ADB serial to pin before live flashing")
    parser.add_argument("--variant", action="append", choices=DEFAULT_BATCH_LABELS, help="Authorized M28 variant label to run; repeatable")
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
    log_path = run_dir / "s22plus_m28_dep_complete_live_gate.txt"
    append_log(log_path, f"=== {utc_now()} s22plus M28 dependency-complete live gate ===")
    append_log(log_path, f"target={EXPECTED_TARGET}")

    odin = resolve(root, args.odin)
    m28_manifest = resolve(root, args.m28_manifest)
    m25_dtbo_ap = resolve(root, args.m25_dtbo_ap)
    m25_stock_dtbo_ap = resolve(root, args.m25_stock_dtbo_ap)
    magisk_rollback_ap = resolve(root, args.magisk_rollback_ap)
    stock_rollback_ap = resolve(root, args.stock_rollback_ap)
    boot_rollback_ap = magisk_rollback_ap if args.rollback_target == ROLLBACK_MAGISK else stock_rollback_ap
    candidates = selected_candidates(args.variant)

    if not odin.is_file():
        raise SystemExit(f"odin4 missing: {odin}")
    verify_m28_artifacts(
        root=root,
        manifest=m28_manifest,
        candidates=candidates,
        m25_dtbo_ap=m25_dtbo_ap,
        m25_stock_dtbo_ap=m25_stock_dtbo_ap,
        magisk_rollback_ap=magisk_rollback_ap,
        stock_rollback_ap=stock_rollback_ap,
        log_path=log_path,
    )

    if args.offline_check:
        append_log(log_path, "offline_check=ok device_action=0 agents_exception_checked=0 android_checked=0")
        print(f"offline-check ok: M28 candidates {[c.label for c in candidates]} and rollback APs verified; no device action; log={log_path}")
        return 0

    verify_agents_exception(root, log_path)

    if args.restore_dtbo_from_download:
        if args.ack != RESTORE_DTBO_ACK_TOKEN:
            raise SystemExit(f"--restore-dtbo-from-download requires --ack {RESTORE_DTBO_ACK_TOKEN}")
        record_timeline_event(run_dir, "live_session_start")
        devices = odin_devices(odin, log_path, "m28-stock-dtbo-rollback")
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
        print(f"M28 stock DTBO restore-from-download completed rc=0; log={log_path}")
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
        print(f"M28 rollback-from-download completed rc={rc}; log={log_path}")
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
        print(f"M28 stock DTBO restore-from-android completed rc={rc}; log={log_path}")
        return rc

    verify_partition_hash(log_path, selected_serial, "dtbo", EXPECTED_STOCK_DTBO_RAW_SHA256, "current")
    host_snapshot(run_dir, log_path, "dryrun_current", odin)

    if not args.live:
        print(
            "dry-run ok: M28 candidates, M25 DTBO cap, rollback APs, AGENTS exception, Android stability, "
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
        print("M28 failed while applying DTBO high-speed cap; use DTBO restore helper if needed.", file=sys.stderr)
        return rc or 6

    last_android = android
    results: list[dict[str, str | int]] = []
    for candidate in candidates:
        boot_ap = resolve(root, candidate.ap_path)
        print(f"M28 {candidate.label} candidate flashing under patched DTBO.")
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
        append_log(log_path, f"m28_{candidate.label}_final_rc={rc} result={result}")
        if rc != 0 or last_android is None:
            record_timeline_event(run_dir, "live_session_end")
            print(
                f"M28 {candidate.label} stopped with result={result} rc={rc}. "
                "If the device is not in Android, enter Download manually and run --rollback-from-download.",
                file=sys.stderr,
            )
            return rc or 4

    append_log(log_path, f"m28_batch_results={json.dumps(results, sort_keys=True)}")
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
    print(f"M28 live gate completed rc={dtbo_rc}; results={results}; log={log_path}")
    return dtbo_rc


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
