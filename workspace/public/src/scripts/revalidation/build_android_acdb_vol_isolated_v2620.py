#!/usr/bin/env python3
"""Build V2620 ARM32 ACDB VOL-isolated direct GET artifacts.

Host-only build-only unit after V2618/V2619.  V2618 showed that the V2617
matrix SIGSEGVs after entering tail-meta command 0x12eeb, before the VOL sweep.
V2620 keeps the proven init/manual-arm/fake-allocate path but removes 0x12eeb
and runs only a minimal safe prelude plus VOL size/data commands.  Live execution
is intentionally deferred to a later V-iteration.
"""

from __future__ import annotations

import argparse
import contextlib
import json
from pathlib import Path
from typing import Any, Iterator

import build_android_acdb_direct_matrix_v2617 as v2617

ROOT = v2617.ROOT
RUN_ID = "V2620"
BUILD_TAG = "v2620-acdb-vol-isolated-build-only"
DEFAULT_BUILD_ROOT = ROOT / "workspace/private/builds/audio" / BUILD_TAG
DEFAULT_MANIFEST = DEFAULT_BUILD_ROOT / "manifest.json"
DEFAULT_REPORT = ROOT / "docs/reports/NATIVE_INIT_V2620_AUDIO_ACDB_VOL_ISOLATED_BUILD_2026-06-16.md"

HELPER_SOURCE_REL = "workspace/public/src/android/acdb_payload_capture/a90_acdb_vol_isolated_exec_linked_v2620.c"
HELPER_ARTIFACT_NAME = "a90_acdb_vol_isolated_exec_linked_v2620"
PRELOAD_ARTIFACT_NAME = "liba90_acdb_vol_isolated_combined_preload_v2620.so"
PRELOAD_LDFLAGS = ("-shared", "--allow-shlib-undefined", "-soname", PRELOAD_ARTIFACT_NAME)


def rel(path: Path | str) -> str:
    return v2617.rel(path)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


@contextlib.contextmanager
def patched_constants() -> Iterator[None]:
    old_v2617 = {
        "HELPER_SOURCE_REL": v2617.HELPER_SOURCE_REL,
        "HELPER_ARTIFACT_NAME": v2617.HELPER_ARTIFACT_NAME,
        "PRELOAD_ARTIFACT_NAME": v2617.PRELOAD_ARTIFACT_NAME,
        "PRELOAD_LDFLAGS": v2617.PRELOAD_LDFLAGS,
    }
    old_v2613 = {
        "HELPER_SOURCE_REL": v2617.v2613.HELPER_SOURCE_REL,
        "HELPER_ARTIFACT_NAME": v2617.v2613.HELPER_ARTIFACT_NAME,
        "PRELOAD_ARTIFACT_NAME": v2617.v2613.PRELOAD_ARTIFACT_NAME,
        "PRELOAD_LDFLAGS": v2617.v2613.PRELOAD_LDFLAGS,
    }
    v2617.HELPER_SOURCE_REL = HELPER_SOURCE_REL
    v2617.HELPER_ARTIFACT_NAME = HELPER_ARTIFACT_NAME
    v2617.PRELOAD_ARTIFACT_NAME = PRELOAD_ARTIFACT_NAME
    v2617.PRELOAD_LDFLAGS = PRELOAD_LDFLAGS
    v2617.v2613.HELPER_SOURCE_REL = HELPER_SOURCE_REL
    v2617.v2613.HELPER_ARTIFACT_NAME = HELPER_ARTIFACT_NAME
    v2617.v2613.PRELOAD_ARTIFACT_NAME = PRELOAD_ARTIFACT_NAME
    v2617.v2613.PRELOAD_LDFLAGS = PRELOAD_LDFLAGS
    try:
        yield
    finally:
        v2617.HELPER_SOURCE_REL = old_v2617["HELPER_SOURCE_REL"]
        v2617.HELPER_ARTIFACT_NAME = old_v2617["HELPER_ARTIFACT_NAME"]
        v2617.PRELOAD_ARTIFACT_NAME = old_v2617["PRELOAD_ARTIFACT_NAME"]
        v2617.PRELOAD_LDFLAGS = old_v2617["PRELOAD_LDFLAGS"]
        v2617.v2613.HELPER_SOURCE_REL = old_v2613["HELPER_SOURCE_REL"]
        v2617.v2613.HELPER_ARTIFACT_NAME = old_v2613["HELPER_ARTIFACT_NAME"]
        v2617.v2613.PRELOAD_ARTIFACT_NAME = old_v2613["PRELOAD_ARTIFACT_NAME"]
        v2617.v2613.PRELOAD_LDFLAGS = old_v2613["PRELOAD_LDFLAGS"]


def source_state() -> dict[str, Any]:
    helper_path = ROOT / HELPER_SOURCE_REL
    preinit_path = ROOT / v2617.v2613.PREINIT_SOURCE_REL
    tap_path = ROOT / v2617.v2613.ACDBTAP_SOURCE_REL
    ioctl_path = ROOT / v2617.v2613.v2611.v2608.v2572.IOCTL_SOURCE_REL
    helper = read_text(helper_path)
    preinit = read_text(preinit_path)
    tap = read_text(tap_path)
    ioctl = read_text(ioctl_path)
    combined = "\n".join([helper, preinit, tap, ioctl])
    tap_extra_cflags = tuple(v2617.v2613.v2611.v2608.v2600.TAP_EXTRA_CFLAGS)
    init_pos = helper.find("init_ret = acdb_loader_init_v3")
    arm_pos = helper.find("a90_arm_capture()")
    prelude_pos = helper.find("a90_run_safe_prelude()")
    vol_pos = helper.find("a90_run_vol_sweep()")
    required = {
        "helper_source_exists": helper_path.exists(),
        "preinit_source_exists": preinit_path.exists(),
        "tap_source_exists": tap_path.exists(),
        "ioctl_source_exists": ioctl_path.exists(),
        "helper_prepares_empty_meta_list": "a90_prepare_empty_meta_list" in helper,
        "helper_calls_init_v3_with_meta_head": "acdb_loader_init_v3(A90_ACDB_FILES_PATH, A90_DELTA_DIR, meta_head)" in helper,
        "helper_arms_after_init_before_vol": init_pos >= 0 and arm_pos > init_pos and vol_pos > arm_pos,
        "helper_runs_safe_prelude_before_vol": prelude_pos >= 0 and vol_pos > prelude_pos,
        "helper_declares_direct_acdb_ioctl": "extern int32_t acdb_ioctl" in helper,
        "helper_does_not_call_send_audio_cal_v5": "acdb_loader_send_audio_cal_v5" not in helper,
        "helper_has_only_safe_prelude_commands": all(token in helper for token in ("0x0001122eU", "0x0001122dU")),
        "helper_has_bounded_vol_sweep": "A90_VOL_MAX_GAIN_STEP 15U" in helper and "0x0001326dU" in helper and "0x0001326eU" in helper,
        "helper_skips_v2618_crash_tail_meta": "0x00012eeb" not in helper and "tail-meta" not in helper,
        "helper_skips_afe_audproc_matrix": all(token not in helper for token in ("0x00013265U", "0x00013269U", "0x0001326fU", "0x000130d8U", "0x00013271U")),
        "helper_has_indirect_output_buffer": "A90_MATRIX_CAPACITY 0x5000U" in helper and "(uint32_t)(uintptr_t)a90_out" in helper,
        "preinit_still_no_send": "return_to_init_v3_no_arm_no_send" in preinit and "a90_real_send_audio_cal_v5" not in preinit,
        "preinit_still_patches_init_flag": "A90_LOADER_INIT_FLAG_OFF" in preinit and "*flag = 1U" in preinit,
        "tap_manual_arm_exported": "void a90_arm_capture(void)" in tap,
        "tap_unarmed_real_only_path": "if (!a90_armed)" in tap and "return ret;" in tap,
        "tap_auto_arm_disabled_by_build_flags": "-DA90_ACDBTAP_AUTO_ARM_ON_INITIALIZE=0" in tap_extra_cflags,
        "tap_exit_on_target_disabled_by_build_flags": "-DA90_ACDBTAP_EXIT_ON_TARGET=0" in tap_extra_cflags,
        "tap_layout_dump_enabled": "a90_log_command_layout_indirect_captures" in tap,
        "tap_capture_inbuf_capable": "A90_ACDBTAP_CAPTURE_INBUF" in tap and '"in"' in tap,
        "ioctl_fake_allocate_env": "A90_ACDB_FAKE_ALLOCATE" in ioctl,
        "ioctl_fakes_set_in_fake_mode": "A90_AUDIO_SET_CALIBRATION" in ioctl and "fake-success" in ioctl,
    }
    prohibited = {
        "helper_passes_zero_arg3": "acdb_loader_init_v3(A90_ACDB_FILES_PATH, A90_DELTA_DIR, 0U)" in helper,
        "helper_calls_send_audio_cal_v5": "acdb_loader_send_audio_cal_v5" in helper,
        "helper_opens_msm_audio_cal": 'open("/dev/msm_audio_cal' in helper or "open('/dev/msm_audio_cal" in helper,
        "helper_audio_set_literal": "0xC00461CB" in helper or "AUDIO_SET_CALIBRATION" in helper,
        "helper_v2618_crash_cmd_literal": "0x00012eeb" in helper,
        "preinit_exits_process": "exit_group" in preinit or "A90_NR_EXIT_GROUP" in preinit,
        "combined_global_pthread_hooks": "pthread_mutex_lock" in combined or "pthread_mutex_unlock" in combined,
        "combined_android_log_hook": "__android_log_print" in combined,
        "native_speaker_write": any(token in combined for token in ("tinyplay", "tinymix", "AudioTrack")),
        "persistent_magisk_install": "magisk --install-module" in combined,
    }
    return {
        "sources": [HELPER_SOURCE_REL, v2617.v2613.PREINIT_SOURCE_REL, v2617.v2613.ACDBTAP_SOURCE_REL, v2617.v2613.v2611.v2608.v2572.IOCTL_SOURCE_REL],
        "required": required,
        "required_ok": all(required.values()),
        "prohibited": prohibited,
        "prohibited_ok": not any(prohibited.values()),
        "vol_isolated_matrix": {
            "safe_prelude_commands": ["0x1122e", "0x1122d"],
            "skipped_v2618_crash_command": "0x12eeb",
            "vol_sweep": {"commands": ["0x1326d", "0x1326e"], "gain_steps": list(range(16))},
            "max_direct_calls": 34,
            "live_boundary": "future Android-good own-process run only; no native replay SET",
        },
        "armed_capture_contract": {
            "unarmed": "all init-time acdb_ioctl calls pass through with no dump/hash/file I/O",
            "arm_point": "helper calls a90_arm_capture only after acdb_loader_init_v3 returns 0",
            "auto_arm_on_initialize": False,
            "exit_on_first_4916": False,
            "reason_exit_disabled": "V2620 is a VOL isolation run; keep all VOL rows if live succeeds",
        },
    }


def build(build_root: Path, *, clang: Path, lld: Path, readelf: str, file_cmd: str) -> dict[str, Any]:
    with patched_constants():
        build_state = v2617.v2613.build(build_root, clang=clang, lld=lld, readelf=readelf, file_cmd=file_cmd)
    artifacts = build_state.get("artifacts", {}) if isinstance(build_state, dict) else {}
    helper = artifacts.get("helper", {}) if isinstance(artifacts, dict) else {}
    preload = artifacts.get("preload", {}) if isinstance(artifacts, dict) else {}
    helper_sym = helper.get("symbols", {}).get("stdout", "") if isinstance(helper, dict) else ""
    preload_dyn = preload.get("dynamic", {}).get("stdout", "") if isinstance(preload, dict) else ""
    helper_checks = helper.setdefault("checks", {}) if isinstance(helper, dict) else {}
    helper_checks.pop("undefined_send_audio_cal_v5", None)
    helper_checks.update({
        "undefined_acdb_ioctl": " UND acdb_ioctl" in helper_sym,
        "undefined_init_v3": " UND acdb_loader_init_v3" in helper_sym,
        "undefined_or_weak_a90_arm_capture": " a90_arm_capture" in helper_sym,
        "does_not_reference_send_audio_cal_v5": "acdb_loader_send_audio_cal_v5" not in helper_sym,
        "does_not_reference_tail_meta_cmd": "00012eeb" not in helper_sym.lower(),
    })
    if isinstance(helper, dict):
        helper["ok"] = bool(helper.get("file", {}).get("ok") and all(helper_checks.values()))
    preload_checks = preload.setdefault("checks", {}) if isinstance(preload, dict) else {}
    preload_checks.pop("soname_v2613", None)
    preload_checks.update({"soname_v2620": f"Library soname: [{PRELOAD_ARTIFACT_NAME}]" in preload_dyn})
    if isinstance(preload, dict):
        preload["ok"] = bool(preload.get("file", {}).get("ok") and all(preload_checks.values()))
    build_state["ok"] = bool(helper.get("ok") and preload.get("ok")) if isinstance(build_state, dict) else False
    return build_state


def make_payload(args: argparse.Namespace) -> dict[str, Any]:
    source = source_state()
    vendor = v2617.v2613.v2611.v2608.v2572.vendor_lib_state(args.readelf)
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
            "no_real_audio_set": "direct helper does not open /dev/msm_audio_cal; preload fake-successes any accidental SET in fake mode",
        },
        "capture_contract": {
            "base": "V2611 meta-list init + V2608 no-send preinit + V2613 indirect-layout tap",
            "postinit": "init_v3 return -> a90_arm_capture -> safe prelude -> VOL direct GET sweep",
            "does_not_call": "acdb_loader_send_audio_cal_v5",
            "skips": "V2618 crash command 0x12eeb and the already-captured AFE/AUDPROC matrix",
            "success_discriminator": "future live ACDB captures require ret==0 plus non-all-zero indirect payloads",
            "purpose": "isolate VOL 0x1326d/0x1326e from the V2618 tail-meta SIGSEGV",
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


def write_report(payload: dict[str, Any], path: Path) -> None:
    helper = payload.get("build", {}).get("artifacts", {}).get("helper", {})
    preload = payload.get("build", {}).get("artifacts", {}).get("preload", {})
    matrix = payload.get("sources", {}).get("vol_isolated_matrix", {})
    lines = [
        "# NATIVE_INIT V2620 — ACDB VOL-isolated build",
        "",
        "Date: 2026-06-16",
        "",
        "## Scope",
        "",
        "Host-only build-only unit after V2618/V2619. V2618 captured AFE/AUDPROC",
        "payload candidates but SIGSEGVed after entering `0x12eeb` before the VOL",
        "sweep. V2620 builds a helper/preload pair that keeps the proven init and",
        "manual-arm capture path, skips `0x12eeb`, and runs only the safe prelude plus",
        "VOL direct GET commands. No device handoff or native replay occurred.",
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
        "## Contract",
        "",
        f"- safe_prelude_commands: `{matrix.get('safe_prelude_commands')}`",
        f"- skipped_v2618_crash_command: `{matrix.get('skipped_v2618_crash_command')}`",
        f"- vol_sweep: `{matrix.get('vol_sweep')}`",
        "- `acdb_ioctl` capture stays unarmed during init and arms only after `init_v3` returns.",
        "- `send_audio_cal_v5`, `/dev/msm_audio_cal` open, native replay `SET`, and speaker writes are absent.",
        "- Live execution is deferred to the next checked Android-good handoff unit.",
        "",
        "## Validation",
        "",
        "- `python3 -m py_compile workspace/public/src/scripts/revalidation/build_android_acdb_vol_isolated_v2620.py tests/test_build_android_acdb_vol_isolated_v2620.py`",
        "- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_build_android_acdb_vol_isolated_v2620 -v`",
        "- `python3 workspace/public/src/scripts/revalidation/build_android_acdb_vol_isolated_v2620.py --build`",
        "- `git diff --check`",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--build-root", type=Path, default=DEFAULT_BUILD_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--write-report", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--clang", type=Path, default=v2617.v2613.v2611.v2608.v2572.TOOLCHAIN_ROOT / "bin/clang")
    parser.add_argument("--lld", type=Path, default=v2617.v2613.v2611.v2608.v2572.TOOLCHAIN_ROOT / "bin/ld.lld")
    parser.add_argument("--readelf", default="readelf")
    parser.add_argument("--file", default="file")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = make_payload(args)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.manifest.chmod(0o600)
    if args.write_report:
        write_report(payload, args.report)
    print(json.dumps({
        "decision": BUILD_TAG,
        "ok": payload.get("ok"),
        "build_root": rel(args.build_root),
        "manifest": rel(args.manifest),
        "helper": payload.get("build", {}).get("artifacts", {}).get("helper", {}).get("path"),
        "preload": payload.get("build", {}).get("artifacts", {}).get("preload", {}).get("path"),
    }, indent=2, sort_keys=True))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
