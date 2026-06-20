#!/usr/bin/env python3
"""V2990 live handoff for DOOM input state validation.

This runner targets the V2989 ``doominput`` candidate. It stages a bounded
live validation path that flashes the candidate only in ``--live`` mode, reads
input inventory/capabilities, samples ``doominput <event>``, and rolls back to
the v2321 clean USB identity checkpoint. The path only reads input state; it
does not inject events, grab evdev nodes, alter keymaps, or write touch/sysfs
configuration.
"""

from __future__ import annotations

import argparse
import json
import re
import socket
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import a90ctl
from a90_serial_lock import SerialBridgeLock
import native_doom_keyboard_live_handoff_v2986 as keyboard_live
import native_inputcaps_touch_diag_live_handoff_v2984 as caps_live
import native_inputscan_live_handoff_v2978 as inputscan_live
import native_readinput_timeout_live_handoff_v2982 as readinput_live

base = inputscan_live.base
ROOT = inputscan_live.ROOT

RUN_ID = "V2990"
BUILD_TAG = "v2990-doominput-state-live"
DECISION_PREFIX = "v2990-doominput-state"
REPORT_PATH = ROOT / "docs/reports/NATIVE_INIT_V2990_DOOMINPUT_STATE_LIVE_HANDOFF_DRY_RUN_2026-06-20.md"

CANDIDATE_IMAGE = ROOT / "workspace/private/inputs/boot_images/boot_linux_v2989_doominput_state.img"
CANDIDATE_VERSION = "0.10.65"
CANDIDATE_TAG = "v2989-doominput-state"
CANDIDATE_SHA256 = "30e37c64196e7ff2649291c1398c67e96efea9313b25c51dade39d1c62c9ccc2"

ROLLBACK_IMAGE = inputscan_live.ROLLBACK_IMAGE
ROLLBACK_VERSION = inputscan_live.ROLLBACK_VERSION
ROLLBACK_SHA256 = inputscan_live.ROLLBACK_SHA256
FALLBACK_V2237 = inputscan_live.FALLBACK_V2237
FALLBACK_V2237_SHA256 = inputscan_live.FALLBACK_V2237_SHA256
FALLBACK_V48 = inputscan_live.FALLBACK_V48
SELFTEST_FAIL0_RE = inputscan_live.SELFTEST_FAIL0_RE

DEFAULT_COUNT = 32
DEFAULT_TIMEOUT_MS = 45000
VALID_MODES = ("auto", "touch", "keyboard")
TOUCH_PREFERRED_EVENTS = ("event6", "event8")
DOOM_BUTTON_FIELDS = ("forward", "back", "left", "right", "fire", "use", "menu", "run")

DOOM_EVENT_RE = re.compile(
    r"doominput\.event\s+(?P<index>\d+):\s+type=(?P<type>\S+)\s+"
    r"code=(?P<code>\S+)\s+role=(?P<role>\S+)\s+value=(?P<value>-?\d+)"
)
DOOM_STATE_RE = re.compile(
    r"doominput\.state\s+(?P<index>\d+):\s+"
    r"forward=(?P<forward>[01])\s+back=(?P<back>[01])\s+"
    r"left=(?P<left>[01])\s+right=(?P<right>[01])\s+"
    r"fire=(?P<fire>[01])\s+use=(?P<use>[01])\s+"
    r"menu=(?P<menu>[01])\s+run=(?P<run>[01])\s+"
    r"touch=(?P<touch>[01])\s+x=(?P<x>-?\d+)\s+y=(?P<y>-?\d+)\s+"
    r"has_x=(?P<has_x>[01])\s+has_y=(?P<has_y>[01])\s+"
    r"tracking=(?P<tracking>-?\d+)\s+slot=(?P<slot>-?\d+)\s+"
    r"pressure=(?P<pressure>-?\d+)\s+has_pressure=(?P<has_pressure>[01])\s+"
    r"active=(?P<active>[01])\s+frame=(?P<frame>\d+)"
)


def now_slug() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y%m%d-%H%M%S")


def rel(path: Path) -> str:
    return inputscan_live.rel(path)


def stdout_of(step: dict[str, Any] | None) -> str:
    return inputscan_live.stdout_of(step)


def write_json(path: Path, payload: Any) -> None:
    inputscan_live.av_live.write_json(path, payload)


def file_state(path: Path, expected_sha: str | None = None) -> dict[str, Any]:
    return inputscan_live.file_state(path, expected_sha)


def selftest_step_ok(step: dict[str, Any]) -> bool:
    return bool(SELFTEST_FAIL0_RE.search(stdout_of(step))) or base.protocol_selftest_ok(step)


def flash_command(image: Path, expect_version: str, expect_sha: str, *, from_native: bool) -> list[str]:
    return inputscan_live.flash_command(image, expect_version, expect_sha, from_native=from_native)


def class_tokens(item: dict[str, str]) -> set[str]:
    return {part.strip() for part in str(item.get("class", "")).split(",") if part.strip()}


def touch_caps_ok(parsed_caps: dict[str, Any]) -> bool:
    decoded = parsed_caps.get("decode", {}) if isinstance(parsed_caps.get("decode"), dict) else {}
    return bool(
        parsed_caps.get("has_event_header")
        and decoded.get("ev_abs") == "1"
        and decoded.get("btn_touch") == "1"
        and decoded.get("mt_x") == "1"
        and decoded.get("mt_y") == "1"
        and decoded.get("mt_tracking_id") == "1"
    )


def keyboard_caps_ok(parsed_caps: dict[str, Any]) -> bool:
    return keyboard_live.keyboard_caps_ok(parsed_caps)


def parse_doominput(text: str) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    states: list[dict[str, int]] = []
    for match in DOOM_EVENT_RE.finditer(text):
        events.append({
            "index": int(match.group("index"), 10),
            "type": match.group("type"),
            "code": match.group("code"),
            "role": match.group("role"),
            "value": int(match.group("value"), 10),
        })
    for match in DOOM_STATE_RE.finditer(text):
        states.append({
            "index": int(match.group("index"), 10),
            "forward": int(match.group("forward"), 10),
            "back": int(match.group("back"), 10),
            "left": int(match.group("left"), 10),
            "right": int(match.group("right"), 10),
            "fire": int(match.group("fire"), 10),
            "use": int(match.group("use"), 10),
            "menu": int(match.group("menu"), 10),
            "run": int(match.group("run"), 10),
            "touch": int(match.group("touch"), 10),
            "x": int(match.group("x"), 10),
            "y": int(match.group("y"), 10),
            "has_x": int(match.group("has_x"), 10),
            "has_y": int(match.group("has_y"), 10),
            "tracking": int(match.group("tracking"), 10),
            "slot": int(match.group("slot"), 10),
            "pressure": int(match.group("pressure"), 10),
            "has_pressure": int(match.group("has_pressure"), 10),
            "active": int(match.group("active"), 10),
            "frame": int(match.group("frame"), 10),
        })
    touch_states = [
        item for item in states
        if item.get("touch") == 1 or item.get("has_x") == 1 or item.get("has_y") == 1
    ]
    active_states = [item for item in states if item.get("active") == 1]
    doom_button_states = [
        item for item in states
        if any(item.get(field) == 1 for field in DOOM_BUTTON_FIELDS)
    ]
    return {
        "events": events,
        "states": states,
        "doominput_event_count": len(events),
        "doominput_state_count": len(states),
        "touch_state_count": len(touch_states),
        "active_state_count": len(active_states),
        "doom_button_state_count": len(doom_button_states),
        "has_touch_state": bool(touch_states),
        "has_active_state": bool(active_states),
        "has_doom_button_state": bool(doom_button_states),
        "max_frame": max((item["frame"] for item in states), default=None),
    }


def has_prompt_after_last_end(data: bytearray) -> bool:
    return readinput_live.has_prompt_after_last_end(data)


def run_timeout_doominput(host: str,
                          port: int,
                          event: str,
                          count: int,
                          *,
                          timeout_ms: int,
                          connect_timeout: float = 3.0,
                          command_timeout_margin: float = 8.0) -> dict[str, Any]:
    command = ["doominput", event, str(count), str(timeout_ms)]
    line = a90ctl.encode_cmdv1_line(command)
    data = bytearray()
    started = time.monotonic()
    command_timeout = (timeout_ms / 1000.0) + command_timeout_margin + connect_timeout
    with SerialBridgeLock(timeout_sec=command_timeout, purpose="v2990-doominput"):
        with socket.create_connection((host, port), timeout=connect_timeout) as sock:
            sock.settimeout(0.25)
            sock.sendall(("\n" + line + "\n").encode("utf-8"))
            deadline = started + command_timeout
            while True:
                if b"A90P1 END " in data and has_prompt_after_last_end(data):
                    break
                if time.monotonic() >= deadline:
                    break
                try:
                    chunk = sock.recv(8192)
                except socket.timeout:
                    continue
                if not chunk:
                    break
                data.extend(chunk)
    text = data.decode("utf-8", errors="replace")
    protocol: dict[str, Any] = {"begin": {}, "end": {}, "rc": None, "status": "missing"}
    protocol_error = None
    try:
        parsed = a90ctl.parse_protocol_output(text)
        protocol = {"begin": parsed.begin, "end": parsed.end, "rc": parsed.rc, "status": parsed.status}
    except Exception as exc:  # noqa: BLE001 - record partial output for report
        protocol_error = f"{type(exc).__name__}: {exc}"
    return {
        "command": command,
        "text": text,
        "timeout_ms": timeout_ms,
        "duration_sec": round(time.monotonic() - started, 3),
        "protocol": protocol,
        "protocol_error": protocol_error,
        "parsed": parse_doominput(text),
    }


def choose_event(parsed_scan: dict[str, Any], requested: str | None, mode: str) -> tuple[str, dict[str, str]]:
    events = parsed_scan.get("events", []) if isinstance(parsed_scan.get("events"), list) else []
    if requested:
        item = next((entry for entry in events if entry.get("event") == requested), {})
        if not item:
            return mode, {}
        tokens = class_tokens(item)
        if mode == "auto":
            if "keyboard" in tokens:
                return "keyboard", item
            if "touch" in tokens:
                return "touch", item
        return mode, item

    if mode in ("auto", "keyboard"):
        keyboard_events = parsed_scan.get("keyboard_events", [])
        if isinstance(keyboard_events, list) and keyboard_events:
            return "keyboard", keyboard_events[0]
        if mode == "keyboard":
            return "keyboard", {}

    if mode in ("auto", "touch"):
        touch_events = parsed_scan.get("touch_events", [])
        touch_list = touch_events if isinstance(touch_events, list) else []
        for preferred in TOUCH_PREFERRED_EVENTS:
            item = next((entry for entry in touch_list if entry.get("event") == preferred), {})
            if item:
                return "touch", item
        if touch_list:
            return "touch", touch_list[0]
        return "touch", {}

    return mode, {}


def evaluate_result(result: dict[str, Any]) -> bool:
    mode = result.get("selected_mode")
    selected = result.get("selected_event", {})
    caps = result.get("inputcaps", {}) if isinstance(result.get("inputcaps"), dict) else {}
    sample = result.get("doominput", {}) if isinstance(result.get("doominput"), dict) else {}
    parsed_sample = sample.get("parsed", {}) if isinstance(sample.get("parsed"), dict) else {}
    common_ok = bool(
        result.get("candidate_version_ok")
        and result.get("candidate_selftest_fail0")
        and result.get("inputscan_rc") == 0
        and selected
        and caps.get("rc") == 0
        and result.get("doominput_rc") == 0
        and result.get("candidate_selftest_after_doominput_fail0")
    )
    if not common_ok:
        return False
    if mode == "keyboard":
        return bool(
            "keyboard" in class_tokens(selected)
            and keyboard_caps_ok(caps.get("parsed", {}))
            and parsed_sample.get("has_doom_button_state")
        )
    if mode == "touch":
        return bool(
            "touch" in class_tokens(selected)
            and touch_caps_ok(caps.get("parsed", {}))
            and parsed_sample.get("has_touch_state")
        )
    return False


def preflight_state(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "run_id": RUN_ID,
        "candidate": file_state(CANDIDATE_IMAGE, CANDIDATE_SHA256),
        "rollback": file_state(ROLLBACK_IMAGE, ROLLBACK_SHA256),
        "fallback_v2237": file_state(FALLBACK_V2237, FALLBACK_V2237_SHA256),
        "fallback_v48": file_state(FALLBACK_V48),
        "flash_helper": file_state(base.FLASH),
        "candidate_version": CANDIDATE_VERSION,
        "candidate_tag": CANDIDATE_TAG,
        "requested_mode": args.mode,
        "requested_event": args.event,
        "count": args.count,
        "timeout_ms": args.timeout_ms,
        "operator_prerequisite": (
            "touch mode requires finger movement during the doominput window; "
            "keyboard mode requires USB keyboard/OTG attached and keys pressed"
        ),
        "hard_boundary": [
            "boot partition only via native_init_flash.py",
            "rollback to v2321 and verify selftest fail=0",
            "read-only inputscan/inputcaps plus read-only doominput evdev sample",
            "no input injection, no EVIOCGRAB, no keymap changes, no sysfs writes",
            "no Wi-Fi/audio/video playback/PMIC/backlight/GPIO/regulator/GDSC",
            "no forbidden partition path",
        ],
    }


def preflight_ok(state: dict[str, Any]) -> bool:
    return bool(
        state["candidate"].get("sha256_ok")
        and state["rollback"].get("sha256_ok")
        and state["fallback_v2237"].get("sha256_ok")
        and state["fallback_v48"].get("exists")
        and state["flash_helper"].get("exists")
        and state.get("requested_mode") in VALID_MODES
        and state.get("timeout_ms", 0) > 0
        and state.get("count", 0) > 0
    )


def mode_caps_ok(mode: str, parsed_caps: dict[str, Any]) -> bool:
    return touch_caps_ok(parsed_caps) if mode == "touch" else keyboard_caps_ok(parsed_caps)


def render_report(result: dict[str, Any]) -> str:
    live_executed = bool(result.get("live_executed"))
    preflight = result.get("preflight", {}) if isinstance(result.get("preflight"), dict) else {}
    inputscan = result.get("inputscan", {}) if isinstance(result.get("inputscan"), dict) else {}
    selected = result.get("selected_event", {}) if isinstance(result.get("selected_event"), dict) else {}
    caps = result.get("inputcaps", {}) if isinstance(result.get("inputcaps"), dict) else {}
    sample = result.get("doominput", {}) if isinstance(result.get("doominput"), dict) else {}
    parsed_sample = sample.get("parsed", {}) if isinstance(sample.get("parsed"), dict) else {}

    candidate_lines = []
    for item in inputscan.get("keyboard_events", []) if isinstance(inputscan.get("keyboard_events"), list) else []:
        candidate_lines.append(f"- keyboard `{item.get('event')}` `{item.get('name')}` class=`{item.get('class')}`")
    for item in inputscan.get("touch_events", []) if isinstance(inputscan.get("touch_events"), list) else []:
        candidate_lines.append(f"- touch `{item.get('event')}` `{item.get('name')}` class=`{item.get('class')}`")
    if not candidate_lines:
        candidate_lines = ["- none captured in this run"]

    state_lines = []
    for item in parsed_sample.get("states", [])[:12] if isinstance(parsed_sample.get("states"), list) else []:
        buttons = ",".join(field for field in DOOM_BUTTON_FIELDS if item.get(field) == 1) or "-"
        state_lines.append(
            f"- index=`{item.get('index')}` touch=`{item.get('touch')}` "
            f"x=`{item.get('x')}` y=`{item.get('y')}` has_x=`{item.get('has_x')}` "
            f"has_y=`{item.get('has_y')}` active=`{item.get('active')}` "
            f"frame=`{item.get('frame')}` buttons=`{buttons}`"
        )
    if not state_lines:
        state_lines = ["- none captured"]

    def live_bool(value: Any) -> str:
        return str(int(bool(value))) if live_executed else "not-run"

    def live_value(value: Any) -> str:
        return str(value) if live_executed else "not-run"

    return "\n".join([
        "# Native Init V2990 DOOM Input State Live Handoff Dry Run",
        "",
        "## Summary",
        "",
        f"- Decision: `{result.get('decision')}`",
        f"- Result before rollback: `{int(bool(result.get('pass')))}`",
        "- Track: active Video playback / DOOM input prerequisite.",
        f"- Candidate: `A90 Linux init {CANDIDATE_VERSION} ({CANDIDATE_TAG})`",
        f"- Candidate image: `{rel(CANDIDATE_IMAGE)}`",
        f"- Candidate SHA256: `{CANDIDATE_SHA256}`",
        f"- Private run dir: `{result.get('out_dir')}`",
        f"- Live execution: `{int(live_executed)}`",
        f"- Requested mode: `{preflight.get('requested_mode', '-')}` selected_mode=`{result.get('selected_mode', '-')}`",
        "",
        "## Dry-Run Preflight",
        "",
        f"- Preflight ok: `{int(bool(result.get('preflight_ok') if 'preflight_ok' in result else (preflight_ok(preflight) if preflight else False)))}`",
        f"- Candidate SHA256 ok: `{int(bool((preflight.get('candidate') or {}).get('sha256_ok')))}`",
        f"- Rollback v2321 SHA256 ok: `{int(bool((preflight.get('rollback') or {}).get('sha256_ok')))}`",
        f"- Fallback v2237 SHA256 ok: `{int(bool((preflight.get('fallback_v2237') or {}).get('sha256_ok')))}`",
        f"- Fallback v48 exists: `{int(bool((preflight.get('fallback_v48') or {}).get('exists')))}`",
        f"- Flash helper exists: `{int(bool((preflight.get('flash_helper') or {}).get('exists')))}`",
        f"- Operator prerequisite: `{preflight.get('operator_prerequisite', '-')}`",
        "",
        "## Evidence",
        "",
        f"- Candidate version ok: `{live_bool(result.get('candidate_version_ok'))}`",
        f"- Candidate selftest fail=0: `{live_bool(result.get('candidate_selftest_fail0'))}`",
        f"- Inputscan rc: `{live_value(result.get('inputscan_rc'))}` keyboard_candidates=`{live_value(inputscan.get('keyboard_candidates'))}` touch_candidates=`{live_value(inputscan.get('touch_candidates'))}`",
        f"- Selected event: `{selected.get('event', '-')}` name=`{selected.get('name', '-')}` class=`{selected.get('class', '-')}`",
        f"- Inputcaps rc: `{live_value(caps.get('rc'))}` caps_ok=`{live_bool(result.get('inputcaps_mode_ok'))}`",
        f"- `doominput` rc: `{live_value(result.get('doominput_rc'))}` timeout_ms=`{live_value(sample.get('timeout_ms'))}`",
        f"- DOOM input events: `{live_value(parsed_sample.get('doominput_event_count'))}` states=`{live_value(parsed_sample.get('doominput_state_count'))}` touch_states=`{live_value(parsed_sample.get('touch_state_count'))}` active_states=`{live_value(parsed_sample.get('active_state_count'))}` doom_button_states=`{live_value(parsed_sample.get('doom_button_state_count'))}` max_frame=`{live_value(parsed_sample.get('max_frame'))}`",
        f"- Candidate post-sample selftest fail=0: `{live_bool(result.get('candidate_selftest_after_doominput_fail0'))}`",
        "",
        "## Input Candidates",
        "",
        *candidate_lines,
        "",
        "## Captured DOOM Input State",
        "",
        *state_lines,
        "",
        "## Rollback Evidence",
        "",
        f"- Rollback attempted: `{int(bool(result.get('rollback_attempted')))}`",
        f"- Rollback step ok: `{int(bool(result.get('rollback_step_ok')))}`",
        f"- Rollback health: version_ok=`{int(bool(result.get('rollback_version_ok')))}` selftest_fail0=`{int(bool(result.get('rollback_selftest_fail0')))}`",
        "",
        "## Interpretation",
        "",
        "- V2990 stages the live handoff for the V2989 `doominput` state candidate, covering both proven MT-capable touch nodes and the USB-keyboard fallback.",
        "- Pass requires `doominput.state` evidence: touch mode needs contact or x/y state; keyboard mode needs at least one active DOOM button state.",
        "- This dry run intentionally does not flash because meaningful validation still needs operator finger motion or an attached USB keyboard during the bounded `doominput` window.",
        "",
        "## Safety",
        "",
        "- Live mode flashes only the boot partition through `native_init_flash.py`; rollback target remains `v2321`.",
        "- The validation path only reads `/sys/class/input` capability files and `/dev/input/event*` events.",
        "- No input injection, `EVIOCGRAB`, keymap change, sysfs write, Wi-Fi, audio route/playback, video playback, PMIC, backlight, GPIO, regulator, GDSC, or forbidden partition path is touched.",
        "- Raw command output stays private under `workspace/private/runs/`; this report includes metadata only.",
    ]) + "\n"


def run_live(args: argparse.Namespace, out_dir: Path, state: dict[str, Any]) -> dict[str, Any]:
    steps: list[dict[str, Any]] = []
    candidate_flash_attempted = False
    candidate_flash_ok = False
    result: dict[str, Any] = {
        "decision": f"{DECISION_PREFIX}-live-started",
        "pass": False,
        "live_executed": True,
        "out_dir": rel(out_dir),
        "preflight": state,
        "steps": steps,
        "rollback_attempted": False,
        "rollback_version_ok": False,
        "rollback_selftest_fail0": False,
    }
    try:
        base.run_step(
            out_dir,
            steps,
            "verify-current-v2321",
            flash_command(ROLLBACK_IMAGE, ROLLBACK_VERSION, ROLLBACK_SHA256, from_native=False) + ["--verify-only"],
            timeout=args.flash_timeout,
        )
        candidate_flash_attempted = True
        flash = base.run_step(
            out_dir,
            steps,
            f"flash-{CANDIDATE_TAG}",
            flash_command(CANDIDATE_IMAGE, CANDIDATE_VERSION, CANDIDATE_SHA256, from_native=True),
            timeout=args.flash_timeout,
        )
        candidate_flash_ok = flash.get("rc") == 0
        version = base.run_serial_step(out_dir, steps, "candidate-version", ["version"], timeout=90.0, retry_unsafe=True)
        selftest = base.run_serial_step(out_dir, steps, "candidate-selftest", ["selftest", "verbose"], timeout=120.0, retry_unsafe=True)
        result.update({
            "candidate_version_ok": f"A90 Linux init {CANDIDATE_VERSION} ({CANDIDATE_TAG})" in stdout_of(version),
            "candidate_selftest_fail0": selftest_step_ok(selftest),
        })
        base.run_serial_step(out_dir, steps, "candidate-hide-before-inputscan", ["hide"], timeout=60.0, retry_unsafe=True)
        inputscan_step = base.run_serial_step(out_dir, steps, "candidate-inputscan-full", ["inputscan"], timeout=120.0, retry_unsafe=True)
        parsed_scan = inputscan_live.parse_inputscan(stdout_of(inputscan_step))
        selected_mode, selected = choose_event(parsed_scan, args.event, args.mode)
        result.update({
            "selected_mode": selected_mode,
            "inputscan_rc": inputscan_step.get("rc"),
            "inputscan": parsed_scan,
            "selected_event": selected,
        })
        if not selected or selected_mode not in ("touch", "keyboard") or selected_mode not in class_tokens(selected):
            result["decision"] = f"{DECISION_PREFIX}-no-{selected_mode}-candidate"
            raise RuntimeError(f"no {selected_mode}-class input event found")
        event_name = str(selected["event"])
        base.run_serial_step(out_dir, steps, f"candidate-hide-before-inputcaps-{event_name}", ["hide"], timeout=60.0, retry_unsafe=True)
        caps_step = base.run_serial_step(out_dir, steps, f"candidate-inputcaps-{event_name}", ["inputcaps", event_name], timeout=120.0, retry_unsafe=True)
        parsed_caps = caps_live.parse_inputcaps(stdout_of(caps_step))
        result["inputcaps"] = {
            "event": event_name,
            "rc": caps_step.get("rc"),
            "stdout_path": caps_step.get("stdout_path"),
            "parsed": parsed_caps,
        }
        result["inputcaps_mode_ok"] = mode_caps_ok(selected_mode, parsed_caps)
        if not result["inputcaps_mode_ok"]:
            result["decision"] = f"{DECISION_PREFIX}-{selected_mode}-caps-not-ready"
            raise RuntimeError(f"{selected_mode} candidate lacks required capability bits")
        base.run_serial_step(out_dir, steps, "candidate-hide-before-doominput", ["hide"], timeout=60.0, retry_unsafe=True)
        sample = run_timeout_doominput(
            args.host,
            args.port,
            event_name,
            args.count,
            timeout_ms=args.timeout_ms,
        )
        readinput_live.write_manual_step(out_dir, steps, f"candidate-doominput-{selected_mode}-state-sample", sample)
        result.update({
            "doominput": {key: value for key, value in sample.items() if key != "text"},
            "doominput_rc": sample.get("protocol", {}).get("rc"),
        })
        after = base.run_serial_step(out_dir, steps, "candidate-selftest-after-doominput", ["selftest", "verbose"], timeout=120.0, retry_unsafe=True)
        result["candidate_selftest_after_doominput_fail0"] = selftest_step_ok(after)
        result["pass"] = evaluate_result(result)
        result["decision"] = f"{DECISION_PREFIX}-{selected_mode}-state-pass-before-rollback" if result["pass"] else f"{DECISION_PREFIX}-{selected_mode}-state-not-proven"
        if not result["pass"]:
            raise RuntimeError(f"doominput {selected_mode} sample did not produce required state evidence")
    except Exception as exc:  # noqa: BLE001 - write report and rollback
        if result["decision"] == f"{DECISION_PREFIX}-live-started":
            result["decision"] = f"{DECISION_PREFIX}-live-blocked"
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)
    finally:
        if candidate_flash_attempted:
            result["rollback_attempted"] = True
            rollback = base.rollback_v2321(out_dir, steps, from_native=candidate_flash_ok, timeout=args.flash_timeout)
            result["rollback_step_ok"] = bool(rollback.get("success"))
            result["rollback_attempts"] = rollback.get("attempts", [])
            result["rollback_recovery_fallback_used"] = bool(rollback.get("used_recovery_fallback"))
            if rollback.get("success"):
                rollback_version = base.run_serial_step(out_dir, steps, "rollback-version", ["version"], timeout=90.0, retry_unsafe=True, allow_error=True)
                rollback_selftest = base.run_serial_step(out_dir, steps, "rollback-selftest", ["selftest", "verbose"], timeout=120.0, retry_unsafe=True, allow_error=True)
                result["rollback_version_ok"] = ROLLBACK_VERSION in stdout_of(rollback_version)
                result["rollback_selftest_fail0"] = selftest_step_ok(rollback_selftest)
        result["result_json"] = rel(out_dir / "result.json")
        write_json(out_dir / "result.json", result)
        REPORT_PATH.write_text(render_report(result), encoding="utf-8")
    return result


def dry_run_payload(args: argparse.Namespace, state: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": f"{DECISION_PREFIX}-dry-run" if preflight_ok(state) else f"{DECISION_PREFIX}-preflight-failed",
        "ok": preflight_ok(state),
        "preflight": state,
        "commands": [
            f"verify rollback image {ROLLBACK_IMAGE}",
            f"flash {CANDIDATE_IMAGE}",
            "version/selftest",
            "hide; inputscan",
            "mode auto: select first keyboard candidate, otherwise prefer touch event6/event8",
            "inputcaps <event> and require mode-specific capability bits",
            f"doominput <event> {args.count} {args.timeout_ms} with native timeout while operator provides real input",
            "require doominput.state active/touch/DOOM button state lines",
            "selftest verbose after doominput",
            "rollback v2321 and verify selftest fail=0",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="flash V2989, sample doominput state, then rollback to V2321")
    parser.add_argument("--mode", choices=VALID_MODES, default="auto")
    parser.add_argument("--event", default=None, help="optional eventX override; otherwise selected from inputscan for the chosen mode")
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT)
    parser.add_argument("--timeout-ms", type=int, default=DEFAULT_TIMEOUT_MS)
    parser.add_argument("--flash-timeout", type=float, default=900.0)
    parser.add_argument("--host", default=a90ctl.DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=a90ctl.DEFAULT_PORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = ROOT / f"workspace/private/runs/input/{BUILD_TAG}-{now_slug()}"
    out_dir.mkdir(parents=True, exist_ok=True)
    state = preflight_state(args)
    if not args.live:
        payload = dry_run_payload(args, state)
        write_json(out_dir / "dry_run.json", payload)
        report_payload = {
            "decision": payload["decision"],
            "pass": False,
            "live_executed": False,
            "out_dir": rel(out_dir),
            "preflight": state,
            "preflight_ok": payload["ok"],
            "rollback_attempted": False,
        }
        REPORT_PATH.write_text(render_report(report_payload), encoding="utf-8")
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if payload["ok"] else 1
    if not preflight_ok(state):
        result = {
            "decision": f"{DECISION_PREFIX}-preflight-failed",
            "pass": False,
            "live_executed": False,
            "out_dir": rel(out_dir),
            "preflight": state,
            "preflight_ok": False,
            "rollback_attempted": False,
        }
        write_json(out_dir / "result.json", result)
        REPORT_PATH.write_text(render_report(result), encoding="utf-8")
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1
    result = run_live(args, out_dir, state)
    print(json.dumps({
        "decision": result.get("decision"),
        "pass": result.get("pass"),
        "selected_mode": result.get("selected_mode"),
        "selected_event": (result.get("selected_event") or {}).get("event") if isinstance(result.get("selected_event"), dict) else None,
        "rollback_version_ok": result.get("rollback_version_ok"),
        "rollback_selftest_fail0": result.get("rollback_selftest_fail0"),
        "result_json": result.get("result_json"),
    }, indent=2, sort_keys=True))
    return 0 if result.get("pass") and result.get("rollback_version_ok") and result.get("rollback_selftest_fail0") else 1


if __name__ == "__main__":
    raise SystemExit(main())
