#!/usr/bin/env python3
"""Build a Gate-2 VOL-status handoff after V2621.

Host-only.  Combines the private V2619 Gate-2 payload-candidate manifest with
the V2621 VOL-isolated live result.  It does not promote raw payloads into
tracked paths, does not run the device, and does not mark native replay ready.
The purpose is to hand the operator a single redacted/public status plus a
private manifest that says: AUDPROC/AFE candidate bytes exist, but the current
speaker tuple's VOL direct GET path returned -19 for every gain step.
"""

from __future__ import annotations

import argparse
import json
import stat
from datetime import datetime
from pathlib import Path
from typing import Any

import native_audio_acdb_gate2_handoff_v2619 as v2619

ROOT = v2619.ROOT
RUN_ID = "V2622"
BUILD_TAG = "v2622-audio-acdb-gate2-vol-status-handoff"
DEFAULT_AUDIO_RUNS = ROOT / "workspace/private/runs/audio"
DEFAULT_V2618_GLOB = "v2618-acdb-direct-matrix-*"
DEFAULT_V2621_GLOB = "v2621-acdb-vol-isolated-*"
DEFAULT_REPORT = ROOT / "docs/reports/NATIVE_INIT_V2622_AUDIO_ACDB_GATE2_VOL_STATUS_HANDOFF_2026-06-16.md"
DEFAULT_PRIVATE_NAME = "v2622-acdb-gate2-vol-status-manifest.json"


def rel(path: Path | str) -> str:
    return v2619.rel(path)


def write_json(path: Path, payload: dict[str, Any], mode: int | None = None) -> None:
    v2619.write_json(path, payload, mode)


def read_json(path: Path) -> dict[str, Any]:
    return v2619.read_json(path)


def latest_run(base: Path, pattern: str, marker: str) -> Path:
    candidates = sorted(
        path for path in base.glob(pattern)
        if path.is_dir() and (path / marker).exists()
    )
    if not candidates:
        raise FileNotFoundError(f"no runs matching {pattern} with {marker} under {rel(base)}")
    return candidates[-1]


def load_or_build_v2619_manifest(v2618_run_dir: Path) -> tuple[dict[str, Any], Path]:
    existing = v2618_run_dir / v2619.DEFAULT_PRIVATE_NAME
    if existing.exists():
        return read_json(existing), existing
    manifest = v2619.build_manifest(v2618_run_dir)
    write_json(existing, manifest, 0o600)
    return manifest, existing


def vol_status_from_v2621(v2621_run_dir: Path) -> dict[str, Any]:
    result_path = v2621_run_dir / "v2621-result.json"
    if not result_path.exists():
        raise FileNotFoundError(f"missing {rel(result_path)}")
    result = read_json(result_path)
    summary = result.get("vol_isolated_summary", {})
    base = summary.get("base_summary", {})
    status = {
        "source_run_id": "V2621",
        "source_run_dir": rel(v2621_run_dir),
        "source_result": rel(result_path),
        "source_decision": result.get("decision"),
        "source_rolled_back": result.get("rolled_back"),
        "classification": summary.get("classification"),
        "helper_done": bool(summary.get("helper_done")),
        "vol_sweep_seen": bool(summary.get("vol_sweep_seen")),
        "vol_size_case_count": summary.get("vol_size_case_count"),
        "vol_data_case_count": summary.get("vol_data_case_count"),
        "vol_size_ret_values": summary.get("vol_size_ret_values"),
        "vol_data_ret_values": summary.get("vol_data_ret_values"),
        "vol_size_ret_failed_count": summary.get("vol_size_ret_failed_count"),
        "vol_data_ret_failed_count": summary.get("vol_data_ret_failed_count"),
        "vol_request_in_buffer_count": summary.get("vol_request_in_buffer_count"),
        "vol_payload_count": summary.get("vol_payload_count"),
        "real_audio_set_pass_through_count": summary.get("real_audio_set_pass_through_count"),
        "helper_rc": base.get("diagnostics", {}).get("helper_rc"),
        "helper_sigsegv": base.get("diagnostics", {}).get("helper_sigsegv"),
    }
    status["vol_direct_get_exhausted_for_current_tuple"] = bool(
        status["source_rolled_back"]
        and status["helper_done"]
        and status["vol_sweep_seen"]
        and status["vol_size_case_count"] == 16
        and status["vol_data_case_count"] == 16
        and status["vol_payload_count"] == 0
        and status["vol_size_ret_values"] == [-19]
        and status["vol_data_ret_values"] == [-19]
        and status["real_audio_set_pass_through_count"] == 0
        and not status["helper_sigsegv"]
    )
    status["operator_interpretation"] = (
        "V2621 executed the current speaker tuple's VOL size/data sweep for gain steps 0..15. "
        "Every direct VOL command returned -19, and no ind-ap-gain payload was captured. "
        "Treat this as VOL-negative evidence for this tuple, not as a raw-payload capture failure."
    )
    return status


def redacted_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        key: candidate.get(key)
        for key in [
            "order", "category", "cmd", "seq", "buffer", "in_len", "out_len", "ret",
            "sha256", "raw_size", "nonzero", "hash_matches_event", "verified_for_gate2",
        ]
    }


def build_manifest(v2618_run_dir: Path, v2621_run_dir: Path) -> dict[str, Any]:
    v2619_manifest, v2619_path = load_or_build_v2619_manifest(v2618_run_dir)
    vol_status = vol_status_from_v2621(v2621_run_dir)
    candidates = v2619_manifest.get("payload_candidates", [])
    redacted = [redacted_candidate(item) for item in candidates]
    summary = dict(v2619_manifest.get("summary", {}))
    summary.update({
        "vol_direct_get_exhausted_for_current_tuple": vol_status["vol_direct_get_exhausted_for_current_tuple"],
        "vol_status_source_decision": vol_status["source_decision"],
        "vol_status_payload_count": vol_status["vol_payload_count"],
        "vol_status_ret_values": {
            "size": vol_status["vol_size_ret_values"],
            "data": vol_status["vol_data_ret_values"],
        },
    })
    replay_blockers = [
        "operator must verify size/order/cmd to ACDB cal_type mapping before replay",
        "topology payload is already separately verified, but this handoff does not copy it",
        "VOL direct GET for the current speaker tuple returned -19 for every gain step",
    ]
    payload = {
        "run_id": RUN_ID,
        "build_tag": BUILD_TAG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "host_only": True,
        "device_action": "none",
        "source_gate2_run_id": "V2619",
        "source_gate2_manifest": rel(v2619_path),
        "source_v2618_run_dir": rel(v2618_run_dir),
        "source_v2621_run_dir": rel(v2621_run_dir),
        "gate": "operator-gate2-pending",
        "native_replay_ready": False,
        "replay_blockers": replay_blockers,
        "summary": summary,
        "payload_candidates": candidates,
        "payload_candidates_redacted": redacted,
        "vol_status": vol_status,
        "operator_note": (
            "AUDPROC/AFE candidate bytes remain private and verified by SHA. "
            "V2621 adds VOL-negative evidence for the current tuple. "
            "Do not enter native replay until the operator confirms whether the manifest may proceed without VOL or supplies a different VOL route."
        ),
    }
    payload["ok"] = bool(
        v2619_manifest.get("ok")
        and vol_status["vol_direct_get_exhausted_for_current_tuple"]
        and summary.get("payload_candidate_count", 0) >= 3
        and summary.get("real_audio_set_pass_through_count") == 0
    )
    return payload


def write_report(path: Path, manifest: dict[str, Any], private_manifest_path: Path) -> None:
    summary = manifest.get("summary", {})
    vol = manifest.get("vol_status", {})
    candidates = manifest.get("payload_candidates_redacted", [])
    lines = [
        "# NATIVE_INIT V2622 — ACDB Gate-2 VOL-status handoff",
        "",
        "Date: 2026-06-16",
        "",
        "## Scope",
        "",
        "Host-only Gate-2 status handoff after V2621. This unit combines the V2619",
        "AUDPROC/AFE payload-candidate manifest with the V2621 VOL-isolated live result.",
        "It does not run the device, replay calibration, copy raw payload bytes to tracked",
        "paths, or mark native replay ready.",
        "",
        "## Result",
        "",
        f"- decision: `v2622-gate2-vol-status-{'ready' if manifest.get('ok') else 'needs-review'}`",
        f"- ok: `{manifest.get('ok')}`",
        f"- private_manifest: `{rel(private_manifest_path)}`",
        f"- native_replay_ready: `{manifest.get('native_replay_ready')}`",
        f"- source_gate2_manifest: `{manifest.get('source_gate2_manifest')}`",
        f"- source_v2618_run_dir: `{manifest.get('source_v2618_run_dir')}`",
        f"- source_v2621_run_dir: `{manifest.get('source_v2621_run_dir')}`",
        f"- payload_candidate_count: `{summary.get('payload_candidate_count')}`",
        f"- payload_verified_count: `{summary.get('payload_verified_count')}`",
        f"- audproc_candidate_count: `{summary.get('audproc_candidate_count')}`",
        f"- afe_candidate_count: `{summary.get('afe_candidate_count')}`",
        f"- vol_candidate_count: `{summary.get('vol_candidate_count')}`",
        f"- vol_direct_get_exhausted_for_current_tuple: `{summary.get('vol_direct_get_exhausted_for_current_tuple')}`",
        f"- vol_status_source_decision: `{summary.get('vol_status_source_decision')}`",
        f"- vol_status_ret_values: `{summary.get('vol_status_ret_values')}`",
        "",
        "## Payload Candidates",
        "",
        "| order | category | cmd | seq | buffer | bytes | sha256 |",
        "| --- | --- | --- | --- | --- | ---: | --- |",
    ]
    for item in candidates:
        lines.append(
            f"| {item.get('order')} | `{item.get('category')}` | `{item.get('cmd')}` | "
            f"`{item.get('seq')}` | `{item.get('buffer')}` | {item.get('out_len')} | "
            f"`{item.get('sha256')}` |"
        )
    lines.extend([
        "",
        "## VOL Status",
        "",
        f"- classification: `{vol.get('classification')}`",
        f"- helper_done: `{vol.get('helper_done')}`",
        f"- vol_sweep_seen: `{vol.get('vol_sweep_seen')}`",
        f"- vol_size_case_count: `{vol.get('vol_size_case_count')}`",
        f"- vol_data_case_count: `{vol.get('vol_data_case_count')}`",
        f"- vol_size_ret_values: `{vol.get('vol_size_ret_values')}`",
        f"- vol_data_ret_values: `{vol.get('vol_data_ret_values')}`",
        f"- vol_payload_count: `{vol.get('vol_payload_count')}`",
        f"- real_audio_set_pass_through_count: `{vol.get('real_audio_set_pass_through_count')}`",
        f"- helper_rc: `{vol.get('helper_rc')}`",
        f"- helper_sigsegv: `{vol.get('helper_sigsegv')}`",
        "",
        "## Boundary",
        "",
        "- This is **not** a replay manifest.",
        "- Raw payload paths are present only in the private manifest.",
        "- Native replay remains blocked until operator Gate-2 mapping confirms the candidate cal types and decides whether the VOL-negative result is acceptable or a new VOL route is required.",
        "",
        "## Validation",
        "",
        "- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_acdb_gate2_vol_status_handoff_v2622.py tests/test_native_audio_acdb_gate2_vol_status_handoff_v2622.py`",
        "- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_native_audio_acdb_gate2_vol_status_handoff_v2622 -v`",
        "- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/native_audio_acdb_gate2_vol_status_handoff_v2622.py --write-report`",
        "- `git diff --check`",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio-runs", type=Path, default=DEFAULT_AUDIO_RUNS)
    parser.add_argument("--v2618-run-dir", type=Path)
    parser.add_argument("--v2621-run-dir", type=Path)
    parser.add_argument("--private-manifest-path", type=Path)
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    v2618_run_dir = args.v2618_run_dir or latest_run(args.audio_runs, DEFAULT_V2618_GLOB, "v2618-result.json")
    v2621_run_dir = args.v2621_run_dir or latest_run(args.audio_runs, DEFAULT_V2621_GLOB, "v2621-result.json")
    payload = build_manifest(v2618_run_dir, v2621_run_dir)
    private_path = args.private_manifest_path or (v2621_run_dir / DEFAULT_PRIVATE_NAME)
    write_json(private_path, payload, 0o600)
    if args.write_report:
        write_report(args.report_path, payload, private_path)
    print(json.dumps({
        "run_id": RUN_ID,
        "decision": f"v2622-gate2-vol-status-{'ready' if payload.get('ok') else 'needs-review'}",
        "ok": payload.get("ok"),
        "private_manifest": rel(private_path),
        "report": rel(args.report_path) if args.write_report else None,
        "native_replay_ready": payload.get("native_replay_ready"),
        "summary": payload.get("summary"),
    }, indent=2, sort_keys=True))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
