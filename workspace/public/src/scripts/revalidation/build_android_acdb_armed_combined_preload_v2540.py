#!/usr/bin/env python3
"""Build V2540 ARM32 armed ACDB tap + ioctl fake preload.

Host-only unit.  The output is one private 32-bit Android shared object that
exports both acdb_ioctl() and ioctl().  Unlike V2538, the acdb_ioctl dumper is
compiled in armed mode: it passes through init-time calls without file I/O and
only starts dumping after a helper calls a90_arm_capture().
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import build_android_acdb_combined_preload_v2538 as base

ROOT = base.ROOT
RUN_ID = "V2540"
BUILD_TAG = "v2540-acdb-armed-combined-preload-host-only"
ACDBTAP_SOURCE_REL = base.ACDBTAP_SOURCE_REL
IOCTL_SOURCE_REL = base.IOCTL_SOURCE_REL
TOOLCHAIN_ROOT = base.TOOLCHAIN_ROOT
DEFAULT_BUILD_ROOT = ROOT / "workspace/private/builds/audio" / BUILD_TAG
DEFAULT_MANIFEST = DEFAULT_BUILD_ROOT / "manifest.json"
ARTIFACT_NAME = "liba90_acdb_armed_combined_preload_v2540.so"
TARGET = base.TARGET
CFLAGS = base.CFLAGS
TAP_EXTRA_CFLAGS = ("-DA90_ACDBTAP_ARMED_CAPTURE=1", "-DA90_ACDBTAP_LOG_ENTER=1")
LDFLAGS = (
    "-shared",
    "--allow-shlib-undefined",
    "-soname",
    ARTIFACT_NAME,
)


def source_state() -> dict[str, Any]:
    tap_source = ROOT / ACDBTAP_SOURCE_REL
    ioctl_source = ROOT / IOCTL_SOURCE_REL
    tap_text = tap_source.read_text(encoding="utf-8", errors="replace") if tap_source.exists() else ""
    ioctl_text = ioctl_source.read_text(encoding="utf-8", errors="replace") if ioctl_source.exists() else ""
    required = {
        "tap_source_exists": tap_source.exists(),
        "ioctl_source_exists": ioctl_source.exists(),
        "tap_exports_acdb_ioctl": "acdb_ioctl(uint32_t cmd" in tap_text,
        "tap_exports_arm_capture": "void a90_arm_capture(void)" in tap_text,
        "tap_armed_macro": "A90_ACDBTAP_ARMED_CAPTURE" in tap_text,
        "tap_unarmed_passthrough": "if (!a90_armed)" in tap_text and "return a90_real_acdb_ioctl" in tap_text,
        "tap_private_raw_dir": "/data/local/tmp/a90-acdb-tap" in tap_text,
        "tap_target_len_4916": "A90_TARGET_OUT_LEN 4916U" in tap_text,
        "tap_exit_after_target": "a90_exit_group(0)" in tap_text,
        "tap_all_zero_guard": "\\\"all_zero\\\":" in tap_text and "a90_is_all_zero" in tap_text,
        "ioctl_exports_ioctl": "int ioctl(int fd, unsigned long request, ...)" in ioctl_text,
        "ioctl_fake_allocate_mode": "A90_ACDB_FAKE_ALLOCATE" in ioctl_text and "fake-success" in ioctl_text,
        "ioctl_fakes_allocate_deallocate_set": (
            "A90_AUDIO_ALLOCATE_CALIBRATION" in ioctl_text
            and "A90_AUDIO_DEALLOCATE_CALIBRATION" in ioctl_text
            and "A90_AUDIO_SET_CALIBRATION" in ioctl_text
        ),
        "ioctl_uses_raw_syscall": "A90_NR_IOCTL 54" in ioctl_text and "a90_syscall3(A90_NR_IOCTL" in ioctl_text,
    }
    prohibited = {
        "tap_opens_msm_audio_cal": "/dev/msm_audio_cal" in tap_text,
        "ioctl_opens_msm_audio_cal": 'open("/dev/msm_audio_cal' in ioctl_text or "open('/dev/msm_audio_cal" in ioctl_text,
        "native_speaker_write": any(token in (tap_text + ioctl_text) for token in ("tinyplay", "tinymix", "AudioTrack")),
        "persistent_magisk_install": "magisk --install-module" in (tap_text + ioctl_text),
    }
    return {
        "sources": [ACDBTAP_SOURCE_REL, IOCTL_SOURCE_REL],
        "required": required,
        "required_ok": all(required.values()),
        "prohibited": prohibited,
        "prohibited_ok": not any(prohibited.values()),
    }


def compile_object(source: Path, obj: Path, *, clang: Path, env: dict[str, str], log_dir: Path, extra: tuple[str, ...] = ()) -> dict[str, Any]:
    command = [str(clang), *CFLAGS, *extra, "-c", str(source), "-o", str(obj)]
    result = base.run(command, env=env)
    stem = obj.stem
    (log_dir / f"{stem}.compile.stdout.txt").write_text(result["stdout"], encoding="utf-8", errors="replace")
    (log_dir / f"{stem}.compile.stderr.txt").write_text(result["stderr"], encoding="utf-8", errors="replace")
    return {k: v for k, v in result.items() if k not in {"stdout", "stderr"}}


def build(build_root: Path, *, clang: Path, lld: Path, readelf: str, file_cmd: str) -> dict[str, Any]:
    obj_dir = build_root / "obj"
    bin_dir = build_root / "bin"
    log_dir = build_root / "logs"
    obj_dir.mkdir(parents=True, exist_ok=True)
    bin_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    host_libraries = base.prepare_host_libraries(build_root)
    env = base.tool_env(host_libraries)
    tap_obj = obj_dir / "libacdbtap_v2475_armed.o"
    ioctl_obj = obj_dir / "a90_ioctl_trace_preload_v2531.o"
    out = bin_dir / ARTIFACT_NAME

    tap_compile = compile_object(ROOT / ACDBTAP_SOURCE_REL, tap_obj, clang=clang, env=env, log_dir=log_dir, extra=TAP_EXTRA_CFLAGS)
    ioctl_compile = compile_object(ROOT / IOCTL_SOURCE_REL, ioctl_obj, clang=clang, env=env, log_dir=log_dir)
    if tap_compile["ok"] and ioctl_compile["ok"]:
        link_cmd = [str(lld), *LDFLAGS, "-o", str(out), str(tap_obj), str(ioctl_obj)]
        link_result = base.run(link_cmd, env=env)
        (log_dir / "link.stdout.txt").write_text(link_result["stdout"], encoding="utf-8", errors="replace")
        (log_dir / "link.stderr.txt").write_text(link_result["stderr"], encoding="utf-8", errors="replace")
        link_result = {k: v for k, v in link_result.items() if k not in {"stdout", "stderr"}}
        if link_result["ok"] and out.exists():
            out.chmod(0o600)
    else:
        link_result = {"ok": False, "skipped": True, "reason": "compile failed"}

    binary: dict[str, Any] = {"path": base.rel(out), "exists": out.exists()}
    if out.exists():
        symbols = base.run([readelf, "-Ws", str(out)], env=env, timeout=30.0)
        dyn = base.run([readelf, "-d", str(out)], env=env, timeout=30.0)
        binary.update({
            "sha256": base.sha256_file(out),
            "size": out.stat().st_size,
            "mode": oct(out.stat().st_mode & 0o777),
            "file": base.run([file_cmd, str(out)], timeout=30.0),
            "symbols": {
                "readelf_ok": symbols["ok"],
                "exports_acdb_ioctl": " acdb_ioctl" in symbols["stdout"],
                "exports_ioctl": " ioctl" in symbols["stdout"],
                "exports_a90_arm_capture": " a90_arm_capture" in symbols["stdout"],
                "undefined_dlsym": " UND dlsym" in symbols["stdout"],
                "undefined_errno": " UND __errno" in symbols["stdout"],
            },
            "dynamic": {
                "readelf_ok": dyn["ok"],
                "soname": f"Library soname: [{ARTIFACT_NAME}]" in dyn["stdout"],
            },
        })
    return {
        "host_libraries": host_libraries,
        "compile": {"acdbtap_armed": tap_compile, "ioctl_trace": ioctl_compile},
        "link": link_result,
        "logs": base.rel(log_dir),
        "binary": binary,
        "ok": bool(
            tap_compile.get("ok")
            and ioctl_compile.get("ok")
            and link_result.get("ok")
            and binary.get("exists")
            and binary.get("symbols", {}).get("exports_acdb_ioctl")
            and binary.get("symbols", {}).get("exports_ioctl")
            and binary.get("symbols", {}).get("exports_a90_arm_capture")
            and binary.get("dynamic", {}).get("soname")
        ),
    }


def manifest(args: argparse.Namespace) -> dict[str, Any]:
    clang = Path(args.clang) if args.clang else TOOLCHAIN_ROOT / "bin/clang"
    lld = Path(args.lld) if args.lld else TOOLCHAIN_ROOT / "bin/ld.lld"
    payload: dict[str, Any] = {
        "run_id": RUN_ID,
        "build_tag": BUILD_TAG,
        "created_at": base.now_iso(),
        "host_only": True,
        "device_action": "none",
        "flash_action": "none",
        "android_action": "none",
        "operator_spec": "docs/OPERATOR_ACDB_IOCTL_INTERPOSE_CAPTURE_SPEC_2026-06-15.md",
        "source_state": source_state(),
        "capture_contract": {
            "artifact": ARTIFACT_NAME,
            "abi": "32-bit armeabi-v7a shared object",
            "exports": ["acdb_ioctl", "ioctl", "a90_arm_capture"],
            "unarmed_policy": "acdb_ioctl pass-through only; no dump, no hash, no file I/O",
            "armed_policy": "dump every out_len>0 and exit after first ret==0 non-zero 4916-byte out buffer",
            "fake_audio_cal_allocate_env": "A90_ACDB_FAKE_ALLOCATE=1",
        },
        "boundaries": {
            "no_native_msm_audio_cal_open": True,
            "no_extra_ioctl_issuance": True,
            "no_speaker_write": True,
            "raw_output_private_only": True,
        },
        "toolchain": {
            "clang": str(clang),
            "lld": str(lld),
            "readelf": args.readelf,
            "file": args.file,
            "cflags": [*CFLAGS, *TAP_EXTRA_CFLAGS],
            "ldflags": list(LDFLAGS),
            "target": TARGET,
        },
        "build_root": base.rel(args.build_root),
    }
    if args.build:
        payload["build"] = build(
            args.build_root,
            clang=clang,
            lld=lld,
            readelf=args.readelf,
            file_cmd=args.file,
        )
    else:
        payload["build"] = {"built": False, "reason": "pass --build to materialize private ARM32 preload"}
    payload["ok"] = bool(payload["source_state"]["required_ok"] and payload["source_state"]["prohibited_ok"] and payload.get("build", {}).get("ok", True))
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
