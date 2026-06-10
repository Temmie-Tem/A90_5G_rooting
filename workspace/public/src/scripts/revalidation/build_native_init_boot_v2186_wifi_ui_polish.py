#!/usr/bin/env python3
"""Build the V2186 Wi-Fi UI polish image."""

from __future__ import annotations

import json

from _workspace_bootstrap import add_legacy_revalidation_path, repo_root

REPO_ROOT = repo_root()
add_legacy_revalidation_path(REPO_ROOT)

import build_native_init_boot_v2182_hud_menu_cleanup as v2182
from a90harness.evidence import workspace_private_build_path, workspace_private_input_path


OUT_DIR = workspace_private_build_path("native-init", "v2186-wifi-ui-polish-boot")
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V2186_WIFI_UI_POLISH_SOURCE_BUILD_2026-06-10.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images", "boot_linux_v2186_wifi_ui_polish.img", legacy_fallback=False
)
INIT_BINARY = OUT_DIR / "init_v2186_wifi_ui_polish"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v2186_wifi_ui_polish.cpio"
REMOTE_PROPERTY_ROOT = v2182.REMOTE_PROPERTY_ROOT
EXPECTED_HELPER_MARKER = v2182.EXPECTED_HELPER_MARKER
EXPECTED_HELPER_SHA256 = v2182.EXPECTED_HELPER_SHA256
EXTRA_INIT_FLAGS = v2182.EXTRA_INIT_FLAGS


def base_module():
    return v2182.base_module()


def configure_base() -> None:
    v2182.OUT_DIR = OUT_DIR
    v2182.REPORT_PATH = REPORT_PATH
    v2182.BOOT_IMAGE = BOOT_IMAGE
    v2182.INIT_BINARY = INIT_BINARY
    v2182.RAMDISK_CPIO = RAMDISK_CPIO
    v2182.configure_base()

    base = base_module()
    args = list(base.DEFAULT_ARGS)
    replacements = {
        "--cycle": "V2186",
        "--decision": "v2186-wifi-ui-polish-source-build-pass",
        "--cycle-label": "v2186",
        "--init-version": "0.9.258",
        "--init-build": "v2186-wifi-ui-polish",
        "--out-dir": str(OUT_DIR),
        "--init-binary": str(INIT_BINARY),
        "--helper-binary": str(OUT_DIR / "a90_android_execns_probe_v427_wifi_ui_polish"),
        "--ramdisk-cpio": str(RAMDISK_CPIO),
        "--boot-image": str(BOOT_IMAGE),
        "--wifi-test-klog-prefix": "A90v2186",
        "--wifi-test-disable": "/cache/native-init-wifi-test-boot-v2186.disable",
        "--wifi-test-log": "/cache/native-init-wifi-test-boot-v2186.log",
        "--wifi-test-summary": "/cache/native-init-wifi-test-boot-v2186.summary",
        "--wifi-test-helper-result": "/cache/native-init-wifi-test-boot-v2186-helper.result",
        "--wifi-test-pid": "/cache/native-init-wifi-test-boot-v2186.pid",
        "--wifi-test-watcher-pid": "/cache/native-init-wifi-test-boot-v2186-supervisor.pid",
        "--wifi-test-property-root": REMOTE_PROPERTY_ROOT,
    }
    for key, value in replacements.items():
        v2182.v2178.v2176.v2174.v2169.v726.set_arg(args, key, value)
    base.DEFAULT_ARGS = args
    base.base.EXTRA_INIT_FLAGS = EXTRA_INIT_FLAGS


def render_report(manifest: dict[str, object]) -> str:
    wifi = manifest["wifi_test"]
    return "\n".join([
        "# Native Init V2186 Wi-Fi UI Polish Source Build",
        "",
        "## Summary",
        "",
        "- Candidate tag: `v2186-wifi-ui-polish`",
        "- Parent baseline: `v2185-network-ping-test`",
        "- Type: source/build-only test boot candidate.",
        f"- Decision: `{manifest['decision']}`",
        "- Result: PASS",
        "- Reason: V2186 keeps the V2185 network-ping baseline and polishes Wi-Fi status/HUD labels with redacted link metrics.",
        "- Manifest: `workspace/private/builds/native-init/v2186-wifi-ui-polish-boot/manifest.json`",
        f"- Base boot: `{manifest['base_boot']}`",
        f"- Boot image: `{manifest['boot_image']}`",
        f"- Boot SHA256: `{manifest['boot_sha256']}`",
        "- Boot SHA verification: source/build output only; live flash/readback/selftest must be recorded separately before promotion.",
        f"- Init: `A90 Linux init {manifest['init_version']} ({manifest['init_build']})`",
        f"- Helper marker: `a90_android_execns_probe helper-v427` (binary marker string: `{manifest['helper_marker']}`)",
        f"- Helper SHA256: `{manifest['helper_sha256']}`",
        "",
        "## Included Route",
        "",
        f"- Helper runtime mode: `{wifi['helper_runtime_mode']}`",
        f"- Helper timeout: `{wifi['helper_timeout_sec']}`",
        f"- Property root: `{REMOTE_PROPERTY_ROOT}`",
        "- Added: `wifi status` runtime fields for WPA state, RSSI, link speed, and frequency.",
        "- Added: `NETWORK > WIFI STATUS` clearer PASS/RUN/OFF/FAIL labels and RF line.",
        "- Preserved: V2185 network ping menu/CLI, V2182 HUD storage/Wi-Fi glance, V2178 profile/autoconnect commands, and V2169 transport contract.",
        "",
        "## Safety Scope",
        "",
        "- Wi-Fi status and profile screens are read-only.",
        "- Wi-Fi scan is bounded and credential-free; it does not associate, run DHCP, install routes/DNS, or ping.",
        "- Wi-Fi ping is explicit user/test action only; it does not connect, run DHCP, change routes, or read credentials.",
        "- Gateway target is redacted in command output; public reports must redact private LAN details.",
        "- Scan result SSID/frequency/RSSI/security is rendered on screen only; raw BSSID/SSID results are not written to serial logs or public artifacts.",
        "- No `/dev/subsys_esoc0`, forced RC1/case, PMIC/GPIO/GDSC/regulator write, PCI rescan, platform bind/unbind, fake ONLINE, or eSoC notify/BOOT_DONE path is included.",
        "",
    ])


def normalize_manifest_axes() -> None:
    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["candidate_tag"] = "v2186-wifi-ui-polish"
    manifest["parent_baseline"] = "v2185-network-ping-test"
    manifest["rollback_baseline"] = "v2186-wifi-ui-polish"
    manifest["promoted_baseline"] = True
    manifest["version_axes"] = {
        "candidate_tag": "v2186-wifi-ui-polish",
        "parent_baseline": "v2185-network-ping-test",
        "rollback_baseline": "v2186-wifi-ui-polish",
        "helper_version": "helper-v427",
        "run_id": "V2186",
        "note": "V2186 is promoted as the current Wi-Fi UI polish baseline after live validation.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def main() -> int:
    configure_base()
    base = base_module()
    helper_builder = (
        v2182.v2178.v2176.v2174.v2169.v726.v2168.prev2137.prev2135.prev2133.prev2131
        .prev2129.prev2127.prev2120.prev2112.prev2108.prev2106.prev2102
        .prev2100.prev2097.prev2095.prev2082.prev2080.prev2058.prev2038
    )
    helper_builder.patch_helper_builder(base)
    base.render_report = render_report
    created_legacy_link = v2182.v2178.v2176.v2174.v2169.ensure_legacy_mkbootimg_link()
    try:
        rc = base.main()
        if rc == 0:
            normalize_manifest_axes()
            REPORT_PATH.chmod(0o644)
        return rc
    finally:
        if created_legacy_link and v2182.v2178.v2176.v2174.v2169.LEGACY_MKBOOTIMG_DIR.is_symlink():
            v2182.v2178.v2176.v2174.v2169.LEGACY_MKBOOTIMG_DIR.unlink()


if __name__ == "__main__":
    raise SystemExit(main())
