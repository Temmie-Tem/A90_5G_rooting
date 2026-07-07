#!/usr/bin/env python3
"""Guarded S22+ M12 M5-floor USB-ACM native-init live gate.

Default dry-run and live modes require a SHA-pinned AGENTS.md exception plus a
recovered rooted Android baseline.  --offline-check verifies only the host-built
M12 package and rollback APs without touching any device.

M12 deliberately has no reboot beacon and no ACM-triggered download command.
If M12 parks or exposes ACM, rollback requires operator manual download-mode
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


LIVE_ACK_TOKEN = "S22PLUS-M12-M5-FLOOR-LIVE-GATE"
ROLLBACK_ACK_TOKEN = "S22PLUS-M12-ROLLBACK-FROM-DOWNLOAD"

EXPECTED_TARGET = "SM-S906N/g0q/S906NKSS7FYG8"
EXPECTED_M12_AP_SHA256 = "deece127aa5c85dbf4937459fc528f2cfcd9926fb3556f26ffc9b10fbfe932cb"
EXPECTED_M12_BOOT_SHA256 = "f211e46c7153df31c458a907f4ac56fe4a3d160d8ded2a13a8e0e31af6f5106c"
EXPECTED_M12_BASE_BOOT_SHA256 = "2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e"
EXPECTED_M12_KERNEL_SHA256 = "bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff"
EXPECTED_M12_INIT_SHA256 = "50ae525230680c495d3c40fc671cb88118e8bd473cef92873266142549a28002"
EXPECTED_M12_SOURCE_SHA256 = "5b43593a24b3b03a667f5515b8a558e40121b4da091efb56adf383ea50240392"
EXPECTED_M12_SUBSET_SHA256 = "c2e44f6f934542f8f7889ef09245294ee342c5ae03a0f6db9988b58b943ddc16"
EXPECTED_M12_VENDOR_RAMDISK_SHA256 = "41b2481b779ff48863c300250dabf1b3dcc45c7f58fab421fcf6df1245145193"
EXPECTED_M12_MARKER = "S22_NATIVE_INIT_USB_ACM_M12"
EXPECTED_M12_USB_VENDOR = "04e8"
EXPECTED_M12_USB_PRODUCT = "685d"
EXPECTED_M12_USB_SERIAL = "S22M12ACM0001"
EXPECTED_VENDOR_KO_COUNT = 441
EXPECTED_RECOVERY_COUNT = 446
EXPECTED_RECOVERY_BYTES = 7239
EXPECTED_M5_FLOOR_COUNT = 24
EXPECTED_M11_ONLY_REFERENCE_COUNT = 24
EXPECTED_M5_FLOOR_BYTES = 391
EXPECTED_M5_FLOOR_BUFFER = 8192
EXPECTED_MODULE_NAME_BUFFER = 128
EXPECTED_M5_ONLY_WITHHELD = ["usb_notifier_qcom.ko", "qc_usb_audio.ko"]
EXPECTED_M5_FLOOR_MODULES = [
    "phy-msm-ssusb-qmp.ko",
    "phy-msm-snps-eusb2.ko",
    "dwc3-msm.ko",
    "usb_f_diag.ko",
    "usb_f_qdss.ko",
    "usb_f_gsi.ko",
    "usb_f_conn_gadget.ko",
    "usb_f_ss_mon_gadget.ko",
    "usb_f_ss_acm.ko",
    "repeater.ko",
    "redriver.ko",
    "usb_notify_layer.ko",
    "ipa_fmwk.ko",
    "usb_bam.ko",
    "sps_drv.ko",
    "switch_class.ko",
    "common_muic.ko",
    "vbus_notifier.ko",
    "usb_typec_manager.ko",
    "if_cb_manager.ko",
    "pdic_notifier_module.ko",
    "mfd_max77705.ko",
    "pdic_max77705.ko",
    "spu_verify.ko",
]

DEFAULT_M12_AP = Path("workspace/private/outputs/s22plus_native_init/inplace_m12_m5_floor_v0_1/odin4/AP.tar.md5")
DEFAULT_M12_MANIFEST = Path("workspace/private/outputs/s22plus_native_init/inplace_m12_m5_floor_v0_1/manifest.json")


def resolve_run_dir(root: Path, requested: Path | None) -> Path:
    if requested is not None:
        run_dir = requested
        run_dir = resolve(root, run_dir)
        run_dir.mkdir(parents=True, exist_ok=False)
        return run_dir
    else:
        stamp = utc_now().replace("-", "").replace(":", "").replace("Z", "Z")
        base = resolve(root, DEFAULT_RUN_ROOT / f"s22plus_m12_m5_floor_live_gate_{stamp}")
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
        "S22+ M12 M5-floor USB-ACM native-init boot-only",
        EXPECTED_M12_AP_SHA256,
        EXPECTED_M12_BOOT_SHA256,
        EXPECTED_M12_BASE_BOOT_SHA256,
        EXPECTED_M12_KERNEL_SHA256,
        EXPECTED_M12_INIT_SHA256,
        EXPECTED_M12_SUBSET_SHA256,
        EXPECTED_M12_VENDOR_RAMDISK_SHA256,
        LIVE_ACK_TOKEN,
        ROLLBACK_ACK_TOKEN,
        "s22plus_m12_m5_floor.modules",
        "24 modules",
        "M5/M11 common",
        "M5-only",
        "usb_notifier_qcom.ko",
        "no reboot beacon",
        "park-vs-loop",
        "watchdog",
        "qc_usb_audio.ko",
        "a600000.dwc3",
        "never dummy_udc.0",
        "manual download-mode rollback",
    ]
    missing = [item for item in required if item not in normalized]
    append_log(log_path, f"agents_exception_missing={missing}")
    if missing:
        raise SystemExit(f"AGENTS.md missing M12 live authorization markers: {missing}")


def verify_m12_manifest(path: Path, log_path: Path) -> None:
    if not path.is_file():
        raise SystemExit(f"M12 manifest missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    hashes = data.get("hashes", {})
    safety = data.get("safety", {})
    ramdisk = data.get("ramdisk", {})
    vendor = data.get("vendor_ramdisk", {})
    m12_init = data.get("m12_init", {})
    tar_members_seen = data.get("tar_members")
    append_log(log_path, f"m12_manifest_path={path}")
    append_log(log_path, f"m12_manifest_hashes={json.dumps(hashes, sort_keys=True)}")
    append_log(log_path, f"m12_manifest_safety={json.dumps(safety, sort_keys=True)}")
    append_log(log_path, f"m12_manifest_ramdisk={json.dumps(ramdisk, sort_keys=True)}")
    append_log(log_path, f"m12_manifest_vendor={json.dumps(vendor, sort_keys=True)}")
    if hashes.get("ap_tar_md5") != EXPECTED_M12_AP_SHA256:
        raise SystemExit("M12 manifest AP hash mismatch")
    if hashes.get("boot_img") != EXPECTED_M12_BOOT_SHA256:
        raise SystemExit("M12 manifest boot image hash mismatch")
    if hashes.get("base_boot") != EXPECTED_M12_BASE_BOOT_SHA256:
        raise SystemExit("M12 manifest base boot hash mismatch")
    if hashes.get("kernel") != EXPECTED_M12_KERNEL_SHA256:
        raise SystemExit("M12 manifest kernel hash mismatch")
    if hashes.get("m12_init") != EXPECTED_M12_INIT_SHA256:
        raise SystemExit("M12 manifest init hash mismatch")
    if hashes.get("source") != EXPECTED_M12_SOURCE_SHA256:
        raise SystemExit("M12 manifest source hash mismatch")
    if hashes.get("m12_m5_floor") != EXPECTED_M12_SUBSET_SHA256:
        raise SystemExit("M12 manifest subset-list hash mismatch")
    if hashes.get("vendor_ramdisk") != EXPECTED_M12_VENDOR_RAMDISK_SHA256:
        raise SystemExit("M12 manifest vendor ramdisk hash mismatch")
    if tar_members_seen != [EXPECTED_MEMBER]:
        raise SystemExit(f"M12 manifest tar members mismatch: {tar_members_seen!r}")
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
        "module_list_path": "/s22plus_m12_m5_floor.modules",
        "module_subset": "M5 v0.4 order filtered to the 24 modules common with M11; M5-only qc_usb_audio/usb_notifier_qcom withheld",
        "configfs_runtime_gadget": "ss_acm.0 only",
        "udc_binding": "a600000.dwc3 only; never dummy_udc.0",
        "usb_role_force": "attempt /sys/class/usb_role/*/role=device",
        "watchdog": "not-touched-by-init-source; watchdog modules absent from M12 floor subset",
        "observation_model": "park-vs-loop plus host ACM enumeration; no reboot beacon",
    }
    for key, expected in required_safety.items():
        if safety.get(key) != expected:
            raise SystemExit(f"M12 manifest safety {key} mismatch: {safety.get(key)!r} != {expected!r}")
    if ramdisk.get("replaced_entry") != "init":
        raise SystemExit("M12 manifest did not replace /init")
    if ramdisk.get("added_subset_entry") != "s22plus_m12_m5_floor.modules":
        raise SystemExit("M12 manifest did not add subset list")
    if ramdisk.get("module_list_files_injected_into_boot_ramdisk") != 1:
        raise SystemExit("M12 must inject exactly one module-list text file into boot ramdisk")
    if ramdisk.get("module_files_injected_into_boot_ramdisk") != 0:
        raise SystemExit("M12 must not inject vendor modules into boot ramdisk")
    if vendor.get("ko_count") != EXPECTED_VENDOR_KO_COUNT:
        raise SystemExit("M12 vendor .ko count mismatch")
    if vendor.get("modules_load_recovery_count") != EXPECTED_RECOVERY_COUNT:
        raise SystemExit("M12 modules.load.recovery count mismatch")
    if vendor.get("modules_load_recovery_bytes") != EXPECTED_RECOVERY_BYTES:
        raise SystemExit("M12 modules.load.recovery byte count mismatch")
    if vendor.get("runtime_module_name_buffer") != EXPECTED_MODULE_NAME_BUFFER:
        raise SystemExit("M12 runtime module-name buffer mismatch")
    if vendor.get("modules_load_recovery_max_basename_len", EXPECTED_MODULE_NAME_BUFFER) >= EXPECTED_MODULE_NAME_BUFFER:
        raise SystemExit("M12 modules.load.recovery basename does not fit runtime parser buffer")
    if vendor.get("modules_load_recovery_has_inline_whitespace") is not False:
        raise SystemExit("M12 modules.load.recovery has inline whitespace tokens")
    if vendor.get("modules_load_recovery_all_ko") is not True:
        raise SystemExit("M12 modules.load.recovery contains non-.ko entries")
    if vendor.get("modules_softdep_has_dwc3_msm") is not True:
        raise SystemExit("M12 vendor softdep gate did not prove dwc3_msm")
    subset = vendor.get("m12_m5_floor", {})
    append_log(log_path, f"m12_manifest_m5_floor={json.dumps(subset, sort_keys=True)}")
    if subset.get("m5_floor_common_count") != EXPECTED_M5_FLOOR_COUNT:
        raise SystemExit("M12 M5-floor common count mismatch")
    if subset.get("subset_count") != EXPECTED_M5_FLOOR_COUNT:
        raise SystemExit("M12 M5 floor count mismatch")
    if subset.get("subset_bytes") != EXPECTED_M5_FLOOR_BYTES:
        raise SystemExit("M12 M5 floor byte count mismatch")
    if subset.get("runtime_modules_m5_floor_buffer") != EXPECTED_M5_FLOOR_BUFFER:
        raise SystemExit("M12 M5 floor runtime buffer mismatch")
    if subset.get("subset_bytes", EXPECTED_M5_FLOOR_BUFFER) >= subset.get("runtime_modules_m5_floor_buffer", 0):
        raise SystemExit("M12 M5 floor does not fit runtime buffer")
    if subset.get("runtime_module_name_buffer") != EXPECTED_MODULE_NAME_BUFFER:
        raise SystemExit("M12 M5 floor module-name buffer mismatch")
    if subset.get("subset_max_basename_len", EXPECTED_MODULE_NAME_BUFFER) >= EXPECTED_MODULE_NAME_BUFFER:
        raise SystemExit("M12 M5 floor basename does not fit runtime parser buffer")
    if subset.get("m11_only_reference_count") != EXPECTED_M11_ONLY_REFERENCE_COUNT:
        raise SystemExit("M12 M11-only reference count mismatch")
    if subset.get("m5_only_withheld_modules") != EXPECTED_M5_ONLY_WITHHELD:
        raise SystemExit("M12 M5-only withheld module list mismatch")
    if subset.get("order_source") != "M5 v0.4 order filtered to modules common with M11":
        raise SystemExit("M12 M5-floor order source mismatch")
    explicit_blocklist = set(subset.get("explicit_m12_blocklist", []))
    expected_explicit = {
        "abc.ko",
        "altmode-glink.ko",
        "eud.ko",
        "gh_virt_wdt.ko",
        "icc-debug.ko",
        "minidump.ko",
        "pdr_interface.ko",
        "pmic_glink.ko",
        "qc_usb_audio.ko",
        "qcom_glink.ko",
        "qcom_glink_smem.ko",
        "qcom_smd.ko",
        "qcom_soc_wdt.ko",
        "qcom_wdt_core.ko",
        "qmi_helpers.ko",
        "rproc_qcom_common.ko",
        "sec_debug.ko",
        "sec_qc_qcom_wdt_core.ko",
        "ucsi_glink.ko",
    }
    if explicit_blocklist != expected_explicit:
        raise SystemExit("M12 explicit blocklist mismatch")
    final_subset = subset.get("subset", [])
    if final_subset != EXPECTED_M5_FLOOR_MODULES:
        raise SystemExit("M12 final subset does not match the expected M5/M11 common floor")
    if subset.get("m5_floor_common_modules") != EXPECTED_M5_FLOOR_MODULES:
        raise SystemExit("M12 manifest common module list mismatch")
    if len(final_subset) != EXPECTED_M5_FLOOR_COUNT:
        raise SystemExit("M12 final subset length mismatch")
    forbidden_present = sorted(expected_explicit.intersection(final_subset))
    if forbidden_present:
        raise SystemExit(f"M12 final subset contains explicitly blocked modules: {forbidden_present}")
    for required_module in (
        "dwc3-msm.ko",
        "usb_f_ss_acm.ko",
        "usb_typec_manager.ko",
        "if_cb_manager.ko",
        "pdic_notifier_module.ko",
        "vbus_notifier.ko",
        "mfd_max77705.ko",
        "pdic_max77705.ko",
    ):
        if required_module not in final_subset:
            raise SystemExit(f"M12 final subset missing critical USB module: {required_module}")
    required_strings = set(m12_init.get("required_strings", []))
    for required in [
        EXPECTED_M12_MARKER,
        "/s22plus_m12_m5_floor.modules",
        "module_list=boot_ramdisk_m5_floor",
        "watchdog_blocklist=1",
        "no_reboot_beacon=1",
        "acm_cmd_status=1",
        "module_source=stock_vendor_boot_ramdisk",
        "module_injection=list_only",
        "a600000.dwc3",
        "role_force=device",
        "ss_acm.0",
        "ttyGS0",
        EXPECTED_M12_USB_SERIAL,
        "S22_NATIVE_INIT_USB_ACM_M12 READY",
        "S22_NATIVE_INIT_USB_ACM_M12 ACK status park",
    ]:
        if required not in required_strings:
            raise SystemExit(f"M12 required string missing from manifest: {required}")
    objdump = str(m12_init.get("objdump", ""))
    reboot_nr_lines = [
        line
        for line in objdump.splitlines()
        if "mov" in line and "x8" in line and "#0x8e" in line and "// #142" in line
    ]
    if reboot_nr_lines:
        raise SystemExit(f"M12 /init unexpectedly loads arm64 __NR_reboot: {reboot_nr_lines}")


def is_m12_acm(device: dict[str, Any]) -> bool:
    model = str(device.get("model", ""))
    return (
        device.get("vendor") == EXPECTED_M12_USB_VENDOR
        and device.get("product") == EXPECTED_M12_USB_PRODUCT
    ) or device.get("serial") == EXPECTED_M12_USB_SERIAL or "S22_Native_Init_M12_ACM" in model


def observe_m12_acm(run_dir: Path, log_path: Path, seconds: int, odin: Path) -> tuple[str, str | None]:
    host_snapshot(run_dir, log_path, "after_candidate_flash", odin)
    deadline = time.monotonic() + seconds
    iteration = 0
    while time.monotonic() < deadline:
        iteration += 1
        label = f"m12_acm_observe_{iteration:03d}"
        if iteration == 1 or iteration % 5 == 0:
            host_snapshot(run_dir, log_path, label, odin)
        for device in acm_devices(log_path, label):
            if is_m12_acm(device):
                path = str(device["path"])
                payload = read_acm_banner(path, log_path)
                append_log(log_path, f"m12_acm_seen=1 path={path} banner_found={int(EXPECTED_M12_MARKER.encode('ascii') in payload)}")
                return ("acm", path)
        devices = odin_devices(odin, log_path, f"{label}-odin")
        if len(devices) == 1:
            append_log(log_path, f"m12_odin_returned=1 device={devices[0]}")
            return ("odin", devices[0])
        if len(devices) > 1:
            raise SystemExit(f"refusing ambiguous Odin devices during M12 observation: {devices}")
        rows = adb_rows(log_path, f"{label}-adb")
        usable = [row for row in rows if row[1] == "device"]
        if len(usable) == 1:
            append_log(log_path, f"m12_adb_returned=1 serial={usable[0][0]}")
            return ("adb", usable[0][0])
        if len(usable) > 1:
            raise SystemExit(f"refusing ambiguous ADB devices during M12 observation: {usable}")
        time.sleep(1.0)
    append_log(log_path, "m12_acm_seen=0")
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
    collect_android_pstore(run_dir, log_path, "post_rollback", serial, marker=EXPECTED_M12_MARKER)
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m12-ap", type=Path, default=DEFAULT_M12_AP)
    parser.add_argument("--m12-manifest", type=Path, default=DEFAULT_M12_MANIFEST)
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
    log_path = run_dir / "s22plus_m12_m5_floor_live_gate.txt"
    append_log(log_path, f"=== {utc_now()} s22plus m12 M5-floor live gate ===")
    append_log(log_path, f"target={EXPECTED_TARGET}")

    odin = resolve(root, args.odin)
    m12_ap = resolve(root, args.m12_ap)
    m12_manifest = resolve(root, args.m12_manifest)
    magisk_rollback_ap = resolve(root, args.magisk_rollback_ap)
    stock_rollback_ap = resolve(root, args.stock_rollback_ap)
    rollback_ap = magisk_rollback_ap if args.rollback_target == ROLLBACK_MAGISK else stock_rollback_ap
    if not odin.is_file():
        raise SystemExit(f"odin4 missing: {odin}")

    verify_ap(m12_ap, EXPECTED_M12_AP_SHA256, "m12_candidate", log_path)
    verify_m12_manifest(m12_manifest, log_path)
    verify_ap(magisk_rollback_ap, EXPECTED_MAGISK_AP_SHA256, "magisk_boot_rollback", log_path)
    verify_ap(stock_rollback_ap, EXPECTED_STOCK_BOOT_AP_SHA256, "stock_boot_fallback", log_path)

    if args.offline_check:
        append_log(log_path, "offline_check=ok device_action=0 agents_exception_checked=0 android_checked=0")
        print(f"offline-check ok: M12 candidate and rollback APs verified; no device action; log={log_path}")
        return 0

    verify_agents_exception(root, log_path)

    if args.rollback_from_download:
        if args.ack != ROLLBACK_ACK_TOKEN:
            raise SystemExit(f"--rollback-from-download requires --ack {ROLLBACK_ACK_TOKEN}")
        rc = rollback_from_download(odin, rollback_ap, run_dir, log_path, args.rollback_target, args.android_wait_sec)
        print(f"M12 rollback-from-download completed rc={rc}; log={log_path}")
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
        print(f"dry-run ok: M12 candidate, rollback APs, AGENTS exception, Android stability, and boot hash verified; log={log_path}")
        return 0
    if args.ack != LIVE_ACK_TOKEN:
        raise SystemExit(f"--live requires --ack {LIVE_ACK_TOKEN}")

    reboot = run(["adb", "-s", selected_serial, "reboot", "download"], timeout=20.0)
    append_log(log_path, f"adb_reboot_download_rc={reboot.returncode}")
    append_log(log_path, reboot.stdout + reboot.stderr)
    odin_device = wait_for_odin(odin, log_path, "candidate-wait", args.odin_wait_sec)
    if odin_device is None:
        print("download mode did not appear for M12 candidate flash", file=sys.stderr)
        return 2

    candidate_rc = flash_ap(odin, m12_ap, odin_device, log_path, "candidate")
    if candidate_rc != 0:
        print(f"M12 candidate Odin flash failed rc={candidate_rc}; log={log_path}", file=sys.stderr)
        return candidate_rc or 3

    print("M12 candidate flashed. Waiting for M5-floor ACM/park signal. No reboot beacon exists.")
    observed, endpoint = observe_m12_acm(run_dir, log_path, args.acm_wait_sec, odin)
    if observed == "acm" and endpoint:
        append_log(log_path, f"m12_result=acm_seen_manual_download_required endpoint={endpoint}")
        print(
            "M12 ACM appeared. This is the target signal, but M12 has no reboot/download command path; "
            "enter download mode manually and run --rollback-from-download.",
            file=sys.stderr,
        )
        return 4
    elif observed == "odin":
        odin_device = endpoint
    elif observed == "adb" and endpoint:
        append_log(log_path, f"m12_unexpected_adb_returned={endpoint}")
        reboot_back = run(["adb", "-s", endpoint, "reboot", "download"], timeout=20.0)
        append_log(log_path, f"m12_unexpected_adb_reboot_download_rc={reboot_back.returncode}")
        append_log(log_path, reboot_back.stdout + reboot_back.stderr)
        odin_device = wait_for_odin(odin, log_path, "m12-unexpected-adb-rollback-wait", args.odin_wait_sec)
    else:
        append_log(log_path, "m12_result=no_acm_no_transport_manual_download_required")
        print("M12 ACM did not appear. Enter download mode manually and run --rollback-from-download.", file=sys.stderr)
        return 4
    if odin_device is None:
        print("M12 download mode did not appear; manual download rollback required.", file=sys.stderr)
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
    collect_android_pstore(run_dir, log_path, "post_rollback", post_rollback_serial, marker=EXPECTED_M12_MARKER)
    print(f"M12 live gate completed and rollback ok; log={log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
