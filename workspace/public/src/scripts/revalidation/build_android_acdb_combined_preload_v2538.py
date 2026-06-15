#!/usr/bin/env python3
"""Build V2538 ARM32 combined ACDB tap + ioctl fake preload.

Host-only unit.  The output is one private 32-bit Android shared object that
exports both acdb_ioctl() and ioctl().  It links the already-validated V2475
acdb_ioctl tap object and the V2531 ioctl trace/fake object into one preload so
Android linker multi-LD_PRELOAD behavior is no longer part of the measurement.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[5]
RUN_ID = "V2538"
BUILD_TAG = "v2538-acdb-combined-preload-host-only"
ACDBTAP_SOURCE_REL = "workspace/public/src/android/acdb_payload_capture/libacdbtap_v2475.c"
IOCTL_SOURCE_REL = "workspace/public/src/android/acdb_payload_capture/a90_ioctl_trace_preload_v2531.c"
TOOLCHAIN_ROOT = ROOT / "workspace/private/inputs/toolchains/llvm-arm-toolchain-ship-10.0"
DEFAULT_BUILD_ROOT = ROOT / "workspace/private/builds/audio" / BUILD_TAG
DEFAULT_MANIFEST = DEFAULT_BUILD_ROOT / "manifest.json"
ARTIFACT_NAME = "liba90_acdb_combined_preload_v2538.so"
TARGET = "armv7a-linux-androideabi29"
CFLAGS = (
    "--target=armv7a-linux-androideabi29",
    "-fPIC",
    "-ffreestanding",
    "-fno-builtin",
    "-fno-stack-protector",
    "-fvisibility=hidden",
    "-marm",
    "-Os",
    "-Wall",
    "-Wextra",
)
LDFLAGS = (
    "-shared",
    "--allow-shlib-undefined",
    "-soname",
    ARTIFACT_NAME,
)


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(command: list[str], *, cwd: Path = ROOT, env: dict[str, str] | None = None, timeout: float = 180.0) -> dict[str, Any]:
    started = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    return {
        "command": command,
        "cwd": rel(cwd),
        "rc": completed.returncode,
        "ok": completed.returncode == 0,
        "elapsed_sec": round(time.monotonic() - started, 3),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def find_host_libxml2() -> Path | None:
    for path in (Path("/usr/lib/x86_64-linux-gnu/libxml2.so.16"), Path("/lib/x86_64-linux-gnu/libxml2.so.16")):
        if path.exists():
            return path
    return None


def prepare_host_libraries(build_root: Path) -> dict[str, Any]:
    host_lib_dir = build_root / "host-libs"
    host_lib_dir.mkdir(parents=True, exist_ok=True)
    linked: dict[str, str] = {}

    libtinfo = ROOT / "workspace/private/inputs/toolchains/compat-libs/libtinfo.so.5"
    if not libtinfo.exists():
        fallback = ROOT / "tmp/relibs/libtinfo.so.5"
        if fallback.exists():
            libtinfo = fallback
    if libtinfo.exists():
        target = host_lib_dir / "libtinfo.so.5"
        if target.exists() or target.is_symlink():
            target.unlink()
        target.symlink_to(libtinfo)
        linked["libtinfo.so.5"] = rel(libtinfo)

    libxml2 = find_host_libxml2()
    if libxml2 is not None:
        target = host_lib_dir / "libxml2.so.2"
        if target.exists() or target.is_symlink():
            target.unlink()
        target.symlink_to(libxml2)
        linked["libxml2.so.2"] = str(libxml2)

    return {
        "path": rel(host_lib_dir),
        "linked": linked,
        "ready": {"libtinfo.so.5", "libxml2.so.2"}.issubset(linked.keys()),
    }


def tool_env(host_libraries: dict[str, Any]) -> dict[str, str]:
    env = os.environ.copy()
    ld_paths = [str(ROOT / host_libraries["path"])]
    existing = env.get("LD_LIBRARY_PATH")
    if existing:
        ld_paths.append(existing)
    env["LD_LIBRARY_PATH"] = ":".join(ld_paths)
    return env


def source_state() -> dict[str, Any]:
    tap_source = ROOT / ACDBTAP_SOURCE_REL
    ioctl_source = ROOT / IOCTL_SOURCE_REL
    tap_text = tap_source.read_text(encoding="utf-8", errors="replace") if tap_source.exists() else ""
    ioctl_text = ioctl_source.read_text(encoding="utf-8", errors="replace") if ioctl_source.exists() else ""
    required = {
        "tap_source_exists": tap_source.exists(),
        "ioctl_source_exists": ioctl_source.exists(),
        "tap_exports_acdb_ioctl": "acdb_ioctl(uint32_t cmd" in tap_text,
        "tap_dlsym_next": 'dlsym(A90_RTLD_NEXT, "acdb_ioctl")' in tap_text,
        "tap_private_raw_dir": "/data/local/tmp/a90-acdb-tap" in tap_text,
        "tap_target_len_4916": "A90_TARGET_OUT_LEN 4916U" in tap_text,
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


def compile_object(source: Path, obj: Path, *, clang: Path, env: dict[str, str], log_dir: Path) -> dict[str, Any]:
    command = [str(clang), *CFLAGS, "-c", str(source), "-o", str(obj)]
    result = run(command, env=env)
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

    host_libraries = prepare_host_libraries(build_root)
    env = tool_env(host_libraries)
    tap_obj = obj_dir / "libacdbtap_v2475.o"
    ioctl_obj = obj_dir / "a90_ioctl_trace_preload_v2531.o"
    out = bin_dir / ARTIFACT_NAME

    tap_compile = compile_object(ROOT / ACDBTAP_SOURCE_REL, tap_obj, clang=clang, env=env, log_dir=log_dir)
    ioctl_compile = compile_object(ROOT / IOCTL_SOURCE_REL, ioctl_obj, clang=clang, env=env, log_dir=log_dir)
    link_result: dict[str, Any]
    if tap_compile["ok"] and ioctl_compile["ok"]:
        link_cmd = [str(lld), *LDFLAGS, "-o", str(out), str(tap_obj), str(ioctl_obj)]
        link_result = run(link_cmd, env=env)
        (log_dir / "link.stdout.txt").write_text(link_result["stdout"], encoding="utf-8", errors="replace")
        (log_dir / "link.stderr.txt").write_text(link_result["stderr"], encoding="utf-8", errors="replace")
        link_result = {k: v for k, v in link_result.items() if k not in {"stdout", "stderr"}}
        if link_result["ok"] and out.exists():
            out.chmod(0o600)
    else:
        link_result = {"ok": False, "skipped": True, "reason": "compile failed"}

    binary: dict[str, Any] = {"path": rel(out), "exists": out.exists()}
    if out.exists():
        symbols = run([readelf, "-Ws", str(out)], env=env, timeout=30.0)
        dyn = run([readelf, "-d", str(out)], env=env, timeout=30.0)
        binary.update({
            "sha256": sha256_file(out),
            "size": out.stat().st_size,
            "mode": oct(out.stat().st_mode & 0o777),
            "file": run([file_cmd, str(out)], timeout=30.0),
            "symbols": {
                "readelf_ok": symbols["ok"],
                "exports_acdb_ioctl": " acdb_ioctl" in symbols["stdout"],
                "exports_ioctl": " ioctl" in symbols["stdout"],
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
        "compile": {"acdbtap": tap_compile, "ioctl_trace": ioctl_compile},
        "link": link_result,
        "logs": rel(log_dir),
        "binary": binary,
        "ok": bool(
            tap_compile.get("ok")
            and ioctl_compile.get("ok")
            and link_result.get("ok")
            and binary.get("exists")
            and binary.get("symbols", {}).get("exports_acdb_ioctl")
            and binary.get("symbols", {}).get("exports_ioctl")
            and binary.get("dynamic", {}).get("soname")
        ),
    }


def manifest(args: argparse.Namespace) -> dict[str, Any]:
    clang = Path(args.clang) if args.clang else TOOLCHAIN_ROOT / "bin/clang"
    lld = Path(args.lld) if args.lld else TOOLCHAIN_ROOT / "bin/ld.lld"
    payload: dict[str, Any] = {
        "run_id": RUN_ID,
        "build_tag": BUILD_TAG,
        "created_at": now_iso(),
        "host_only": True,
        "device_action": "none",
        "android_action": "none",
        "source": source_state(),
        "toolchain": {
            "clang": rel(clang),
            "lld": rel(lld),
            "target": TARGET,
            "cflags": list(CFLAGS),
            "ldflags": list(LDFLAGS),
        },
        "boundaries": {
            "single_preload_library": True,
            "exports_acdb_ioctl_and_ioctl": True,
            "acdb_ioctl_observes_existing_gets_only": True,
            "fake_allocate_mode_requires_A90_ACDB_FAKE_ALLOCATE": True,
            "fake_mode_noops_allocate_deallocate_set_only": True,
            "does_not_open_msm_audio_cal": True,
            "does_not_issue_extra_ioctl": True,
            "does_not_call_audio_set_calibration": True,
            "raw_bytes_private": True,
        },
        "v2537_delta": "replaces failed separate two-LD_PRELOAD approach with one combined .so",
    }
    if args.build:
        payload["build"] = build(args.build_root, clang=clang, lld=lld, readelf=args.readelf, file_cmd=args.file)
    payload["ok"] = bool(
        payload["source"]["required_ok"]
        and payload["source"]["prohibited_ok"]
        and (not args.build or payload.get("build", {}).get("ok"))
    )
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--build-root", type=Path, default=DEFAULT_BUILD_ROOT)
    parser.add_argument("--manifest-path", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--clang")
    parser.add_argument("--lld", type=Path, default=TOOLCHAIN_ROOT / "bin/ld.lld")
    parser.add_argument("--readelf", default=str(TOOLCHAIN_ROOT / "bin/llvm-readelf"))
    parser.add_argument("--file", default="file")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    args.build_root.mkdir(parents=True, exist_ok=True)
    payload = manifest(args)
    args.manifest_path.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
