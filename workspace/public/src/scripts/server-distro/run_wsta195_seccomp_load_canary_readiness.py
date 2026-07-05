#!/usr/bin/env python3
"""WSTA195 read-only readiness gate for the seccomp-load canary packet.

Consumes the WSTA194 private/default-off operator packet and verifies it is a
safe input for a later WSTA196 live-runner design.  This unit is host-only: it
does not contact the device, does not execute the packet shell wrapper, does
not generate or run a live command, does not supply the correct WSTA161 token,
and does not load or enforce seccomp.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import prepare_wsta3_sta_rootfs as wsta3  # noqa: E402
import run_wsta160_seccomp_full_rootfs_chroot_dry_run as wsta160  # noqa: E402
import run_wsta193_seccomp_correct_token_canary_source as wsta193  # noqa: E402
import run_wsta194_seccomp_load_canary_operator_packet as wsta194  # noqa: E402


REPO_ROOT = wsta3.REPO_ROOT
PRIVATE_ROOT = REPO_ROOT / "workspace/private"
DEFAULT_RUN_BASE = wsta3.DEFAULT_RUN_BASE
DEFAULT_WSTA194_OPERATOR_PACKET_JSON = (
    DEFAULT_RUN_BASE
    / "wsta194-seccomp-load-canary-operator-packet-20260705T1648KST"
    / wsta194.PACKET_JSON_NAME
)
PASS_DECISION = "wsta195-seccomp-load-canary-readiness-pass"
SUMMARY_NAME = "wsta195_result.json"
READINESS_JSON_NAME = "wsta195_seccomp_load_canary_readiness.json"
READINESS_MD_NAME = "wsta195_seccomp_load_canary_readiness.md"
FORBIDDEN_TOKEN_PREFIX = "WSTA161-" + "EXPLICIT"


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
        "host_readiness_only": True,
        "operator_packet_executed": False,
        "shell_wrapper_executed": False,
        "shell_wrapper_syntax_checked": True,
        "live_command_generated": False,
        "live_command_executed": False,
        "correct_wsta161_token_supplied": False,
        "correct_wsta161_token_in_artifact": False,
        "seccomp_filter_loaded": False,
        "seccomp_enforced": False,
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def template() -> dict[str, Any]:
    return {
        "scope": "WSTA195 host-only seccomp-load canary readiness",
        "default_mode": "host-only-readiness-gate",
        "command": [
            "python3",
            rel(Path(__file__).resolve()),
            "--emit-wsta195-seccomp-load-canary-readiness",
        ],
        "device_readiness": "not-checked-by-wsta195",
        "live_execution": "not-generated-by-wsta195",
        "correct_wsta161_token": "not-supplied",
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def public_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": result.get("decision"),
        "run_dir": result.get("run_dir"),
        "gate_decision": result.get("gate_decision"),
        "readiness": result.get("readiness", {}),
        "checks": result.get("checks", {}),
        "safety": result.get("safety", {}),
    }


def no_external_network_inputs(text: str) -> bool:
    lowered = text.lower()
    return (
        "cloudflared" not in lowered
        and ("ss" + "id=") not in lowered
        and ("ps" + "k=") not in lowered
        and "try" + "cloudflare.com" not in lowered
        and "http" + "://" not in lowered
        and "https" + "://" not in lowered
    )


def validate_packet_payload(payload: dict[str, Any]) -> tuple[dict[str, bool], dict[str, Any]]:
    packet = payload.get("operator_packet") if isinstance(payload.get("operator_packet"), dict) else {}
    serialized = json.dumps(payload, sort_keys=True)
    command = packet.get("future_live_command_template", [])
    if not isinstance(command, list):
        command = []
    ack = packet.get("operator_acknowledgements_required", [])
    if not isinstance(ack, list):
        ack = []
    safety_boundary = packet.get("safety_boundary", {})
    if not isinstance(safety_boundary, dict):
        safety_boundary = {}
    checks = {
        "payload_decision_pass": payload.get("decision") == wsta194.PASS_DECISION,
        "operator_packet_object": bool(packet),
        "schema_ok": packet.get("schema") == "a90-wsta194-seccomp-load-canary-operator-packet-v1",
        "state_default_off": (
            packet.get("state") == "READY_OPERATOR_PACKET_SINGLE_SERVICE_CANARY_DEFAULT_OFF_WSTA196_REQUIRED"
        ),
        "default_off": packet.get("default_off") is True,
        "not_ready_for_live_execution": packet.get("ready_for_live_execution") is False,
        "ready_for_wsta195": packet.get("ready_for_wsta195_readiness") is True,
        "ready_for_wsta196_design": packet.get("ready_for_wsta196_design") is True,
        "live_execution_not_requested": packet.get("live_execution_requested") is False,
        "canary_service_hud": packet.get("canary_service") == wsta193.CANARY_SERVICE,
        "policy_service_hud_intent": packet.get("policy_service") == "dpublic-hud-intent",
        "single_service_canary": packet.get("single_service_canary") is True,
        "private_token_env_named": packet.get("private_token_env") == wsta193.PRIVATE_TOKEN_ENV,
        "token_value_not_included": packet.get("token_value_included") is False,
        "correct_token_not_supplied": packet.get("correct_wsta161_token_supplied") is False,
        "seccomp_not_loaded": packet.get("seccomp_filter_loaded") is False,
        "seccomp_not_enforced": packet.get("seccomp_enforced") is False,
        "boundary_no_flash": safety_boundary.get("boot_flash") is False,
        "boundary_no_reboot": safety_boundary.get("native_reboot") is False,
        "boundary_no_wifi": safety_boundary.get("wifi_connect") is False,
        "boundary_no_dhcp": safety_boundary.get("dhcp") is False,
        "boundary_no_packet_filter": safety_boundary.get("packet_filter_mutation") is False,
        "boundary_no_seccomp_load": safety_boundary.get("seccomp_filter_loaded") is False,
        "boundary_no_seccomp_enforce": safety_boundary.get("seccomp_enforced") is False,
        "future_command_targets_wsta196": wsta194.FUTURE_WSTA196_RUNNER in command,
        "future_command_has_all_ack_flags": all(flag in command for flag in ack),
        "future_command_not_currently_executable": any("<fresh-timestamp>" in str(item) for item in command),
        "no_wsta187_reuse": "run_wsta187" not in serialized and "WSTA187" not in serialized,
        "no_wsta190_reuse": "run_wsta190" not in serialized and "WSTA190" not in serialized,
        "no_flash_surface": ("native_" + "init_flash.py") not in serialized,
        "no_external_network_inputs": no_external_network_inputs(json.dumps(command, sort_keys=True)),
        "token_literal_absent": FORBIDDEN_TOKEN_PREFIX not in serialized,
        "secret_values_zero": packet.get("secret_values_logged") == 0,
        "public_url_not_logged": packet.get("public_url_value_logged") is False,
    }
    return checks, packet


def shell_syntax(script_path: Path) -> dict[str, Any]:
    completed = subprocess.run(
        ["sh", "-n", str(script_path)],
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        timeout=10.0,
    )
    return {
        "command": ["sh", "-n", rel(script_path)],
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "ok": completed.returncode == 0,
    }


def validate_shell(packet: dict[str, Any]) -> tuple[dict[str, bool], dict[str, Any], str]:
    shell_raw = packet.get("operator_packet_shell")
    shell_path = resolve_path(shell_raw) if isinstance(shell_raw, str) and shell_raw else REPO_ROOT / "__missing__"
    text = shell_path.read_text(encoding="utf-8") if shell_path.is_file() else ""
    syntax = shell_syntax(shell_path) if shell_path.is_file() else {"ok": False, "returncode": None}
    checks = {
        "shell_path_private": wsta160.is_under(shell_path, PRIVATE_ROOT),
        "shell_present": shell_path.is_file(),
        "shell_executable": os.access(shell_path, os.X_OK) if shell_path.exists() else False,
        "shell_syntax_ok": syntax.get("ok") is True,
        "shell_default_off_marker": "A90WSTA194_OPERATOR_PACKET_DEFAULT_OFF=1" in text,
        "shell_wsta196_required_marker": "A90WSTA194_WSTA196_REQUIRED=1" in text,
        "shell_fails_closed": "a90_wsta194_decision=blocked-wsta196-not-implemented" in text
        and "exit 65" in text,
        "shell_not_executing_live_runner": "exec python3" not in text and wsta194.FUTURE_WSTA196_RUNNER not in text,
        "shell_token_literal_absent": FORBIDDEN_TOKEN_PREFIX not in text,
        "shell_no_external_network_inputs": no_external_network_inputs(text),
    }
    return checks, syntax, text


def validate_markdown(packet: dict[str, Any]) -> tuple[dict[str, bool], str]:
    markdown_raw = packet.get("operator_packet_markdown")
    md_path = resolve_path(markdown_raw) if isinstance(markdown_raw, str) and markdown_raw else REPO_ROOT / "__missing__"
    text = md_path.read_text(encoding="utf-8") if md_path.is_file() else ""
    checks = {
        "markdown_path_private": wsta160.is_under(md_path, PRIVATE_ROOT),
        "markdown_present": md_path.is_file(),
        "markdown_default_off": "Default off" in text,
        "markdown_says_no_execute": "does not execute" in text,
        "markdown_token_literal_absent": FORBIDDEN_TOKEN_PREFIX not in text,
        "markdown_no_external_network_inputs": no_external_network_inputs(text),
    }
    return checks, text


def build_readiness(run_dir: Path, packet_json: Path, packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "a90-wsta195-seccomp-load-canary-readiness-v1",
        "state": "READY_FOR_WSTA196_DESIGN_READONLY_NOT_EXECUTABLE",
        "readiness_scope": "host-only-packet-readiness-not-device-readiness",
        "source_wsta194_operator_packet": rel(packet_json),
        "source_wsta194_operator_shell": packet.get("operator_packet_shell"),
        "source_wsta194_operator_markdown": packet.get("operator_packet_markdown"),
        "readiness_json": rel(run_dir / READINESS_JSON_NAME),
        "readiness_markdown": rel(run_dir / READINESS_MD_NAME),
        "canary_service": packet.get("canary_service"),
        "policy_service": packet.get("policy_service"),
        "single_service_canary": True,
        "private_token_env": packet.get("private_token_env"),
        "token_value_included": False,
        "correct_wsta161_token_supplied": False,
        "seccomp_filter_loaded": False,
        "seccomp_enforced": False,
        "device_readiness_checked": False,
        "read_only_native_health_check_required_in_wsta196": True,
        "ready_for_wsta196_design": True,
        "ready_for_live_execution": False,
        "live_command_generated": False,
        "live_command_executed": False,
        "future_wsta196_runner": wsta194.FUTURE_WSTA196_RUNNER,
        "required_wsta196_preconditions": [
            "fresh-WSTA195-readiness-pass",
            "explicit-operator-acknowledgement",
            "private-token-env-set-only-in-attended-shell",
            "read-only-native-health-check-before-load",
            "single-service-canary-only",
            "no-flash-no-reboot-no-wifi-connect-no-dhcp",
            "post-run-audit-and-cleanup-required",
            "stop-on-any-health-regression",
        ],
        "abort_conditions": [
            "WSTA194-packet-not-fresh-or-invalid",
            "operator-shell-wrapper-no-longer-fails-closed",
            "token-value-present-in-artifact",
            "canary-expanded-beyond-one-service",
            "device-health-check-unavailable-in-WSTA196",
            "unexpected-flash-reboot-wifi-or-public-tunnel-surface",
        ],
        "next_action": "design-WSTA196-live-runner-source-only-or-attended-execute-gate",
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def validate_readiness(readiness: dict[str, Any]) -> dict[str, bool]:
    serialized = json.dumps(readiness, sort_keys=True)
    return {
        "schema_ok": readiness.get("schema") == "a90-wsta195-seccomp-load-canary-readiness-v1",
        "state_readonly_not_executable": (
            readiness.get("state") == "READY_FOR_WSTA196_DESIGN_READONLY_NOT_EXECUTABLE"
        ),
        "scope_host_only": readiness.get("readiness_scope") == "host-only-packet-readiness-not-device-readiness",
        "single_service_canary": readiness.get("single_service_canary") is True,
        "canary_service_hud": readiness.get("canary_service") == wsta193.CANARY_SERVICE,
        "private_token_env_named": readiness.get("private_token_env") == wsta193.PRIVATE_TOKEN_ENV,
        "token_value_not_included": readiness.get("token_value_included") is False,
        "correct_token_not_supplied": readiness.get("correct_wsta161_token_supplied") is False,
        "seccomp_not_loaded": readiness.get("seccomp_filter_loaded") is False,
        "seccomp_not_enforced": readiness.get("seccomp_enforced") is False,
        "device_readiness_not_checked": readiness.get("device_readiness_checked") is False,
        "wsta196_health_check_required": readiness.get("read_only_native_health_check_required_in_wsta196") is True,
        "ready_for_wsta196_design": readiness.get("ready_for_wsta196_design") is True,
        "not_ready_for_live_execution": readiness.get("ready_for_live_execution") is False,
        "live_command_not_generated": readiness.get("live_command_generated") is False,
        "live_command_not_executed": readiness.get("live_command_executed") is False,
        "future_runner_wsta196": readiness.get("future_wsta196_runner") == wsta194.FUTURE_WSTA196_RUNNER,
        "token_literal_absent": FORBIDDEN_TOKEN_PREFIX not in serialized,
        "no_external_network_inputs": no_external_network_inputs(serialized),
        "secret_values_zero": readiness.get("secret_values_logged") == 0,
        "public_url_not_logged": readiness.get("public_url_value_logged") is False,
    }


def readiness_markdown(readiness: dict[str, Any]) -> str:
    lines = [
        "# WSTA195 Seccomp-Load Canary Readiness",
        "",
        f"- State: `{readiness.get('state')}`",
        f"- Scope: `{readiness.get('readiness_scope')}`",
        f"- Canary service: `{readiness.get('canary_service')}`",
        f"- Private token env: `{readiness.get('private_token_env')}`",
        f"- Ready for WSTA196 design: `{str(readiness.get('ready_for_wsta196_design')).lower()}`",
        f"- Ready for live execution: `{str(readiness.get('ready_for_live_execution')).lower()}`",
        f"- Device readiness checked: `{str(readiness.get('device_readiness_checked')).lower()}`",
        "",
        "## Boundary",
        "",
        "- WSTA195 is a host-only packet readiness gate.",
        "- WSTA195 does not execute the operator packet.",
        "- WSTA195 does not supply the correct WSTA161 token.",
        "- WSTA195 does not load or enforce seccomp.",
        "- WSTA196 must run a fresh read-only native health check before any load attempt.",
        "",
    ]
    return "\n".join(lines)


def classify(result: dict[str, Any]) -> str:
    checks = result.get("checks", {})
    ordered = (
        ("explicit_gate", "wsta195-blocked-explicit-gate-required"),
        ("private_run_dir", "wsta195-blocked-nonprivate-run-dir"),
        ("wsta194_packet_private", "wsta195-blocked-wsta194-packet-nonprivate"),
        ("wsta194_packet_present", "wsta195-blocked-wsta194-packet-missing"),
        ("wsta194_payload_valid", "wsta195-blocked-wsta194-payload-invalid"),
        ("wsta194_operator_packet_valid", "wsta195-blocked-wsta194-operator-packet-invalid"),
        ("shell_wrapper_valid", "wsta195-blocked-shell-wrapper-invalid"),
        ("markdown_valid", "wsta195-blocked-markdown-invalid"),
        ("readiness_valid", "wsta195-blocked-readiness-invalid"),
    )
    for key, decision in ordered:
        if not checks.get(key):
            return decision
    return PASS_DECISION


def run(args: argparse.Namespace) -> dict[str, Any]:
    ts = utc_stamp()
    run_id = args.run_id or f"wsta195-seccomp-load-canary-readiness-{ts}"
    run_dir = resolve_path(args.run_dir or (DEFAULT_RUN_BASE / run_id))
    packet_json = resolve_path(args.wsta194_operator_packet_json)
    result: dict[str, Any] = {
        "scope": "WSTA195 host-only seccomp-load canary readiness",
        "started_utc": ts,
        "run_dir": rel(run_dir),
        "wsta194_operator_packet_json": rel(packet_json),
        "gate_decision": "not-run",
        "safety": safety_flags(),
        "checks": {
            "explicit_gate": bool(args.emit_wsta195_seccomp_load_canary_readiness),
            "private_run_dir": wsta160.is_under(run_dir, PRIVATE_ROOT),
            "wsta194_packet_private": wsta160.is_under(packet_json, PRIVATE_ROOT),
            "wsta194_packet_present": packet_json.is_file(),
        },
    }
    if not result["checks"]["private_run_dir"]:
        result["decision"] = classify(result)
        result["ended_utc"] = utc_stamp()
        return result
    run_dir.mkdir(parents=True, exist_ok=True)
    out_path = run_dir / SUMMARY_NAME
    for key in ("explicit_gate", "wsta194_packet_private", "wsta194_packet_present"):
        if not result["checks"][key]:
            result["decision"] = classify(result)
            result["gate_decision"] = result["decision"]
            result["ended_utc"] = utc_stamp()
            write_json(out_path, result)
            return result

    payload = load_json(packet_json)
    payload_checks, packet = validate_packet_payload(payload)
    shell_checks, syntax, shell_text = validate_shell(packet)
    markdown_checks, markdown_text = validate_markdown(packet)
    result["wsta194_payload_checks"] = {
        "payload_decision_pass": payload_checks.pop("payload_decision_pass"),
        "operator_packet_object": payload_checks.pop("operator_packet_object"),
    }
    result["wsta194_operator_packet_checks"] = payload_checks
    result["shell_checks"] = shell_checks
    result["shell_syntax"] = syntax
    result["markdown_checks"] = markdown_checks
    result["checks"].update({
        "wsta194_payload_valid": all(result["wsta194_payload_checks"].values()),
        "wsta194_operator_packet_valid": all(payload_checks.values()),
        "shell_wrapper_valid": all(shell_checks.values()),
        "markdown_valid": all(markdown_checks.values()),
    })
    readiness = build_readiness(run_dir, packet_json, packet)
    readiness_checks = validate_readiness(readiness)
    result["readiness_checks"] = readiness_checks
    result["checks"]["readiness_valid"] = all(readiness_checks.values())
    result["readiness"] = {
        "readiness_json": rel(run_dir / READINESS_JSON_NAME),
        "readiness_markdown": rel(run_dir / READINESS_MD_NAME),
        "state": readiness["state"],
        "readiness_scope": readiness["readiness_scope"],
        "canary_service": readiness["canary_service"],
        "single_service_canary": True,
        "private_token_env": readiness["private_token_env"],
        "ready_for_wsta196_design": True,
        "ready_for_live_execution": False,
        "device_readiness_checked": False,
        "correct_wsta161_token_supplied": False,
        "seccomp_filter_loaded": False,
        "seccomp_enforced": False,
    }
    combined_text = json.dumps(payload, sort_keys=True) + "\n" + shell_text + "\n" + markdown_text
    result["artifact_checks"] = {
        "token_literal_absent": FORBIDDEN_TOKEN_PREFIX not in combined_text,
        "no_external_network_inputs": no_external_network_inputs(combined_text),
    }
    result["decision"] = classify(result)
    result["gate_decision"] = "ok" if result["decision"] == PASS_DECISION else result["decision"]
    result["ended_utc"] = utc_stamp()
    if result["decision"] == PASS_DECISION:
        write_json(run_dir / READINESS_JSON_NAME, readiness)
        write_text(run_dir / READINESS_MD_NAME, readiness_markdown(readiness))
    write_json(out_path, result)
    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--wsta194-operator-packet-json", type=Path, default=DEFAULT_WSTA194_OPERATOR_PACKET_JSON)
    parser.add_argument("--emit-wsta195-seccomp-load-canary-readiness", action="store_true")
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
        payload = {"decision": "wsta195-runner-error", "error": str(exc)}
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1
    payload = result if args.print_full_json else public_summary(result)
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result.get("decision") == PASS_DECISION else 2


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
