#!/usr/bin/env python3
"""Build V2630 ARM32 ACDB SET-calibration capture artifacts.

V2628 rejected the four-byte AFE topology gate outputs as replay payloads.
V2629 therefore moved the next unit to the actual SET-path argument: fake the
AUDIO_SET_CALIBRATION ioctl, dump the full arg[0:data_size] header/geometry, and
when cal_size/mem_handle is present, mmap and dump the same-process dma-buf.

This is host-only build-only.  No Android handoff, device flash, native replay,
real audio SET, mixer, PCM, or speaker write happens here.
"""

from __future__ import annotations

import argparse
import contextlib
import json
from pathlib import Path
from typing import Any, Iterator

import build_android_acdb_meta_list_indirect_layout_capture_v2613 as v2613

ROOT = v2613.ROOT
RUN_ID = "V2630"
BUILD_TAG = "v2630-acdb-setcal-capture-build-only"
DEFAULT_BUILD_ROOT = ROOT / "workspace/private/builds/audio" / BUILD_TAG
DEFAULT_MANIFEST = DEFAULT_BUILD_ROOT / "manifest.json"
DEFAULT_REPORT = ROOT / "docs/reports/NATIVE_INIT_V2630_AUDIO_ACDB_SETCAL_CAPTURE_BUILD_2026-06-17.md"

HELPER_SOURCE_REL = v2613.HELPER_SOURCE_REL
PREINIT_SOURCE_REL = v2613.PREINIT_SOURCE_REL
ACDBTAP_SOURCE_REL = v2613.ACDBTAP_SOURCE_REL
IOCTL_SOURCE_REL = "workspace/public/src/android/acdb_payload_capture/a90_ioctl_setcal_capture_preload_v2630.c"
HELPER_ARTIFACT_NAME = "a90_acdb_setcal_capture_exec_linked_v2630"
PRELOAD_ARTIFACT_NAME = "liba90_acdb_setcal_capture_combined_preload_v2630.so"
PRELOAD_LDFLAGS = ("-shared", "--allow-shlib-undefined", "-soname", PRELOAD_ARTIFACT_NAME)


def rel(path: Path | str) -> str:
    return v2613.rel(path)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


@contextlib.contextmanager
def patched_v2613_constants() -> Iterator[None]:
    v2608 = v2613.v2611.v2608
    v2572 = v2608.v2572
    old = {
        "HELPER_ARTIFACT_NAME": v2613.HELPER_ARTIFACT_NAME,
        "PRELOAD_ARTIFACT_NAME": v2613.PRELOAD_ARTIFACT_NAME,
        "PRELOAD_LDFLAGS": v2613.PRELOAD_LDFLAGS,
        "IOCTL_SOURCE_REL": v2572.IOCTL_SOURCE_REL,
    }
    v2613.HELPER_ARTIFACT_NAME = HELPER_ARTIFACT_NAME
    v2613.PRELOAD_ARTIFACT_NAME = PRELOAD_ARTIFACT_NAME
    v2613.PRELOAD_LDFLAGS = PRELOAD_LDFLAGS
    v2572.IOCTL_SOURCE_REL = IOCTL_SOURCE_REL
    try:
        yield
    finally:
        v2613.HELPER_ARTIFACT_NAME = old["HELPER_ARTIFACT_NAME"]
        v2613.PRELOAD_ARTIFACT_NAME = old["PRELOAD_ARTIFACT_NAME"]
        v2613.PRELOAD_LDFLAGS = old["PRELOAD_LDFLAGS"]
        v2572.IOCTL_SOURCE_REL = old["IOCTL_SOURCE_REL"]


def source_state() -> dict[str, Any]:
    with patched_v2613_constants():
        base = v2613.source_state()
    ioctl_path = ROOT / IOCTL_SOURCE_REL
    ioctl = _read(ioctl_path)
    combined = "\n".join(
        _read(ROOT / path)
        for path in [HELPER_SOURCE_REL, PREINIT_SOURCE_REL, ACDBTAP_SOURCE_REL, IOCTL_SOURCE_REL]
    )

    required = {
        "base_v2613_required_ok": bool(base.get("required_ok")),
        "base_v2613_prohibited_ok": bool(base.get("prohibited_ok")),
        "ioctl_source_exists": ioctl_path.exists(),
        "setcal_events_path": "A90_SETCAL_EVENTS_PATH" in ioctl and "setcal-events.jsonl" in ioctl,
        "setcal_raw_private_prefix": "A90_SETCAL_RAW_PREFIX" in ioctl and "/data/local/tmp/a90-acdb-ownget/setcal-" in ioctl,
        "always_fakes_audio_set": (
            "always fake AUDIO_SET_CALIBRATION" in ioctl
            and "if (request == A90_AUDIO_SET_CALIBRATION)\n        return 1;" in ioctl
            and "fake-set-always" in ioctl
        ),
        "preserves_full_set_arg": (
            "Dump exactly arg[0:data_size]" in ioctl
            and "header.data_size" in ioctl
            and "A90_MAX_SET_ARG_BYTES" in ioctl
            and "4096U" in ioctl
        ),
        "parses_set_header_words": all(
            token in ioctl
            for token in [
                "header->data_size = source[0]",
                "header->cal_type = source[2]",
                "header->cal_size = source[6]",
                "header->mem_handle = (int32_t)source[7]",
            ]
        ),
        "same_process_dmabuf_mmap_dump": (
            "mmap(0, header.cal_size, A90_PROT_READ, A90_MAP_SHARED" in ioctl
            and "munmap(mapping, header.cal_size)" in ioctl
            and "A90_MAX_DMABUF_BYTES" in ioctl
            and "262144U" in ioctl
        ),
        "header_only_is_not_failure": "dmabuf_status = \"header-only\"" in ioctl,
        "sha256_for_arg_and_dmabuf": (
            "a90_sha256_update(&sha, buf, len)" in ioctl
            and "arg_sha" in ioctl
            and "dmabuf_sha" in ioctl
        ),
        "retains_v2531_trace_events": "ioctl-trace-events.jsonl" in ioctl and "arg_snapshot" in ioctl,
    }
    prohibited = {
        "ioctl_opens_msm_audio_cal": 'open("/dev/msm_audio_cal' in ioctl or "/dev/msm_audio_cal" in ioctl,
        "combined_native_speaker_write": any(token in combined for token in ("tinyplay", "tinymix", "AudioTrack")),
        "combined_persistent_magisk_install": "magisk --install-module" in combined,
        "combined_global_pthread_hooks": "pthread_mutex_lock" in combined or "pthread_mutex_unlock" in combined,
        "combined_android_log_hook": "__android_log_print" in combined,
    }
    return {
        "sources": [HELPER_SOURCE_REL, PREINIT_SOURCE_REL, ACDBTAP_SOURCE_REL, IOCTL_SOURCE_REL],
        "base_v2613": base,
        "required": required,
        "required_ok": all(required.values()),
        "prohibited": prohibited,
        "prohibited_ok": not any(prohibited.values()),
        "v2630_delta": {
            "basis": "V2628 rejected 0x13262 four-byte gate outputs; V2629 selected SET arg + same-process dmabuf capture",
            "set_arg_policy": "fake AUDIO_SET_CALIBRATION, dump arg[0:data_size] capped at 4096 bytes with SHA-256",
            "dmabuf_policy": "if cal_size>0 and mem_handle>=0, mmap the same-process fd read-only and dump cal_size bytes capped at 262144",
            "header_only_policy": "cal_size==0 or mem_handle<0 is a valid header-only SET record, not a failed capture",
        },
    }


def build(build_root: Path, *, clang: Path, lld: Path, readelf: str, file_cmd: str) -> dict[str, Any]:
    with patched_v2613_constants():
        build_state = v2613.build(build_root, clang=clang, lld=lld, readelf=readelf, file_cmd=file_cmd)
    preload = build_state.get("artifacts", {}).get("preload", {}) if isinstance(build_state, dict) else {}
    checks = preload.get("checks", {}) if isinstance(preload, dict) else {}
    if "soname_v2613" in checks:
        checks["soname_v2630"] = checks.pop("soname_v2613")
    return build_state


def make_payload(args: argparse.Namespace) -> dict[str, Any]:
    source = source_state()
    vendor = v2613.v2611.v2608.v2572.vendor_lib_state(args.readelf)
    if args.build:
        build_state = build(args.build_root, clang=args.clang, lld=args.lld, readelf=args.readelf, file_cmd=args.file)
    else:
        build_state = {"ok": True, "built": False, "reason": "pass --build to materialize private ARM32 artifacts"}
    artifacts = build_state.get("artifacts", {}) if isinstance(build_state, dict) else {}
    payload: dict[str, Any] = {
        "run_id": RUN_ID,
        "build_tag": BUILD_TAG,
        "host_only_build": True,
        "measurement_boundary": {
            "no_live_default": True,
            "no_native_replay": True,
            "no_speaker_write": True,
            "raw_payload_private_only": True,
            "fake_audio_cal_env": "A90_ACDB_FAKE_ALLOCATE=1",
            "no_real_audio_set": "V2630 ioctl shim always fake-successes AUDIO_SET_CALIBRATION after dumping SET metadata/raw bytes",
        },
        "capture_contract": {
            "base": "V2613 meta-list post-init send_v5 capture stack",
            "postinit": "init_v3 return -> a90_arm_capture -> send_audio_cal_v5",
            "per_device_call": "acdb_loader_send_audio_cal_v5(15, 1, 0x11135, 48000, 0, 48000, 1)",
            "set_capture": "AUDIO_SET_CALIBRATION arg[0:data_size] is dumped and SHA-256 recorded before fake success",
            "dmabuf_capture": "cal_size>0/mem_handle>=0 triggers same-process read-only mmap of the dma-buf fd, capped and hashed",
            "success_discriminator": "future live SET capture is useful if SET arg rows are present; dmabuf rows are required only for cal_size>0 records",
        },
        "sources": source,
        "vendor_libs": vendor,
        "build": build_state,
        "build_root": rel(args.build_root),
    }
    payload["ok"] = bool(
        source.get("required_ok")
        and source.get("prohibited_ok")
        and vendor.get("required_for_v2572_ok")
        and (not args.build or (artifacts.get("helper", {}).get("ok") and artifacts.get("preload", {}).get("ok")))
    )
    return payload


def write_report(payload: dict[str, Any], report_path: Path) -> None:
    helper = payload.get("build", {}).get("artifacts", {}).get("helper", {})
    preload = payload.get("build", {}).get("artifacts", {}).get("preload", {})
    build = payload.get("build", {})
    lines = [
        "# NATIVE_INIT V2630 — ACDB SET-calibration capture build",
        "",
        "Date: 2026-06-17",
        "",
        "## Scope",
        "",
        "Host-only build-only unit. No Android handoff, device flash, native replay SET, mixer,",
        "PCM, or speaker write was performed. Raw ACDB bytes remain private-only.",
        "",
        "## Decision",
        "",
        f"- decision: `{BUILD_TAG}`",
        f"- ok: `{payload.get('ok')}`",
        f"- build_root: `{payload.get('build_root')}`",
        f"- helper: `{helper.get('path')}`",
        f"- helper_sha256: `{helper.get('sha256')}`",
        f"- preload: `{preload.get('path')}`",
        f"- preload_sha256: `{preload.get('sha256')}`",
        "",
        "## Why This Unit",
        "",
        "V2628 proved the AFE topology gate query is useful state evidence but not a replay",
        "payload. V2629 therefore selected the SET path itself: intercept the loader's",
        "`AUDIO_SET_CALIBRATION` call, preserve the exact `arg[0:data_size]` bytes, and only",
        "then fake success so the kernel SET ioctl is never reached in this measurement unit.",
        "",
        "## Capture Contract",
        "",
        "- reuses the V2613 helper/preinit/acdbtap stack and swaps only the ioctl shim",
        "- `AUDIO_SET_CALIBRATION` is always fake-successed; allocate/deallocate remain fake under `A90_ACDB_FAKE_ALLOCATE=1`",
        "- every SET row emits `setcal-events.jsonl` with parsed `data_size`, `cal_type`, `cal_size`, `mem_handle`, and SHA-256",
        "- full SET arg bytes are dumped as private `setcal-arg-*` files capped at 4096 bytes",
        "- if `cal_size>0 && mem_handle>=0`, the same-process dma-buf fd is mmap'd read-only and dumped capped at 262144 bytes",
        "- `cal_size==0` or `mem_handle<0` is `header-only`, not a capture failure",
        "",
        "## Boundary",
        "",
        "- no `/dev/msm_audio_cal` open in the shim",
        "- no extra ioctl issuance; unrelated ioctls pass through only as in V2531",
        "- no real `AUDIO_SET_CALIBRATION` pass-through",
        "- no native replay, mixer, PCM, AudioTrack, or speaker write",
        "",
        "## Build Evidence",
        "",
        f"- source_required_ok: `{payload.get('sources', {}).get('required_ok')}`",
        f"- source_prohibited_ok: `{payload.get('sources', {}).get('prohibited_ok')}`",
        f"- helper_compile_ok: `{build.get('compile', {}).get('helper', {}).get('ok') if isinstance(build, dict) else None}`",
        f"- tap_compile_ok: `{build.get('compile', {}).get('acdbtap_v2600', {}).get('ok') if isinstance(build, dict) else None}`",
        f"- ioctl_compile_ok: `{build.get('compile', {}).get('ioctl_trace', {}).get('ok') if isinstance(build, dict) else None}`",
        f"- preinit_compile_ok: `{build.get('compile', {}).get('preinit_no_send', {}).get('ok') if isinstance(build, dict) else None}`",
        f"- helper_checks: `{helper.get('checks')}`",
        f"- preload_checks: `{preload.get('checks')}`",
        "",
        "## Next Unit",
        "",
        "Run an Android-good own-process handoff with the V2630 helper/preload override. The run",
        "should pull `ioctl-trace-events.jsonl`, `setcal-events.jsonl`, and private `setcal-*` raw",
        "files. Operator Gate-2 verification decides which SET rows enter replay.",
        "",
        "## Validation",
        "",
        "- `python3 -m py_compile workspace/public/src/scripts/revalidation/build_android_acdb_setcal_capture_v2630.py tests/test_build_android_acdb_setcal_capture_v2630.py`",
        "- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_build_android_acdb_setcal_capture_v2630 -v`",
        "- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/build_android_acdb_setcal_capture_v2630.py --build --write-report`",
        "- `git diff --check`",
        "",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--build-root", type=Path, default=DEFAULT_BUILD_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--clang", type=Path, default=v2613.v2611.v2608.v2572.TOOLCHAIN_ROOT / "bin/clang")
    parser.add_argument("--lld", type=Path, default=v2613.v2611.v2608.v2572.TOOLCHAIN_ROOT / "bin/ld.lld")
    parser.add_argument("--readelf", default="readelf")
    parser.add_argument("--file", default="file")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = make_payload(args)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.write_report:
        write_report(payload, args.report)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
