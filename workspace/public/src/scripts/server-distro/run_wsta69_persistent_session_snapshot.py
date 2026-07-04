#!/usr/bin/env python3
"""WSTA69 host-only persistent session operator snapshot.

WSTA67 produces a machine inventory.  WSTA69 turns that inventory into a
redacted JSON + Markdown operator snapshot with counts, session rows, and
default-off next actions.  It never starts public exposure; a READY session only
means an operator may choose the explicit WSTA58 live gate separately.
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

import run_wsta67_persistent_session_inventory as wsta67  # noqa: E402


REPO_ROOT = wsta67.REPO_ROOT
PRIVATE_ROOT = wsta67.PRIVATE_ROOT
DEFAULT_RUN_BASE = wsta67.DEFAULT_RUN_BASE
PASS_DECISION = "wsta69-persistent-session-snapshot-pass"


def rel(path: Path) -> str:
    return wsta67.rel(path)


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
    return wsta67.load_json(path)


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def is_under(path: Path, root: Path) -> bool:
    return wsta67.is_under(path, root)


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
        "scope": "WSTA69 host-only persistent session operator snapshot",
        "default_mode": "host-only-report",
        "input": "workspace/private/runs/server-distro/<wsta67-run>/wsta67_inventory.json",
        "command": [
            "python3",
            rel(Path(__file__).resolve()),
            "--wsta67-inventory-json",
            "workspace/private/runs/server-distro/<wsta67-run>/wsta67_inventory.json",
        ],
        "live_execution": "not-run-by-wsta69",
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def public_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": result.get("decision"),
        "run_dir": result.get("run_dir"),
        "gate_decision": result.get("gate_decision"),
        "snapshot": result.get("snapshot", {}),
        "checks": result.get("checks", {}),
        "safety": result.get("safety", {}),
    }


def redaction_findings(payload: Any) -> list[str]:
    return wsta67.redaction_findings(payload)


def require_private_path(value: Any, label: str) -> tuple[Path | None, str | None]:
    if isinstance(value, Path):
        candidate = value
    elif isinstance(value, str) and value:
        candidate = Path(value)
    else:
        return None, f"wsta69-blocked-{label}-missing"
    path = resolve_path(candidate)
    if not is_under(path, PRIVATE_ROOT):
        return None, f"wsta69-blocked-{label}-nonprivate"
    if not path.exists():
        return None, f"wsta69-blocked-{label}-missing"
    return path, None


def validate_inventory(path: Path) -> tuple[bool, str, dict[str, Any]]:
    try:
        payload = load_json(path)
    except Exception as exc:  # noqa: BLE001
        return False, "wsta69-blocked-inventory-unreadable", {"error": str(exc)}
    if payload.get("decision") != wsta67.PASS_DECISION:
        return False, "wsta69-blocked-inventory-not-pass", {"decision": payload.get("decision")}
    inventory = payload.get("inventory")
    if not isinstance(inventory, dict):
        return False, "wsta69-blocked-inventory-missing", {}
    entries = inventory.get("entries")
    if not isinstance(entries, list):
        return False, "wsta69-blocked-inventory-entries-missing", {}
    if inventory.get("public_url_value_logged") is not False:
        return False, "wsta69-blocked-public-url-logged", {}
    if inventory.get("secret_values_logged") not in (0, "0", None):
        return False, "wsta69-blocked-secret-values-logged", {}
    return True, "ok", {"payload": payload, "inventory": inventory, "entries": entries}


def overall_state(inventory: dict[str, Any]) -> str:
    if int(inventory.get("invalid_session_count") or 0) > 0:
        return "INSPECT_REQUIRED"
    if int(inventory.get("stale_count") or 0) > 0:
        return "CLEANUP_RECOMMENDED"
    if int(inventory.get("expired_count") or 0) > 0:
        return "CLEANUP_RECOMMENDED"
    if int(inventory.get("not_ready_count") or 0) > 0:
        return "CLEANUP_RECOMMENDED"
    if int(inventory.get("ready_count") or 0) > 0:
        return "READY_PRESENT_DEFAULT_OFF"
    return "NO_LIVE_READY"


def next_actions(inventory_path: Path, inventory: dict[str, Any]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    nonliveable = (
        int(inventory.get("stale_count") or 0)
        + int(inventory.get("expired_count") or 0)
        + int(inventory.get("not_ready_count") or 0)
    )
    if nonliveable:
        actions.append({
            "action": "bulk-retire-nonliveable",
            "reason": "stale-expired-or-not-ready-sessions-present",
            "command": [
                "python3",
                rel(SCRIPT_DIR / "run_wsta68_persistent_session_bulk_retire.py"),
                "--bulk-retire",
                "--ack-bulk-retire",
                "--wsta67-inventory-json",
                rel(inventory_path),
            ],
        })
    if int(inventory.get("ready_count") or 0) > 0:
        actions.append({
            "action": "operator-may-select-explicit-live",
            "reason": "ready-sessions-exist-but-default-off-remains",
            "command": [
                "rerun",
                "WSTA65-status",
                "then",
                "operator-selected-WSTA58-live-gate",
            ],
        })
    if not actions:
        actions.append({
            "action": "no-live-ready-session",
            "reason": "prepare-a-fresh-session-if-live-is-needed",
            "command": [
                "rerun",
                "WSTA63-then-WSTA64",
            ],
        })
    return actions


def redacted_entries(entries: list[Any], limit: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for entry in entries[:limit]:
        if not isinstance(entry, dict):
            continue
        rows.append({
            "wsta64_result": entry.get("wsta64_result"),
            "session_state": entry.get("session_state"),
            "ready_for_live": bool(entry.get("ready_for_live")),
            "initial_seconds_remaining": entry.get("initial_seconds_remaining"),
            "recommended_next_action": entry.get("recommended_next_action"),
            "retire_marker_present": bool(entry.get("retire_marker")),
            "state": "PUBLIC_OFF",
            "public_url_value_logged": False,
            "secret_values_logged": 0,
        })
    return rows


def build_snapshot(inventory_path: Path,
                   inventory: dict[str, Any],
                   entries: list[Any],
                   entry_limit: int) -> dict[str, Any]:
    state = overall_state(inventory)
    rows = redacted_entries(entries, entry_limit)
    return {
        "source_inventory": rel(inventory_path),
        "overall_state": state,
        "session_count": inventory.get("session_count", 0),
        "invalid_session_count": inventory.get("invalid_session_count", 0),
        "state_counts": inventory.get("state_counts", {}),
        "ready_count": inventory.get("ready_count", 0),
        "retired_count": inventory.get("retired_count", 0),
        "stale_count": inventory.get("stale_count", 0),
        "expired_count": inventory.get("expired_count", 0),
        "not_ready_count": inventory.get("not_ready_count", 0),
        "entries_shown": len(rows),
        "entries_truncated": len(entries) > entry_limit,
        "entries": rows,
        "next_actions": next_actions(inventory_path, inventory),
        "default_public_off": True,
        "live_execution_requested": False,
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def markdown(snapshot: dict[str, Any]) -> str:
    lines = [
        "# WSTA Persistent Session Snapshot",
        "",
        f"- Overall state: `{snapshot.get('overall_state')}`",
        f"- Source inventory: `{snapshot.get('source_inventory')}`",
        f"- Sessions: `{snapshot.get('session_count')}`",
        f"- READY: `{snapshot.get('ready_count')}`",
        f"- STALE: `{snapshot.get('stale_count')}`",
        f"- EXPIRED: `{snapshot.get('expired_count')}`",
        f"- NOT_READY: `{snapshot.get('not_ready_count')}`",
        f"- RETIRED: `{snapshot.get('retired_count')}`",
        f"- Invalid: `{snapshot.get('invalid_session_count')}`",
        "- Default public state: `PUBLIC_OFF`",
        "- Live execution requested: `false`",
        "",
        "## Next Actions",
        "",
    ]
    for action in snapshot.get("next_actions", []):
        command = " ".join(action.get("command") or [])
        lines.append(f"- `{action.get('action')}`: {action.get('reason')} - `{command}`")
    lines.extend([
        "",
        "## Sessions",
        "",
        "| State | Ready | Seconds Remaining | Retired | WSTA64 Result |",
        "| --- | --- | ---: | --- | --- |",
    ])
    for entry in snapshot.get("entries", []):
        lines.append(
            "| {state} | {ready} | {seconds} | {retired} | `{path}` |".format(
                state=entry.get("session_state"),
                ready=str(bool(entry.get("ready_for_live"))).lower(),
                seconds=entry.get("initial_seconds_remaining"),
                retired=str(bool(entry.get("retire_marker_present"))).lower(),
                path=entry.get("wsta64_result"),
            )
        )
    lines.append("")
    return "\n".join(lines)


def run(args: argparse.Namespace) -> dict[str, Any]:
    started = utc_now()
    ts = utc_stamp(started)
    run_id = args.run_id or f"wsta69-persistent-session-snapshot-{ts}"
    run_dir = args.run_dir or (DEFAULT_RUN_BASE / run_id)
    run_dir = resolve_path(run_dir)
    result: dict[str, Any] = {
        "scope": "WSTA69 host-only persistent session operator snapshot",
        "started_utc": ts,
        "run_dir": rel(run_dir),
        "decision": "wsta69-blocked",
        "gate_decision": "not-run",
        "safety": safety_flags(),
    }
    if not is_under(run_dir, PRIVATE_ROOT):
        result["decision"] = "wsta69-blocked-nonprivate-run-dir"
        result["gate_decision"] = result["decision"]
        result["ended_utc"] = utc_stamp()
        return result
    run_dir.mkdir(parents=True, exist_ok=True)
    out_json = run_dir / "wsta69_snapshot.json"
    out_md = run_dir / "wsta69_snapshot.md"

    if args.wsta67_inventory_json is None:
        result["decision"] = "wsta69-blocked-inventory-required"
        result["gate_decision"] = result["decision"]
        result["ended_utc"] = utc_stamp()
        write_json(out_json, result)
        return result
    inventory_path, path_error = require_private_path(args.wsta67_inventory_json, "inventory")
    if path_error or inventory_path is None:
        result["decision"] = path_error or "wsta69-blocked-inventory"
        result["gate_decision"] = result["decision"]
        result["ended_utc"] = utc_stamp()
        write_json(out_json, result)
        return result
    valid, decision, detail = validate_inventory(inventory_path)
    if not valid:
        result["decision"] = decision
        result["gate_decision"] = decision
        result["gate_detail"] = detail
        result["ended_utc"] = utc_stamp()
        write_json(out_json, result)
        return result

    snapshot = build_snapshot(inventory_path, detail["inventory"], detail["entries"], int(args.entry_limit))
    result.update({
        "decision": PASS_DECISION,
        "gate_decision": "ok",
        "snapshot": {
            **snapshot,
            "json_path": rel(out_json),
            "markdown_path": rel(out_md),
        },
        "checks": {
            "inventory_private": True,
            "default_public_off": True,
            "live_execution_requested": False,
            "public_url_value_logged": False,
            "secret_values_logged": 0,
        },
    })
    findings = redaction_findings(public_summary(result))
    md_text = markdown(snapshot)
    md_findings = redaction_findings({"markdown": md_text})
    if findings or md_findings:
        result["decision"] = "wsta69-blocked-redaction-finding"
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
    parser.add_argument("--wsta67-inventory-json", type=Path)
    parser.add_argument("--entry-limit", type=int, default=20)
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
        payload = {"decision": "wsta69-runner-error", "error": str(exc)}
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1
    payload = result if args.print_full_json else public_summary(result)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.get("decision") == PASS_DECISION else 2


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
