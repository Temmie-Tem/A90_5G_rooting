#!/usr/bin/env python3
"""Build the host-only S22+ O3F freestanding generic-ACM candidate."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import build_s22plus_inplace_m23_dts_exact_qmp_park as m23
import s22plus_o2_module_plan as o2
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


DEFAULT_OUT = Path("workspace/private/outputs/s22plus_native_init/o3f_freestanding_acm_v0_1")
DEFAULT_SOURCE = Path("workspace/public/src/native-init/s22plus_init_o3f_freestanding_acm.c")
DEFAULT_PROTOCOL = Path("workspace/public/src/native-init/s22plus_o3_freestanding_protocol.h")
DEFAULT_LOADER = Path("workspace/public/src/native-init/s22plus_o2_loader_core.h")
DEFAULT_METADATA = o2.DEFAULT_METADATA_DIR
DEFAULT_VENDOR_RAMDISK = m23.DEFAULT_VENDOR_RAMDISK
DEFAULT_LZ4 = m23.DEFAULT_LZ4

MARKER = "S22_NATIVE_INIT_O3F_FREESTANDING_ACM"
EXPECTED_PLAN_COUNT = o2.EXPECTED_O3_MINIMAL_ACM_PLAN_COUNT
EXPECTED_PLAN_SHA256 = o2.EXPECTED_O3_MINIMAL_ACM_PLAN_TSV_SHA256


def verify_source_contract(source: Path, protocol: Path) -> dict[str, Any]:
    text = source.read_text(encoding="ascii")
    protocol_text = protocol.read_text(encoding="ascii")
    required = [
        "__attribute__((noreturn)) void _start(void)",
        "phase=entry-pre-mount",
        "s22plus_o2_execute_module_plan",
        "s22plus_o2_scan_proc_modules",
        "S22PLUS_O2_BIND_GATE_COUNT",
        "/config/usb_gadget/g1/functions/acm.usb0",
        "/sys/devices/platform/soc/a600000.ssusb/mode",
        "/config/usb_gadget/g1/UDC",
        "a600000.dwc3",
        "o3f_control_loop(&state)",
        "S22O3FACM01",
    ]
    forbidden = [
        "NR_REBOOT",
        "NR_EXECVE",
        "execve(",
        "system(",
        "functionfs",
        "ffs.adb",
        "ss_acm",
        "max77705",
        "/sys/module/eud/parameters/enable",
        "sysrq",
        "/system/bin/init",
    ]
    missing = [token for token in required if token not in text]
    present = [token for token in forbidden if token.lower() in text.lower()]
    if missing or present:
        raise SystemExit(f"O3F source contract failed missing={missing} forbidden={present}")
    for token in [
        "S22PLUS_O3F_MAX_PAYLOAD 1024U",
        "s22plus_o3f_validate_request",
        "s22plus_o3f_build_response",
        "S22PLUS_O3F_FRAME_CRC",
    ]:
        if token not in protocol_text:
            raise SystemExit(f"O3F protocol contract missing: {token}")
    return {
        "required": required,
        "forbidden_absent": forbidden,
        "entry": "raw _start",
        "protocol_owner": "same freestanding PID1",
    }


def compile_init(
    source: Path,
    output: Path,
    native_dir: Path,
    plan_dir: Path,
    build_dir: Path,
) -> dict[str, Any]:
    command = [
        "aarch64-linux-gnu-gcc",
        "-std=gnu11",
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
        "-I",
        native_dir,
        "-I",
        plan_dir,
        source,
        "-o",
        output,
    ]
    require_ok(run(command), "compile O3F freestanding init")
    require_ok(run(["aarch64-linux-gnu-strip", "-s", output]), "strip O3F init")
    file_result = run(["file", output])
    readelf_result = run(["aarch64-linux-gnu-readelf", "-h", "-l", output])
    objdump_result = run(["aarch64-linux-gnu-objdump", "-d", output])
    undefined_result = run(["aarch64-linux-gnu-nm", "-u", output])
    require_ok(file_result, "file O3F init")
    require_ok(readelf_result, "readelf O3F init")
    require_ok(objdump_result, "objdump O3F init")
    require_ok(undefined_result, "undefined-symbol O3F init")
    file_text = (file_result.stdout + file_result.stderr).decode("utf-8", errors="replace")
    readelf_text = readelf_result.stdout.decode("utf-8", errors="replace")
    objdump_text = objdump_result.stdout.decode("utf-8", errors="replace")
    undefined_text = undefined_result.stdout.decode("utf-8", errors="replace").strip()
    if "ARM aarch64" not in file_text or "statically linked" not in file_text:
        raise SystemExit(f"O3F init is not static AArch64: {file_text.strip()}")
    if "INTERP" in readelf_text or "Requesting program interpreter" in readelf_text:
        raise SystemExit("O3F init unexpectedly has PT_INTERP")
    if undefined_text:
        raise SystemExit(f"O3F init has undefined symbols: {undefined_text}")
    if "svc" not in objdump_text:
        raise SystemExit("O3F init has no raw syscall instruction")
    if output.stat().st_size >= 131072:
        raise SystemExit(f"O3F init unexpectedly large: {output.stat().st_size}")
    binary = output.read_bytes()
    required_strings = [
        MARKER,
        "version=0.2",
        "runtime=freestanding",
        "raw_syscalls=1",
        "phase=entry-pre-mount",
        "plan_count=59",
        "S22O3FACM01",
        "O3 STATUS",
        "gadget_function=acm.usb0",
        "udc=a600000.dwc3",
        "protocol_result=",
    ]
    forbidden_strings = [
        b"ld-linux",
        b"libc.so",
        b"/system/bin/init",
        b"ss_acm",
        b"max77705",
        b"reboot-download",
    ]
    for value in required_strings:
        if value.encode("ascii") not in binary:
            raise SystemExit(f"O3F init required string missing: {value}")
    for value in forbidden_strings:
        if value in binary:
            raise SystemExit(f"O3F init forbidden string present: {value!r}")
    (build_dir / "o3f_init.file.txt").write_text(file_text, encoding="utf-8")
    (build_dir / "o3f_init.readelf.txt").write_text(readelf_text, encoding="utf-8")
    (build_dir / "o3f_init.objdump.txt").write_text(objdump_text, encoding="utf-8")
    return {
        "command": [str(item) for item in command],
        "file": file_text.strip(),
        "sha256": sha256_file(output),
        "size": output.stat().st_size,
        "no_interp": True,
        "undefined_symbols": [],
        "required_strings": required_strings,
        "forbidden_strings_absent": [value.decode("ascii") for value in forbidden_strings],
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--base-boot", type=Path, default=DEFAULT_BASE_BOOT)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--loader", type=Path, default=DEFAULT_LOADER)
    parser.add_argument("--metadata-dir", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--vendor-ramdisk", type=Path, default=DEFAULT_VENDOR_RAMDISK)
    parser.add_argument("--lz4", type=Path, default=DEFAULT_LZ4)
    parser.add_argument("--magiskboot", type=Path, default=DEFAULT_MAGISKBOOT)
    parser.add_argument("--magisk-apk", type=Path, default=DEFAULT_MAGISK_APK)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    root = repo_root()
    out_dir = resolve(root, args.out)
    base_boot = resolve(root, args.base_boot)
    source = resolve(root, args.source)
    protocol = resolve(root, args.protocol)
    loader = resolve(root, args.loader)
    metadata_dir = resolve(root, args.metadata_dir)
    vendor_ramdisk = resolve(root, args.vendor_ramdisk)
    lz4_tool = resolve(root, args.lz4)
    magiskboot = resolve(root, args.magiskboot)
    magisk_apk = resolve(root, args.magisk_apk)
    if out_dir.exists():
        if not args.force:
            raise SystemExit(f"output directory exists; pass --force: {out_dir}")
        shutil.rmtree(out_dir)
    build_dir = out_dir / "build"
    plan_dir = build_dir / "plan"
    work_dir = out_dir / "magiskboot-work"
    nochange_dir = out_dir / "nochange-probe"
    patched_unpack_dir = out_dir / "patched-unpack"
    odin_dir = out_dir / "odin4"
    for directory in (build_dir, plan_dir, work_dir, nochange_dir, patched_unpack_dir, odin_dir):
        directory.mkdir(parents=True, exist_ok=True)

    source_contract = verify_source_contract(source, protocol)
    ensure_magiskboot(magiskboot, magisk_apk)
    base_sha = sha256_file(base_boot)
    if base_sha != EXPECTED_BASE_BOOT_SHA256:
        raise SystemExit(f"base Magisk boot SHA mismatch: {base_sha}")
    if base_boot.stat().st_size != BOOT_PARTITION_SIZE:
        raise SystemExit(f"base boot size mismatch: {base_boot.stat().st_size}")

    metadata = o2.load_metadata(metadata_dir)
    o2.verify_fyg8_pins(metadata)
    plan = o2.build_plan(metadata, o2.O3_MINIMAL_ACM_ROOTS)
    o2.validate_plan_contract(metadata, plan)
    o2.verify_o3_minimal_acm_plan_identity(metadata, plan)
    plan_manifest = o2.write_outputs(root, plan_dir, metadata, plan)
    plan_tsv = plan_dir / "module-plan.tsv"
    plan_header = plan_dir / "module-plan.generated.h"
    if len(plan.modules) != EXPECTED_PLAN_COUNT or sha256_file(plan_tsv) != EXPECTED_PLAN_SHA256:
        raise SystemExit("O3F plan identity changed")

    vendor = m23.extract_vendor_metadata(vendor_ramdisk, lz4_tool, build_dir)
    missing_modules = sorted(set(plan.modules) - set(vendor["ko_names"]))
    if missing_modules:
        raise SystemExit(f"O3F modules absent from vendor_boot: {missing_modules}")
    for name in ["modules.dep", "modules.softdep", "modules.load", "modules.load.recovery", "modules.alias"]:
        if vendor["metadata_hashes"].get(name) != metadata.metadata_hashes.get(name):
            raise SystemExit(f"O3F vendor metadata mismatch: {name}")

    init_out = build_dir / "init"
    init_info = compile_init(source, init_out, source.parent, plan_dir, build_dir)

    run_in_dir([magiskboot, "unpack", "-h", base_boot], nochange_dir, "O3F no-change unpack")
    nochange_boot = out_dir / "boot_nochange_repack.img"
    run_in_dir([magiskboot, "repack", base_boot, nochange_boot], nochange_dir, "O3F no-change repack")
    nochange_sha = sha256_file(nochange_boot)
    if nochange_sha != base_sha:
        raise SystemExit(f"O3F no-change repack differs: {nochange_sha} != {base_sha}")

    unpack_text = run_in_dir([magiskboot, "unpack", "-h", base_boot], work_dir, "O3F unpack")
    ramdisk = work_dir / "ramdisk.cpio"
    kernel = work_dir / "kernel"
    header = work_dir / "header"
    original_init = build_dir / "init.magisk.original"
    run_in_dir([magiskboot, "cpio", ramdisk, f"extract init {original_init}"], work_dir, "O3F extract original init")
    original_init_sha = sha256_file(original_init)
    if original_init_sha != EXPECTED_ORIGINAL_MAGISK_INIT_SHA256:
        raise SystemExit(f"original Magisk /init SHA mismatch: {original_init_sha}")
    ramdisk_before = build_dir / "ramdisk.before.cpio"
    shutil.copy2(ramdisk, ramdisk_before)
    cpio_test_before = run([magiskboot, "cpio", ramdisk, "test"], cwd=work_dir).returncode
    if cpio_test_before != 1:
        raise SystemExit(f"unexpected base ramdisk test rc: {cpio_test_before}")
    patch_text = run_in_dir(
        [magiskboot, "cpio", ramdisk, f"add 750 init {init_out}"],
        work_dir,
        "O3F replace /init",
    )
    cpio_test_after = run([magiskboot, "cpio", ramdisk, "test"], cwd=work_dir).returncode
    if cpio_test_after not in (1, 2):
        raise SystemExit(f"unexpected O3F ramdisk test rc: {cpio_test_after}")
    extracted_init = build_dir / "init.extracted"
    run_in_dir([magiskboot, "cpio", ramdisk, f"extract init {extracted_init}"], work_dir, "O3F verify /init")
    if sha256_file(extracted_init) != sha256_file(init_out):
        raise SystemExit("O3F ramdisk /init differs from compiled artifact")

    ramdisk_after = build_dir / "ramdisk.after.cpio"
    shutil.copy2(ramdisk, ramdisk_after)
    boot_img = out_dir / "boot.img"
    repack_text = run_in_dir([magiskboot, "repack", base_boot, boot_img], work_dir, "O3F repack")
    if boot_img.stat().st_size != BOOT_PARTITION_SIZE:
        raise SystemExit(f"O3F boot size mismatch: {boot_img.stat().st_size}")
    run_in_dir([magiskboot, "unpack", "-h", boot_img], patched_unpack_dir, "O3F unpack patched boot")
    if sha256_file(patched_unpack_dir / "kernel") != sha256_file(kernel):
        raise SystemExit("O3F patched boot kernel changed")
    patched_init = build_dir / "init.patched-boot"
    run_in_dir(
        [magiskboot, "cpio", patched_unpack_dir / "ramdisk.cpio", f"extract init {patched_init}"],
        patched_unpack_dir,
        "O3F extract patched-boot init",
    )
    if sha256_file(patched_init) != sha256_file(init_out):
        raise SystemExit("O3F patched boot does not contain exact init")

    boot_lz4 = odin_dir / "boot.img.lz4"
    ap_tar = odin_dir / "AP.tar"
    ap_md5 = odin_dir / "AP.tar.md5"
    write_boot_lz4(boot_img, boot_lz4)
    write_ap_tar(boot_lz4, ap_tar, ap_md5)
    members = tar_members(ap_md5)
    if members != ["boot.img.lz4"]:
        raise SystemExit(f"O3F AP member mismatch: {members}")

    hashes = {
        "source": sha256_file(source),
        "protocol_header": sha256_file(protocol),
        "loader_header": sha256_file(loader),
        "plan_tsv": sha256_file(plan_tsv),
        "plan_header": sha256_file(plan_header),
        "base_boot": base_sha,
        "nochange_repack_boot": nochange_sha,
        "original_magisk_init": original_init_sha,
        "o3f_init": sha256_file(init_out),
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
        "base_boot": base_boot.stat().st_size,
        "o3f_init": init_out.stat().st_size,
        "ramdisk_before": ramdisk_before.stat().st_size,
        "ramdisk_after": ramdisk_after.stat().st_size,
        "boot_img": boot_img.stat().st_size,
        "boot_img_lz4": boot_lz4.stat().st_size,
        "ap_tar_md5": ap_md5.stat().st_size,
    }
    manifest = {
        "schema": "s22plus_o3f_freestanding_acm_build_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "target": o2.TARGET,
        "purpose": "O3F no-libc direct-PID1 generic ACM control proof",
        "safety": {
            "boot_only": True,
            "host_only_build": True,
            "live_flash_authorized": False,
            "requires_new_sha_pinned_agents_exception_before_flash": True,
            "base_is_known_booting_magisk_boot": True,
            "construction": "magiskboot in-place repack; replace ramdisk /init only",
            "kernel_changed": False,
            "mkbootimg_from_scratch": False,
            "runtime": "freestanding-raw-syscall",
            "glibc_static_startup": False,
            "protocol_in_pid1": True,
            "daemon_exec": False,
            "no_android_or_magisk_handoff": True,
            "auto_reboot": False,
            "reboot_syscall": False,
            "persistent_partition_mount": False,
            "block_device_writes": False,
            "module_binary_injection": False,
            "module_source": "stock vendor_boot /lib/modules",
            "configfs_runtime_gadget": "one generic acm.usb0 function",
            "udc_binding": "a600000.dwc3 only",
            "sysfs_write_allowlist": ["/sys/devices/platform/soc/a600000.ssusb/mode=peripheral"],
            "eud_enable": False,
            "sec_debug_trigger": False,
            "pmic_typec_power_write": False,
        },
        "paths": {
            "out_dir": display_path(root, out_dir),
            "base_boot": display_path(root, base_boot),
            "vendor_ramdisk": display_path(root, vendor_ramdisk),
            "boot_img": display_path(root, boot_img),
            "ap_tar_md5": display_path(root, ap_md5),
        },
        "hashes": hashes,
        "sizes": sizes,
        "plan": {
            "module_count": len(plan.modules),
            "tsv_sha256": hashes["plan_tsv"],
            "header_sha256": hashes["plan_header"],
            "modules": list(plan.modules),
            "roots": list(plan.requested_roots),
            "tolerated_unresolved_softdeps": {
                key: list(value) for key, value in plan.tolerated_unresolved_softdeps.items()
            },
            "manifest": plan_manifest,
        },
        "vendor": {
            "ramdisk_sha256": sha256_file(vendor_ramdisk),
            "ko_count": vendor["ko_count"],
            "all_plan_modules_present": True,
            "metadata_hashes": vendor["metadata_hashes"],
        },
        "source_contract": source_contract,
        "init": init_info,
        "ramdisk": {
            "cpio_test_before_rc": cpio_test_before,
            "cpio_test_after_rc": cpio_test_after,
            "replaced_entry": "init",
            "replaced_entry_mode": "750",
            "added_entries": [],
            "module_files_injected": 0,
        },
        "magiskboot": {
            "nochange_repack_byte_identical": True,
            "unpack_output": unpack_text,
            "repack_output": repack_text,
            "patch_output": patch_text,
        },
        "boot_diff_vs_base": diff_ranges(base_boot, boot_img),
        "tar_members": members,
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_dir / "sha256.txt").write_text(
        "".join(f"{value}  {key}\n" for key, value in sorted(hashes.items())), encoding="ascii"
    )
    (out_dir / "sizes.txt").write_text(
        "".join(f"{value:12d}  {key}\n" for key, value in sorted(sizes.items())), encoding="ascii"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
