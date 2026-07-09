#!/usr/bin/env python3
"""Guarded S22+ M34 S11P1 timed loader-result live gate.

Dry-run is the default. Live mode requires a fresh SHA-pinned AGENTS.md
exception and an explicit ack token.

S11P1 keeps the S9/S10C0/S11P0 isolated module recipe and changes only the
observation channel: the candidate always requests reboot(download) after a
bounded delay that encodes the loader/proc outcome.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from build_s22plus_m34_runtime_gadget_split import (
    M34_S10C0_PROBE_MODULE,
    M34_S10C0_PROBE_PROC_NAME,
    M34_S11P0_POSITIVE_CONTROL_MODULES,
    M34_S11P0_POSITIVE_CONTROL_PROC_NAMES,
    M34_S11P1_DELAY_MODEL,
    M34_S11P1_MODULE_LOAD_PROBE,
)
from s22plus_m3_observable_live_gate import (
    DEFAULT_MAGISK_ROLLBACK_AP,
    DEFAULT_ODIN,
    DEFAULT_RUN_ROOT,
    EXPECTED_MAGISK_AP_SHA256,
    ROLLBACK_MAGISK,
    ROLLBACK_STOCK,
    append_log,
    flash_ap,
    host_snapshot,
    odin_devices,
    repo_root,
    require_current_android,
    resolve,
    run,
    utc_now,
    verify_ap,
    wait_for_odin,
)
from s22plus_m25_hs_only_usb2_acm_live_gate import (
    EXPECTED_BASE_BOOT_SHA256,
    record_timeline_event,
    verify_partition_hash,
)
from s22plus_m34_s10c0_direct_finit_loader_audit_live_gate import (
    DEFAULT_STOCK_ROLLBACK_AP,
    EXPECTED_STOCK_BOOT_AP_SHA256,
    EXPECTED_STOCK_BOOT_RAW_SHA256,
    rollback_boot_only_from_download,
    wait_for_odin_absent,
)
from s22plus_m5_usb_acm_live_gate import verify_android_stability


LIVE_ACK_TOKEN = "S22PLUS-M34-S11P1-TIMED-LOADER-RESULT-LIVE-GATE"
ROLLBACK_ACK_TOKEN = "S22PLUS-M34-S11P1-TIMED-LOADER-RESULT-ROLLBACK-FROM-DOWNLOAD"

EXPECTED_TARGET = "SM-S906N/g0q/S906NKSS7FYG8"
EXPECTED_STAGE = "S11P1"
EXPECTED_STAGE_NUMBER = 22
DISPLAY_SERIAL_REDACTED = "<S22_SERIAL_REDACTED>"
EXPECTED_M34_MARKER = "S22_NATIVE_INIT_M34_RUNTIME_GADGET_SPLIT_S11P1"
EXPECTED_M34_AP_SHA256 = "1bc209674aa6b496bcc4132eae4343c1311de06143164771994cc8b1df945b56"
EXPECTED_M34_BOOT_SHA256 = "874c312b4ce1b95388c158a686f22e56d7a5278dd09cfab13c0c853ab688c61e"
EXPECTED_M34_BOOT_LZ4_SHA256 = "cb4234a257a91b4b7b43343f97c1c9f90049a2daca59cc28f19da5159567605a"
EXPECTED_M34_INIT_SHA256 = "af4eb75a8bcdcbbe8bd4fe81e1100cbc34ef786c1c2e64b09b111582c727c3d1"
EXPECTED_M34_MODULE_LIST_SHA256 = "c07425f4c738b53822e9f6783a142a2b5eafd72a15bd34c06fb3b49357c8fe26"
EXPECTED_M34_TEMPLATE_SOURCE_SHA256 = "4d6688c2961eb58e5a86ddf2c6372943c0e50faf1c50298ac4a3e783ade44fca"
EXPECTED_M34_KERNEL_SHA256 = "bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff"
EXPECTED_M34_BASE_BOOT_SHA256 = EXPECTED_BASE_BOOT_SHA256
EXPECTED_MODULE_COUNT = 89
EXPECTED_MEMBER = "boot.img.lz4"
EXPECTED_MODULE_ENTRY = "s22plus_m34_s11p1_runtime_gadget_split.modules"
EXPECTED_SCHEMA = "s22plus_m34_s11p1_timed_result_v1"

DEFAULT_M34_AP = Path("workspace/private/outputs/s22plus_native_init/m34_runtime_gadget_split_v0_15/S11P1/odin4/AP.tar.md5")
DEFAULT_M34_MANIFEST = Path("workspace/private/outputs/s22plus_native_init/m34_runtime_gadget_split_v0_15/manifest.json")
ACTIVE_EXCEPTION_INSERT_ANCHOR = "   **Consumed exception (2026-07-10, S22+ M34 S11P0 proc-modules positive-control boot-only live gate):**"


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def resolve_run_dir(root: Path, requested: Path | None) -> Path:
    if requested is not None:
        run_dir = resolve(root, requested)
        run_dir.mkdir(parents=True, exist_ok=False)
        return run_dir
    base = resolve(root, DEFAULT_RUN_ROOT / f"s22plus_m34_s11p1_timed_loader_result_live_gate_{utc_stamp()}")
    for suffix in range(100):
        run_dir = base if suffix == 0 else Path(f"{base}_{suffix:02d}")
        try:
            run_dir.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            continue
        return run_dir
    raise SystemExit(f"could not allocate unique run directory under {base.parent}")


def policy_required_markers() -> list[str]:
    delay_values = [str(value) for value in M34_S11P1_DELAY_MODEL.values()]
    return [
        "S22+ M34 S11P1 timed loader-result native-init boot-only",
        "workspace/public/src/scripts/revalidation/s22plus_m34_s11p1_timed_loader_result_live_gate.py",
        LIVE_ACK_TOKEN,
        ROLLBACK_ACK_TOKEN,
        EXPECTED_TARGET,
        EXPECTED_STAGE,
        EXPECTED_M34_MARKER,
        EXPECTED_M34_AP_SHA256,
        EXPECTED_M34_BOOT_SHA256,
        EXPECTED_M34_BOOT_LZ4_SHA256,
        EXPECTED_M34_INIT_SHA256,
        EXPECTED_M34_MODULE_LIST_SHA256,
        EXPECTED_M34_TEMPLATE_SOURCE_SHA256,
        EXPECTED_M34_KERNEL_SHA256,
        EXPECTED_M34_BASE_BOOT_SHA256,
        EXPECTED_MAGISK_AP_SHA256,
        EXPECTED_STOCK_BOOT_AP_SHA256,
        EXPECTED_STOCK_BOOT_RAW_SHA256,
        "S11P1 keeps the S9/S10C0/S11P0 isolated module recipe",
        "S11P1 always returns to Download after a bounded timed result delay",
        f"module_load_probe={M34_S11P1_MODULE_LOAD_PROBE}",
        "s11p1_timed_loader_result=1",
        "timed_download_beacon=1",
        "always_reboot_download=1",
        "download_delay_model=first_fail_index_or_proc_result",
        "phase=s11p1_timed_loader_result_probe",
        "predicate=timed_first_failure_or_proc_modules_result",
        "result_code=",
        "result=",
        "download_delay_sec=",
        "modules_open_or_read_fail",
        "cmd_db_not_attempted",
        "cmd_db_rc_fail",
        "first_module_failure",
        "proc_watchdog_missing",
        "watchdog_visible_cmd_db_proc_missing",
        "proc_watchdog_and_cmd_db_visible",
        *delay_values,
        "proc_modules=1",
        "direct_finit_rc=1",
        f"probe_module={M34_S10C0_PROBE_MODULE}",
        f"probe_proc_name={M34_S10C0_PROBE_PROC_NAME}",
        "positive_control=watchdog_proc_visible",
        "positive_control_proc_names=" + ",".join(M34_S11P0_POSITIVE_CONTROL_PROC_NAMES),
        "positive_control_modules=" + ",".join(M34_S11P0_POSITIVE_CONTROL_MODULES),
        "cmd_db_proc_seen=",
        "qcom_wdt_core_proc_seen=",
        "gh_virt_wdt_proc_seen=",
        "watchdog_proc_seen=",
        "cmd_db_seen=",
        "cmd_db_rc=",
        "modules_open_rc=",
        "modules_read_rc=",
        "attempted=",
        "ok=",
        "eexist=",
        "fail=",
        "first_fail_index=",
        "first_fail_rc=",
        "first_fail_name=",
        "both_graphs_closure=1",
        "devlink_supplier_closure=1",
        "substrate_load_set=waipio_devlink",
        "driver_load_only=1",
        "manual_power_write=0",
        f"module_count={EXPECTED_MODULE_COUNT}",
        "configfs_gadget=0",
        "udc_bind=0",
        "role_write_discriminator=0",
        "typec_readback=0",
        "reboot_request=download",
        "download_beacon=1",
        "true_action=timed_reboot_download",
        "false_action=timed_reboot_download",
        "download-beacon-hit-timed",
        "download-beacon-miss-manual-download-required",
        "no configfs gadget setup",
        "no UDC bind",
        "no TypeC role write",
        "no ssusb role write",
        "no Android/Magisk handoff",
        "no persistent partition mount",
        "no block write",
        "manual Download rollback is recovery-only",
    ]


def missing_policy_markers(text: str) -> list[str]:
    normalized = " ".join(text.split())
    return [marker for marker in policy_required_markers() if marker not in normalized]


def agents_exception_active_template() -> str:
    marker_lines = "\n".join(f"   `{marker}`" for marker in policy_required_markers())
    return f"""   **Narrow operator-authorized exception (2026-07-10, S22+ M34 S11P1 timed loader-result boot-only live gate):**
   After the M34 S11P1 host-build report pinned the exact artifact hashes and
   the operator provided live approval, Codex may run one bounded attended
   boot-partition-only M34 S11P1 live gate on the Samsung S22+
   `SM-S906N`/`g0q` `S906NKSS7FYG8` using only the checked helper
   `workspace/public/src/scripts/revalidation/s22plus_m34_s11p1_timed_loader_result_live_gate.py`.
   Live ack token: `{LIVE_ACK_TOKEN}`. Rollback ack token:
   `{ROLLBACK_ACK_TOKEN}`.

   The exact candidate AP.tar.md5 SHA256 must be
   `{EXPECTED_M34_AP_SHA256}`; contained padded `boot.img` SHA256 must be
   `{EXPECTED_M34_BOOT_SHA256}`; `boot.img.lz4` SHA256 must be
   `{EXPECTED_M34_BOOT_LZ4_SHA256}`; direct `/init` SHA256 must be
   `{EXPECTED_M34_INIT_SHA256}`; template source SHA256 must be
   `{EXPECTED_M34_TEMPLATE_SOURCE_SHA256}`; module-list SHA256 must be
   `{EXPECTED_M34_MODULE_LIST_SHA256}`; preserved kernel SHA256 must be
   `{EXPECTED_M34_KERNEL_SHA256}`; and known-booting base Magisk boot SHA256
   must be `{EXPECTED_M34_BASE_BOOT_SHA256}`. The AP must contain exactly one
   tar member, `boot.img.lz4`, and must not carry recovery, vendor_boot, dtbo,
   vbmeta, vbmeta_system, BL, CP, CSC, super, persist, userdata, EFS,
   sec_efs, RPMB, keymaster, modem, bootloader, or any other partition payload.
   Before live flash, the helper must verify the pinned Magisk boot-only
   rollback AP SHA256 `{EXPECTED_MAGISK_AP_SHA256}` and the S10C0-specific
   FYG8 stock boot-only fallback AP SHA256 `{EXPECTED_STOCK_BOOT_AP_SHA256}`
   generated from stock raw boot SHA256 `{EXPECTED_STOCK_BOOT_RAW_SHA256}`.

   The candidate is limited to freestanding direct PID1 M34 S11P1 behavior:
   `S22+ M34 S11P1 timed loader-result native-init boot-only`,
   `{EXPECTED_M34_MARKER}`, `S11P1 keeps the S9/S10C0/S11P0 isolated module
   recipe`, and `S11P1 always returns to Download after a bounded timed result
   delay`. It remains driver-load-only: `both_graphs_closure=1`,
   `devlink_supplier_closure=1`, `substrate_load_set=waipio_devlink`,
   `driver_load_only=1`, `manual_power_write=0`, `module_count=89`,
   `configfs_gadget=0`, `udc_bind=0`, `role_write_discriminator=0`, and
   `typec_readback=0`.

   S11P1 intentionally performs no downstream USB gadget work: no configfs
   gadget setup, no UDC bind, no TypeC role write, no ssusb role write, no
   FunctionFS, and no stock composite. Its observation is
   `s11p1_timed_loader_result=1`,
   `module_load_probe={M34_S11P1_MODULE_LOAD_PROBE}`,
   `predicate=timed_first_failure_or_proc_modules_result`,
   `phase=s11p1_timed_loader_result_probe`, `proc_modules=1`,
   `timed_download_beacon=1`, `always_reboot_download=1`,
   `download_delay_model=first_fail_index_or_proc_result`,
   `direct_finit_rc=1`, `probe_module={M34_S10C0_PROBE_MODULE}`,
   `probe_proc_name={M34_S10C0_PROBE_PROC_NAME}`,
   `positive_control=watchdog_proc_visible`,
   `positive_control_proc_names={','.join(M34_S11P0_POSITIVE_CONTROL_PROC_NAMES)}`,
   `positive_control_modules={','.join(M34_S11P0_POSITIVE_CONTROL_MODULES)}`,
   `result_code=`, `result=`, `download_delay_sec=`,
   `modules_open_rc=`, `modules_read_rc=`, `attempted=`, `ok=`, `eexist=`,
   `fail=`, `first_fail_index=`, `first_fail_rc=`, `first_fail_name=`,
   `cmd_db_seen=`, `cmd_db_rc=`, `cmd_db_proc_seen=`,
   `qcom_wdt_core_proc_seen=`, `gh_virt_wdt_proc_seen=`, and
   `watchdog_proc_seen=`.

   The timing contract is: `6` seconds for `modules_open_or_read_fail`, `12`
   seconds for `cmd_db_not_attempted`, `18` seconds for `cmd_db_rc_fail`,
   `20 + first_fail_index` seconds for `first_module_failure`, `116` seconds
   for `proc_watchdog_missing`, `122` seconds for
   `watchdog_visible_cmd_db_proc_missing`, and `128` seconds for
   `proc_watchdog_and_cmd_db_visible`. Both true and false paths record
   `true_action=timed_reboot_download` and
   `false_action=timed_reboot_download` semantics and request
   `reboot_request=download` with `download_beacon=1`. The host-visible result
   is `download-beacon-hit-timed`, where a new Odin Download endpoint appears
   after the original Download endpoint disconnects. If no new Download appears
   within the bounded observation window, the result is
   `download-beacon-miss-manual-download-required`; manual Download rollback is
   recovery-only.

   The candidate must have no Android/Magisk handoff, no persistent partition
   mount, no block write, no module binary injection into boot ramdisk, no raw
   host `dd`, no fastboot, no Magisk modules, no multidisabler, no format data,
   no DTBO/vendor_boot/recovery/vbmeta/non-boot flash, and no A90 action. It
   must not write charge current, OTG/VBUS boost, regulator, GDSC, GPIO,
   display, raw PMIC knobs, EUD sysfs, TypeC role nodes, configfs, UDC, or
   ssusb role nodes. PMIC/RDX abnormal reset before the observation window is
   FAIL. This exception does not authorize S11P0 repeat, S10C0 repeat, S10B
   repeat, B2/B3/B4, descriptor/composition pivots, FunctionFS/conn_gadget
   parity, display/distro candidates, kernel rebuilds, RDX PC dump retrieval,
   or any non-boot partition action.

   Required policy marker coverage:
{marker_lines}
"""


def has_exact_active_exception_template(text: str) -> bool:
    return " ".join(agents_exception_active_template().split()) in " ".join(text.split())


def verify_agents_text(agents: str, log_path: Path, *, source_label: str) -> None:
    missing = missing_policy_markers(agents)
    append_log(log_path, f"agents_exception_source={source_label}")
    append_log(log_path, f"agents_exception_missing={missing}")
    if missing:
        raise SystemExit(f"{source_label} missing M34 S11P1 authorization markers: {missing}")
    active_template_present = has_exact_active_exception_template(agents)
    append_log(log_path, f"agents_exception_exact_active_template_present={int(active_template_present)}")
    if not active_template_present:
        raise SystemExit(f"{source_label} marker coverage is present but exact M34 S11P1 active template is absent")


def verify_agents_exception(root: Path, log_path: Path) -> None:
    verify_agents_text((root / "AGENTS.md").read_text(encoding="utf-8"), log_path, source_label="AGENTS.md")


def agents_candidate_text(current_agents: str) -> str:
    template = agents_exception_active_template()
    if missing_policy_markers(template):
        raise SystemExit("internal S11P1 active template is missing policy markers")
    if has_exact_active_exception_template(current_agents):
        return current_agents
    if ACTIVE_EXCEPTION_INSERT_ANCHOR not in current_agents:
        raise SystemExit("source AGENTS missing S11P1 insertion anchor")
    return current_agents.replace(ACTIVE_EXCEPTION_INSERT_ANCHOR, template + "\n\n" + ACTIVE_EXCEPTION_INSERT_ANCHOR, 1)


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
    runtime_steps = stage.get("runtime_steps", {})
    init_info = stage.get("init", {})
    closure = stage.get("closure", {})
    ramdisk = stage.get("ramdisk", {})

    append_log(log_path, f"m34_manifest_path={path}")
    append_log(log_path, f"m34_s11p1_manifest_hashes={json.dumps(hashes, sort_keys=True)}")

    if data.get("target") != EXPECTED_TARGET:
        raise SystemExit(f"M34 target mismatch: {data.get('target')!r}")
    if data.get("hashes", {}).get("template_source") != EXPECTED_M34_TEMPLATE_SOURCE_SHA256:
        raise SystemExit("M34 template source hash mismatch")
    if data.get("hashes", {}).get("nochange_repack_boot") != EXPECTED_M34_BASE_BOOT_SHA256:
        raise SystemExit("M34 no-change MagiskBoot repack is not pinned to the known booting base")
    if data.get("magiskboot", {}).get("nochange_repack_byte_identical") is not True:
        raise SystemExit("M34 no-change MagiskBoot repack is not byte-identical")
    if matrix.get("next_host_only_candidate") != EXPECTED_STAGE:
        raise SystemExit(f"M34 next host-only candidate mismatch: {matrix.get('next_host_only_candidate')!r}")

    required_matrix = {
        "s11p1_module_load_probe": M34_S11P1_MODULE_LOAD_PROBE,
        "s11p1_probe_module": M34_S10C0_PROBE_MODULE,
        "s11p1_probe_proc_name": M34_S10C0_PROBE_PROC_NAME,
        "s11p1_positive_control_proc_names": M34_S11P0_POSITIVE_CONTROL_PROC_NAMES,
        "s11p1_positive_control_modules": M34_S11P0_POSITIVE_CONTROL_MODULES,
        "s11p1_true_action": "timed_reboot(download)",
        "s11p1_false_action": "timed_reboot(download)",
        "s11p1_always_reboots_download": True,
        "s11p1_timed_download_beacon": True,
        "s11p1_delay_model": M34_S11P1_DELAY_MODEL,
        "s11p1_maps_first_fail_index_to_module_list": True,
        "s11p1_starts_from_s10c0_module_recipe": True,
        "s11p1_uses_direct_finit_module_rc": True,
        "s11p1_skips_downstream_configfs_and_udc_to_isolate_module_load": True,
    }
    for key, expected in required_matrix.items():
        if matrix.get(key) != expected:
            raise SystemExit(f"M34 S11P1 matrix {key} mismatch: {matrix.get(key)!r} != {expected!r}")

    if stage.get("stage_number") != EXPECTED_STAGE_NUMBER:
        raise SystemExit(f"M34 S11P1 stage number mismatch: {stage.get('stage_number')!r}")
    if runtime_steps.get("module_load_probe") != M34_S11P1_MODULE_LOAD_PROBE:
        raise SystemExit(f"M34 S11P1 runtime module_load_probe mismatch: {runtime_steps!r}")

    required_hashes = {
        "ap_tar_md5": EXPECTED_M34_AP_SHA256,
        "boot_img": EXPECTED_M34_BOOT_SHA256,
        "boot_img_lz4": EXPECTED_M34_BOOT_LZ4_SHA256,
        "base_boot": EXPECTED_M34_BASE_BOOT_SHA256,
        "kernel": EXPECTED_M34_KERNEL_SHA256,
        "m34_init": EXPECTED_M34_INIT_SHA256,
        "m34_modules": EXPECTED_M34_MODULE_LIST_SHA256,
    }
    for key, expected in required_hashes.items():
        if hashes.get(key) != expected:
            raise SystemExit(f"M34 S11P1 manifest hash {key} mismatch: {hashes.get(key)!r} != {expected!r}")
    if stage.get("tar_members") != [EXPECTED_MEMBER]:
        raise SystemExit(f"M34 S11P1 tar members mismatch: {stage.get('tar_members')!r}")
    if closure.get("module_count") != EXPECTED_MODULE_COUNT:
        raise SystemExit(f"M34 S11P1 module count mismatch: {closure.get('module_count')!r}")
    for module in [M34_S10C0_PROBE_MODULE, *M34_S11P0_POSITIVE_CONTROL_MODULES]:
        if module not in closure.get("modules", []):
            raise SystemExit(f"M34 S11P1 closure missing module: {module}")
    if ramdisk.get("added_subset_entry") != EXPECTED_MODULE_ENTRY:
        raise SystemExit(f"M34 S11P1 module-list ramdisk entry mismatch: {ramdisk.get('added_subset_entry')!r}")
    if ramdisk.get("module_files_injected_into_boot_ramdisk") != 0:
        raise SystemExit("M34 S11P1 must not inject module binaries into boot ramdisk")

    required_safety = {
        "boot_only": True,
        "host_only_build": True,
        "live_flash_authorized": False,
        "requires_new_sha_pinned_agents_exception_before_flash": True,
        "base_is_known_booting_magisk_boot": True,
        "mkbootimg_from_scratch": False,
        "no_android_or_magisk_handoff": True,
        "auto_reboot": "download-if-probe-true-or-s11p1-timed-always",
        "intended_reboot_syscall": True,
        "reboot_request": "download-if-probe-true-or-s11p1-timed-always",
        "persistent_partition_mount": False,
        "block_device_writes": False,
        "module_binary_injection": False,
        "stage_s11p1_starts_from_s10c0_module_recipe": True,
        "stage_s11p1_module_load_probe": M34_S11P1_MODULE_LOAD_PROBE,
        "stage_s11p1_positive_control_proc_names": M34_S11P0_POSITIVE_CONTROL_PROC_NAMES,
        "stage_s11p1_true_timed_reboot_download_false_timed_reboot_download": True,
        "stage_s11p1_always_reboots_download_after_bounded_delay": True,
        "stage_s11p1_delay_model": M34_S11P1_DELAY_MODEL,
        "stage_s11p1_no_configfs_udc_or_role_write": True,
        "stage_s11p1_driver_load_only_no_manual_power_write": True,
    }
    for key, expected in required_safety.items():
        if safety.get(key) != expected:
            raise SystemExit(f"M34 S11P1 safety {key} mismatch: {safety.get(key)!r} != {expected!r}")

    required_strings = set(init_info.get("required_strings", []))
    for required in [
        EXPECTED_M34_MARKER,
        "version=0.13",
        "stage=S11P1",
        "runtime_step=S11P1",
        "module_count=89",
        "reboot_request=download",
        "download_beacon=1",
        "configfs_gadget=0",
        "udc_bind=0",
        "role_write_discriminator=0",
        "typec_readback=0",
        "devlink_supplier_closure=1",
        "both_graphs_closure=1",
        f"module_load_probe={M34_S11P1_MODULE_LOAD_PROBE}",
        "s11p1_timed_loader_result=1",
        "timed_download_beacon=1",
        "always_reboot_download=1",
        "download_delay_model=first_fail_index_or_proc_result",
        "proc_modules=1",
        "direct_finit_rc=1",
        f"probe_module={M34_S10C0_PROBE_MODULE}",
        f"probe_proc_name={M34_S10C0_PROBE_PROC_NAME}",
        "positive_control=watchdog_proc_visible",
        "positive_control_proc_names=qcom_wdt_core,gh_virt_wdt",
        "positive_control_modules=qcom_wdt_core.ko,gh_virt_wdt.ko",
        "phase=s11p1_timed_loader_result_probe",
        "predicate=timed_first_failure_or_proc_modules_result",
        "result_code=",
        "result=",
        "download_delay_sec=",
        "modules_open_or_read_fail",
        "cmd_db_not_attempted",
        "cmd_db_rc_fail",
        "first_module_failure",
        "proc_watchdog_missing",
        "watchdog_visible_cmd_db_proc_missing",
        "proc_watchdog_and_cmd_db_visible",
        "cmd_db_proc_seen=",
        "qcom_wdt_core_proc_seen=",
        "gh_virt_wdt_proc_seen=",
        "watchdog_proc_seen=",
        "true_action=timed_reboot_download",
        "false_action=timed_reboot_download",
        "phase=s11p1_timed_loader_result_reboot_returned",
        "/proc/modules",
    ]:
        if required not in required_strings:
            raise SystemExit(f"M34 S11P1 required string missing from manifest: {required}")


def verify_m34_artifacts(
    *,
    m34_ap: Path,
    m34_manifest: Path,
    magisk_rollback_ap: Path,
    stock_rollback_ap: Path,
    log_path: Path,
) -> None:
    verify_ap(m34_ap, EXPECTED_M34_AP_SHA256, "m34_s11p1_candidate", log_path)
    verify_m34_manifest(m34_manifest, log_path)
    verify_ap(magisk_rollback_ap, EXPECTED_MAGISK_AP_SHA256, "magisk_boot_rollback", log_path)
    verify_ap(stock_rollback_ap, EXPECTED_STOCK_BOOT_AP_SHA256, "stock_boot_fallback", log_path)


def observe_timed_download_beacon(
    *,
    run_dir: Path,
    log_path: Path,
    odin: Path,
    observe_sec: int,
    snapshot_interval_sec: float,
) -> tuple[str, str | None, float | None]:
    start = time.monotonic()
    deadline = start + observe_sec
    next_snapshot = 0.0
    while time.monotonic() < deadline:
        devices = odin_devices(odin, log_path, "candidate-timed-beacon-observe")
        if len(devices) > 1:
            raise SystemExit(f"refusing ambiguous Odin devices during S11P1 observation: {devices}")
        if len(devices) == 1:
            elapsed = time.monotonic() - start
            host_snapshot(run_dir, log_path, "candidate_timed_beacon_hit", odin)
            record_timeline_event(run_dir, "candidate_timed_download_ready")
            append_log(log_path, f"s11p1_result=download-beacon-hit-timed odin_device={devices[0]} elapsed_sec={elapsed:.3f}")
            return "download-beacon-hit-timed", devices[0], elapsed
        now = time.monotonic()
        if now >= next_snapshot:
            host_snapshot(run_dir, log_path, "candidate_timed_observe", odin)
            next_snapshot = now + snapshot_interval_sec
        time.sleep(1.0)
    append_log(log_path, "s11p1_result=download-beacon-miss-manual-download-required")
    return "download-beacon-miss-manual-download-required", None, None


def write_result_summary(
    run_dir: Path,
    log_path: Path,
    *,
    result: str,
    rc: int,
    rollback_target: str,
    rollback_device: str | None = None,
    android_serial: str | None = None,
    timed_elapsed_sec: float | None = None,
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
        "module_load_probe": M34_S11P1_MODULE_LOAD_PROBE,
        "delay_model": dict(M34_S11P1_DELAY_MODEL),
        "probe_module": M34_S10C0_PROBE_MODULE,
        "probe_proc_name": M34_S10C0_PROBE_PROC_NAME,
        "positive_control_proc_names": list(M34_S11P0_POSITIVE_CONTROL_PROC_NAMES),
    }
    if timed_elapsed_sec is not None:
        payload["candidate_timed_download_elapsed_sec"] = round(timed_elapsed_sec, 3)
        payload["timing_note"] = "elapsed starts after original Odin endpoint disappears; subtract kernel/native-init boot overhead before mapping to delay_model"
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


def print_only_mode(args: argparse.Namespace) -> bool:
    return (
        args.print_agents_exception_active_template
        or args.write_agents_candidate is not None
        or args.verify_agents_candidate is not None
    )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m34-ap", type=Path, default=DEFAULT_M34_AP)
    parser.add_argument("--m34-manifest", type=Path, default=DEFAULT_M34_MANIFEST)
    parser.add_argument("--magisk-rollback-ap", type=Path, default=DEFAULT_MAGISK_ROLLBACK_AP)
    parser.add_argument("--stock-rollback-ap", type=Path, default=DEFAULT_STOCK_ROLLBACK_AP)
    parser.add_argument("--odin", type=Path, default=DEFAULT_ODIN)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--serial")
    parser.add_argument("--observe-sec", type=int, default=180)
    parser.add_argument("--snapshot-interval-sec", type=float, default=5.0)
    parser.add_argument("--post-flash-disconnect-wait-sec", type=int, default=20)
    parser.add_argument("--manual-download-wait-sec", type=int, default=300)
    parser.add_argument("--odin-wait-sec", type=int, default=90)
    parser.add_argument("--android-wait-sec", type=int, default=240)
    parser.add_argument("--android-stability-samples", type=int, default=2)
    parser.add_argument("--android-stability-interval-sec", type=float, default=2.0)
    parser.add_argument("--rollback-target", choices=[ROLLBACK_MAGISK, ROLLBACK_STOCK], default=ROLLBACK_MAGISK)
    parser.add_argument("--offline-check", action="store_true")
    parser.add_argument("--print-agents-exception-active-template", action="store_true")
    parser.add_argument("--write-agents-candidate", type=Path)
    parser.add_argument("--verify-agents-candidate", type=Path)
    parser.add_argument("--rollback-from-download", action="store_true")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--ack")
    args = parser.parse_args(argv)

    modes = sum(
        1
        for enabled in (
            args.offline_check,
            args.print_agents_exception_active_template,
            args.write_agents_candidate is not None,
            args.verify_agents_candidate is not None,
            args.rollback_from_download,
            args.live,
        )
        if enabled
    )
    if modes > 1:
        raise SystemExit(
            "--offline-check, --print-agents-exception-active-template, "
            "--write-agents-candidate, --verify-agents-candidate, "
            "--rollback-from-download, and --live are mutually exclusive"
        )
    if args.observe_sec < 150:
        raise SystemExit("--observe-sec must be at least 150 for the M34 S11P1 timed download beacon")
    if args.snapshot_interval_sec < 1.0:
        raise SystemExit("--snapshot-interval-sec must be at least 1.0")

    root = repo_root()
    m34_ap = resolve(root, args.m34_ap)
    m34_manifest = resolve(root, args.m34_manifest)
    magisk_rollback_ap = resolve(root, args.magisk_rollback_ap)
    stock_rollback_ap = resolve(root, args.stock_rollback_ap)

    if print_only_mode(args):
        with tempfile.TemporaryDirectory(prefix="s22plus_m34_s11p1_print_") as tmp:
            log_path = Path(tmp) / "s22plus_m34_s11p1_timed_loader_result_live_gate.txt"
            append_log(log_path, f"=== {utc_now()} s22plus M34 S11P1 timed loader-result live gate ===")
            verify_m34_artifacts(
                m34_ap=m34_ap,
                m34_manifest=m34_manifest,
                magisk_rollback_ap=magisk_rollback_ap,
                stock_rollback_ap=stock_rollback_ap,
                log_path=log_path,
            )
            if args.print_agents_exception_active_template:
                print(agents_exception_active_template(), end="")
                return 0
            if args.write_agents_candidate is not None:
                candidate_path = resolve(root, args.write_agents_candidate)
                agents_path = (root / "AGENTS.md").resolve()
                if candidate_path == agents_path:
                    raise SystemExit("--write-agents-candidate refuses to write AGENTS.md directly")
                if candidate_path.exists():
                    raise SystemExit(f"AGENTS candidate already exists; refuse to overwrite: {candidate_path}")
                candidate = agents_candidate_text((root / "AGENTS.md").read_text(encoding="utf-8"))
                verify_agents_text(candidate, log_path, source_label=str(candidate_path))
                candidate_path.parent.mkdir(parents=True, exist_ok=True)
                candidate_path.write_text(candidate, encoding="utf-8")
                print(f"write-agents-candidate ok: exact M34 S11P1 active exception inserted; candidate={candidate_path}")
                return 0
            if args.verify_agents_candidate is not None:
                candidate_path = resolve(root, args.verify_agents_candidate)
                verify_agents_text(candidate_path.read_text(encoding="utf-8"), log_path, source_label=str(candidate_path))
                print(f"verify-agents-candidate ok: exact M34 S11P1 active exception is present; candidate={candidate_path}")
                return 0

    run_dir = resolve_run_dir(root, args.run_dir)
    log_path = run_dir / "s22plus_m34_s11p1_timed_loader_result_live_gate.txt"
    append_log(log_path, f"=== {utc_now()} s22plus M34 S11P1 timed loader-result live gate ===")

    verify_m34_artifacts(
        m34_ap=m34_ap,
        m34_manifest=m34_manifest,
        magisk_rollback_ap=magisk_rollback_ap,
        stock_rollback_ap=stock_rollback_ap,
        log_path=log_path,
    )
    if args.offline_check:
        append_log(log_path, "offline_check=ok device_action=0 agents_exception_checked=0 android_checked=0")
        print(f"offline-check ok: M34 S11P1 artifacts verified; no AGENTS/device action; log={log_path}")
        return 0

    odin = resolve(root, args.odin)
    if not odin.is_file():
        raise SystemExit(f"odin4 missing: {odin}")
    verify_agents_exception(root, log_path)

    if args.rollback_from_download:
        if args.ack != ROLLBACK_ACK_TOKEN:
            raise SystemExit(f"--rollback-from-download requires --ack {ROLLBACK_ACK_TOKEN}")
        devices = odin_devices(odin, log_path, "rollback-only")
        if len(devices) != 1:
            raise SystemExit(f"S11P1 rollback requires exactly one Odin device, got {devices}")
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
            result="rollback-only-no-s11p1-proof",
            rc=rollback.rc,
            rollback_target=rollback.rollback_target,
            rollback_device=rollback.rollback_device,
            android_serial=rollback.android_serial,
        )
        print(f"M34 S11P1 rollback-from-download completed rc={rollback.rc}; log={log_path}")
        return rollback.rc

    selected_serial = require_current_android(log_path, args.serial)
    verify_android_stability(log_path, selected_serial, args.android_stability_samples, args.android_stability_interval_sec)
    verify_partition_hash(log_path, selected_serial, "boot", EXPECTED_M34_BASE_BOOT_SHA256, "current")
    host_snapshot(run_dir, log_path, "dryrun_current", odin)

    if not args.live:
        print(f"dry-run ok: M34 S11P1 candidate, rollback APs, AGENTS exception, Android, and boot hash verified; log={log_path}")
        return 0
    if args.ack != LIVE_ACK_TOKEN:
        raise SystemExit(f"--live requires --ack {LIVE_ACK_TOKEN}")

    record_timeline_event(run_dir, "live_session_start")
    print("M34 S11P1 live gate starting. Candidate should re-enter Download mode after its timed result delay.", flush=True)
    reboot = run(["adb", "-s", selected_serial, "reboot", "download"], timeout=20.0)
    append_log(log_path, f"adb_reboot_download_rc={reboot.returncode}")
    append_log(log_path, reboot.stdout + reboot.stderr)
    odin_device = wait_for_odin(odin, log_path, "candidate-wait", args.odin_wait_sec)
    if odin_device is None:
        record_timeline_event(run_dir, "live_session_end")
        write_result_summary(run_dir, log_path, result="candidate-download-mode-missing", rc=2, rollback_target=args.rollback_target)
        print("download mode did not appear for M34 S11P1 candidate flash", file=sys.stderr)
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
    print(f"M34 S11P1 candidate flashed. Observing timed download beacon for {args.observe_sec}s.", flush=True)
    result, rollback_device, elapsed = observe_timed_download_beacon(
        run_dir=run_dir,
        log_path=log_path,
        odin=odin,
        observe_sec=args.observe_sec,
        snapshot_interval_sec=args.snapshot_interval_sec,
    )

    if result == "download-beacon-hit-timed":
        if rollback_device is None:
            record_timeline_event(run_dir, "live_session_end")
            write_result_summary(run_dir, log_path, result=result, rc=4, rollback_target=args.rollback_target, timed_elapsed_sec=elapsed)
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
            label="timed_beacon_hit",
        )
        record_timeline_event(run_dir, "live_session_end")
        write_result_summary(run_dir, log_path, result=result, rc=rollback.rc, rollback_target=rollback.rollback_target, rollback_device=rollback.rollback_device, android_serial=rollback.android_serial, timed_elapsed_sec=elapsed)
        print(f"M34 S11P1 live gate completed rc={rollback.rc}; result={result}; elapsed_sec={elapsed:.3f}; log={log_path}")
        return rollback.rc

    print(f"M34 S11P1 result={result}. Enter Download mode manually for rollback now; waiting up to {args.manual_download_wait_sec}s.", flush=True)
    rollback_device = wait_for_odin(odin, log_path, "manual-rollback-wait", args.manual_download_wait_sec)
    if rollback_device is None:
        record_timeline_event(run_dir, "live_session_end")
        write_result_summary(run_dir, log_path, result=result, rc=4, rollback_target=args.rollback_target, note="manual Download rollback did not appear within bounded wait")
        print(f"M34 S11P1 MISS observed, but manual Download mode did not appear. Run --rollback-from-download after entering Download mode. log={log_path}", file=sys.stderr)
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
    print(f"M34 S11P1 live gate completed rc={rollback.rc}; result={result}; log={log_path}")
    return rollback.rc


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
