#!/usr/bin/env python3
"""Fail-closed host-only checker for the FYG8 R3C0/R3C1 boot differential.

The checker reads existing evidence and, for later stages, already-created boot
and Odin AP files. It never constructs or modifies an image, contacts a device,
or invokes Odin.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import stat
import struct
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA = "s22plus_fyg8_r3_static_checker_v1"
TARGET = "SM-S906N/g0q/S906NKSS7FYG8"
ANDROID_MAGIC = b"ANDROID!"
SEANDROID_MAGIC = b"SEANDROIDENFORCE"
AVB_FOOTER_FORMAT = "!4s2I3Q28s"
AP_TRAILER_RE = re.compile(rb"([0-9a-f]{32})  AP\.tar\n\Z")
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")

EXPECTED_RELEASE = "5.10.226-android12-9-30958166-abS906NKSS7FYG8"
EXPECTED_BANNER = (
    "Linux version 5.10.226-android12-9-30958166-abS906NKSS7FYG8 "
    "(build-user@build-host) (Android (7284624, based on r416183b) clang "
    "version 12.0.5 (https://android.googlesource.com/toolchain/llvm-project "
    "c935d99d7cf2016289302412d708641d52d2f7ee), LLD 12.0.5 "
    "(/buildbot/src/android/llvm-toolchain/out/llvm-project/lld "
    "c935d99d7cf2016289302412d708641d52d2f7ee)) #1 SMP PREEMPT "
    "Fri Aug 1 05:55:56 UTC 2025"
)

EXPECTED_R1_RESULT_SIZE = 680_172
EXPECTED_R1_RESULT_SHA256 = "448f024b9c0d99fcac02cbc6a858a227ca5cb290a44f0616621542994b329c6f"
EXPECTED_R2_RESULT_SIZE = 6_756
EXPECTED_R2_RESULT_SHA256 = "ee935a523270b45c93d2db3e1f21d32b2bf49f3a96965efe5d8df66515964392"
EXPECTED_R2_IMAGE_SIZE = 41_490_944
EXPECTED_R2_IMAGE_SHA256 = "9110a7722f28f075c5cb09789710341b44956147fa05867d05e5b3e7d024770d"

EXPECTED_STOCK_BOOT_SIZE = 100_663_296
EXPECTED_STOCK_BOOT_SHA256 = "4150b962314e6136acba61b20f471d6ee1c418b83cf8c3ee4d9cf7c91a3640ae"
EXPECTED_STOCK_BOOT_LZ4_SIZE = 27_721_802
EXPECTED_STOCK_BOOT_LZ4_SHA256 = "a75dd0285f31a5d18b0d19a0fa8f024f45a3682bb60dcdbfcbef3f654b848b38"
EXPECTED_STOCK_KERNEL_SHA256 = "027d4ab6f39d4544f87d33b219bb7877ab9b662b40434bfb96464c1193aeb69d"
EXPECTED_STOCK_RAMDISK_SHA256 = "0cb87ca46b876a8765fed95bb0ce047485a14d2ec76de95af4680423b3ed1443"
EXPECTED_STOCK_SIGNER_SHA256 = "13c2a41e4b47b0e7173d054ddff148bfcc195e639c7bca137753c03e8dfedc36"
EXPECTED_STOCK_VBMETA_SHA256 = "2128d4fa64fdbed386f8cf628e1df89b1161a60a59aec985bb28a5770873561d"

EXPECTED_MAGISK_BOOT_SIZE = 100_663_296
EXPECTED_MAGISK_BOOT_SHA256 = "2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e"
EXPECTED_MAGISK_AP_SIZE = 23_367_721
EXPECTED_MAGISK_AP_SHA256 = "d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56"
EXPECTED_STOCK_AP_SIZE = 100_669_481
EXPECTED_STOCK_AP_SHA256 = "2f6a8ac093587a0f03c423d8e21f65c6fe3a8d2ce9915297170cdaa2cac37c94"
EXPECTED_DTBO_SIZE = 8_388_608
EXPECTED_DTBO_SHA256 = "97a4864fee4e61892d733962d1ec76f8d14b52bc19e6f47440bc27d9dfc4bd0c"
EXPECTED_RECOVERY_SIZE = 104_857_600
EXPECTED_RECOVERY_SHA256 = "93fac06ca79bf4b365b25a8d49902bc41aba112ea253c30880c90e314d7895d4"

EXPECTED_MAGISKBOOT_SIZE = 943_848
EXPECTED_MAGISKBOOT_SHA256 = "a18ecbd7981179494b7d281453d6c4e25b5c719e7d2ef7f6eba3c6be3043c58e"
EXPECTED_LZ4_SIZE = 218_696
EXPECTED_LZ4_SHA256 = "91975bf197d485b81475dfa6267aa2284550b844e8e8d64a4e7e35d9a1fa9fb8"
EXPECTED_AVBTOOL_SHA256 = "063d7c7a19744ceeb72553c95962ac98fff977fc27f5f95e6063c2f15f8d3e88"
EXPECTED_AVBTOOL_SIZE = 14_060_849
MAX_AP_FILE_SIZE = EXPECTED_STOCK_BOOT_SIZE + 5 * 1024 * 1024

EXPECTED_FULL_FW_ZIP_SHA256 = "f831e5fb8abe1c7a9d8c38fe9c033a3fce7e77651776383641c385c2bb85a2c8"
EXPECTED_EXTRACTED_FULL_FW = (
    (
        "AP_S906NKSS7FYG8_S906NKSS7FYG8_MQB99315260_REV00_user_low_ship_MULTI_CERT_meta_OS15.tar.md5",
        11_499_653_242,
        "7934579fc2e7fc8097b58cb28e915578a972718b2cdc3f53d3f9b5e9bd5a0bb2",
    ),
    (
        "BL_S906NKSS7FYG8_S906NKSS7FYG8_MQB99315260_REV00_user_low_ship_MULTI_CERT.tar.md5",
        114_319_472,
        "e5aeb59de4ed16c21111945900aeda4743b717361b0919084e9d284d08e4e0ba",
    ),
    (
        "CP_S906NKSS7FYG1_CP30713288_MQB98036461_REV00_user_low_ship_MULTI_CERT.tar.md5",
        68_833_389,
        "08495982043835aa233061c70dfc42b327684e93cf7c7e02d89278a5ea3ec445",
    ),
    (
        "CSC_OKR_S906NOKR7FYG8_MQB99315260_REV00_user_low_ship_MULTI_CERT.tar.md5",
        24_811_623,
        "bb13931519fa48a9a9a08c2a00619088e037650fd573280296dedcaa5355984d",
    ),
    (
        "HOME_CSC_OKR_S906NOKR7FYG8_MQB99315260_REV00_user_low_ship_MULTI_CERT.tar.md5",
        24_780_908,
        "b8753e80cf1053b0dfe33ecdc3389c6c5c0df41ae5184d4b221ec9fe0672c514",
    ),
    (
        "_FirmwareInfo_Samfw.com.txt",
        719,
        "80daa81f48e8928827f804a34156f9d7cf2df2d7dc6160748d3b4296c674146f",
    ),
)

DEFAULT_R1_RESULT = Path(
    "workspace/private/outputs/s22plus_fyg8_kernel_rebuild_r0/"
    "remote-fx8300-r1-v3-clean/result.json"
)
DEFAULT_R2_RESULT = Path(
    "workspace/private/outputs/s22plus_fyg8_kernel_rebuild_r0/"
    "remote-fx8300-r2-v2-clean/result.json"
)
DEFAULT_R2_IMAGE = Path(
    "workspace/private/outputs/s22plus_fyg8_kernel_rebuild_r0/"
    "remote-fx8300-r1-v3-operational/source-clean-final/out/"
    "msm-waipio-waipio-gki/gki_kernel/dist/Image"
)
DEFAULT_STOCK_BOOT = Path(
    "workspace/private/inputs/s22plus_firmware/S906NKSS7FYG8_SKC/"
    "extracted-images/raw/boot.img"
)
DEFAULT_STOCK_BOOT_LZ4 = Path(
    "workspace/private/inputs/s22plus_firmware/S906NKSS7FYG8_SKC/"
    "extracted-images/lz4/boot.img.lz4"
)
DEFAULT_MAGISK_BOOT = Path("workspace/private/outputs/s22plus_magisk_root_boot_only/boot.img")
DEFAULT_MAGISK_AP = Path("workspace/private/outputs/s22plus_magisk_root_boot_only/AP.tar.md5")
DEFAULT_STOCK_AP = Path(
    "workspace/private/outputs/s22plus_native_init/"
    "odin4_stock_rollback_fyg8_raw_repacked_20260709/AP.tar.md5"
)
DEFAULT_DTBO = Path(
    "workspace/private/inputs/s22plus_firmware/S906NKSS7FYG8_SKC/"
    "extracted-images/raw/dtbo.img"
)
DEFAULT_RECOVERY = Path(
    "workspace/private/inputs/s22plus_firmware/S906NKSS7FYG8_SKC/"
    "extracted-images/raw/recovery.img"
)
DEFAULT_MAGISKBOOT = Path("workspace/private/tools/magisk-v30.7/magiskboot")
DEFAULT_LZ4 = Path(
    "workspace/private/work/s22plus_fyg8_kernel_rebuild_r0/kernel_platform/"
    "prebuilts/kernel-build-tools/linux-x86/bin/lz4"
)
DEFAULT_AVBTOOL = Path(
    "workspace/private/work/s22plus_fyg8_kernel_rebuild_r0/kernel_platform/"
    "prebuilts/kernel-build-tools/linux-x86/bin/avbtool"
)
DEFAULT_FULL_FW_ZIP = Path(
    "workspace/private/inputs/firmware/SAMFW.COM_SM-S906N_SKC_S906NKSS7FYG8_fac.zip"
)
DEFAULT_FULL_FW_DIR = Path(
    "workspace/private/inputs/firmware/SAMFW.COM_SM-S906N_SKC_S906NKSS7FYG8_fac"
)


class CheckError(ValueError):
    pass


@dataclass(frozen=True)
class BootGeometry:
    total_size: int
    header_end: int
    kernel_start: int
    kernel_end: int
    kernel_pad_end: int
    ramdisk_end: int
    ramdisk_pad_end: int
    signature_end: int
    signer_end: int
    vbmeta_start: int
    vbmeta_end: int
    footer_start: int

    @property
    def ramdisk_start(self) -> int:
        return self.kernel_pad_end

    @property
    def signature_start(self) -> int:
        return self.ramdisk_pad_end

    @property
    def signer_start(self) -> int:
        return self.signature_end

    @property
    def final_pad_start(self) -> int:
        return self.vbmeta_end

    def regions(self) -> tuple[tuple[str, int, int], ...]:
        return (
            ("header", 0, self.header_end),
            ("kernel", self.kernel_start, self.kernel_end),
            ("kernel_alignment", self.kernel_end, self.kernel_pad_end),
            ("ramdisk", self.ramdisk_start, self.ramdisk_end),
            ("ramdisk_alignment", self.ramdisk_end, self.ramdisk_pad_end),
            ("gki_signature", self.signature_start, self.signature_end),
            ("samsung_signer", self.signer_start, self.signer_end),
            ("avb_prepad", self.signer_end, self.vbmeta_start),
            ("vbmeta", self.vbmeta_start, self.vbmeta_end),
            ("final_padding", self.final_pad_start, self.footer_start),
            ("avb_footer", self.footer_start, self.total_size),
        )


FYG8_GEOMETRY = BootGeometry(
    total_size=100_663_296,
    header_end=4_096,
    kernel_start=4_096,
    kernel_end=41_495_040,
    kernel_pad_end=41_496_576,
    ramdisk_end=43_475_543,
    ramdisk_pad_end=43_479_040,
    signature_end=43_483_136,
    signer_end=43_483_664,
    vbmeta_start=43_487_232,
    vbmeta_end=43_489_344,
    footer_start=100_663_232,
)


def repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "GOAL.md").is_file() and (parent / "AGENTS.md").is_file():
            return parent
    raise CheckError("repository root not found")


def resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else (root / path).resolve()


def display_path(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require_pinned_file(path: Path, size: int, sha256: str, label: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise CheckError(f"{label} missing: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        before = os.fstat(handle.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise CheckError(f"{label} is not a regular file: {path}")
        if before.st_size != size:
            raise CheckError(f"{label} size mismatch: {before.st_size} != {size}")
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
        after = os.fstat(handle.fileno())
    current = path.stat(follow_symlinks=False)
    identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
    identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
    identity_current = (current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns, current.st_ctime_ns)
    if identity_before != identity_after or identity_after != identity_current:
        raise CheckError(f"{label} changed during verification: {path}")
    actual_sha = digest.hexdigest()
    if actual_sha != sha256:
        raise CheckError(f"{label} SHA256 mismatch: {actual_sha}")
    return {"path": str(path), "size": before.st_size, "sha256": actual_sha}


def read_pinned_bytes(path: Path, size: int, sha256: str, label: str) -> tuple[dict[str, Any], bytes]:
    if path.is_symlink() or not path.is_file():
        raise CheckError(f"{label} missing: {path}")
    with path.open("rb") as handle:
        before = os.fstat(handle.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise CheckError(f"{label} is not a regular file: {path}")
        data = handle.read()
        after = os.fstat(handle.fileno())
    current = path.stat(follow_symlinks=False)
    identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
    identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
    identity_current = (current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns, current.st_ctime_ns)
    if identity_before != identity_after or identity_after != identity_current:
        raise CheckError(f"{label} changed during verification: {path}")
    if len(data) != size:
        raise CheckError(f"{label} size mismatch: {len(data)} != {size}")
    actual_sha = sha256_bytes(data)
    if actual_sha != sha256:
        raise CheckError(f"{label} SHA256 mismatch: {actual_sha}")
    return {"path": str(path), "size": len(data), "sha256": actual_sha}, data


def read_json_bytes(payload: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise CheckError(f"invalid {label} JSON") from exc
    if not isinstance(value, dict):
        raise CheckError(f"{label} JSON top level must be an object")
    return value


def require_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise CheckError(f"{label} mismatch: {actual!r} != {expected!r}")


def audit_r1(path: Path) -> dict[str, Any]:
    pin, payload = read_pinned_bytes(path, EXPECTED_R1_RESULT_SIZE, EXPECTED_R1_RESULT_SHA256, "R1 result")
    data = read_json_bytes(payload, "R1 result")
    expected = {
        "schema": "s22plus_fyg8_kernel_build_v3",
        "target": TARGET,
        "host_only": True,
        "mode": "build",
        "lto_mode": "full",
        "returncode": 0,
        "r1_buildability_pass": True,
    }
    for key, value in expected.items():
        require_equal(data.get(key), value, f"R1 {key}")
    for gate in ("kernel_banner_gate", "module_gate", "output_gate"):
        require_equal(data.get(gate, {}).get("verified"), True, f"R1 {gate}.verified")
    require_equal(data.get("kernel_banner_gate", {}).get("banner"), EXPECTED_BANNER, "R1 banner")
    require_equal(data.get("timestamp_control_runtime", {}).get("verified"), True, "R1 timestamp verified")
    require_equal(data.get("timestamp_control_runtime", {}).get("restored"), True, "R1 timestamp restored")
    require_equal(data.get("provenance", {}).get("source_overlay", {}).get("verified"), True, "R1 overlay")
    require_equal(data.get("incremental_dist_refresh", {}).get("verified"), True, "R1 dist refresh")
    safety = data.get("safety", {})
    for key in ("boot_image_packaging", "device_contact", "flash", "partition_write"):
        require_equal(safety.get(key), False, f"R1 safety.{key}")
    outputs = [item for item in data.get("outputs", []) if item.get("name") == "Image"]
    if len(outputs) != 1:
        raise CheckError(f"R1 requires one Image output, got {len(outputs)}")
    require_equal(outputs[0].get("size"), EXPECTED_R2_IMAGE_SIZE, "R1 Image size")
    require_equal(outputs[0].get("sha256"), EXPECTED_R2_IMAGE_SHA256, "R1 Image SHA256")
    return {**pin, "schema": data["schema"], "pass": True}


def audit_r2(path: Path) -> dict[str, Any]:
    pin, payload = read_pinned_bytes(path, EXPECTED_R2_RESULT_SIZE, EXPECTED_R2_RESULT_SHA256, "R2 result")
    data = read_json_bytes(payload, "R2 result")
    require_equal(data.get("schema"), "s22plus_fyg8_kernel_r2_audit_v2", "R2 schema")
    require_equal(data.get("target"), TARGET, "R2 target")
    require_equal(data.get("host_only"), True, "R2 host_only")
    require_equal(data.get("r2_static_pass"), True, "R2 static pass")
    require_equal(data.get("blockers"), [], "R2 blockers")
    require_equal(data.get("r1_gate", {}).get("sha256"), EXPECTED_R1_RESULT_SHA256, "R2 R1 pin")
    require_equal(data.get("r1_gate", {}).get("verified"), True, "R2 R1 gate")
    image = data.get("image", {})
    require_equal(image.get("sha256"), EXPECTED_R2_IMAGE_SHA256, "R2 Image SHA256")
    require_equal(image.get("file_bytes"), EXPECTED_R2_IMAGE_SIZE, "R2 Image size")
    require_equal(image.get("banner"), EXPECTED_BANNER, "R2 banner")
    for key in ("exact_banner_match", "release_match", "compiler_match", "preempt_marker_present"):
        require_equal(image.get(key), True, f"R2 image.{key}")
    require_equal(data.get("config", {}).get("full_lto"), True, "R2 Full LTO")
    require_equal(data.get("config", {}).get("compatible_for_mode"), True, "R2 config compatibility")
    require_equal(data.get("module_corpus", {}).get("complete_on_disk_corpus"), True, "R2 corpus")
    require_equal(data.get("module_provider_crc", {}).get("provider_crc_closed"), True, "R2 CRC closure")
    require_equal(data.get("boot_capacity", {}).get("fits"), True, "R2 boot capacity")
    safety = data.get("safety", {})
    for key in ("device_contact", "flash", "image_packaging", "partition_write"):
        require_equal(safety.get(key), False, f"R2 safety.{key}")
    return {**pin, "schema": data["schema"], "pass": True}


def parse_arm64_header(kernel: bytes) -> tuple[int, ...]:
    if len(kernel) < 64:
        raise CheckError("kernel is too short for ARM64 Image header")
    fields = struct.unpack_from("<IIQQQQQQII", kernel, 0)
    if fields[8] != 0x644D5241:
        raise CheckError(f"kernel ARM64 magic mismatch: 0x{fields[8]:08x}")
    return fields


def audit_r2_image(path: Path, stock_kernel: bytes) -> tuple[dict[str, Any], bytes]:
    pin, data = read_pinned_bytes(path, EXPECTED_R2_IMAGE_SIZE, EXPECTED_R2_IMAGE_SHA256, "R2 Image")
    if data == stock_kernel:
        raise CheckError("R2 Image unexpectedly equals stock kernel")
    require_equal(parse_arm64_header(data), parse_arm64_header(stock_kernel), "R2 ARM64 header")
    banner = EXPECTED_BANNER.encode("ascii")
    require_equal(data.count(banner), 1, "R2 exact banner occurrence count")
    return {**pin, "arm64_header_exact_stock_match": True, "exact_banner_count": 1}, data


def parse_avb_footer(data: bytes) -> dict[str, Any]:
    if len(data) < 64:
        raise CheckError("boot image is too short for AVB footer")
    magic, major, minor, original_size, vbmeta_offset, vbmeta_size, reserved = struct.unpack(
        AVB_FOOTER_FORMAT, data[-64:]
    )
    if magic != b"AVBf" or any(reserved):
        raise CheckError("invalid AVB footer")
    if vbmeta_offset + vbmeta_size > len(data) - 64:
        raise CheckError("AVB vbmeta range exceeds boot image")
    if data[vbmeta_offset : vbmeta_offset + 4] != b"AVB0":
        raise CheckError("AVB vbmeta magic missing")
    return {
        "version_major": major,
        "version_minor": minor,
        "original_image_size": original_size,
        "vbmeta_offset": vbmeta_offset,
        "vbmeta_size": vbmeta_size,
    }


def region_summary(data: bytes, geometry: BootGeometry) -> list[dict[str, Any]]:
    return [
        {"name": name, "start": start, "end_exclusive": end, "size": end - start, "sha256": sha256_bytes(data[start:end])}
        for name, start, end in geometry.regions()
    ]


def validate_geometry(geometry: BootGeometry) -> None:
    regions = geometry.regions()
    if regions[0][1] != 0 or regions[-1][2] != geometry.total_size:
        raise CheckError("boot geometry does not span the complete image")
    for left, right in zip(regions, regions[1:]):
        if left[2] != right[1]:
            raise CheckError(f"boot geometry gap/overlap between {left[0]} and {right[0]}")


def validate_stock_boot(
    data: bytes,
    geometry: BootGeometry = FYG8_GEOMETRY,
    expected_signer_sha256: str = EXPECTED_STOCK_SIGNER_SHA256,
) -> dict[str, Any]:
    validate_geometry(geometry)
    require_equal(len(data), geometry.total_size, "stock boot size")
    if data[:8] != ANDROID_MAGIC:
        raise CheckError("stock boot Android magic missing")
    kernel_size, ramdisk_size, _os_version, header_size = struct.unpack_from("<4I", data, 8)
    header_version = struct.unpack_from("<I", data, 40)[0]
    signature_size = struct.unpack_from("<I", data, 1580)[0]
    require_equal(header_version, 4, "stock boot header version")
    require_equal(header_size, 1584, "stock boot header size")
    require_equal(kernel_size, geometry.kernel_end - geometry.kernel_start, "stock kernel size")
    require_equal(ramdisk_size, geometry.ramdisk_end - geometry.ramdisk_start, "stock ramdisk size")
    require_equal(signature_size, geometry.signature_end - geometry.signature_start, "stock signature size")
    signer = data[geometry.signer_start : geometry.signer_end]
    if not signer.startswith(SEANDROID_MAGIC + b"SignerVer02"):
        raise CheckError("stock Samsung signer record marker mismatch")
    require_equal(sha256_bytes(signer), expected_signer_sha256, "stock signer SHA256")
    if any(data[geometry.kernel_end : geometry.kernel_pad_end]):
        raise CheckError("stock kernel alignment is nonzero")
    if any(data[geometry.ramdisk_end : geometry.ramdisk_pad_end]):
        raise CheckError("stock ramdisk alignment is nonzero")
    if any(data[geometry.signature_start : geometry.signature_end]):
        raise CheckError("stock GKI signature is not all zero")
    if any(data[geometry.signer_end : geometry.vbmeta_start]):
        raise CheckError("stock AVB pre-padding is nonzero")
    if any(data[geometry.final_pad_start : geometry.footer_start]):
        raise CheckError("stock final padding is nonzero")
    footer = parse_avb_footer(data)
    require_equal(footer["original_image_size"], geometry.signer_end, "stock AVB original size")
    require_equal(footer["vbmeta_offset"], geometry.vbmeta_start, "stock AVB vbmeta offset")
    require_equal(footer["vbmeta_size"], geometry.vbmeta_end - geometry.vbmeta_start, "stock vbmeta size")
    return {"footer": footer, "regions": region_summary(data, geometry)}


def expected_control_bytes(stock: bytes, geometry: BootGeometry = FYG8_GEOMETRY) -> bytes:
    expected = bytearray(stock)
    marker_end = geometry.signer_start + len(SEANDROID_MAGIC)
    expected[marker_end : geometry.signer_end] = b"\0" * (geometry.signer_end - marker_end)
    struct.pack_into("!Q", expected, geometry.footer_start + 12, marker_end)
    return bytes(expected)


def validate_control_boot(stock: bytes, control: bytes, geometry: BootGeometry = FYG8_GEOMETRY) -> dict[str, Any]:
    require_equal(len(control), geometry.total_size, "R3C0 boot size")
    expected = expected_control_bytes(stock, geometry)
    if control != expected:
        ranges = diff_ranges(expected, control, limit=8)
        raise CheckError(f"R3C0 differs outside exact normalized contract: {ranges}")
    footer = parse_avb_footer(control)
    marker_end = geometry.signer_start + len(SEANDROID_MAGIC)
    require_equal(footer["original_image_size"], marker_end, "R3C0 AVB original size")
    require_equal(footer["vbmeta_offset"], geometry.vbmeta_start, "R3C0 vbmeta offset")
    require_equal(footer["vbmeta_size"], geometry.vbmeta_end - geometry.vbmeta_start, "R3C0 vbmeta size")
    require_equal(
        control[geometry.vbmeta_start : geometry.vbmeta_end],
        stock[geometry.vbmeta_start : geometry.vbmeta_end],
        "R3C0 exact stock vbmeta",
    )
    return {
        "footer": footer,
        "regions": region_summary(control, geometry),
        "exact_stock_vbmeta": True,
        "exact_expected_bytes": True,
    }


def validate_candidate_boot(
    control: bytes,
    candidate: bytes,
    r2_image: bytes,
    geometry: BootGeometry = FYG8_GEOMETRY,
) -> dict[str, Any]:
    require_equal(len(candidate), geometry.total_size, "R3C1 boot size")
    expected = bytearray(control)
    require_equal(len(r2_image), geometry.kernel_end - geometry.kernel_start, "R3C1 kernel size")
    expected[geometry.kernel_start : geometry.kernel_end] = r2_image
    if candidate != bytes(expected):
        ranges = diff_ranges(bytes(expected), candidate, limit=8)
        raise CheckError(f"R3C1 differs outside exact kernel-only contract: {ranges}")
    require_equal(parse_arm64_header(r2_image), parse_arm64_header(control[geometry.kernel_start : geometry.kernel_end]), "R3C1 ARM64 header")
    footer = parse_avb_footer(candidate)
    require_equal(footer, parse_avb_footer(control), "R3C1 exact R3C0 AVB footer")
    require_equal(
        candidate[geometry.vbmeta_start : geometry.vbmeta_end],
        control[geometry.vbmeta_start : geometry.vbmeta_end],
        "R3C1 exact R3C0 vbmeta",
    )
    return {
        "footer": footer,
        "regions": region_summary(candidate, geometry),
        "exact_r3c0_vbmeta": True,
        "exact_expected_bytes": True,
    }


def diff_ranges(expected: bytes, actual: bytes, limit: int = 16) -> list[dict[str, int]]:
    if len(expected) != len(actual):
        return [{"start": 0, "end_exclusive": max(len(expected), len(actual))}]
    ranges: list[dict[str, int]] = []
    start: int | None = None
    for offset, (left, right) in enumerate(zip(expected, actual)):
        if left != right and start is None:
            start = offset
        elif left == right and start is not None:
            ranges.append({"start": start, "end_exclusive": offset})
            start = None
            if len(ranges) >= limit:
                return ranges
    if start is not None and len(ranges) < limit:
        ranges.append({"start": start, "end_exclusive": len(expected)})
    return ranges


def parse_tar_octal(field: bytes, label: str) -> int:
    if field and field[0] & 0x80:
        raise CheckError(f"GNU base-256 tar number forbidden: {label}")
    value = field.rstrip(b"\0 ").lstrip(b" ")
    if not value:
        return 0
    if any(byte not in b"01234567" for byte in value):
        raise CheckError(f"invalid tar octal field: {label}")
    return int(value, 8)


def tar_text(field: bytes, label: str) -> str:
    raw = field.split(b"\0", 1)[0]
    try:
        return raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise CheckError(f"non-ASCII tar field: {label}") from exc


def parse_single_boot_tar(prefix: bytes, strict_metadata: bool) -> tuple[dict[str, Any], bytes]:
    if len(prefix) % 512:
        raise CheckError("AP tar prefix is not 512-byte aligned")
    members: list[dict[str, Any]] = []
    payloads: list[bytes] = []
    offset = 0
    while offset + 512 <= len(prefix):
        header = prefix[offset : offset + 512]
        if header == bytes(512):
            if offset + 1024 > len(prefix) or prefix[offset + 512 : offset + 1024] != bytes(512):
                raise CheckError("AP tar lacks two terminal zero blocks")
            if any(prefix[offset:]):
                raise CheckError("AP tar has nonzero data after terminal block")
            break
        stored_checksum = parse_tar_octal(header[148:156], "checksum")
        calculated_checksum = sum(header[:148]) + 8 * ord(" ") + sum(header[156:])
        require_equal(stored_checksum, calculated_checksum, "tar header checksum")
        if header[257:263] != b"ustar\0" or header[263:265] != b"00":
            raise CheckError("AP tar must use canonical POSIX ustar header")
        name = tar_text(header[0:100], "name")
        prefix_name = tar_text(header[345:500], "prefix")
        if prefix_name:
            name = f"{prefix_name}/{name}"
        typeflag = header[156:157]
        if typeflag not in (b"0", b"\0"):
            raise CheckError(f"AP tar non-regular member forbidden: type={typeflag!r}")
        if name != "boot.img.lz4" or name.startswith("/") or ".." in Path(name).parts:
            raise CheckError(f"AP tar member name forbidden: {name!r}")
        if tar_text(header[157:257], "linkname"):
            raise CheckError("AP tar linkname must be empty")
        size = parse_tar_octal(header[124:136], "size")
        member = {
            "name": name,
            "type": "regular",
            "size": size,
            "mode": parse_tar_octal(header[100:108], "mode"),
            "uid": parse_tar_octal(header[108:116], "uid"),
            "gid": parse_tar_octal(header[116:124], "gid"),
            "mtime": parse_tar_octal(header[136:148], "mtime"),
            "uname": tar_text(header[265:297], "uname"),
            "gname": tar_text(header[297:329], "gname"),
        }
        data_start = offset + 512
        data_end = data_start + size
        padded_end = (data_end + 511) // 512 * 512
        if data_end > len(prefix) or padded_end > len(prefix):
            raise CheckError("AP tar member is truncated")
        if any(prefix[data_end:padded_end]):
            raise CheckError("AP tar member padding is nonzero")
        members.append(member)
        payloads.append(prefix[data_start:data_end])
        offset = padded_end
    else:
        raise CheckError("AP tar terminal blocks not found")
    if len(members) != 1:
        raise CheckError(f"AP tar requires exactly one raw header/member, got {len(members)}")
    if strict_metadata:
        expected = {"mode": 0o644, "uid": 0, "gid": 0, "mtime": 0, "uname": "", "gname": ""}
        for key, value in expected.items():
            require_equal(members[0][key], value, f"AP deterministic metadata {key}")
    return members[0], payloads[0]


def parse_lz4_frame(frame: bytes) -> dict[str, Any]:
    if len(frame) < 11 or frame[:4] != b"\x04\x22\x4d\x18":
        raise CheckError("LZ4 frame magic missing or legacy/skippable frame used")
    position = 4
    flg, bd = frame[position], frame[position + 1]
    position += 2
    if (flg >> 6) != 1 or flg & 0x02:
        raise CheckError(f"invalid LZ4 FLG: 0x{flg:02x}")
    block_code = (bd >> 4) & 0x07
    block_max = {4: 64 * 1024, 5: 256 * 1024, 6: 1024 * 1024, 7: 4 * 1024 * 1024}.get(block_code)
    if block_max is None or (bd & 0x80) or (bd & 0x0F):
        raise CheckError(f"invalid LZ4 BD: 0x{bd:02x}")
    content_size = None
    if flg & 0x08:
        if position + 8 > len(frame):
            raise CheckError("truncated LZ4 content-size field")
        content_size = struct.unpack_from("<Q", frame, position)[0]
        position += 8
    if flg & 0x01:
        if position + 4 > len(frame):
            raise CheckError("truncated LZ4 dictionary-id field")
        position += 4
    if position >= len(frame):
        raise CheckError("truncated LZ4 header checksum")
    position += 1
    blocks = 0
    while True:
        if position + 4 > len(frame):
            raise CheckError("truncated LZ4 block size")
        encoded_size = struct.unpack_from("<I", frame, position)[0]
        position += 4
        if encoded_size == 0:
            break
        block_size = encoded_size & 0x7FFFFFFF
        if block_size == 0 or block_size > block_max:
            raise CheckError(f"invalid LZ4 block size: {block_size}")
        if position + block_size > len(frame):
            raise CheckError("truncated LZ4 block")
        position += block_size
        if flg & 0x10:
            if position + 4 > len(frame):
                raise CheckError("truncated LZ4 block checksum")
            position += 4
        blocks += 1
    if flg & 0x04:
        if position + 4 > len(frame):
            raise CheckError("truncated LZ4 content checksum")
        position += 4
    if position != len(frame):
        raise CheckError(f"trailing or concatenated LZ4 data: {len(frame) - position} bytes")
    return {
        "flg": flg,
        "bd": bd,
        "block_count": blocks,
        "content_size": content_size,
        "frame_size": len(frame),
        "single_frame_no_trailing_data": True,
    }


def decompress_lz4(tool: Path, frame: bytes) -> bytes:
    result = subprocess.run(
        [str(tool), "-d", "-c"],
        input=frame,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=120,
    )
    if result.returncode != 0:
        raise CheckError(f"LZ4 decompression failed: {result.stderr.decode(errors='replace')}")
    return result.stdout


def validate_ap(
    path: Path,
    expected_size: int | None,
    expected_sha256: str,
    expected_raw: bytes,
    lz4: Path,
    label: str,
    strict_metadata: bool,
) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise CheckError(f"{label} missing: {path}")
    actual_size = path.stat().st_size
    if actual_size < 41 or actual_size > MAX_AP_FILE_SIZE:
        raise CheckError(f"{label} size outside bounded AP envelope: {actual_size}")
    if expected_size is not None:
        require_equal(actual_size, expected_size, f"{label} size")
    pin, data = read_pinned_bytes(path, actual_size, expected_sha256, label)
    if len(data) < 41:
        raise CheckError(f"{label} is too short for MD5 trailer")
    trailer = data[-41:]
    match = AP_TRAILER_RE.fullmatch(trailer)
    if match is None:
        raise CheckError(f"{label} MD5 trailer is not exact")
    tar_prefix = data[:-41]
    actual_md5 = hashlib.md5(tar_prefix).hexdigest()
    require_equal(match.group(1).decode("ascii"), actual_md5, f"{label} tar MD5")
    member, frame = parse_single_boot_tar(tar_prefix, strict_metadata)
    frame_info = parse_lz4_frame(frame)
    require_equal(frame_info["content_size"], len(expected_raw), f"{label} declared LZ4 content size")
    raw = decompress_lz4(lz4, frame)
    if raw != expected_raw:
        raise CheckError(f"{label} decompressed boot bytes mismatch: {sha256_bytes(raw)}")
    require_equal(frame_info["content_size"], len(raw), f"{label} decoded LZ4 content size")
    return {
        **pin,
        "tar_md5": actual_md5,
        "member": member,
        "flash_member_set": ["boot.img.lz4"],
        "boot_partition_only": True,
        "member_sha256": sha256_bytes(frame),
        "lz4": frame_info,
        "raw_boot_size": len(raw),
        "raw_boot_sha256": sha256_bytes(raw),
    }


def validate_stock_lz4(path: Path, stock: bytes, lz4: Path) -> dict[str, Any]:
    pin, frame = read_pinned_bytes(path, EXPECTED_STOCK_BOOT_LZ4_SIZE, EXPECTED_STOCK_BOOT_LZ4_SHA256, "stock boot.img.lz4")
    frame_info = parse_lz4_frame(frame)
    require_equal(frame_info["content_size"], len(stock), "stock boot.img.lz4 declared content size")
    raw = decompress_lz4(lz4, frame)
    if raw != stock:
        raise CheckError(f"stock boot.img.lz4 raw mismatch: {sha256_bytes(raw)}")
    return {**pin, "lz4": frame_info, "raw_boot_sha256": sha256_bytes(raw)}


def run_avbtool(tool: Path, image: bytes) -> dict[str, Any]:
    if not hasattr(os, "memfd_create"):
        raise CheckError("sealed memfd is required for TOCTOU-safe avbtool input")
    fd = os.memfd_create("s22plus-fyg8-r3-avb", os.MFD_CLOEXEC | os.MFD_ALLOW_SEALING)
    try:
        view = memoryview(image)
        written = 0
        while written < len(view):
            count = os.write(fd, view[written : written + 4 * 1024 * 1024])
            if count <= 0:
                raise CheckError("short write while preparing sealed avbtool input")
            written += count
        os.lseek(fd, 0, os.SEEK_SET)
        seals = fcntl.F_SEAL_SEAL | fcntl.F_SEAL_SHRINK | fcntl.F_SEAL_GROW | fcntl.F_SEAL_WRITE
        fcntl.fcntl(fd, fcntl.F_ADD_SEALS, seals)
        with tempfile.TemporaryDirectory(prefix="s22plus-r3-avb-") as temporary:
            boot_path = Path(temporary) / "boot"
            boot_path.symlink_to(f"/proc/self/fd/{fd}")
            result = subprocess.run(
                [str(tool), "verify_image", "--image", str(boot_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=60,
                pass_fds=(fd,),
            )
    finally:
        os.close(fd)
    combined = result.stdout + result.stderr
    return {
        "returncode": result.returncode,
        "vbmeta_signature_verified": "Successfully verified footer and SHA256_RSA4096 vbmeta struct" in combined,
        "payload_hash_verified": "Successfully verified sha256 hash" in combined,
        "payload_hash_mismatch": "does not match digest in descriptor" in combined,
        "input_transport": "sealed-memfd",
    }


def require_stock_avb_pass(result: dict[str, Any]) -> None:
    require_equal(result["returncode"], 0, "stock AVB returncode")
    require_equal(result["vbmeta_signature_verified"], True, "stock vbmeta signature")
    require_equal(result["payload_hash_verified"], True, "stock payload hash")


def require_stale_avb(result: dict[str, Any], label: str) -> None:
    if result["returncode"] == 0:
        raise CheckError(f"{label} unexpectedly passes full AVB verification")
    require_equal(result["vbmeta_signature_verified"], True, f"{label} vbmeta signature")
    require_equal(result["payload_hash_mismatch"], True, f"{label} stale payload digest")


def verify_full_firmware(zip_path: Path, extracted_dir: Path) -> dict[str, Any]:
    if zip_path.is_file():
        pin = require_pinned_file(
            zip_path,
            zip_path.stat().st_size,
            EXPECTED_FULL_FW_ZIP_SHA256,
            "full firmware ZIP",
        )
        return {"form": "zip", **pin}
    if not extracted_dir.is_dir():
        raise CheckError(f"full firmware evidence missing: {zip_path} or {extracted_dir}")
    files = []
    for name, size, sha256 in EXPECTED_EXTRACTED_FULL_FW:
        files.append(require_pinned_file(extracted_dir / name, size, sha256, f"full firmware {name}"))
    return {"form": "extracted-six-file-set", "path": str(extracted_dir), "files": files}


def validate_pin(value: str | None, label: str) -> str:
    if value is None or SHA256_RE.fullmatch(value) is None:
        raise CheckError(f"{label} requires an exact lowercase SHA256 pin")
    return value


def build_common_audit(args: argparse.Namespace, root: Path) -> tuple[dict[str, Any], dict[str, bytes], dict[str, Path]]:
    paths = {
        name: resolve(root, getattr(args, name))
        for name in (
            "r1_result", "r2_result", "r2_image", "stock_boot", "stock_boot_lz4",
            "magisk_boot", "magisk_ap", "stock_ap", "dtbo", "recovery", "magiskboot",
            "lz4", "avbtool", "full_fw_zip", "full_fw_dir",
        )
    }
    tools = {
        "magiskboot": require_pinned_file(paths["magiskboot"], EXPECTED_MAGISKBOOT_SIZE, EXPECTED_MAGISKBOOT_SHA256, "magiskboot"),
        "lz4": require_pinned_file(paths["lz4"], EXPECTED_LZ4_SIZE, EXPECTED_LZ4_SHA256, "lz4"),
        "avbtool": require_pinned_file(paths["avbtool"], EXPECTED_AVBTOOL_SIZE, EXPECTED_AVBTOOL_SHA256, "avbtool"),
    }
    r1 = audit_r1(paths["r1_result"])
    r2 = audit_r2(paths["r2_result"])
    stock_pin, stock = read_pinned_bytes(paths["stock_boot"], EXPECTED_STOCK_BOOT_SIZE, EXPECTED_STOCK_BOOT_SHA256, "stock boot")
    stock_audit = validate_stock_boot(stock)
    require_equal(sha256_bytes(stock[FYG8_GEOMETRY.kernel_start:FYG8_GEOMETRY.kernel_end]), EXPECTED_STOCK_KERNEL_SHA256, "stock kernel SHA256")
    require_equal(sha256_bytes(stock[FYG8_GEOMETRY.ramdisk_start:FYG8_GEOMETRY.ramdisk_end]), EXPECTED_STOCK_RAMDISK_SHA256, "stock ramdisk SHA256")
    require_equal(sha256_bytes(stock[FYG8_GEOMETRY.vbmeta_start:FYG8_GEOMETRY.vbmeta_end]), EXPECTED_STOCK_VBMETA_SHA256, "stock vbmeta SHA256")
    stock_avb = run_avbtool(paths["avbtool"], stock)
    require_stock_avb_pass(stock_avb)
    r2_image, r2_bytes = audit_r2_image(paths["r2_image"], stock[FYG8_GEOMETRY.kernel_start:FYG8_GEOMETRY.kernel_end])
    magisk_pin, magisk = read_pinned_bytes(paths["magisk_boot"], EXPECTED_MAGISK_BOOT_SIZE, EXPECTED_MAGISK_BOOT_SHA256, "Magisk boot")
    dtbo = require_pinned_file(paths["dtbo"], EXPECTED_DTBO_SIZE, EXPECTED_DTBO_SHA256, "stock DTBO")
    recovery = require_pinned_file(paths["recovery"], EXPECTED_RECOVERY_SIZE, EXPECTED_RECOVERY_SHA256, "stock recovery")
    stock_lz4 = validate_stock_lz4(paths["stock_boot_lz4"], stock, paths["lz4"])
    magisk_ap = validate_ap(paths["magisk_ap"], EXPECTED_MAGISK_AP_SIZE, EXPECTED_MAGISK_AP_SHA256, magisk, paths["lz4"], "Magisk rollback AP", False)
    stock_ap = validate_ap(paths["stock_ap"], EXPECTED_STOCK_AP_SIZE, EXPECTED_STOCK_AP_SHA256, stock, paths["lz4"], "stock cleanup AP", False)
    firmware = verify_full_firmware(paths["full_fw_zip"], paths["full_fw_dir"])
    report = {
        "r1": r1,
        "r2": r2,
        "r2_image": r2_image,
        "stock_boot": {**stock_pin, **stock_audit, "avb_verify": stock_avb},
        "stock_boot_lz4": stock_lz4,
        "magisk_boot": magisk_pin,
        "magisk_rollback_ap": magisk_ap,
        "stock_cleanup_ap": stock_ap,
        "stock_dtbo": dtbo,
        "stock_recovery": recovery,
        "tools": tools,
        "full_firmware_evidence": firmware,
    }
    return report, {"stock": stock, "magisk": magisk, "r2": r2_bytes}, paths


def require_stage_args(args: argparse.Namespace, names: tuple[str, ...]) -> None:
    missing = [name for name in names if getattr(args, name) is None]
    if missing:
        raise CheckError(f"stage {args.stage} missing required arguments: {missing}")


def validate_stage_shape(args: argparse.Namespace) -> None:
    r3c0 = ("r3c0_boot", "r3c0_ap", "r3c0_boot_sha256", "r3c0_ap_sha256")
    r3c1 = ("r3c1_boot", "r3c1_ap", "r3c1_boot_sha256", "r3c1_ap_sha256")
    if args.stage == "inputs":
        unexpected = [name for name in r3c0 + r3c1 if getattr(args, name) is not None]
    elif args.stage == "r3c0":
        unexpected = [name for name in r3c1 if getattr(args, name) is not None]
    else:
        unexpected = []
    if unexpected:
        raise CheckError(f"stage {args.stage} forbids unused artifact arguments: {unexpected}")


def audit(args: argparse.Namespace) -> dict[str, Any]:
    root = repo_root()
    validate_stage_shape(args)
    if args.stage in ("r3c0", "r3c1"):
        require_stage_args(args, ("r3c0_boot", "r3c0_ap", "r3c0_boot_sha256", "r3c0_ap_sha256"))
    if args.stage == "r3c1":
        require_stage_args(args, ("r3c1_boot", "r3c1_ap", "r3c1_boot_sha256", "r3c1_ap_sha256"))
    common, blobs, paths = build_common_audit(args, root)
    artifacts: dict[str, Any] = {}
    verdict = "PASS_R3_INPUTS_READY"
    if args.stage in ("r3c0", "r3c1"):
        control_path = resolve(root, args.r3c0_boot)
        control_ap_path = resolve(root, args.r3c0_ap)
        control_sha = validate_pin(args.r3c0_boot_sha256, "R3C0 boot")
        control_ap_sha = validate_pin(args.r3c0_ap_sha256, "R3C0 AP")
        control_pin, control = read_pinned_bytes(control_path, EXPECTED_STOCK_BOOT_SIZE, control_sha, "R3C0 boot")
        control_audit = validate_control_boot(blobs["stock"], control)
        control_avb = run_avbtool(paths["avbtool"], control)
        require_stale_avb(control_avb, "R3C0")
        control_ap = validate_ap(
            control_ap_path,
            None,
            control_ap_sha,
            control,
            paths["lz4"],
            "R3C0 AP",
            True,
        )
        artifacts["r3c0"] = {"boot": {**control_pin, **control_audit, "avb_verify": control_avb}, "ap": control_ap}
        blobs["control"] = control
        verdict = "PASS_R3C0_STATIC_CONTRACT"
    if args.stage == "r3c1":
        candidate_path = resolve(root, args.r3c1_boot)
        candidate_ap_path = resolve(root, args.r3c1_ap)
        candidate_sha = validate_pin(args.r3c1_boot_sha256, "R3C1 boot")
        candidate_ap_sha = validate_pin(args.r3c1_ap_sha256, "R3C1 AP")
        candidate_pin, candidate = read_pinned_bytes(candidate_path, EXPECTED_STOCK_BOOT_SIZE, candidate_sha, "R3C1 boot")
        candidate_audit = validate_candidate_boot(blobs["control"], candidate, blobs["r2"])
        candidate_avb = run_avbtool(paths["avbtool"], candidate)
        require_stale_avb(candidate_avb, "R3C1")
        candidate_ap = validate_ap(
            candidate_ap_path,
            None,
            candidate_ap_sha,
            candidate,
            paths["lz4"],
            "R3C1 AP",
            True,
        )
        artifacts["r3c1"] = {"boot": {**candidate_pin, **candidate_audit, "avb_verify": candidate_avb}, "ap": candidate_ap}
        verdict = "PASS_R3C1_STATIC_CONTRACT"
    return {
        "schema": SCHEMA,
        "target": TARGET,
        "stage": args.stage,
        "scope": {
            "host_only": True,
            "inputs_read_only": True,
            "image_construction": False,
            "ap_construction": False,
            "device_contact": False,
            "odin_invocation": False,
            "flash_authorized": False,
        },
        "inputs": common,
        "artifacts": artifacts,
        "verdict": verdict,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("inputs", "r3c0", "r3c1"), default="inputs")
    parser.add_argument("--r1-result", type=Path, default=DEFAULT_R1_RESULT)
    parser.add_argument("--r2-result", type=Path, default=DEFAULT_R2_RESULT)
    parser.add_argument("--r2-image", type=Path, default=DEFAULT_R2_IMAGE)
    parser.add_argument("--stock-boot", type=Path, default=DEFAULT_STOCK_BOOT)
    parser.add_argument("--stock-boot-lz4", type=Path, default=DEFAULT_STOCK_BOOT_LZ4)
    parser.add_argument("--magisk-boot", type=Path, default=DEFAULT_MAGISK_BOOT)
    parser.add_argument("--magisk-ap", type=Path, default=DEFAULT_MAGISK_AP)
    parser.add_argument("--stock-ap", type=Path, default=DEFAULT_STOCK_AP)
    parser.add_argument("--dtbo", type=Path, default=DEFAULT_DTBO)
    parser.add_argument("--recovery", type=Path, default=DEFAULT_RECOVERY)
    parser.add_argument("--magiskboot", type=Path, default=DEFAULT_MAGISKBOOT)
    parser.add_argument("--lz4", type=Path, default=DEFAULT_LZ4)
    parser.add_argument("--avbtool", type=Path, default=DEFAULT_AVBTOOL)
    parser.add_argument("--full-fw-zip", type=Path, default=DEFAULT_FULL_FW_ZIP)
    parser.add_argument("--full-fw-dir", type=Path, default=DEFAULT_FULL_FW_DIR)
    parser.add_argument("--r3c0-boot", type=Path)
    parser.add_argument("--r3c0-ap", type=Path)
    parser.add_argument("--r3c0-boot-sha256")
    parser.add_argument("--r3c0-ap-sha256")
    parser.add_argument("--r3c1-boot", type=Path)
    parser.add_argument("--r3c1-ap", type=Path)
    parser.add_argument("--r3c1-boot-sha256")
    parser.add_argument("--r3c1-ap-sha256")
    parser.add_argument("--out", type=Path, help="optional JSON report path; stdout is always emitted")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = audit(args)
    except (CheckError, OSError, subprocess.SubprocessError) as exc:
        print(json.dumps({"schema": SCHEMA, "stage": args.stage, "verdict": "FAIL_CLOSED", "error": str(exc)}, sort_keys=True))
        return 1
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is not None:
        root = repo_root()
        out = resolve(root, args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(encoded, encoding="ascii")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
