#!/usr/bin/env python3
"""Build V2583 ARM32 ACDB pre-init store_get metadata probe artifacts.

Host-only unit.  The generated private artifacts are:

- a 32-bit Android PIE helper that calls acdb_loader_init_v3();
- a single 32-bit preload exporting ioctl() and
  acdb_loader_send_common_custom_topology().

The preload uses the V2531 fake allocation ioctl wrapper and a V2583
common-topology hook.  The hook skips the already-pinned topology public call,
patches the known initialized flag, runs the V2580 store_get metadata cases,
and exits before the libacdbloader init-tail crash observed in V2582.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import build_android_acdb_combined_preload_v2538 as preload_base
import build_android_acdb_perdevice_indirect_capture_v2572 as v2572_base

ROOT = v2572_base.ROOT
RUN_ID = "V2583"
BUILD_TAG = "v2583-acdb-preinit-store-get-build-only"
HELPER_SOURCE_REL = "workspace/public/src/android/acdb_payload_capture/a90_acdb_preinit_store_get_exec_linked_v2583.c"
PREINIT_SOURCE_REL = "workspace/public/src/android/acdb_payload_capture/libacdb_preinit_store_get_v2583.c"
IOCTL_SOURCE_REL = v2572_base.IOCTL_SOURCE_REL
TOOLCHAIN_ROOT = v2572_base.TOOLCHAIN_ROOT
VENDOR_LIB_DIR = v2572_base.VENDOR_LIB_DIR
DEFAULT_BUILD_ROOT = ROOT / "workspace/private/builds/audio" / BUILD_TAG
DEFAULT_MANIFEST = DEFAULT_BUILD_ROOT / "manifest.json"
DEFAULT_REPORT = ROOT / "docs/reports/NATIVE_INIT_V2583_AUDIO_ACDB_PREINIT_STORE_GET_BUILD_2026-06-16.md"
HELPER_ARTIFACT_NAME = "a90_acdb_preinit_store_get_exec_linked_v2583"
PRELOAD_ARTIFACT_NAME = "liba90_acdb_preinit_store_get_v2583.so"
HELPER_CFLAGS = v2572_base.HELPER_CFLAGS
HELPER_LDFLAGS = v2572_base.HELPER_LDFLAGS
PRELOAD_CFLAGS = v2572_base.PRELOAD_CFLAGS
PRELOAD_LDFLAGS = (
    "-shared",
    "--allow-shlib-undefined",
    "-soname",
    PRELOAD_ARTIFACT_NAME,
)
LINK_LIBS = v2572_base.LINK_LIBS
REQUIRED_NEEDED = v2572_base.REQUIRED_NEEDED


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.resolve().relative_to(ROOT))
    except ValueError:
        return str(p)


def _read(rel_path: str) -> str:
    path = ROOT / rel_path
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def source_state() -> dict[str, Any]:
    helper = ROOT / HELPER_SOURCE_REL
    preinit = ROOT / PREINIT_SOURCE_REL
    ioctl = ROOT / IOCTL_SOURCE_REL
    helper_text = _read(HELPER_SOURCE_REL)
    preinit_text = _read(PREINIT_SOURCE_REL)
    ioctl_text = _read(IOCTL_SOURCE_REL)
    combined_public = "\n".join((helper_text, preinit_text))

    patch_pos = preinit_text.find("patch_initialized_flag_return")
    before_store_pos = preinit_text.find("before_store_get_cases")
    exit_pos = preinit_text.find("exit_before_init_tail")

    required = {
        "helper_source_exists": helper.exists(),
        "preinit_source_exists": preinit.exists(),
        "ioctl_source_exists": ioctl.exists(),
        "helper_calls_init_v3_only": "acdb_loader_init_v3(A90_ACDB_FILES_PATH, A90_DELTA_DIR, 0U)" in helper_text,
        "preinit_exports_common_topology": "int32_t acdb_loader_send_common_custom_topology(void)" in preinit_text,
        "preinit_skips_real_common_topology_by_default": (
            "#define A90_V2583_CALL_REAL_COMMON_TOPOLOGY 0" in preinit_text
            and "skip_real_common_topology" in preinit_text
        ),
        "preinit_patches_init_flag": "A90_LOADER_INIT_FLAG_OFF" in preinit_text and "*flag = 1U" in preinit_text,
        "preinit_runs_cases_after_patch": patch_pos >= 0 and before_store_pos > patch_pos,
        "preinit_exits_before_init_tail": exit_pos > before_store_pos and "a90_exit_group(0)" in preinit_text,
        "declares_store_get": "a90_store_get_audio_cal_fn" in preinit_text and "acdb_loader_store_get_audio_cal" in preinit_text,
        "covers_selector_37": '"store_selector_37"' in preinit_text,
        "covers_selector_0_no_instance": '"store_selector_0_no_instance"' in preinit_text,
        "covers_selector_0_instance": '"store_selector_0_instance"' in preinit_text,
        "covers_selector_1_no_instance": '"store_selector_1_no_instance"' in preinit_text,
        "covers_selector_1_instance": '"store_selector_1_instance"' in preinit_text,
        "bounded_output_buffer": "A90_OUTPUT_MAX 65536U" in preinit_text and "out_len <= A90_OUTPUT_MAX" in preinit_text,
        "zero_buffer_guard": "a90_is_all_zero" in preinit_text and "all_zero" in preinit_text,
        "metadata_hash_only": "a90_fnv1a32" in preinit_text and "fnv1a32" in preinit_text,
        "private_metadata_path": "/data/local/tmp/a90-acdb-ownget/acdb-v2583-preinit-storeget-events.jsonl" in preinit_text,
        "ioctl_fake_allocate_set_available": (
            "A90_AUDIO_ALLOCATE_CALIBRATION" in ioctl_text
            and "A90_AUDIO_DEALLOCATE_CALIBRATION" in ioctl_text
            and "A90_AUDIO_SET_CALIBRATION" in ioctl_text
            and "fake-success" in ioctl_text
        ),
    }
    prohibited = {
        "helper_or_preinit_opens_msm_audio_cal": "/dev/msm_audio_cal" in combined_public,
        "helper_or_preinit_audio_set_constant": "AUDIO_SET_CALIBRATION" in combined_public or "0xc00461cb" in combined_public.lower(),
        "helper_or_preinit_direct_acdb_ioctl": "acdb_ioctl(" in combined_public,
        "helper_or_preinit_ioctl_call": "ioctl(" in combined_public,
        "raw_payload_write": ".bin" in combined_public or "payload.bin" in combined_public,
        "native_speaker_write": any(token in combined_public for token in ("tinyplay", "tinymix", "AudioTrack")),
        "persistent_magisk_install": "magisk --install-module" in combined_public,
    }
    return {
        "sources": [HELPER_SOURCE_REL, PREINIT_SOURCE_REL, IOCTL_SOURCE_REL],
        "required": required,
        "required_ok": all(required.values()),
        "prohibited": prohibited,
        "prohibited_ok": not any(prohibited.values()),
        "cases": [
            "store_selector_37",
            "store_selector_0_no_instance",
            "store_selector_0_instance",
            "store_selector_1_no_instance",
            "store_selector_1_instance",
        ],
    }


def vendor_lib_state(readelf: str) -> dict[str, Any]:
    state = v2572_base.vendor_lib_state(readelf)
    loader = VENDOR_LIB_DIR / "libacdbloader.so"
    symbol_text = ""
    if loader.exists():
        result = preload_base.run([readelf, "-Ws", str(loader)], timeout=30.0)
        symbol_text = result["stdout"] if result["ok"] else ""
    required = {
        "has_acdb_loader_init_v3": " acdb_loader_init_v3" in symbol_text,
        "has_acdb_loader_is_initialized": " acdb_loader_is_initialized" in symbol_text,
        "has_acdb_loader_send_common_custom_topology": " acdb_loader_send_common_custom_topology" in symbol_text,
        "has_acdb_loader_store_get_audio_cal": " acdb_loader_store_get_audio_cal" in symbol_text,
    }
    state["required_for_v2583"] = required
    state["required_for_v2583_ok"] = all(required.values())
    return state


def _compile(source: Path, obj: Path, *, clang: Path, env: dict[str, str], log_dir: Path, cflags: tuple[str, ...]) -> dict[str, Any]:
    return v2572_base.compile_object(source, obj, clang=clang, env=env, log_dir=log_dir, cflags=cflags)


def _binary_state(path: Path, *, readelf: str, file_cmd: str, kind: str) -> dict[str, Any]:
    state: dict[str, Any] = {"path": rel(path), "exists": path.exists(), "kind": kind}
    if not path.exists():
        state["ok"] = False
        return state
    symbols = preload_base.run([readelf, "-Ws", str(path)], timeout=30.0)
    dynamic = preload_base.run([readelf, "-d", str(path)], timeout=30.0)
    header = preload_base.run([readelf, "-h", str(path)], timeout=30.0)
    file_result = preload_base.run([file_cmd, str(path)], timeout=30.0)
    sym = symbols["stdout"]
    dyn = dynamic["stdout"]
    hdr = header["stdout"]
    if kind == "helper":
        checks = {
            "is_pie": "DYN (Shared object file)" in hdr,
            "entry_start": "_start" in sym,
            "undefined_init_v3": " UND acdb_loader_init_v3" in sym,
            "needed_libacdbloader": "Shared library: [libacdbloader.so]" in dyn,
            "needed_libaudcal": "Shared library: [libaudcal.so]" in dyn,
        }
    else:
        checks = {
            "exports_ioctl": " ioctl" in sym,
            "exports_common_topology": " acdb_loader_send_common_custom_topology" in sym,
            "does_not_export_acdb_ioctl": " acdb_ioctl" not in sym,
            "undefined_dlsym": " UND dlsym" in sym,
            "undefined_errno": " UND __errno" in sym,
            "soname": f"Library soname: [{PRELOAD_ARTIFACT_NAME}]" in dyn,
        }
    state.update(
        {
            "sha256": preload_base.sha256_file(path),
            "size": path.stat().st_size,
            "mode": oct(path.stat().st_mode & 0o777),
            "file": file_result["stdout"].strip(),
            "checks": checks,
            "ok": bool(file_result.get("ok") and symbols.get("ok") and dynamic.get("ok") and header.get("ok") and all(checks.values())),
        }
    )
    return state


def build(build_root: Path, *, clang: Path, lld: Path, readelf: str, file_cmd: str) -> dict[str, Any]:
    obj_dir = build_root / "obj"
    bin_dir = build_root / "bin"
    log_dir = build_root / "logs"
    obj_dir.mkdir(parents=True, exist_ok=True)
    bin_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    missing = [name for name in REQUIRED_NEEDED if not (VENDOR_LIB_DIR / name).exists()]
    if missing:
        return {"ok": False, "error": f"missing private ACDB closure libs: {', '.join(missing)}"}

    host_libraries = preload_base.prepare_host_libraries(build_root)
    env = preload_base.tool_env(host_libraries)

    helper_obj = obj_dir / "a90_acdb_preinit_store_get_exec_linked_v2583.o"
    ioctl_obj = obj_dir / "a90_ioctl_trace_preload_v2531.o"
    preinit_obj = obj_dir / "libacdb_preinit_store_get_v2583.o"
    helper_out = bin_dir / HELPER_ARTIFACT_NAME
    preload_out = bin_dir / PRELOAD_ARTIFACT_NAME

    helper_compile = _compile(ROOT / HELPER_SOURCE_REL, helper_obj, clang=clang, env=env, log_dir=log_dir, cflags=HELPER_CFLAGS)
    ioctl_compile = _compile(ROOT / IOCTL_SOURCE_REL, ioctl_obj, clang=clang, env=env, log_dir=log_dir, cflags=PRELOAD_CFLAGS)
    preinit_compile = _compile(ROOT / PREINIT_SOURCE_REL, preinit_obj, clang=clang, env=env, log_dir=log_dir, cflags=PRELOAD_CFLAGS)

    if helper_compile["ok"]:
        helper_link = preload_base.run(
            [str(lld), *HELPER_LDFLAGS, "-L", str(VENDOR_LIB_DIR), "-o", str(helper_out), str(helper_obj), *LINK_LIBS],
            env=env,
        )
        (log_dir / "helper.link.stdout.txt").write_text(helper_link["stdout"], encoding="utf-8", errors="replace")
        (log_dir / "helper.link.stderr.txt").write_text(helper_link["stderr"], encoding="utf-8", errors="replace")
        helper_link = {k: v for k, v in helper_link.items() if k not in {"stdout", "stderr"}}
        if helper_link["ok"] and helper_out.exists():
            helper_out.chmod(0o600)
    else:
        helper_link = {"ok": False, "skipped": True, "reason": "helper compile failed"}

    if ioctl_compile["ok"] and preinit_compile["ok"]:
        preload_link = preload_base.run(
            [str(lld), *PRELOAD_LDFLAGS, "-o", str(preload_out), str(ioctl_obj), str(preinit_obj)],
            env=env,
        )
        (log_dir / "preload.link.stdout.txt").write_text(preload_link["stdout"], encoding="utf-8", errors="replace")
        (log_dir / "preload.link.stderr.txt").write_text(preload_link["stderr"], encoding="utf-8", errors="replace")
        preload_link = {k: v for k, v in preload_link.items() if k not in {"stdout", "stderr"}}
        if preload_link["ok"] and preload_out.exists():
            preload_out.chmod(0o600)
    else:
        preload_link = {"ok": False, "skipped": True, "reason": "preload compile failed"}

    helper_state = _binary_state(helper_out, readelf=readelf, file_cmd=file_cmd, kind="helper")
    preload_state = _binary_state(preload_out, readelf=readelf, file_cmd=file_cmd, kind="preload")
    return {
        "host_libraries": host_libraries,
        "compile": {"helper": helper_compile, "ioctl_trace": ioctl_compile, "preinit_store_get": preinit_compile},
        "link": {"helper": helper_link, "preload": preload_link},
        "artifacts": {"helper": helper_state, "preload": preload_state},
        "ok": bool(helper_state.get("ok") and preload_state.get("ok")),
    }


def manifest(args: argparse.Namespace) -> dict[str, Any]:
    source = source_state()
    vendor = vendor_lib_state(args.readelf)
    build_state = build(args.build_root, clang=args.clang, lld=args.lld, readelf=args.readelf, file_cmd=args.file) if args.build else {
        "built": False,
        "reason": "pass --build to materialize private ARM32 artifacts",
    }
    payload: dict[str, Any] = {
        "decision": "v2583-acdb-preinit-store-get-build-only",
        "run_id": RUN_ID,
        "build_tag": BUILD_TAG,
        "host_only": True,
        "device_action": "none",
        "flash_action": "none",
        "android_action": "none",
        "source_state": source,
        "vendor_lib_state": vendor,
        "build": build_state,
        "build_root": rel(args.build_root),
        "capture_contract": {
            "why_preinit": "V2582 proved init_v3 runs common topology and crashes before helper post-init store_get can execute",
            "common_topology_policy": "skip real public common-topology call; topology payload already captured in V2547",
            "store_get_policy": "run five V2580 metadata-only store_get cases inside common-topology hook before init-tail crash",
            "ioctl_policy": "V2531 fake-success ALLOC/DEALLOC/SET when A90_ACDB_FAKE_ALLOCATE=1; no real SET pass-through in future live use",
            "success_rule": "future live success requires ret==0 and all_zero=false; requested length alone is not success",
        },
        "boundaries": {
            "no_device_action": True,
            "no_native_replay": True,
            "no_speaker_write": True,
            "no_raw_payload_dump": True,
            "live_execution_blocked_in_this_unit": True,
        },
    }
    payload["ok"] = bool(
        source["required_ok"]
        and source["prohibited_ok"]
        and vendor.get("required_for_v2583_ok")
        and (not args.build or build_state.get("ok"))
    )
    return payload


def write_report(path: Path, payload: dict[str, Any]) -> None:
    source = payload["source_state"]
    vendor = payload["vendor_lib_state"].get("required_for_v2583", {})
    artifacts = payload.get("build", {}).get("artifacts", {}) if isinstance(payload.get("build"), dict) else {}
    helper = artifacts.get("helper", {})
    preload = artifacts.get("preload", {})
    helper_file = str(helper.get("file") or "")
    preload_file = str(preload.get("file") or "")
    if ": " in helper_file:
        helper_file = helper_file.split(": ", 1)[1]
    if ": " in preload_file:
        preload_file = preload_file.split(": ", 1)[1]
    lines = [
        "# NATIVE_INIT V2583 — ACDB pre-init store-get probe build",
        "",
        "## Scope",
        "",
        "Host-only build-only unit after V2582. No device action, Android handoff, native replay SET,",
        "speaker write, or raw ACDB payload publication was performed.",
        "",
        "## Decision",
        "",
        f"- decision: `{payload['decision']}`",
        f"- ok: `{payload['ok']}`",
        f"- build_root: `{payload['build_root']}`",
        f"- helper: `{helper.get('path')}`",
        f"- helper_sha256: `{helper.get('sha256')}`",
        f"- preload: `{preload.get('path')}`",
        f"- preload_sha256: `{preload.get('sha256')}`",
        f"- source_required_ok: `{source['required_ok']}`",
        f"- source_prohibited_ok: `{source['prohibited_ok']}`",
        f"- vendor_required_for_v2583: `{vendor}`",
        "",
        "## Rationale",
        "",
        "- V2582 proved the V2580 post-init store-get helper never reaches its cases: `init_v3()`",
        "  itself enters common topology and then crashes before returning.",
        "- Repeating a literal post-init arm/store-get path is therefore not useful for this binary.",
        "- V2583 moves the same five V2580 store-get metadata cases into a common-topology hook, after",
        "  the initialized flag patch and before the known init-tail crash.",
        "- The real common-topology call is skipped because the topology payload is already pinned; this",
        "  unit targets lower GET metadata only.",
        "",
        "## Boundaries",
        "",
        "- The helper only calls `acdb_loader_init_v3()`.",
        "- The preload writes metadata only: `ret`, returned length, all-zero discriminator, and FNV-1a32.",
        "- The helper/preinit source does not open `/dev/msm_audio_cal`, does not call `ioctl()`, and does",
        "  not call direct `acdb_ioctl()`.",
        "- The linked V2531 ioctl wrapper is present only for future fake-success ALLOC/DEALLOC/SET under",
        "  `A90_ACDB_FAKE_ALLOCATE=1`; no real native replay is run in this unit.",
        "",
        "## Artifact Checks",
        "",
        f"- helper_file: `{helper_file}`",
        f"- helper_checks: `{helper.get('checks')}`",
        f"- preload_file: `{preload_file}`",
        f"- preload_checks: `{preload.get('checks')}`",
        "",
        "## Next Unit",
        "",
        "A future V2584 live runner can stage these private artifacts through the checked Android handoff,",
        "set `A90_ACDB_FAKE_ALLOCATE=1`, and classify only the metadata rows. Native calibration SET and",
        "speaker playback remain blocked until per-device payload bytes/order and cleanup policy are pinned.",
        "",
        "## Validation",
        "",
        "- `python3 -m py_compile workspace/public/src/scripts/revalidation/build_android_acdb_preinit_store_get_probe_v2583.py tests/test_build_android_acdb_preinit_store_get_probe_v2583.py`",
        "- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_build_android_acdb_preinit_store_get_probe_v2583`",
        "- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/build_android_acdb_preinit_store_get_probe_v2583.py --build --write-report`",
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
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--clang", type=Path, default=TOOLCHAIN_ROOT / "bin/clang")
    parser.add_argument("--lld", type=Path, default=TOOLCHAIN_ROOT / "bin/ld.lld")
    parser.add_argument("--readelf", default="readelf")
    parser.add_argument("--file", default="file")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = manifest(args)
    args.manifest_path.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.write_report:
        write_report(args.report_path, payload)
    print(json.dumps({
        "ok": payload["ok"],
        "decision": payload["decision"],
        "manifest_path": rel(args.manifest_path),
        "report_path": rel(args.report_path) if args.write_report else None,
        "helper": payload.get("build", {}).get("artifacts", {}).get("helper", {}).get("path"),
        "preload": payload.get("build", {}).get("artifacts", {}).get("preload", {}).get("path"),
    }, indent=2, sort_keys=True))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
