#!/usr/bin/env python3
"""V2999 live handoff for the V2998 DOOM multi-event input mux candidate.

The V2998 source build adds ``doominputmux`` so event3 volume keys and event0
power can feed one diagnostic DOOM state machine in a single bounded sample.
Dry-run is the default; ``--live`` is required before any flash, and live mode
rolls back to v2321 after sampling.
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
import native_doominput_state_live_handoff_v2990 as state_live
import native_inputcaps_touch_diag_live_handoff_v2984 as caps_live
import native_inputscan_live_handoff_v2978 as inputscan_live
import native_readinput_timeout_live_handoff_v2982 as readinput_live

base = state_live.base
ROOT = state_live.ROOT

RUN_ID = "V2999"
BUILD_TAG = "v2999-doominput-mux-live"
DECISION_PREFIX = "v2999-doominput-mux"
REPORT_PATH = ROOT / "docs/reports/NATIVE_INIT_V2999_DOOMINPUT_MUX_LIVE_HANDOFF_DRY_RUN_2026-06-20.md"

CANDIDATE_IMAGE = ROOT / "workspace/private/inputs/boot_images/boot_linux_v2998_doominput_mux.img"
CANDIDATE_VERSION = "0.10.67"
CANDIDATE_TAG = "v2998-doominput-mux"
CANDIDATE_SHA256 = "4828fdfba65c80a5d0a2883c2a8964a82074a6863e03e95f0f8f9aa1e9e138d6"

ROLLBACK_IMAGE = state_live.ROLLBACK_IMAGE
ROLLBACK_VERSION = state_live.ROLLBACK_VERSION
ROLLBACK_SHA256 = state_live.ROLLBACK_SHA256
FALLBACK_V2237 = state_live.FALLBACK_V2237
FALLBACK_V2237_SHA256 = state_live.FALLBACK_V2237_SHA256
FALLBACK_V48 = state_live.FALLBACK_V48

DEFAULT_EVENTS = ("event3", "event0")
DEFAULT_COUNT = 24
DEFAULT_TIMEOUT_MS = 45000
PROXY_BUTTON_FIELDS = ("forward", "back", "fire")
BUTTON_CAP_KEYS = ("key_volup", "key_voldown", "key_power")

MUX_EVENT_RE = re.compile(
    r"doominputmux\.event\s+(?P<index>\d+):\s+source=(?P<source>\S+)\s+"
    r"type=(?P<type>\S+)\s+code=(?P<code>\S+)\s+role=(?P<role>\S+)\s+"
    r"value=(?P<value>-?\d+)"
)
MUX_STATE_RE = re.compile(
    r"doominputmux\.state\s+(?P<index>\d+):\s+source=(?P<source>\S+)\s+"
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
    return state_live.rel(path)


def stdout_of(step: dict[str, Any] | None) -> str:
    return state_live.stdout_of(step)


def write_json(path: Path, payload: Any) -> None:
    state_live.write_json(path, payload)


def file_state(path: Path, expected_sha: str | None = None) -> dict[str, Any]:
    return state_live.file_state(path, expected_sha)


def selftest_step_ok(step: dict[str, Any]) -> bool:
    return state_live.selftest_step_ok(step)


def flash_command(image: Path, expect_version: str, expect_sha: str, *, from_native: bool) -> list[str]:
    return state_live.flash_command(image, expect_version, expect_sha, from_native=from_native)


def parse_events_arg(value: str) -> tuple[str, ...]:
    events = tuple(part.strip() for part in value.split(",") if part.strip())
    if not events:
        raise argparse.ArgumentTypeError("at least one event name is required")
    for event in events:
        if not event.startswith("event") or not event[5:].isdigit():
            raise argparse.ArgumentTypeError(f"invalid event name: {event}")
    if len(events) > 4:
        raise argparse.ArgumentTypeError("doominputmux supports at most four events")
    return events


def button_mux_caps_ok(parsed_caps: dict[str, Any]) -> bool:
    decoded = parsed_caps.get("decode", {}) if isinstance(parsed_caps.get("decode"), dict) else {}
    return bool(
        parsed_caps.get("has_event_header")
        and decoded.get("ev_key") == "1"
        and any(decoded.get(key) == "1" for key in BUTTON_CAP_KEYS)
    )


def parse_doominputmux(text: str) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    states: list[dict[str, Any]] = []
    for match in MUX_EVENT_RE.finditer(text):
        events.append({
            "index": int(match.group("index"), 10),
            "source": match.group("source"),
            "type": match.group("type"),
            "code": match.group("code"),
            "role": match.group("role"),
            "value": int(match.group("value"), 10),
        })
    for match in MUX_STATE_RE.finditer(text):
        states.append({
            "index": int(match.group("index"), 10),
            "source": match.group("source"),
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
    active_states = [item for item in states if item.get("active") == 1]
    proxy_states = [
        item for item in states
        if any(item.get(field) == 1 for field in PROXY_BUTTON_FIELDS)
    ]
    sources_seen = sorted({str(item.get("source")) for item in events + states if item.get("source")})
    return {
        "events": events,
        "states": states,
        "doominputmux_event_count": len(events),
        "doominputmux_state_count": len(states),
        "active_state_count": len(active_states),
        "proxy_state_count": len(proxy_states),
        "source_names": sources_seen,
        "has_active_state": bool(active_states),
        "has_proxy_state": bool(proxy_states),
        "max_frame": max((int(item["frame"]) for item in states), default=None),
    }


def proxy_state_fields(parsed_sample: dict[str, Any]) -> list[str]:
    states = parsed_sample.get("states", []) if isinstance(parsed_sample.get("states"), list) else []
    fields: set[str] = set()
    for item in states:
        if not isinstance(item, dict):
            continue
        for field in PROXY_BUTTON_FIELDS:
            if item.get(field) == 1:
                fields.add(field)
    return sorted(fields)


def has_proxy_button_state(parsed_sample: dict[str, Any]) -> bool:
    return bool(proxy_state_fields(parsed_sample))


def run_timeout_doominputmux(host: str,
                             port: int,
                             events: tuple[str, ...],
                             count: int,
                             *,
                             timeout_ms: int,
                             connect_timeout: float = 3.0,
                             command_timeout_margin: float = 8.0) -> dict[str, Any]:
    event_arg = ",".join(events)
    command = ["doominputmux", event_arg, str(count), str(timeout_ms)]
    line = a90ctl.encode_cmdv1_line(command)
    data = bytearray()
    started = time.monotonic()
    command_timeout = (timeout_ms / 1000.0) + command_timeout_margin + connect_timeout
    with SerialBridgeLock(timeout_sec=command_timeout, purpose="v2999-doominputmux"):
        with socket.create_connection((host, port), timeout=connect_timeout) as sock:
            sock.settimeout(0.25)
            sock.sendall(("\n" + line + "\n").encode("utf-8"))
            deadline = started + command_timeout
            while True:
                if b"A90P1 END " in data and state_live.has_prompt_after_last_end(data):
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
        "parsed": parse_doominputmux(text),
    }


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
        "events": list(args.events),
        "count": args.count,
        "timeout_ms": args.timeout_ms,
        "operator_prerequisite": "operator presses VOLUMEUP/VOLUMEDOWN/POWER during the single bounded doominputmux window",
        "hard_boundary": [
            "boot partition only via native_init_flash.py",
            "rollback to v2321 and verify selftest fail=0",
            "read-only inputscan/inputcaps plus read-only doominputmux evdev sample",
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
        and state.get("events")
        and len(state.get("events", [])) <= 4
        and state.get("timeout_ms", 0) > 0
        and state.get("count", 0) > 0
    )


def mux_sample_pass(result: dict[str, Any]) -> bool:
    sample = result.get("doominputmux", {}) if isinstance(result.get("doominputmux"), dict) else {}
    parsed = sample.get("parsed", {}) if isinstance(sample.get("parsed"), dict) else {}
    events = result.get("event_results", []) if isinstance(result.get("event_results"), list) else []
    return bool(
        result.get("candidate_version_ok")
        and result.get("candidate_selftest_fail0")
        and result.get("inputscan_rc") == 0
        and events
        and all(item.get("selected_is_button") and item.get("inputcaps_button_ok") for item in events)
        and result.get("doominputmux_rc") == 0
        and has_proxy_button_state(parsed)
        and result.get("candidate_selftest_after_doominputmux_fail0")
    )


def summarize_event_results(event_results: list[dict[str, Any]]) -> list[str]:
    lines = []
    for item in event_results:
        lines.append(
            f"- `{item.get('event')}` selected_buttons=`{int(bool(item.get('selected_is_button')))}` "
            f"caps_ok=`{int(bool(item.get('inputcaps_button_ok')))}` inputcaps_rc=`{item.get('inputcaps_rc')}`"
        )
    return lines or ["- none captured in this run"]


def render_report(result: dict[str, Any]) -> str:
    live_executed = bool(result.get("live_executed"))
    preflight = result.get("preflight", {}) if isinstance(result.get("preflight"), dict) else {}
    inputscan = result.get("inputscan", {}) if isinstance(result.get("inputscan"), dict) else {}
    sample = result.get("doominputmux", {}) if isinstance(result.get("doominputmux"), dict) else {}
    parsed_sample = sample.get("parsed", {}) if isinstance(sample.get("parsed"), dict) else {}
    event_results = result.get("event_results", []) if isinstance(result.get("event_results"), list) else []
    title = "Mux Live" if live_executed else "Mux Live Handoff Dry Run"
    preflight_status = result.get("preflight_ok") if "preflight_ok" in result else False
    if "preflight_ok" not in result and all(
        key in preflight for key in ("candidate", "rollback", "fallback_v2237", "fallback_v48", "flash_helper")
    ):
        preflight_status = preflight_ok(preflight)

    candidate_lines = []
    for item in inputscan.get("button_events", []) if isinstance(inputscan.get("button_events"), list) else []:
        candidate_lines.append(f"- buttons `{item.get('event')}` `{item.get('name')}` class=`{item.get('class')}`")
    if not candidate_lines:
        candidate_lines = ["- none captured in this run"]

    def live_bool(value: Any) -> str:
        return str(int(bool(value))) if live_executed else "not-run"

    def live_value(value: Any) -> str:
        return str(value) if live_executed else "not-run"

    fields = ",".join(proxy_state_fields(parsed_sample)) or "-"
    sources = ",".join(parsed_sample.get("source_names", [])) if isinstance(parsed_sample.get("source_names"), list) else "-"
    return "\n".join([
        f"# Native Init V2999 DOOM Input {title}",
        "",
        "## Summary",
        "",
        f"- Decision: `{result.get('decision')}`",
        f"- Result before rollback: `{int(bool(result.get('pass')))}`",
        "- Track: active Video playback / DOOM input prerequisite.",
        f"- Candidate: `A90 Linux init {CANDIDATE_VERSION} ({CANDIDATE_TAG})`",
        f"- Candidate image: `{rel(CANDIDATE_IMAGE)}`",
        f"- Candidate SHA256: `{CANDIDATE_SHA256}`",
        f"- Events: `{','.join(str(item) for item in preflight.get('events', []))}`",
        f"- Private run dir: `{result.get('out_dir')}`",
        f"- Live execution: `{int(live_executed)}`",
        "",
        "## Preflight",
        "",
        f"- Preflight ok: `{int(bool(preflight_status))}`",
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
        f"- Inputscan rc: `{live_value(result.get('inputscan_rc'))}` button_candidates=`{live_value(inputscan.get('button_candidates'))}`",
        f"- `doominputmux` rc: `{live_value(result.get('doominputmux_rc'))}` timeout_ms=`{live_value(sample.get('timeout_ms'))}`",
        f"- Mux events: `{live_value(parsed_sample.get('doominputmux_event_count'))}` states=`{live_value(parsed_sample.get('doominputmux_state_count'))}` active_states=`{live_value(parsed_sample.get('active_state_count'))}` proxy_states=`{live_value(parsed_sample.get('proxy_state_count'))}` max_frame=`{live_value(parsed_sample.get('max_frame'))}` sources=`{sources}` proxy_fields=`{fields}`",
        f"- Candidate post-sample selftest fail=0: `{live_bool(result.get('candidate_selftest_after_doominputmux_fail0'))}`",
        "",
        "## Button Candidates",
        "",
        *candidate_lines,
        "",
        "## Requested Event Checks",
        "",
        *summarize_event_results(event_results),
        "",
        "## Rollback Evidence",
        "",
        f"- Rollback attempted: `{int(bool(result.get('rollback_attempted')))}`",
        f"- Rollback step ok: `{int(bool(result.get('rollback_step_ok')))}`",
        f"- Rollback health: version_ok=`{int(bool(result.get('rollback_version_ok')))}` selftest_fail0=`{int(bool(result.get('rollback_selftest_fail0')))}`",
        "",
        "## Interpretation",
        "",
        "- V2999 stages live validation for the V2998 diagnostic multi-event DOOM input mux candidate.",
        "- Pass requires selected `buttons` events, POWER/VOLUME capability bits, and `doominputmux.state` evidence for `forward`, `back`, or `fire` while candidate health remains clean.",
        "- Dry-run mode does not flash; live mode should run only when an operator can press A90 physical buttons during the bounded mux sample window.",
        "- This is diagnostic evdev-to-`doominput.state` liveness proof, not a final DOOM control scheme.",
        "",
        "## Safety",
        "",
        "- Live mode flashes only the boot partition through `native_init_flash.py`; rollback target remains `v2321`.",
        "- The validation path only reads `/sys/class/input` capability files and `/dev/input/event*` events.",
        "- No input injection, `EVIOCGRAB`, keymap change, sysfs write, Wi-Fi, audio route/playback, video playback, PMIC, backlight, GPIO, regulator, GDSC, or forbidden partition path is touched.",
        "- Raw command output stays private under `workspace/private/runs/`; this report includes metadata only.",
        "",
        "## Host Validation",
        "",
        "- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_doominput_mux_live_handoff_v2999.py tests/test_native_doominput_mux_live_handoff_v2999.py`: PASS",
        "- `PYTHONPATH=workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 -m unittest tests.test_native_doominput_mux_live_handoff_v2999`: PASS",
        "- `PYTHONPATH=workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 workspace/public/src/scripts/revalidation/native_doominput_mux_live_handoff_v2999.py --count 24 --timeout-ms 45000`: PASS (dry-run preflight/report)",
        "- `git diff --check`: PASS",
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
        "event_results": [],
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
        result.update({"inputscan_rc": inputscan_step.get("rc"), "inputscan": parsed_scan})
        events_by_name = {
            str(item.get("event")): item
            for item in parsed_scan.get("events", [])
            if isinstance(item, dict) and item.get("event")
        }
        for event_name in args.events:
            selected = events_by_name.get(event_name, {})
            event_result: dict[str, Any] = {
                "event": event_name,
                "selected_event": selected,
                "selected_is_button": "buttons" in state_live.class_tokens(selected),
                "inputcaps_rc": None,
                "inputcaps_button_ok": False,
            }
            result["event_results"].append(event_result)
            if not event_result["selected_is_button"]:
                event_result["decision"] = "not-button-candidate"
                continue
            base.run_serial_step(out_dir, steps, f"candidate-hide-before-inputcaps-{event_name}", ["hide"], timeout=60.0, retry_unsafe=True)
            caps_step = base.run_serial_step(out_dir, steps, f"candidate-inputcaps-{event_name}", ["inputcaps", event_name], timeout=120.0, retry_unsafe=True)
            parsed_caps = caps_live.parse_inputcaps(stdout_of(caps_step))
            event_result.update({
                "inputcaps_rc": caps_step.get("rc"),
                "inputcaps_stdout_path": caps_step.get("stdout_path"),
                "inputcaps_button_ok": button_mux_caps_ok(parsed_caps),
            })
        if not result["event_results"] or not all(
            item.get("selected_is_button") and item.get("inputcaps_button_ok")
            for item in result["event_results"]
        ):
            result["decision"] = f"{DECISION_PREFIX}-button-candidates-not-ready"
            raise RuntimeError("requested mux events are not all button-capable")
        base.run_serial_step(out_dir, steps, "candidate-hide-before-doominputmux", ["hide"], timeout=60.0, retry_unsafe=True)
        sample = run_timeout_doominputmux(
            args.host,
            args.port,
            args.events,
            args.count,
            timeout_ms=args.timeout_ms,
        )
        readinput_live.write_manual_step(out_dir, steps, "candidate-doominputmux-button-proxy-sample", sample)
        result.update({
            "doominputmux": {key: value for key, value in sample.items() if key != "text"},
            "doominputmux_rc": sample.get("protocol", {}).get("rc"),
        })
        after = base.run_serial_step(out_dir, steps, "candidate-selftest-after-doominputmux", ["selftest", "verbose"], timeout=120.0, retry_unsafe=True)
        result["candidate_selftest_after_doominputmux_fail0"] = selftest_step_ok(after)
        result["pass"] = mux_sample_pass(result)
        result["decision"] = f"{DECISION_PREFIX}-state-pass-before-rollback" if result["pass"] else f"{DECISION_PREFIX}-state-not-proven"
        if not result["pass"]:
            raise RuntimeError("doominputmux sample did not produce required proxy state evidence")
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
            "inputcaps for each requested button event",
            f"doominputmux {','.join(args.events)} {args.count} {args.timeout_ms}",
            "operator presses VOLUMEUP/VOLUMEDOWN/POWER during the single bounded mux window",
            "require doominputmux.state forward/back/fire proxy state lines",
            "selftest verbose after doominputmux sample",
            "rollback v2321 and verify selftest fail=0",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="flash V2998, sample physical-button doominputmux state, then rollback")
    parser.add_argument("--events", type=parse_events_arg, default=DEFAULT_EVENTS, help="comma-separated button events, default event3,event0")
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT)
    parser.add_argument("--timeout-ms", type=int, default=DEFAULT_TIMEOUT_MS)
    parser.add_argument("--flash-timeout", type=float, default=900.0)
    parser.add_argument("--host", default=state_live.a90ctl.DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=state_live.a90ctl.DEFAULT_PORT)
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
            "event_results": [],
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
            "event_results": [],
        }
        write_json(out_dir / "result.json", result)
        REPORT_PATH.write_text(render_report(result), encoding="utf-8")
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1
    result = run_live(args, out_dir, state)
    sample = result.get("doominputmux", {}) if isinstance(result.get("doominputmux"), dict) else {}
    parsed = sample.get("parsed", {}) if isinstance(sample.get("parsed"), dict) else {}
    print(json.dumps({
        "decision": result.get("decision"),
        "pass": result.get("pass"),
        "proxy_fields": proxy_state_fields(parsed),
        "source_names": parsed.get("source_names", []),
        "rollback_version_ok": result.get("rollback_version_ok"),
        "rollback_selftest_fail0": result.get("rollback_selftest_fail0"),
        "result_json": result.get("result_json"),
    }, indent=2, sort_keys=True))
    return 0 if result.get("pass") and result.get("rollback_version_ok") and result.get("rollback_selftest_fail0") else 1


if __name__ == "__main__":
    raise SystemExit(main())
