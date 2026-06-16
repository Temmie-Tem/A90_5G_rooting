#!/usr/bin/env python3
"""V2621 Android handoff wrapper for the V2620 ACDB VOL-isolated helper.

Host-only by default.  Live mode reuses the V2490 checked Android
boot/stage/pull/rollback engine, but selects the V2620 helper/preload artifacts
and classifies only the VOL-isolated direct GET sweep.  The live action remains
measurement-only: no native replay SET, no speaker write, and raw buffers stay
under workspace/private.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import build_android_acdb_vol_isolated_v2620 as v2620
import native_audio_acdb_direct_matrix_live_handoff_v2618 as v2618
import native_audio_acdb_ownprocess_get_live_handoff_v2490 as v2490
import native_audio_acdb_perdevice_indirect_capture_live_handoff_v2573 as v2573

ROOT = v2620.ROOT
RUN_ID = "V2621"
BUILD_TAG = "v2621-audio-acdb-vol-isolated-live-runner"
DEFAULT_OUT_BASE = ROOT / "workspace/private/runs/audio"
DEFAULT_REPORT = ROOT / "docs/reports/NATIVE_INIT_V2621_AUDIO_ACDB_VOL_ISOLATED_LIVE_HANDOFF_2026-06-16.md"

VOL_SIZE_CMD = "0x0001326d"
VOL_DATA_CMD = "0x0001326e"
VOL_BUFFER_LABEL = "ind-ap-gain"


def rel(path: Path | str) -> str:
    return v2573.rel(path)


def default_live_out_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return DEFAULT_OUT_BASE / f"v2621-acdb-vol-isolated-{stamp}"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return v2573.read_jsonl(path)


def int_or_none(value: Any) -> int | None:
    return v2573.int_or_none(value)


def int32_or_none(value: Any) -> int | None:
    return v2573.int32_or_none(value)


def cmd_text(value: Any) -> str:
    return v2618._cmd_text(value)


def build_v2620_artifacts(args: argparse.Namespace) -> dict[str, Any]:
    build_args = argparse.Namespace(
        build=True,
        write_report=False,
        build_root=args.v2620_build_root,
        manifest=args.v2620_manifest_path,
        report=v2620.DEFAULT_REPORT,
        clang=v2620.v2617.v2613.v2611.v2608.v2572.TOOLCHAIN_ROOT / "bin/clang",
        lld=v2620.v2617.v2613.v2611.v2608.v2572.TOOLCHAIN_ROOT / "bin/ld.lld",
        readelf=args.readelf,
        file=args.file,
    )
    payload = v2620.make_payload(build_args)
    args.v2620_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    args.v2620_manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def read_v2620_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"ok": False, "error": f"manifest missing: {rel(path)}"}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return {"ok": False, "error": f"manifest json error: {error}"}
    build = payload.get("build", {})
    artifacts = build.get("artifacts", {})
    helper = artifacts.get("helper", {})
    preload = artifacts.get("preload", {})
    source_state = payload.get("sources", {})
    required = source_state.get("required", {})
    prohibited = source_state.get("prohibited", {})
    armed_contract = source_state.get("armed_capture_contract", {})
    return {
        "ok": bool(payload.get("ok") and helper.get("ok") and preload.get("ok")),
        "path": rel(path),
        "manifest": payload,
        "helper": helper,
        "preload": preload,
        "vol_isolated_contract_ok": bool(
            required.get("helper_calls_init_v3_with_meta_head")
            and required.get("helper_arms_after_init_before_vol")
            and required.get("helper_runs_safe_prelude_before_vol")
            and required.get("helper_has_bounded_vol_sweep")
            and required.get("helper_skips_v2618_crash_tail_meta")
            and required.get("helper_skips_afe_audproc_matrix")
            and required.get("tap_manual_arm_exported")
            and required.get("tap_auto_arm_disabled_by_build_flags")
            and required.get("tap_exit_on_target_disabled_by_build_flags")
            and required.get("ioctl_fake_allocate_env")
            and not prohibited.get("helper_calls_send_audio_cal_v5")
            and not prohibited.get("helper_audio_set_literal")
            and not prohibited.get("helper_opens_msm_audio_cal")
        ),
        "armed_contract_ok": bool(
            armed_contract.get("auto_arm_on_initialize") is False
            and armed_contract.get("exit_on_first_4916") is False
        ),
        "capture_contract": payload.get("capture_contract", {}),
    }


def selected_artifacts(args: argparse.Namespace) -> dict[str, Any]:
    if args.build_v2620_artifacts:
        build_v2620_artifacts(args)
    manifest = read_v2620_manifest(args.v2620_manifest_path)
    helper = v2573.artifact_from_manifest(manifest.get("helper", {}), args.helper_path, args.helper_sha256)
    preload = v2573.artifact_from_manifest(manifest.get("preload", {}), args.preload_path, args.preload_sha256)
    return {
        "manifest": manifest,
        "helper": helper,
        "preload": preload,
        "ok": bool(
            manifest.get("ok")
            and manifest.get("vol_isolated_contract_ok")
            and manifest.get("armed_contract_ok")
            and helper.get("ok")
            and preload.get("ok")
        ),
    }


def to_v2490_args(args: argparse.Namespace, artifacts: dict[str, Any]) -> argparse.Namespace:
    return v2618.to_v2490_args(args, artifacts)


def select_pulled_dir_from_result(result: dict[str, Any]) -> Path | None:
    return v2573.select_pulled_dir_from_result(result)


def is_vol_payload_row(state: dict[str, Any]) -> bool:
    return bool(
        state.get("ret") == 0
        and state.get("valid_raw")
        and state.get("nonzero")
        and cmd_text(state.get("cmd")) == VOL_DATA_CMD
        and state.get("buffer") == VOL_BUFFER_LABEL
        and state.get("out_len") not in {None, 0, 4}
    )


def summarize_vol_isolated_capture(artifact_dir: Path) -> dict[str, Any]:
    base_summary = v2490.parse_ownget_artifacts(artifact_dir)
    helper_events_path = artifact_dir / "acdb-v2620-vol-isolated-events.jsonl"
    helper_events = read_jsonl(helper_events_path)
    helper_stages = [
        event.get("stage")
        for event in helper_events
        if event.get("event") == "v2620_vol_isolated"
    ]
    case_rows = [
        event
        for event in helper_events
        if event.get("event") == "v2620_vol_isolated" and event.get("stage") == "case_return"
    ]
    case_names = [str(event.get("case", "")) for event in case_rows]
    vol_size_case_rows = [event for event in case_rows if event.get("case") == "vol-size"]
    vol_data_case_rows = [event for event in case_rows if event.get("case") == "vol-data"]
    vol_size_ret_values = sorted({value for value in (int32_or_none(event.get("ret")) for event in vol_size_case_rows) if value is not None})
    vol_data_ret_values = sorted({value for value in (int32_or_none(event.get("ret")) for event in vol_data_case_rows) if value is not None})
    vol_size_ret0_steps = [
        int_or_none(event.get("step"))
        for event in vol_size_case_rows
        if int_or_none(event.get("step")) is not None and int32_or_none(event.get("ret")) == 0
    ]
    vol_data_ret0_steps = [
        int_or_none(event.get("step"))
        for event in vol_data_case_rows
        if int_or_none(event.get("step")) is not None and int32_or_none(event.get("ret")) == 0
    ]
    acdbtap_dir = artifact_dir / "acdbtap"
    if not (acdbtap_dir / "acdbtap-events.jsonl").exists() and (artifact_dir / "acdbtap-events.jsonl").exists():
        acdbtap_dir = artifact_dir
    rows = base_summary.get("acdbtap_rows", [])
    record_states = [v2573.row_raw_state(row, acdbtap_dir) for row in rows]
    successful = [
        item for item in record_states
        if item.get("ret") == 0 and item.get("valid_raw") and item.get("nonzero")
    ]
    vol_size_indirect_rows = [
        item for item in record_states
        if cmd_text(item.get("cmd")) == VOL_SIZE_CMD and item.get("ret") == 0 and item.get("valid_raw")
    ]
    vol_request_in_rows = [
        item for item in record_states
        if cmd_text(item.get("cmd")) in {VOL_SIZE_CMD, VOL_DATA_CMD}
        and item.get("buffer") == "in"
        and item.get("valid_raw")
    ]
    vol_payloads = [item for item in successful if is_vol_payload_row(item)]
    topology = [item for item in successful if item.get("out_len") == 4916]
    ioctl_events = base_summary.get("ioctl_trace_events", [])
    pass_through_set_events = [
        event for event in ioctl_events
        if event.get("name") == "AUDIO_SET_CALIBRATION" and event.get("intercept") != "fake-success"
    ]
    fake_set_events = [
        event for event in ioctl_events
        if event.get("name") == "AUDIO_SET_CALIBRATION" and event.get("intercept") == "fake-success"
    ]
    helper_done = "done" in helper_stages
    vol_sweep_seen = "before_vol_sweep" in helper_stages
    if pass_through_set_events:
        classification = "v2621-boundary-violation-real-audio-set-passthrough"
    elif vol_payloads:
        classification = "v2621-vol-isolated-vol-captured"
    elif vol_sweep_seen and vol_data_case_rows:
        classification = "v2621-vol-isolated-vol-sweep-no-payload"
    elif helper_events:
        classification = "v2621-helper-events-before-vol-sweep"
    else:
        classification = f"v2621-{base_summary.get('classification', 'no-artifacts')}"
    return {
        "classification": classification,
        "success": classification == "v2621-vol-isolated-vol-captured",
        "partial_success": classification in {
            "v2621-vol-isolated-vol-sweep-no-payload",
            "v2621-helper-events-before-vol-sweep",
        },
        "operator_valuable": bool(vol_payloads or vol_size_indirect_rows or vol_data_case_rows or rows),
        "helper_event_path": rel(helper_events_path),
        "helper_event_count": len(helper_events),
        "helper_stages": helper_stages,
        "case_return_count": len(case_rows),
        "case_names": case_names,
        "helper_done": helper_done,
        "safe_prelude_seen": "before_safe_prelude" in helper_stages,
        "vol_sweep_seen": vol_sweep_seen,
        "vol_size_case_count": len(vol_size_case_rows),
        "vol_data_case_count": len(vol_data_case_rows),
        "vol_size_ret_values": vol_size_ret_values,
        "vol_data_ret_values": vol_data_ret_values,
        "vol_size_ret0_steps": vol_size_ret0_steps,
        "vol_data_ret0_steps": vol_data_ret0_steps,
        "vol_size_ret_failed_count": sum(1 for event in vol_size_case_rows if int32_or_none(event.get("ret")) != 0),
        "vol_data_ret_failed_count": sum(1 for event in vol_data_case_rows if int32_or_none(event.get("ret")) != 0),
        "successful_nonzero_count": len(successful),
        "topology_success_count": len(topology),
        "vol_request_in_buffer_count": len(vol_request_in_rows),
        "vol_size_indirect_count": len(vol_size_indirect_rows),
        "vol_payload_count": len(vol_payloads),
        "fake_audio_set_count": len(fake_set_events),
        "real_audio_set_pass_through_count": len(pass_through_set_events),
        "ordered_records": record_states,
        "base_summary": base_summary,
    }


def dry_run_payload(args: argparse.Namespace) -> dict[str, Any]:
    artifacts = selected_artifacts(args)
    base_args = to_v2490_args(args, artifacts) if artifacts.get("ok") else None
    base_payload = v2490.dry_run_payload(base_args) if base_args else {}
    payload: dict[str, Any] = {
        "run_id": RUN_ID,
        "build_tag": BUILD_TAG,
        "decision": "v2621-acdb-vol-isolated-live-runner-dry-run",
        "host_only": True,
        "device_action": "none",
        "operator_spec": "docs/OPERATOR_ACDB_IOCTL_INTERPOSE_CAPTURE_SPEC_2026-06-15.md",
        "v2620_artifacts": artifacts,
        "v2490_engine": {
            "run_id": "V2490",
            "decision": base_payload.get("decision"),
            "live_ready": base_payload.get("live_ready", False),
            "command_safety": base_payload.get("command_safety"),
            "commands": base_payload.get("commands", {}),
        },
        "capture_contract": {
            "vol_isolated": "safe prelude plus VOL 0x1326d/0x1326e gain-step sweep 0..15",
            "manual_arm_after_init": True,
            "auto_arm_on_initialize": False,
            "exit_on_first_4916": False,
            "fake_audio_cal_allocate": True,
            "combined_preload": True,
            "success_requires": "ret==0 plus non-all-zero raw ind-ap-gain buffers; requested length alone is not success",
            "native_replay": "blocked; no SET replay in this runner",
            "raw_private_only": True,
        },
    }
    payload["live_ready"] = bool(artifacts.get("ok") and base_payload.get("live_ready"))
    payload["live_blockers"] = []
    if not artifacts.get("ok"):
        payload["live_blockers"].append("V2620 VOL-isolated helper/preload artifacts are not ready")
    payload["live_blockers"].extend(base_payload.get("live_blockers", []))
    payload["command_safety"] = base_payload.get("command_safety", {"ok": False, "findings": ["base payload missing"]})
    payload["ok"] = bool(payload["live_ready"] and payload["command_safety"].get("ok"))
    return payload


def run_live(args: argparse.Namespace) -> dict[str, Any]:
    if args.out_dir is None:
        args.out_dir = default_live_out_dir()
    dry = dry_run_payload(args)
    if not dry.get("ok"):
        raise RuntimeError(f"V2621 live inputs are not ready: {dry.get('live_blockers')}")
    artifacts = dry["v2620_artifacts"]
    base_args = to_v2490_args(args, artifacts)
    result = v2490.run_live(base_args)
    pulled_dir = select_pulled_dir_from_result(result)
    summary = summarize_vol_isolated_capture(pulled_dir) if pulled_dir else {
        "classification": "v2621-no-pulled-artifacts",
        "success": False,
        "partial_success": False,
        "operator_valuable": False,
    }
    wrapper = {
        "run_id": RUN_ID,
        "build_tag": BUILD_TAG,
        "decision": f"{summary['classification']}-rollback-{'pass' if result.get('rolled_back') else 'unknown'}",
        "out_dir": result.get("out_dir"),
        "rolled_back": bool(result.get("rolled_back")),
        "counts_toward_fails_twice": result.get("counts_toward_fails_twice"),
        "operator_valuable": bool(summary.get("operator_valuable")),
        "partial_success": bool(summary.get("partial_success")),
        "success": bool(summary.get("success")),
        "v2620_artifacts": artifacts,
        "v2490_engine_result": result,
        "vol_isolated_summary": summary,
        "ok": bool(result.get("rolled_back") and summary.get("operator_valuable")),
    }
    out_dir_raw = result.get("out_dir")
    if out_dir_raw:
        write_json(ROOT / str(out_dir_raw) / "v2621-result.json", wrapper)
    return wrapper


def write_report(path: Path, payload: dict[str, Any]) -> None:
    summary = payload.get("vol_isolated_summary", {})
    artifacts = payload.get("v2620_artifacts", {})
    helper = artifacts.get("helper", {})
    preload = artifacts.get("preload", {})
    lines = [
        "# NATIVE_INIT V2621 — ACDB VOL-isolated live handoff",
        "",
        "Date: 2026-06-16",
        "",
        "## Scope",
        "",
        "Android own-process ACDB VOL-isolated handoff using the V2490 checked Android",
        "boot/stage/pull/rollback engine and the V2620 helper/preload artifacts. This",
        "is measurement-only: no native replay `SET`, no speaker write, and raw buffers",
        "remain under `workspace/private`.",
        "",
        "## Result",
        "",
        f"- decision: `{payload.get('decision')}`",
        f"- ok: `{payload.get('ok')}`",
        f"- rolled_back: `{payload.get('rolled_back')}`",
        f"- counts_toward_fails_twice: `{payload.get('counts_toward_fails_twice')}`",
        f"- operator_valuable: `{payload.get('operator_valuable')}`",
        f"- partial_success: `{payload.get('partial_success')}`",
        f"- out_dir: `{payload.get('out_dir')}`",
        f"- classification: `{summary.get('classification')}`",
        f"- helper_done: `{summary.get('helper_done')}`",
        f"- safe_prelude_seen: `{summary.get('safe_prelude_seen')}`",
        f"- vol_sweep_seen: `{summary.get('vol_sweep_seen')}`",
        f"- case_return_count: `{summary.get('case_return_count')}`",
        f"- vol_size_case_count: `{summary.get('vol_size_case_count')}`",
        f"- vol_data_case_count: `{summary.get('vol_data_case_count')}`",
        f"- vol_size_ret_values: `{summary.get('vol_size_ret_values')}`",
        f"- vol_data_ret_values: `{summary.get('vol_data_ret_values')}`",
        f"- vol_size_ret_failed_count: `{summary.get('vol_size_ret_failed_count')}`",
        f"- vol_data_ret_failed_count: `{summary.get('vol_data_ret_failed_count')}`",
        f"- vol_request_in_buffer_count: `{summary.get('vol_request_in_buffer_count')}`",
        f"- vol_size_indirect_count: `{summary.get('vol_size_indirect_count')}`",
        f"- vol_payload_count: `{summary.get('vol_payload_count')}`",
        f"- real_audio_set_pass_through_count: `{summary.get('real_audio_set_pass_through_count')}`",
        f"- base_classification: `{summary.get('base_summary', {}).get('classification')}`",
        f"- helper_rc: `{summary.get('base_summary', {}).get('diagnostics', {}).get('helper_rc')}`",
        f"- helper_sigsegv: `{summary.get('base_summary', {}).get('diagnostics', {}).get('helper_sigsegv')}`",
        "",
        "## Artifact Selection",
        "",
        f"- helper: `{helper.get('path')}`",
        f"- helper_sha256: `{helper.get('sha256')}`",
        f"- preload: `{preload.get('path')}`",
        f"- preload_sha256: `{preload.get('sha256')}`",
        "",
        "## Contract",
        "",
        "- stages the V2620 helper/preload through the V2490 Android-good handoff engine;",
        "- forces `A90_ACDB_FAKE_ALLOCATE=1`; any real audio-cal SET pass-through is a boundary violation;",
        "- keeps `acdb_ioctl` capture silent before `init_v3` returns and helper calls `a90_arm_capture()`;",
        "- skips the V2618 crash command `0x12eeb` and already-captured AFE/AUDPROC matrix;",
        "- executes only safe prelude plus `0x1326d`/`0x1326e` VOL sweep once;",
        "- pulls `/data/local/tmp/a90-acdb-ownget/` and `acdbtap/` privately; and",
        "- classifies VOL success only from `ret==0` plus non-all-zero `ind-ap-gain` raw buffers.",
        "",
        "## Validation",
        "",
        "- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_acdb_vol_isolated_live_handoff_v2621.py tests/test_native_audio_acdb_vol_isolated_live_handoff_v2621.py`",
        "- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_native_audio_acdb_vol_isolated_live_handoff_v2621 -v`",
        "- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/native_audio_acdb_vol_isolated_live_handoff_v2621.py --dry-run --write-report`",
        "- live run, if present: `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/native_audio_acdb_vol_isolated_live_handoff_v2621.py --run-live --write-report`",
        "- `git diff --check`",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--run-live", action="store_true")
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--build-v2620-artifacts", action="store_true")
    parser.add_argument("--v2620-build-root", type=Path, default=v2620.DEFAULT_BUILD_ROOT)
    parser.add_argument("--v2620-manifest-path", type=Path, default=v2620.DEFAULT_MANIFEST)
    parser.add_argument("--helper-path", type=Path)
    parser.add_argument("--helper-sha256")
    parser.add_argument("--preload-path", type=Path)
    parser.add_argument("--preload-sha256")
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--adb", default="adb")
    parser.add_argument("--serial")
    parser.add_argument("--from-native", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--android-timeout", type=float, default=240.0)
    parser.add_argument("--flash-timeout", type=float, default=420.0)
    parser.add_argument("--adb-command-timeout", type=float, default=90.0)
    parser.add_argument("--adb-pull-timeout", type=float, default=120.0)
    parser.add_argument("--helper-timeout", type=float, default=90.0)
    parser.add_argument("--android-root-recheck-attempts", type=int, default=v2490.v2396.DEFAULT_ANDROID_ROOT_RECHECK_ATTEMPTS)
    parser.add_argument("--android-root-recheck-sleep-sec", type=float, default=v2490.v2396.DEFAULT_ANDROID_ROOT_RECHECK_SLEEP_SEC)
    parser.add_argument("--android-settle-adb-retry-attempts", type=int, default=v2490.DEFAULT_SETTLE_ADB_RETRY_ATTEMPTS)
    parser.add_argument("--android-settle-adb-retry-sleep-sec", type=float, default=v2490.DEFAULT_SETTLE_ADB_RETRY_SLEEP_SEC)
    parser.add_argument("--readelf", default="readelf")
    parser.add_argument("--file", default="file")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.run_live:
        payload = run_live(args)
    else:
        payload = dry_run_payload(args)
    if args.write_report:
        write_report(args.report_path, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
