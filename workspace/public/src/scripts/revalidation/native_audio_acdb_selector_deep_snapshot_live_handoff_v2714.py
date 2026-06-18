#!/usr/bin/env python3
"""V2714 Android-good handoff for V2713 ACDB selector deep-snapshot capture.

Host-only by default. Live mode reuses the V2490 checked Android
boot/stage/pull/rollback engine, but selects the V2713 helper/preload artifacts.
The capture is measurement-only: no native replay, no speaker write, no real
kernel AUDIO_SET_CALIBRATION from the V2713 preinit path, and raw buffers remain
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

import build_android_acdb_selector_deep_snapshot_v2713 as v2713
import native_audio_acdb_lower_hidden_node_inhook_setcal_capture_live_handoff_v2675 as v2675
import native_audio_acdb_ownprocess_get_live_handoff_v2490 as v2490
import native_audio_acdb_perdevice_indirect_capture_live_handoff_v2573 as v2573

ROOT = v2713.ROOT
RUN_ID = "V2714"
BUILD_TAG = "v2714-audio-acdb-selector-deep-snapshot-live-runner"
DEFAULT_OUT_BASE = ROOT / "workspace/private/runs/audio"
DEFAULT_REPORT = ROOT / "docs/reports/NATIVE_INIT_V2714_AUDIO_ACDB_SELECTOR_DEEP_SNAPSHOT_LIVE_HANDOFF_2026-06-18.md"

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
    return DEFAULT_OUT_BASE / f"v2714-acdb-selector-deep-snapshot-{stamp}"


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


def build_v2713_artifacts(args: argparse.Namespace) -> dict[str, Any]:
    build_args = argparse.Namespace(
        build=True,
        write_report=False,
        build_root=args.v2713_build_root,
        manifest=args.v2713_manifest_path,
        report=v2713.DEFAULT_REPORT,
        clang=v2713.v2692.v2674.v2659.v2630.v2613.v2611.v2608.v2572.TOOLCHAIN_ROOT / "bin/clang",
        lld=v2713.v2692.v2674.v2659.v2630.v2613.v2611.v2608.v2572.TOOLCHAIN_ROOT / "bin/ld.lld",
        readelf=args.readelf,
        file=args.file,
    )
    payload = v2713.make_payload(build_args)
    args.v2713_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    args.v2713_manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def read_v2713_manifest(path: Path) -> dict[str, Any]:
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
        and contract.get("target_cal_types") == v2713.TARGET_CAL_TYPES
        and get_commands == v2713.TARGET_GET_COMMANDS
        and contract.get("large_get_bytes") == v2713.LARGE_GET_BYTES
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
        "selector_snapshot_contract_ok": contract_ok,
        "capture_contract": contract,
    }


def selected_artifacts(args: argparse.Namespace) -> dict[str, Any]:
    if args.build_v2713_artifacts:
        build_v2713_artifacts(args)
    manifest = read_v2713_manifest(args.v2713_manifest_path)
    helper = v2573.artifact_from_manifest(manifest.get("helper", {}), args.helper_path, args.helper_sha256)
    preload = v2573.artifact_from_manifest(manifest.get("preload", {}), args.preload_path, args.preload_sha256)
    return {
        "manifest": manifest,
        "helper": helper,
        "preload": preload,
        "ok": bool(
            manifest.get("ok")
            and manifest.get("selector_snapshot_contract_ok")
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


def summarize_selector_snapshot_capture(artifact_dir: Path) -> dict[str, Any]:
    base_summary = v2490.parse_ownget_artifacts(artifact_dir)
    acdbtap_dir = acdbtap_dir_for(artifact_dir)
    selector_path = artifact_dir / "acdb-v2713-selector-deep-snapshot-events.jsonl"
    selector_log_events = read_jsonl(selector_path)
    selector_events = [event for event in selector_log_events if event.get("event") == "v2713_selector_deep_snapshot"]
    lower_events = [event for event in selector_log_events if event.get("event") == "v2672_lower_hidden"]
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

    selector_rows: list[dict[str, Any]] = []
    selector_success_by_cal_type: dict[int, bool] = {cal_type: False for cal_type in TARGETS}
    for event in selector_events:
        cal_type = int_or_none(event.get("cal_type"))
        node_words = event.get("node_words") if isinstance(event.get("node_words"), list) else []
        block_words = event.get("block_words") if isinstance(event.get("block_words"), list) else []
        row = {
            "cal_type": cal_type,
            "node": event.get("node"),
            "block": event.get("block"),
            "node_words": node_words,
            "block_words": block_words,
            "node_word_count": len(node_words),
            "block_word_count": len(block_words),
            "has_expected_depth": len(node_words) >= 16 and len(block_words) >= 32,
        }
        selector_rows.append(row)
        if cal_type in selector_success_by_cal_type and row["has_expected_depth"]:
            selector_success_by_cal_type[cal_type] = True

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
    snapshot_cal_types = sorted([cal_type for cal_type, ok in selector_success_by_cal_type.items() if ok])
    missing_snapshot_cal_types = sorted([cal_type for cal_type, ok in selector_success_by_cal_type.items() if not ok])
    ret_failed_target_rows = [row for rows in rows_by_cal.values() for row in rows if row.get("ret") not in {0, None}]
    target_seen_count = sum(len(rows) for rows in rows_by_cal.values())

    if real_set_events:
        classification = "v2714-boundary-violation-real-audio-set-passthrough"
    elif not missing_cal_types and not missing_snapshot_cal_types:
        classification = "v2714-selector-deep-snapshot-lower-custom-topology-captured"
    elif selector_events and captured_cal_types:
        classification = "v2714-selector-deep-snapshot-partial-with-target-raw"
    elif selector_events:
        classification = "v2714-selector-deep-snapshot-captured-no-target-raw"
    elif captured_cal_types:
        classification = "v2714-selector-deep-snapshot-lower-custom-topology-partial"
    elif ret_failed_target_rows:
        classification = "v2714-selector-deep-snapshot-target-ret-failed"
    elif target_seen_count:
        classification = "v2714-selector-deep-snapshot-target-raw-invalid"
    elif lower_events:
        classification = "v2714-selector-deep-snapshot-lower-events-no-target-raw"
    else:
        classification = f"v2714-{base_summary.get('classification', 'no-events')}"

    success = classification == "v2714-selector-deep-snapshot-lower-custom-topology-captured"
    partial_success = classification in {
        "v2714-selector-deep-snapshot-partial-with-target-raw",
        "v2714-selector-deep-snapshot-captured-no-target-raw",
        "v2714-selector-deep-snapshot-lower-custom-topology-partial",
        "v2714-selector-deep-snapshot-target-ret-failed",
        "v2714-selector-deep-snapshot-target-raw-invalid",
        "v2714-selector-deep-snapshot-lower-events-no-target-raw",
    }
    operator_valuable = bool(success or partial_success or selector_events or lower_events or acdbtap_rows)
    return {
        "classification": classification,
        "success": success,
        "partial_success": partial_success,
        "operator_valuable": operator_valuable,
        "counts_toward_fails_twice": False if operator_valuable else base_summary.get("counts_toward_fails_twice"),
        "selector_events_path": rel(selector_path),
        "selector_event_count": len(selector_events),
        "selector_success_by_cal_type": selector_success_by_cal_type,
        "snapshot_cal_types": snapshot_cal_types,
        "missing_snapshot_cal_types": missing_snapshot_cal_types,
        "selector_rows": selector_rows,
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
    base["classification"] = str(base.get("classification", "no-pulled-artifacts")).replace("v2675", "v2714")
    return base


def dry_run_payload(args: argparse.Namespace) -> dict[str, Any]:
    artifacts = selected_artifacts(args)
    base_args = to_v2490_args(args, artifacts) if artifacts.get("ok") else None
    base_payload = v2490.dry_run_payload(base_args) if base_args else {}
    payload: dict[str, Any] = {
        "run_id": RUN_ID,
        "build_tag": BUILD_TAG,
        "decision": "v2714-acdb-selector-deep-snapshot-live-runner-dry-run",
        "host_only": True,
        "device_action": "none",
        "operator_spec": "docs/OPERATOR_ACDB_IOCTL_INTERPOSE_CAPTURE_SPEC_2026-06-15.md",
        "v2713_artifacts": artifacts,
        "v2490_engine": {
            "run_id": "V2490",
            "decision": base_payload.get("decision"),
            "live_ready": base_payload.get("live_ready", False),
            "command_safety": base_payload.get("command_safety"),
            "commands": base_payload.get("commands", {}),
        },
        "capture_contract": {
            "send_path": "init_v3 -> common hook -> patch initialized -> arm acdbtap -> lower hidden nodes -> deep snapshot -> 64KiB GET",
            "target_cal_types": sorted(TARGETS),
            "target_commands": {str(key): f"0x{value['cmd']:08x}" for key, value in TARGETS.items()},
            "large_get_bytes": v2713.LARGE_GET_BYTES,
            "success_requires": "acdbtap indirect rows for cal_types 10, 14, and 24 with ret==0, matching SHA, matching size, and non-zero raw buffers",
            "native_replay": "blocked; no SET replay in this runner",
            "raw_private_only": True,
        },
    }
    payload["live_ready"] = bool(artifacts.get("ok") and base_payload.get("live_ready"))
    payload["live_blockers"] = []
    if not artifacts.get("ok"):
        payload["live_blockers"].append("V2713 selector-deep-snapshot helper/preload artifacts are not ready")
    payload["live_blockers"].extend(base_payload.get("live_blockers", []))
    payload["command_safety"] = base_payload.get("command_safety", {"ok": False, "findings": ["base payload missing"]})
    payload["ok"] = bool(payload["live_ready"] and payload["command_safety"].get("ok"))
    return payload


def run_live(args: argparse.Namespace) -> dict[str, Any]:
    if args.out_dir is None:
        args.out_dir = default_live_out_dir()
    dry = dry_run_payload(args)
    if not dry.get("ok"):
        raise RuntimeError(f"V2714 live inputs are not ready: {dry.get('live_blockers')}")
    artifacts = dry["v2713_artifacts"]
    base_args = to_v2490_args(args, artifacts)
    result = v2490.run_live(base_args)
    pulled_dir = select_pulled_dir_from_result(result)
    summary = summarize_selector_snapshot_capture(pulled_dir) if pulled_dir else summarize_no_pulled_artifacts(result)
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
        "v2713_artifacts": artifacts,
        "v2490_engine_result": result,
        "selector_snapshot_summary": summary,
        "ok": bool(result.get("rolled_back") and summary.get("operator_valuable")),
    }
    out_dir_raw = result.get("out_dir")
    if out_dir_raw:
        write_json(ROOT / str(out_dir_raw) / "v2714-result.json", wrapper)
    return wrapper


def write_report(path: Path, payload: dict[str, Any]) -> None:
    summary = payload.get("selector_snapshot_summary", {})
    artifacts = payload.get("v2713_artifacts", {})
    helper = artifacts.get("helper", {})
    preload = artifacts.get("preload", {})
    lines = [
        "# NATIVE_INIT V2714 — ACDB selector deep-snapshot live handoff",
        "",
        "Date: 2026-06-18",
        "",
        "## Scope",
        "",
        "Android own-process ACDB lower custom-topology GET capture using the V2490 checked Android",
        "boot/stage/pull/rollback engine and the V2713 helper/preload artifacts. This is",
        "measurement-only: no native replay, no speaker write, no real kernel SET from the V2713",
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
        f"- selector_event_count: `{summary.get('selector_event_count')}`",
        f"- selector_success_by_cal_type: `{summary.get('selector_success_by_cal_type')}`",
        f"- snapshot_cal_types: `{summary.get('snapshot_cal_types')}`",
        f"- missing_snapshot_cal_types: `{summary.get('missing_snapshot_cal_types')}`",
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
        f"- selector_events_path: `{summary.get('selector_events_path')}`",
        "",
        "## Selector Deep Snapshots",
        "",
        "| cal_type | node_word_count | block_word_count | depth_ok | node_words | block_words |",
        "| ---: | ---: | ---: | --- | --- | --- |",
    ]
    for row in summary.get("selector_rows", []) or []:
        node_words = row.get("node_words") if isinstance(row.get("node_words"), list) else []
        block_words = row.get("block_words") if isinstance(row.get("block_words"), list) else []
        lines.append(
            f"| {row.get('cal_type')} | {row.get('node_word_count')} | {row.get('block_word_count')} | "
            f"`{row.get('has_expected_depth')}` | `{node_words}` | `{block_words}` |"
        )
    if not summary.get("selector_rows"):
        lines.append("| - | - | - | - | - | - |")
    lines.extend([
        "",
        "## Target Rows (metadata only)",
        "",
        "| cal_type | seq | cmd | ret | out_len | buffer | raw_ok | sha256 |",
        "| ---: | ---: | --- | ---: | ---: | --- | --- | --- |",
    ])
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
        "Raw buffers are private. Public output reports only command, length, return code, SHA-256,",
        "and selector word metadata. A success classification requires cal_types `10`, `14`, and",
        "`24` to each have a bounded 16/32-word selector snapshot and a ret==0 non-zero indirect",
        "raw buffer with matching length and SHA.",
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
        "- stages the V2713 helper/preload through the V2490 Android-good handoff engine;",
        "- forces `A90_ACDB_FAKE_ALLOCATE=1`; the V2713 preinit path does not call real or fake SET;",
        "- uses the common-topology hook to patch initialized state, arm capture, run lower hidden nodes,",
        "  and issue selector-deep-snapshot GET commands for 24/10/14;",
        "- captures lower ADM/ASM/AFE custom topology indirect outputs through `acdbtap`;",
        "- pulls `/data/local/tmp/a90-acdb-ownget/` privately; and",
        "- keeps native replay blocked until selected raw bytes are recovered and reviewed.",
        "",
        "## Validation",
        "",
        "- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_acdb_selector_deep_snapshot_live_handoff_v2714.py tests/test_native_audio_acdb_selector_deep_snapshot_live_handoff_v2714.py`",
        "- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_native_audio_acdb_selector_deep_snapshot_live_handoff_v2714 -v`",
        "- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/native_audio_acdb_selector_deep_snapshot_live_handoff_v2714.py --dry-run --write-report`",
        "- live run, if present: `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/native_audio_acdb_selector_deep_snapshot_live_handoff_v2714.py --run-live --write-report`",
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
    parser.add_argument("--build-v2713-artifacts", action="store_true")
    parser.add_argument("--v2713-build-root", type=Path, default=v2713.DEFAULT_BUILD_ROOT)
    parser.add_argument("--v2713-manifest-path", type=Path, default=v2713.DEFAULT_MANIFEST)
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
