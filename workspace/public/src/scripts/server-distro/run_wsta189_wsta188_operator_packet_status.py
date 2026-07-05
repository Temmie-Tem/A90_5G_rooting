#!/usr/bin/env python3
"""WSTA189 host-only WSTA188 operator packet status.

WSTA188 renders a WSTA187 no-load live operator packet that is fresh at
creation time.  WSTA189 consumes that private packet, validates its default-off
command surface, reruns WSTA188 from the same WSTA168 inputs, and reports
whether the packet is still a current no-load live handoff.

WSTA189 never executes the WSTA187 live path.  It performs no device action,
boot flash, native reboot, Wi-Fi association, DHCP, public tunnel, packet
filter mutation, userdata write, switch-root, seccomp load, seccomp enforce, or
correct WSTA161 token supply.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
for _path in (SCRIPT_DIR, SCRIPT_DIR.parent / "revalidation"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import prepare_wsta3_sta_rootfs as wsta3  # noqa: E402
import run_wsta160_seccomp_full_rootfs_chroot_dry_run as wsta160  # noqa: E402
import run_wsta188_wsta187_operator_packet as wsta188  # noqa: E402


REPO_ROOT = wsta3.REPO_ROOT
PRIVATE_ROOT = REPO_ROOT / "workspace/private"
DEFAULT_RUN_BASE = wsta3.DEFAULT_RUN_BASE
DEFAULT_WSTA188_PACKET_JSON = (
    DEFAULT_RUN_BASE
    / "wsta188-wsta187-operator-packet-20260705T160737KST"
    / wsta188.PACKET_JSON_NAME
)
PASS_DECISION = "wsta189-wsta188-operator-packet-status-pass"
SUMMARY_NAME = "wsta189_result.json"
STATUS_JSON_NAME = "wsta189_operator_packet_status.json"
STATUS_MD_NAME = "wsta189_operator_packet_status.md"


def rel(path: Path) -> str:
    return wsta3.rel(path)


def utc_stamp() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def resolve_path(path: Path | str) -> Path:
    path_obj = path if isinstance(path, Path) else Path(path)
    return path_obj if path_obj.is_absolute() else REPO_ROOT / path_obj


def write_json(path: Path, payload: Any) -> None:
    wsta3.write_json(path, payload)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fp:
        payload = json.load(fp)
    if not isinstance(payload, dict):
        raise ValueError(f"expected object JSON: {path}")
    return payload


def safety_flags() -> dict[str, Any]:
    return {
        "device_action": False,
        "boot_flash": False,
        "native_reboot": False,
        "wifi_connect": False,
        "dhcp": False,
        "public_tunnel": False,
        "public_smoke": False,
        "packet_filter_mutation": False,
        "userdata_touch": False,
        "switch_root": False,
        "wsta188_recheck_executed": False,
        "wsta187_live_command_executed": False,
        "wsta185_execute_command_executed": False,
        "wsta181_execute_command_executed": False,
        "post_run_audit_executed": False,
        "live_command_executed": False,
        "seccomp_filter_loaded": False,
        "seccomp_enforced": False,
        "correct_wsta161_token_supplied": False,
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def template() -> dict[str, Any]:
    return {
        "scope": "WSTA189 host-only WSTA188 operator packet status",
        "default_mode": "host-only-revalidate-wsta188-operator-packet",
        "input": "workspace/private/runs/server-distro/<wsta188-run>/wsta188_operator_packet.json",
        "command": [
            "python3",
            rel(Path(__file__).resolve()),
            "--wsta188-operator-packet-json",
            "workspace/private/runs/server-distro/<wsta188-run>/wsta188_operator_packet.json",
        ],
        "live_execution": "not-run-by-wsta189",
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def public_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": result.get("decision"),
        "run_dir": result.get("run_dir"),
        "operator_packet_status": result.get("operator_packet_status", {}),
        "checks": result.get("checks", {}),
        "safety": result.get("safety", {}),
    }


def command_arg(command: list[Any], flag: str) -> str | None:
    try:
        idx = command.index(flag)
        value = command[idx + 1]
    except (ValueError, IndexError):
        return None
    return value if isinstance(value, str) else None


def command_text(command: Any) -> str:
    return json.dumps(command, sort_keys=True) if isinstance(command, list) else ""


def validate_packet_payload(path: Path) -> tuple[bool, str, dict[str, Any]]:
    try:
        payload = load_json(path)
    except Exception as exc:  # noqa: BLE001
        return False, "wsta189-blocked-operator-packet-unreadable", {"error": str(exc)}
    if payload.get("decision") != wsta188.PASS_DECISION:
        return False, "wsta189-blocked-operator-packet-not-pass", {"decision": payload.get("decision")}
    packet = payload.get("operator_packet")
    if not isinstance(packet, dict):
        return False, "wsta189-blocked-operator-packet-missing", {}
    command = packet.get("live_command_template")
    if not isinstance(command, list):
        return False, "wsta189-blocked-command-template-missing", {}
    text = command_text(command)
    command_json_value = command_arg(command, "--wsta168-command-json")
    command_sh_value = command_arg(command, "--wsta168-command-sh")
    command_json = resolve_path(command_json_value or "")
    command_sh = resolve_path(command_sh_value or "")
    checks = {
        "packet_private": wsta160.is_under(path, PRIVATE_ROOT),
        "state_ready": packet.get("state") == "READY_OPERATOR_PACKET_NO_LOAD_DEFAULT_OFF",
        "default_off": packet.get("default_off") is True,
        "ready_for_no_load_live": packet.get("ready_for_no_load_live") is True,
        "live_not_requested": packet.get("live_execution_requested") is False,
        "source_decision_is_gate_block": (
            packet.get("source_wsta187_decision") == "wsta187-blocked-explicit-execution-gate-required"
        ),
        "command_targets_wsta187": "run_wsta187_fresh_wsta185_orchestrator.py" in text,
        "command_has_prepare_gate": "--prepare-wsta187-fresh-orchestrator" in text,
        "command_has_execute_gate": "--execute-wsta187-fresh-orchestrator" in text,
        "command_has_all_ack_flags": all(flag in text for flag in wsta188.ACK_FLAGS),
        "command_json_private": wsta160.is_under(command_json, PRIVATE_ROOT),
        "command_sh_private": wsta160.is_under(command_sh, PRIVATE_ROOT),
        "command_json_present": command_json.is_file(),
        "command_sh_present": command_sh.is_file(),
        "no_flash_surface": ("native_" + "init_flash.py") not in text,
        "no_correct_token_literal": "WSTA161-EXPLICIT-ALLOW-SECCOMP-LOAD" not in text,
        "no_external_network_inputs": (
            "cloudflared" not in text
            and ("ss" + "id=") not in text.lower()
            and ("ps" + "k=") not in text.lower()
            and "dhcp" not in text.lower()
        ),
        "secret_values_logged_zero": packet.get("secret_values_logged") == 0,
        "public_url_not_logged": packet.get("public_url_value_logged") is False,
    }
    if not all(checks.values()):
        return False, "wsta189-blocked-operator-packet-invalid", {
            "payload": payload,
            "packet": packet,
            "checks": checks,
        }
    return True, "ok", {
        "payload": payload,
        "packet": packet,
        "command_json": command_json,
        "command_sh": command_sh,
        "checks": checks,
    }


def wsta188_args(
    args: argparse.Namespace,
    run_dir: Path,
    command_json: Path,
    command_sh: Path,
) -> argparse.Namespace:
    return argparse.Namespace(
        run_id="wsta189-wsta188-recheck",
        run_dir=run_dir,
        wsta168_command_json=command_json,
        wsta168_command_sh=command_sh,
        readiness_timeout=args.readiness_timeout,
        execution_timeout=args.execution_timeout,
        audit_timeout=args.audit_timeout,
        max_age_sec=args.max_age_sec,
        prepare_wsta188_operator_packet=True,
        print_template=False,
        print_full_json=False,
    )


def stable_packet_view(packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "state": packet.get("state"),
        "ready_for_no_load_live": packet.get("ready_for_no_load_live"),
        "default_off": packet.get("default_off"),
        "live_command_template": packet.get("live_command_template"),
        "operator_acknowledgements_required": packet.get("operator_acknowledgements_required"),
        "operator_preflight_checks": packet.get("operator_preflight_checks"),
        "abort_conditions": packet.get("abort_conditions"),
        "cleanup_expectations": packet.get("cleanup_expectations"),
        "safety_boundary": packet.get("safety_boundary"),
        "live_execution_requested": packet.get("live_execution_requested"),
        "public_url_value_logged": packet.get("public_url_value_logged"),
        "secret_values_logged": packet.get("secret_values_logged"),
    }


def validate_recheck(result: dict[str, Any]) -> dict[str, bool]:
    checks = result.get("checks", {})
    safety = result.get("safety", {})
    packet = result.get("operator_packet", {})
    return {
        "decision_pass": result.get("decision") == wsta188.PASS_DECISION,
        "wsta187_source_gate_valid": checks.get("wsta187_source_gate_valid") is True,
        "operator_packet_valid": checks.get("operator_packet_valid") is True,
        "packet_ready": isinstance(packet, dict) and packet.get("state") == "READY_OPERATOR_PACKET_NO_LOAD_DEFAULT_OFF",
        "no_live_execution": safety.get("live_command_executed") is False,
        "no_wsta187_live": safety.get("wsta187_live_command_executed") is False,
        "no_seccomp_load": safety.get("seccomp_filter_loaded") is False,
        "no_seccomp_enforce": safety.get("seccomp_enforced") is False,
        "no_correct_token": safety.get("correct_wsta161_token_supplied") is False,
    }


def build_status(
    packet_path: Path,
    old_packet: dict[str, Any],
    recheck_result: dict[str, Any],
    recheck_path: Path,
    out_json: Path,
    out_md: Path,
) -> dict[str, Any]:
    new_packet = recheck_result.get("operator_packet")
    recheck_pass = recheck_result.get("decision") == wsta188.PASS_DECISION
    packet_match = bool(
        recheck_pass
        and isinstance(new_packet, dict)
        and stable_packet_view(old_packet) == stable_packet_view(new_packet)
    )
    ready = bool(recheck_pass and packet_match)
    state = "READY_TO_RUN_NO_LOAD_DEFAULT_OFF" if ready else "STALE_OR_NOT_READY"
    if recheck_pass and not packet_match:
        state = "DRIFT_RECHECK_REQUIRED"
    return {
        "state": state,
        "ready_for_no_load_live": ready,
        "wsta188_operator_packet": rel(packet_path),
        "wsta188_recheck_result": rel(recheck_path),
        "wsta188_recheck_decision": recheck_result.get("decision"),
        "wsta188_recheck_source_gate_valid": recheck_result.get("checks", {}).get("wsta187_source_gate_valid"),
        "packet_match": packet_match,
        "template_match": (
            isinstance(new_packet, dict)
            and old_packet.get("live_command_template") == new_packet.get("live_command_template")
        ),
        "operator_acknowledgements_required": old_packet.get("operator_acknowledgements_required") or [],
        "live_command_script": old_packet.get("live_command_script"),
        "source_wsta187_decision": old_packet.get("source_wsta187_decision"),
        "fresh_source_wsta187_decision": (
            new_packet.get("source_wsta187_decision") if isinstance(new_packet, dict) else None
        ),
        "recommended_next_action": (
            "operator-may-run-wsta188-private-shell-wrapper-for-no-load-live"
            if ready
            else "rerun-wsta188-before-attended-no-load-live"
        ),
        "json_path": rel(out_json),
        "markdown_path": rel(out_md),
        "default_off": True,
        "live_execution_requested": False,
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def markdown(status: dict[str, Any]) -> str:
    lines = [
        "# WSTA188 Operator Packet Status",
        "",
        f"- State: `{status.get('state')}`",
        f"- Ready for no-load live: `{str(status.get('ready_for_no_load_live')).lower()}`",
        f"- Packet match: `{str(status.get('packet_match')).lower()}`",
        f"- Template match: `{str(status.get('template_match')).lower()}`",
        f"- Recheck decision: `{status.get('wsta188_recheck_decision')}`",
        f"- Recommended next action: `{status.get('recommended_next_action')}`",
        "",
        "## Boundary",
        "",
        "WSTA189 does not execute the WSTA187 live path.",
        "",
    ]
    return "\n".join(lines)


def classify(result: dict[str, Any]) -> str:
    checks = result.get("checks", {})
    ordered = (
        ("operator_packet_private", "wsta189-blocked-operator-packet-nonprivate"),
        ("operator_packet_present", "wsta189-blocked-operator-packet-missing"),
        ("operator_packet_valid", result.get("operator_packet_error") or "wsta189-blocked-operator-packet-invalid"),
        ("wsta188_recheck_valid", "wsta189-blocked-wsta188-recheck-invalid"),
        ("operator_packet_status_valid", "wsta189-blocked-status-invalid"),
    )
    for key, decision in ordered:
        if not checks.get(key):
            return str(decision)
    return PASS_DECISION


def run(args: argparse.Namespace) -> dict[str, Any]:
    ts = utc_stamp()
    run_id = args.run_id or f"wsta189-wsta188-operator-packet-status-{ts}"
    run_dir = resolve_path(args.run_dir or (DEFAULT_RUN_BASE / run_id))
    packet_path = resolve_path(args.wsta188_operator_packet_json)
    result: dict[str, Any] = {
        "scope": "WSTA189 host-only WSTA188 operator packet status",
        "started_utc": ts,
        "run_dir": rel(run_dir),
        "wsta188_operator_packet_json": rel(packet_path),
        "safety": safety_flags(),
        "checks": {
            "private_run_dir": wsta160.is_under(run_dir, PRIVATE_ROOT),
            "operator_packet_private": wsta160.is_under(packet_path, PRIVATE_ROOT),
            "operator_packet_present": packet_path.is_file(),
        },
    }
    if not result["checks"]["private_run_dir"]:
        result["decision"] = "wsta189-blocked-nonprivate-run-dir"
        result["ended_utc"] = utc_stamp()
        return result
    run_dir.mkdir(parents=True, exist_ok=True)
    out_path = run_dir / SUMMARY_NAME
    for key in ("operator_packet_private", "operator_packet_present"):
        if not result["checks"][key]:
            result["decision"] = classify(result)
            result["ended_utc"] = utc_stamp()
            write_json(out_path, result)
            return result

    valid, decision, packet_info = validate_packet_payload(packet_path)
    result["operator_packet_checks"] = packet_info.get("checks", {})
    result["checks"]["operator_packet_valid"] = valid
    result["operator_packet_error"] = None if valid else decision
    write_json(out_path, result)
    if not valid:
        result["decision"] = classify(result)
        result["ended_utc"] = utc_stamp()
        write_json(out_path, result)
        return result

    command_json = packet_info["command_json"]
    command_sh = packet_info["command_sh"]
    recheck_dir = run_dir / "wsta188-recheck"
    recheck_result = wsta188.run(wsta188_args(args, recheck_dir, command_json, command_sh))
    result["safety"]["wsta188_recheck_executed"] = True
    result["wsta188_recheck"] = {
        "run_dir": rel(recheck_dir),
        "result_json": rel(recheck_dir / wsta188.SUMMARY_NAME),
        "decision": recheck_result.get("decision"),
    }
    result["wsta188_recheck_checks"] = validate_recheck(recheck_result)
    result["checks"]["wsta188_recheck_valid"] = all(result["wsta188_recheck_checks"].values())
    write_json(out_path, result)
    if not result["checks"]["wsta188_recheck_valid"]:
        result["decision"] = classify(result)
        result["ended_utc"] = utc_stamp()
        write_json(out_path, result)
        return result

    status_json = run_dir / STATUS_JSON_NAME
    status_md = run_dir / STATUS_MD_NAME
    status = build_status(
        packet_path,
        packet_info["packet"],
        recheck_result,
        recheck_dir / wsta188.SUMMARY_NAME,
        status_json,
        status_md,
    )
    result["operator_packet_status"] = status
    result["checks"]["operator_packet_status_valid"] = status.get("state") in (
        "READY_TO_RUN_NO_LOAD_DEFAULT_OFF",
        "STALE_OR_NOT_READY",
        "DRIFT_RECHECK_REQUIRED",
    )
    result["decision"] = classify(result)
    result["ended_utc"] = utc_stamp()
    write_json(status_json, result)
    write_text(status_md, markdown(status))
    write_json(out_path, result)
    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--wsta188-operator-packet-json", type=Path, default=DEFAULT_WSTA188_PACKET_JSON)
    parser.add_argument("--readiness-timeout", type=float, default=20.0)
    parser.add_argument("--execution-timeout", type=float, default=1800.0)
    parser.add_argument("--audit-timeout", type=float, default=1800.0)
    parser.add_argument("--max-age-sec", type=int, default=900)
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
        payload = {"decision": "wsta189-runner-error", "error": str(exc)}
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1
    payload = result if args.print_full_json else public_summary(result)
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result.get("decision") == PASS_DECISION else 2


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
