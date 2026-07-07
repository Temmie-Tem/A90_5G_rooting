#!/usr/bin/env python3
"""Guarded S22+ ramoops-DTBO + M18 capture live gate.

Default dry-run and all device modes require a future SHA-pinned AGENTS.md
exception. --offline-check verifies only the host-built DTBO/M18 packages and
rollback APs without touching a connected device.

Intended live flow, once separately authorized:
1. flash the patched DTBO that enables the ramoops overlay;
2. require Android/root to return on the patched DTBO;
3. flash the M18 native-init boot candidate;
4. observe for ACM/ADB/Odin/manual-download evidence;
5. roll boot back to Magisk, collect pstore, then restore stock DTBO.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

from s22plus_m3_observable_live_gate import (
    DEFAULT_MAGISK_ROLLBACK_AP,
    DEFAULT_ODIN,
    DEFAULT_RUN_ROOT,
    DEFAULT_STOCK_ROLLBACK_AP,
    EXPECTED_BUILD,
    EXPECTED_DEVICE,
    EXPECTED_MAGISK_AP_SHA256,
    EXPECTED_MODEL,
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
    run,
    sha256_file,
    tar_members,
    utc_now,
    wait_for_odin,
)
from s22plus_m5_usb_acm_live_gate import acm_devices, read_acm_banner, verify_android_stability


LIVE_ACK_TOKEN = "S22PLUS-RAMOOPS-DTBO-M18-CAPTURE-LIVE-GATE"
ROLLBACK_BOOT_ACK_TOKEN = "S22PLUS-RAMOOPS-M18-ROLLBACK-BOOT-FROM-DOWNLOAD"
RESTORE_DTBO_ACK_TOKEN = "S22PLUS-RAMOOPS-RESTORE-STOCK-DTBO"

EXPECTED_TARGET = "SM-S906N/g0q/S906NKSS7FYG8"
EXPECTED_BOOT_MEMBER = "boot.img.lz4"
EXPECTED_DTBO_MEMBER = "dtbo.img.lz4"

EXPECTED_DTBO_CANDIDATE_AP_SHA256 = "4f82663a7c2175a41760ec099c0f662dd04b8932a5ae82ba46b3ecb401a14a00"
EXPECTED_DTBO_ROLLBACK_AP_SHA256 = "6f397421bee84f4ea0c80a8519be0f6f6af84119794970e8a1faaa05f261caaa"
EXPECTED_PATCHED_DTBO_RAW_SHA256 = "1c90b54577cbb42e029818a0c4248e85ec3a0e40903b0887648d6556355c85ab"
EXPECTED_STOCK_DTBO_RAW_SHA256 = "97a4864fee4e61892d733962d1ec76f8d14b52bc19e6f47440bc27d9dfc4bd0c"
EXPECTED_DTBO_PATCH_COUNT = 2
EXPECTED_DTBO_CHANGED_BYTES = 16

EXPECTED_M18_AP_SHA256 = "9382f91bf2cd3235410368ca08208b9343d8584da48c29b25c46a931b1f42805"
EXPECTED_M18_BOOT_SHA256 = "a99a09fa062d1aaa848a41037c649a43abc983f177714dfc24c39d0df4d84083"
EXPECTED_M18_BASE_BOOT_SHA256 = "2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e"
EXPECTED_M18_INIT_SHA256 = "e73f39f7cc6f3a70e62ab2837b9e2d23422e2b6a5747e94f77bafcf0443baa40"
EXPECTED_M18_MODULE_LIST_SHA256 = "153921f2cd886e31a5989ba589f6e5058fda4cc8eb6eb196e843293f8fae8e78"
EXPECTED_M18_SOURCE_SHA256 = "29e0a4a9771aacbef24106f3b838d0731cbe294ae0cf064bf14e4256face7dfd"
EXPECTED_M18_MARKER = "S22_NATIVE_INIT_USB_ACM_M18_FULL"
EXPECTED_M18_USB_VENDOR = "04e8"
EXPECTED_M18_USB_PRODUCT = "685d"
EXPECTED_M18_USB_SERIAL = "S22M18FULL0001"
EXPECTED_M18_MODULE_COUNT = 141

DEFAULT_DTBO_CANDIDATE_AP = Path("workspace/private/outputs/s22plus_ramoops_dtbo_enable_v0_1/candidate_odin4/AP.tar.md5")
DEFAULT_DTBO_ROLLBACK_AP = Path("workspace/private/outputs/s22plus_ramoops_dtbo_enable_v0_1/stock_rollback_odin4/AP.tar.md5")
DEFAULT_DTBO_MANIFEST = Path("workspace/private/outputs/s22plus_ramoops_dtbo_enable_v0_1/manifest.json")
DEFAULT_M18_AP = Path("workspace/private/outputs/s22plus_native_init/inplace_m18_full_firststage_usb_v0_1/odin4/AP.tar.md5")
DEFAULT_M18_MANIFEST = Path("workspace/private/outputs/s22plus_native_init/inplace_m18_full_firststage_usb_v0_1/manifest.json")


def resolve_run_dir(root: Path, requested: Path | None) -> Path:
    if requested is not None:
        run_dir = resolve(root, requested)
        run_dir.mkdir(parents=True, exist_ok=False)
        return run_dir
    stamp = utc_now().replace("-", "").replace(":", "").replace("Z", "Z")
    base = resolve(root, DEFAULT_RUN_ROOT / f"s22plus_ramoops_dtbo_m18_capture_{stamp}")
    for suffix in range(100):
        run_dir = base if suffix == 0 else Path(f"{base}_{suffix:02d}")
        try:
            run_dir.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            continue
        return run_dir
    raise SystemExit(f"could not allocate unique run directory under {base.parent}")


def verify_ap_member(path: Path, expected_sha: str, expected_member: str, label: str, log_path: Path) -> None:
    if not path.is_file():
        raise SystemExit(f"{label} AP missing: {path}")
    actual_sha = sha256_file(path)
    members = tar_members(path)
    append_log(log_path, f"{label}_sha256={actual_sha}")
    append_log(log_path, f"{label}_members={members}")
    if actual_sha != expected_sha:
        raise SystemExit(f"{label} AP SHA mismatch: {actual_sha}")
    if members != [expected_member]:
        raise SystemExit(f"{label} AP must contain exactly {expected_member!r}, got {members!r}")


def verify_dtbo_manifest(path: Path, log_path: Path) -> None:
    if not path.is_file():
        raise SystemExit(f"DTBO manifest missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    hashes = data.get("hashes", {})
    safety = data.get("safety", {})
    evidence = data.get("evidence", {})
    append_log(log_path, f"dtbo_manifest_path={path}")
    append_log(log_path, f"dtbo_manifest_hashes={json.dumps(hashes, sort_keys=True)}")
    append_log(log_path, f"dtbo_manifest_safety={json.dumps(safety, sort_keys=True)}")

    required_hashes = {
        "candidate_ap_tar_md5": EXPECTED_DTBO_CANDIDATE_AP_SHA256,
        "rollback_ap_tar_md5": EXPECTED_DTBO_ROLLBACK_AP_SHA256,
        "patched_dtbo_raw": EXPECTED_PATCHED_DTBO_RAW_SHA256,
        "stock_dtbo_raw": EXPECTED_STOCK_DTBO_RAW_SHA256,
    }
    for key, expected in required_hashes.items():
        if hashes.get(key) != expected:
            raise SystemExit(f"DTBO manifest hash {key} mismatch: {hashes.get(key)!r} != {expected!r}")

    required_safety: dict[str, Any] = {
        "host_only": True,
        "touches_connected_device": False,
        "live_flash_authorized": False,
        "partition_scope_if_later_authorized": "dtbo only",
        "requires_new_sha_pinned_dtbo_exception_before_flash": True,
        "current_agents_boot_only_rule_does_not_authorize_this_live_flash": True,
        "forbidden_partitions_touched": False,
        "rollback_ap_built": True,
        "stock_dtbo_avb_descriptor_matches": True,
        "patched_dtbo_avb_descriptor_matches": False,
        "patched_dtbo_requires_disabled_vbmeta_or_resigning_before_live": True,
    }
    for key, expected in required_safety.items():
        if safety.get(key) != expected:
            raise SystemExit(f"DTBO manifest safety {key} mismatch: {safety.get(key)!r} != {expected!r}")

    patches = evidence.get("applied_patches")
    if not isinstance(patches, list) or len(patches) != EXPECTED_DTBO_PATCH_COUNT:
        raise SystemExit(f"DTBO applied patch count mismatch: {patches!r}")
    if evidence.get("changed_byte_count") != EXPECTED_DTBO_CHANGED_BYTES:
        raise SystemExit(f"DTBO changed-byte count mismatch: {evidence.get('changed_byte_count')!r}")
    candidate_members = evidence.get("candidate_tar_members")
    rollback_members = evidence.get("rollback_tar_members")
    if candidate_members != [EXPECTED_DTBO_MEMBER] or rollback_members != [EXPECTED_DTBO_MEMBER]:
        raise SystemExit(f"DTBO tar members mismatch: candidate={candidate_members!r} rollback={rollback_members!r}")

    avb = evidence.get("dtbo_avb_hash_descriptor", {})
    if avb.get("stock_matches_descriptor") is not True or avb.get("patched_matches_descriptor") is not False:
        raise SystemExit(f"DTBO AVB descriptor expectation mismatch: {avb!r}")


def verify_m18_manifest(path: Path, log_path: Path) -> None:
    if not path.is_file():
        raise SystemExit(f"M18 manifest missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    hashes = data.get("hashes", {})
    safety = data.get("safety", {})
    ramdisk = data.get("ramdisk", {})
    m18_init = data.get("m18_full_init", {})
    vendor = data.get("vendor_ramdisk", {}).get("m18_full_firststage_usb", {})
    tar_members_seen = data.get("tar_members")
    append_log(log_path, f"m18_manifest_path={path}")
    append_log(log_path, f"m18_manifest_hashes={json.dumps(hashes, sort_keys=True)}")
    append_log(log_path, f"m18_manifest_safety={json.dumps(safety, sort_keys=True)}")

    required_hashes = {
        "ap_tar_md5": EXPECTED_M18_AP_SHA256,
        "boot_img": EXPECTED_M18_BOOT_SHA256,
        "base_boot": EXPECTED_M18_BASE_BOOT_SHA256,
        "m18_full_init": EXPECTED_M18_INIT_SHA256,
        "m18_full_firststage_usb": EXPECTED_M18_MODULE_LIST_SHA256,
        "source": EXPECTED_M18_SOURCE_SHA256,
    }
    for key, expected in required_hashes.items():
        if hashes.get(key) != expected:
            raise SystemExit(f"M18 manifest hash {key} mismatch: {hashes.get(key)!r} != {expected!r}")
    if tar_members_seen != [EXPECTED_BOOT_MEMBER]:
        raise SystemExit(f"M18 manifest tar members mismatch: {tar_members_seen!r}")

    required_safety: dict[str, Any] = {
        "boot_only": True,
        "host_only_build": True,
        "live_flash_authorized": False,
        "requires_new_sha_pinned_agents_exception_before_flash": True,
        "base_is_known_booting_magisk_boot": True,
        "construction": "magiskboot unpack/repack; replace ramdisk /init only",
        "runtime": "freestanding-raw-syscall",
        "no_android_or_magisk_handoff": True,
        "auto_reboot": False,
        "reboot_syscall": False,
        "host_commanded_reboot_download": False,
        "persistent_partition_mount": False,
        "block_device_writes": False,
        "module_binary_injection": False,
        "module_list_path": "/s22plus_m18_full_firststage_usb.modules",
        "udc_binding": "a600000.dwc3 only; never dummy_udc.0",
    }
    for key, expected in required_safety.items():
        if safety.get(key) != expected:
            raise SystemExit(f"M18 manifest safety {key} mismatch: {safety.get(key)!r} != {expected!r}")
    if ramdisk.get("replaced_entry") != "init":
        raise SystemExit("M18 did not replace /init")
    if ramdisk.get("added_subset_entry") != "s22plus_m18_full_firststage_usb.modules":
        raise SystemExit("M18 did not add the expected module list")
    if ramdisk.get("module_files_injected_into_boot_ramdisk") != 0:
        raise SystemExit("M18 must not inject module binaries into boot ramdisk")
    if vendor.get("subset_count") != EXPECTED_M18_MODULE_COUNT:
        raise SystemExit(f"M18 module count mismatch: {vendor.get('subset_count')!r}")

    required_strings = set(m18_init.get("required_strings", []))
    for required in [
        EXPECTED_M18_MARKER,
        "module_group=full_firststage_usb",
        "module_count=141",
        "watchdog_blocklist=1",
        "no_reboot_beacon=1",
        "a600000.dwc3",
        "role_force=device",
        "ss_acm.0",
        "S22M18FULL0001",
    ]:
        if required not in required_strings:
            raise SystemExit(f"M18 required string missing: {required}")


def verify_agents_exception(root: Path, log_path: Path) -> None:
    agents = (root / "AGENTS.md").read_text(encoding="utf-8")
    normalized = " ".join(agents.split())
    required = [
        "S22+ ramoops DTBO + M18 capture",
        EXPECTED_DTBO_CANDIDATE_AP_SHA256,
        EXPECTED_DTBO_ROLLBACK_AP_SHA256,
        EXPECTED_PATCHED_DTBO_RAW_SHA256,
        EXPECTED_STOCK_DTBO_RAW_SHA256,
        EXPECTED_M18_AP_SHA256,
        EXPECTED_M18_BOOT_SHA256,
        EXPECTED_M18_BASE_BOOT_SHA256,
        EXPECTED_MAGISK_AP_SHA256,
        EXPECTED_STOCK_BOOT_AP_SHA256,
        LIVE_ACK_TOKEN,
        ROLLBACK_BOOT_ACK_TOKEN,
        RESTORE_DTBO_ACK_TOKEN,
        "dtbo.img.lz4",
        "boot.img.lz4",
        "disabled-vbmeta",
        "pstore",
        "restore stock DTBO",
        "manual download-mode",
    ]
    missing = [item for item in required if item not in normalized]
    append_log(log_path, f"agents_exception_missing={missing}")
    if missing:
        raise SystemExit(f"AGENTS.md missing ramoops DTBO + M18 capture authorization markers: {missing}")


def verify_current_boot_hash(log_path: Path, serial: str) -> None:
    result = adb_shell(
        "su -c 'dd if=/dev/block/by-name/boot bs=4096 2>/dev/null | sha256sum'",
        serial=serial,
        timeout=45.0,
    )
    text = result.stdout + result.stderr
    append_log(log_path, f"current_boot_hash_rc={result.returncode}")
    append_log(log_path, text)
    if result.returncode != 0 or EXPECTED_M18_BASE_BOOT_SHA256 not in text:
        raise SystemExit("current boot hash does not match known-booting Magisk baseline")


def wait_for_android_root(log_path: Path, wait_sec: int, serial: str | None = None) -> str | None:
    deadline = time.monotonic() + wait_sec
    while True:
        rows = adb_rows(log_path, "android-wait", serial)
        usable = [row for row in rows if row[1] == "device"]
        if serial:
            usable = [row for row in usable if row[0] == serial]
        if len(usable) == 1:
            selected = usable[0][0]
            props = adb_shell(
                "printf 'boot_completed='; getprop sys.boot_completed; "
                "printf 'model='; getprop ro.product.model; "
                "printf 'device='; getprop ro.product.device; "
                "printf 'bootloader='; getprop ro.boot.bootloader; "
                "printf 'incremental='; getprop ro.build.version.incremental; "
                "printf 'vbstate='; getprop ro.boot.verifiedbootstate; "
                "printf 'boot_recovery='; getprop ro.boot.boot_recovery; "
                "printf 'su_id='; su -c id 2>/dev/null || true",
                serial=selected,
                timeout=25.0,
            )
            text = props.stdout + props.stderr
            append_log(log_path, "android_wait_props:")
            append_log(log_path, text)
            required = [
                "boot_completed=1",
                f"model={EXPECTED_MODEL}",
                f"device={EXPECTED_DEVICE}",
                f"bootloader={EXPECTED_BUILD}",
                f"incremental={EXPECTED_BUILD}",
                "vbstate=orange",
                "boot_recovery=0",
                "uid=0(root)",
            ]
            if all(item in text for item in required):
                return selected
        if time.monotonic() >= deadline:
            return None
        time.sleep(2.0)


def is_m18_acm(device: dict[str, Any]) -> bool:
    model = str(device.get("model", ""))
    return (
        device.get("vendor") == EXPECTED_M18_USB_VENDOR
        and device.get("product") == EXPECTED_M18_USB_PRODUCT
    ) or device.get("serial") == EXPECTED_M18_USB_SERIAL or "S22_Native_Init_M18" in model


def observe_m18(run_dir: Path, log_path: Path, seconds: int, odin: Path) -> tuple[str, str | None]:
    host_snapshot(run_dir, log_path, "after_m18_flash", odin)
    deadline = time.monotonic() + seconds
    iteration = 0
    while time.monotonic() < deadline:
        iteration += 1
        label = f"m18_capture_observe_{iteration:03d}"
        if iteration == 1 or iteration % 5 == 0:
            host_snapshot(run_dir, log_path, label, odin)
        for device in acm_devices(log_path, label):
            if is_m18_acm(device):
                path = str(device["path"])
                payload = read_acm_banner(path, log_path)
                append_log(log_path, f"m18_acm_seen=1 path={path} banner_has_marker={int(EXPECTED_M18_MARKER.encode('ascii') in payload)}")
                return ("acm", path)
        devices = odin_devices(odin, log_path, f"{label}-odin")
        if len(devices) == 1:
            append_log(log_path, f"m18_odin_seen=1 device={devices[0]}")
            return ("odin", devices[0])
        if len(devices) > 1:
            raise SystemExit(f"refusing ambiguous Odin devices during M18 observation: {devices}")
        rows = adb_rows(log_path, f"{label}-adb")
        usable = [row for row in rows if row[1] == "device"]
        if len(usable) == 1:
            append_log(log_path, f"m18_adb_returned=1 serial={usable[0][0]}")
            return ("adb", usable[0][0])
        if len(usable) > 1:
            raise SystemExit(f"refusing ambiguous ADB devices during M18 observation: {usable}")
        time.sleep(1.0)
    append_log(log_path, "m18_observe_timeout=1")
    return ("none", None)


def reboot_android_to_download(serial: str, log_path: Path, label: str) -> None:
    result = run(["adb", "-s", serial, "reboot", "download"], timeout=20.0)
    append_log(log_path, f"{label}_adb_reboot_download_rc={result.returncode}")
    append_log(log_path, result.stdout + result.stderr)
    if result.returncode != 0:
        raise SystemExit(f"{label} adb reboot download failed rc={result.returncode}")


def restore_dtbo_from_download(
    odin: Path,
    dtbo_rollback_ap: Path,
    log_path: Path,
    android_wait_sec: int,
    serial: str | None = None,
) -> int:
    device = wait_for_odin(odin, log_path, "stock-dtbo-rollback-wait", 5)
    if device is None:
        devices = odin_devices(odin, log_path, "stock-dtbo-rollback-present")
        if len(devices) != 1:
            raise SystemExit(f"stock DTBO rollback requires exactly one Odin device, got {devices}")
        device = devices[0]
    rc = flash_ap(odin, dtbo_rollback_ap, device, log_path, "stock_dtbo_rollback")
    if rc != 0:
        return rc or 5
    android = wait_for_android_root(log_path, android_wait_sec, serial)
    if android is None:
        return 6
    append_log(log_path, f"stock_dtbo_restore_android={android}")
    return 0


def rollback_boot_collect_pstore(
    odin: Path,
    boot_rollback_ap: Path,
    run_dir: Path,
    log_path: Path,
    rollback_target: str,
    android_wait_sec: int,
) -> tuple[int, str | None]:
    devices = odin_devices(odin, log_path, "boot-rollback")
    if len(devices) != 1:
        raise SystemExit(f"boot rollback requires exactly one Odin device, got {devices}")
    rc = flash_ap(odin, boot_rollback_ap, devices[0], log_path, f"{rollback_target}_boot_rollback")
    if rc != 0:
        return (rc or 5, None)
    android = wait_for_android_root(log_path, android_wait_sec)
    if android is None:
        return (6, None)
    marker_found = collect_android_pstore(run_dir, log_path, "post_m18_boot_rollback", android, marker=EXPECTED_M18_MARKER)
    append_log(log_path, f"m18_capture_pstore_marker_found={int(marker_found)}")
    return (0, android)


def preflight_common(args: argparse.Namespace) -> tuple[Path, Path, Path, Path, Path, Path, Path, Path, Path]:
    root = repo_root()
    run_dir = resolve_run_dir(root, args.run_dir)
    log_path = run_dir / "s22plus_ramoops_dtbo_m18_capture_live_gate.txt"
    append_log(log_path, f"=== {utc_now()} s22plus ramoops DTBO M18 capture live gate ===")
    append_log(log_path, f"target={EXPECTED_TARGET}")

    odin = resolve(root, args.odin)
    dtbo_candidate_ap = resolve(root, args.dtbo_candidate_ap)
    dtbo_rollback_ap = resolve(root, args.dtbo_rollback_ap)
    dtbo_manifest = resolve(root, args.dtbo_manifest)
    m18_ap = resolve(root, args.m18_ap)
    m18_manifest = resolve(root, args.m18_manifest)
    magisk_rollback_ap = resolve(root, args.magisk_rollback_ap)
    stock_rollback_ap = resolve(root, args.stock_rollback_ap)
    if not odin.is_file():
        raise SystemExit(f"odin4 missing: {odin}")

    verify_ap_member(dtbo_candidate_ap, EXPECTED_DTBO_CANDIDATE_AP_SHA256, EXPECTED_DTBO_MEMBER, "dtbo_candidate", log_path)
    verify_ap_member(dtbo_rollback_ap, EXPECTED_DTBO_ROLLBACK_AP_SHA256, EXPECTED_DTBO_MEMBER, "dtbo_stock_rollback", log_path)
    verify_dtbo_manifest(dtbo_manifest, log_path)
    verify_ap_member(m18_ap, EXPECTED_M18_AP_SHA256, EXPECTED_BOOT_MEMBER, "m18_candidate", log_path)
    verify_m18_manifest(m18_manifest, log_path)
    verify_ap_member(magisk_rollback_ap, EXPECTED_MAGISK_AP_SHA256, EXPECTED_BOOT_MEMBER, "magisk_boot_rollback", log_path)
    verify_ap_member(stock_rollback_ap, EXPECTED_STOCK_BOOT_AP_SHA256, EXPECTED_BOOT_MEMBER, "stock_boot_fallback", log_path)
    return root, run_dir, log_path, odin, dtbo_candidate_ap, dtbo_rollback_ap, m18_ap, magisk_rollback_ap, stock_rollback_ap


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dtbo-candidate-ap", type=Path, default=DEFAULT_DTBO_CANDIDATE_AP)
    parser.add_argument("--dtbo-rollback-ap", type=Path, default=DEFAULT_DTBO_ROLLBACK_AP)
    parser.add_argument("--dtbo-manifest", type=Path, default=DEFAULT_DTBO_MANIFEST)
    parser.add_argument("--m18-ap", type=Path, default=DEFAULT_M18_AP)
    parser.add_argument("--m18-manifest", type=Path, default=DEFAULT_M18_MANIFEST)
    parser.add_argument("--magisk-rollback-ap", type=Path, default=DEFAULT_MAGISK_ROLLBACK_AP)
    parser.add_argument("--stock-rollback-ap", type=Path, default=DEFAULT_STOCK_ROLLBACK_AP)
    parser.add_argument("--odin", type=Path, default=DEFAULT_ODIN)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--serial", help="ADB serial to pin before live flashing")
    parser.add_argument("--m18-observe-sec", type=int, default=180)
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
        )
        if enabled
    )
    if modes > 1:
        raise SystemExit(
            "--offline-check, --live, --rollback-boot-from-download, "
            "--restore-dtbo-from-download, and --restore-dtbo-from-android are mutually exclusive"
        )

    (
        root,
        run_dir,
        log_path,
        odin,
        dtbo_candidate_ap,
        dtbo_rollback_ap,
        m18_ap,
        magisk_rollback_ap,
        stock_rollback_ap,
    ) = preflight_common(args)

    if args.offline_check:
        append_log(log_path, "offline_check=ok device_action=0 agents_exception_checked=0 android_checked=0")
        print(f"offline-check ok: DTBO/M18 candidate and rollback APs verified; no device action; log={log_path}")
        return 0

    verify_agents_exception(root, log_path)

    if args.rollback_boot_from_download:
        if args.ack != ROLLBACK_BOOT_ACK_TOKEN:
            raise SystemExit(f"--rollback-boot-from-download requires --ack {ROLLBACK_BOOT_ACK_TOKEN}")
        boot_rollback_ap = magisk_rollback_ap if args.rollback_target == ROLLBACK_MAGISK else stock_rollback_ap
        rc, android = rollback_boot_collect_pstore(
            odin,
            boot_rollback_ap,
            run_dir,
            log_path,
            args.rollback_target,
            args.android_wait_sec,
        )
        print(f"M18 boot rollback-from-download completed rc={rc} android={android}; log={log_path}")
        return rc

    if args.restore_dtbo_from_download:
        if args.ack != RESTORE_DTBO_ACK_TOKEN:
            raise SystemExit(f"--restore-dtbo-from-download requires --ack {RESTORE_DTBO_ACK_TOKEN}")
        rc = restore_dtbo_from_download(odin, dtbo_rollback_ap, log_path, args.android_wait_sec)
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
    host_snapshot(run_dir, log_path, "dryrun_current", odin)

    if args.restore_dtbo_from_android:
        if args.ack != RESTORE_DTBO_ACK_TOKEN:
            raise SystemExit(f"--restore-dtbo-from-android requires --ack {RESTORE_DTBO_ACK_TOKEN}")
        reboot_android_to_download(selected_serial, log_path, "stock_dtbo_restore")
        device = wait_for_odin(odin, log_path, "stock-dtbo-restore-wait", args.odin_wait_sec)
        if device is None:
            print("download mode did not appear for stock DTBO restore", file=sys.stderr)
            return 2
        rc = flash_ap(odin, dtbo_rollback_ap, device, log_path, "stock_dtbo_rollback")
        if rc != 0:
            return rc or 5
        android = wait_for_android_root(log_path, args.android_wait_sec)
        print(f"stock DTBO restore-from-android completed android={android}; log={log_path}")
        return 0 if android else 6

    if not args.live:
        print(
            "dry-run ok: DTBO/M18 candidates, rollback APs, AGENTS exception, Android stability, "
            f"and boot hash verified; log={log_path}"
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
        print(
            "Android did not return after patched DTBO. Enter download mode and run --restore-dtbo-from-download.",
            file=sys.stderr,
        )
        return 6
    append_log(log_path, f"patched_dtbo_android_ok={patched_serial}")

    reboot_android_to_download(patched_serial, log_path, "m18_candidate")
    device = wait_for_odin(odin, log_path, "m18-candidate-wait", args.odin_wait_sec)
    if device is None:
        print("download mode did not appear for M18 candidate flash", file=sys.stderr)
        return 2
    rc = flash_ap(odin, m18_ap, device, log_path, "m18_candidate")
    if rc != 0:
        print(f"M18 candidate Odin flash failed rc={rc}; log={log_path}", file=sys.stderr)
        return rc or 3

    observed, endpoint = observe_m18(run_dir, log_path, args.m18_observe_sec, odin)
    if observed == "acm":
        append_log(log_path, f"m18_result=acm_seen endpoint={endpoint}")
        print(
            "M18 ACM appeared. Enter download mode manually for boot rollback, then run --rollback-boot-from-download.",
            file=sys.stderr,
        )
        return 4
    if observed == "adb" and endpoint:
        append_log(log_path, f"m18_unexpected_adb_returned={endpoint}")
        reboot_android_to_download(endpoint, log_path, "m18_unexpected_adb_rollback")
        endpoint = wait_for_odin(odin, log_path, "m18-unexpected-adb-rollback-wait", args.odin_wait_sec)
        observed = "odin" if endpoint else "none"
    if observed != "odin" or endpoint is None:
        append_log(log_path, "m18_result=no_rollback_transport_manual_download_required")
        print("M18 did not expose rollback transport. Enter download mode manually and run --rollback-boot-from-download.", file=sys.stderr)
        return 4

    boot_rollback_ap = magisk_rollback_ap if args.rollback_target == ROLLBACK_MAGISK else stock_rollback_ap
    rc = flash_ap(odin, boot_rollback_ap, endpoint, log_path, f"{args.rollback_target}_boot_rollback")
    if rc != 0 and args.rollback_target == ROLLBACK_MAGISK:
        append_log(log_path, "magisk_rollback_failed_attempting_stock_fallback=1")
        fallback = wait_for_odin(odin, log_path, "stock-boot-fallback-wait", 30)
        if fallback:
            rc = flash_ap(odin, stock_rollback_ap, fallback, log_path, "stock_boot_fallback")
    if rc != 0:
        return rc or 5

    post_boot_rollback_android = wait_for_android_root(log_path, args.android_wait_sec)
    if post_boot_rollback_android is None:
        return 6
    marker_found = collect_android_pstore(run_dir, log_path, "post_m18_boot_rollback", post_boot_rollback_android, marker=EXPECTED_M18_MARKER)
    append_log(log_path, f"m18_capture_pstore_marker_found={int(marker_found)}")

    reboot_android_to_download(post_boot_rollback_android, log_path, "stock_dtbo_restore_after_capture")
    device = wait_for_odin(odin, log_path, "stock-dtbo-after-capture-wait", args.odin_wait_sec)
    if device is None:
        print("download mode did not appear for final stock DTBO restore; run --restore-dtbo-from-android/download.", file=sys.stderr)
        return 7
    rc = flash_ap(odin, dtbo_rollback_ap, device, log_path, "stock_dtbo_rollback_after_capture")
    if rc != 0:
        return rc or 8
    final_android = wait_for_android_root(log_path, args.android_wait_sec)
    append_log(log_path, f"final_android_after_stock_dtbo={final_android}")
    if final_android is None:
        return 9
    print(
        f"ramoops DTBO + M18 capture live gate completed; pstore_marker_found={int(marker_found)}; log={log_path}"
    )
    return 0 if marker_found else 10


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
