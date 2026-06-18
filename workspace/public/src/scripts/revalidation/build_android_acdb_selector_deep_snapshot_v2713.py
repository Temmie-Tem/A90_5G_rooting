#!/usr/bin/env python3
"""Build V2713 ACDB lower selector deep-snapshot artifacts.

V2712 pinned the frontier to selected cal10/cal14 selector and payload semantics. This
host-only build unit keeps the V2703 lower hidden-node large-buffer GET path but
adds a bounded node/block deep snapshot before each GET so a future live run can
inspect loader-internal selector state instead of replaying exhausted payloads.

No Android handoff, device flash, real audio SET, native replay, mixer, PCM, or
speaker write happens in this build unit.
"""

from __future__ import annotations

import argparse
import contextlib
import json
from pathlib import Path
from typing import Any, Iterator

import build_android_acdb_lower_ptrtarget_capture_v2692 as v2692

ROOT = v2692.ROOT
RUN_ID = "V2713"
BUILD_TAG = "v2713-acdb-selector-deep-snapshot-build-only"
DEFAULT_BUILD_ROOT = ROOT / "workspace/private/builds/audio" / BUILD_TAG
DEFAULT_MANIFEST = DEFAULT_BUILD_ROOT / "manifest.json"
DEFAULT_REPORT = ROOT / "docs/reports/NATIVE_INIT_V2713_AUDIO_ACDB_SELECTOR_DEEP_SNAPSHOT_BUILD_2026-06-18.md"

HELPER_SOURCE_REL = v2692.HELPER_SOURCE_REL
PREINIT_SOURCE_REL = "workspace/public/src/android/acdb_payload_capture/libacdb_selector_deep_snapshot_inhook_v2713.c"
ACDBTAP_SOURCE_REL = "workspace/public/src/android/acdb_payload_capture/libacdbtap_lower_large_get_v2703.c"
HELPER_ARTIFACT_NAME = "a90_acdb_selector_deep_snapshot_exec_linked_v2713"
PRELOAD_ARTIFACT_NAME = "liba90_acdb_selector_deep_snapshot_combined_preload_v2713.so"
PRELOAD_LDFLAGS = ("-shared", "--allow-shlib-undefined", "-soname", PRELOAD_ARTIFACT_NAME)
TARGET_CAL_TYPES = [24, 10, 14]
TARGET_GET_COMMANDS = {24: "0x000130da", 10: "0x00011394", 14: "0x00012e01"}
LARGE_GET_BYTES = 65536


def rel(path: Path | str) -> str:
    return v2692.rel(path)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


@contextlib.contextmanager
def patched_v2692_constants() -> Iterator[None]:
    old = {
        "helper_source": v2692.HELPER_SOURCE_REL,
        "preinit_source": v2692.PREINIT_SOURCE_REL,
        "acdbtap_source": v2692.ACDBTAP_SOURCE_REL,
        "helper_artifact": v2692.HELPER_ARTIFACT_NAME,
        "preload_artifact": v2692.PRELOAD_ARTIFACT_NAME,
        "preload_ldflags": v2692.PRELOAD_LDFLAGS,
    }
    v2692.HELPER_SOURCE_REL = HELPER_SOURCE_REL
    v2692.PREINIT_SOURCE_REL = PREINIT_SOURCE_REL
    v2692.ACDBTAP_SOURCE_REL = ACDBTAP_SOURCE_REL
    v2692.HELPER_ARTIFACT_NAME = HELPER_ARTIFACT_NAME
    v2692.PRELOAD_ARTIFACT_NAME = PRELOAD_ARTIFACT_NAME
    v2692.PRELOAD_LDFLAGS = PRELOAD_LDFLAGS
    try:
        with v2692.patched_v2674_constants():
            yield
    finally:
        v2692.HELPER_SOURCE_REL = old["helper_source"]
        v2692.PREINIT_SOURCE_REL = old["preinit_source"]
        v2692.ACDBTAP_SOURCE_REL = old["acdbtap_source"]
        v2692.HELPER_ARTIFACT_NAME = old["helper_artifact"]
        v2692.PRELOAD_ARTIFACT_NAME = old["preload_artifact"]
        v2692.PRELOAD_LDFLAGS = old["preload_ldflags"]


def source_state() -> dict[str, Any]:
    helper_path = ROOT / HELPER_SOURCE_REL
    preinit_path = ROOT / PREINIT_SOURCE_REL
    tap_path = ROOT / ACDBTAP_SOURCE_REL
    ioctl_path = ROOT / v2692.v2674.v2659.v2630.IOCTL_SOURCE_REL
    helper = _read(helper_path)
    preinit = _read(preinit_path)
    tap = _read(tap_path)
    ioctl = _read(ioctl_path)
    combined = "\n".join([helper, preinit, tap, ioctl])

    large_request_pos = preinit.find("get_in[0] = A90_V2703_LARGE_GET_BYTES")
    real_get_pos = preinit.find("get_ret = acdb_ioctl", large_request_pos)
    fake_set_pos = preinit.find("ioctl(-1, A90_AUDIO_SET_CALIBRATION")
    tap_real_pos = tap.find("ret = a90_real_acdb_ioctl(cmd, in, in_len, out, out_len);")
    tap_post_real = tap[tap_real_pos:] if tap_real_pos >= 0 else ""
    adm_indirect_pos = tap.find("ind-lower-adm-custom-topology")
    asm_indirect_pos = tap.find("ind-lower-asm-custom-topology")

    required = {
        "helper_source_exists": helper_path.exists(),
        "preinit_source_exists": preinit_path.exists(),
        "tap_source_exists": tap_path.exists(),
        "ioctl_source_exists": ioctl_path.exists(),
        "preinit_uses_large_get_constant": f"A90_V2703_LARGE_GET_BYTES {LARGE_GET_BYTES}U" in preinit,
        "preinit_declares_ownprocess_buffer": "static uint8_t a90_v2703_large_get_buf[A90_V2703_LARGE_GET_BYTES]" in preinit,
        "preinit_zeros_large_buffer_before_get": "a90_zero_bytes(a90_v2703_large_get_buf, A90_V2703_LARGE_GET_BYTES)" in preinit,
        "preinit_sets_word0_to_large_len": "get_in[0] = A90_V2703_LARGE_GET_BYTES" in preinit,
        "preinit_sets_word1_to_ownprocess_buffer": "get_in[1] = (uint32_t)(uintptr_t)a90_v2703_large_get_buf" in preinit,
        "preinit_large_request_before_get": large_request_pos >= 0 and real_get_pos > large_request_pos,
        "preinit_logs_large_get_markers": "v2703_large_get_request" in preinit and "v2703_large_get_return" in preinit,
        "preinit_logs_selector_deep_snapshot": "v2713_selector_deep_snapshot" in preinit and "A90_V2713_NODE_WORDS 16U" in preinit and "A90_V2713_BLOCK_WORDS 32U" in preinit,
        "preinit_no_fake_set_call": fake_set_pos < 0,
        "preinit_keeps_lower_hidden_route": all(token in preinit for token in ["A90_CREATE_CAL_NODE_OFF 0x0000fd44UL", "A90_ALLOCATE_CAL_BLOCK_OFF 0x0000fbbcUL", "a90_run_lower_hidden_nodes"]),
        "tap_captures_lower_afe_custom_topology": "ind-lower-afe-custom-topology" in tap,
        "tap_captures_lower_adm_custom_topology": "ind-lower-adm-custom-topology" in tap,
        "tap_captures_lower_asm_custom_topology": "ind-lower-asm-custom-topology" in tap,
        "tap_captures_lower_supp_custom_topology": "ind-lower-afe-supp-custom-topology" in tap,
        "tap_indirect_capture_after_real_get": (
            tap_real_pos >= 0
            and "a90_log_command_layout_indirect_captures(seq, cmd, in_len, ret, in, out, out_len)" in tap_post_real
            and adm_indirect_pos >= 0
            and asm_indirect_pos >= 0
        ),
        "tap_retains_zero_buffer_discriminator": "all_zero" in tap and "ret == 0" in tap,
        "tap_retains_65536_capture_cap": "A90_MAX_CAPTURE_LEN 65536U" in tap,
        "ioctl_still_fakes_real_set_if_reached": (
            "always fake AUDIO_SET_CALIBRATION" in ioctl
            and "if (request == A90_AUDIO_SET_CALIBRATION)\n        return 1;" in ioctl
        ),
    }
    prohibited = {
        "helper_opens_msm_audio_cal": "/dev/msm_audio_cal" in helper,
        "preinit_opens_msm_audio_cal": "/dev/msm_audio_cal" in preinit,
        "preinit_calls_audio_set": "ioctl(-1, A90_AUDIO_SET_CALIBRATION" in preinit,
        "tap_opens_msm_audio_cal": "/dev/msm_audio_cal" in tap,
        "combined_native_speaker_write": any(token in combined for token in ("tinyplay", "tinymix", "AudioTrack")),
        "combined_persistent_magisk_install": "magisk --install-module" in combined,
        "combined_global_pthread_hooks": "pthread_mutex_lock" in combined or "pthread_mutex_unlock" in combined,
        "combined_android_log_hook": "__android_log_print" in combined,
    }
    return {
        "sources": [HELPER_SOURCE_REL, PREINIT_SOURCE_REL, ACDBTAP_SOURCE_REL, v2692.v2674.v2659.v2630.IOCTL_SOURCE_REL],
        "required": required,
        "required_ok": all(required.values()),
        "prohibited": prohibited,
        "prohibited_ok": not any(prohibited.values()),
        "v2713_delta": {
            "basis": "V2702 reclassified cal_type 10 ret=-12 as insufficient output buffer",
            "word0": f"force lower custom topology GET input word0 to {LARGE_GET_BYTES}",
            "word1": "force GET input word1 to an own-process output buffer before acdb_ioctl",
            "capture": "extend acdbtap known indirect captures to lower ADM/ASM/AFE custom topology commands",
            "boundary": "do not call fake or real AUDIO_SET_CALIBRATION in the V2713 preinit path",
        },
    }


def build(build_root: Path, *, clang: Path, lld: Path, readelf: str, file_cmd: str) -> dict[str, Any]:
    with patched_v2692_constants():
        build_state = v2692.build(build_root, clang=clang, lld=lld, readelf=readelf, file_cmd=file_cmd)
    artifacts = build_state.get("artifacts", {}) if isinstance(build_state, dict) else {}
    helper = artifacts.get("helper", {}) if isinstance(artifacts, dict) else {}
    preload = artifacts.get("preload", {}) if isinstance(artifacts, dict) else {}
    preload_symbols = preload.get("symbols", {}).get("stdout", "") if isinstance(preload, dict) else ""
    preload_dynamic = preload.get("dynamic", {}).get("stdout", "") if isinstance(preload, dict) else ""

    if isinstance(preload, dict):
        checks = preload.setdefault("checks", {})
        if isinstance(checks, dict):
            checks.pop("soname_v2692", None)
            checks["soname_v2713"] = f"Library soname: [{PRELOAD_ARTIFACT_NAME}]" in preload_dynamic
            checks["exports_common_hook"] = " acdb_loader_send_common_custom_topology" in preload_symbols
            checks["exports_lower_runner"] = " a90_run_lower_hidden_nodes" in preload_symbols
            checks["exports_acdb_ioctl"] = " acdb_ioctl" in preload_symbols
            checks["exports_ioctl"] = " ioctl" in preload_symbols
            checks["exports_a90_arm_capture"] = " a90_arm_capture" in preload_symbols
            preload["ok"] = bool(preload.get("exists") and all(checks.values()))
    build_state["ok"] = bool(helper.get("ok") and preload.get("ok"))
    return build_state


def make_payload(args: argparse.Namespace) -> dict[str, Any]:
    source = source_state()
    vendor = v2692.v2674.v2659.v2630.v2613.v2611.v2608.v2572.vendor_lib_state(args.readelf)
    if args.build:
        build_state = build(args.build_root, clang=args.clang, lld=args.lld, readelf=args.readelf, file_cmd=args.file)
    else:
        build_state = {"ok": True, "built": False, "reason": "pass --build to materialize private ARM32 artifacts"}
    artifacts = build_state.get("artifacts", {}) if isinstance(build_state, dict) else {}
    helper = artifacts.get("helper", {}) if isinstance(artifacts, dict) else {}
    preload = artifacts.get("preload", {}) if isinstance(artifacts, dict) else {}
    payload: dict[str, Any] = {
        "run_id": RUN_ID,
        "build_tag": BUILD_TAG,
        "host_only_build": True,
        "measurement_boundary": {
            "no_live_default": True,
            "no_native_replay": True,
            "no_speaker_write": True,
            "raw_payload_private_only": True,
            "preinit_no_audio_set_call": True,
            "fake_audio_cal_env": "A90_ACDB_FAKE_ALLOCATE=1",
            "real_set_still_blocked": "linked V2630 ioctl shim would fake-success AUDIO_SET_CALIBRATION if any dependency reaches it",
        },
        "capture_contract": {
            "call_order": "acdb_loader_init_v3 -> common hook -> patch initialized -> arm acdbtap -> lower hidden nodes -> large-buffer GET -> exit_group(0)",
            "target_cal_types": TARGET_CAL_TYPES,
            "get_commands": TARGET_GET_COMMANDS,
            "large_get_bytes": LARGE_GET_BYTES,
            "success_discriminator": "future live run must capture v2713_selector_deep_snapshot rows for cal_type 24/10/14 plus ret==0 non-all-zero indirect lower custom topology buffers; raw bytes private only",
            "v2702_dependency": "V2702 showed cal_type 10 ret=-12 came from the word0 insufficient-buffer branch, so V2703 changes word0 and word1 before the real GET",
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
        and (not args.build or (helper.get("ok") and preload.get("ok")))
    )
    return payload


def write_report(payload: dict[str, Any], report_path: Path) -> None:
    helper = payload.get("build", {}).get("artifacts", {}).get("helper", {})
    preload = payload.get("build", {}).get("artifacts", {}).get("preload", {})
    lines = [
        "# NATIVE_INIT V2713 — ACDB selector deep-snapshot build",
        "",
        "Date: 2026-06-18",
        "",
        "## Scope",
        "",
        "Host-only build-only unit. No Android handoff, device flash, native replay,",
        "real or fake `AUDIO_SET_CALIBRATION` call from the V2713 preinit path, mixer",
        "write, PCM write, speaker playback, or raw ACDB payload publication occurred.",
        "Private build artifacts stay under `workspace/private`.",
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
        "V2712 closed existing replay candidates and left the selected cal10/cal14 selector contract as the active frontier.",
        "V2704 already captured successful large-buffer lower GETs, but its shallow block snapshot showed the visible selector words are identical across cal24/10/14.",
        "V2713 therefore adds a bounded deep snapshot of loader-internal node/block words before each lower GET.",
        "",
        "The V2702 finding still applies: `AcdbCmdGetAudioCOPPTopologyData` returns `-12` from the",
        "insufficient output-buffer branch after comparing request `word0` with the",
        "ACDB table required size. The V2703/V2713 path therefore stops treating cal_type `10` as",
        "absent and prepares a larger own-process destination buffer for the lower",
        "custom-topology GET commands.",
        "",
        "## Capture Contract",
        "",
        f"- `word0`: force GET destination capacity to `{LARGE_GET_BYTES}` bytes",
        "- `word1`: force GET destination pointer to an own-process buffer",
        "- selector snapshot: dump `v2713_selector_deep_snapshot` rows with 16 node words and 32 block words for cal_type `24`, `10`, and `14`",
        "- ACDB tap: dump lower ADM/ASM/AFE custom-topology indirect outputs after `ret==0`",
        "- success: future live run needs all three selector snapshot rows plus `ret==0` non-all-zero indirect buffers for cal_type `10` and `14`",
        "- boundary: raw bytes stay private; native replay remains parked until selected payloads are recovered",
        "",
        "## Source Checks",
        "",
        f"- required_ok: `{payload.get('sources', {}).get('required_ok')}`",
        f"- prohibited_ok: `{payload.get('sources', {}).get('prohibited_ok')}`",
        f"- helper_checks: `{helper.get('checks')}`",
        f"- preload_checks: `{preload.get('checks')}`",
        "",
        "## Next Unit",
        "",
        "A future live Android-good handoff can stage the V2713 helper/preload through",
        "the existing V2693/V2490 engine, force `A90_ACDB_FAKE_ALLOCATE=1`, pull the",
        "full private event/acdbtap output, roll back to V2321, and report only metadata",
        "for selector words and lower custom-topology indirect buffers. Native replay remains blocked.",
        "",
        "## Validation",
        "",
        "- `python3 -m py_compile workspace/public/src/scripts/revalidation/build_android_acdb_selector_deep_snapshot_v2713.py tests/test_build_android_acdb_selector_deep_snapshot_v2713.py`",
        "- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_build_android_acdb_selector_deep_snapshot_v2713 -v`",
        "- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/build_android_acdb_selector_deep_snapshot_v2713.py --build --write-report`",
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
    parser.add_argument("--clang", type=Path, default=v2692.v2674.v2659.v2630.v2613.v2611.v2608.v2572.TOOLCHAIN_ROOT / "bin/clang")
    parser.add_argument("--lld", type=Path, default=v2692.v2674.v2659.v2630.v2613.v2611.v2608.v2572.TOOLCHAIN_ROOT / "bin/ld.lld")
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
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
