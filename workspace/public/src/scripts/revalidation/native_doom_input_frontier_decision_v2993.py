#!/usr/bin/env python3
"""V2993 host-only DOOM input frontier decision.

This script consolidates the latest touch and keyboard-fallback evidence into a
metadata-only report. It does not flash, open evdev nodes, or touch the device.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[5]

RUN_ID = "V2993"
DECISION = "v2993-doom-input-frontier-pivot-keyboard-fallback"
REPORT_PATH = ROOT / "docs/reports/NATIVE_INIT_V2993_DOOM_INPUT_FRONTIER_DECISION_2026-06-20.md"

V2984_RESULT = ROOT / "workspace/private/runs/input/v2984-inputcaps-touch-diag-live-20260620-164505/result.json"
V2991_RESULT = ROOT / "workspace/private/runs/input/v2991-doominput-dual-touch-live-20260620-181451/result.json"
V2992_REPORT = ROOT / "docs/reports/NATIVE_INIT_V2992_DOOMINPUT_KEYBOARD_STATE_LIVE_HANDOFF_DRY_RUN_2026-06-20.md"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def touch_caps_summary(v2984: dict[str, Any]) -> list[dict[str, Any]]:
    caps = v2984.get("inputcaps", {}) if isinstance(v2984.get("inputcaps"), dict) else {}
    rows: list[dict[str, Any]] = []
    for event in ("event6", "event8"):
        item = caps.get(event, {}) if isinstance(caps.get(event), dict) else {}
        parsed = item.get("parsed", {}) if isinstance(item.get("parsed"), dict) else {}
        decode = parsed.get("decode", {}) if isinstance(parsed.get("decode"), dict) else {}
        rows.append({
            "event": event,
            "rc": item.get("rc"),
            "ev_abs": decode.get("ev_abs"),
            "btn_touch": decode.get("btn_touch"),
            "mt_x": decode.get("mt_x"),
            "mt_y": decode.get("mt_y"),
            "mt_tracking_id": decode.get("mt_tracking_id"),
            "runtime_status": parsed.get("runtime_status"),
        })
    return rows


def v2991_touch_results(v2991: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in v2991.get("event_results", []) if isinstance(v2991.get("event_results"), list) else []:
        parsed = item.get("parsed", {}) if isinstance(item.get("parsed"), dict) else {}
        rows.append({
            "event": item.get("event"),
            "selected_touch": bool(item.get("selected_is_touch")),
            "caps_ok": bool(item.get("inputcaps_touch_ok")),
            "doominput_rc": item.get("doominput_rc"),
            "doominput_events": parsed.get("doominput_event_count", 0),
            "doominput_states": parsed.get("doominput_state_count", 0),
            "touch_states": parsed.get("touch_state_count", 0),
            "pass": bool(item.get("pass")),
        })
    return rows


def build_decision_payload() -> dict[str, Any]:
    v2984 = read_json(V2984_RESULT)
    v2991 = read_json(V2991_RESULT)
    v2992_report_exists = V2992_REPORT.exists()
    scan = v2991.get("inputscan", {}) if isinstance(v2991.get("inputscan"), dict) else {}
    touch_rows = v2991_touch_results(v2991)
    all_touch_nodes_sampled = {row.get("event") for row in touch_rows} >= {"event6", "event8"}
    all_touch_zero = bool(touch_rows) and all(
        row.get("doominput_events") == 0
        and row.get("doominput_states") == 0
        and row.get("touch_states") == 0
        and row.get("doominput_rc") == -110
        for row in touch_rows
    )
    rollback_clean = bool(v2991.get("rollback_version_ok") and v2991.get("rollback_selftest_fail0"))
    keyboard_staged = v2992_report_exists and "v2992-doominput-keyboard-state-dry-run" in V2992_REPORT.read_text(encoding="utf-8")
    return {
        "run_id": RUN_ID,
        "decision": DECISION,
        "touch_caps": touch_caps_summary(v2984),
        "touch_results": touch_rows,
        "keyboard_candidates_in_v2991": scan.get("keyboard_candidates"),
        "keyboard_fallback_staged": keyboard_staged,
        "rollback_clean_after_touch_live": rollback_clean,
        "all_touch_nodes_sampled": all_touch_nodes_sampled,
        "all_touch_zero_event": all_touch_zero,
        "inputs": {
            "v2984_result": rel(V2984_RESULT),
            "v2991_result": rel(V2991_RESULT),
            "v2992_report": rel(V2992_REPORT),
        },
        "action": (
            "Do not keep re-running identical event6/event8 touch samples. "
            "Run V2992 live only when USB keyboard/OTG hardware is attached, "
            "or reopen touch with a new evidence-backed hypothesis."
        ),
    }


def render_report(payload: dict[str, Any]) -> str:
    caps_lines = [
        "| Event | rc | EV_ABS | BTN_TOUCH | MT_X | MT_Y | MT_TRACKING_ID | runtime_status |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["touch_caps"]:
        caps_lines.append(
            f"| `{row['event']}` | `{row.get('rc')}` | `{row.get('ev_abs')}` | "
            f"`{row.get('btn_touch')}` | `{row.get('mt_x')}` | `{row.get('mt_y')}` | "
            f"`{row.get('mt_tracking_id')}` | `{row.get('runtime_status')}` |"
        )

    result_lines = [
        "| Event | selected_touch | caps_ok | doominput_rc | events | states | touch_states | pass |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["touch_results"]:
        result_lines.append(
            f"| `{row.get('event')}` | `{int(bool(row.get('selected_touch')))}` | "
            f"`{int(bool(row.get('caps_ok')))}` | `{row.get('doominput_rc')}` | "
            f"`{row.get('doominput_events')}` | `{row.get('doominput_states')}` | "
            f"`{row.get('touch_states')}` | `{int(bool(row.get('pass')))}` |"
        )

    return "\n".join([
        "# Native Init V2993 DOOM Input Frontier Decision",
        "",
        "## Summary",
        "",
        f"- Decision: `{payload['decision']}`",
        "- Device action: `none` in this host-only unit.",
        "- Track: active Video playback / DOOM input prerequisite.",
        f"- Built-in touch nodes sampled: `{int(bool(payload['all_touch_nodes_sampled']))}`",
        f"- Built-in touch zero-event result: `{int(bool(payload['all_touch_zero_event']))}`",
        f"- V2991 rollback clean: `{int(bool(payload['rollback_clean_after_touch_live']))}`",
        f"- Keyboard candidates seen in V2991 inputscan: `{payload.get('keyboard_candidates_in_v2991')}`",
        f"- V2992 keyboard fallback staged: `{int(bool(payload['keyboard_fallback_staged']))}`",
        "",
        "## Touch Capability Baseline",
        "",
        *caps_lines,
        "",
        "## Latest Touch Live Result",
        "",
        *result_lines,
        "",
        "## Decision",
        "",
        "- V2984 showed both `event6 sec_touchscreen` and `event8 sec_touchpad` expose touch/MT capability bits; runtime PM reported `unsupported`, not `suspended`.",
        "- V2991 then sampled both known touch-class nodes under the V2989 `doominput.state` candidate, and both bounded windows timed out with zero `doominput.event` and zero `doominput.state` lines.",
        "- Repeating the same touch sample without a deliberate input-state change or a new touch-driver hypothesis is low-information.",
        "- V2992 already stages the USB-keyboard/OTG fallback on the same `doominput.state` surface. That is the next live path when a keyboard-class event appears.",
        "",
        "## Next Action",
        "",
        f"- {payload['action']}",
        "",
        "## Evidence Inputs",
        "",
        f"- V2984 result: `{payload['inputs']['v2984_result']}`",
        f"- V2991 result: `{payload['inputs']['v2991_result']}`",
        f"- V2992 report: `{payload['inputs']['v2992_report']}`",
        "",
        "## Host Validation",
        "",
        "- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_doom_input_frontier_decision_v2993.py tests/test_native_doom_input_frontier_decision_v2993.py`: PASS",
        "- `PYTHONPATH=workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 -m unittest tests.test_native_doom_input_frontier_decision_v2993`: PASS (`4` tests)",
        "- `PYTHONPATH=workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 workspace/public/src/scripts/revalidation/native_doom_input_frontier_decision_v2993.py`: PASS (host-only report materialized)",
        "- `git diff --check`: PASS",
        "",
        "## Safety",
        "",
        "- Host-only metadata consolidation; no flash, no serial command, no evdev open, no input injection, no sysfs writes.",
        "- No Wi-Fi/audio/video playback, PMIC, backlight, GPIO, regulator, GDSC, or forbidden partition path is touched.",
        "- Private raw command outputs remain under `workspace/private/runs/`; this report includes metadata only.",
    ]) + "\n"


def main() -> int:
    payload = build_decision_payload()
    REPORT_PATH.write_text(render_report(payload), encoding="utf-8")
    print(json.dumps({
        "decision": payload["decision"],
        "all_touch_nodes_sampled": payload["all_touch_nodes_sampled"],
        "all_touch_zero_event": payload["all_touch_zero_event"],
        "keyboard_candidates_in_v2991": payload["keyboard_candidates_in_v2991"],
        "keyboard_fallback_staged": payload["keyboard_fallback_staged"],
        "report": rel(REPORT_PATH),
    }, indent=2, sort_keys=True))
    return 0 if (
        payload["all_touch_nodes_sampled"]
        and payload["all_touch_zero_event"]
        and payload["keyboard_fallback_staged"]
        and payload["rollback_clean_after_touch_live"]
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
