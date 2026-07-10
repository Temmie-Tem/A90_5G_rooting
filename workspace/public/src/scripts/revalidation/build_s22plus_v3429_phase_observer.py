#!/usr/bin/env python3
"""Build the host-only S22+ V3429 direct-PID1 phase observer."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import s22plus_v3426_phase_observer_design as observer
import s22plus_v3427_transition_selection as transition
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


SCHEMA = "s22plus_v3429_phase_observer_build_v1"
CONTEXT_SCHEMA = "s22plus_v3429_phase_observer_context_v1"
TARGET = observer.TARGET
DEFAULT_OUT = Path(
    "workspace/private/outputs/s22plus_native_init/v3429_phase_observer_v0_1"
)
DEFAULT_SOURCE = Path(
    "workspace/public/src/native-init/s22plus_init_v3429_phase_observer.c"
)
POSITIVE_CONTROL_REPORT = Path(
    "docs/reports/"
    "NATIVE_INIT_V3428R_S22PLUS_STOCK_TRANSITION_POSITIVE_CONTROL_LIVE_PASS_2026-07-10.md"
)
POSITIVE_CONTROL_REPORT_SHA256 = (
    "21e233829a583b186377cb9aa0b330821e928fa41d13a7ab965cf6e06254ea3d"
)
EXPECTED_KERNEL_OSRELEASE = observer.MODULE_VERMAGIC.split()[0]
RING_MAX_BYTES = transition.MAX_LAST_KMSG_BYTES
RUN_ID_RE = re.compile(r"^[0-9a-f]{32}$")

EXPECTED_SYSCALLS = {
    "mknodat": 33,
    "mkdirat": 34,
    "mount": 40,
    "openat": 56,
    "close": 57,
    "read": 63,
    "write": 64,
    "readlinkat": 78,
    "nanosleep": 101,
    "finit_module": 273,
}

FAILURE_CODES = {
    "sha256_selftest": 1,
    "dev_mkdir": 2,
    "kmsg_mknod": 3,
    "proc_mkdir": 4,
    "proc_mount": 5,
    "sys_mkdir": 6,
    "sysfs_mount": 7,
    "kernel_identity": 8,
    "module_identity": 9,
    "module_load": 10,
    "proc_modules_eof_live": 11,
    "driver_bind_symlink": 12,
    "proc_nodes": 13,
    "baseline_negative": 14,
    "precheck_write": 15,
    "precheck_current_ring": 16,
    "final_write": 17,
    "final_current_ring": 18,
}


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(observer.canonical_json(value)).hexdigest()


def phase_context(
    run_id: str,
    phase: str,
    source_sha256: str,
    base_boot_sha256: str,
) -> str:
    return canonical_sha256(
        {
            "schema": CONTEXT_SCHEMA,
            "target": TARGET,
            "run_id": run_id,
            "phase": phase,
            "source_sha256": source_sha256,
            "base_boot_sha256": base_boot_sha256,
            "module_sha256": observer.MODULE_SHA256,
            "observer_contract_sha256": observer.CONTRACT_SHA256,
            "transition_sha256": transition.TRANSITION_SHA256,
        }
    )


def make_expectation(
    run_id: str,
    source_sha256: str,
    base_boot_sha256: str,
) -> observer.MarkerExpectation:
    return observer.make_expectation(
        run_id,
        phase_context(
            run_id,
            observer.PHASE_PRECHECK,
            source_sha256,
            base_boot_sha256,
        ),
        phase_context(
            run_id,
            observer.PHASE_FINAL,
            source_sha256,
            base_boot_sha256,
        ),
    )


def marker_record(
    expectation: observer.MarkerExpectation,
    source_sha256: str,
    base_boot_sha256: str,
) -> dict[str, Any]:
    precheck = observer.encode_marker(expectation, observer.PHASE_PRECHECK)
    final = observer.encode_marker(expectation, observer.PHASE_FINAL)
    return {
        "schema": "s22plus_v3429_expected_markers_v1",
        "target": TARGET,
        "run_id": expectation.run_id,
        "context_schema": CONTEXT_SCHEMA,
        "source_sha256": source_sha256,
        "base_boot_sha256": base_boot_sha256,
        "module_sha256": expectation.module_sha256,
        "observer_contract_sha256": expectation.contract_sha256,
        "transition_sha256": transition.TRANSITION_SHA256,
        "precheck_context_sha256": expectation.precheck_context_sha256,
        "final_context_sha256": expectation.final_context_sha256,
        "precheck_frame": precheck.decode("ascii"),
        "precheck_frame_size": len(precheck),
        "precheck_frame_sha256": hashlib.sha256(precheck).hexdigest(),
        "final_frame": final.decode("ascii"),
        "final_frame_size": len(final),
        "final_frame_sha256": hashlib.sha256(final).hexdigest(),
        "raw_run_token": f"run={expectation.run_id}",
    }


def render_generated_header(record: dict[str, Any]) -> str:
    module_bytes = bytes.fromhex(observer.MODULE_SHA256)
    digest_initializer = ", ".join(f"0x{value:02x}" for value in module_bytes)
    return "\n".join(
        [
            "#ifndef S22PLUS_V3429_PHASE_OBSERVER_GENERATED_H",
            "#define S22PLUS_V3429_PHASE_OBSERVER_GENERATED_H",
            "",
            f'#define V3429_RUN_ID "{record["run_id"]}"',
            f'#define V3429_RAW_RUN_TOKEN "{record["raw_run_token"]}"',
            f'#define V3429_RAW_RUN_TOKEN_LEN {len(record["raw_run_token"])}U',
            f'#define V3429_PRECHECK_FRAME "{record["precheck_frame"]}"',
            f'#define V3429_PRECHECK_FRAME_LEN {record["precheck_frame_size"]}U',
            f'#define V3429_FINAL_FRAME "{record["final_frame"]}"',
            f'#define V3429_FINAL_FRAME_LEN {record["final_frame_size"]}U',
            f'#define V3429_MODULE_SIZE {observer.MODULE_SIZE}U',
            f"#define V3429_MODULE_SHA256_BYTES {{{digest_initializer}}}",
            f'#define V3429_KERNEL_OSRELEASE "{EXPECTED_KERNEL_OSRELEASE}"',
            f"#define V3429_RING_MAX_BYTES {RING_MAX_BYTES}U",
            "",
            "#endif",
            "",
        ]
    )


def verify_source_contract(source: Path) -> dict[str, Any]:
    text = source.read_text(encoding="ascii")
    required = [
        "__attribute__((noreturn)) void _start(void)",
        "V3429_RING_MAX_BYTES + 1U",
        "v3429_verify_module_identity",
        "v3429_verify_proc_modules",
        "v3429_symlink_present",
        "v3429_read_snapshot",
        "v3429_classify_snapshot(0U, 0U, 0U, 0)",
        "v3429_classify_snapshot(1U, 0U, 1U, 0)",
        "v3429_classify_snapshot(1U, 1U, 2U, 1)",
        "v3429_emit_frame(V3429_PRECHECK_FRAME",
        "v3429_emit_frame(V3429_FINAL_FRAME",
        "v3429_quiet_park();",
        "V3429_SHA256_SELFTEST_ONLY",
        "V3429_FAILURE_SELFTEST_ONLY",
        "NR_FINIT_MODULE",
        "NR_READLINKAT",
    ]
    forbidden = [
        "/config/",
        "usb_gadget",
        "acm.usb0",
        "a600000",
        "sec_debug",
        "sysrq",
        "watchdog",
        "NR_REBOOT",
        "NR_CLONE",
        "/dev/block",
        "/data/",
        "/system/",
        "execve",
    ]
    missing = [token for token in required if token not in text]
    present = [token for token in forbidden if token.lower() in text.lower()]
    if missing or present:
        raise SystemExit(
            f"V3429 source contract failed missing={missing} forbidden={present}"
        )
    if text.count("v3429_load_module()") != 1:
        raise SystemExit("V3429 must call the one-module loader exactly once")
    if text.count("v3429_emit_frame(V3429_PRECHECK_FRAME") != 1:
        raise SystemExit("V3429 PRECHECK call count mismatch")
    if text.count("v3429_emit_frame(V3429_FINAL_FRAME") != 1:
        raise SystemExit("V3429 FINAL call count mismatch")
    return {
        "required": required,
        "forbidden_absent": forbidden,
        "module_load_call_count": 1,
        "precheck_emit_call_count": 1,
        "final_emit_call_count": 1,
        "all_paths_park": True,
    }


def compiler_command(
    source: Path,
    generated_dir: Path,
    output: Path,
    *,
    selftest: str | None,
) -> list[str | Path]:
    command: list[str | Path] = [
        "aarch64-linux-gnu-gcc",
        "-std=gnu11",
        "-nostdlib",
        "-static",
        "-ffreestanding",
        "-fno-builtin",
        "-fno-tree-loop-distribute-patterns",
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
        generated_dir,
    ]
    if selftest is not None:
        defines = {
            "sha256": "V3429_SHA256_SELFTEST_ONLY",
            "failure": "V3429_FAILURE_SELFTEST_ONLY",
        }
        if selftest not in defines:
            raise ValueError(f"unknown V3429 selftest: {selftest}")
        command.extend(
            ["-Wno-unused-function", f"-D{defines[selftest]}=1"]
        )
    command.extend([source, "-o", output])
    return command


def compile_init(
    source: Path,
    generated_dir: Path,
    output: Path,
    build_dir: Path,
    record: dict[str, Any],
) -> dict[str, Any]:
    selftest = build_dir / "sha256-selftest"
    require_ok(
        run(compiler_command(source, generated_dir, selftest, selftest="sha256")),
        "compile V3429 SHA256 selftest",
    )
    selftest_result = run(["qemu-aarch64", selftest])
    require_ok(selftest_result, "run V3429 SHA256 known-vector selftest")

    failure_selftest = build_dir / "failure-render-selftest"
    require_ok(
        run(
            compiler_command(
                source,
                generated_dir,
                failure_selftest,
                selftest="failure",
            )
        ),
        "compile V3429 failure-render selftest",
    )
    require_ok(
        run(["qemu-aarch64", failure_selftest]),
        "run V3429 full-run-token failure-render selftest",
    )

    command = compiler_command(source, generated_dir, output, selftest=None)
    require_ok(run(command), "compile V3429 init")
    require_ok(run(["aarch64-linux-gnu-strip", "-s", output]), "strip V3429 init")
    file_result = run(["file", output])
    readelf_result = run(["aarch64-linux-gnu-readelf", "-h", "-l", output])
    objdump_result = run(["aarch64-linux-gnu-objdump", "-d", output])
    undefined_result = run(["aarch64-linux-gnu-nm", "-u", output])
    for result, label in (
        (file_result, "file V3429 init"),
        (readelf_result, "readelf V3429 init"),
        (objdump_result, "objdump V3429 init"),
        (undefined_result, "undefined V3429 init"),
    ):
        require_ok(result, label)
    file_text = (file_result.stdout + file_result.stderr).decode(
        "utf-8", errors="replace"
    )
    readelf_text = readelf_result.stdout.decode("utf-8", errors="replace")
    objdump_text = objdump_result.stdout.decode("utf-8", errors="replace")
    undefined_text = undefined_result.stdout.decode("utf-8", errors="replace").strip()
    if "ARM aarch64" not in file_text or "statically linked" not in file_text:
        raise SystemExit(f"V3429 init is not static AArch64: {file_text.strip()}")
    if "INTERP" in readelf_text or "Requesting program interpreter" in readelf_text:
        raise SystemExit("V3429 init unexpectedly has PT_INTERP")
    if undefined_text:
        raise SystemExit(f"V3429 init has undefined symbols: {undefined_text}")
    if output.stat().st_size >= 131072:
        raise SystemExit(f"V3429 init unexpectedly large: {output.stat().st_size}")
    if "svc" not in objdump_text:
        raise SystemExit("V3429 init has no raw syscall instruction")
    for name, number in EXPECTED_SYSCALLS.items():
        needle = f"#0x{number:x}"
        if not any(
            "mov" in line
            and ("x8" in line or "x0" in line)
            and needle in line
            for line in objdump_text.splitlines()
        ):
            raise SystemExit(f"V3429 init lacks arm64 __NR_{name} ({number})")
    for number, name in ((94, "exit_group"), (142, "reboot"), (220, "clone")):
        needle = f"#0x{number:x}"
        if any(
            "mov" in line
            and ("x8" in line or "x0" in line)
            and needle in line
            for line in objdump_text.splitlines()
        ):
            raise SystemExit(f"V3429 runtime unexpectedly loads __NR_{name} ({number})")
    binary = output.read_bytes()
    required_strings = [
        record["precheck_frame"],
        record["final_frame"],
        record["raw_run_token"],
        "/lib/modules/sec_log_buf.ko",
        observer.DRIVER_BIND,
        "/proc/ap_klog",
        "/proc/last_kmsg",
        EXPECTED_KERNEL_OSRELEASE,
    ]
    forbidden_strings = [
        b"/config/",
        b"usb_gadget",
        b"sysrq",
        b"watchdog",
        b"/dev/block",
        b"/system/bin/init",
    ]
    for value in required_strings:
        if value.encode("ascii") not in binary:
            raise SystemExit(f"V3429 init required string missing: {value}")
    for value in forbidden_strings:
        if value in binary:
            raise SystemExit(f"V3429 init forbidden string present: {value!r}")
    (build_dir / "v3429_init.file.txt").write_text(file_text, encoding="utf-8")
    (build_dir / "v3429_init.readelf.txt").write_text(
        readelf_text, encoding="utf-8"
    )
    (build_dir / "v3429_init.objdump.txt").write_text(
        objdump_text, encoding="utf-8"
    )
    return {
        "command": [str(item) for item in command],
        "file": file_text.strip(),
        "sha256": sha256_file(output),
        "size": output.stat().st_size,
        "no_interp": True,
        "undefined_symbols": [],
        "runtime_syscalls": EXPECTED_SYSCALLS,
        "forbidden_syscalls_absent": ["exit_group", "reboot", "clone"],
        "sha256_known_vector_qemu": True,
        "failure_full_run_token_qemu": True,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--base-boot", type=Path, default=DEFAULT_BASE_BOOT)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--magiskboot", type=Path, default=DEFAULT_MAGISKBOOT)
    parser.add_argument("--magisk-apk", type=Path, default=DEFAULT_MAGISK_APK)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    if not RUN_ID_RE.fullmatch(args.run_id):
        raise SystemExit("--run-id must be exactly 32 lowercase hex characters")

    root = repo_root()
    out_dir = resolve(root, args.out)
    base_boot = resolve(root, args.base_boot)
    source = resolve(root, args.source)
    magiskboot = resolve(root, args.magiskboot)
    magisk_apk = resolve(root, args.magisk_apk)
    if out_dir.exists():
        if not args.force:
            raise SystemExit(f"output directory exists; pass --force: {out_dir}")
        shutil.rmtree(out_dir)
    build_dir = out_dir / "build"
    generated_dir = build_dir / "generated"
    work_dir = out_dir / "magiskboot-work"
    nochange_dir = out_dir / "nochange-probe"
    patched_unpack_dir = out_dir / "patched-unpack"
    odin_dir = out_dir / "odin4"
    for directory in (
        build_dir,
        generated_dir,
        work_dir,
        nochange_dir,
        patched_unpack_dir,
        odin_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    design = observer.build_design(root)
    selection = transition.build_selection(root)
    if design["contract_sha256"] != observer.CONTRACT_SHA256:
        raise SystemExit("V3426 observer contract mismatch")
    if selection["transition_sha256"] != transition.TRANSITION_SHA256:
        raise SystemExit("V3427 transition contract mismatch")
    report = root / POSITIVE_CONTROL_REPORT
    if sha256_file(report) != POSITIVE_CONTROL_REPORT_SHA256:
        raise SystemExit("V3428R positive-control report identity mismatch")
    source_contract = verify_source_contract(source)
    source_sha = sha256_file(source)
    module = root / observer.MODULE_DIR / observer.MODULE_NAME
    if module.stat().st_size != observer.MODULE_SIZE:
        raise SystemExit("V3429 sec_log_buf.ko size mismatch")
    if sha256_file(module) != observer.MODULE_SHA256:
        raise SystemExit("V3429 sec_log_buf.ko SHA256 mismatch")
    ensure_magiskboot(magiskboot, magisk_apk)
    base_sha = sha256_file(base_boot)
    if base_sha != EXPECTED_BASE_BOOT_SHA256:
        raise SystemExit(f"base Magisk boot SHA mismatch: {base_sha}")
    if base_boot.stat().st_size != BOOT_PARTITION_SIZE:
        raise SystemExit(f"base boot size mismatch: {base_boot.stat().st_size}")

    expectation = make_expectation(args.run_id, source_sha, base_sha)
    expected = marker_record(expectation, source_sha, base_sha)
    expected_path = out_dir / "expected_markers.json"
    expected_path.write_text(
        json.dumps(expected, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    generated_header = generated_dir / "s22plus_v3429_phase_observer.generated.h"
    generated_header.write_text(render_generated_header(expected), encoding="ascii")

    init_out = build_dir / "init"
    init_info = compile_init(source, generated_dir, init_out, build_dir, expected)

    run_in_dir([magiskboot, "unpack", "-h", base_boot], nochange_dir, "V3429 no-change unpack")
    nochange_boot = out_dir / "boot_nochange_repack.img"
    run_in_dir(
        [magiskboot, "repack", base_boot, nochange_boot],
        nochange_dir,
        "V3429 no-change repack",
    )
    nochange_sha = sha256_file(nochange_boot)
    if nochange_sha != base_sha:
        raise SystemExit(f"V3429 no-change repack differs: {nochange_sha}")

    unpack_text = run_in_dir(
        [magiskboot, "unpack", "-h", base_boot], work_dir, "V3429 unpack"
    )
    ramdisk = work_dir / "ramdisk.cpio"
    kernel = work_dir / "kernel"
    original_init = build_dir / "init.magisk.original"
    run_in_dir(
        [magiskboot, "cpio", ramdisk, f"extract init {original_init}"],
        work_dir,
        "V3429 extract original init",
    )
    if sha256_file(original_init) != EXPECTED_ORIGINAL_MAGISK_INIT_SHA256:
        raise SystemExit("V3429 original Magisk init mismatch")
    ramdisk_before = build_dir / "ramdisk.before.cpio"
    shutil.copy2(ramdisk, ramdisk_before)
    cpio_before = run([magiskboot, "cpio", ramdisk, "test"], cwd=work_dir).returncode
    if cpio_before != 1:
        raise SystemExit(f"V3429 base ramdisk test rc mismatch: {cpio_before}")
    patch_text = run_in_dir(
        [magiskboot, "cpio", ramdisk, f"add 750 init {init_out}"],
        work_dir,
        "V3429 replace init",
    )
    cpio_after = run([magiskboot, "cpio", ramdisk, "test"], cwd=work_dir).returncode
    if cpio_after not in (1, 2):
        raise SystemExit(f"V3429 patched ramdisk test rc mismatch: {cpio_after}")
    extracted_init = build_dir / "init.extracted"
    run_in_dir(
        [magiskboot, "cpio", ramdisk, f"extract init {extracted_init}"],
        work_dir,
        "V3429 verify init",
    )
    if sha256_file(extracted_init) != sha256_file(init_out):
        raise SystemExit("V3429 ramdisk init mismatch")
    ramdisk_after = build_dir / "ramdisk.after.cpio"
    shutil.copy2(ramdisk, ramdisk_after)

    boot_img = out_dir / "boot.img"
    repack_text = run_in_dir(
        [magiskboot, "repack", base_boot, boot_img], work_dir, "V3429 repack"
    )
    if boot_img.stat().st_size != BOOT_PARTITION_SIZE:
        raise SystemExit(f"V3429 boot size mismatch: {boot_img.stat().st_size}")
    run_in_dir(
        [magiskboot, "unpack", "-h", boot_img],
        patched_unpack_dir,
        "V3429 unpack patched",
    )
    if sha256_file(patched_unpack_dir / "kernel") != sha256_file(kernel):
        raise SystemExit("V3429 patched boot kernel changed")
    patched_init = build_dir / "init.patched-boot"
    run_in_dir(
        [
            magiskboot,
            "cpio",
            patched_unpack_dir / "ramdisk.cpio",
            f"extract init {patched_init}",
        ],
        patched_unpack_dir,
        "V3429 extract patched init",
    )
    if sha256_file(patched_init) != sha256_file(init_out):
        raise SystemExit("V3429 patched boot init mismatch")

    boot_lz4 = odin_dir / "boot.img.lz4"
    ap_tar = odin_dir / "AP.tar"
    ap_md5 = odin_dir / "AP.tar.md5"
    write_boot_lz4(boot_img, boot_lz4)
    write_ap_tar(boot_lz4, ap_tar, ap_md5)
    members = tar_members(ap_md5)
    if members != ["boot.img.lz4"]:
        raise SystemExit(f"V3429 AP member mismatch: {members}")

    hashes = {
        "source": source_sha,
        "generated_header": sha256_file(generated_header),
        "expected_markers": sha256_file(expected_path),
        "positive_control_report": sha256_file(report),
        "sec_log_buf_ko": sha256_file(module),
        "base_boot": base_sha,
        "nochange_repack_boot": nochange_sha,
        "original_magisk_init": sha256_file(original_init),
        "init": sha256_file(init_out),
        "ramdisk_before": sha256_file(ramdisk_before),
        "ramdisk_after": sha256_file(ramdisk_after),
        "kernel": sha256_file(kernel),
        "boot_img": sha256_file(boot_img),
        "boot_img_lz4": sha256_file(boot_lz4),
        "ap_tar": sha256_file(ap_tar),
        "ap_tar_md5": sha256_file(ap_md5),
    }
    manifest = {
        "schema": SCHEMA,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace(
            "+00:00", "Z"
        ),
        "target": TARGET,
        "purpose": "direct-PID1 V3426 Stage-A retained-ring phase observer",
        "run_id": args.run_id,
        "paths": {
            "out_dir": display_path(root, out_dir),
            "source": display_path(root, source),
            "base_boot": display_path(root, base_boot),
            "boot_img": display_path(root, boot_img),
            "ap_tar_md5": display_path(root, ap_md5),
            "expected_markers": display_path(root, expected_path),
        },
        "hashes": hashes,
        "sizes": {
            "init": init_out.stat().st_size,
            "boot_img": boot_img.stat().st_size,
            "boot_img_lz4": boot_lz4.stat().st_size,
            "ap_tar_md5": ap_md5.stat().st_size,
        },
        "contracts": {
            "observer_sha256": observer.CONTRACT_SHA256,
            "transition_sha256": transition.TRANSITION_SHA256,
            "positive_control_report_sha256": POSITIVE_CONTROL_REPORT_SHA256,
        },
        "expected_markers": expected,
        "source_contract": source_contract,
        "failure_codes": FAILURE_CODES,
        "init": init_info,
        "ramdisk": {
            "cpio_test_before_rc": cpio_before,
            "cpio_test_after_rc": cpio_after,
            "replaced_entry": "init",
            "replaced_entry_mode": "750",
            "added_entries": [],
            "module_binary_injection": False,
            "module_source": "untouched vendor_boot /lib/modules/sec_log_buf.ko",
        },
        "magiskboot": {
            "nochange_repack_byte_identical": True,
            "unpack_output": unpack_text,
            "repack_output": repack_text,
            "patch_output": patch_text,
        },
        "boot_diff_vs_base": diff_ranges(base_boot, boot_img),
        "tar_members": members,
        "safety": {
            "host_only_build": True,
            "live_flash_authorized": False,
            "requires_new_sha_pinned_agents_exception_before_flash": True,
            "boot_only": True,
            "kernel_changed": False,
            "construction": "magiskboot in-place repack; replace ramdisk /init only",
            "runtime": "freestanding raw-syscall direct PID1",
            "pid1_never_exits": True,
            "success_state": "quiet park after exact G11 self-gate",
            "failure_state": "one run-bound failure diagnostic then quiet park",
            "module_load_allowlist": [observer.MODULE_NAME],
            "volatile_mounts": ["proc", "sysfs"],
            "kmsg_run_writes": [observer.PHASE_PRECHECK, observer.PHASE_FINAL],
            "sysfs_write": False,
            "configfs_write": False,
            "usb_setup": False,
            "panic": False,
            "watchdog": False,
            "reboot_syscall": False,
            "block_device_write": False,
            "persistent_partition_mount": False,
            "android_or_magisk_handoff": False,
            "candidate_transition": False,
        },
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_dir / "sha256.txt").write_text(
        "".join(f"{value}  {key}\n" for key, value in sorted(hashes.items())),
        encoding="ascii",
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
