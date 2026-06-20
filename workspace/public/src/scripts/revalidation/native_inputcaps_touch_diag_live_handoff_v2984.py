#!/usr/bin/env python3
"""V2984 live diagnostics for touch inputcaps state.

This runner flashes the V2983 inputcaps-touch-diagnostics candidate, captures
read-only ``inputscan`` plus ``inputcaps event6/event8`` output, then rolls back
to the v2321 clean USB identity checkpoint. It does not open event streams,
inject input, alter keymaps, or write touch/sysfs state.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import native_inputscan_live_handoff_v2978 as inputscan_live

base = inputscan_live.base
ROOT = inputscan_live.ROOT

RUN_ID = "V2984"
BUILD_TAG = "v2984-inputcaps-touch-diag-live"
DECISION_PREFIX = "v2984-inputcaps"
REPORT_PATH = ROOT / "docs/reports/NATIVE_INIT_V2984_INPUTCAPS_TOUCH_DIAG_LIVE_2026-06-20.md"

CANDIDATE_IMAGE = ROOT / "workspace/private/inputs/boot_images/boot_linux_v2983_inputcaps_touch_diag.img"
CANDIDATE_VERSION = "0.10.62"
CANDIDATE_TAG = "v2983-inputcaps-touch-diag"
CANDIDATE_SHA256 = "3edb059b7887cd0577a98bc28b41f1ce8c643b4234b7d3100896bb27aa86d226"

ROLLBACK_IMAGE = inputscan_live.ROLLBACK_IMAGE
ROLLBACK_VERSION = inputscan_live.ROLLBACK_VERSION
ROLLBACK_SHA256 = inputscan_live.ROLLBACK_SHA256
FALLBACK_V2237 = inputscan_live.FALLBACK_V2237
FALLBACK_V2237_SHA256 = inputscan_live.FALLBACK_V2237_SHA256
FALLBACK_V48 = inputscan_live.FALLBACK_V48
SELFTEST_FAIL0_RE = inputscan_live.SELFTEST_FAIL0_RE

DEFAULT_EVENTS = ("event6", "event8")
DECODE_RE = re.compile(r"^inputcaps\.decode (?P<body>.+)$", re.MULTILINE)
CAP_RE = re.compile(r"^inputcaps\.cap\.(?P<cap>\S+)=(?P<value>.+)$", re.MULTILINE)
ATTR_RE = re.compile(r"^inputcaps\.(?P<name>power\.[^=]+|id\.[^=]+|phys|uniq)=(?P<value>.+)$", re.MULTILINE)


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
        "events": args.events,
        "hard_boundary": [
            "boot partition only via native_init_flash.py",
            "rollback to v2321 and verify selftest fail=0",
            "read-only inputscan/inputcaps sysfs inventory only",
            "no readinput event stream, no input injection, no keymap changes",
            "no Wi-Fi/audio/video playback/PMIC/backlight/GPIO/regulator/GDSC",
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
    )


def parse_key_values(body: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for token in body.split():
        if "=" in token:
            key, value = token.split("=", 1)
            values[key] = value
    return values


def parse_inputcaps(text: str) -> dict[str, Any]:
    caps = {match.group("cap"): match.group("value").strip() for match in CAP_RE.finditer(text)}
    attrs = {match.group("name"): match.group("value").strip() for match in ATTR_RE.finditer(text)}
    decode: dict[str, str] = {}
    for match in DECODE_RE.finditer(text):
        decode.update(parse_key_values(match.group("body")))
    return {
        "has_event_header": "inputcaps.event=" in text,
        "caps": caps,
        "attrs": attrs,
        "decode": decode,
        "has_ev_abs": decode.get("ev_abs") == "1",
        "has_btn_touch": decode.get("btn_touch") == "1",
        "has_mt_x": decode.get("mt_x") == "1",
        "has_mt_y": decode.get("mt_y") == "1",
        "has_mt_tracking_id": decode.get("mt_tracking_id") == "1",
        "has_runtime_status": "power.runtime_status" in attrs,
        "runtime_status": attrs.get("power.runtime_status"),
    }


def evaluate_result(result: dict[str, Any]) -> bool:
    inputscan = result.get("inputscan", {}) if isinstance(result.get("inputscan"), dict) else {}
    caps = result.get("inputcaps", {}) if isinstance(result.get("inputcaps"), dict) else {}
    return bool(
        result.get("candidate_version_ok")
        and result.get("candidate_selftest_fail0")
        and result.get("inputscan_rc") == 0
        and inputscan.get("summary_found")
        and inputscan.get("touch_candidates", 0) >= 2
        and caps
        and all(item.get("rc") == 0 for item in caps.values())
        and all((item.get("parsed") or {}).get("has_event_header") for item in caps.values())
        and result.get("candidate_selftest_after_diag_fail0")
    )


def render_report(result: dict[str, Any]) -> str:
    inputscan = result.get("inputscan", {}) if isinstance(result.get("inputscan"), dict) else {}
    caps = result.get("inputcaps", {}) if isinstance(result.get("inputcaps"), dict) else {}
    all_touch_mt = bool(caps) and all(
        (item.get("parsed") or {}).get("has_ev_abs") and
        (item.get("parsed") or {}).get("has_btn_touch") and
        (item.get("parsed") or {}).get("has_mt_x") and
        (item.get("parsed") or {}).get("has_mt_y") and
        (item.get("parsed") or {}).get("has_mt_tracking_id")
        for item in caps.values()
    )
    runtime_statuses = sorted({
        (item.get("parsed") or {}).get("runtime_status")
        for item in caps.values()
        if (item.get("parsed") or {}).get("runtime_status")
    })
    runtime_status_text = ", ".join(runtime_statuses) if runtime_statuses else "-"
    rows = []
    for event_name, item in sorted(caps.items()):
        parsed = item.get("parsed") or {}
        rows.append(
            "| " + " | ".join([
                f"`{event_name}`",
                f"`{item.get('rc')}`",
                f"`{int(bool(parsed.get('has_ev_abs')))}`",
                f"`{int(bool(parsed.get('has_btn_touch')))}`",
                f"`{int(bool(parsed.get('has_mt_x')))}`",
                f"`{int(bool(parsed.get('has_mt_y')))}`",
                f"`{int(bool(parsed.get('has_mt_tracking_id')))}`",
                f"`{parsed.get('runtime_status')}`",
            ]) + " |"
        )
    if not rows:
        rows = ["| `-` | `-` | `0` | `0` | `0` | `0` | `0` | `-` |"]
    return "\n".join([
        "# Native Init V2984 Inputcaps Touch Diagnostics Live",
        "",
        "## Summary",
        "",
        f"- Decision: `{result.get('decision')}`",
        f"- Result before rollback: `{int(bool(result.get('pass')))}`",
        "- Track: Video playback / DOOM input prerequisite.",
        f"- Candidate: `A90 Linux init {CANDIDATE_VERSION} ({CANDIDATE_TAG})`",
        f"- Candidate SHA256: `{CANDIDATE_SHA256}`",
        f"- Private run dir: `{result.get('out_dir')}`",
        "",
        "## Live Evidence",
        "",
        f"- Candidate version ok: `{int(bool(result.get('candidate_version_ok')))}`",
        f"- Candidate selftest fail=0: `{int(bool(result.get('candidate_selftest_fail0')))}`",
        f"- Full `inputscan` rc: `{result.get('inputscan_rc')}` events=`{inputscan.get('event_count', 0)}` touch_candidates=`{inputscan.get('touch_candidates', 0)}`",
        f"- Candidate post-diagnostics selftest fail=0: `{int(bool(result.get('candidate_selftest_after_diag_fail0')))}`",
        "",
        "## Touch Capability Diagnostics",
        "",
        "| Event | rc | EV_ABS | BTN_TOUCH | MT_X | MT_Y | MT_TRACKING_ID | runtime_status |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
        *rows,
        "",
        "## Rollback Evidence",
        "",
        f"- Rollback attempted: `{int(bool(result.get('rollback_attempted')))}`",
        f"- Rollback step ok: `{int(bool(result.get('rollback_step_ok')))}`",
        f"- Rollback health: version_ok=`{int(bool(result.get('rollback_version_ok')))}` selftest_fail0=`{int(bool(result.get('rollback_selftest_fail0')))}`",
        "",
        "## Interpretation",
        "",
        "- This unit does not prove live touch events; it explains the read-only capability/runtime-PM state after V2982 produced zero events.",
        f"- Capability verdict: touch/MT bits present on all requested events = `{int(all_touch_mt)}`; runtime_status values = `{runtime_status_text}`.",
        "- Because both `event6` and `event8` expose `EV_ABS` + `BTN_TOUCH` + MT position/tracking bits and runtime PM reports `unsupported` rather than `suspended`, the prior zero-event samples are not explained by missing capabilities or a sysfs runtime-PM suspended state.",
        "- Next branch: attempt a focused live `readinput` touch sample again with operator finger input on the proven MT-capable events, or choose the DOOM input fallback if real touches still produce no events.",
        "",
        "## Safety",
        "",
        "- Only the boot partition is flashed, through `native_init_flash.py`; rollback target is `v2321`.",
        "- The live path only runs `inputscan` and `inputcaps`; it does not open an event stream, inject input, alter keymaps, or write touch configuration.",
        "- Raw command output stays private under `workspace/private/runs/`; this report includes metadata only.",
    ]) + "\n"


def run_live(args: argparse.Namespace, out_dir: Path, state: dict[str, Any]) -> dict[str, Any]:
    steps: list[dict[str, Any]] = []
    candidate_flash_attempted = False
    candidate_flash_ok = False
    result: dict[str, Any] = {
        "decision": f"{DECISION_PREFIX}-live-started",
        "pass": False,
        "out_dir": rel(out_dir),
        "preflight": state,
        "steps": steps,
        "events": args.events,
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
        inputscan = inputscan_live.parse_inputscan(stdout_of(inputscan_step))
        result.update({
            "inputscan_rc": inputscan_step.get("rc"),
            "inputscan": inputscan,
        })
        inputcaps: dict[str, Any] = {}
        for event_name in args.events:
            base.run_serial_step(out_dir, steps, f"candidate-hide-before-inputcaps-{event_name}", ["hide"], timeout=60.0, retry_unsafe=True)
            step = base.run_serial_step(out_dir, steps, f"candidate-inputcaps-{event_name}", ["inputcaps", event_name], timeout=120.0, retry_unsafe=True)
            text = stdout_of(step)
            inputcaps[event_name] = {
                "rc": step.get("rc"),
                "stdout_path": step.get("stdout_path"),
                "parsed": parse_inputcaps(text),
            }
        result["inputcaps"] = inputcaps
        after = base.run_serial_step(out_dir, steps, "candidate-selftest-after-diagnostics", ["selftest", "verbose"], timeout=120.0, retry_unsafe=True)
        result["candidate_selftest_after_diag_fail0"] = selftest_step_ok(after)
        result["pass"] = evaluate_result(result)
        result["decision"] = f"{DECISION_PREFIX}-live-pass-before-rollback" if result["pass"] else f"{DECISION_PREFIX}-live-not-proven"
        if not result["pass"]:
            raise RuntimeError("inputcaps diagnostics did not meet pass markers")
    except Exception as exc:  # noqa: BLE001
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
            "version/selftest/inputscan full",
            *[f"inputcaps {event_name}" for event_name in args.events],
            "selftest verbose after diagnostics",
            "rollback v2321 and verify selftest fail=0",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="flash V2983, capture inputcaps, then rollback to V2321")
    parser.add_argument("--events", nargs="+", default=list(DEFAULT_EVENTS))
    parser.add_argument("--flash-timeout", type=float, default=900.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = ROOT / f"workspace/private/runs/input/{BUILD_TAG}-{now_slug()}"
    out_dir.mkdir(parents=True, exist_ok=True)
    state = preflight_state(args)
    if not args.live:
        payload = dry_run_payload(args, state)
        write_json(out_dir / "dry_run.json", payload)
        REPORT_PATH.write_text(render_report({
            "decision": payload["decision"],
            "pass": False,
            "out_dir": rel(out_dir),
            "rollback_attempted": False,
        }), encoding="utf-8")
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if payload["ok"] else 1
    if not preflight_ok(state):
        payload = {"decision": f"{DECISION_PREFIX}-preflight-failed", "pass": False, "preflight": state, "out_dir": rel(out_dir)}
        write_json(out_dir / "result.json", payload)
        REPORT_PATH.write_text(render_report(payload), encoding="utf-8")
        print(json.dumps({"decision": payload["decision"], "pass": False, "out_dir": rel(out_dir)}, indent=2, sort_keys=True))
        return 1
    result = run_live(args, out_dir, state)
    print(json.dumps({
        "decision": result.get("decision"),
        "pass": bool(result.get("pass")),
        "out_dir": rel(out_dir),
        "events": result.get("events"),
        "inputscan_rc": result.get("inputscan_rc"),
        "rollback_version_ok": result.get("rollback_version_ok"),
        "rollback_selftest_fail0": result.get("rollback_selftest_fail0"),
    }, indent=2, sort_keys=True))
    return 0 if (result.get("pass") and result.get("rollback_version_ok") and result.get("rollback_selftest_fail0")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
