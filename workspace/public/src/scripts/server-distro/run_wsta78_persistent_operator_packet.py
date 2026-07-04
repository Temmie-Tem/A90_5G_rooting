#!/usr/bin/env python3
"""WSTA78 host-only persistent operator packet.

WSTA77 summarizes current launch briefs.  WSTA78 is a final default-off packet
renderer for the operator: it consumes a private WSTA77 summary, reruns WSTA77
against the original scan root, selects a fresh READY brief, loads the fresh
WSTA76 recheck brief, and writes a compact packet with the WSTA58 command
template, required acknowledgements, abort conditions, cleanup expectations, and
pre-live guardrails.

It never executes the WSTA58 live gate.  It performs no device action, native
reboot, Wi-Fi association, DHCP, public tunnel, public smoke, userdata action,
switch-root, or flash.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_wsta77_persistent_launch_brief_summary as wsta77  # noqa: E402


REPO_ROOT = wsta77.REPO_ROOT
PRIVATE_ROOT = wsta77.PRIVATE_ROOT
DEFAULT_RUN_BASE = wsta77.DEFAULT_RUN_BASE
PASS_DECISION = "wsta78-persistent-operator-packet-pass"


def rel(path: Path) -> str:
    return wsta77.rel(path)


def utc_now() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc)


def utc_stamp(value: _dt.datetime | None = None) -> str:
    return (value or utc_now()).strftime("%Y%m%dT%H%M%SZ")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return wsta77.load_json(path)


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def is_under(path: Path, root: Path) -> bool:
    return wsta77.is_under(path, root)


def safety_flags() -> dict[str, Any]:
    return {
        "device_action": False,
        "boot_flash": False,
        "native_reboot": False,
        "wifi_connect": False,
        "dhcp": False,
        "public_tunnel": False,
        "public_smoke": False,
        "userdata_touch": False,
        "switch_root": False,
        "native_confirm_token_value_logged": False,
        "public_confirm_token_value_logged": False,
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def template() -> dict[str, Any]:
    return {
        "scope": "WSTA78 host-only persistent operator packet",
        "default_mode": "host-only-revalidate-and-render-operator-packet",
        "input": "workspace/private/runs/server-distro/<wsta77-run>/wsta77_launch_brief_summary.json",
        "command": [
            "python3",
            rel(Path(__file__).resolve()),
            "--wsta77-launch-summary-json",
            "workspace/private/runs/server-distro/<wsta77-run>/wsta77_launch_brief_summary.json",
            "--ready-index",
            "0",
        ],
        "live_execution": "not-run-by-wsta78",
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def public_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": result.get("decision"),
        "run_dir": result.get("run_dir"),
        "gate_decision": result.get("gate_decision"),
        "operator_packet": result.get("operator_packet", {}),
        "checks": result.get("checks", {}),
        "safety": result.get("safety", {}),
    }


def redaction_findings(payload: Any) -> list[str]:
    return wsta77.redaction_findings(payload)


def require_private_path(value: Any, label: str) -> tuple[Path | None, str | None]:
    if isinstance(value, Path):
        candidate = value
    elif isinstance(value, str) and value:
        candidate = Path(value)
    else:
        return None, f"wsta78-blocked-{label}-missing"
    path = resolve_path(candidate)
    if not is_under(path, PRIVATE_ROOT):
        return None, f"wsta78-blocked-{label}-nonprivate"
    if not path.exists():
        return None, f"wsta78-blocked-{label}-missing"
    return path, None


def validate_summary(path: Path) -> tuple[bool, str, dict[str, Any]]:
    try:
        payload = load_json(path)
    except Exception as exc:  # noqa: BLE001
        return False, "wsta78-blocked-summary-unreadable", {"error": str(exc)}
    if payload.get("decision") != wsta77.PASS_DECISION:
        return False, "wsta78-blocked-summary-not-pass", {"decision": payload.get("decision")}
    summary = payload.get("launch_summary")
    if not isinstance(summary, dict):
        return False, "wsta78-blocked-summary-missing", {}
    if summary.get("default_public_off") is not True:
        return False, "wsta78-blocked-default-public-off-missing", {}
    if summary.get("live_execution_requested") is not False:
        return False, "wsta78-blocked-live-execution-requested", {}
    if summary.get("public_url_value_logged") is not False:
        return False, "wsta78-blocked-public-url-logged", {}
    if summary.get("secret_values_logged") not in (0, "0", None):
        return False, "wsta78-blocked-secret-values-logged", {}
    scan_root, path_error = require_private_path(summary.get("scan_root"), "scan-root")
    if path_error or scan_root is None:
        return False, path_error or "wsta78-blocked-scan-root", {}
    return True, "ok", {"payload": payload, "summary": summary, "scan_root": scan_root}


def wsta77_args(run_dir: Path,
                scan_root: Path,
                max_briefs: int,
                max_packets: int,
                ready_index: int,
                min_remaining: int | None,
                now_utc: str | None) -> argparse.Namespace:
    argv = [
        "--run-dir",
        str(run_dir),
        "--scan-root",
        str(scan_root),
        "--max-briefs",
        str(max_briefs),
        "--max-packets",
        str(max_packets),
        "--ready-index",
        str(ready_index),
    ]
    if min_remaining is not None:
        argv.extend(["--min-initial-seconds-remaining", str(min_remaining)])
    if now_utc:
        argv.extend(["--now-utc", now_utc])
    return wsta77.build_arg_parser().parse_args(argv)


def ready_entries(entries: list[Any]) -> list[dict[str, Any]]:
    ready: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if entry.get("state") == "READY_TO_EXECUTE_DEFAULT_OFF" and entry.get("ready_for_live") is True:
            ready.append(entry)
    return sorted(ready, key=wsta77.ready_sort_key, reverse=True)


def load_fresh_brief(entry: dict[str, Any]) -> tuple[dict[str, Any], Path]:
    brief_path, path_error = require_private_path(entry.get("wsta76_recheck_result"), "wsta76-recheck")
    if path_error or brief_path is None:
        raise ValueError(path_error or "wsta78-blocked-wsta76-recheck")
    payload = load_json(brief_path)
    if payload.get("decision") != wsta77.wsta76.PASS_DECISION:
        raise ValueError("wsta78-blocked-wsta76-recheck-not-pass")
    brief = payload.get("launch_brief")
    if not isinstance(brief, dict):
        raise ValueError("wsta78-blocked-launch-brief-missing")
    if brief.get("state") != "READY_TO_EXECUTE_DEFAULT_OFF" or brief.get("ready_for_live") is not True:
        raise ValueError("wsta78-blocked-launch-brief-not-ready")
    if brief.get("live_execution_requested") is not False:
        raise ValueError("wsta78-blocked-live-execution-requested")
    return brief, brief_path


def build_operator_packet(source_summary: Path,
                          recheck_summary: Path,
                          selected_index: int,
                          ready_count: int,
                          summary_entry: dict[str, Any],
                          brief: dict[str, Any],
                          brief_path: Path,
                          out_json: Path,
                          out_md: Path) -> dict[str, Any]:
    return {
        "state": "READY_OPERATOR_PACKET_DEFAULT_OFF",
        "source_wsta77_summary": rel(source_summary),
        "fresh_wsta77_summary": rel(recheck_summary),
        "selected_ready_index": selected_index,
        "ready_brief_count": ready_count,
        "selected_wsta76_launch_brief": summary_entry.get("wsta76_launch_brief"),
        "fresh_wsta76_launch_brief": rel(brief_path),
        "selected_wsta73_arming_packet": brief.get("selected_wsta73_arming_packet"),
        "initial_seconds_remaining": brief.get("initial_seconds_remaining"),
        "wsta65_session_state": brief.get("wsta65_session_state"),
        "ready_for_live": True,
        "wsta58_live_command_template": brief.get("wsta58_live_command_template"),
        "operator_required_replacements": brief.get("operator_required_replacements") or [
            "<native-confirm-token>",
            "<public-confirm-token>",
        ],
        "operator_acknowledgements_required": brief.get("operator_acknowledgements_required") or [],
        "abort_conditions": brief.get("abort_conditions") or [],
        "cleanup_expectations": brief.get("cleanup_expectations") or [],
        "operator_preflight_checks": brief.get("operator_preflight_checks") or [],
        "execution_guardrails": [
            "wsta78-does-not-execute-live",
            "rerun-wsta78-if-time-elapsed-before-live",
            "replace-placeholders-out-of-band-only",
            "run-wsta58-only-with-explicit-operator-intent",
            "verify-public-off-after-wsta58",
        ],
        "recommended_next_action": "operator-may-copy-wsta58-template-after-token-replacement",
        "json_path": rel(out_json),
        "markdown_path": rel(out_md),
        "default_public_off": True,
        "live_execution_requested": False,
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def markdown(packet: dict[str, Any]) -> str:
    command = " ".join(str(part) for part in packet.get("wsta58_live_command_template") or [])
    lines = [
        "# WSTA Persistent Operator Packet",
        "",
        f"- State: `{packet.get('state')}`",
        f"- Source WSTA77 summary: `{packet.get('source_wsta77_summary')}`",
        f"- Fresh WSTA77 summary: `{packet.get('fresh_wsta77_summary')}`",
        f"- Selected READY index: `{packet.get('selected_ready_index')}`",
        f"- Selected WSTA76 brief: `{packet.get('selected_wsta76_launch_brief')}`",
        f"- Fresh WSTA76 brief: `{packet.get('fresh_wsta76_launch_brief')}`",
        f"- Selected WSTA73 packet: `{packet.get('selected_wsta73_arming_packet')}`",
        f"- Initial seconds remaining: `{packet.get('initial_seconds_remaining')}`",
        "- Live execution requested: `false`",
        "- Default public state: `PUBLIC_OFF`",
        "",
        "## Operator Replacements",
        "",
    ]
    for item in packet.get("operator_required_replacements", []):
        lines.append(f"- `{item}`")
    lines.extend(["", "## Required Acknowledgements", ""])
    for item in packet.get("operator_acknowledgements_required", []):
        lines.append(f"- `{item}`")
    lines.extend(["", "## Abort Conditions", ""])
    for item in packet.get("abort_conditions", []):
        lines.append(f"- `{item}`")
    lines.extend(["", "## Cleanup Expectations", ""])
    for item in packet.get("cleanup_expectations", []):
        lines.append(f"- `{item}`")
    lines.extend(["", "## Execution Guardrails", ""])
    for item in packet.get("execution_guardrails", []):
        lines.append(f"- `{item}`")
    lines.extend([
        "",
        "## WSTA58 Command Template",
        "",
        "```text",
        command,
        "```",
        "",
        "This packet does not run the live gate. Replace placeholders only when explicitly running WSTA58.",
        "",
    ])
    return "\n".join(lines)


def run(args: argparse.Namespace) -> dict[str, Any]:
    started = utc_now()
    ts = utc_stamp(started)
    run_id = args.run_id or f"wsta78-persistent-operator-packet-{ts}"
    run_dir = args.run_dir or (DEFAULT_RUN_BASE / run_id)
    run_dir = resolve_path(run_dir)
    result: dict[str, Any] = {
        "scope": "WSTA78 host-only persistent operator packet",
        "started_utc": ts,
        "run_dir": rel(run_dir),
        "decision": "wsta78-blocked",
        "gate_decision": "not-run",
        "safety": safety_flags(),
    }
    if not is_under(run_dir, PRIVATE_ROOT):
        result["decision"] = "wsta78-blocked-nonprivate-run-dir"
        result["gate_decision"] = result["decision"]
        result["ended_utc"] = utc_stamp()
        return result
    run_dir.mkdir(parents=True, exist_ok=True)
    out_json = run_dir / "wsta78_operator_packet.json"
    out_md = run_dir / "wsta78_operator_packet.md"

    if args.wsta77_launch_summary_json is None:
        result["decision"] = "wsta78-blocked-summary-required"
        result["gate_decision"] = result["decision"]
        result["ended_utc"] = utc_stamp()
        write_json(out_json, result)
        return result
    summary_path, path_error = require_private_path(args.wsta77_launch_summary_json, "summary")
    if path_error or summary_path is None:
        result["decision"] = path_error or "wsta78-blocked-summary"
        result["gate_decision"] = result["decision"]
        result["ended_utc"] = utc_stamp()
        write_json(out_json, result)
        return result
    valid, decision, detail = validate_summary(summary_path)
    if not valid:
        result["decision"] = decision
        result["gate_decision"] = decision
        result["gate_detail"] = detail
        result["ended_utc"] = utc_stamp()
        write_json(out_json, result)
        return result

    recheck_dir = run_dir / "wsta77-recheck"
    recheck = wsta77.run(wsta77_args(
        recheck_dir,
        detail["scan_root"],
        int(args.max_briefs),
        int(args.max_packets),
        0,
        args.min_initial_seconds_remaining,
        args.now_utc,
    ))
    recheck_path = recheck_dir / "wsta77_launch_brief_summary.json"
    if recheck.get("decision") != wsta77.PASS_DECISION:
        result["decision"] = "wsta78-blocked-wsta77-recheck"
        result["gate_decision"] = result["decision"]
        result["gate_detail"] = {"wsta77_decision": recheck.get("decision"), "wsta77_recheck": rel(recheck_path)}
        result["ended_utc"] = utc_stamp()
        write_json(out_json, result)
        return result
    fresh_summary = recheck.get("launch_summary")
    if not isinstance(fresh_summary, dict):
        result["decision"] = "wsta78-blocked-wsta77-recheck-missing-summary"
        result["gate_decision"] = result["decision"]
        result["ended_utc"] = utc_stamp()
        write_json(out_json, result)
        return result
    candidates = ready_entries(fresh_summary.get("entries") or [])
    result["candidate_summary"] = {
        "ready_brief_count": len(candidates),
        "selected_ready_index": args.ready_index,
    }
    if not candidates:
        result["decision"] = "wsta78-blocked-no-ready-brief"
        result["gate_decision"] = result["decision"]
        result["gate_detail"] = {
            "overall_state": fresh_summary.get("overall_state"),
            "state_counts": fresh_summary.get("state_counts"),
            "wsta77_recheck": rel(recheck_path),
        }
        result["ended_utc"] = utc_stamp()
        write_json(out_json, result)
        return result
    if args.ready_index < 0 or args.ready_index >= len(candidates):
        result["decision"] = "wsta78-blocked-ready-index-out-of-range"
        result["gate_decision"] = result["decision"]
        result["ended_utc"] = utc_stamp()
        write_json(out_json, result)
        return result

    selected = candidates[int(args.ready_index)]
    try:
        fresh_brief, fresh_brief_path = load_fresh_brief(selected)
    except Exception as exc:  # noqa: BLE001
        result["decision"] = "wsta78-blocked-selected-brief-unusable"
        result["gate_decision"] = result["decision"]
        result["gate_detail"] = {"error": str(exc)}
        result["ended_utc"] = utc_stamp()
        write_json(out_json, result)
        return result

    packet = build_operator_packet(
        summary_path,
        recheck_path,
        int(args.ready_index),
        len(candidates),
        selected,
        fresh_brief,
        fresh_brief_path,
        out_json,
        out_md,
    )
    result.update({
        "decision": PASS_DECISION,
        "gate_decision": "ok",
        "operator_packet": packet,
        "checks": {
            "summary_private": True,
            "wsta77_rechecked": True,
            "selected_brief_ready": True,
            "default_public_off": True,
            "live_execution_requested": False,
            "public_url_value_logged": False,
            "secret_values_logged": 0,
        },
    })
    md_text = markdown(packet)
    findings = redaction_findings(public_summary(result))
    md_findings = redaction_findings({"markdown": md_text})
    if findings or md_findings:
        result["decision"] = "wsta78-blocked-redaction-finding"
        result["gate_decision"] = result["decision"]
        result["gate_detail"] = {"findings": sorted(set(findings + md_findings))}
        result["ended_utc"] = utc_stamp()
        write_json(out_json, result)
        return result

    result["ended_utc"] = utc_stamp()
    write_json(out_json, result)
    write_text(out_md, md_text)
    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--wsta77-launch-summary-json", type=Path)
    parser.add_argument("--ready-index", type=int, default=0)
    parser.add_argument("--max-briefs", type=int, default=wsta77.DEFAULT_MAX_BRIEFS)
    parser.add_argument("--max-packets", type=int, default=wsta77.wsta76.wsta75.DEFAULT_MAX_PACKETS)
    parser.add_argument("--min-initial-seconds-remaining", type=int)
    parser.add_argument("--now-utc")
    parser.add_argument("--print-template", action="store_true")
    parser.add_argument("--print-full-json", action="store_true")
    return parser


def main_with_args(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    if args.print_template:
        print(json.dumps(template(), indent=2, sort_keys=True))
        return 0
    try:
        result = run(args)
    except Exception as exc:  # noqa: BLE001
        payload = {"decision": "wsta78-runner-error", "error": str(exc)}
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1
    payload = result if args.print_full_json else public_summary(result)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.get("decision") == PASS_DECISION else 2


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
