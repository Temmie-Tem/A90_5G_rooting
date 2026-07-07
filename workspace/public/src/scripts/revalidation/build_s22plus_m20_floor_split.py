#!/usr/bin/env python3
"""Build S22+ M20 floor-split boot-only native-init candidates.

Host-only. This script does not reboot, flash, or touch a connected device.

M20 follows the M19 C000 bootloop/manual-download result by splitting the C000
floor itself:
  M20A: raw assembly first-action reboot(download), no fs or marker.
  M20B: minimal dev/proc/sys/run setup, then reboot(download), no kmsg write.
  M20C: minimal dev/proc/sys/run setup, kmsg marker, then reboot(download).
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from build_s22plus_direct_p3_boot import (
    BOOT_PARTITION_SIZE,
    DEFAULT_ODIN,
    display_path,
    repo_root,
    require_ok,
    resolve,
    run,
    sha256_file,
    tar_members,
    write_ap_tar,
    write_boot_lz4,
)
from build_s22plus_inplace_m4t1_magiskboot import (
    DEFAULT_BASE_BOOT,
    DEFAULT_MAGISK_APK,
    DEFAULT_MAGISKBOOT,
    EXPECTED_BASE_BOOT_SHA256,
    EXPECTED_ORIGINAL_MAGISK_INIT_SHA256,
    diff_ranges,
    ensure_magiskboot,
    run_in_dir,
)


DEFAULT_OUT = Path("workspace/private/outputs/s22plus_native_init/m20_floor_split_v0_1")
DEFAULT_RAW_SOURCE = Path("workspace/public/src/native-init/s22plus_init_raw_reboot_m20a.S")
DEFAULT_C_SOURCE = Path("workspace/public/src/native-init/s22plus_init_m20_floor_split.c")
DOWNLOAD_ARG = "download"


@dataclass(frozen=True)
class Variant:
    label: str
    kind: str
    source_attr: str
    marker: str
    purpose: str
    kmsg: bool = False


VARIANTS = (
    Variant(
        label="M20A_RAW",
        kind="asm",
        source_attr="raw_source",
        marker="S22_NATIVE_INIT_M20A_RAW_REBOOT",
        purpose="first-action raw reboot(download) positive control",
    ),
    Variant(
        label="M20B_MINFS",
        kind="c",
        source_attr="c_source",
        marker="S22_NATIVE_INIT_M20B_MINFS_REBOOT",
        purpose="minimal dev/proc/sys/run setup then reboot(download), no kmsg write",
        kmsg=False,
    ),
    Variant(
        label="M20C_KMSG",
        kind="c",
        source_attr="c_source",
        marker="S22_NATIVE_INIT_M20C_KMSG_REBOOT",
        purpose="minimal dev/proc/sys/run setup, kmsg marker, then reboot(download)",
        kmsg=True,
    ),
)


def compile_asm_init(source: Path, out_path: Path, build_dir: Path, variant: Variant) -> dict[str, Any]:
    result = run(
        [
            "aarch64-linux-gnu-gcc",
            "-nostdlib",
            "-static",
            "-Wl,--build-id=none",
            "-Wl,-e,_start",
            "-Wl,-z,noexecstack",
            "-o",
            out_path,
            source,
        ]
    )
    require_ok(result, f"compile {variant.label} raw init")
    strip = run(["aarch64-linux-gnu-strip", "-s", out_path])
    require_ok(strip, f"strip {variant.label} raw init")

    file_info = run(["file", out_path])
    require_ok(file_info, f"file {variant.label} init")
    readelf = run(["aarch64-linux-gnu-readelf", "-h", "-l", out_path])
    require_ok(readelf, f"readelf {variant.label} init")
    objdump = run(["aarch64-linux-gnu-objdump", "-d", out_path])
    require_ok(objdump, f"objdump {variant.label} init")
    readelf_text = readelf.stdout.decode("utf-8", errors="replace")
    objdump_text = objdump.stdout.decode("utf-8", errors="replace")
    if "INTERP" in readelf_text or "Requesting program interpreter" in readelf_text:
        raise SystemExit(f"{variant.label} unexpectedly has a program interpreter")
    if "AArch64" not in readelf_text:
        raise SystemExit(f"{variant.label} init is not AArch64")
    if not any("mov" in line and "x8" in line and "#0x8e" in line for line in objdump_text.splitlines()):
        raise SystemExit(f"{variant.label} does not load arm64 __NR_reboot (142)")
    if not any("svc" in line and "#0x0" in line for line in objdump_text.splitlines()):
        raise SystemExit(f"{variant.label} does not contain the expected svc #0")

    required_strings = [variant.marker, DOWNLOAD_ARG]
    forbidden_strings = [b"ld-linux", b"libc.so", b"/lib/modules", b"finit_module", b"ttyGS0", b"usb_gadget", b"/config"]
    binary = out_path.read_bytes()
    for required in required_strings:
        if required.encode("ascii") not in binary:
            raise SystemExit(f"required string missing from {variant.label}: {required}")
    for forbidden in forbidden_strings:
        if forbidden in binary:
            raise SystemExit(f"{variant.label} contains forbidden string: {forbidden!r}")

    (build_dir / f"{variant.label}_init_file.txt").write_bytes(file_info.stdout + file_info.stderr)
    (build_dir / f"{variant.label}_init_readelf.txt").write_text(readelf_text, encoding="utf-8")
    (build_dir / f"{variant.label}_init_objdump.txt").write_text(objdump_text, encoding="utf-8")
    return {
        "file": (file_info.stdout + file_info.stderr).decode("utf-8", errors="replace").strip(),
        "readelf": readelf_text,
        "objdump": objdump_text,
        "required_strings": required_strings,
        "forbidden_strings": [item.decode("ascii") for item in forbidden_strings],
    }


def compile_c_init(source: Path, out_path: Path, build_dir: Path, variant: Variant) -> dict[str, Any]:
    result = run(
        [
            "aarch64-linux-gnu-gcc",
            "-nostdlib",
            "-static",
            "-ffreestanding",
            "-fno-builtin",
            "-fno-stack-protector",
            "-fno-asynchronous-unwind-tables",
            "-fno-unwind-tables",
            "-Os",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-Wl,--build-id=none",
            "-Wl,-e,_start",
            "-Wl,-z,noexecstack",
            f'-DM20_VARIANT_LABEL="{variant.label}"',
            f'-DM20_MARKER="{variant.marker}"',
            f"-DM20_ENABLE_KMSG={1 if variant.kmsg else 0}",
            "-o",
            out_path,
            source,
        ]
    )
    require_ok(result, f"compile {variant.label} init")
    strip = run(["aarch64-linux-gnu-strip", "-s", out_path])
    require_ok(strip, f"strip {variant.label} init")

    file_info = run(["file", out_path])
    require_ok(file_info, f"file {variant.label} init")
    readelf = run(["aarch64-linux-gnu-readelf", "-h", "-l", out_path])
    require_ok(readelf, f"readelf {variant.label} init")
    objdump = run(["aarch64-linux-gnu-objdump", "-d", out_path])
    require_ok(objdump, f"objdump {variant.label} init")
    readelf_text = readelf.stdout.decode("utf-8", errors="replace")
    objdump_text = objdump.stdout.decode("utf-8", errors="replace")
    if "INTERP" in readelf_text or "Requesting program interpreter" in readelf_text:
        raise SystemExit(f"{variant.label} unexpectedly has a program interpreter")
    if "AArch64" not in readelf_text:
        raise SystemExit(f"{variant.label} init is not AArch64")
    if "svc" not in objdump_text:
        raise SystemExit(f"{variant.label} disassembly does not contain svc")
    if not any("mov" in line and "x8" in line and "#0x8e" in line for line in objdump_text.splitlines()):
        raise SystemExit(f"{variant.label} does not load arm64 __NR_reboot (142)")

    required_strings = [
        variant.marker,
        "version=0.1",
        f"variant={variant.label}",
        "runtime=freestanding",
        "raw_syscalls=1",
        "minfs=dev,proc,sys,run",
        f"kmsg_emit={1 if variant.kmsg else 0}",
        "no_modules=1",
        "no_configfs=1",
        "no_usb_acm=1",
        "no_gadget_setup=1",
        "reboot_request=download",
        DOWNLOAD_ARG,
    ]
    if variant.kmsg:
        required_strings.extend(["/dev/kmsg", "phase=kmsg"])
    forbidden_strings = [
        b"ld-linux",
        b"libc.so",
        b"/lib/modules",
        b"finit_module",
        b"modules.load",
        b"ttyGS0",
        b"ss_acm.0",
        b"usb_gadget",
        b"/config",
    ]
    if not variant.kmsg:
        forbidden_strings.extend([b"/dev/kmsg", b"phase=kmsg", b"kmsg_emit=1"])

    binary = out_path.read_bytes()
    for required in required_strings:
        if required.encode("ascii") not in binary:
            raise SystemExit(f"required string missing from {variant.label}: {required}")
    for forbidden in forbidden_strings:
        if forbidden in binary:
            raise SystemExit(f"{variant.label} contains forbidden string: {forbidden!r}")

    (build_dir / f"{variant.label}_init_file.txt").write_bytes(file_info.stdout + file_info.stderr)
    (build_dir / f"{variant.label}_init_readelf.txt").write_text(readelf_text, encoding="utf-8")
    (build_dir / f"{variant.label}_init_objdump.txt").write_text(objdump_text, encoding="utf-8")
    return {
        "file": (file_info.stdout + file_info.stderr).decode("utf-8", errors="replace").strip(),
        "readelf": readelf_text,
        "objdump": objdump_text,
        "required_strings": required_strings,
        "forbidden_strings": [item.decode("ascii") for item in forbidden_strings],
    }


def package_variant(
    *,
    root: Path,
    out_dir: Path,
    base_boot: Path,
    magiskboot: Path,
    odin: Path,
    source: Path,
    nochange_sha: str,
    variant: Variant,
    no_odin_parse_gate: bool,
) -> dict[str, Any]:
    variant_dir = out_dir / variant.label
    build_dir = variant_dir / "build"
    work_dir = variant_dir / "magiskboot-work"
    odin_dir = variant_dir / "odin4"
    patched_unpack_dir = variant_dir / "patched-unpack"
    for directory in (build_dir, work_dir, odin_dir, patched_unpack_dir):
        directory.mkdir(parents=True)

    init_path = build_dir / f"s22plus_init_{variant.label.lower()}"
    if variant.kind == "asm":
        init_info = compile_asm_init(source, init_path, build_dir, variant)
    elif variant.kind == "c":
        init_info = compile_c_init(source, init_path, build_dir, variant)
    else:
        raise SystemExit(f"unknown variant kind: {variant.kind}")

    unpack_text = run_in_dir([magiskboot, "unpack", "-h", base_boot], work_dir, f"magiskboot unpack {variant.label}")
    ramdisk = work_dir / "ramdisk.cpio"
    kernel = work_dir / "kernel"
    header = work_dir / "header"
    original_init = build_dir / "init.magisk.original"
    extract_text = run_in_dir([magiskboot, "cpio", ramdisk, f"extract init {original_init}"], work_dir, f"extract Magisk init {variant.label}")
    original_init_sha = sha256_file(original_init)
    if original_init_sha != EXPECTED_ORIGINAL_MAGISK_INIT_SHA256:
        raise SystemExit(f"{variant.label} original Magisk /init SHA mismatch: {original_init_sha}")

    ramdisk_before = build_dir / "ramdisk.before.cpio"
    shutil.copy2(ramdisk, ramdisk_before)
    ramdisk_before_sha = sha256_file(ramdisk_before)
    cpio_test_before = run([magiskboot, "cpio", ramdisk, "test"], cwd=work_dir).returncode
    if cpio_test_before != 1:
        raise SystemExit(f"{variant.label} expected Magisk ramdisk cpio test rc=1, got {cpio_test_before}")

    patch_text = run_in_dir([magiskboot, "cpio", ramdisk, f"add 750 init {init_path}"], work_dir, f"replace /init {variant.label}")
    cpio_test_after = run([magiskboot, "cpio", ramdisk, "test"], cwd=work_dir).returncode
    if cpio_test_after not in (1, 2):
        raise SystemExit(f"{variant.label} unexpected ramdisk cpio test rc after patch: {cpio_test_after}")

    extracted_replaced = build_dir / "init.replaced"
    run_in_dir([magiskboot, "cpio", ramdisk, f"extract init {extracted_replaced}"], work_dir, f"extract replaced init {variant.label}")
    if sha256_file(extracted_replaced) != sha256_file(init_path):
        raise SystemExit(f"{variant.label} replaced /init does not match compiled init")

    ramdisk_after = build_dir / "ramdisk.after.cpio"
    shutil.copy2(ramdisk, ramdisk_after)
    ramdisk_after_sha = sha256_file(ramdisk_after)
    boot_img = variant_dir / "boot.img"
    repack_text = run_in_dir([magiskboot, "repack", base_boot, boot_img], work_dir, f"magiskboot repack {variant.label}")
    if boot_img.stat().st_size != BOOT_PARTITION_SIZE:
        raise SystemExit(f"{variant.label} patched boot size mismatch: {boot_img.stat().st_size} != {BOOT_PARTITION_SIZE}")

    patched_unpack = run_in_dir([magiskboot, "unpack", "-h", boot_img], patched_unpack_dir, f"unpack patched boot {variant.label}")
    if sha256_file(patched_unpack_dir / "kernel") != sha256_file(kernel):
        raise SystemExit(f"{variant.label} patched boot kernel changed")

    boot_lz4 = odin_dir / "boot.img.lz4"
    write_boot_lz4(boot_img, boot_lz4)
    ap_tar = odin_dir / "AP.tar"
    ap_md5 = odin_dir / "AP.tar.md5"
    write_ap_tar(boot_lz4, ap_tar, ap_md5)
    members = tar_members(ap_md5)
    if members != ["boot.img.lz4"]:
        raise SystemExit(f"{variant.label} AP tar member mismatch: {members}")

    parse_gate_text = ""
    if not no_odin_parse_gate and odin.exists():
        gate = run([odin, "-a", ap_md5, "-d", "/dev/bus/usb/999/999"])
        parse_gate_text = (gate.stdout + gate.stderr).decode("utf-8", errors="replace")
        (odin_dir / "parse_dry_run_invalid_device.txt").write_text(parse_gate_text, encoding="utf-8")

    hashes = {
        "source": sha256_file(source),
        "base_boot": sha256_file(base_boot),
        "nochange_repack_boot": nochange_sha,
        "original_magisk_init": original_init_sha,
        "init": sha256_file(init_path),
        "ramdisk_before": ramdisk_before_sha,
        "ramdisk_after": ramdisk_after_sha,
        "kernel": sha256_file(kernel),
        "header": sha256_file(header),
        "boot_img": sha256_file(boot_img),
        "boot_img_lz4": sha256_file(boot_lz4),
        "ap_tar": sha256_file(ap_tar),
        "ap_tar_md5": sha256_file(ap_md5),
    }
    sizes = {
        "base_boot": base_boot.stat().st_size,
        "init": init_path.stat().st_size,
        "original_magisk_init": original_init.stat().st_size,
        "ramdisk_before": ramdisk_before.stat().st_size,
        "ramdisk_after": ramdisk_after.stat().st_size,
        "boot_img": boot_img.stat().st_size,
        "boot_img_lz4": boot_lz4.stat().st_size,
        "ap_tar": ap_tar.stat().st_size,
        "ap_tar_md5": ap_md5.stat().st_size,
    }
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "target": "SM-S906N/g0q/S906NKSS7FYG8",
        "label": variant.label,
        "purpose": variant.purpose,
        "safety": {
            "boot_only": True,
            "host_only_build": True,
            "live_flash_authorized": False,
            "requires_new_sha_pinned_agents_exception_before_flash": True,
            "base_is_known_booting_magisk_boot": True,
            "construction": "magiskboot unpack/repack; replace only ramdisk /init",
            "mkbootimg_from_scratch": False,
            "runtime": "raw-assembly" if variant.kind == "asm" else "freestanding-raw-syscall",
            "glibc_static_startup": False,
            "no_android_or_magisk_handoff": True,
            "persistent_partition_mount": False,
            "block_device_writes": False,
            "module_insertions": False,
            "module_binary_injection": False,
            "module_list_files_injected_into_boot_ramdisk": 0,
            "configfs_runtime_gadget": False,
            "udc_binding": False,
            "usb_role_force": False,
            "watchdog": "not-touched",
            "kmsg_marker_write": bool(variant.kmsg),
            "auto_reboot": "download",
            "on_reboot_syscall_return": "infinite-park",
        },
        "paths": {
            "variant_dir": display_path(root, variant_dir),
            "source": display_path(root, source),
            "base_boot": display_path(root, base_boot),
            "boot_img": display_path(root, boot_img),
            "ap_tar_md5": display_path(root, ap_md5),
        },
        "hashes": hashes,
        "sizes": sizes,
        "init": init_info,
        "ramdisk": {
            "cpio_test_before_rc": cpio_test_before,
            "cpio_test_after_rc": cpio_test_after,
            "replaced_entry": "init",
            "replaced_entry_mode": "750",
            "only_intended_entry_change": "init",
            "module_files_injected_into_boot_ramdisk": 0,
            "module_list_files_injected_into_boot_ramdisk": 0,
        },
        "magiskboot": {
            "nochange_repack_byte_identical": True,
            "unpack_output": unpack_text,
            "repack_output": repack_text,
            "patched_unpack_output": patched_unpack,
            "extract_output": extract_text,
            "patch_output": patch_text,
        },
        "boot_diff_vs_base": diff_ranges(base_boot, boot_img),
        "tar_members": members,
        "odin_invalid_device_parse_gate": parse_gate_text,
    }
    if variant.label == "M20A_RAW":
        manifest["future_live_interpretation"] = {
            "download_mode_returns": "raw reboot syscall path still works under current operator timing",
            "bootloop_or_no_download": "regression or host/manual-download ambiguity exists below minimal-fs work",
        }
    elif variant.label == "M20B_MINFS":
        manifest["future_live_interpretation"] = {
            "download_mode_returns": "minimal fs setup survived; failure is at or after kmsg marker path",
            "bootloop_or_no_download": "failure is in minimal fs setup or C runtime before kmsg",
        }
    else:
        manifest["future_live_interpretation"] = {
            "download_mode_returns": "minimal fs plus kmsg marker path survived",
            "bootloop_or_no_download": "failure is in or after kmsg marker path before reboot request",
            "retained_marker_found": "candidate reached M20C marker before reboot request",
        }

    (variant_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (variant_dir / "sha256.txt").write_text(
        "".join(f"{value}  {key}\n" for key, value in sorted(hashes.items())),
        encoding="ascii",
    )
    (variant_dir / "sizes.txt").write_text(
        "".join(f"{value:12d}  {key}\n" for key, value in sorted(sizes.items())),
        encoding="ascii",
    )
    (variant_dir / "required_strings.txt").write_text(
        "\n".join(init_info["required_strings"]) + "\n",
        encoding="ascii",
    )
    return manifest


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--base-boot", type=Path, default=DEFAULT_BASE_BOOT)
    parser.add_argument("--raw-source", type=Path, default=DEFAULT_RAW_SOURCE)
    parser.add_argument("--c-source", type=Path, default=DEFAULT_C_SOURCE)
    parser.add_argument("--magiskboot", type=Path, default=DEFAULT_MAGISKBOOT)
    parser.add_argument("--magisk-apk", type=Path, default=DEFAULT_MAGISK_APK)
    parser.add_argument("--odin", type=Path, default=DEFAULT_ODIN)
    parser.add_argument("--force", action="store_true", help="remove an existing output directory first")
    parser.add_argument("--no-odin-parse-gate", action="store_true")
    args = parser.parse_args(argv)

    root = repo_root()
    out_dir = resolve(root, args.out)
    base_boot = resolve(root, args.base_boot)
    raw_source = resolve(root, args.raw_source)
    c_source = resolve(root, args.c_source)
    magiskboot = resolve(root, args.magiskboot)
    magisk_apk = resolve(root, args.magisk_apk)
    odin = resolve(root, args.odin)

    if out_dir.exists():
        if not args.force:
            raise SystemExit(f"output directory exists; pass --force to replace: {out_dir}")
        shutil.rmtree(out_dir)
    common_dir = out_dir / "common"
    nochange_dir = common_dir / "nochange-probe"
    nochange_dir.mkdir(parents=True)
    ensure_magiskboot(magiskboot, magisk_apk)

    base_sha = sha256_file(base_boot)
    if base_sha != EXPECTED_BASE_BOOT_SHA256:
        raise SystemExit(f"base Magisk boot SHA mismatch: {base_sha}")
    if base_boot.stat().st_size != BOOT_PARTITION_SIZE:
        raise SystemExit(f"base boot size mismatch: {base_boot.stat().st_size} != {BOOT_PARTITION_SIZE}")

    nochange_unpack = run_in_dir([magiskboot, "unpack", "-h", base_boot], nochange_dir, "magiskboot no-change unpack")
    nochange_repack = run_in_dir(
        [magiskboot, "repack", base_boot, out_dir / "boot_nochange_repack.img"],
        nochange_dir,
        "magiskboot no-change repack",
    )
    nochange_sha = sha256_file(out_dir / "boot_nochange_repack.img")
    if nochange_sha != base_sha:
        raise SystemExit(f"magiskboot no-change repack is not byte-identical: {nochange_sha} != {base_sha}")

    manifests: dict[str, Any] = {}
    for variant in VARIANTS:
        source = raw_source if variant.source_attr == "raw_source" else c_source
        manifests[variant.label] = package_variant(
            root=root,
            out_dir=out_dir,
            base_boot=base_boot,
            magiskboot=magiskboot,
            odin=odin,
            source=source,
            nochange_sha=nochange_sha,
            variant=variant,
            no_odin_parse_gate=args.no_odin_parse_gate,
        )

    top_manifest = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "target": "SM-S906N/g0q/S906NKSS7FYG8",
        "purpose": "M20 host-only C000 floor split after M19 C000 bootloop/manual-download result",
        "safety": {
            "boot_only": True,
            "host_only_build": True,
            "live_flash_authorized": False,
            "requires_new_sha_pinned_agents_exception_before_flash": True,
            "no_cascading_live_flash_after_m19_bootloop": True,
            "variants": [variant.label for variant in VARIANTS],
        },
        "paths": {
            "out_dir": display_path(root, out_dir),
            "base_boot": display_path(root, base_boot),
            "raw_source": display_path(root, raw_source),
            "c_source": display_path(root, c_source),
            "magiskboot": display_path(root, magiskboot),
        },
        "base": {
            "base_boot_sha256": base_sha,
            "nochange_repack_sha256": nochange_sha,
            "nochange_repack_byte_identical": True,
            "nochange_unpack_output": nochange_unpack,
            "nochange_repack_output": nochange_repack,
        },
        "variants": {
            label: {
                "purpose": manifest["purpose"],
                "marker": next(variant.marker for variant in VARIANTS if variant.label == label),
                "ap_tar_md5_sha256": manifest["hashes"]["ap_tar_md5"],
                "boot_img_sha256": manifest["hashes"]["boot_img"],
                "init_sha256": manifest["hashes"]["init"],
                "ap_tar_md5": manifest["paths"]["ap_tar_md5"],
                "live_flash_authorized": False,
            }
            for label, manifest in manifests.items()
        },
        "future_live_order": [
            "M20A_RAW first, to re-establish raw reboot(download) positive control under current timing",
            "M20B_MINFS only after M20A is operator-clean",
            "M20C_KMSG only after M20B is operator-clean",
        ],
    }
    (out_dir / "manifest.json").write_text(json.dumps(top_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "sha256.txt").write_text(
        "".join(
            f"{item['ap_tar_md5_sha256']}  {label}/odin4/AP.tar.md5\n"
            f"{item['boot_img_sha256']}  {label}/boot.img\n"
            f"{item['init_sha256']}  {label}/init\n"
            for label, item in sorted(top_manifest["variants"].items())
        ),
        encoding="ascii",
    )
    print(json.dumps(top_manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
