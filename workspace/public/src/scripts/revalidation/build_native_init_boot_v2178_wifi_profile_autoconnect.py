#!/usr/bin/env python3
"""Build the V2178 Wi-Fi profile/autoconnect test image."""

from __future__ import annotations

import json

from _workspace_bootstrap import add_legacy_revalidation_path, repo_root

REPO_ROOT = repo_root()
add_legacy_revalidation_path(REPO_ROOT)

import build_native_init_boot_v2176_wifi_dhcp as v2176
from a90harness.evidence import workspace_private_build_path, workspace_private_input_path


OUT_DIR = workspace_private_build_path("native-init", "v2178-wifi-profile-autoconnect-test-boot")
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V2178_WIFI_PROFILE_AUTOCONNECT_SOURCE_BUILD_2026-06-09.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images", "boot_linux_v2178_wifi_profile_autoconnect.img", legacy_fallback=False
)
INIT_BINARY = OUT_DIR / "init_v2178_wifi_profile_autoconnect"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v2178_wifi_profile_autoconnect.cpio"
REMOTE_PROPERTY_ROOT = v2176.REMOTE_PROPERTY_ROOT
EXPECTED_HELPER_MARKER = v2176.EXPECTED_HELPER_MARKER
EXPECTED_HELPER_SHA256 = v2176.EXPECTED_HELPER_SHA256
EXTRA_INIT_FLAGS = v2176.EXTRA_INIT_FLAGS


def base_module():
    return v2176.base_module()


def configure_base() -> None:
    v2176.OUT_DIR = OUT_DIR
    v2176.REPORT_PATH = REPORT_PATH
    v2176.BOOT_IMAGE = BOOT_IMAGE
    v2176.INIT_BINARY = INIT_BINARY
    v2176.RAMDISK_CPIO = RAMDISK_CPIO
    v2176.configure_base()

    base = base_module()
    args = list(base.DEFAULT_ARGS)
    replacements = {
        "--cycle": "V2178",
        "--decision": "v2178-wifi-profile-autoconnect-source-build-pass",
        "--cycle-label": "v2178",
        "--init-version": "0.9.253",
        "--init-build": "v2178-wifi-profile-autoconnect",
        "--out-dir": str(OUT_DIR),
        "--init-binary": str(INIT_BINARY),
        "--helper-binary": str(OUT_DIR / "a90_android_execns_probe_v427_wifi_profile_autoconnect"),
        "--ramdisk-cpio": str(RAMDISK_CPIO),
        "--boot-image": str(BOOT_IMAGE),
        "--wifi-test-klog-prefix": "A90v2178",
        "--wifi-test-disable": "/cache/native-init-wifi-test-boot-v2178.disable",
        "--wifi-test-log": "/cache/native-init-wifi-test-boot-v2178.log",
        "--wifi-test-summary": "/cache/native-init-wifi-test-boot-v2178.summary",
        "--wifi-test-helper-result": "/cache/native-init-wifi-test-boot-v2178-helper.result",
        "--wifi-test-pid": "/cache/native-init-wifi-test-boot-v2178.pid",
        "--wifi-test-watcher-pid": "/cache/native-init-wifi-test-boot-v2178-supervisor.pid",
        "--wifi-test-property-root": REMOTE_PROPERTY_ROOT,
    }
    for key, value in replacements.items():
        v2176.v2174.v2169.v726.set_arg(args, key, value)
    base.DEFAULT_ARGS = args
    base.base.EXTRA_INIT_FLAGS = EXTRA_INIT_FLAGS


def render_report(manifest: dict[str, object]) -> str:
    wifi = manifest["wifi_test"]
    return "\n".join([
        "# Native Init V2178 Wi-Fi Profile Autoconnect Source Build",
        "",
        "## Summary",
        "",
        "- Candidate tag: `v2178-wifi-profile-autoconnect`",
        "- Parent test route: `v2176-wifi-dhcp`",
        "- Current rollback baseline: `v2174-wifi-urandom-connect`",
        "- Type: source/build-only test boot candidate.",
        f"- Decision: `{manifest['decision']}`",
        "- Result: PASS",
        "- Reason: V2178 keeps the V2176 Wi-Fi connect/DHCP/cleanup route and adds profile inventory plus explicit autoconnect controls.",
        "- Manifest: `workspace/private/builds/native-init/v2178-wifi-profile-autoconnect-test-boot/manifest.json`",
        f"- Base boot: `{manifest['base_boot']}`",
        f"- Boot image: `{manifest['boot_image']}`",
        f"- Boot SHA256: `{manifest['boot_sha256']}`",
        f"- Init: `A90 Linux init {manifest['init_version']} ({manifest['init_build']})`",
        f"- Helper marker: `a90_android_execns_probe helper-v427` (binary marker string: `{manifest['helper_marker']}`)",
        f"- Helper SHA256: `{manifest['helper_sha256']}`",
        "",
        "## Included Route",
        "",
        f"- Helper runtime mode: `{wifi['helper_runtime_mode']}`",
        f"- Helper timeout: `{wifi['helper_timeout_sec']}`",
        f"- Property root: `{REMOTE_PROPERTY_ROOT}`",
        "- Preserved from V2176: `wifi connect [profile]`, `wifi dhcp [profile]`, `wifi cleanup`, standalone `wpa_supplicant`, V726 Wi-Fi lifecycle route, and `transport.contract=1` status fields.",
        "- Added: `wifi profile list` and `wifi profile status [profile]` for redacted profile inventory and validation.",
        "- Added: `wifi autoconnect status|enable [profile]|disable|once [profile]` with explicit opt-in config and no boot external ping.",
        "- Added: boot-background autoconnect worker that returns immediately when disabled and stays off unless `autoconnect=1` is staged.",
        "",
        "## Safety Scope",
        "",
        "- Raw SSID/PSK still live only in private config/secret files and generated runtime supplicant config.",
        "- Boot autoconnect is disabled by default and does not run external ping.",
        "- No `/dev/subsys_esoc0`, forced RC1/case, PMIC/GPIO/GDSC/regulator write, PCI rescan, platform bind/unbind, fake ONLINE, or eSoC notify/BOOT_DONE path is included.",
        "",
    ])


def normalize_manifest_axes() -> None:
    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["candidate_tag"] = "v2178-wifi-profile-autoconnect"
    manifest["parent_test_route"] = "v2176-wifi-dhcp"
    manifest["rollback_baseline"] = "v2174-wifi-urandom-connect"
    manifest["version_axes"] = {
        "candidate_tag": "v2178-wifi-profile-autoconnect",
        "parent_test_route": "v2176-wifi-dhcp",
        "rollback_baseline": "v2174-wifi-urandom-connect",
        "helper_version": "helper-v427",
        "run_id": "V2178",
        "note": "V2178 is a test-boot candidate for profile/autoconnect, not a promoted baseline.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def main() -> int:
    configure_base()
    base = base_module()
    helper_builder = (
        v2176.v2174.v2169.v726.v2168.prev2137.prev2135.prev2133.prev2131.prev2129
        .prev2127.prev2120.prev2112.prev2108.prev2106.prev2102.prev2100
        .prev2097.prev2095.prev2082.prev2080.prev2058.prev2038
    )
    helper_builder.patch_helper_builder(base)
    base.render_report = render_report
    created_legacy_link = v2176.v2174.v2169.ensure_legacy_mkbootimg_link()
    try:
        rc = base.main()
        if rc == 0:
            normalize_manifest_axes()
            REPORT_PATH.chmod(0o644)
        return rc
    finally:
        if created_legacy_link and v2176.v2174.v2169.LEGACY_MKBOOTIMG_DIR.is_symlink():
            v2176.v2174.v2169.LEGACY_MKBOOTIMG_DIR.unlink()


if __name__ == "__main__":
    raise SystemExit(main())
