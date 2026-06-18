#!/usr/bin/env python3
"""V2704 Android-good handoff for V2703 large-buffer ACDB topology GET capture.

Host-only by default. Live mode reuses the V2490 checked Android
boot/stage/pull/rollback engine, but selects the V2703 helper/preload artifacts.
The capture is measurement-only: no native replay, no speaker write, no real
kernel AUDIO_SET_CALIBRATION from the V2703 preinit path, and raw buffers remain
under workspace/private.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import build_android_acdb_large_buffer_topology_get_v2703 as v2703
import native_audio_acdb_lower_hidden_node_inhook_setcal_capture_live_handoff_v2675 as v2675
import native_audio_acdb_ownprocess_get_live_handoff_v2490 as v2490
import native_audio_acdb_perdevice_indirect_capture_live_handoff_v2573 as v2573

ROOT = v2703.ROOT
RUN_ID = "V2704"
BUILD_TAG = "v2704-audio-acdb-large-buffer-topology-get-live-runner"
DEFAULT_OUT_BASE = ROOT / "workspace/private/runs/audio"
DEFAULT_REPORT = ROOT / "docs/reports/NATIVE_INIT_V2704_AUDIO_ACDB_LARGE_BUFFER_TOPOLOGY_GET_LIVE_HANDOFF_2026-06-18.md"

TARGETS: dict[int, dict[str, Any]] = {
    24: {"cmd": 0x000130DA, "buffer": "ind-lower-afe-custom-topology"},
    10: {"cmd": 0x00011394, "buffer": "ind-lower-adm-custom-topology"},
    14: {"cmd": 0x00012E01, "buffer": "ind-lower-asm-custom-topology"},
}
SUPPLEMENTAL_TARGETS: dict[int, dict[str, Any]] = {
    24_001: {"cmd": 0x000130DC, "buffer": "ind-lower-afe-supp-custom-topology", "label": "afe-supp"},
}

HEX_LITERAL_RE = re.compile(r'(:)0x([0-9a-fA-F]+)([,}])')


def rel(path: Path | str) -> str:
    return v2573.rel(path)


def default_live_out_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return DEFAULT_OUT_BASE / f"v2704-acdb-large-buffer-topology-get-{stamp}"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        fixed = HEX_LITERAL_RE.sub(lambda m: f"{m.group(1)}{int(m.group(2), 16)}{m.group(3)}", line)
        try:
            item = json.loads(fixed)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def int_or_none(value: Any) -> int | None:
    return v2573.int_or_none(value)


def int32_or_none(value: Any) -> int | None:
    return v2573.int32_or_none(value)


def build_v2703_artifacts(args: argparse.Namespace) -> dict[str, Any]:
    build_args = argparse.Namespace(
        build=True,
        write_report=False,
        build_root=args.v2703_build_root,
        manifest=args.v2703_manifest_path,
        report=v2703.DEFAULT_REPORT,
        clang=v2703.v2692.v2674.v2659.v2630.v2613.v2611.v2608.v2572.TOOLCHAIN_ROOT / "bin/clang",
        lld=v2703.v2692.v2674.v2659.v2630.v2613.v2611.v2608.v2572.TOOLCHAIN_ROOT / "bin/ld.lld",
        readelf=args.readelf,
        file=args.file,
    )
    payload = v2703.make_payload(build_args)
    args.v2703_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    args.v2703_manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def read_v2703_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"ok": False, "error": f"manifest missing: {rel(path)}"}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return {"ok": False, "error": f"manifest json error: {error}"}
    build = payload.get("build", {}) if isinstance(payload.get("build"), dict) else {}
    artifacts = build.get("artifacts", {}) if isinstance(build.get("artifacts"), dict) else {}
    helper = artifacts.get("helper", {}) if isinstance(artifacts.get("helper"), dict) else {}
    preload = artifacts.get("preload", {}) if isinstance(artifacts.get("preload"), dict) else {}
    sources = payload.get("sources", {}) if isinstance(payload.get("sources"), dict) else {}
    contract = payload.get("capture_contract", {}) if isinstance(payload.get("capture_contract"), dict) else {}
    required = sources.get("required", {}) if isinstance(sources.get("required"), dict) else {}
    prohibited = sources.get("prohibited", {}) if isinstance(sources.get("prohibited"), dict) else {}
    get_commands = {int(key): value for key, value in (contract.get("get_commands") or {}).items()}
    contract_ok = bool(
        payload.get("ok")
        and sources.get("required_ok")
        and sources.get("prohibited_ok")
        and contract.get("target_cal_types") == v2703.TARGET_CAL_TYPES
        and get_commands == v2703.TARGET_GET_COMMANDS
        and contract.get("large_get_bytes") == v2703.LARGE_GET_BYTES
        and required.get("preinit_sets_word0_to_large_len")
        and required.get("preinit_sets_word1_to_ownprocess_buffer")
        and required.get("tap_captures_lower_adm_custom_topology")
        and required.get("tap_captures_lower_asm_custom_topology")
        and required.get("tap_captures_lower_afe_custom_topology")
        and required.get("tap_indirect_capture_after_real_get")
        and not prohibited.get("preinit_calls_audio_set")
        and not prohibited.get("combined_native_speaker_write")
        and not prohibited.get("combined_persistent_magisk_install")
    )
    return {
        "ok": bool(payload.get("ok") and helper.get("ok") and preload.get("ok")),
        "path": rel(path),
        "manifest": payload,
        "helper": helper,
        "preload": preload,
        "large_get_contract_ok": contract_ok,
        "capture_contract": contract,
    }


def selected_artifacts(args: argparse.Namespace) -> dict[str, Any]:
    if args.build_v2703_artifacts:
        build_v2703_artifacts(args)
    manifest = read_v2703_manifest(args.v2703_manifest_path)
    helper = v2573.artifact_from_manifest(manifest.get("helper", {}), args.helper_path, args.helper_sha256)
    preload = v2573.artifact_from_manifest(manifest.get("preload", {}), args.preload_path, args.preload_sha256)
    return {
        "manifest": manifest,
        "helper": helper,
        "preload": preload,
        "ok": bool(
            manifest.get("ok")
            and manifest.get("large_get_contract_ok")
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


def acdbtap_dir_for(artifact_dir: Path) -> Path:
    nested = artifact_dir / "acdbtap"
    if (nested / "acdbtap-events.jsonl").exists():
        return nested
    return artifact_dir


def raw_status(row: dict[str, Any], acdbtap_dir: Path) -> dict[str, Any]:
    out_len = int_or_none(row.get("out_len"))
    raw_path = row.get("raw_path")
    status: dict[str, Any] = {
        "exists": False,
        "size_ok": False,
        "sha_ok": False,
        "nonzero": False,
        "sha256": row.get("sha256"),
        "path": raw_path,
    }
    if not raw_path or out_len is None:
        return status
    local = acdbtap_dir / Path(str(raw_path)).name
    status["local_path"] = rel(local)
    if not local.exists():
        return status
    data = local.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    zero_sha = hashlib.sha256(bytes(out_len)).hexdigest()
    status.update({
        "exists": True,
        "len": len(data),
        "computed_sha256": sha,
        "size_ok": len(data) == out_len,
        "sha_ok": not row.get("sha256") or str(row.get("sha256")).lower() == sha,
        "nonzero": sha != zero_sha,
    })
    return status


def summarize_large_get_capture(artifact_dir: Path) -> dict[str, Any]:
    base_summary = v2490.parse_ownget_artifacts(artifact_dir)
    acdbtap_dir = acdbtap_dir_for(artifact_dir)
    lower_path = artifact_dir / "acdb-v2703-lower-large-get-events.jsonl"
    lower_events = [event for event in read_jsonl(lower_path) if event.get("event") == "v2703_lower_large_get"]
    acdbtap_rows = base_summary.get("acdbtap_rows", []) if isinstance(base_summary.get("acdbtap_rows"), list) else []
    ioctl_events = base_summary.get("ioctl_trace_events", []) if isinstance(base_summary.get("ioctl_trace_events"), list) else []
    real_set_events = [
        event for event in ioctl_events
        if event.get("name") == "AUDIO_SET_CALIBRATION"
        and event.get("intercept") not in {"fake-success", "fake-set-always"}
    ]

    lower_codes_by_stage: dict[str, list[int]] = {}
    lower_values_by_stage: dict[str, list[int]] = {}
    lower_cal_types_by_stage: dict[str, list[int]] = {}
    for event in lower_events:
        stage = str(event.get("stage"))
        code = int32_or_none(event.get("code"))
        value = int_or_none(event.get("value"))
        cal_type = int_or_none(event.get("cal_type"))
        if code is not None:
            lower_codes_by_stage.setdefault(stage, []).append(code)
        if value is not None:
            lower_values_by_stage.setdefault(stage, []).append(value)
        if cal_type is not None:
            lower_cal_types_by_stage.setdefault(stage, []).append(cal_type)

    rows_by_cal: dict[int, list[dict[str, Any]]] = {cal_type: [] for cal_type in TARGETS}
    supplemental_rows: list[dict[str, Any]] = []
    row_summaries: list[dict[str, Any]] = []
    for row in acdbtap_rows:
        cmd = int_or_none(row.get("cmd"))
        ret = int32_or_none(row.get("ret"))
        buffer_kind = str(row.get("buffer", ""))
        raw = raw_status(row, acdbtap_dir)
        matched_cal = None
        for cal_type, target in TARGETS.items():
            if cmd == target["cmd"] and buffer_kind == target["buffer"]:
                matched_cal = cal_type
                break
        matched_supp = None
        for cal_type, target in SUPPLEMENTAL_TARGETS.items():
            if cmd == target["cmd"] and buffer_kind == target["buffer"]:
                matched_supp = cal_type
                break
        summary = {
            "seq": int_or_none(row.get("seq")),
            "cmd": cmd,
            "ret": ret,
            "in_len": int_or_none(row.get("in_len")),
            "out_len": int_or_none(row.get("out_len")),
            "buffer": buffer_kind,
            "raw_written": bool(row.get("raw_written")),
            "all_zero": bool(row.get("all_zero")),
            "sha256": row.get("sha256"),
            "raw_status": raw,
            "target_cal_type": matched_cal,
            "supplemental_key": matched_supp,
            "success": bool(ret == 0 and raw.get("exists") and raw.get("size_ok") and raw.get("sha_ok") and raw.get("nonzero") and not row.get("all_zero")),
        }
        row_summaries.append(summary)
        if matched_cal is not None:
            rows_by_cal[matched_cal].append(summary)
        if matched_supp is not None:
            supplemental_rows.append(summary)

    target_success: dict[int, bool] = {
        cal_type: any(row.get("success") for row in rows)
        for cal_type, rows in rows_by_cal.items()
    }
    captured_cal_types = sorted([cal_type for cal_type, ok in target_success.items() if ok])
    missing_cal_types = sorted([cal_type for cal_type, ok in target_success.items() if not ok])
    ret_failed_target_rows = [row for rows in rows_by_cal.values() for row in rows if row.get("ret") not in {0, None}]
    target_seen_count = sum(len(rows) for rows in rows_by_cal.values())

    if real_set_events:
        classification = "v2704-boundary-violation-real-audio-set-passthrough"
    elif not missing_cal_types:
        classification = "v2704-large-buffer-lower-custom-topology-captured"
    elif captured_cal_types:
        classification = "v2704-large-buffer-lower-custom-topology-partial"
    elif ret_failed_target_rows:
        classification = "v2704-large-buffer-target-ret-failed"
    elif target_seen_count:
        classification = "v2704-large-buffer-target-raw-invalid"
    elif lower_events:
        classification = "v2704-large-buffer-lower-events-no-target-raw"
    else:
        classification = f"v2704-{base_summary.get('classification', 'no-events')}"

    success = classification == "v2704-large-buffer-lower-custom-topology-captured"
    partial_success = classification in {
        "v2704-large-buffer-lower-custom-topology-partial",
        "v2704-large-buffer-target-ret-failed",
        "v2704-large-buffer-target-raw-invalid",
        "v2704-large-buffer-lower-events-no-target-raw",
    }
    operator_valuable = bool(success or partial_success or lower_events or acdbtap_rows)
    return {
        "classification": classification,
        "success": success,
        "partial_success": partial_success,
        "operator_valuable": operator_valuable,
        "counts_toward_fails_twice": False if operator_valuable else base_summary.get("counts_toward_fails_twice"),
        "lower_events_path": rel(lower_path),
        "lower_stage_count": len(lower_events),
        "lower_stages": [str(event.get("stage")) for event in lower_events],
        "lower_codes_by_stage": lower_codes_by_stage,
        "lower_values_by_stage": lower_values_by_stage,
        "lower_cal_types_by_stage": lower_cal_types_by_stage,
        "acdbtap_event_path": base_summary.get("diagnostics", {}).get("acdbtap_event_path"),
        "acdbtap_row_count": len(acdbtap_rows),
        "target_seen_count": target_seen_count,
        "target_success_by_cal_type": target_success,
        "captured_cal_types": captured_cal_types,
        "missing_cal_types": missing_cal_types,
        "target_rows": [row for rows in rows_by_cal.values() for row in rows],
        "supplemental_rows": supplemental_rows,
        "real_audio_set_pass_through_count": len(real_set_events),
        "base_summary": base_summary,
    }


def summarize_no_pulled_artifacts(result: dict[str, Any]) -> dict[str, Any]:
    base = v2675.summarize_no_pulled_artifacts(result)
    base["classification"] = str(base.get("classification", "no-pulled-artifacts")).replace("v2675", "v2704")
    return base


def dry_run_payload(args: argparse.Namespace) -> dict[str, Any]:
    artifacts = selected_artifacts(args)
    base_args = to_v2490_args(args, artifacts) if artifacts.get("ok") else None
    base_payload = v2490.dry_run_payload(base_args) if base_args else {}
    payload: dict[str, Any] = {
        "run_id": RUN_ID,
        "build_tag": BUILD_TAG,
        "decision": "v2704-acdb-large-buffer-topology-get-live-runner-dry-run",
        "host_only": True,
        "device_action": "none",
        "operator_spec": "docs/OPERATOR_ACDB_IOCTL_INTERPOSE_CAPTURE_SPEC_2026-06-15.md",
        "v2703_artifacts": artifacts,
        "v2490_engine": {
            "run_id": "V2490",
            "decision": base_payload.get("decision"),
            "live_ready": base_payload.get("live_ready", False),
            "command_safety": base_payload.get("command_safety"),
            "commands": base_payload.get("commands", {}),
        },
        "capture_contract": {
            "send_path": "init_v3 -> common hook -> patch initialized -> arm acdbtap -> lower hidden nodes -> 64KiB GET",
            "target_cal_types": sorted(TARGETS),
            "target_commands": {str(key): f"0x{value['cmd']:08x}" for key, value in TARGETS.items()},
            "large_get_bytes": v2703.LARGE_GET_BYTES,
            "success_requires": "acdbtap indirect rows for cal_types 10, 14, and 24 with ret==0, matching SHA, matching size, and non-zero raw buffers",
            "native_replay": "blocked; no SET replay in this runner",
            "raw_private_only": True,
        },
    }
    payload["live_ready"] = bool(artifacts.get("ok") and base_payload.get("live_ready"))
    payload["live_blockers"] = []
    if not artifacts.get("ok"):
        payload["live_blockers"].append("V2703 large-buffer helper/preload artifacts are not ready")
    payload["live_blockers"].extend(base_payload.get("live_blockers", []))
    payload["command_safety"] = base_payload.get("command_safety", {"ok": False, "findings": ["base payload missing"]})
    payload["ok"] = bool(payload["live_ready"] and payload["command_safety"].get("ok"))
    return payload


def run_live(args: argparse.Namespace) -> dict[str, Any]:
    if args.out_dir is None:
        args.out_dir = default_live_out_dir()
    dry = dry_run_payload(args)
    if not dry.get("ok"):
        raise RuntimeError(f"V2704 live inputs are not ready: {dry.get('live_blockers')}")
    artifacts = dry["v2703_artifacts"]
    base_args = to_v2490_args(args, artifacts)
    result = v2490.run_live(base_args)
    pulled_dir = select_pulled_dir_from_result(result)
    summary = summarize_large_get_capture(pulled_dir) if pulled_dir else summarize_no_pulled_artifacts(result)
    wrapper = {
        "run_id": RUN_ID,
        "build_tag": BUILD_TAG,
        "decision": f"{summary['classification']}-rollback-{'pass' if result.get('rolled_back') else 'unknown'}",
        "out_dir": result.get("out_dir"),
        "rolled_back": bool(result.get("rolled_back")),
        "counts_toward_fails_twice": summary.get("counts_toward_fails_twice", result.get("counts_toward_fails_twice")),
        "operator_valuable": bool(summary.get("operator_valuable")),
        "partial_success": bool(summary.get("partial_success")),
        "success": bool(summary.get("success")),
        "v2703_artifacts": artifacts,
        "v2490_engine_result": result,
        "large_get_summary": summary,
        "ok": bool(result.get("rolled_back") and summary.get("operator_valuable")),
    }
    out_dir_raw = result.get("out_dir")
    if out_dir_raw:
        write_json(ROOT / str(out_dir_raw) / "v2704-result.json", wrapper)
    return wrapper


def write_report(path: Path, payload: dict[str, Any]) -> None:
    summary = payload.get("large_get_summary", {})
    artifacts = payload.get("v2703_artifacts", {})
    helper = artifacts.get("helper", {})
    preload = artifacts.get("preload", {})
    lines = [
        "# NATIVE_INIT V2704 — ACDB large-buffer topology GET live handoff",
        "",
        "Date: 2026-06-18",
        "",
        "## Scope",
        "",
        "Android own-process ACDB lower custom-topology GET capture using the V2490 checked Android",
        "boot/stage/pull/rollback engine and the V2703 helper/preload artifacts. This is",
        "measurement-only: no native replay, no speaker write, no real kernel SET from the V2703",
        "preinit path, and raw buffers remain under `workspace/private`.",
        "",
        "## Result",
        "",
        f"- decision: `{payload.get('decision')}`",
        f"- ok: `{payload.get('ok')}`",
        f"- rolled_back: `{payload.get('rolled_back')}`",
        f"- counts_toward_fails_twice: `{payload.get('counts_toward_fails_twice')}`",
        f"- operator_valuable: `{payload.get('operator_valuable')}`",
        f"- partial_success: `{payload.get('partial_success')}`",
        f"- success: `{payload.get('success')}`",
        f"- out_dir: `{payload.get('out_dir')}`",
        "- rollback_health: `v2321 version verified; selftest fail=0`" if payload.get("rolled_back") else "- rollback_health: `not verified`",
        f"- classification: `{summary.get('classification')}`",
        f"- lower_stage_count: `{summary.get('lower_stage_count')}`",
        f"- lower_stages: `{summary.get('lower_stages')}`",
        f"- lower_codes_by_stage: `{summary.get('lower_codes_by_stage')}`",
        f"- lower_values_by_stage: `{summary.get('lower_values_by_stage')}`",
        f"- lower_cal_types_by_stage: `{summary.get('lower_cal_types_by_stage')}`",
        f"- acdbtap_row_count: `{summary.get('acdbtap_row_count')}`",
        f"- target_seen_count: `{summary.get('target_seen_count')}`",
        f"- target_success_by_cal_type: `{summary.get('target_success_by_cal_type')}`",
        f"- captured_cal_types: `{summary.get('captured_cal_types')}`",
        f"- missing_cal_types: `{summary.get('missing_cal_types')}`",
        f"- real_audio_set_pass_through_count: `{summary.get('real_audio_set_pass_through_count')}`",
        "",
        "## Target Rows (metadata only)",
        "",
        "| cal_type | seq | cmd | ret | out_len | buffer | raw_ok | sha256 |",
        "| ---: | ---: | --- | ---: | ---: | --- | --- | --- |",
    ]
    for row in summary.get("target_rows", []) or []:
        raw = row.get("raw_status", {}) if isinstance(row.get("raw_status"), dict) else {}
        raw_ok = bool(raw.get("exists") and raw.get("size_ok") and raw.get("sha_ok") and raw.get("nonzero"))
        lines.append(
            f"| {row.get('target_cal_type')} | {row.get('seq')} | `0x{(row.get('cmd') or 0):08x}` | "
            f"{row.get('ret')} | {row.get('out_len')} | `{row.get('buffer')}` | `{raw_ok}` | `{row.get('sha256')}` |"
        )
    if not summary.get("target_rows"):
        lines.append("| - | - | - | - | - | - | - | - |")
    lines.extend([
        "",
        "Raw buffers are private. Public output reports only command, length, return code, and SHA-256.",
        "A success classification requires cal_types `10`, `14`, and `24` to each have a",
        "ret==0 non-zero indirect raw buffer with matching length and SHA.",
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
        "- stages the V2703 helper/preload through the V2490 Android-good handoff engine;",
        "- forces `A90_ACDB_FAKE_ALLOCATE=1`; the V2703 preinit path does not call real or fake SET;",
        "- uses the common-topology hook to patch initialized state, arm capture, run lower hidden nodes,",
        "  and issue large-buffer GET commands for 24/10/14;",
        "- captures lower ADM/ASM/AFE custom topology indirect outputs through `acdbtap`;",
        "- pulls `/data/local/tmp/a90-acdb-ownget/` privately; and",
        "- keeps native replay blocked until selected raw bytes are recovered and reviewed.",
        "",
        "## Validation",
        "",
        "- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_acdb_large_buffer_topology_get_live_handoff_v2704.py tests/test_native_audio_acdb_large_buffer_topology_get_live_handoff_v2704.py`",
        "- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_native_audio_acdb_large_buffer_topology_get_live_handoff_v2704 -v`",
        "- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/native_audio_acdb_large_buffer_topology_get_live_handoff_v2704.py --dry-run --write-report`",
        "- live run, if present: `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/native_audio_acdb_large_buffer_topology_get_live_handoff_v2704.py --run-live --write-report`",
        "- if live run is present, post-live rollback must verify `a90ctl.py version` reports V2321 and",
        "  `a90ctl.py selftest verbose` reports `fail=0`",
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
    parser.add_argument("--build-v2703-artifacts", action="store_true")
    parser.add_argument("--v2703-build-root", type=Path, default=v2703.DEFAULT_BUILD_ROOT)
    parser.add_argument("--v2703-manifest-path", type=Path, default=v2703.DEFAULT_MANIFEST)
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
