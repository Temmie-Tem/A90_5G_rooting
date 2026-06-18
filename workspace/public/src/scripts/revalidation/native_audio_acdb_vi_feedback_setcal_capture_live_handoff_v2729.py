#!/usr/bin/env python3
"""V2729 Android handoff wrapper for V2728 vi-feedback ACDB SET capture.

Host-only by default. Live mode reuses the V2490 checked Android
boot/stage/pull/rollback engine, selects the V2728 helper/preload artifacts,
and classifies the captured ``AUDIO_SET_CALIBRATION`` records emitted to
``setcal-events.jsonl``.  The live action remains measurement-only: the V2630
ioctl shim fake-successes SET, so the Android kernel SET is never reached.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import build_android_acdb_vi_feedback_setcal_capture_v2728 as v2728
import native_audio_acdb_ownprocess_get_live_handoff_v2490 as v2490
import native_audio_acdb_perdevice_indirect_capture_live_handoff_v2573 as v2573
import native_audio_acdb_setcal_capture_live_handoff_v2631 as v2631

ROOT = v2728.ROOT
RUN_ID = "V2729"
BUILD_TAG = "v2729-audio-acdb-vi-feedback-setcal-capture-live-runner"
DEFAULT_OUT_BASE = ROOT / "workspace/private/runs/audio"
DEFAULT_REPORT = ROOT / "docs/reports/NATIVE_INIT_V2729_AUDIO_ACDB_VI_FEEDBACK_SETCAL_CAPTURE_LIVE_HANDOFF_2026-06-18.md"
TARGET_CAL_TYPE = 17
SUPPLEMENTAL_CAL_TYPES = {11}


def rel(path: Path | str) -> str:
    return v2573.rel(path)


def default_live_out_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return DEFAULT_OUT_BASE / f"v2729-acdb-vi-feedback-setcal-capture-{stamp}"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return v2573.read_jsonl(path)


def build_v2728_artifacts(args: argparse.Namespace) -> dict[str, Any]:
    build_args = argparse.Namespace(
        build=True,
        write_report=False,
        build_root=args.v2728_build_root,
        manifest=args.v2728_manifest_path,
        report=v2728.DEFAULT_REPORT,
        clang=v2728.v2630.v2613.v2611.v2608.v2572.TOOLCHAIN_ROOT / "bin/clang",
        lld=v2728.v2630.v2613.v2611.v2608.v2572.TOOLCHAIN_ROOT / "bin/ld.lld",
        readelf=args.readelf,
        file=args.file,
    )
    payload = v2728.make_payload(build_args)
    args.v2728_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    args.v2728_manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def read_v2728_manifest(path: Path) -> dict[str, Any]:
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
    sources = payload.get("sources", {})
    required = sources.get("required", {})
    prohibited = sources.get("prohibited", {})
    contract = payload.get("capture_contract", {})
    setcal_contract_ok = bool(
        sources.get("required_ok")
        and sources.get("prohibited_ok")
        and required.get("helper_vi_feedback_tuple")
        and required.get("ioctl_fake_setcal_capture_reused")
        and not prohibited.get("helper_opens_msm_audio_cal")
        and not prohibited.get("helper_issues_ioctl")
        and contract.get("vi_feedback_call", {}).get("acdb_id") == 102
        and contract.get("vi_feedback_call", {}).get("app_type") == "0x11132"
        and contract.get("vi_feedback_call", {}).get("sample_rate") == 8000
    )
    return {
        "ok": bool(payload.get("ok") and helper.get("ok") and preload.get("ok")),
        "path": rel(path),
        "manifest": payload,
        "helper": helper,
        "preload": preload,
        "setcal_contract_ok": setcal_contract_ok,
        "capture_contract": contract,
    }


def selected_artifacts(args: argparse.Namespace) -> dict[str, Any]:
    if args.build_v2728_artifacts:
        build_v2728_artifacts(args)
    manifest = read_v2728_manifest(args.v2728_manifest_path)
    helper = v2573.artifact_from_manifest(manifest.get("helper", {}), args.helper_path, args.helper_sha256)
    preload = v2573.artifact_from_manifest(manifest.get("preload", {}), args.preload_path, args.preload_sha256)
    return {
        "manifest": manifest,
        "helper": helper,
        "preload": preload,
        "ok": bool(
            manifest.get("ok")
            and manifest.get("setcal_contract_ok")
            and helper.get("ok")
            and preload.get("ok")
        ),
    }


def to_v2490_args(args: argparse.Namespace, artifacts: dict[str, Any]) -> argparse.Namespace:
    base = v2490.parse_args([])
    base.dry_run = args.dry_run
    base.run_live = args.run_live
    base.build_helper = False
    base.build_combined_preload = False
    base.build_acdbtap = False
    base.build_ioctl_trace = False
    base.use_combined_preload = True
    base.enable_acdbtap_preload = False
    base.disable_ioctl_trace = False
    base.fake_audio_cal_allocate = True
    base.out_dir = args.out_dir
    base.adb = args.adb
    base.serial = args.serial
    base.from_native = args.from_native
    base.android_timeout = args.android_timeout
    base.flash_timeout = args.flash_timeout
    base.adb_command_timeout = args.adb_command_timeout
    base.adb_pull_timeout = args.adb_pull_timeout
    base.helper_timeout = args.helper_timeout
    base.android_root_recheck_attempts = args.android_root_recheck_attempts
    base.android_root_recheck_sleep_sec = args.android_root_recheck_sleep_sec
    base.android_settle_adb_retry_attempts = args.android_settle_adb_retry_attempts
    base.android_settle_adb_retry_sleep_sec = args.android_settle_adb_retry_sleep_sec
    base.helper_path = ROOT / artifacts["helper"]["path"]
    base.helper_sha256 = artifacts["helper"]["sha256"]
    base.combined_preload_so = ROOT / artifacts["preload"]["path"]
    base.combined_preload_sha256 = artifacts["preload"]["sha256"]
    base.readelf = args.readelf
    base.file = args.file
    return base


def select_pulled_dir_from_result(result: dict[str, Any]) -> Path | None:
    return v2573.select_pulled_dir_from_result(result)


def summarize_setcal_capture(artifact_dir: Path) -> dict[str, Any]:
    base_summary = v2490.parse_ownget_artifacts(artifact_dir)
    setcal_path = artifact_dir / "setcal-events.jsonl"
    setcal_events = [
        event for event in read_jsonl(setcal_path)
        if event.get("event") == "setcal_capture"
    ]
    rows = [v2631._setcal_row(event) for event in setcal_events]

    target_rows = [row for row in rows if row["cal_type"] == TARGET_CAL_TYPE]
    supplemental_rows = [row for row in rows if row["cal_type"] in SUPPLEMENTAL_CAL_TYPES]
    payload_target_rows = [row for row in target_rows if row["is_payload"]]
    target_dmabuf_dumped = [
        row for row in payload_target_rows
        if row.get("dmabuf_status") == "dumped" and not row.get("dmabuf_all_zero")
    ]
    arg_dump_rows = [
        row for row in rows
        if row.get("arg_sha256") and not row.get("arg_all_zero") and (row.get("arg_dump_rc") or 0) >= 0
    ]

    ioctl_events = base_summary.get("ioctl_trace_events", [])
    fake_set_events = [
        event for event in ioctl_events
        if event.get("name") == "AUDIO_SET_CALIBRATION"
        and event.get("intercept") in {"fake-success", "fake-set-always"}
    ]
    real_set_events = [
        event for event in ioctl_events
        if event.get("name") == "AUDIO_SET_CALIBRATION"
        and event.get("intercept") not in {"fake-success", "fake-set-always"}
    ]
    cal_types_seen = sorted({row["cal_type"] for row in rows if row["cal_type"] is not None})
    has_target = bool(target_rows)
    target_payload_ok = bool(target_rows) and (not payload_target_rows or len(target_dmabuf_dumped) == len(payload_target_rows))

    if real_set_events:
        classification = "v2729-boundary-violation-real-audio-set-passthrough"
    elif has_target and target_payload_ok:
        classification = "v2729-vi-feedback-cal17-captured"
    elif has_target:
        classification = "v2729-vi-feedback-cal17-partial-dmabuf"
    elif rows:
        classification = "v2729-setcal-records-no-cal17"
    else:
        classification = f"v2729-{base_summary.get('classification', 'no-setcal-records')}"

    return {
        "classification": classification,
        "success": classification == "v2729-vi-feedback-cal17-captured",
        "partial_success": classification in {
            "v2729-vi-feedback-cal17-partial-dmabuf",
            "v2729-setcal-records-no-cal17",
        },
        "operator_valuable": bool(rows),
        "setcal_events_path": rel(setcal_path),
        "setcal_record_count": len(rows),
        "cal_types_seen": cal_types_seen,
        "target_cal_type": TARGET_CAL_TYPE,
        "target_record_count": len(target_rows),
        "target_payload_record_count": len(payload_target_rows),
        "target_dmabuf_dumped_count": len(target_dmabuf_dumped),
        "target_payload_ok": target_payload_ok,
        "supplemental_cal_types_seen": sorted({row["cal_type"] for row in supplemental_rows if row["cal_type"] is not None}),
        "arg_dump_count": len(arg_dump_rows),
        "fake_audio_set_count": len(fake_set_events),
        "real_audio_set_pass_through_count": len(real_set_events),
        "ordered_records": rows,
        "base_summary": base_summary,
    }


def dry_run_payload(args: argparse.Namespace) -> dict[str, Any]:
    artifacts = selected_artifacts(args)
    base_args = to_v2490_args(args, artifacts) if artifacts.get("ok") else None
    base_payload = v2490.dry_run_payload(base_args) if base_args else {}
    payload: dict[str, Any] = {
        "run_id": RUN_ID,
        "build_tag": BUILD_TAG,
        "decision": "v2729-acdb-vi-feedback-setcal-capture-live-runner-dry-run",
        "host_only": True,
        "device_action": "none",
        "operator_spec": "docs/OPERATOR_ACDB_IOCTL_INTERPOSE_CAPTURE_SPEC_2026-06-15.md",
        "v2728_artifacts": artifacts,
        "v2490_engine": {
            "run_id": "V2490",
            "decision": base_payload.get("decision"),
            "live_ready": base_payload.get("live_ready", False),
            "command_safety": base_payload.get("command_safety"),
            "commands": base_payload.get("commands", {}),
        },
        "capture_contract": {
            "send_path": "init_v3 -> a90_arm_capture -> send_audio_cal_v5(102,1,0x11132,8000,0,8000,1)",
            "set_intercept": "AUDIO_SET_CALIBRATION always fake-successed; never reaches Android kernel SET",
            "target": "cal_type 17 / acdb_id 102 vi-feedback evidence",
            "fake_audio_cal_allocate": True,
            "combined_preload": True,
            "native_replay": "blocked; capture and classify before any replay extension",
            "raw_private_only": True,
        },
    }
    payload["live_ready"] = bool(artifacts.get("ok") and base_payload.get("live_ready"))
    payload["live_blockers"] = []
    if not artifacts.get("ok"):
        payload["live_blockers"].append("V2728 vi-feedback helper/preload artifacts are not ready")
    payload["live_blockers"].extend(base_payload.get("live_blockers", []))
    payload["command_safety"] = base_payload.get("command_safety", {"ok": False, "findings": ["base payload missing"]})
    payload["ok"] = bool(payload["live_ready"] and payload["command_safety"].get("ok"))
    return payload


def run_live(args: argparse.Namespace) -> dict[str, Any]:
    if args.out_dir is None:
        args.out_dir = default_live_out_dir()
    dry = dry_run_payload(args)
    if not dry.get("ok"):
        raise RuntimeError(f"V2729 live inputs are not ready: {dry.get('live_blockers')}")
    artifacts = dry["v2728_artifacts"]
    base_args = to_v2490_args(args, artifacts)
    result = v2490.run_live(base_args)
    pulled_dir = select_pulled_dir_from_result(result)
    summary = summarize_setcal_capture(pulled_dir) if pulled_dir else v2631.summarize_no_pulled_artifacts(result)
    wrapper = {
        "run_id": RUN_ID,
        "build_tag": BUILD_TAG,
        "decision": f"{summary['classification']}-rollback-{'pass' if result.get('rolled_back') else 'unknown'}",
        "out_dir": result.get("out_dir"),
        "rolled_back": bool(result.get("rolled_back")),
        "counts_toward_fails_twice": summary.get(
            "counts_toward_fails_twice",
            result.get("counts_toward_fails_twice"),
        ),
        "operator_valuable": bool(summary.get("operator_valuable")),
        "partial_success": bool(summary.get("partial_success")),
        "success": bool(summary.get("success")),
        "v2728_artifacts": artifacts,
        "v2490_engine_result": result,
        "setcal_summary": summary,
        "ok": bool(result.get("rolled_back") and summary.get("operator_valuable")),
    }
    out_dir_raw = result.get("out_dir")
    if out_dir_raw:
        write_json(ROOT / str(out_dir_raw) / "v2729-result.json", wrapper)
    return wrapper


def write_report(path: Path, payload: dict[str, Any]) -> None:
    summary = payload.get("setcal_summary", {})
    artifacts = payload.get("v2728_artifacts", {})
    helper = artifacts.get("helper", {})
    preload = artifacts.get("preload", {})
    lines = [
        "# NATIVE_INIT V2729 — vi-feedback ACDB SET capture live handoff",
        "",
        "Date: 2026-06-18",
        "",
        "## Scope",
        "",
        "Android own-process ACDB vi-feedback SET-calibration capture using the V2490",
        "checked Android boot/stage/pull/rollback engine and the V2728 helper/preload",
        "artifacts. Measurement only: the SET ioctl is fake-successed in-process;",
        "there is no native replay and no speaker write.",
        "",
        "## Result",
        "",
        f"- decision: `{payload.get('decision')}`",
        f"- ok: `{payload.get('ok')}`",
        f"- rolled_back: `{payload.get('rolled_back')}`",
        f"- operator_valuable: `{payload.get('operator_valuable')}`",
        f"- partial_success: `{payload.get('partial_success')}`",
        f"- success: `{payload.get('success')}`",
        f"- out_dir: `{payload.get('out_dir')}`",
        f"- classification: `{summary.get('classification')}`",
        f"- setcal_record_count: `{summary.get('setcal_record_count')}`",
        f"- cal_types_seen: `{summary.get('cal_types_seen')}`",
        f"- target_record_count: `{summary.get('target_record_count')}`",
        f"- target_payload_record_count: `{summary.get('target_payload_record_count')}`",
        f"- target_dmabuf_dumped_count: `{summary.get('target_dmabuf_dumped_count')}`",
        f"- supplemental_cal_types_seen: `{summary.get('supplemental_cal_types_seen')}`",
        f"- real_audio_set_pass_through_count: `{summary.get('real_audio_set_pass_through_count')}`",
        "",
        "## Ordered SET Records (metadata only)",
        "",
        "| seq | cal_type | data_size | cal_size | mem_handle | arg_sha256 | dmabuf_status | dmabuf_sha256 |",
        "| ---: | ---: | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for row in summary.get("ordered_records", []) or []:
        lines.append(
            f"| {row.get('sequence')} | {row.get('cal_type')} | {row.get('data_size')} | "
            f"{row.get('cal_size')} | {row.get('mem_handle')} | `{row.get('arg_sha256')}` | "
            f"`{row.get('dmabuf_status')}` | `{row.get('dmabuf_sha256')}` |"
        )
    if not summary.get("ordered_records"):
        lines.append("| - | - | - | - | - | - | - | - |")
    lines.extend([
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
        "- stages the V2728 helper/preload through the V2490 Android-good handoff engine;",
        "- forces `A90_ACDB_FAKE_ALLOCATE=1`; real Android kernel SET pass-through is a boundary violation;",
        "- calls `send_audio_cal_v5(102,1,0x11132,8000,0,8000,1)` once;",
        "- pulls `setcal-events.jsonl`, `ioctl-trace-events.jsonl`, helper events, and private raw `setcal-*` files;",
        "- classifies success only after a captured `cal_type=17` vi-feedback SET record.",
        "",
        "## Validation",
        "",
        "- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_acdb_vi_feedback_setcal_capture_live_handoff_v2729.py tests/test_native_audio_acdb_vi_feedback_setcal_capture_live_handoff_v2729.py`",
        "- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_native_audio_acdb_vi_feedback_setcal_capture_live_handoff_v2729 -v`",
        "- dry-run/live command as recorded by the V2490 engine",
        "- `git diff --check`",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--run-live", action="store_true")
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--build-v2728-artifacts", action="store_true")
    parser.add_argument("--v2728-build-root", type=Path, default=v2728.DEFAULT_BUILD_ROOT)
    parser.add_argument("--v2728-manifest-path", type=Path, default=v2728.DEFAULT_MANIFEST)
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
