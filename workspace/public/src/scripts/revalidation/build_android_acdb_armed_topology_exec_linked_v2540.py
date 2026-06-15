#!/usr/bin/env python3
"""Build V2540 ARM32 own-process ACDB armed topology caller.

Host-only unit.  The helper links the stock ACDB closure at process startup,
calls acdb_loader_init_v3(), arms the V2540 acdb_ioctl preload, then calls
acdb_loader_send_common_custom_topology().  It does not issue direct GET
matrices and does not touch speaker playback.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import build_android_acdb_ownprocess_get_exec_linked_v2512 as base

ROOT = base.ROOT
RUN_ID = "V2540"
BUILD_TAG = "v2540-acdb-armed-topology-host-only"
SOURCE_REL = "workspace/public/src/android/acdb_payload_capture/a90_acdb_armed_topology_exec_linked_v2540.c"
TOOLCHAIN_ROOT = base.TOOLCHAIN_ROOT
DEFAULT_BUILD_ROOT = ROOT / "workspace/private/builds/audio" / BUILD_TAG
DEFAULT_MANIFEST = DEFAULT_BUILD_ROOT / "manifest.json"
ARTIFACT_NAME = "a90_acdb_armed_topology_exec_linked_v2540"
TARGET = base.TARGET
CFLAGS = base.CFLAGS
LDFLAGS = base.LDFLAGS
LINK_LIBS = base.LINK_LIBS
VENDOR_LIB_DIR = base.VENDOR_LIB_DIR
REQUIRED_NEEDED = base.REQUIRED_NEEDED


def source_state() -> dict[str, Any]:
    source = ROOT / SOURCE_REL
    text = source.read_text(encoding="utf-8", errors="replace") if source.exists() else ""
    required = {
        "source_exists": source.exists(),
        "custom_start": "void _start(void)" in text,
        "direct_decl_acdb_loader_init_v3": "extern int32_t acdb_loader_init_v3" in text,
        "direct_decl_common_topology": "extern int32_t acdb_loader_send_common_custom_topology" in text,
        "weak_arm_capture": "a90_arm_capture" in text and "__attribute__((weak" in text,
        "acdb_root_audconf_open": 'A90_ACDB_FILES_PATH "/vendor/etc/audconf/OPEN"' in text,
        "calls_init_v3_direct": "acdb_loader_init_v3(A90_ACDB_FILES_PATH, A90_DELTA_DIR, 0U)" in text,
        "arms_after_init": "a90_arm_capture();" in text and "armed_before_common_topology" in text,
        "calls_common_topology_after_arm": "acdb_loader_send_common_custom_topology()" in text,
        "private_event_path": "/data/local/tmp/a90-acdb-ownget/acdb-ownget-events.jsonl" in text,
        "uses_exit_group": "A90_NR_EXIT_GROUP" in text and "a90_syscall1(A90_NR_EXIT_GROUP" in text,
        "raw_syscalls_only": "A90_NR_OPENAT" in text and "A90_NR_WRITE" in text,
        "no_libc_headers": "#include <" not in text,
    }
    prohibited = {
        "direct_acdb_ioctl_matrix": "a90_capture_one" in text or "acdb_ioctl(" in text,
        "dlopen_path": "dlopen" in text or "dlsym" in text or "dlerror" in text,
        "android_linker_namespace_api": "android_dlopen" in text or "android_get_exported_namespace" in text,
        "opens_msm_audio_cal": 'open("/dev/msm_audio_cal' in text or "open('/dev/msm_audio_cal" in text,
        "forbidden_set_ioctl_constant": "0xC00461CB" in text or "0xc00461cb" in text,
        "audio_calibration_ioctl": "AUDIO_SET_CALIBRATION" in text or "AUDIO_ALLOCATE_CALIBRATION" in text,
        "native_speaker_write": "tinyplay" in text or "tinymix" in text or "AudioTrack" in text,
        "persistent_magisk_install": "magisk --install-module" in text,
    }
    return {
        "source": SOURCE_REL,
        "exists": source.exists(),
        "required": required,
        "required_ok": all(required.values()),
        "prohibited": prohibited,
        "prohibited_ok": not any(prohibited.values()),
    }


def build(build_root: Path, *, clang: Path, lld: Path, readelf: str, file_cmd: str) -> dict[str, Any]:
    source = ROOT / SOURCE_REL
    obj_dir = build_root / "obj"
    bin_dir = build_root / "bin"
    log_dir = build_root / "logs"
    obj_dir.mkdir(parents=True, exist_ok=True)
    bin_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    host_libraries = base.prepare_host_libraries(build_root)
    env = base.tool_env(host_libraries)
    obj = obj_dir / "a90_acdb_armed_topology_exec_linked_v2540.o"
    out = bin_dir / ARTIFACT_NAME

    missing = [name for name in REQUIRED_NEEDED if not (VENDOR_LIB_DIR / name).exists()]
    if missing:
        raise RuntimeError(f"missing private ACDB closure libs: {', '.join(missing)}")

    compile_cmd = [str(clang), *CFLAGS, "-c", str(source), "-o", str(obj)]
    compile_result = base.run(compile_cmd, env=env, timeout=180.0)
    (log_dir / "compile.stdout.txt").write_text(compile_result["stdout"], encoding="utf-8", errors="replace")
    (log_dir / "compile.stderr.txt").write_text(compile_result["stderr"], encoding="utf-8", errors="replace")
    if not compile_result["ok"]:
        raise RuntimeError(f"compile failed; see {base.rel(log_dir / 'compile.stderr.txt')}")

    link_cmd = [
        str(lld),
        *LDFLAGS,
        "-L",
        str(VENDOR_LIB_DIR),
        "-o",
        str(out),
        str(obj),
        *LINK_LIBS,
    ]
    link_result = base.run(link_cmd, env=env, timeout=180.0)
    (log_dir / "link.stdout.txt").write_text(link_result["stdout"], encoding="utf-8", errors="replace")
    (log_dir / "link.stderr.txt").write_text(link_result["stderr"], encoding="utf-8", errors="replace")
    if not link_result["ok"]:
        raise RuntimeError(f"link failed; see {base.rel(log_dir / 'link.stderr.txt')}")
    out.chmod(0o600)

    file_result = base.run([file_cmd, str(out)], timeout=10.0)
    readelf_header = base.run([readelf, "-h", str(out)], timeout=30.0)
    readelf_dynamic = base.run([readelf, "-d", str(out)], timeout=30.0)
    readelf_symbols = base.run([readelf, "-Ws", str(out)], timeout=30.0)
    for path, result in (
        (log_dir / "readelf.header.txt", readelf_header),
        (log_dir / "readelf.dynamic.txt", readelf_dynamic),
        (log_dir / "readelf.symbols.txt", readelf_symbols),
    ):
        path.write_text(result["stdout"], encoding="utf-8", errors="replace")
    for result, name in (
        (file_result, "file"),
        (readelf_header, "readelf header"),
        (readelf_dynamic, "readelf dynamic"),
        (readelf_symbols, "readelf symbols"),
    ):
        if not result["ok"]:
            raise RuntimeError(result["stderr"] or result["stdout"] or f"{name} failed")

    dynamic = readelf_dynamic["stdout"]
    symbols = readelf_symbols["stdout"]
    header = readelf_header["stdout"]
    needed = {name: f"Shared library: [{name}]" in dynamic for name in REQUIRED_NEEDED}
    return {
        "host_libraries": host_libraries,
        "commands": {
            "compile": {k: v for k, v in compile_result.items() if k not in {"stdout", "stderr"}},
            "link": {k: v for k, v in link_result.items() if k not in {"stdout", "stderr"}},
        },
        "logs": base.rel(log_dir),
        "artifact": {
            "path": base.rel(out),
            "sha256": base.sha256_file(out),
            "size": out.stat().st_size,
            "file": file_result["stdout"].strip(),
            "target": TARGET,
            "private_generated": True,
            "entry_start": "_start" in symbols,
            "needed": needed,
            "needed_ok": all(needed.values()),
            "undefined_acdb_loader_init_v3": " UND acdb_loader_init_v3" in symbols,
            "undefined_common_topology": " UND acdb_loader_send_common_custom_topology" in symbols,
            "weak_undefined_arm_capture": " WEAK" in symbols and " UND a90_arm_capture" in symbols,
            "interpreter_system_linker": "/system/bin/linker" in file_result["stdout"]
            or "Requesting program interpreter: /system/bin/linker" in header
            or "/system/bin/linker" in dynamic,
            "readelf_header": base.rel(log_dir / "readelf.header.txt"),
            "readelf_dynamic": base.rel(log_dir / "readelf.dynamic.txt"),
            "readelf_symbols": base.rel(log_dir / "readelf.symbols.txt"),
        },
    }


def manifest(args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "decision": "v2540-acdb-armed-topology-host-only",
        "run_id": RUN_ID,
        "build_tag": BUILD_TAG,
        "created_at": base.now_iso(),
        "host_only": True,
        "device_action": "none",
        "flash_action": "none",
        "android_action": "none",
        "source_state": source_state(),
        "vendor_lib_state": base.vendor_lib_state(args.readelf),
        "operator_spec": "docs/OPERATOR_ACDB_IOCTL_INTERPOSE_CAPTURE_SPEC_2026-06-15.md",
        "capture_contract": {
            "artifact": ARTIFACT_NAME,
            "abi": "32-bit armeabi-v7a PIE",
            "load_strategy": "exec-linked DT_NEEDED for staged stock ACDB libraries plus LD_PRELOAD arm callback",
            "required_dt_needed": REQUIRED_NEEDED,
            "acdb_init": {
                "function": "acdb_loader_init_v3",
                "acdb_files_path": "/vendor/etc/audconf/OPEN",
                "delta_file_path": "/data/local/tmp/a90-acdb-ownget/delta",
                "meta_info_type": 0,
                "required_ret": 0,
            },
            "post_init_sequence": ["a90_arm_capture", "acdb_loader_send_common_custom_topology"],
            "capture_dir": "/data/local/tmp/a90-acdb-ownget",
            "public_output": "metadata and SHA-256 only",
            "raw_output": "preload-private /data/local/tmp then workspace/private only",
        },
        "boundaries": {
            "no_direct_acdb_ioctl_get_matrix": True,
            "no_native_msm_audio_cal_ioctls": True,
            "no_native_speaker_write": True,
            "no_hal_injection": True,
            "no_android_live_staging": True,
            "live_execution_blocked_in_this_unit": True,
        },
        "toolchain": {
            "clang": str(args.clang),
            "lld": str(args.lld),
            "readelf": args.readelf,
            "file": args.file,
            "cflags": list(CFLAGS),
            "ldflags": list(LDFLAGS),
            "link_libs": list(LINK_LIBS),
            "target": TARGET,
        },
        "build_root": base.rel(args.build_root),
    }
    if args.build:
        payload["build"] = build(
            args.build_root,
            clang=args.clang,
            lld=args.lld,
            readelf=args.readelf,
            file_cmd=args.file,
        )
    else:
        payload["build"] = {"built": False, "reason": "pass --build to materialize private ARM32 helper"}
    build_payload = payload.get("build", {})
    artifact = build_payload.get("artifact", {}) if isinstance(build_payload, dict) else {}
    payload["ok"] = bool(
        payload["source_state"]["required_ok"]
        and payload["source_state"]["prohibited_ok"]
        and (not args.build or (
            artifact.get("entry_start")
            and artifact.get("needed_ok")
            and artifact.get("undefined_acdb_loader_init_v3")
            and artifact.get("undefined_common_topology")
            and artifact.get("weak_undefined_arm_capture")
        ))
    )
    payload["manifest_path"] = base.rel(args.manifest_path)
    args.manifest_path.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--build-root", type=Path, default=DEFAULT_BUILD_ROOT)
    parser.add_argument("--manifest-path", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--clang", type=Path, default=TOOLCHAIN_ROOT / "bin/clang")
    parser.add_argument("--lld", type=Path, default=TOOLCHAIN_ROOT / "bin/ld.lld")
    parser.add_argument("--readelf", default="readelf")
    parser.add_argument("--file", default="file")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    payload = manifest(parse_args(argv))
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
