#!/usr/bin/env python3
"""Build V2580 ARM32 ACDB store-get pure-read probe helper.

Host-only unit. The generated private PIE is live-gated by a runtime marker file
and is not executed by this builder. It links the stock ACDB closure and prepares
a future pure-read store_get probe without native calibration SET or speaker I/O.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import build_android_acdb_ownprocess_get_exec_linked_v2512 as base

ROOT = base.ROOT
RUN_ID = "V2580"
BUILD_TAG = "v2580-acdb-store-get-probe-build-only"
SOURCE_REL = "workspace/public/src/android/acdb_payload_capture/a90_acdb_store_get_probe_exec_linked_v2580.c"
TOOLCHAIN_ROOT = base.TOOLCHAIN_ROOT
VENDOR_LIB_DIR = base.VENDOR_LIB_DIR
DEFAULT_BUILD_ROOT = ROOT / "workspace/private/builds/audio" / BUILD_TAG
DEFAULT_MANIFEST = DEFAULT_BUILD_ROOT / "manifest.json"
ARTIFACT_NAME = "a90_acdb_store_get_probe_exec_linked_v2580"
TARGET = base.TARGET
CFLAGS = base.CFLAGS
LDFLAGS = base.LDFLAGS
LINK_LIBS = base.LINK_LIBS
REQUIRED_NEEDED = base.REQUIRED_NEEDED


def rel(path: Path | str) -> str:
    return base.rel(Path(path) if not isinstance(path, Path) else path)


def source_state() -> dict[str, Any]:
    source = ROOT / SOURCE_REL
    text = source.read_text(encoding="utf-8", errors="replace") if source.exists() else ""
    start_body = text[text.find("void _start(void)"):] if "void _start(void)" in text else ""
    required = {
        "source_exists": source.exists(),
        "custom_start": "void _start(void)" in text,
        "direct_decl_init_v3": "extern int32_t acdb_loader_init_v3" in text,
        "direct_decl_store_get": "extern int32_t acdb_loader_store_get_audio_cal" in text,
        "gate_file_guard": "A90_GATE_PATH" in text and "gate_absent_no_live" in text and "a90_gate_present" in text,
        "no_live_before_gate": start_body.find("a90_gate_present") < start_body.find("acdb_loader_init_v3") if "a90_gate_present" in start_body and "acdb_loader_init_v3" in start_body else False,
        "acdb_root_audconf_open": 'A90_ACDB_FILES_PATH "/vendor/etc/audconf/OPEN"' in text,
        "private_event_path": "/data/local/tmp/a90-acdb-ownget/acdb-storeget-v2580-events.jsonl" in text,
        "request_struct_has_selector_28": "uint32_t selector;" in text and "+28" in text,
        "request_struct_has_instance_offsets": "instance_ptr" in text and "instance_len" in text,
        "covers_selector_37": '"store_selector_37"' in text,
        "covers_selector_0_no_instance": '"store_selector_0_no_instance"' in text,
        "covers_selector_0_instance": '"store_selector_0_instance"' in text,
        "covers_selector_1_no_instance": '"store_selector_1_no_instance"' in text,
        "covers_selector_1_instance": '"store_selector_1_instance"' in text,
        "calls_store_get_direct": "acdb_loader_store_get_audio_cal(&req, a90_output, &out_len)" in text,
        "bounded_output_buffer": "A90_OUTPUT_MAX 65536U" in text and "out_len <= A90_OUTPUT_MAX" in text,
        "zero_buffer_guard": "a90_is_all_zero" in text and "all_zero" in text,
        "metadata_hash": "a90_fnv1a32" in text and "fnv1a32" in text,
        "uses_exit_group": "A90_NR_EXIT_GROUP" in text and "a90_syscall1(A90_NR_EXIT_GROUP" in text,
        "raw_syscalls_only": "A90_NR_OPENAT" in text and "A90_NR_WRITE" in text,
        "no_libc_headers": "#include <" not in text,
    }
    prohibited = {
        "dlopen_path": "dlopen" in text or "dlsym" in text or "dlerror" in text,
        "android_linker_namespace_api": "android_dlopen" in text or "android_get_exported_namespace" in text,
        "opens_msm_audio_cal": "/dev/msm_audio_cal" in text,
        "forbidden_set_ioctl_constant": "0xC00461CB" in text or "0xc00461cb" in text,
        "audio_calibration_ioctl_name": "AUDIO_SET_CALIBRATION" in text or "AUDIO_ALLOCATE_CALIBRATION" in text,
        "direct_acdb_ioctl": "acdb_ioctl(" in text,
        "ioctl_call": "ioctl(" in text,
        "native_speaker_write": any(token in text for token in ("tinyplay", "tinymix", "AudioTrack")),
        "persistent_magisk_install": "magisk --install-module" in text,
    }
    return {
        "source": SOURCE_REL,
        "exists": source.exists(),
        "required": required,
        "required_ok": all(required.values()),
        "prohibited": prohibited,
        "prohibited_ok": not any(prohibited.values()),
        "runtime_gate": "/data/local/tmp/a90-acdb-ownget/V2580_STORE_GET_GO",
        "cases": [
            "store_selector_37",
            "store_selector_0_no_instance",
            "store_selector_0_instance",
            "store_selector_1_no_instance",
            "store_selector_1_instance",
        ],
    }


def vendor_lib_state(readelf: str) -> dict[str, Any]:
    state = base.vendor_lib_state(readelf)
    loader = VENDOR_LIB_DIR / "libacdbloader.so"
    text = ""
    if loader.exists():
        result = base.run([readelf, "-Ws", str(loader)], timeout=30.0)
        text = result["stdout"] if result["ok"] else ""
    state["required_for_v2580"] = {
        "has_acdb_loader_init_v3": state.get("libacdbloader_symbols", {}).get("has_acdb_loader_init_v3"),
        "has_acdb_loader_store_get_audio_cal": " acdb_loader_store_get_audio_cal" in text,
    }
    state["required_for_v2580_ok"] = all(state["required_for_v2580"].values())
    return state


def build(build_root: Path, *, clang: Path, lld: Path, readelf: str, file_cmd: str) -> dict[str, Any]:
    source = ROOT / SOURCE_REL
    obj_dir = build_root / "obj"
    bin_dir = build_root / "bin"
    log_dir = build_root / "logs"
    obj_dir.mkdir(parents=True, exist_ok=True)
    bin_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    missing = [name for name in REQUIRED_NEEDED if not (VENDOR_LIB_DIR / name).exists()]
    if missing:
        raise RuntimeError(f"missing private ACDB closure libs: {', '.join(missing)}")

    host_libraries = base.prepare_host_libraries(build_root)
    env = base.tool_env(host_libraries)
    obj = obj_dir / "a90_acdb_store_get_probe_exec_linked_v2580.o"
    out = bin_dir / ARTIFACT_NAME

    compile_cmd = [str(clang), *CFLAGS, "-c", str(source), "-o", str(obj)]
    compile_result = base.run(compile_cmd, env=env, timeout=180.0)
    (log_dir / "compile.stdout.txt").write_text(compile_result["stdout"], encoding="utf-8", errors="replace")
    (log_dir / "compile.stderr.txt").write_text(compile_result["stderr"], encoding="utf-8", errors="replace")
    if not compile_result["ok"]:
        raise RuntimeError(f"compile failed; see {rel(log_dir / 'compile.stderr.txt')}")

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
        raise RuntimeError(f"link failed; see {rel(log_dir / 'link.stderr.txt')}")
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
    checks = {
        "is_pie": "DYN (Shared object file)" in header,
        "entry_start": "_start" in symbols,
        "needed_ok": all(needed.values()),
        "undefined_init_v3": " UND acdb_loader_init_v3" in symbols,
        "undefined_store_get": " UND acdb_loader_store_get_audio_cal" in symbols,
        "no_undefined_acdb_ioctl": " UND acdb_ioctl" not in symbols,
        "interpreter_system_linker": "/system/bin/linker" in file_result["stdout"]
        or "Requesting program interpreter: /system/bin/linker" in header
        or "/system/bin/linker" in dynamic,
        "mode_0600": oct(out.stat().st_mode & 0o777) == "0o600",
    }
    return {
        "host_libraries": host_libraries,
        "commands": {
            "compile": {k: v for k, v in compile_result.items() if k not in {"stdout", "stderr"}},
            "link": {k: v for k, v in link_result.items() if k not in {"stdout", "stderr"}},
        },
        "logs": rel(log_dir),
        "artifact": {
            "path": rel(out),
            "sha256": base.sha256_file(out),
            "size": out.stat().st_size,
            "mode": oct(out.stat().st_mode & 0o777),
            "file": file_result["stdout"].strip(),
            "target": TARGET,
            "private_generated": True,
            "needed": needed,
            "checks": checks,
            "checks_ok": all(checks.values()),
            "readelf_header": rel(log_dir / "readelf.header.txt"),
            "readelf_dynamic": rel(log_dir / "readelf.dynamic.txt"),
            "readelf_symbols": rel(log_dir / "readelf.symbols.txt"),
        },
    }


def manifest(args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "decision": "v2580-acdb-store-get-probe-build-only",
        "run_id": RUN_ID,
        "build_tag": BUILD_TAG,
        "created_at": base.now_iso(),
        "host_only": True,
        "device_action": "none",
        "flash_action": "none",
        "android_action": "none",
        "source_state": source_state(),
        "vendor_lib_state": vendor_lib_state(args.readelf),
        "prior_layout_report": "docs/reports/NATIVE_INIT_V2579_AUDIO_ACDB_DIRECT_GET_LAYOUT_EXTRACTOR_2026-06-16.md",
        "capture_contract": {
            "artifact": ARTIFACT_NAME,
            "abi": "32-bit armeabi-v7a PIE",
            "runtime_gate": "/data/local/tmp/a90-acdb-ownget/V2580_STORE_GET_GO",
            "default_behavior_without_gate": "exit before acdb_loader_init_v3/store_get",
            "target_function": "acdb_loader_store_get_audio_cal",
            "request_cases": source_state()["cases"],
            "max_output_len": 65536,
            "success_rule": "future live success requires ret==0 and all_zero=false; requested length alone is not success",
            "public_output": "metadata only",
        },
        "boundaries": {
            "no_device_action": True,
            "no_native_msm_audio_cal_ioctl": True,
            "no_direct_acdb_ioctl_matrix": True,
            "no_native_speaker_write": True,
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
        "build_root": rel(args.build_root),
    }
    if args.build:
        payload["build"] = build(args.build_root, clang=args.clang, lld=args.lld, readelf=args.readelf, file_cmd=args.file)
    payload["ok"] = bool(
        payload["source_state"]["required_ok"]
        and payload["source_state"]["prohibited_ok"]
        and payload["vendor_lib_state"].get("required_for_v2580_ok")
        and (not args.build or payload.get("build", {}).get("artifact", {}).get("checks_ok"))
    )
    return payload


def write_report(path: Path, payload: dict[str, Any]) -> None:
    build = payload.get("build", {}) if isinstance(payload.get("build"), dict) else {}
    artifact = build.get("artifact", {}) if isinstance(build.get("artifact"), dict) else {}
    source = payload["source_state"]
    vendor = payload["vendor_lib_state"].get("required_for_v2580", {})
    file_desc = str(artifact.get("file") or "")
    if ": " in file_desc:
        file_desc = file_desc.split(": ", 1)[1]
    lines = [
        "# NATIVE_INIT V2580 — ACDB store-get pure-read harness build",
        "",
        "## Scope",
        "",
        "Host-only build-only unit after V2579. No device action, Android handoff, native calibration",
        "ioctl, ACDB command execution, speaker write, or raw payload capture was performed.",
        "",
        "## Decision",
        "",
        f"- decision: `{payload['decision']}`",
        f"- ok: `{payload['ok']}`",
        f"- build_root: `{payload['build_root']}`",
        f"- artifact: `{artifact.get('path')}`",
        f"- artifact_sha256: `{artifact.get('sha256')}`",
        f"- source_required_ok: `{source['required_ok']}`",
        f"- source_prohibited_ok: `{source['prohibited_ok']}`",
        f"- vendor_required_for_v2580: `{vendor}`",
        "",
        "## Harness Contract",
        "",
        "- Runtime is protected by `V2580_STORE_GET_GO`; without that marker, the binary exits before",
        "  `acdb_loader_init_v3()` or `acdb_loader_store_get_audio_cal()`.",
        "- The helper covers the five V2579 store-get cases: selector 37, selector 0 without/with",
        "  instance data, and selector 1 without/with instance data.",
        "- Output is bounded to 65536 bytes and metadata checks include `ret`, returned length,",
        "  `all_zero`, and FNV-1a32. This preserves the V2530 rule: requested length alone is never",
        "  success.",
        "- The helper does not call direct `acdb_ioctl`, does not open `/dev/msm_audio_cal`, and does not",
        "  contain native speaker playback code.",
        "",
        "## Artifact Checks",
        "",
        f"- file: `{file_desc}`",
        f"- mode: `{artifact.get('mode')}`",
        f"- checks: `{artifact.get('checks')}`",
        "",
        "## Next Unit",
        "",
        "V2581 should remain non-live unless a stricter future gate is written: add a dry-run/live runner",
        "that refuses to execute without the marker file, stages this private helper plus the existing",
        "fake-allocation preload, and classifies only metadata results. Actual native replay SET and",
        "speaker playback remain blocked.",
        "",
        "## Validation",
        "",
        "- `python3 -m py_compile workspace/public/src/scripts/revalidation/build_android_acdb_store_get_probe_v2580.py`",
        "- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_build_android_acdb_store_get_probe_v2580`",
        "- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/build_android_acdb_store_get_probe_v2580.py --build --write-report`",
        "- `git diff --check`",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--build-root", type=Path, default=DEFAULT_BUILD_ROOT)
    parser.add_argument("--manifest-path", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--report-path", type=Path, default=ROOT / "docs/reports/NATIVE_INIT_V2580_AUDIO_ACDB_STORE_GET_PROBE_BUILD_2026-06-16.md")
    parser.add_argument("--clang", type=Path, default=TOOLCHAIN_ROOT / "bin/clang")
    parser.add_argument("--lld", type=Path, default=TOOLCHAIN_ROOT / "bin/ld.lld")
    parser.add_argument("--readelf", default="readelf")
    parser.add_argument("--file", default="file")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = manifest(args)
    args.manifest_path.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    if args.write_report:
        write_report(args.report_path, payload)
    print(json.dumps({
        "ok": payload["ok"],
        "decision": payload["decision"],
        "manifest_path": rel(args.manifest_path),
        "report_path": rel(args.report_path) if args.write_report else None,
        "artifact": payload.get("build", {}).get("artifact", {}).get("path"),
    }, indent=2, sort_keys=True))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
