#!/usr/bin/env python3
"""Build V2322 named single-LUN mass-storage identity boot.

V2322 keeps the V2321 clean parent USB descriptor rodata patch and changes only
native-init mass-storage behavior: lun.0 gets a per-LUN SCSI INQUIRY identity
and the exposed read-only backing file is a labeled FAT image.
"""

from __future__ import annotations

import json
from pathlib import Path

from _workspace_bootstrap import add_legacy_revalidation_path, repo_root

REPO_ROOT = repo_root()
add_legacy_revalidation_path(REPO_ROOT)

import build_native_init_boot_v2321_usb_clean_identity_rodata as v2321
from a90harness.evidence import workspace_private_build_path, workspace_private_input_path


OUT_DIR = workspace_private_build_path("native-init", "v2322-usb-named-lun-identity")
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V2322_USB_NAMED_LUN_IDENTITY_SOURCE_BUILD_2026-06-14.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images", "boot_linux_v2322_usb_named_lun_identity.img", legacy_fallback=False
)
INIT_BINARY = OUT_DIR / "init_v2322_usb_named_lun_identity"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v2322_usb_named_lun_identity.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v438_usb_named_lun_identity"
PATCHED_KERNEL = OUT_DIR / "kernel_v2322_usb_named_lun_identity"

INQUIRY_VENDOR = "A90-LNX"
INQUIRY_PRODUCT = "A90-INTERNAL"
INQUIRY_REVISION = "0001"
INQUIRY_STRING = f"{INQUIRY_VENDOR:<8}{INQUIRY_PRODUCT:<16}{INQUIRY_REVISION}"
VOLUME_LABEL = "A90INTERNAL"
BACKING_PATH = "/cache/a90-usb-mass-storage-v2322-internal.img"
BACKING_BYTES = 8 * 1024 * 1024


def base_module():
    return v2321.base_module()


def helper_builder_module():
    return v2321.helper_builder_module()


def configure_base() -> tuple[str, ...]:
    v2321.OUT_DIR = OUT_DIR
    v2321.REPORT_PATH = REPORT_PATH
    v2321.BOOT_IMAGE = BOOT_IMAGE
    v2321.INIT_BINARY = INIT_BINARY
    v2321.RAMDISK_CPIO = RAMDISK_CPIO
    v2321.HELPER_BINARY = HELPER_BINARY
    v2321.PATCHED_KERNEL = PATCHED_KERNEL
    helper_flags = v2321.configure_base()

    base = base_module()
    args = list(base.DEFAULT_ARGS)
    replacements = {
        "--cycle": "V2322",
        "--decision": "v2322-usb-named-lun-identity-source-build-pass",
        "--cycle-label": "v2322",
        "--init-version": "0.9.286",
        "--init-build": "v2322-usb-named-lun-identity",
        "--out-dir": str(OUT_DIR),
        "--init-binary": str(INIT_BINARY),
        "--helper-binary": str(HELPER_BINARY),
        "--ramdisk-cpio": str(RAMDISK_CPIO),
        "--boot-image": str(BOOT_IMAGE),
        "--wifi-test-klog-prefix": "A90v2322",
        "--wifi-test-disable": "/cache/native-init-wifi-test-boot-v2322.disable",
        "--wifi-test-log": "/cache/native-init-wifi-test-boot-v2322.log",
        "--wifi-test-summary": "/cache/native-init-wifi-test-boot-v2322.summary",
        "--wifi-test-helper-result": "/cache/native-init-wifi-test-boot-v2322-helper.result",
        "--wifi-test-pid": "/cache/native-init-wifi-test-boot-v2322.pid",
        "--wifi-test-watcher-pid": "/cache/native-init-wifi-test-boot-v2322-supervisor.pid",
    }
    for key, value in replacements.items():
        v2321.set_arg(args, key, value)
    base.DEFAULT_ARGS = args
    return helper_flags


def render_report(manifest: dict[str, object], helper_flags: tuple[str, ...]) -> str:
    helper_flag_lines = [f"- `{flag}`" for flag in helper_flags]
    patch_info = manifest["usb_clean_identity_rodata_patch"]
    return "\n".join([
        "# Native Init V2322 USB Named LUN Identity Source Build",
        "",
        "## Summary",
        "",
        "- Cycle: `V2322`",
        "- Track: named multi-LUN mass-storage identity, unit U-A single named LUN.",
        "- Type: source/build-only rollbackable native-init boot.",
        f"- Decision: `{manifest['decision']}`",
        "- Result: PASS",
        "- Parent USB descriptor scope: unchanged from V2321 (`A90-LNX` / `A90 Linux ARM64` / `A90NATIVE001`).",
        "- Manifest: `workspace/private/builds/native-init/v2322-usb-named-lun-identity/manifest.json`",
        f"- Boot image: `{manifest['boot_image']}`",
        f"- Boot SHA256: `{manifest['boot_sha256']}`",
        f"- Init: `A90 Linux init {manifest['init_version']} ({manifest['init_build']})`",
        f"- Helper marker: `a90_android_execns_probe helper-v427` (binary marker string: `{manifest['helper_marker']}`)",
        f"- Helper SHA256: `{manifest['helper_sha256']}`",
        "",
        "## U-A Named LUN Contract",
        "",
        f"- LUN: `mass_storage.0/lun.0` only; U-B multi-LUN is not included.",
        f"- SCSI INQUIRY vendor: `{INQUIRY_VENDOR}`.",
        f"- SCSI INQUIRY product/model: `{INQUIRY_PRODUCT}`.",
        f"- SCSI INQUIRY revision: `{INQUIRY_REVISION}`.",
        f"- Exact 28-byte INQUIRY string: `{INQUIRY_STRING}`.",
        f"- FAT volume label: `{VOLUME_LABEL}`.",
        f"- Backing file: `{BACKING_PATH}`.",
        f"- Backing bytes: `{BACKING_BYTES}`.",
        "- Storage source: file-backed read-only image under `/cache`; no real `/data`, internal partition, SD block, or forbidden partition is exposed.",
        "",
        "## Clean Parent Descriptor Patch Retained",
        "",
        f"- Source kernel SHA256: `{patch_info['source_kernel_sha256']}`",
        f"- Patched kernel SHA256: `{patch_info['patched_kernel_sha256']}`",
        "- Product patch remains fixed-length: `SAMSUNG_Android\\0` -> `A90 Linux ARM64\\0`.",
        "- Manufacturer patch remains fixed-length: `SAMSUNG` -> `A90-LNX`.",
        f"- Adjacent product-slot bytes: `{patch_info['product_expected_adjacent_bytes_after_slot']}`.",
        "- No new rodata patch is introduced for the mass-storage disk name; per-LUN identity is userspace/configfs controlled.",
        "",
        "## Helper Flags",
        "",
        *helper_flag_lines,
        "",
        "## Required Device Step",
        "",
        "- Boot-only flash through `native_init_flash.py`, pinned SHA, and auto-rollback to V2321 on any failure.",
        "- `version` / `status` / `selftest fail=0`.",
        "- `usb mass-storage expose`; reconnect and verify `control.ok=1`, NCM+ACM remain present, `lun.0/inquiry_string` is populated, and the backing path is the V2322 image.",
        "- Host parked checkpoint: `lsblk -S` or `udevadm` must show model `A90-INTERNAL`, and mounted volume label must show `A90INTERNAL`.",
        "- `usb mass-storage remove`; reconnect and verify control returns and no mass-storage medium remains active.",
        "",
        "## Safety Scope",
        "",
        "This build changes only native-init mass-storage persona behavior and the run/build identity. It preserves V2321 parent USB descriptor identity, keeps VID/PID unchanged, keeps every reconfigure path on the existing atomic unbind/rebind watchdog/restore flow, and never exposes real storage or forbidden partitions.",
        "",
    ])


def main() -> int:
    helper_flags = configure_base()
    helper_builder = helper_builder_module()
    helper_builder.EXPECTED_HELPER_MARKER = v2321.EXPECTED_HELPER_MARKER
    helper_builder.EXPECTED_HELPER_SHA256 = v2321.EXPECTED_HELPER_SHA256
    base = base_module()
    base.base.EXPECTED_HELPER_MARKER = v2321.EXPECTED_HELPER_MARKER
    base.base.EXPECTED_HELPER_SHA256 = v2321.EXPECTED_HELPER_SHA256
    helper_builder.patch_helper_builder(base)
    v2321.patch_mkbootimg_tools(base)

    def render_with_v2322_info(manifest: dict[str, object]) -> str:
        if "usb_clean_identity_rodata_patch" not in manifest:
            if v2321.LAST_PATCH_INFO is None:
                raise RuntimeError("clean identity rodata patch info missing before report render")
            manifest["usb_clean_identity_rodata_patch"] = v2321.LAST_PATCH_INFO
        manifest["usb_named_lun_identity"] = {
            "lun": 0,
            "inquiry_vendor": INQUIRY_VENDOR,
            "inquiry_product": INQUIRY_PRODUCT,
            "inquiry_revision": INQUIRY_REVISION,
            "inquiry_string": INQUIRY_STRING,
            "volume_label": VOLUME_LABEL,
            "backing_file": BACKING_PATH,
            "backing_bytes": BACKING_BYTES,
        }
        return render_report(manifest, helper_flags)

    base.render_report = render_with_v2322_info
    rc = base.main()
    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    patch_info = {
        **v2321.USB_CLEAN_IDENTITY_RODATA_PATCH,
        "patched_kernel_sha256": v2321.sha256(PATCHED_KERNEL),
    }
    manifest["candidate_tag"] = "v2322-usb-named-lun-identity"
    manifest["parent_baseline"] = "v2321-usb-clean-identity-rodata"
    manifest["rollback_baseline"] = "v2321-usb-clean-identity-rodata"
    manifest["deeper_fallback_baseline"] = "v2237-supplicant-terminate-poll"
    manifest["helper_flags"] = list(helper_flags)
    manifest["usb_clean_identity_rodata_patch"] = patch_info
    manifest["usb_named_lun_identity"] = {
        "lun": 0,
        "inquiry_vendor": INQUIRY_VENDOR,
        "inquiry_product": INQUIRY_PRODUCT,
        "inquiry_revision": INQUIRY_REVISION,
        "inquiry_string": INQUIRY_STRING,
        "volume_label": VOLUME_LABEL,
        "backing_file": BACKING_PATH,
        "backing_bytes": BACKING_BYTES,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(render_report(manifest, helper_flags), encoding="utf-8")
    promotion_path = OUT_DIR / "promotion-candidate.json"
    promotion_path.write_text(json.dumps({
        "candidate_tag": "v2322-usb-named-lun-identity",
        "boot_image": str(BOOT_IMAGE.relative_to(REPO_ROOT)),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "helper_sha256": manifest["helper_sha256"],
        "source_report": str(REPORT_PATH.relative_to(REPO_ROOT)),
        "usb_named_lun_identity": manifest["usb_named_lun_identity"],
        "clean_identity_rodata_patch": patch_info,
        "note": "V2322 is U-A: parent USB descriptor remains V2321 while lun.0 reports A90-INTERNAL and exposes a read-only FAT image labeled A90INTERNAL.",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
