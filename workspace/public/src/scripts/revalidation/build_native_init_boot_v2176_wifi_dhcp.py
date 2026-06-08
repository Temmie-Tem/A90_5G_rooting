#!/usr/bin/env python3
"""Build the V2176 Wi-Fi DHCP/connectivity test image.

V2176 is a test-boot candidate on top of the promoted V2174 Wi-Fi carrier
baseline. It adds native-init `wifi dhcp [profile]` and `wifi cleanup` so DHCP,
temporary route/DNS setup, and cleanup can be validated separately from
association/carrier.
"""

from __future__ import annotations

import json

from _workspace_bootstrap import add_legacy_revalidation_path, repo_root

REPO_ROOT = repo_root()
add_legacy_revalidation_path(REPO_ROOT)

import build_native_init_boot_v2174_wifi_urandom_connect as v2174
from a90harness.evidence import workspace_private_build_path, workspace_private_input_path


OUT_DIR = workspace_private_build_path("native-init", "v2176-wifi-dhcp-test-boot")
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V2176_WIFI_DHCP_SOURCE_BUILD_2026-06-08.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images", "boot_linux_v2176_wifi_dhcp.img", legacy_fallback=False
)
INIT_BINARY = OUT_DIR / "init_v2176_wifi_dhcp"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v2176_wifi_dhcp.cpio"
REMOTE_PROPERTY_ROOT = v2174.REMOTE_PROPERTY_ROOT
EXPECTED_HELPER_MARKER = v2174.EXPECTED_HELPER_MARKER
EXPECTED_HELPER_SHA256 = v2174.EXPECTED_HELPER_SHA256
EXTRA_INIT_FLAGS = v2174.EXTRA_INIT_FLAGS


def base_module():
    return v2174.base_module()


def configure_base() -> None:
    v2174.OUT_DIR = OUT_DIR
    v2174.REPORT_PATH = REPORT_PATH
    v2174.BOOT_IMAGE = BOOT_IMAGE
    v2174.INIT_BINARY = INIT_BINARY
    v2174.RAMDISK_CPIO = RAMDISK_CPIO
    v2174.configure_base()

    base = base_module()
    args = list(base.DEFAULT_ARGS)
    replacements = {
        "--cycle": "V2176",
        "--decision": "v2176-wifi-dhcp-source-build-pass",
        "--cycle-label": "v2176",
        "--init-version": "0.9.252",
        "--init-build": "v2176-wifi-dhcp",
        "--out-dir": str(OUT_DIR),
        "--init-binary": str(INIT_BINARY),
        "--helper-binary": str(OUT_DIR / "a90_android_execns_probe_v427_wifi_dhcp"),
        "--ramdisk-cpio": str(RAMDISK_CPIO),
        "--boot-image": str(BOOT_IMAGE),
        "--wifi-test-klog-prefix": "A90v2176",
        "--wifi-test-disable": "/cache/native-init-wifi-test-boot-v2176.disable",
        "--wifi-test-log": "/cache/native-init-wifi-test-boot-v2176.log",
        "--wifi-test-summary": "/cache/native-init-wifi-test-boot-v2176.summary",
        "--wifi-test-helper-result": "/cache/native-init-wifi-test-boot-v2176-helper.result",
        "--wifi-test-pid": "/cache/native-init-wifi-test-boot-v2176.pid",
        "--wifi-test-watcher-pid": "/cache/native-init-wifi-test-boot-v2176-supervisor.pid",
        "--wifi-test-property-root": REMOTE_PROPERTY_ROOT,
    }
    for key, value in replacements.items():
        v2174.v2169.v726.set_arg(args, key, value)
    base.DEFAULT_ARGS = args
    base.base.EXTRA_INIT_FLAGS = EXTRA_INIT_FLAGS


def render_report(manifest: dict[str, object]) -> str:
    wifi = manifest["wifi_test"]
    return "\n".join([
        "# Native Init V2176 Wi-Fi DHCP Source Build",
        "",
        "## Summary",
        "",
        "- Candidate tag: `v2176-wifi-dhcp`",
        "- Parent baseline: `v2174-wifi-urandom-connect`",
        "- Type: source/build-only test boot candidate.",
        f"- Decision: `{manifest['decision']}`",
        "- Result: PASS",
        "- Reason: V2176 keeps the V2174 Wi-Fi carrier baseline and adds explicit native-init DHCP/cleanup primitives.",
        "- Manifest: `workspace/private/builds/native-init/v2176-wifi-dhcp-test-boot/manifest.json`",
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
        "- Preserved from V2174: `wifi status`, `wifi scan [delay_ms]`, `wifi connect [profile]`, `/dev/random` and `/dev/urandom`, V726 Wi-Fi lifecycle route, and `transport.contract=1` status fields.",
        "- Added: `wifi dhcp [profile]` requires an existing carrier, runs bounded `udhcpc`, installs temporary route/DNS through a generated `/cache/a90-wifi/udhcpc-wlan0.script`, records redacted DHCP status, and refreshes the Wi-Fi HUD/runtime summary.",
        "- Added: `wifi cleanup` terminates the private supplicant control path, stops DHCP residue, removes temporary wlan0 route/address/DNS state, and refreshes the runtime summary.",
        "- Not added: boot autoconnect, unbounded ping, raw credential logging, or permanent Wi-Fi profile storage.",
        "",
        "## Safety Scope",
        "",
        "- DHCP and route/DNS mutation are explicit Wi-Fi connectivity scope only.",
        "- External ping remains runner/test scope, not part of `wifi dhcp [profile]`.",
        "- No `/dev/subsys_esoc0`, forced RC1/case, PMIC/GPIO/GDSC/regulator write, PCI rescan, platform bind/unbind, fake ONLINE, or eSoC notify/BOOT_DONE path is included.",
        "",
    ])


def normalize_manifest_axes() -> None:
    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["candidate_tag"] = "v2176-wifi-dhcp"
    manifest["parent_baseline"] = "v2174-wifi-urandom-connect"
    manifest["version_axes"] = {
        "candidate_tag": "v2176-wifi-dhcp",
        "parent_baseline": "v2174-wifi-urandom-connect",
        "helper_version": "helper-v427",
        "run_id": "V2176",
        "note": "V2176 is a test-boot candidate for DHCP/route/ping-scoped Wi-Fi validation, not a promoted baseline.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def main() -> int:
    configure_base()
    base = base_module()
    helper_builder = (
        v2174.v2169.v726.v2168.prev2137.prev2135.prev2133.prev2131.prev2129
        .prev2127.prev2120.prev2112.prev2108.prev2106.prev2102.prev2100
        .prev2097.prev2095.prev2082.prev2080.prev2058.prev2038
    )
    helper_builder.patch_helper_builder(base)
    base.render_report = render_report
    created_legacy_link = v2174.v2169.ensure_legacy_mkbootimg_link()
    try:
        rc = base.main()
        if rc == 0:
            normalize_manifest_axes()
            REPORT_PATH.chmod(0o644)
        return rc
    finally:
        if created_legacy_link and v2174.v2169.LEGACY_MKBOOTIMG_DIR.is_symlink():
            v2174.v2169.LEGACY_MKBOOTIMG_DIR.unlink()


if __name__ == "__main__":
    raise SystemExit(main())
