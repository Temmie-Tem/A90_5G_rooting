#!/usr/bin/env python3
"""Build V2232 service-object-visible plus post-FW_READY fwclass bridge boot.

This source/build wrapper keeps the V2230 service-object-visible route that
reached WLFW cap/BDF QMI, then enables the previously verified V2137
post-FW_READY boot_wlan + firmware_class feeder tail for this route only.
"""

from __future__ import annotations

import json
import shlex
import tempfile
from pathlib import Path

from _workspace_bootstrap import add_legacy_revalidation_path, repo_root

REPO_ROOT = repo_root()
add_legacy_revalidation_path(REPO_ROOT)

import build_native_init_boot_v2230_service_object_visible_post_bdf_hold as v2230
from a90harness.evidence import workspace_private_build_path, workspace_private_input_path


OUT_DIR = workspace_private_build_path("native-init", "v2232-service-object-fwclass-bridge")
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V2232_SERVICE_OBJECT_FWCLASS_BRIDGE_SOURCE_BUILD_2026-06-12.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images", "boot_linux_v2232_service_object_fwclass_bridge.img", legacy_fallback=False
)
INIT_BINARY = OUT_DIR / "init_v2232_service_object_fwclass_bridge"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v2232_service_object_fwclass_bridge.cpio"
REMOTE_PROPERTY_ROOT = "/mnt/sdext/a90/private-property-v317/v726/dev/__properties__"
EXPECTED_HELPER_MARKER = v2230.EXPECTED_HELPER_MARKER
EXPECTED_HELPER_SHA256 = "062c7a491bee66bcb7112850f4581e53e58d923719d85dbbe651d9df285ee910"
EXTRA_INIT_FLAGS = v2230.EXTRA_INIT_FLAGS
HELPER_MODE = v2230.HELPER_MODE
HELPER_RUNTIME_MODE = v2230.HELPER_RUNTIME_MODE
SERVICE_OBJECT_FWCLASS_BRIDGE_FLAG = (
    "-DA90_WIFI_TEST_BOOT_SERVICE_OBJECT_POST_FW_READY_FWCLASS_BRIDGE=1"
)
THIRD_PARTY_MKBOOTIMG = REPO_ROOT / "workspace" / "public" / "src" / "third_party" / "mkbootimg"


def base_module():
    return v2230.base_module()


def helper_chain():
    return (
        v2230.v2189.v2188.v2187.v2182.v2178.v2176.v2174.v2169.v726
        .v2168.prev2137
    )


def helper_builder_module():
    prev2137 = helper_chain()
    return (
        prev2137.prev2135.prev2133.prev2131.prev2129.prev2127.prev2120
        .prev2112.prev2108.prev2106.prev2102.prev2100.prev2097.prev2095
        .prev2082.prev2080.prev2058.prev2038
    )


def with_bridge_flag(flags: tuple[str, ...]) -> tuple[str, ...]:
    return (*tuple(flag for flag in flags if flag != SERVICE_OBJECT_FWCLASS_BRIDGE_FLAG),
            SERVICE_OBJECT_FWCLASS_BRIDGE_FLAG)


def configure_helper_flags() -> tuple[str, ...]:
    prev2137 = helper_chain()
    helper_flags = with_bridge_flag(prev2137.HELPER_FLAGS)
    prev2137.HELPER_FLAGS = helper_flags
    prev2137.prev2135.HELPER_FLAGS = helper_flags
    prev2137.prev2135.prev2133.prev2131.HELPER_FLAGS = helper_flags
    helper_builder_module().HELPER_FLAGS = helper_flags
    return helper_flags


def configure_base() -> tuple[str, ...]:
    helper_flags = configure_helper_flags()
    v2230.OUT_DIR = OUT_DIR
    v2230.REPORT_PATH = REPORT_PATH
    v2230.BOOT_IMAGE = BOOT_IMAGE
    v2230.INIT_BINARY = INIT_BINARY
    v2230.RAMDISK_CPIO = RAMDISK_CPIO
    v2230.REMOTE_PROPERTY_ROOT = REMOTE_PROPERTY_ROOT
    v2230.configure_base()
    helper_flags = configure_helper_flags()

    base = base_module()
    args = list(base.DEFAULT_ARGS)
    replacements = {
        "--cycle": "V2232",
        "--decision": "v2232-service-object-fwclass-bridge-source-build-pass",
        "--cycle-label": "v2232",
        "--init-version": "0.9.266",
        "--init-build": "v2232-service-object-fwclass-bridge",
        "--out-dir": str(OUT_DIR),
        "--init-binary": str(INIT_BINARY),
        "--helper-binary": str(OUT_DIR / "a90_android_execns_probe_v430_service_object_fwclass_bridge"),
        "--ramdisk-cpio": str(RAMDISK_CPIO),
        "--boot-image": str(BOOT_IMAGE),
        "--wifi-test-klog-prefix": "A90v2232",
        "--wifi-test-disable": "/cache/native-init-wifi-test-boot-v2232.disable",
        "--wifi-test-log": "/cache/native-init-wifi-test-boot-v2232.log",
        "--wifi-test-summary": "/cache/native-init-wifi-test-boot-v2232.summary",
        "--wifi-test-helper-result": "/cache/native-init-wifi-test-boot-v2232-helper.result",
        "--wifi-test-pid": "/cache/native-init-wifi-test-boot-v2232.pid",
        "--wifi-test-watcher-pid": "/cache/native-init-wifi-test-boot-v2232-supervisor.pid",
        "--wifi-test-property-root": REMOTE_PROPERTY_ROOT,
        "--wifi-test-helper-mode": HELPER_MODE,
        "--wifi-test-watch-sec": "180",
        "--wifi-test-supervisor-timeout-sec": "215",
    }
    for key, value in replacements.items():
        v2230.v2189.v2188.v2187.v2182.v2178.v2176.v2174.v2169.v726.set_arg(args, key, value)
    base.DEFAULT_ARGS = args
    base.base.EXTRA_INIT_FLAGS = EXTRA_INIT_FLAGS
    return helper_flags


def patch_mkbootimg_tools(base_wrapper) -> None:
    build_base = base_wrapper.base

    def build_boot_image(args) -> None:
        with tempfile.TemporaryDirectory(prefix="a90-v2232-unpack-") as temp_name:
            temp_dir = Path(temp_name)
            unpack_args = build_base.run(
                [
                    "python3",
                    THIRD_PARTY_MKBOOTIMG / "unpack_bootimg.py",
                    "--boot_img",
                    args.base_boot,
                    "--out",
                    temp_dir,
                    "--format=mkbootimg",
                ],
                capture=True,
            ).stdout
            mkboot_args = shlex.split(unpack_args)

            for index, item in enumerate(mkboot_args):
                if item == "--ramdisk":
                    mkboot_args[index + 1] = str(args.ramdisk_cpio)
                    break
            else:
                raise RuntimeError("base boot image mkbootimg args did not include --ramdisk")

            if args.boot_image.exists():
                args.boot_image.unlink()
            build_base.run([
                "python3",
                THIRD_PARTY_MKBOOTIMG / "mkbootimg.py",
                *mkboot_args,
                "--output",
                args.boot_image,
            ])
        args.boot_image.chmod(0o600)

    build_base.build_boot_image = build_boot_image


def render_report(manifest: dict[str, object], helper_flags: tuple[str, ...]) -> str:
    wifi = manifest["wifi_test"]
    helper_flag_lines = [f"- `{flag}`" for flag in helper_flags]
    return "\n".join([
        "# Native Init V2232 Service-Object FWClass Bridge Source Build",
        "",
        "## Summary",
        "",
        "- Cycle: `V2232`",
        "- Type: source/build-only rollbackable service-object-visible + post-FW_READY fwclass bridge test boot.",
        f"- Decision: `{manifest['decision']}`",
        "- Result: PASS",
        "- Reason: V2231 proved service-manager, PM registration, WLFW cap QMI, and BDF result complete but no `wlan0`; V2232 keeps that route and reattaches the V2137 post-FW_READY `boot_wlan` + firmware_class feeder tail under a new compile-time bridge gate.",
        "- Manifest: `workspace/private/builds/native-init/v2232-service-object-fwclass-bridge/manifest.json`",
        f"- Boot image: `{manifest['boot_image']}`",
        f"- Boot SHA256: `{manifest['boot_sha256']}`",
        f"- Init: `A90 Linux init {manifest['init_version']} ({manifest['init_build']})`",
        f"- Helper marker: `a90_android_execns_probe helper-v430` (binary marker string: `{manifest['helper_marker']}`)",
        f"- Helper SHA256: `{manifest['helper_sha256']}`",
        "",
        "## Route",
        "",
        f"- Helper runtime mode: `{wifi['helper_runtime_mode']}`",
        f"- Helper timeout: `{wifi['helper_timeout_sec']}`",
        f"- Property root: `{REMOTE_PROPERTY_ROOT}`",
        "- Kept from V2230: service-object-visible service-manager/PM route, provider-visible startup, internal modem holder, WLFW cap/BDF focused uprobes, long post-BDF hold.",
        "- Added for this build only: `A90_WIFI_TEST_BOOT_SERVICE_OBJECT_POST_FW_READY_FWCLASS_BRIDGE=1`, allowing service-object mode to run the already compile-gated V2137 post-FW_READY `boot_wlan` trigger and QCACLD firmware_class feeder.",
        "- Expected discriminator: if `post_fw_ready_boot_wlan_trigger.executed=1` plus firmware_class feeder produces `wlan0`, the V2231 blocker was the missing post-FW_READY QCACLD driver-start tail; if it executes but still no `wlan0`, inspect FW_READY/register-driver/firmware_class counters from the same run.",
        "",
        "## Helper Flags",
        "",
        *helper_flag_lines,
        "",
        "## Safety Scope",
        "",
        "This build script performed host-side source/build work only. The eventual live handoff remains rollbackable and excludes Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, eSoC/PCIe/GDSC/PMIC/GPIO writes, platform bind/unbind, module load/unload, `/dev/subsys_esoc0`, and sda29 writes. The only intended active WLAN driver-start action is the existing compile-gated `/sys/kernel/boot_wlan/boot_wlan` write after ICNSS FW_READY, plus bounded firmware_class fallback writes for observed QCACLD request nodes.",
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
    patch_mkbootimg_tools(base)
    base.render_report = lambda manifest: render_report(manifest, helper_flags)
    rc = base.main()
    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["candidate_tag"] = "v2232-service-object-fwclass-bridge"
    manifest["helper_flags"] = list(helper_flags)
    manifest["service_object_fwclass_bridge_flag"] = SERVICE_OBJECT_FWCLASS_BRIDGE_FLAG
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    BOOT_IMAGE.parent.mkdir(parents=True, exist_ok=True)
    promotion_path = OUT_DIR / "promotion-candidate.json"
    promotion_path.write_text(json.dumps({
        "candidate_tag": "v2232-service-object-fwclass-bridge",
        "boot_image": str(BOOT_IMAGE.relative_to(REPO_ROOT)),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "helper_sha256": manifest["helper_sha256"],
        "source_report": str(REPORT_PATH.relative_to(REPO_ROOT)),
        "note": "V2232 combines the V2230 service-object-visible route with the V2137 post-FW_READY boot_wlan/fwclass tail under a new helper compile gate.",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
