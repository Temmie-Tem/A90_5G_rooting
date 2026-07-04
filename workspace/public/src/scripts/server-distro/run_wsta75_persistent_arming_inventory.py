#!/usr/bin/env python3
"""WSTA75 host-only persistent arming packet inventory.

WSTA74 answers "is this one arming packet still usable?"  WSTA75 scans a
private WSTA run tree for WSTA73 arming packets, reruns WSTA74 for each
candidate, and emits a redacted inventory of currently READY/stale/drifted
packets.

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

import run_wsta74_persistent_arming_status as wsta74  # noqa: E402


REPO_ROOT = wsta74.REPO_ROOT
PRIVATE_ROOT = wsta74.PRIVATE_ROOT
DEFAULT_RUN_BASE = wsta74.DEFAULT_RUN_BASE
PASS_DECISION = "wsta75-persistent-arming-inventory-pass"
DEFAULT_MAX_PACKETS = 50
RECHECK_DIR_NAME = "wsta73-recheck"


def rel(path: Path) -> str:
    return wsta74.rel(path)


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
    return wsta74.load_json(path)


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def is_under(path: Path, root: Path) -> bool:
    return wsta74.is_under(path, root)


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
        "scope": "WSTA75 host-only persistent arming packet inventory",
        "default_mode": "host-only-revalidate-packet-inventory",
        "command": [
            "python3",
            rel(Path(__file__).resolve()),
            "--scan-root",
            "workspace/private/runs/server-distro",
            "--max-packets",
            str(DEFAULT_MAX_PACKETS),
        ],
        "live_execution": "not-run-by-wsta75",
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def public_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": result.get("decision"),
        "run_dir": result.get("run_dir"),
        "gate_decision": result.get("gate_decision"),
        "arming_inventory": result.get("arming_inventory", {}),
        "checks": result.get("checks", {}),
        "safety": result.get("safety", {}),
    }


def redaction_findings(payload: Any) -> list[str]:
    return wsta74.redaction_findings(payload)


def newest_first(paths: list[Path]) -> list[Path]:
    return sorted(paths, key=lambda path: (path.stat().st_mtime, str(path)), reverse=True)


def is_recheck_artifact(path: Path) -> bool:
    return RECHECK_DIR_NAME in path.parts


def scan_packet_paths(root: Path, run_dir: Path, limit: int) -> tuple[list[Path], bool]:
    matches: list[Path] = []
    for path in root.rglob("wsta73_arming_packet.json"):
        if not path.is_file():
            continue
        if is_under(path, run_dir):
            continue
        if is_recheck_artifact(path):
            continue
        matches.append(path)
    matches = newest_first(matches)
    truncated = len(matches) > limit
    return matches[:limit], truncated


def wsta74_args(run_dir: Path,
                packet_path: Path,
                min_remaining: int | None,
                now_utc: str | None) -> argparse.Namespace:
    argv = [
        "--run-dir",
        str(run_dir),
        "--wsta73-arming-packet-json",
        str(packet_path),
    ]
    if min_remaining is not None:
        argv.extend(["--min-initial-seconds-remaining", str(min_remaining)])
    if now_utc:
        argv.extend(["--now-utc", now_utc])
    return wsta74.build_arg_parser().parse_args(argv)


def inventory_entry(index: int, packet_path: Path, status_result: dict[str, Any], status_path: Path) -> dict[str, Any]:
    status = status_result.get("arming_status") if isinstance(status_result.get("arming_status"), dict) else {}
    return {
        "index": index,
        "wsta73_arming_packet": rel(packet_path),
        "wsta74_status_result": rel(status_path),
        "wsta74_decision": status_result.get("decision"),
        "state": status.get("state") or "INVALID_OR_BLOCKED",
        "ready_for_live": bool(status.get("ready_for_live")),
        "wsta73_recheck_decision": status.get("wsta73_recheck_decision"),
        "wsta65_session_state": status.get("wsta65_session_state"),
        "initial_seconds_remaining": status.get("initial_seconds_remaining"),
        "template_match": bool(status.get("template_match")),
        "recommended_next_action": status.get("recommended_next_action") or "inspect-or-rerun-wsta72-then-wsta73",
        "default_public_off": True,
        "live_execution_requested": False,
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def count_states(entries: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in entries:
        state = str(entry.get("state") or "UNKNOWN")
        counts[state] = counts.get(state, 0) + 1
    return counts


def ready_sort_key(entry: dict[str, Any]) -> tuple[int, str]:
    seconds = entry.get("initial_seconds_remaining")
    if not isinstance(seconds, int):
        seconds = -1
    return int(seconds), str(entry.get("wsta73_arming_packet") or "")


def selected_ready_entry(entries: list[dict[str, Any]]) -> dict[str, Any] | None:
    ready = [entry for entry in entries if entry.get("state") == "READY_TO_EXECUTE_DEFAULT_OFF"]
    if not ready:
        return None
    return sorted(ready, key=ready_sort_key, reverse=True)[0]


def build_inventory(scan_root: Path,
                    entries: list[dict[str, Any]],
                    invalid_entries: list[dict[str, Any]],
                    truncated: bool,
                    max_packets: int) -> dict[str, Any]:
    counts = count_states(entries)
    ready_entry = selected_ready_entry(entries)
    ready_count = counts.get("READY_TO_EXECUTE_DEFAULT_OFF", 0)
    stale_count = counts.get("STALE_OR_NOT_READY", 0)
    drift_count = counts.get("DRIFT_RECHECK_REQUIRED", 0)
    blocked_count = counts.get("INVALID_OR_BLOCKED", 0)
    if ready_count:
        overall_state = "READY_PACKET_PRESENT_DEFAULT_OFF"
        next_action = "operator-may-run-explicit-wsta58-live-gate-for-selected-packet"
    elif entries:
        overall_state = "NO_READY_PACKET"
        next_action = "rerun-wsta72-then-wsta73"
    else:
        overall_state = "NO_ARMING_PACKETS_FOUND"
        next_action = "run-wsta72-then-wsta73"
    return {
        "scan_root": rel(scan_root),
        "overall_state": overall_state,
        "packet_count": len(entries),
        "invalid_packet_count": len(invalid_entries),
        "state_counts": counts,
        "ready_count": ready_count,
        "stale_count": stale_count,
        "drift_count": drift_count,
        "blocked_count": blocked_count,
        "scan_truncated": truncated,
        "max_packets": max_packets,
        "selected_ready_packet": ready_entry,
        "entries": entries,
        "invalid_entries": invalid_entries,
        "recommended_next_action": next_action,
        "default_public_off": True,
        "live_execution_requested": False,
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def markdown(inventory: dict[str, Any]) -> str:
    selected = inventory.get("selected_ready_packet") or {}
    lines = [
        "# WSTA Persistent Arming Packet Inventory",
        "",
        f"- Overall state: `{inventory.get('overall_state')}`",
        f"- Scan root: `{inventory.get('scan_root')}`",
        f"- Packets: `{inventory.get('packet_count')}`",
        f"- READY: `{inventory.get('ready_count')}`",
        f"- STALE/NOT_READY: `{inventory.get('stale_count')}`",
        f"- DRIFT: `{inventory.get('drift_count')}`",
        f"- BLOCKED: `{inventory.get('blocked_count')}`",
        f"- Invalid: `{inventory.get('invalid_packet_count')}`",
        f"- Selected ready packet: `{selected.get('wsta73_arming_packet')}`",
        f"- Recommended next action: `{inventory.get('recommended_next_action')}`",
        "- Default public state: `PUBLIC_OFF`",
        "- Live execution requested: `false`",
        "",
        "## Packets",
        "",
        "| State | Ready | Seconds Remaining | WSTA73 Recheck | Packet |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for entry in inventory.get("entries", []):
        lines.append(
            "| {state} | {ready} | {seconds} | `{recheck}` | `{path}` |".format(
                state=entry.get("state"),
                ready=str(bool(entry.get("ready_for_live"))).lower(),
                seconds=entry.get("initial_seconds_remaining"),
                recheck=entry.get("wsta73_recheck_decision"),
                path=entry.get("wsta73_arming_packet"),
            )
        )
    lines.append("")
    return "\n".join(lines)


def run(args: argparse.Namespace) -> dict[str, Any]:
    started = utc_now()
    ts = utc_stamp(started)
    run_id = args.run_id or f"wsta75-persistent-arming-inventory-{ts}"
    run_dir = args.run_dir or (DEFAULT_RUN_BASE / run_id)
    run_dir = resolve_path(run_dir)
    scan_root = resolve_path(args.scan_root)
    result: dict[str, Any] = {
        "scope": "WSTA75 host-only persistent arming packet inventory",
        "started_utc": ts,
        "run_dir": rel(run_dir),
        "decision": "wsta75-blocked",
        "gate_decision": "not-run",
        "safety": safety_flags(),
    }
    if not is_under(run_dir, PRIVATE_ROOT):
        result["decision"] = "wsta75-blocked-nonprivate-run-dir"
        result["gate_decision"] = result["decision"]
        result["ended_utc"] = utc_stamp()
        return result
    if not is_under(scan_root, PRIVATE_ROOT):
        result["decision"] = "wsta75-blocked-nonprivate-scan-root"
        result["gate_decision"] = result["decision"]
        result["ended_utc"] = utc_stamp()
        return result
    if not scan_root.exists():
        result["decision"] = "wsta75-blocked-scan-root-missing"
        result["gate_decision"] = result["decision"]
        result["ended_utc"] = utc_stamp()
        return result
    run_dir.mkdir(parents=True, exist_ok=True)
    out_json = run_dir / "wsta75_arming_inventory.json"
    out_md = run_dir / "wsta75_arming_inventory.md"

    packet_paths, truncated = scan_packet_paths(scan_root, run_dir, int(args.max_packets))
    entries: list[dict[str, Any]] = []
    invalid_entries: list[dict[str, Any]] = []
    for index, packet_path in enumerate(packet_paths):
        status_dir = run_dir / f"status-{index:03d}"
        status_path = status_dir / "wsta74_arming_status.json"
        try:
            status_result = wsta74.run(wsta74_args(
                status_dir,
                packet_path,
                args.min_initial_seconds_remaining,
                args.now_utc,
            ))
            entries.append(inventory_entry(index, packet_path, status_result, status_path))
        except Exception as exc:  # noqa: BLE001
            invalid_entries.append({
                "index": index,
                "wsta73_arming_packet": rel(packet_path),
                "error": str(exc),
                "public_url_value_logged": False,
                "secret_values_logged": 0,
            })

    inventory = build_inventory(scan_root, entries, invalid_entries, truncated, int(args.max_packets))
    result.update({
        "decision": PASS_DECISION,
        "gate_decision": "ok",
        "arming_inventory": inventory,
        "checks": {
            "scan_root_private": True,
            "wsta74_rechecked": True,
            "default_public_off": True,
            "live_execution_requested": False,
            "public_url_value_logged": False,
            "secret_values_logged": 0,
        },
    })
    md_text = markdown(inventory)
    findings = redaction_findings(public_summary(result))
    md_findings = redaction_findings({"markdown": md_text})
    if findings or md_findings:
        result["decision"] = "wsta75-blocked-redaction-finding"
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
    parser.add_argument("--scan-root", type=Path, default=DEFAULT_RUN_BASE)
    parser.add_argument("--max-packets", type=int, default=DEFAULT_MAX_PACKETS)
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
        payload = {"decision": "wsta75-runner-error", "error": str(exc)}
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1
    payload = result if args.print_full_json else public_summary(result)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.get("decision") == PASS_DECISION else 2


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
