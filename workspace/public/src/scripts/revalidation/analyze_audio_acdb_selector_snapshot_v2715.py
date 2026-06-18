#!/usr/bin/env python3
"""V2715 host-only interpretation of the V2714 ACDB selector deep snapshot.

The V2714 live run recovered deep selector/node/block words plus non-zero lower
custom-topology GET payloads for cal_types 24/10/14.  This audit determines
whether that evidence changes the replay frontier or only confirms that the lower
hidden selector path still returns the stale lower custom-topology family.

It reads metadata JSON/report text only. It does not read raw ACDB payload bytes,
run a device step, issue /dev/msm_audio_cal ioctls, or perform PCM/audio writes.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[5]
RUN_ID = "V2715"
DEFAULT_V2714_RESULT = ROOT / "workspace/private/runs/audio/v2714-acdb-selector-deep-snapshot-20260618-202450/v2714-result.json"
DEFAULT_V2711_REPORT = ROOT / "docs/reports/NATIVE_INIT_V2711_AUDIO_ACDB_SETARG_GEOMETRY_FRONTIER_2026-06-18.md"
DEFAULT_V2712_REPORT = ROOT / "docs/reports/NATIVE_INIT_V2712_AUDIO_ACDB_SELECTED_PAYLOAD_FRONTIER_2026-06-18.md"
DEFAULT_V2708_REPORT = ROOT / "docs/reports/NATIVE_INIT_V2708_AUDIO_ACDB_SUBSYSTEM_TOPOLOGY_SETCAL_REPLAY_LIVE_2026-06-18.md"
DEFAULT_REPORT = ROOT / "docs/reports/NATIVE_INIT_V2715_AUDIO_ACDB_SELECTOR_SNAPSHOT_INTERPRETATION_2026-06-18.md"

TARGETS = {
    24: {"role": "AFE_CUST_TOPOLOGY", "selected_topology": 0x1001025D},
    10: {"role": "ADM_CUST_TOPOLOGY", "selected_topology": 0x10004000},
    14: {"role": "ASM_CUST_TOPOLOGY", "selected_topology": 0x10005000},
}
EXPECTED_SIZES = {24: 1180, 10: 16076, 14: 2356}
EXPECTED_SHAS = {
    24: "53307305946f1a39e1d57de10c5bb7d65d120ea8f1c90725d0432b684c8e92c4",
    10: "fef3ed8df47486a54e625d632961f93366807f70413b47e08b35e7d00216ca36",
    14: "bc03e4be2dc4667ebfaf14b27ecc088f28fb23f784b352c14f0524963f7b7c98",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path | str | None) -> str | None:
    if path is None:
        return None
    target = Path(path)
    try:
        return str(target.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def int_from_any(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 0)
        except ValueError:
            return None
    return None


def word_list(values: Any) -> list[int]:
    if not isinstance(values, list):
        return []
    output: list[int] = []
    for value in values:
        parsed = int_from_any(value)
        if parsed is not None:
            output.append(parsed & 0xFFFFFFFF)
    return output


def hex32(value: int | None) -> str | None:
    if value is None:
        return None
    return f"0x{value & 0xFFFFFFFF:08x}"


def report_has(path: Path, *needles: str) -> bool:
    text = read_text(path)
    return all(needle in text for needle in needles)


def extract_rows(v2714: dict[str, Any]) -> dict[int, dict[str, Any]]:
    summary = v2714.get("selector_snapshot_summary") or {}
    selector_by_cal: dict[int, dict[str, Any]] = {}
    for row in summary.get("selector_rows") or []:
        cal_type = int_from_any(row.get("cal_type"))
        if cal_type in TARGETS:
            selector_by_cal[cal_type] = row
    target_by_cal: dict[int, dict[str, Any]] = {}
    for row in summary.get("target_rows") or []:
        cal_type = int_from_any(row.get("target_cal_type"))
        if cal_type in TARGETS:
            target_by_cal[cal_type] = row

    rows: dict[int, dict[str, Any]] = {}
    for cal_type, meta in TARGETS.items():
        selector = selector_by_cal.get(cal_type, {})
        target = target_by_cal.get(cal_type, {})
        node_words = word_list(selector.get("node_words"))
        block_words = word_list(selector.get("block_words"))
        selected = int(meta["selected_topology"])
        selected_in_selector_words = selected in node_words or selected in block_words
        rows[cal_type] = {
            "cal_type": cal_type,
            "role": meta["role"],
            "selected_topology": hex32(selected),
            "selector_present": bool(selector),
            "node_word_count": len(node_words),
            "block_word_count": len(block_words),
            "node_word0": hex32(node_words[0]) if len(node_words) > 0 else None,
            "node_block_pointer": hex32(node_words[2]) if len(node_words) > 2 else None,
            "block_get_arg0": hex32(block_words[0]) if len(block_words) > 0 else None,
            "block_get_arg1": hex32(block_words[1]) if len(block_words) > 1 else None,
            "block_get_ptr": hex32(block_words[2]) if len(block_words) > 2 else None,
            "block_mem_handle": block_words[3] if len(block_words) > 3 else None,
            "selector_words_contain_selected_topology": selected_in_selector_words,
            "payload_present": bool(target),
            "payload_len": int_from_any(target.get("out_len")),
            "payload_sha256": target.get("sha256"),
            "payload_len_matches_replayed_family": int_from_any(target.get("out_len")) == EXPECTED_SIZES[cal_type],
            "payload_sha_matches_replayed_family": str(target.get("sha256", "")).lower() == EXPECTED_SHAS[cal_type],
        }
    return rows


def contiguous_handles(rows: dict[int, dict[str, Any]]) -> bool:
    handles = [rows[cal]["block_mem_handle"] for cal in (24, 10, 14)]
    return handles == [35, 36, 37]


def block_shape_lower_hidden(rows: dict[int, dict[str, Any]]) -> bool:
    for cal_type in TARGETS:
        row = rows[cal_type]
        if row["block_get_arg0"] != "0x00001000" or row["block_get_arg1"] != "0x00000001":
            return False
        if row["node_word_count"] < 16 or row["block_word_count"] < 32:
            return False
        if row["selector_words_contain_selected_topology"]:
            return False
        if not row["payload_len_matches_replayed_family"] or not row["payload_sha_matches_replayed_family"]:
            return False
    return contiguous_handles(rows)


def build_summary(args: argparse.Namespace) -> dict[str, Any]:
    v2714 = read_json(args.v2714_result)
    rows = extract_rows(v2714)
    v2714_success = bool(v2714.get("success") and v2714.get("rolled_back"))
    v2711_closed = report_has(args.v2711_report, "v2711-setarg-geometry-exhausted-selector-payload-frontier")
    v2712_exhausted = report_has(args.v2712_report, "v2712-existing-payload-corpus-exhausted-need-new-selector-model")
    v2708_replayed_same = report_has(
        args.v2708_report,
        "| 1 | 24 | 1180 | `AUDIO_SET_CALIBRATION ok` |",
        "| 2 | 10 | 16076 | `AUDIO_SET_CALIBRATION ok` |",
        "| 3 | 14 | 2356 | `AUDIO_SET_CALIBRATION ok` |",
        "send_asm_custom_topology: DSP returned error[ADSP_EBADPARAM]",
    )
    lower_shape = block_shape_lower_hidden(rows)
    no_new_replay_contract = bool(v2714_success and v2711_closed and v2712_exhausted and v2708_replayed_same and lower_shape)
    return {
        "run_id": RUN_ID,
        "created_at": now_iso(),
        "host_only": True,
        "device_action": False,
        "raw_payload_read": False,
        "inputs": {
            "v2714_result": rel(args.v2714_result),
            "v2711_report": rel(args.v2711_report),
            "v2712_report": rel(args.v2712_report),
            "v2708_report": rel(args.v2708_report),
        },
        "rows": rows,
        "classification": {
            "decision": "v2715-selector-snapshot-confirms-lower-hidden-stale-path-no-replay" if no_new_replay_contract else "v2715-selector-snapshot-frontier-open",
            "v2714_capture_success": v2714_success,
            "v2711_setarg_geometry_closed": v2711_closed,
            "v2712_existing_payloads_exhausted": v2712_exhausted,
            "v2708_replayed_same_payload_family_and_failed": v2708_replayed_same,
            "selector_block_shape_is_lower_hidden_family": lower_shape,
            "contiguous_mem_handles_35_36_37": contiguous_handles(rows),
            "all_payloads_match_replayed_family": all(row["payload_len_matches_replayed_family"] and row["payload_sha_matches_replayed_family"] for row in rows.values()),
            "any_selector_word_contains_selected_topology": any(row["selector_words_contain_selected_topology"] for row in rows.values()),
            "native_replay_should_remain_parked": no_new_replay_contract,
            "recommended_next": "route-specific-real-hal-custom-topology-set-capture-or-loader-selector-re",
        },
        "next_requirements": [
            "Do not run another V2639 replay using V2707/V2714 lower-hidden payloads unchanged.",
            "Treat V2714 as evidence that the lower hidden path still selects the same stale payload family for cal10/cal14.",
            "Recover the route-specific Android-good custom-topology SET path for selected ADM/ASM, or RE the selector inputs that should produce selected topology IDs 0x10004000 and 0x10005000.",
            "If a new replay is built, it must change the cal10/cal14 payload/selector contract, not only restage the same SHA values.",
        ],
    }


def write_report(summary: dict[str, Any], path: Path) -> None:
    c = summary["classification"]
    lines = [
        "# NATIVE_INIT V2715 — ACDB selector snapshot interpretation",
        "",
        "Date: 2026-06-18",
        "",
        "## Scope",
        "",
        "Host-only interpretation of V2714 selector deep-snapshot metadata. This unit reads",
        "metadata JSON/report text only: no raw ACDB payload bytes, device action, audio ioctl,",
        "mixer write, PCM probe, or speaker playback occurred.",
        "",
        "## Result",
        "",
        f"- decision: `{c['decision']}`",
        f"- v2714_capture_success: `{c['v2714_capture_success']}`",
        f"- v2711_setarg_geometry_closed: `{c['v2711_setarg_geometry_closed']}`",
        f"- v2712_existing_payloads_exhausted: `{c['v2712_existing_payloads_exhausted']}`",
        f"- v2708_replayed_same_payload_family_and_failed: `{c['v2708_replayed_same_payload_family_and_failed']}`",
        f"- selector_block_shape_is_lower_hidden_family: `{c['selector_block_shape_is_lower_hidden_family']}`",
        f"- contiguous_mem_handles_35_36_37: `{c['contiguous_mem_handles_35_36_37']}`",
        f"- all_payloads_match_replayed_family: `{c['all_payloads_match_replayed_family']}`",
        f"- any_selector_word_contains_selected_topology: `{c['any_selector_word_contains_selected_topology']}`",
        f"- native_replay_should_remain_parked: `{c['native_replay_should_remain_parked']}`",
        f"- recommended_next: `{c['recommended_next']}`",
        "",
        "## Selector Snapshot Rows",
        "",
        "| cal_type | role | selected topology | node_word0 | node_block_ptr | block_arg0 | block_arg1 | block_ptr | mem_handle | selected_in_words | payload_len | payload_sha_match |",
        "| ---: | --- | --- | --- | --- | --- | --- | --- | ---: | --- | ---: | --- |",
    ]
    for cal_type in (24, 10, 14):
        row = summary["rows"][cal_type]
        lines.append(
            f"| {cal_type} | `{row['role']}` | `{row['selected_topology']}` | `{row['node_word0']}` | "
            f"`{row['node_block_pointer']}` | `{row['block_get_arg0']}` | `{row['block_get_arg1']}` | "
            f"`{row['block_get_ptr']}` | {row['block_mem_handle']} | `{row['selector_words_contain_selected_topology']}` | "
            f"{row['payload_len']} | `{row['payload_sha_matches_replayed_family']}` |"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        "V2714 captured the missing deep selector state, but it did not create a new replay contract.",
        "The selector blocks for cal_types 24/10/14 are the same lower-hidden family: `arg0=0x1000`,",
        "`arg1=1`, adjacent payload pointers, and contiguous mem_handles 35/36/37. None of the",
        "selector words contains the selected ADM/ASM topology IDs. The payload lengths and SHA-256",
        "values are exactly the family already replayed in V2708, which reached the DSP and failed at",
        "`send_asm_custom_topology` with `ADSP_EBADPARAM`.",
        "",
        "Therefore a new native replay using V2714 bytes unchanged is low-value and should remain parked.",
        "The next useful frontier is route-specific Android-good custom-topology SET capture or loader",
        "selector RE that changes the cal10/cal14 selected-payload contract.",
        "",
        "## Next Requirements",
        "",
    ])
    for item in summary["next_requirements"]:
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## Validation",
        "",
        "- `python3 -m py_compile workspace/public/src/scripts/revalidation/analyze_audio_acdb_selector_snapshot_v2715.py tests/test_analyze_audio_acdb_selector_snapshot_v2715.py`",
        "- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_analyze_audio_acdb_selector_snapshot_v2715 -v`",
        "- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/analyze_audio_acdb_selector_snapshot_v2715.py --write-report --json`",
        "- `git diff --check`",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v2714-result", type=Path, default=DEFAULT_V2714_RESULT)
    parser.add_argument("--v2711-report", type=Path, default=DEFAULT_V2711_REPORT)
    parser.add_argument("--v2712-report", type=Path, default=DEFAULT_V2712_REPORT)
    parser.add_argument("--v2708-report", type=Path, default=DEFAULT_V2708_REPORT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    summary = build_summary(args)
    if args.write_report:
        write_report(summary, args.report)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["classification"]["decision"] == "v2715-selector-snapshot-confirms-lower-hidden-stale-path-no-replay" else 1


if __name__ == "__main__":
    raise SystemExit(main())
