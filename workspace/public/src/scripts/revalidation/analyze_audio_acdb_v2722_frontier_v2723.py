#!/usr/bin/env python3
"""V2723 host-only analysis of the V2722 corrected ACDB replay frontier."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[5]
RUN_ID = "V2723"
BUILD_TAG = "v2723-audio-acdb-v2722-frontier-analysis"
DEFAULT_V2722_RUN = ROOT / "workspace/private/runs/audio/v2639-acdb-setcal-replay-20260618-212439"
DEFAULT_V2721_MANIFEST = ROOT / "workspace/private/builds/audio/v2721-audio-acdb-corrected-core39-replay-deploy-plan/deploy-plan.json"
DEFAULT_V2632_EVENTS = ROOT / "workspace/private/runs/audio/v2632-acdb-setcal-capture-20260618-083701/ownget-device-artifacts/setcal-events.jsonl"
DEFAULT_REPORT = ROOT / "docs/reports/NATIVE_INIT_V2723_AUDIO_ACDB_V2722_FRONTIER_ANALYSIS_2026-06-18.md"
GOAL_ORDER_CLAIM = [13, 9, 11, 12, 15, 16, 21, 23]
STALE_TYPES = {10, 14, 24}
EXPECTED_CORRECTED_PREFIX = [39, 20, 20]

NEW_FRONTIER_PATTERNS = {
    "afe_port_start_0x4000": r"__afe_port_start: port id: 0x4000",
    "afe_cal_ebadparam": r"afe_send_cal_block: AFE cal for port 0x4000 failed -22",
    "q6asm_eneedmore": r"q6asm_callback: cmd = 0x10da1 returned error = 0x12",
    "q6asm_send_cal_failed": r"q6asm_send_cal: audio audstrm cal send failed",
    "adm_open_0x10004000": r"adm_open:port 0x4000 .*topo_id 0x10004000",
    "adm_efailed": r"adm_open: DSP returned error\[ADSP_EFAILED\]",
    "prepare_minus_22": r"msm_pcm_playback_prepare: stream reg failed ret:-22",
}
OLD_STALE_PATTERNS = {
    "send_asm_custom_topology": r"send_asm_custom_topology",
    "asm_add_custom_topology_cmd": r"0x10dbe",
    "subsystem_custom_topology_ebadparam": r"ASM_CMD_ADD_CUSTOM_TOPOLOGIES|ADSP_EBADPARAM.*custom",
}


def rel(path: Path | str) -> str:
    target = Path(path)
    try:
        return str(target.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def load_v2632_order(path: Path) -> list[int]:
    order: list[int] = []
    for row in iter_jsonl(path):
        if row.get("event") != "setcal_capture":
            continue
        cal_type = row.get("cal_type")
        if isinstance(cal_type, int):
            order.append(cal_type)
    return order


def load_v2721_order(path: Path) -> list[int]:
    manifest = read_json(path)
    return [int(entry["cal_type"]) for entry in manifest.get("replay_entries", [])]


def grep_patterns(text: str, patterns: dict[str, str]) -> dict[str, bool]:
    return {name: bool(re.search(pattern, text, flags=re.IGNORECASE)) for name, pattern in patterns.items()}


def dmesg_text(run_dir: Path) -> str:
    path = run_dir / "63_dmesg-after-setcal-playback-failure-before-reset.txt"
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def summarize_result(run_dir: Path) -> dict[str, Any]:
    result = read_json(run_dir / "result.json")
    replay = result.get("acdb_setcal_replay") or {}
    return {
        "decision": result.get("decision"),
        "error_type": result.get("error_type"),
        "error": result.get("error"),
        "rolled_back": result.get("rolled_back"),
        "rollback_version_ok": result.get("rollback_version_ok"),
        "rollback_selftest_fail0": result.get("rollback_selftest_fail0"),
        "replay_start_ok": bool((replay.get("replay_start") or {}).get("ok")),
        "playback_attempted": bool(replay.get("playback_attempted")),
        "helper_cleanup_ok": bool((replay.get("helper_cleanup") or {}).get("ok")),
        "route_reset_ok": bool((replay.get("route_reset_verification") or {}).get("ok")),
    }


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    run_dir = Path(args.v2722_run)
    v2721_order = load_v2721_order(Path(args.v2721_manifest))
    per_device_order = v2721_order[len(EXPECTED_CORRECTED_PREFIX):]
    v2632_order = load_v2632_order(Path(args.v2632_events))
    text = dmesg_text(run_dir)
    new_markers = grep_patterns(text, NEW_FRONTIER_PATTERNS)
    old_markers = grep_patterns(text, OLD_STALE_PATTERNS)
    stale_present = sorted(STALE_TYPES & set(v2721_order))
    goal_order_conflict = bool(v2632_order and v2632_order != GOAL_ORDER_CLAIM)
    per_device_matches_v2632 = per_device_order == v2632_order
    old_stale_cleared = not any(old_markers.values())
    new_frontier_present = all(new_markers.values())
    result = summarize_result(run_dir)
    decision = "v2723-v2722-frontier-analysis-complete"
    if old_stale_cleared and new_frontier_present and per_device_matches_v2632:
        decision = "v2723-old-asm-cleared-new-afe-q6asm-frontier"
    blockers: list[str] = []
    if stale_present:
        blockers.append(f"stale cal types present in V2721 order: {stale_present}")
    if not result["rolled_back"] or not result["rollback_selftest_fail0"]:
        blockers.append("V2722 rollback/selftest proof missing")
    return {
        "run_id": RUN_ID,
        "build_tag": BUILD_TAG,
        "created_at": now_iso(),
        "host_only": True,
        "device_action": "none",
        "source_v2722_run": rel(run_dir),
        "source_v2721_manifest": rel(Path(args.v2721_manifest)),
        "source_v2632_events": rel(Path(args.v2632_events)),
        "decision": decision,
        "ok": not blockers,
        "blockers": blockers,
        "v2722_result": result,
        "v2721_replay_order": v2721_order,
        "v2721_per_device_order": per_device_order,
        "v2632_event_order": v2632_order,
        "goal_text_order_claim": GOAL_ORDER_CLAIM,
        "per_device_matches_v2632": per_device_matches_v2632,
        "goal_order_conflict_with_v2632_events": goal_order_conflict,
        "stale_cal_types_present": stale_present,
        "old_stale_markers": old_markers,
        "old_stale_cleared": old_stale_cleared,
        "new_frontier_markers": new_markers,
        "new_frontier_present": new_frontier_present,
        "next_recommended_unit": "host-only helper/logging update to record per-SET ioctl return/errno and dmesg after SET replay before PCM prepare; do not reintroduce cal_type 10/14/24",
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# NATIVE_INIT V2723 — V2722 ACDB replay frontier analysis",
        "",
        "Date: 2026-06-18",
        "",
        "## Scope",
        "",
        "Host-only analysis of the V2722 corrected ACDB SET replay result. This",
        "unit does not run device actions, flash, calibration ioctls, or playback.",
        "It consumes only metadata/dmesg from the private V2722 run and existing",
        "private manifests.",
        "",
        "## Decision",
        "",
        f"- decision: `{payload['decision']}`",
        f"- ok: `{payload['ok']}`",
        f"- source_v2722_run: `{payload['source_v2722_run']}`",
        f"- V2722 rollback_selftest_fail0: `{payload['v2722_result']['rollback_selftest_fail0']}`",
        f"- SET replay final marker reached: `{payload['v2722_result']['replay_start_ok']}`",
        f"- old stale ASM custom-topology markers cleared: `{payload['old_stale_cleared']}`",
        f"- new AFE/q6asm/ADM frontier markers present: `{payload['new_frontier_present']}`",
        f"- stale cal_type 10/14/24 in V2721 manifest: `{payload['stale_cal_types_present']}`",
        "",
        "## Order Audit",
        "",
        f"- V2721 full replay order: `{payload['v2721_replay_order']}`",
        f"- V2721 per-device order: `{payload['v2721_per_device_order']}`",
        f"- V2632 event order from private `setcal_capture` rows: `{payload['v2632_event_order']}`",
        f"- current GOAL text order claim: `{payload['goal_text_order_claim']}`",
        f"- V2721 per-device order matches V2632 events: `{payload['per_device_matches_v2632']}`",
        f"- GOAL text order conflicts with V2632 events: `{payload['goal_order_conflict_with_v2632_events']}`",
        "",
        "Interpretation: V2721/V2722 followed the on-disk V2632/V2633/V2634 captured",
        "order (`13,9,11,12,15,23,16,21`). The current GOAL prose also contains a",
        "newer order claim (`13,9,11,12,15,16,21,23`) that conflicts with those",
        "artifacts. Do not silently rerun either order as a guess; if the operator",
        "intends the newer order, make a separate host-only reordered manifest first.",
        "",
        "## Dmesg Marker Classification",
        "",
        "### Old stale path",
        "",
    ]
    for name, present in payload["old_stale_markers"].items():
        lines.append(f"- {name}: `{present}`")
    lines.extend(["", "### New frontier", ""])
    for name, present in payload["new_frontier_markers"].items():
        lines.append(f"- {name}: `{present}`")
    lines.extend(
        [
            "",
            "## Conclusion",
            "",
            "V2722 is a useful positive discriminator: removing cal_type 10/14/24",
            "cleared the old per-subsystem ASM custom-topology failure. The remaining",
            "failure is now the stock prepare path: AFE port `0x4000` calibration returns",
            "`ADSP_EBADPARAM`, q6asm reports `ADSP_ENEEDMORE`, and ADM open for topology",
            "`0x10004000` returns `ADSP_EFAILED`.",
            "",
            "The next useful unit is not another same-manifest replay and not a return to",
            "cal_type 10/14/24. It should add host-only/live-safe logging around the SET",
            "helper so the next run records each `AUDIO_SET_CALIBRATION` return/errno and",
            "captures dmesg immediately after SET replay but before PCM prepare. That will",
            "separate a kernel SET acceptance problem from a DSP-time payload/ordering",
            "problem.",
            "",
            "## Validation",
            "",
            "- `python3 -m py_compile workspace/public/src/scripts/revalidation/analyze_audio_acdb_v2722_frontier_v2723.py tests/test_analyze_audio_acdb_v2722_frontier_v2723.py`",
            "- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_analyze_audio_acdb_v2722_frontier_v2723 -v`",
            "- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/analyze_audio_acdb_v2722_frontier_v2723.py --write-report`",
            "- `git diff --check`",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v2722-run", type=Path, default=DEFAULT_V2722_RUN)
    parser.add_argument("--v2721-manifest", type=Path, default=DEFAULT_V2721_MANIFEST)
    parser.add_argument("--v2632-events", type=Path, default=DEFAULT_V2632_EVENTS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--write-report", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_payload(args)
    if args.write_report:
        write_report(args.report, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
