#!/usr/bin/env python3
"""Build V2315 USB mass-storage persona test boot.

This wrapper builds on V2314 and adds the U3 `usb mass-storage expose` persona
command with a bounded read-only backing file.
"""

from __future__ import annotations

import json

from _workspace_bootstrap import add_legacy_revalidation_path, repo_root

REPO_ROOT = repo_root()
add_legacy_revalidation_path(REPO_ROOT)

import build_native_init_boot_v2314_usb_mass_storage_reconfigure as v2314
from a90harness.evidence import workspace_private_build_path, workspace_private_input_path


OUT_DIR = workspace_private_build_path("native-init", "v2315-usb-ms-persona")
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V2315_USB_MASS_STORAGE_PERSONA_SOURCE_BUILD_2026-06-13.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images", "boot_linux_v2315_usb_ms_persona.img", legacy_fallback=False
)
INIT_BINARY = OUT_DIR / "init_v2315_usb_ms_persona"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v2315_usb_ms_persona.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v434_usb_ms_persona"
REMOTE_PROPERTY_ROOT = v2314.REMOTE_PROPERTY_ROOT
EXPECTED_HELPER_MARKER = v2314.EXPECTED_HELPER_MARKER
EXPECTED_HELPER_SHA256 = v2314.EXPECTED_HELPER_SHA256
EXTRA_INIT_FLAGS = v2314.EXTRA_INIT_FLAGS
BACKING_PATH = "/cache/a90-usb-mass-storage-v2315.img"
BACKING_BYTES = 8 * 1024 * 1024


def base_module():
    return v2314.base_module()


def helper_builder_module():
    return v2314.helper_builder_module()


def set_arg(args: list[str], key: str, value: str) -> None:
    index = args.index(key)
    args[index + 1] = value


def configure_base() -> tuple[str, ...]:
    v2314.OUT_DIR = OUT_DIR
    v2314.REPORT_PATH = REPORT_PATH
    v2314.BOOT_IMAGE = BOOT_IMAGE
    v2314.INIT_BINARY = INIT_BINARY
    v2314.RAMDISK_CPIO = RAMDISK_CPIO
    v2314.REMOTE_PROPERTY_ROOT = REMOTE_PROPERTY_ROOT
    helper_flags = v2314.configure_base()

    base = base_module()
    args = list(base.DEFAULT_ARGS)
    replacements = {
        "--cycle": "V2315",
        "--decision": "v2315-usb-ms-persona-source-build-pass",
        "--cycle-label": "v2315",
        "--init-version": "0.9.279",
        "--init-build": "v2315-usb-ms-persona",
        "--out-dir": str(OUT_DIR),
        "--init-binary": str(INIT_BINARY),
        "--helper-binary": str(HELPER_BINARY),
        "--ramdisk-cpio": str(RAMDISK_CPIO),
        "--boot-image": str(BOOT_IMAGE),
        "--wifi-test-klog-prefix": "A90v2315",
        "--wifi-test-disable": "/cache/native-init-wifi-test-boot-v2315.disable",
        "--wifi-test-log": "/cache/native-init-wifi-test-boot-v2315.log",
        "--wifi-test-summary": "/cache/native-init-wifi-test-boot-v2315.summary",
        "--wifi-test-helper-result": "/cache/native-init-wifi-test-boot-v2315-helper.result",
        "--wifi-test-pid": "/cache/native-init-wifi-test-boot-v2315.pid",
        "--wifi-test-watcher-pid": "/cache/native-init-wifi-test-boot-v2315-supervisor.pid",
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
        "# Native Init V2315 USB Mass Storage Persona Source Build",
        "",
        "## Summary",
        "",
        "- Cycle: `V2315`",
        "- Track: active USB gadget runtime-control epic layer 1, U3 first persona end-to-end.",
        "- Type: source/build-only rollbackable native-init test boot.",
        f"- Decision: `{manifest['decision']}`",
        "- Result: PASS",
        "- Reason: U3 needs a bounded mass-storage persona with an explicit read-only backing file and control-return validation.",
        "- Manifest: `workspace/private/builds/native-init/v2315-usb-ms-persona/manifest.json`",
        f"- Boot image: `{manifest['boot_image']}`",
        f"- Boot SHA256: `{manifest['boot_sha256']}`",
        f"- Init: `A90 Linux init {manifest['init_version']} ({manifest['init_build']})`",
        f"- Helper marker: `a90_android_execns_probe helper-v427` (binary marker string: `{manifest['helper_marker']}`)",
        f"- Helper SHA256: `{manifest['helper_sha256']}`",
        "",
        "## Command Scope",
        "",
        "- Keeps `usb status`, `usb mass-storage add`, and `usb mass-storage remove`.",
        "- Adds `usb mass-storage expose`, which creates a bounded read-only backing image under `/cache` and exposes it through `mass_storage.0`.",
        "- The backing image is 8 MiB, contains a visible V2315 marker at offset 0, and is configured read-only before the LUN file is opened.",
        "- `usb mass-storage remove` now also clears the LUN file attribute while the gadget is unbound, returning the function to no-medium state.",
        "- Reconfigure still uses the V2314 detached worker, NCM+ACM preservation, watchdog, and known-good restore path.",
        "",
        "## Route",
        "",
        f"- Helper runtime mode: `{wifi['helper_runtime_mode']}`",
        f"- Helper timeout: `{wifi['helper_timeout_sec']}`",
        f"- Property root: `{REMOTE_PROPERTY_ROOT}`",
        "- Parent test artifact: `v2314-usb-ms-reconfigure`.",
        "- Rollback checkpoint remains: `v2237-supplicant-terminate-poll`.",
        "",
        "## Helper Flags",
        "",
        *helper_flag_lines,
        "",
        "## Safety Scope",
        "",
        "This source build performed host-side build work only. Runtime mutation is limited to the U3 mass-storage persona command and the existing guarded add/remove path. The persona uses a generated read-only `/cache` file only; it does not touch partitions, credentials, Wi-Fi scan/connect/DHCP/ping, adb-over-ffs, HID, or BadUSB.",
        "",
        "## Required Device Step",
        "",
        "- Boot-only flash through `native_init_flash.py`.",
        "- `version` / `status` / `selftest fail=0`.",
        "- Run `usb status` over the serial bridge and verify `control.ok=1` before mutation.",
        "- Run `usb mass-storage expose`; reconnect through the serial bridge after the expected USB drop and verify `mass_storage.0` is linked, `mass_storage.file.present=1`, the backing path is `/cache/a90-usb-mass-storage-v2315.img`, `ro=1`, and `control.ok=1`.",
        "- Host-side enumeration is required for full U3 persona validation and remains an operator parked checkpoint if not available in the automated run.",
        "- Run `usb mass-storage remove`; reconnect and verify `control.ok=1`, no active mass-storage config link, and `mass_storage.file.present=0`.",
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
    v2314.v2313.v2312.v2311.v2310.v2309.v2237.patch_mkbootimg_tools(base)
    base.render_report = lambda manifest: render_report(manifest, helper_flags)
    rc = base.main()
    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["candidate_tag"] = "v2315-usb-ms-persona"
    manifest["parent_baseline"] = "v2314-usb-ms-reconfigure"
    manifest["rollback_baseline"] = "v2237-supplicant-terminate-poll"
    manifest["helper_flags"] = list(helper_flags)
    manifest["usb_mass_storage_persona"] = {
        "commands": ["usb mass-storage expose", "usb mass-storage remove", "usb status"],
        "version": "a90-native-usb-status-v1",
        "auxiliary_function": "mass_storage.0",
        "auxiliary_link": "configs/b.1/f3",
        "backing_file": BACKING_PATH,
        "backing_bytes": BACKING_BYTES,
        "read_only": True,
        "control_required": ["control-acm", "control-ncm"],
        "watchdog_sec": 8,
        "host_enumeration_parked": True,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    promotion_path = OUT_DIR / "promotion-candidate.json"
    promotion_path.write_text(json.dumps({
        "candidate_tag": "v2315-usb-ms-persona",
        "boot_image": str(BOOT_IMAGE.relative_to(REPO_ROOT)),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "helper_sha256": manifest["helper_sha256"],
        "source_report": str(REPORT_PATH.relative_to(REPO_ROOT)),
        "note": "V2315 adds the U3 read-only mass-storage persona command.",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
