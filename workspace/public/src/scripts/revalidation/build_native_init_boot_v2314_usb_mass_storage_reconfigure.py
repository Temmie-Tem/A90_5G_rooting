#!/usr/bin/env python3
"""Build V2314 USB mass-storage reconfigure test boot.

This wrapper builds on V2313 and adds the guarded `usb mass-storage add/remove`
commands for U2 atomic auxiliary-function reconfiguration.
"""

from __future__ import annotations

import json

from _workspace_bootstrap import add_legacy_revalidation_path, repo_root

REPO_ROOT = repo_root()
add_legacy_revalidation_path(REPO_ROOT)

import build_native_init_boot_v2313_usb_status_inventory as v2313
from a90harness.evidence import workspace_private_build_path, workspace_private_input_path


OUT_DIR = workspace_private_build_path("native-init", "v2314-usb-ms-reconfigure")
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V2314_USB_MASS_STORAGE_RECONFIGURE_SOURCE_BUILD_2026-06-13.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images", "boot_linux_v2314_usb_ms_reconfigure.img", legacy_fallback=False
)
INIT_BINARY = OUT_DIR / "init_v2314_usb_ms_reconfigure"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v2314_usb_ms_reconfigure.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v433_usb_ms_reconfigure"
REMOTE_PROPERTY_ROOT = v2313.REMOTE_PROPERTY_ROOT
EXPECTED_HELPER_MARKER = v2313.EXPECTED_HELPER_MARKER
EXPECTED_HELPER_SHA256 = v2313.EXPECTED_HELPER_SHA256
EXTRA_INIT_FLAGS = v2313.EXTRA_INIT_FLAGS


def base_module():
    return v2313.base_module()


def helper_builder_module():
    return v2313.helper_builder_module()


def set_arg(args: list[str], key: str, value: str) -> None:
    index = args.index(key)
    args[index + 1] = value


def configure_base() -> tuple[str, ...]:
    v2313.OUT_DIR = OUT_DIR
    v2313.REPORT_PATH = REPORT_PATH
    v2313.BOOT_IMAGE = BOOT_IMAGE
    v2313.INIT_BINARY = INIT_BINARY
    v2313.RAMDISK_CPIO = RAMDISK_CPIO
    v2313.REMOTE_PROPERTY_ROOT = REMOTE_PROPERTY_ROOT
    helper_flags = v2313.configure_base()

    base = base_module()
    args = list(base.DEFAULT_ARGS)
    replacements = {
        "--cycle": "V2314",
        "--decision": "v2314-usb-ms-reconfigure-source-build-pass",
        "--cycle-label": "v2314",
        "--init-version": "0.9.278",
        "--init-build": "v2314-usb-ms-reconfigure",
        "--out-dir": str(OUT_DIR),
        "--init-binary": str(INIT_BINARY),
        "--helper-binary": str(HELPER_BINARY),
        "--ramdisk-cpio": str(RAMDISK_CPIO),
        "--boot-image": str(BOOT_IMAGE),
        "--wifi-test-klog-prefix": "A90v2314",
        "--wifi-test-disable": "/cache/native-init-wifi-test-boot-v2314.disable",
        "--wifi-test-log": "/cache/native-init-wifi-test-boot-v2314.log",
        "--wifi-test-summary": "/cache/native-init-wifi-test-boot-v2314.summary",
        "--wifi-test-helper-result": "/cache/native-init-wifi-test-boot-v2314-helper.result",
        "--wifi-test-pid": "/cache/native-init-wifi-test-boot-v2314.pid",
        "--wifi-test-watcher-pid": "/cache/native-init-wifi-test-boot-v2314-supervisor.pid",
        "--wifi-test-property-root": REMOTE_PROPERTY_ROOT,
    }
    for key, value in replacements.items():
        set_arg(args, key, value)
    base.DEFAULT_ARGS = args
    base.base.EXTRA_INIT_FLAGS = EXTRA_INIT_FLAGS
    return helper_flags


def render_report(manifest: dict[str, object], helper_flags: tuple[str, ...]) -> str:
    wifi = manifest["wifi_test"]
    helper_flag_lines = [f"- `{flag}`" for flag in helper_flags]
    return "\n".join([
        "# Native Init V2314 USB Mass Storage Reconfigure Source Build",
        "",
        "## Summary",
        "",
        "- Cycle: `V2314`",
        "- Track: active USB gadget runtime-control epic layer 1, U2 atomic auxiliary-function add/remove.",
        "- Type: source/build-only rollbackable native-init test boot.",
        f"- Decision: `{manifest['decision']}`",
        "- Result: PASS",
        "- Reason: U2 must add/remove an auxiliary `mass_storage.0` function without ever shipping a config that lacks NCM plus control ACM.",
        "- Manifest: `workspace/private/builds/native-init/v2314-usb-ms-reconfigure/manifest.json`",
        f"- Boot image: `{manifest['boot_image']}`",
        f"- Boot SHA256: `{manifest['boot_sha256']}`",
        f"- Init: `A90 Linux init {manifest['init_version']} ({manifest['init_build']})`",
        f"- Helper marker: `a90_android_execns_probe helper-v427` (binary marker string: `{manifest['helper_marker']}`)",
        f"- Helper SHA256: `{manifest['helper_sha256']}`",
        "",
        "## Command Scope",
        "",
        "- Keeps `usb [status]` and adds `usb mass-storage add` / `usb mass-storage remove`.",
        "- The mass-storage commands preflight that the live gadget is already bound with `acm.usb0` on `f1` and `ncm.usb0` on `f2`.",
        "- They schedule a detached device-side worker so the command can return before the expected USB disconnect.",
        "- The worker performs one atomic unbind -> reconfigure -> rebind cycle and always preserves `acm.usb0` plus `ncm.usb0`.",
        "- A separate watchdog process restores the known-good control-only gadget if the worker does not mark completion within the bounded window.",
        "- `mass_storage.0` is configured as a removable no-media LUN; no backing file is exposed in U2.",
        "",
        "## Route",
        "",
        f"- Helper runtime mode: `{wifi['helper_runtime_mode']}`",
        f"- Helper timeout: `{wifi['helper_timeout_sec']}`",
        f"- Property root: `{REMOTE_PROPERTY_ROOT}`",
        "- Parent test artifact: `v2313-usb-status-inventory`.",
        "- Rollback checkpoint remains: `v2237-supplicant-terminate-poll`.",
        "",
        "## Helper Flags",
        "",
        *helper_flag_lines,
        "",
        "## Safety Scope",
        "",
        "This source build performed host-side build work only. Runtime mutation is limited to the new U2 commands and is guarded by preflight, detached worker, watchdog restore, and mandatory NCM+ACM preservation. It does not expose a backing file, run Wi-Fi scan/connect/DHCP/ping, touch forbidden partitions, or start adb-over-ffs/HID/BadUSB work.",
        "",
        "## Required Device Step",
        "",
        "- Boot-only flash through `native_init_flash.py`.",
        "- `version` / `status` / `selftest fail=0`.",
        "- Run `usb status` over the serial bridge and verify `control.ok=1` before mutation.",
        "- Run `usb mass-storage add`; reconnect through the serial bridge after the expected USB drop and verify `usb status` shows `mass_storage.0` linked as an aux function while `control.ok=1` remains true.",
        "- Run `usb mass-storage remove`; reconnect again and verify `control.ok=1` and no active mass-storage config link.",
        "- Host-side enumeration is parked as an operator checkpoint for U2/U3; the automated pass criterion is serial control return plus topology state.",
        "",
    ])


def main() -> int:
    helper_flags = configure_base()
    helper_builder = helper_builder_module()
    helper_builder.EXPECTED_HELPER_MARKER = EXPECTED_HELPER_MARKER
    helper_builder.EXPECTED_HELPER_SHA256 = EXPECTED_HELPER_SHA256
    base = base_module()
    base.base.EXPECTED_HELPER_MARKER = EXPECTED_HELPER_MARKER
    base.base.EXPECTED_HELPER_SHA256 = EXPECTED_HELPER_SHA256
    helper_builder.patch_helper_builder(base)
    v2313.v2312.v2311.v2310.v2309.v2237.patch_mkbootimg_tools(base)
    base.render_report = lambda manifest: render_report(manifest, helper_flags)
    rc = base.main()
    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["candidate_tag"] = "v2314-usb-ms-reconfigure"
    manifest["parent_baseline"] = "v2313-usb-status-inventory"
    manifest["rollback_baseline"] = "v2237-supplicant-terminate-poll"
    manifest["helper_flags"] = list(helper_flags)
    manifest["usb_mass_storage_reconfigure"] = {
        "commands": ["usb mass-storage add", "usb mass-storage remove", "usb status"],
        "version": "a90-native-usb-status-v1",
        "auxiliary_function": "mass_storage.0",
        "auxiliary_link": "configs/b.1/f3",
        "backing_file_required": False,
        "control_required": ["control-acm", "control-ncm"],
        "watchdog_sec": 8,
        "mutation_attempted_at_build": False,
        "host_enumeration_parked": True,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    promotion_path = OUT_DIR / "promotion-candidate.json"
    promotion_path.write_text(json.dumps({
        "candidate_tag": "v2314-usb-ms-reconfigure",
        "boot_image": str(BOOT_IMAGE.relative_to(REPO_ROOT)),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "helper_sha256": manifest["helper_sha256"],
        "source_report": str(REPORT_PATH.relative_to(REPO_ROOT)),
        "note": "V2314 adds guarded U2 mass_storage.0 add/remove reconfiguration commands.",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
