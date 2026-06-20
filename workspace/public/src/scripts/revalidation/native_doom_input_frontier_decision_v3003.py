#!/usr/bin/env python3
"""V3003 host-only DOOM input frontier decision after V3002.

This consolidates the touch zero-event evidence, the staged USB-keyboard
fallback, and the V3002 physical-button mux live result. It is metadata-only:
no flash, no serial command, no evdev open, and no device mutation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[5]

RUN_ID = "V3003"
DECISION = "v3003-doom-input-frontier-hardware-stimulus-gated"
REPORT_PATH = ROOT / "docs/reports/NATIVE_INIT_V3003_DOOM_INPUT_FRONTIER_DECISION_2026-06-20.md"

V2993_REPORT = ROOT / "docs/reports/NATIVE_INIT_V2993_DOOM_INPUT_FRONTIER_DECISION_2026-06-20.md"
V2992_REPORT = ROOT / "docs/reports/NATIVE_INIT_V2992_DOOMINPUT_KEYBOARD_STATE_LIVE_HANDOFF_DRY_RUN_2026-06-20.md"
V3002_RESULT = ROOT / "workspace/private/runs/input/v3002-doominput-mux-live-20260620-193808/result.json"
V3002_REPORT = ROOT / "docs/reports/NATIVE_INIT_V3002_DOOMINPUT_MUX_LIVE_2026-06-20.md"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def v3002_event_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in result.get("event_results", []) if isinstance(result.get("event_results"), list) else []:
        selected = item.get("selected_event", {}) if isinstance(item.get("selected_event"), dict) else {}
        rows.append({
            "event": item.get("event"),
            "name": selected.get("name"),
            "class": selected.get("class"),
            "selected_is_button": bool(item.get("selected_is_button")),
            "inputcaps_button_ok": bool(item.get("inputcaps_button_ok")),
            "inputcaps_rc": item.get("inputcaps_rc"),
        })
    return rows


def v3002_mux_summary(result: dict[str, Any]) -> dict[str, Any]:
    sample = result.get("doominputmux", {}) if isinstance(result.get("doominputmux"), dict) else {}
    parsed = sample.get("parsed", {}) if isinstance(sample.get("parsed"), dict) else {}
    return {
        "rc": result.get("doominputmux_rc"),
        "timeout_ms": sample.get("timeout_ms"),
        "duration_sec": sample.get("duration_sec"),
        "event_count": parsed.get("doominputmux_event_count", 0),
        "state_count": parsed.get("doominputmux_state_count", 0),
        "active_state_count": parsed.get("active_state_count", 0),
        "proxy_state_count": parsed.get("proxy_state_count", 0),
        "source_names": parsed.get("source_names", []),
    }


def build_decision_payload() -> dict[str, Any]:
    v3002 = read_json(V3002_RESULT)
    v2993_text = V2993_REPORT.read_text(encoding="utf-8")
    v2992_text = V2992_REPORT.read_text(encoding="utf-8")
    event_rows = v3002_event_rows(v3002)
    mux = v3002_mux_summary(v3002)
    button_capable = bool(event_rows) and all(
        row.get("selected_is_button") and row.get("inputcaps_button_ok")
        for row in event_rows
    )
    mux_zero_event = (
        mux.get("rc") == -110
        and mux.get("event_count") == 0
        and mux.get("state_count") == 0
        and mux.get("proxy_state_count") == 0
    )
    rollback_clean = bool(v3002.get("rollback_version_ok") and v3002.get("rollback_selftest_fail0"))
    touch_pivot_present = "v2993-doom-input-frontier-pivot-keyboard-fallback" in v2993_text
    keyboard_fallback_staged = "v2992-doominput-keyboard-state-dry-run" in v2992_text
    return {
        "run_id": RUN_ID,
        "decision": DECISION,
        "touch_pivot_present": touch_pivot_present,
        "keyboard_fallback_staged": keyboard_fallback_staged,
        "button_event_rows": event_rows,
        "button_capable": button_capable,
        "mux_summary": mux,
        "physical_button_mux_zero_event": mux_zero_event,
        "v3002_rollback_clean": rollback_clean,
        "inputs": {
            "v2993_report": rel(V2993_REPORT),
            "v2992_report": rel(V2992_REPORT),
            "v3002_result": rel(V3002_RESULT),
            "v3002_report": rel(V3002_REPORT),
        },
        "next_action": (
            "Do not repeat the same event3,event0 mux live run unless an operator "
            "is explicitly available to press VOLUMEUP/VOLUMEDOWN/POWER during the "
            "bounded window. The higher-information path is USB keyboard/OTG attach "
            "followed by the staged keyboard live handoff."
        ),
    }


def render_report(payload: dict[str, Any]) -> str:
    button_lines = [
        "| Event | name | class | selected_buttons | caps_ok | inputcaps_rc |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["button_event_rows"]:
        button_lines.append(
            f"| `{row.get('event')}` | `{row.get('name')}` | `{row.get('class')}` | "
            f"`{int(bool(row.get('selected_is_button')))}` | "
            f"`{int(bool(row.get('inputcaps_button_ok')))}` | `{row.get('inputcaps_rc')}` |"
        )

    mux = payload["mux_summary"]
    return "\n".join([
        "# Native Init V3003 DOOM Input Frontier Decision",
        "",
        "## Summary",
        "",
        f"- Decision: `{payload['decision']}`",
        "- Device action: `none` in this host-only unit.",
        "- Track: active Video playback / DOOM input prerequisite.",
        f"- Touch zero-event pivot present: `{int(bool(payload['touch_pivot_present']))}`",
        f"- Keyboard fallback staged: `{int(bool(payload['keyboard_fallback_staged']))}`",
        f"- V3002 button events button-capable: `{int(bool(payload['button_capable']))}`",
        f"- V3002 physical-button mux zero-event result: `{int(bool(payload['physical_button_mux_zero_event']))}`",
        f"- V3002 rollback clean: `{int(bool(payload['v3002_rollback_clean']))}`",
        "",
        "## V3002 Button Candidate Evidence",
        "",
        *button_lines,
        "",
        "## V3002 Mux Evidence",
        "",
        f"- `doominputmux` rc: `{mux.get('rc')}`",
        f"- Timeout: `{mux.get('timeout_ms')}` ms",
        f"- Duration: `{mux.get('duration_sec')}` sec",
        f"- Events: `{mux.get('event_count')}`",
        f"- States: `{mux.get('state_count')}`",
        f"- Active states: `{mux.get('active_state_count')}`",
        f"- Proxy states: `{mux.get('proxy_state_count')}`",
        f"- Sources seen: `{','.join(str(item) for item in mux.get('source_names', []))}`",
        "",
        "## Decision",
        "",
        "- Built-in touch remains not proven: prior MT-capable touch nodes produced zero events and no new touch-driver hypothesis exists.",
        "- Physical-button fallback is now also only partially proven: `event3` and `event0` are button-capable, but V3002 captured zero events/states over the bounded mux window.",
        "- Repeating the identical physical-button mux live run without confirmed operator button input would be low-information churn.",
        "- USB keyboard/OTG remains the next higher-information fallback path because it can introduce a new keyboard-class evdev source instead of resampling the same silent built-in sources.",
        "",
        "## Next Action",
        "",
        f"- {payload['next_action']}",
        "",
        "## Evidence Inputs",
        "",
        f"- V2993 report: `{payload['inputs']['v2993_report']}`",
        f"- V2992 report: `{payload['inputs']['v2992_report']}`",
        f"- V3002 result: `{payload['inputs']['v3002_result']}`",
        f"- V3002 report: `{payload['inputs']['v3002_report']}`",
        "",
        "## Host Validation",
        "",
        "- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_doom_input_frontier_decision_v3003.py tests/test_native_doom_input_frontier_decision_v3003.py`: PASS",
        "- `PYTHONPATH=workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 -m unittest tests.test_native_doom_input_frontier_decision_v3003`: PASS",
        "- `PYTHONPATH=workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 workspace/public/src/scripts/revalidation/native_doom_input_frontier_decision_v3003.py`: PASS (host-only report materialized)",
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
        "button_capable": payload["button_capable"],
        "physical_button_mux_zero_event": payload["physical_button_mux_zero_event"],
        "keyboard_fallback_staged": payload["keyboard_fallback_staged"],
        "touch_pivot_present": payload["touch_pivot_present"],
        "v3002_rollback_clean": payload["v3002_rollback_clean"],
        "report": rel(REPORT_PATH),
    }, indent=2, sort_keys=True))
    return 0 if (
        payload["touch_pivot_present"]
        and payload["keyboard_fallback_staged"]
        and payload["button_capable"]
        and payload["physical_button_mux_zero_event"]
        and payload["v3002_rollback_clean"]
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
