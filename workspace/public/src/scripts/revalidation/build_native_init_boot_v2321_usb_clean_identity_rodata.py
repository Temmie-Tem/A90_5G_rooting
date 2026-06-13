#!/usr/bin/env python3
"""Build V2321 USB clean identity rodata checkpoint boot.

V2321 keeps V2320 native-init behavior but removes the product-string overrun:
``SAMSUNG_Android\0`` is replaced by ``A90 Linux ARM64\0`` exactly inside the
original 16-byte product slot. The manufacturer patch remains the V2318
fixed-length ``SAMSUNG`` -> ``A90-LNX`` replacement.
"""

from __future__ import annotations

import hashlib
import json
import shlex
import tempfile
from pathlib import Path

from _workspace_bootstrap import add_legacy_revalidation_path, repo_root

REPO_ROOT = repo_root()
add_legacy_revalidation_path(REPO_ROOT)

import build_native_init_boot_v2316_usb_linux_identity as v2316
from a90harness.evidence import workspace_private_build_path, workspace_private_input_path


OUT_DIR = workspace_private_build_path("native-init", "v2321-usb-clean-identity-rodata")
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V2321_USB_CLEAN_IDENTITY_RODATA_SOURCE_BUILD_2026-06-14.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images", "boot_linux_v2321_usb_clean_identity_rodata.img", legacy_fallback=False
)
INIT_BINARY = OUT_DIR / "init_v2321_usb_clean_identity_rodata"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v2321_usb_clean_identity_rodata.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v437_usb_clean_identity_rodata"
PATCHED_KERNEL = OUT_DIR / "kernel_v2321_usb_clean_identity_rodata"
REMOTE_PROPERTY_ROOT = v2316.REMOTE_PROPERTY_ROOT
EXPECTED_HELPER_MARKER = v2316.EXPECTED_HELPER_MARKER
EXPECTED_HELPER_SHA256 = v2316.EXPECTED_HELPER_SHA256
EXTRA_INIT_FLAGS = v2316.EXTRA_INIT_FLAGS
THIRD_PARTY_MKBOOTIMG = REPO_ROOT / "workspace" / "public" / "src" / "third_party" / "mkbootimg"

EXPECTED_SOURCE_KERNEL_SHA256 = "9f4fc72c15ce9f96694023cf8f3f0340651d073acd584853941764cf9756b85a"
PRODUCT_OFFSET = 0x233C11E
PRODUCT_OLD = b"SAMSUNG_Android\x00"
PRODUCT_NEW = b"A90 Linux ARM64\x00"
MANUFACTURER_OFFSET = 0x2346D6C
MANUFACTURER_OLD = b"SAMSUNG\x00"
MANUFACTURER_NEW = b"A90-LNX\x00"

USB_CLEAN_IDENTITY_RODATA_PATCH = {
    "mode": "clean-identity-fixed-length",
    "reason": "V2319/V2320 proved the overrun boundary but only damaged adjacent configfs error-log text; V2321 promotes the no-overrun product identity as the safer rollback checkpoint.",
    "manufacturer_old": "SAMSUNG",
    "manufacturer_new": "A90-LNX",
    "manufacturer_offset": hex(MANUFACTURER_OFFSET),
    "manufacturer_old_len": len(MANUFACTURER_OLD),
    "manufacturer_new_len": len(MANUFACTURER_NEW),
    "manufacturer_collateral": "Gamepad for SAMSUNG suffix becomes Gamepad for A90-LNX",
    "product_old": "SAMSUNG_Android",
    "product_new": "A90 Linux ARM64",
    "product_offset": hex(PRODUCT_OFFSET),
    "product_old_len": len(PRODUCT_OLD),
    "product_new_len": len(PRODUCT_NEW),
    "product_overrun_bytes": 0,
    "product_expected_adjacent_bytes_after_slot": "0x01 0x33 retained",
    "source_kernel_sha256": EXPECTED_SOURCE_KERNEL_SHA256,
}
LAST_PATCH_INFO: dict[str, object] | None = None


def base_module():
    return v2316.base_module()


def helper_builder_module():
    return v2316.helper_builder_module()


def set_arg(args: list[str], key: str, value: str) -> None:
    index = args.index(key)
    args[index + 1] = value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def patch_kernel_identity_literals(source_kernel: Path, patched_kernel: Path) -> dict[str, object]:
    source_sha = sha256(source_kernel)
    if source_sha != EXPECTED_SOURCE_KERNEL_SHA256:
        raise RuntimeError(
            f"unexpected source kernel sha256: {source_sha}; "
            f"expected {EXPECTED_SOURCE_KERNEL_SHA256}"
        )

    data = bytearray(source_kernel.read_bytes())
    found = data.count(PRODUCT_OLD)
    if found != 1:
        raise RuntimeError(f"expected exactly one product literal, found {found}")
    actual_offset = data.find(PRODUCT_OLD)
    if actual_offset != PRODUCT_OFFSET:
        raise RuntimeError(f"product literal offset changed: {hex(actual_offset)} != {hex(PRODUCT_OFFSET)}")
    if data[PRODUCT_OFFSET:PRODUCT_OFFSET + len(PRODUCT_OLD)] != PRODUCT_OLD:
        raise RuntimeError("product literal bytes do not match expected old value")
    if len(PRODUCT_NEW) != len(PRODUCT_OLD):
        raise RuntimeError(
            f"product replacement must be fixed-length: {len(PRODUCT_NEW)} != {len(PRODUCT_OLD)}"
        )
    after_slot_offset = PRODUCT_OFFSET + len(PRODUCT_OLD)
    if data[after_slot_offset:after_slot_offset + 2] != bytes([0x01, 0x33]):
        raise RuntimeError(
            "unexpected bytes after product slot: "
            f"{data[after_slot_offset:after_slot_offset + 2].hex(' ')}; "
            "expected 01 33 before fixed-length patch"
        )

    manufacturer_found = data.count(MANUFACTURER_OLD)
    if manufacturer_found != 1:
        raise RuntimeError(f"expected exactly one manufacturer literal, found {manufacturer_found}")
    actual_manufacturer_offset = data.find(MANUFACTURER_OLD)
    if actual_manufacturer_offset != MANUFACTURER_OFFSET:
        raise RuntimeError(
            f"manufacturer literal offset changed: {hex(actual_manufacturer_offset)} != {hex(MANUFACTURER_OFFSET)}"
        )
    if data[MANUFACTURER_OFFSET:MANUFACTURER_OFFSET + len(MANUFACTURER_OLD)] != MANUFACTURER_OLD:
        raise RuntimeError("manufacturer literal bytes do not match expected old value")
    if len(MANUFACTURER_OLD) != len(MANUFACTURER_NEW):
        raise RuntimeError("manufacturer replacement must be fixed-length")

    data[PRODUCT_OFFSET:PRODUCT_OFFSET + len(PRODUCT_NEW)] = PRODUCT_NEW
    data[MANUFACTURER_OFFSET:MANUFACTURER_OFFSET + len(MANUFACTURER_NEW)] = MANUFACTURER_NEW
    patched_kernel.parent.mkdir(parents=True, exist_ok=True)
    patched_kernel.write_bytes(data)
    patched_kernel.chmod(0o600)

    post = patched_kernel.read_bytes()
    if post.count(PRODUCT_OLD) != 0:
        raise RuntimeError("old product literal still present after patch")
    if post.count(PRODUCT_NEW.rstrip(b"\x00") + b"\x00") != 1:
        raise RuntimeError("new product literal not uniquely present after patch")
    if post.count(MANUFACTURER_OLD) != 0:
        raise RuntimeError("old manufacturer literal still present after patch")
    if post.count(MANUFACTURER_NEW) != 1:
        raise RuntimeError("new manufacturer literal not uniquely present after patch")
    if post[after_slot_offset:after_slot_offset + 2] != bytes([0x01, 0x33]):
        raise RuntimeError(
            "fixed-length product patch damaged adjacent configfs log prefix: "
            f"{post[after_slot_offset:after_slot_offset + 2].hex(' ')}"
        )

    return {
        **USB_CLEAN_IDENTITY_RODATA_PATCH,
        "patched_kernel_sha256": sha256(patched_kernel),
    }


def configure_base() -> tuple[str, ...]:
    v2316.OUT_DIR = OUT_DIR
    v2316.REPORT_PATH = REPORT_PATH
    v2316.BOOT_IMAGE = BOOT_IMAGE
    v2316.INIT_BINARY = INIT_BINARY
    v2316.RAMDISK_CPIO = RAMDISK_CPIO
    helper_flags = v2316.configure_base()

    base = base_module()
    args = list(base.DEFAULT_ARGS)
    replacements = {
        "--cycle": "V2321",
        "--decision": "v2321-usb-clean-identity-rodata-source-build-pass",
        "--cycle-label": "v2321",
        "--init-version": "0.9.285",
        "--init-build": "v2321-usb-clean-identity-rodata",
        "--out-dir": str(OUT_DIR),
        "--init-binary": str(INIT_BINARY),
        "--helper-binary": str(HELPER_BINARY),
        "--ramdisk-cpio": str(RAMDISK_CPIO),
        "--boot-image": str(BOOT_IMAGE),
        "--wifi-test-klog-prefix": "A90v2321",
        "--wifi-test-disable": "/cache/native-init-wifi-test-boot-v2321.disable",
        "--wifi-test-log": "/cache/native-init-wifi-test-boot-v2321.log",
        "--wifi-test-summary": "/cache/native-init-wifi-test-boot-v2321.summary",
        "--wifi-test-helper-result": "/cache/native-init-wifi-test-boot-v2321-helper.result",
        "--wifi-test-pid": "/cache/native-init-wifi-test-boot-v2321.pid",
        "--wifi-test-watcher-pid": "/cache/native-init-wifi-test-boot-v2321-supervisor.pid",
        "--wifi-test-property-root": REMOTE_PROPERTY_ROOT,
    }
    for key, value in replacements.items():
        set_arg(args, key, value)
    base.DEFAULT_ARGS = args
    base.base.EXTRA_INIT_FLAGS = EXTRA_INIT_FLAGS
    return helper_flags


def patch_mkbootimg_tools(base_wrapper) -> None:
    build_base = base_wrapper.base

    def build_boot_image(args) -> None:
        global LAST_PATCH_INFO
        with tempfile.TemporaryDirectory(prefix="a90-v2321-unpack-") as temp_name:
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

            patch_info = patch_kernel_identity_literals(temp_dir / "kernel", PATCHED_KERNEL)
            LAST_PATCH_INFO = patch_info
            args.clean_identity_rodata_patch_info = patch_info

            for index, item in enumerate(mkboot_args):
                if item == "--ramdisk":
                    mkboot_args[index + 1] = str(args.ramdisk_cpio)
                if item == "--kernel":
                    mkboot_args[index + 1] = str(PATCHED_KERNEL)

            if "--ramdisk" not in mkboot_args:
                raise RuntimeError("base boot image mkbootimg args did not include --ramdisk")
            if "--kernel" not in mkboot_args:
                raise RuntimeError("base boot image mkbootimg args did not include --kernel")

            if args.boot_image.exists():
                args.boot_image.unlink()
            args.boot_image.parent.mkdir(parents=True, exist_ok=True)
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
    helper_flag_lines = [f"- `{flag}`" for flag in helper_flags]
    patch_info = manifest["usb_clean_identity_rodata_patch"]
    return "\n".join([
        "# Native Init V2321 USB Clean Identity Rodata Source Build",
        "",
        "## Summary",
        "",
        "- Cycle: `V2321`",
        "- Track: USB identity checkpoint after V2319/V2320 bounded-overrun experiments.",
        "- Type: source/build-only rollbackable native-init checkpoint boot.",
        f"- Decision: `{manifest['decision']}`",
        "- Result: PASS",
        "- Reason: promote the clean fixed-length product identity as the safer rollback/checkpoint target.",
        "- Manifest: `workspace/private/builds/native-init/v2321-usb-clean-identity-rodata/manifest.json`",
        f"- Boot image: `{manifest['boot_image']}`",
        f"- Boot SHA256: `{manifest['boot_sha256']}`",
        f"- Init: `A90 Linux init {manifest['init_version']} ({manifest['init_build']})`",
        f"- Helper marker: `a90_android_execns_probe helper-v427` (binary marker string: `{manifest['helper_marker']}`)",
        f"- Helper SHA256: `{manifest['helper_sha256']}`",
        "",
        "## Clean Identity Rodata Patch",
        "",
        f"- Source kernel SHA256: `{patch_info['source_kernel_sha256']}`",
        f"- Patched kernel SHA256: `{patch_info['patched_kernel_sha256']}`",
        f"- Product offset: `{patch_info['product_offset']}`",
        "- Old product: `SAMSUNG_Android`.",
        "- New product: `A90 Linux ARM64`.",
        f"- Product replacement length delta: `{patch_info['product_overrun_bytes']}` bytes.",
        f"- Adjacent bytes after product slot: `{patch_info['product_expected_adjacent_bytes_after_slot']}`.",
        f"- Manufacturer offset: `{patch_info['manufacturer_offset']}`",
        "- Old manufacturer: `SAMSUNG`.",
        "- New manufacturer: `A90-LNX`.",
        f"- Known collateral: `{patch_info['manufacturer_collateral']}`.",
        "- Constraint: byte overwrite only; no section-size, code-layout, branch, VID/PID, or command-behavior change.",
        "",
        "## Why Clean Identity Next",
        "",
        "- The product literal is unique in the extracted V2316 kernel blob.",
        "- V2317 proved the product rodata patch is live and rollbackable.",
        "- V2318 proved the manufacturer fixed-length patch is also live and rollbackable.",
        "- V2319/V2320 proved one-byte and two-byte product overruns can boot, but V2320 also proved the adjacent bytes are the `KERN_ERR` prefix of a USB configfs error-log string.",
        "- V2321 intentionally returns to a fixed-length 16-byte replacement so the adjacent `0x01 0x33` prefix remains intact.",
        "- Expected host descriptor after live boot: `iManufacturer=A90-LNX`, `iProduct=A90 Linux ARM64`, `iSerial=A90NATIVE001`.",
        "",
        "## Command Scope",
        "",
        "- No USB control-surface behavior change. Inherits V2313-V2315 (`usb status`, `usb mass-storage add/remove/expose`) and V2316 serial redaction/userspace configfs identity.",
        "- Keeps `idVendor=0x04e8` and `idProduct=0x6861` for host transport compatibility.",
        "",
        "## Helper Flags",
        "",
        *helper_flag_lines,
        "",
        "## Safety Scope",
        "",
        "This source build performed host-side build work only. It changes the product rodata identity string with no product-slot overrun, keeps the V2318 fixed-length manufacturer replacement, and bumps the native-init run/build identity. It does not change command behavior, USB VID/PID, partitions, adb-over-ffs, HID, BadUSB, Wi-Fi, kernel code flow, or any forbidden subsystem.",
        "",
        "## Required Device Step",
        "",
        "- Boot-only flash through `native_init_flash.py`, pinned SHA, and auto-rollback to the pre-existing known-good checkpoint on any failure.",
        "- `version` / `status` / `selftest fail=0`.",
        "- `usb status`: `control.ok=1`, configfs strings still show V2316 userspace identity.",
        "- Host descriptor validation: `iManufacturer=A90-LNX`, `iProduct=A90 Linux ARM64`, `iSerial=A90NATIVE001`.",
        "- USB persona smoke: `usb mass-storage expose` then `remove`; confirm serial control returns and NCM+ACM remain present.",
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

    original_render_report = render_report

    def render_with_patch_info(manifest: dict[str, object]) -> str:
        if "usb_clean_identity_rodata_patch" not in manifest:
            if LAST_PATCH_INFO is None:
                raise RuntimeError("clean identity rodata patch info missing before report render")
            manifest["usb_clean_identity_rodata_patch"] = LAST_PATCH_INFO
        return original_render_report(manifest, helper_flags)

    base.render_report = render_with_patch_info
    rc = base.main()
    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    patch_info = {
        **USB_CLEAN_IDENTITY_RODATA_PATCH,
        "patched_kernel_sha256": sha256(PATCHED_KERNEL),
    }
    manifest["candidate_tag"] = "v2321-usb-clean-identity-rodata"
    manifest["parent_baseline"] = "v2320-usb-product-overrun2-rodata"
    manifest["rollback_baseline"] = "v2237-supplicant-terminate-poll"
    manifest["helper_flags"] = list(helper_flags)
    manifest["usb_clean_identity_rodata_patch"] = patch_info
    manifest["promotion_intent"] = "clean-identity-rollback-checkpoint"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(render_report(manifest, helper_flags), encoding="utf-8")
    promotion_path = OUT_DIR / "promotion-candidate.json"
    promotion_path.write_text(json.dumps({
        "candidate_tag": "v2321-usb-clean-identity-rodata",
        "boot_image": str(BOOT_IMAGE.relative_to(REPO_ROOT)),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "helper_sha256": manifest["helper_sha256"],
        "source_report": str(REPORT_PATH.relative_to(REPO_ROOT)),
        "clean_identity_rodata_patch": patch_info,
        "note": "V2321 promotes the fixed-length clean product identity on top of the V2318 manufacturer patch: host iManufacturer should remain A90-LNX and iProduct should become A90 Linux ARM64 with no product-slot overrun.",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
