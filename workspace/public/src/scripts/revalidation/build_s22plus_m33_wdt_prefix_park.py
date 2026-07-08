#!/usr/bin/env python3
"""Build S22+ M33 watchdog-managed prefix-park native-init matrix.

Host-only. This script does not reboot, flash, or touch a connected device.

M33 splits the failed M32 watchdog+HS-ACM candidate into module-load-only
prefixes. Each variant uses the M31B park runtime shape: direct PID1, minimal
fs setup, dependency-complete module loading, then an indefinite park. It does
not create configfs, expose ACM, request Download mode, or start Android.
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

import build_s22plus_inplace_m23_dts_exact_qmp_park as m23
from build_s22plus_direct_p3_boot import (
    BOOT_PARTITION_SIZE,
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
from build_s22plus_m25_hs_only_usb2_acm import EXPECTED_M25_HS_ONLY_SUBSET
from build_s22plus_m32_wdt_hs_acm import EXPECTED_M32_MODULES


DEFAULT_OUT = Path("workspace/private/outputs/s22plus_native_init/m33_wdt_prefix_park_matrix_v0_1")
DEFAULT_TEMPLATE_SOURCE = Path("workspace/public/src/native-init/s22plus_init_m31b_wdt_managed_park.c")
DEFAULT_VENDOR_RAMDISK = m23.DEFAULT_VENDOR_RAMDISK
DEFAULT_LZ4 = m23.DEFAULT_LZ4

MARKER_PREFIX = "S22_NATIVE_INIT_M33_WDT_PREFIX_PARK"
WATCHDOG_TARGET = "gh_virt_wdt.ko"

M33_EXCLUDED_MODULES = {
    "eud.ko",
    "phy-msm-ssusb-qmp.ko",
    "sec_debug_region.ko",
    "ucsi_glink.ko",
}


@dataclass(frozen=True)
class PrefixVariant:
    label: str
    prefix_count: int
    purpose: str

    @property
    def lower(self) -> str:
        return self.label.lower()

    @property
    def marker(self) -> str:
        return f"{MARKER_PREFIX}_{self.label}"

    @property
    def modules_ramdisk(self) -> str:
        return f"s22plus_m33_{self.lower}_wdt_prefix_park.modules"

    @property
    def generated_source_name(self) -> str:
        return f"s22plus_init_m33_{self.lower}_wdt_prefix_park.c"

    @property
    def init_name(self) -> str:
        return f"s22plus_init_m33_{self.lower}_wdt_prefix_park"


PREFIX_VARIANTS = [
    PrefixVariant("P12", 12, "early clock/interconnect suppliers before IOMMU and USB PHY"),
    PrefixVariant("P18", 18, "adds RPMh/regulator/provider layer before the SCM/watchdog duplicate boundary"),
    PrefixVariant("P25", 25, "reaches secure-buffer/arm-smmu boundary, still no HS PHY target"),
    PrefixVariant("P27", 27, "adds HS/eUSB2 PHY targets, still no DWC3 target"),
    PrefixVariant("P28", 28, "adds DWC3 target, no USB function targets"),
    PrefixVariant("P30", 30, "adds monitor-gadget and ACM function modules, no configfs runtime gadget"),
    PrefixVariant("P40", 40, "full M32 module closure, but park-only and no configfs/ACM setup"),
]


def _variant_by_label(label: str) -> PrefixVariant:
    for variant in PREFIX_VARIANTS:
        if variant.label == label:
            return variant
    raise KeyError(label)


def dependency_complete_wdt_prefix_order(
    *,
    dep_map: dict[str, list[str]],
    recovery_basenames: list[str],
    prefix_count: int,
) -> dict[str, Any]:
    if prefix_count <= 0 or prefix_count > len(EXPECTED_M25_HS_ONLY_SUBSET):
        raise SystemExit(
            f"M33 prefix_count out of range: {prefix_count} not in 1..{len(EXPECTED_M25_HS_ONLY_SUBSET)}"
        )

    order_index = {module: index for index, module in enumerate(recovery_basenames)}
    targets = list(EXPECTED_M25_HS_ONLY_SUBSET[:prefix_count]) + [WATCHDOG_TARGET]
    seen: set[str] = set()
    visiting: set[str] = set()
    ordered: list[str] = []
    blocked_edges: set[str] = set()
    missing: set[str] = set()

    def sort_key(module: str) -> tuple[int, str]:
        return (order_index.get(module, 10**9), module)

    def visit(module: str, consumer: str | None = None) -> None:
        if module in seen:
            return
        if module in M33_EXCLUDED_MODULES:
            blocked_edges.add(f"{consumer or '<root>'}->{module}")
            return
        if module not in dep_map:
            missing.add(module)
            return
        if module in visiting:
            raise SystemExit(f"cycle in modules.dep while visiting {module}")
        visiting.add(module)
        for dep in sorted(dep_map[module], key=sort_key):
            visit(dep, module)
        visiting.remove(module)
        seen.add(module)
        ordered.append(module)

    for target in sorted(targets, key=sort_key):
        visit(target)

    if missing:
        raise SystemExit(f"M33 dependency closure missing modules.dep entries: {sorted(missing)}")
    if blocked_edges:
        raise SystemExit(f"M33 dependency closure hits excluded hard deps: {sorted(blocked_edges)}")

    dependency_violations = {
        module: [dep for dep in dep_map[module] if dep in ordered and ordered.index(dep) > ordered.index(module)]
        for module in ordered
    }
    dependency_violations = {module: deps for module, deps in dependency_violations.items() if deps}
    if dependency_violations:
        raise SystemExit(f"M33 module order violates modules.dep: {dependency_violations}")

    if prefix_count == len(EXPECTED_M25_HS_ONLY_SUBSET) and ordered != EXPECTED_M32_MODULES:
        raise SystemExit(f"M33 full-prefix closure drifted from M32:\nactual={ordered!r}\nexpected={EXPECTED_M32_MODULES!r}")

    module_text = "".join(f"{module}\n" for module in ordered)
    if len(module_text.encode("ascii")) >= 8192:
        raise SystemExit("M33 dependency-complete module list exceeds runtime parser buffer")
    too_long = [module for module in ordered if len(module) >= m23.RUNTIME_MODULE_NAME_BUF]
    if too_long:
        raise SystemExit(f"M33 module basename exceeds runtime parser buffer: {too_long}")

    return {
        "prefix_count": prefix_count,
        "prefix_targets": targets[:-1],
        "watchdog_target": WATCHDOG_TARGET,
        "targets": targets,
        "modules": ordered,
        "module_count": len(ordered),
        "module_text": module_text,
        "module_sha256": None,
        "excluded_modules": sorted(M33_EXCLUDED_MODULES),
        "key_boundaries": {
            "includes_arm_smmu": "arm_smmu.ko" in ordered,
            "includes_hs_phy": "phy-msm-snps-hs.ko" in ordered,
            "includes_eusb2_phy": "phy-msm-snps-eusb2.ko" in ordered,
            "includes_dwc3": "dwc3-msm.ko" in ordered,
            "includes_acm_module": "usb_f_ss_acm.ko" in ordered,
            "includes_monitor_gadget_module": "usb_f_ss_mon_gadget.ko" in ordered,
            "configfs_runtime_gadget": False,
        },
        "stock_recovery_positions": {
            module: recovery_basenames.index(module) + 1
            for module in ordered
            if module in recovery_basenames
        },
        "order_model": "modules.dep topological order with stock modules.load.recovery tie-breaks",
    }


def generate_m33_source(
    template_source: Path,
    generated_source: Path,
    variant: PrefixVariant,
    module_count: int,
) -> str:
    text = template_source.read_text(encoding="utf-8")
    replacements = [
        (
            "Samsung S22+ native-init M31B watchdog-managed park candidate.",
            f"Samsung S22+ native-init M33 {variant.label} watchdog-managed prefix-park candidate.",
        ),
        (
            "This candidate only tests whether loading the stock watchdog dependency\n"
            " * closure removes the bare-PID1 PMIC/PON reset ceiling.",
            "This candidate tests whether a bounded dependency-complete prefix of\n"
            " * the M32 HS-ACM module set is enough to trigger the observed reset.",
        ),
        ("M31B_MODULE_LIMIT", "M33_MODULE_LIMIT"),
        ("S22_NATIVE_INIT_M31B_WDT_MANAGED_PARK", variant.marker),
        ("s22plus_m31b_wdt_managed.modules", variant.modules_ramdisk),
        (
            "module_source=stock_vendor_boot_ramdisk module_list=watchdog_dependency_closure ",
            "module_source=stock_vendor_boot_ramdisk module_list=wdt_prefix_park "
            f"variant={variant.label} prefix_targets={variant.prefix_count} "
            "matrix=m33_no_configfs ",
        ),
        (
            "observation=watchdog-managed-park no_android_handoff=1 no_configfs=1 no_acm=1 ",
            "observation=watchdog-managed-prefix-park no_android_handoff=1 no_configfs=1 no_acm=1 "
            "module_load_only=1 ",
        ),
    ]
    for old, new in replacements:
        if old not in text:
            raise SystemExit(f"M33 source template replacement missing: {old!r}")
        text = text.replace(old, new)

    required = [
        variant.marker,
        variant.modules_ramdisk,
        "module_list=wdt_prefix_park",
        f"variant={variant.label}",
        f"prefix_targets={variant.prefix_count}",
        "matrix=m33_no_configfs",
        "module_load_only=1",
        "no_reboot_request=1",
        "no_download_beacon=1",
        "phase=modules_load_done",
        "phase=park_enter",
    ]
    forbidden = [
        "S22_NATIVE_INIT_M31B_WDT_MANAGED_PARK",
        "s22plus_m31b_wdt_managed.modules",
        "watchdog_dependency_closure",
        "LINUX_REBOOT_CMD_RESTART2",
        "k_download_arg",
        "usb_gadget",
        "ss_acm.0",
        "ttyGS0",
    ]
    for item in required:
        if item not in text:
            raise SystemExit(f"generated M33 source missing required marker: {item}")
    for item in forbidden:
        if item in text:
            raise SystemExit(f"generated M33 source still contains forbidden marker: {item}")

    generated_source.write_text(text, encoding="utf-8")
    return text


def compile_init(source: Path, out_path: Path, build_dir: Path, variant: PrefixVariant, module_count: int) -> dict[str, Any]:
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
            f"-DM33_MODULE_LIMIT={module_count}",
            "-o",
            out_path,
            source,
        ]
    )
    require_ok(result, f"compile M33 {variant.label} watchdog prefix-park init")
    strip = run(["aarch64-linux-gnu-strip", "-s", out_path])
    require_ok(strip, f"strip M33 {variant.label} watchdog prefix-park init")

    file_info = run(["file", out_path])
    require_ok(file_info, f"file M33 {variant.label} init")
    readelf = run(["aarch64-linux-gnu-readelf", "-h", "-l", out_path])
    require_ok(readelf, f"readelf M33 {variant.label} init")
    objdump = run(["aarch64-linux-gnu-objdump", "-d", out_path])
    require_ok(objdump, f"objdump M33 {variant.label} init")
    readelf_text = readelf.stdout.decode("utf-8", errors="replace")
    objdump_text = objdump.stdout.decode("utf-8", errors="replace")
    if "INTERP" in readelf_text or "Requesting program interpreter" in readelf_text:
        raise SystemExit(f"M33 {variant.label} init unexpectedly has a program interpreter")
    if "AArch64" not in readelf_text:
        raise SystemExit(f"M33 {variant.label} init is not AArch64")
    if "svc" not in objdump_text:
        raise SystemExit(f"M33 {variant.label} init disassembly does not contain svc")
    if not any("#0x111" in line and "// #273" in line for line in objdump_text.splitlines()):
        raise SystemExit(f"M33 {variant.label} init does not load arm64 __NR_finit_module (273)")
    if any("mov" in line and "x8" in line and "#0x8e" in line for line in objdump_text.splitlines()):
        raise SystemExit(f"M33 {variant.label} init must not load arm64 __NR_reboot (142)")

    required_strings = [
        variant.marker,
        "version=0.1",
        "runtime=freestanding",
        "raw_syscalls=1",
        f"/{variant.modules_ramdisk}",
        "module_list=wdt_prefix_park",
        f"variant={variant.label}",
        f"prefix_targets={variant.prefix_count}",
        "module_load_only=1",
        "no_configfs=1",
        "no_acm=1",
        "no_reboot_request=1",
        "no_download_beacon=1",
        f"module_count={module_count}",
        "phase=modules_load_done",
        "phase=park_enter",
    ]
    forbidden_strings = [
        b"S22_NATIVE_INIT_M31B_WDT_MANAGED_PARK",
        b"s22plus_m31b_wdt_managed.modules",
        b"reboot_request=download",
        b"ttyGS0",
        b"ss_acm.0",
        b"/config",
        b"usb_gadget",
        b"ld-linux",
        b"libc.so",
    ]
    binary = out_path.read_bytes()
    for required in required_strings:
        if required.encode("ascii") not in binary:
            raise SystemExit(f"required marker missing from M33 {variant.label} /init: {required}")
    for forbidden in forbidden_strings:
        if forbidden in binary:
            raise SystemExit(f"M33 {variant.label} /init contains forbidden string: {forbidden!r}")

    (build_dir / f"{variant.lower}_init_file.txt").write_bytes(file_info.stdout + file_info.stderr)
    (build_dir / f"{variant.lower}_init_readelf.txt").write_text(readelf_text, encoding="utf-8")
    (build_dir / f"{variant.lower}_init_objdump.txt").write_text(objdump_text, encoding="utf-8")
    return {
        "file": (file_info.stdout + file_info.stderr).decode("utf-8", errors="replace").strip(),
        "required_strings": required_strings,
        "readelf_path": f"build/{variant.lower}_init_readelf.txt",
        "objdump_path": f"build/{variant.lower}_init_objdump.txt",
    }


def build_variant(
    *,
    root: Path,
    out_dir: Path,
    base_boot: Path,
    template_source: Path,
    magiskboot: Path,
    vendor_metadata: dict[str, Any],
    variant: PrefixVariant,
) -> dict[str, Any]:
    variant_dir = out_dir / variant.label
    build_dir = variant_dir / "build"
    work_dir = variant_dir / "magiskboot-work"
    patched_unpack_dir = variant_dir / "patched-unpack"
    odin_dir = variant_dir / "odin4"
    for directory in (build_dir, work_dir, patched_unpack_dir, odin_dir):
        directory.mkdir(parents=True)

    closure = dependency_complete_wdt_prefix_order(
        dep_map=vendor_metadata["dep_map"],
        recovery_basenames=vendor_metadata["recovery_basenames"],
        prefix_count=variant.prefix_count,
    )
    module_list = build_dir / variant.modules_ramdisk
    module_list.write_text(str(closure["module_text"]), encoding="ascii")
    closure["module_sha256"] = sha256_file(module_list)

    generated_source = build_dir / variant.generated_source_name
    generate_m33_source(template_source, generated_source, variant, int(closure["module_count"]))

    init_out = build_dir / variant.init_name
    init_info = compile_init(generated_source, init_out, build_dir, variant, int(closure["module_count"]))

    unpack_text = run_in_dir([magiskboot, "unpack", "-h", base_boot], work_dir, f"M33 {variant.label} unpack")
    ramdisk = work_dir / "ramdisk.cpio"
    kernel = work_dir / "kernel"
    header = work_dir / "header"
    original_init = build_dir / "init.magisk.original"
    run_in_dir([magiskboot, "cpio", ramdisk, f"extract init {original_init}"], work_dir, f"M33 {variant.label} extract original init")
    original_init_sha = sha256_file(original_init)
    if original_init_sha != EXPECTED_ORIGINAL_MAGISK_INIT_SHA256:
        raise SystemExit(f"original Magisk /init SHA mismatch for M33 {variant.label}: {original_init_sha}")

    ramdisk_before = build_dir / "ramdisk.before.cpio"
    shutil.copy2(ramdisk, ramdisk_before)
    cpio_test_before = run([magiskboot, "cpio", ramdisk, "test"], cwd=work_dir).returncode
    if cpio_test_before != 1:
        raise SystemExit(f"expected Magisk ramdisk cpio test rc=1 for M33 {variant.label}, got {cpio_test_before}")

    patch_init_text = run_in_dir([magiskboot, "cpio", ramdisk, f"add 750 init {init_out}"], work_dir, f"M33 {variant.label} replace /init")
    patch_modules_text = run_in_dir(
        [magiskboot, "cpio", ramdisk, f"add 640 {variant.modules_ramdisk} {module_list}"],
        work_dir,
        f"M33 {variant.label} add module list",
    )
    cpio_test_after = run([magiskboot, "cpio", ramdisk, "test"], cwd=work_dir).returncode
    if cpio_test_after not in (1, 2):
        raise SystemExit(f"unexpected ramdisk cpio test rc after M33 {variant.label} patch: {cpio_test_after}")

    extracted_init = build_dir / "init.replaced"
    run_in_dir([magiskboot, "cpio", ramdisk, f"extract init {extracted_init}"], work_dir, f"M33 {variant.label} extract replaced init")
    if sha256_file(extracted_init) != sha256_file(init_out):
        raise SystemExit(f"replaced /init does not match compiled M33 {variant.label} init")
    extracted_modules = build_dir / f"{variant.modules_ramdisk}.extracted"
    run_in_dir(
        [magiskboot, "cpio", ramdisk, f"extract {variant.modules_ramdisk} {extracted_modules}"],
        work_dir,
        f"M33 {variant.label} extract module list",
    )
    if sha256_file(extracted_modules) != sha256_file(module_list):
        raise SystemExit(f"replaced M33 {variant.label} module list does not match builder output")

    ramdisk_after = build_dir / "ramdisk.after.cpio"
    shutil.copy2(ramdisk, ramdisk_after)
    boot_img = variant_dir / "boot.img"
    repack_text = run_in_dir([magiskboot, "repack", base_boot, boot_img], work_dir, f"M33 {variant.label} repack patched boot")
    if boot_img.stat().st_size != BOOT_PARTITION_SIZE:
        raise SystemExit(f"M33 {variant.label} patched boot size mismatch: {boot_img.stat().st_size} != {BOOT_PARTITION_SIZE}")
    run_in_dir([magiskboot, "unpack", "-h", boot_img], patched_unpack_dir, f"M33 {variant.label} unpack patched boot")
    if sha256_file(patched_unpack_dir / "kernel") != sha256_file(kernel):
        raise SystemExit(f"M33 {variant.label} patched boot kernel changed")

    boot_lz4 = odin_dir / "boot.img.lz4"
    write_boot_lz4(boot_img, boot_lz4)
    ap_tar = odin_dir / "AP.tar"
    ap_md5 = odin_dir / "AP.tar.md5"
    write_ap_tar(boot_lz4, ap_tar, ap_md5)
    members = tar_members(ap_md5)
    if members != ["boot.img.lz4"]:
        raise SystemExit(f"M33 {variant.label} AP tar member mismatch: {members}")

    hashes = {
        "generated_source": sha256_file(generated_source),
        "base_boot": sha256_file(base_boot),
        "original_magisk_init": original_init_sha,
        "m33_modules": sha256_file(module_list),
        "m33_init": sha256_file(init_out),
        "ramdisk_before": sha256_file(ramdisk_before),
        "ramdisk_after": sha256_file(ramdisk_after),
        "kernel": sha256_file(kernel),
        "header": sha256_file(header),
        "boot_img": sha256_file(boot_img),
        "boot_img_lz4": sha256_file(boot_lz4),
        "ap_tar": sha256_file(ap_tar),
        "ap_tar_md5": sha256_file(ap_md5),
    }
    sizes = {
        "m33_modules": module_list.stat().st_size,
        "m33_init": init_out.stat().st_size,
        "original_magisk_init": original_init.stat().st_size,
        "ramdisk_before": ramdisk_before.stat().st_size,
        "ramdisk_after": ramdisk_after.stat().st_size,
        "boot_img": boot_img.stat().st_size,
        "boot_img_lz4": boot_lz4.stat().st_size,
        "ap_tar": ap_tar.stat().st_size,
        "ap_tar_md5": ap_md5.stat().st_size,
    }

    variant_manifest = {
        "label": variant.label,
        "prefix_count": variant.prefix_count,
        "purpose": variant.purpose,
        "closure": closure,
        "paths": {
            "variant_dir": display_path(root, variant_dir),
            "generated_source": display_path(root, generated_source),
            "boot_img": display_path(root, boot_img),
            "ap_tar_md5": display_path(root, ap_md5),
            "module_list": display_path(root, module_list),
        },
        "hashes": hashes,
        "sizes": sizes,
        "init": init_info,
        "ramdisk": {
            "cpio_test_before_rc": cpio_test_before,
            "cpio_test_after_rc": cpio_test_after,
            "replaced_entry": "init",
            "replaced_entry_mode": "750",
            "added_subset_entry": variant.modules_ramdisk,
            "added_subset_entry_mode": "640",
            "module_files_injected_into_boot_ramdisk": 0,
            "module_list_files_injected_into_boot_ramdisk": 1,
        },
        "magiskboot": {
            "unpack_output": unpack_text,
            "repack_output": repack_text,
            "patch_output": patch_init_text + "\n" + patch_modules_text,
        },
        "boot_diff_vs_base": diff_ranges(base_boot, boot_img),
        "tar_members": members,
    }
    (variant_dir / "manifest.json").write_text(json.dumps(variant_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return variant_manifest


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--base-boot", type=Path, default=DEFAULT_BASE_BOOT)
    parser.add_argument("--template-source", type=Path, default=DEFAULT_TEMPLATE_SOURCE)
    parser.add_argument("--vendor-ramdisk", type=Path, default=DEFAULT_VENDOR_RAMDISK)
    parser.add_argument("--lz4", type=Path, default=DEFAULT_LZ4)
    parser.add_argument("--magiskboot", type=Path, default=DEFAULT_MAGISKBOOT)
    parser.add_argument("--magisk-apk", type=Path, default=DEFAULT_MAGISK_APK)
    parser.add_argument("--variants", nargs="*", default=[variant.label for variant in PREFIX_VARIANTS])
    parser.add_argument("--force", action="store_true", help="remove an existing output directory first")
    args = parser.parse_args(argv)

    root = repo_root()
    out_dir = resolve(root, args.out)
    base_boot = resolve(root, args.base_boot)
    template_source = resolve(root, args.template_source)
    vendor_ramdisk = resolve(root, args.vendor_ramdisk)
    lz4_tool = resolve(root, args.lz4)
    magiskboot = resolve(root, args.magiskboot)
    magisk_apk = resolve(root, args.magisk_apk)
    selected_variants = [_variant_by_label(label) for label in args.variants]

    if out_dir.exists():
        if not args.force:
            raise SystemExit(f"output directory exists; pass --force to replace: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    common_build_dir = out_dir / "build"
    nochange_dir = out_dir / "nochange-probe"
    common_build_dir.mkdir()
    nochange_dir.mkdir()

    ensure_magiskboot(magiskboot, magisk_apk)
    base_sha = sha256_file(base_boot)
    if base_sha != EXPECTED_BASE_BOOT_SHA256:
        raise SystemExit(f"base Magisk boot SHA mismatch: {base_sha}")
    if base_boot.stat().st_size != BOOT_PARTITION_SIZE:
        raise SystemExit(f"base boot size mismatch: {base_boot.stat().st_size} != {BOOT_PARTITION_SIZE}")

    vendor_metadata = m23.extract_vendor_metadata(vendor_ramdisk, lz4_tool, common_build_dir)

    run_in_dir([magiskboot, "unpack", "-h", base_boot], nochange_dir, "M33 no-change unpack")
    run_in_dir([magiskboot, "repack", base_boot, out_dir / "boot_nochange_repack.img"], nochange_dir, "M33 no-change repack")
    nochange_sha = sha256_file(out_dir / "boot_nochange_repack.img")
    if nochange_sha != base_sha:
        raise SystemExit(f"M33 no-change repack is not byte-identical: {nochange_sha} != {base_sha}")

    variant_manifests = [
        build_variant(
            root=root,
            out_dir=out_dir,
            base_boot=base_boot,
            template_source=template_source,
            magiskboot=magiskboot,
            vendor_metadata=vendor_metadata,
            variant=variant,
        )
        for variant in selected_variants
    ]

    hashes: dict[str, str] = {
        "template_source": sha256_file(template_source),
        "base_boot": base_sha,
        "nochange_repack_boot": nochange_sha,
    }
    for variant_manifest in variant_manifests:
        label = variant_manifest["label"]
        for key in ("boot_img", "boot_img_lz4", "ap_tar", "ap_tar_md5", "m33_init", "m33_modules"):
            hashes[f"{label}.{key}"] = variant_manifest["hashes"][key]

    manifest: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "target": "SM-S906N/g0q/S906NKSS7FYG8",
        "purpose": "M33 watchdog-managed prefix-park matrix; localize M32 bootloop before configfs/ACM",
        "matrix": {
            "variants": [
                {
                    "label": variant.label,
                    "prefix_count": variant.prefix_count,
                    "purpose": variant.purpose,
                    "prefix_last_target": EXPECTED_M25_HS_ONLY_SUBSET[variant.prefix_count - 1],
                }
                for variant in selected_variants
            ],
            "source_of_prefix_targets": "EXPECTED_M25_HS_ONLY_SUBSET",
            "full_prefix_matches_m32_modules": any(
                v["label"] == "P40" and v["closure"]["modules"] == EXPECTED_M32_MODULES
                for v in variant_manifests
            ),
            "configfs_runtime_gadget": False,
            "acm_runtime_setup": False,
        },
        "safety": {
            "boot_only": True,
            "host_only_build": True,
            "live_flash_authorized": False,
            "requires_new_sha_pinned_agents_exception_before_flash": True,
            "base_is_known_booting_magisk_boot": True,
            "construction": "magiskboot unpack/repack; replace ramdisk /init and add one text module list per variant",
            "runtime": "freestanding-raw-syscall",
            "mkbootimg_from_scratch": False,
            "no_android_or_magisk_handoff": True,
            "auto_reboot": False,
            "intended_reboot_syscall": False,
            "reboot_request": None,
            "persistent_partition_mount": False,
            "block_device_writes": False,
            "module_binary_injection": False,
            "configfs_runtime_gadget": False,
            "usb_role_force": False,
            "acm": False,
            "watchdog_managed": True,
            "qmp_module_excluded": True,
            "eud_module_excluded": True,
            "observation_model": "candidate should park; operator/host observe survival vs bootloop, then manual Download rollback",
        },
        "vendor": {
            "vendor_ramdisk": display_path(root, vendor_ramdisk),
            "vendor_ramdisk_sha256": sha256_file(vendor_ramdisk),
            "metadata_hashes": vendor_metadata["metadata_hashes"],
            "modules_load_count": vendor_metadata["modules_load_count"],
            "modules_load_recovery_count": vendor_metadata["modules_load_recovery_count"],
            "modules_dep_count": vendor_metadata["modules_dep_count"],
        },
        "paths": {
            "out_dir": display_path(root, out_dir),
            "template_source": display_path(root, template_source),
            "base_boot": display_path(root, base_boot),
        },
        "hashes": hashes,
        "variants": variant_manifests,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "sha256.txt").write_text("".join(f"{value}  {key}\n" for key, value in sorted(hashes.items())), encoding="ascii")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
