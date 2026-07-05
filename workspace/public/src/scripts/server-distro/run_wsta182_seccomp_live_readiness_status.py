#!/usr/bin/env python3
"""WSTA182 readiness status for the WSTA181 no-load live observation gate.

Consumes the WSTA181 source-gate proof and emits a concise readiness/status
artifact plus the exact WSTA181 execution command packet.  This unit never
executes WSTA181; it only proves the current handoff is ready for explicit
operator approval.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import shlex
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
for _path in (SCRIPT_DIR, SCRIPT_DIR.parent / "revalidation"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import prepare_wsta3_sta_rootfs as wsta3  # noqa: E402
import run_wsta160_seccomp_full_rootfs_chroot_dry_run as wsta160  # noqa: E402
import run_wsta181_seccomp_handoff_execute_audit_gate as wsta181  # noqa: E402


REPO_ROOT = wsta3.REPO_ROOT
PRIVATE_ROOT = REPO_ROOT / "workspace/private"
DEFAULT_RUN_BASE = wsta3.DEFAULT_RUN_BASE
DEFAULT_WSTA181_SOURCE_GATE = (
    DEFAULT_RUN_BASE
    / "wsta181-seccomp-handoff-execute-audit-source-gate-20260705T150428KST"
    / wsta181.SUMMARY_NAME
)
DEFAULT_WSTA180_BUNDLE_JSON = wsta181.DEFAULT_WSTA180_BUNDLE_JSON
DEFAULT_WSTA180_BUNDLE_SH = wsta181.DEFAULT_WSTA180_BUNDLE_SH
PASS_DECISION = "wsta182-seccomp-live-readiness-status-pass"
SUMMARY_NAME = "wsta182_result.json"
STATUS_JSON_NAME = "wsta182_readiness_status.json"
COMMAND_JSON_NAME = "wsta182_wsta181_execute_command.json"
COMMAND_SH_NAME = "wsta182_wsta181_execute_command.sh"
EXECUTION_RUN_ID = "wsta182-seccomp-live-observation-execute"


def rel(path: Path) -> str:
    return wsta3.rel(path)


def utc_stamp() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def resolve_path(path: Path | str) -> Path:
    path_obj = path if isinstance(path, Path) else Path(path)
    return path_obj if path_obj.is_absolute() else REPO_ROOT / path_obj


def write_json(path: Path, payload: Any) -> None:
    wsta3.write_json(path, payload)


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
        "readiness_status_generated": False,
        "wsta181_execute_command_generated": False,
        "wsta181_execute_command_executed": False,
        "wsta178_execute_command_executed": False,
        "wsta177_execute_command_executed": False,
        "wsta175_execute_command_executed": False,
        "wsta170_execute_command_executed": False,
        "live_command_executed": False,
        "seccomp_filter_loaded": False,
        "seccomp_enforced": False,
        "correct_wsta161_token_supplied": False,
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def public_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": result.get("decision"),
        "run_dir": result.get("run_dir"),
        "state": result.get("status", {}).get("state"),
        "command": result.get("command", {}),
        "checks": result.get("checks", {}),
        "safety": result.get("safety", {}),
    }


def validate_wsta181_source_gate(
    source_gate: dict[str, Any],
    source_gate_path: Path,
    bundle_json: Path,
    bundle_sh: Path,
) -> dict[str, bool]:
    checks = source_gate.get("checks", {})
    safety = source_gate.get("safety", {})
    bundle_checks = source_gate.get("handoff_bundle_checks", {})
    execution_checks = source_gate.get("execution_packet_checks", {})
    audit_checks = source_gate.get("post_run_audit_command_checks", {})
    return {
        "source_gate_private": wsta160.is_under(source_gate_path, PRIVATE_ROOT),
        "decision_is_explicit_gate_block": (
            source_gate.get("decision") == "wsta181-blocked-explicit-execution-gate-required"
        ),
        "gate_decision_is_explicit_gate_block": (
            source_gate.get("gate_decision") == "wsta181-blocked-explicit-execution-gate-required"
        ),
        "explicit_execution_gate_false": checks.get("explicit_execution_gate") is False,
        "handoff_bundle_valid": checks.get("handoff_bundle_valid") is True,
        "execution_packet_valid": checks.get("execution_packet_valid") is True,
        "post_run_audit_command_valid": checks.get("post_run_audit_command_valid") is True,
        "bundle_checks_true": bool(bundle_checks) and all(value is True for value in bundle_checks.values()),
        "execution_checks_true": bool(execution_checks) and all(value is True for value in execution_checks.values()),
        "audit_checks_true": bool(audit_checks) and all(value is True for value in audit_checks.values()),
        "bundle_path_matches": source_gate.get("wsta180_bundle_json") == rel(bundle_json),
        "bundle_script_matches": source_gate.get("wsta180_bundle_sh") == rel(bundle_sh),
        "expected_result_missing": bundle_checks.get("expected_result_missing") is True,
        "source_no_device_action": safety.get("device_action_requested") is False,
        "source_no_live_execution": safety.get("live_command_executed") is False,
        "source_no_wsta181_execution": safety.get("wsta181_execute_command_executed") is not True,
        "source_no_wsta178_execution": safety.get("wsta178_execute_command_executed") is False,
        "source_no_wsta177_execution": safety.get("wsta177_execute_command_executed") is False,
        "source_no_wsta175_execution": safety.get("wsta175_execute_command_executed") is False,
        "source_no_wsta170_execution": safety.get("wsta170_execute_command_executed") is False,
        "source_no_seccomp_load": safety.get("seccomp_filter_loaded") is False,
        "source_no_seccomp_enforce": safety.get("seccomp_enforced") is False,
        "source_no_correct_token": safety.get("correct_wsta161_token_supplied") is False,
    }


def execution_command(
    run_dir: Path,
    bundle_json: Path,
    bundle_sh: Path,
    execution_timeout: float,
    audit_timeout: float,
) -> list[str]:
    return [
        "python3",
        "workspace/public/src/scripts/server-distro/run_wsta181_seccomp_handoff_execute_audit_gate.py",
        "--run-id",
        EXECUTION_RUN_ID,
        "--run-dir",
        rel(run_dir / "wsta181-live-run"),
        "--wsta180-bundle-json",
        rel(bundle_json),
        "--wsta180-bundle-sh",
        rel(bundle_sh),
        "--execution-timeout",
        str(execution_timeout),
        "--audit-timeout",
        str(audit_timeout),
        "--execute-wsta181-handoff",
        "--allow-wsta178-command-execution",
        "--ack-handoff-ready",
        "--ack-no-correct-wsta161-token",
        "--ack-no-seccomp-load",
        "--ack-post-run-audit-required",
        "--ack-cleanup-required",
    ]


def command_payload(command: list[str]) -> dict[str, Any]:
    return {
        "schema": "a90-wsta182-wsta181-execute-command-v1",
        "state": "READY_TO_RUN_NOT_EXECUTED",
        "command": command,
        "required_ack_flags": [
            "--execute-wsta181-handoff",
            "--allow-wsta178-command-execution",
            "--ack-handoff-ready",
            "--ack-no-correct-wsta161-token",
            "--ack-no-seccomp-load",
            "--ack-post-run-audit-required",
            "--ack-cleanup-required",
        ],
        "expected_outcome": {
            "decision": wsta181.PASS_DECISION,
            "post_run_audit_decision": wsta181.wsta179.PASS_DECISION,
            "seccomp_filter_loaded": False,
            "seccomp_enforced": False,
            "correct_wsta161_token_supplied": False,
        },
        "forbidden_inputs": [
            "WSTA161-EXPLICIT-ALLOW-SECCOMP-LOAD",
            "cloudflared",
            "wifi",
            "dhcp",
            "packet-filter-mutation",
        ],
        "executed": False,
        "secret_values_logged": 0,
    }


def validate_execution_command(payload: dict[str, Any], script_text: str) -> dict[str, bool]:
    command = payload.get("command", [])
    text = " ".join(str(item) for item in command) + script_text
    required = payload.get("required_ack_flags", [])
    expected = payload.get("expected_outcome", {})
    return {
        "schema_ok": payload.get("schema") == "a90-wsta182-wsta181-execute-command-v1",
        "ready_not_executed": payload.get("state") == "READY_TO_RUN_NOT_EXECUTED",
        "not_executed": payload.get("executed") is False,
        "command_is_string_list": isinstance(command, list) and all(isinstance(item, str) for item in command),
        "command_targets_wsta181": (
            "workspace/public/src/scripts/server-distro/run_wsta181_seccomp_handoff_execute_audit_gate.py" in command
        ),
        "all_ack_flags_present": all(flag in command and flag in script_text for flag in required),
        "correct_token_literal_absent": "WSTA161-EXPLICIT-ALLOW-SECCOMP-LOAD" not in text,
        "no_external_network_inputs": (
            "cloudflared" not in text and "wifi" not in text.lower() and "dhcp" not in text.lower()
        ),
        "expected_wsta181_pass": expected.get("decision") == wsta181.PASS_DECISION,
        "expected_wsta179_pass": expected.get("post_run_audit_decision") == wsta181.wsta179.PASS_DECISION,
        "expected_no_seccomp_load": expected.get("seccomp_filter_loaded") is False,
        "expected_no_seccomp_enforce": expected.get("seccomp_enforced") is False,
        "expected_no_correct_token": expected.get("correct_wsta161_token_supplied") is False,
        "secret_values_logged_zero": payload.get("secret_values_logged") == 0,
    }


def status_payload(
    *,
    source_gate: dict[str, Any],
    source_gate_path: Path,
    bundle_json: Path,
    bundle_sh: Path,
    command_json: Path,
    command_sh: Path,
    command: list[str],
) -> dict[str, Any]:
    bundle = source_gate.get("bundle", {})
    return {
        "schema": "a90-wsta182-seccomp-readiness-status-v1",
        "state": "READY_FOR_EXPLICIT_OPERATOR_APPROVAL",
        "blocking_condition": "explicit-wsta181-operator-approval-required",
        "source_gate": {
            "result_json": rel(source_gate_path),
            "decision": source_gate.get("decision"),
            "gate_decision": source_gate.get("gate_decision"),
        },
        "handoff": {
            "bundle_json": rel(bundle_json),
            "bundle_script": rel(bundle_sh),
            "bundle_state": bundle.get("state"),
            "execute_packet_json": bundle.get("execute_packet_json"),
            "execute_packet_script": bundle.get("execute_packet_script"),
            "expected_wsta177_result_json": bundle.get("expected_wsta177_result_json"),
        },
        "execution": {
            "command_json": rel(command_json),
            "command_script": rel(command_sh),
            "command": command,
            "executed": False,
        },
        "safety": {
            "boot_flash": False,
            "native_reboot": False,
            "wifi_connect": False,
            "dhcp": False,
            "public_tunnel": False,
            "packet_filter_mutation": False,
            "seccomp_filter_load_expected": False,
            "seccomp_enforcement_expected": False,
            "correct_wsta161_token_supplied": False,
            "secret_values_logged": 0,
        },
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    ts = utc_stamp()
    run_id = args.run_id or f"wsta182-seccomp-live-readiness-status-{ts}"
    run_dir = resolve_path(args.run_dir or (DEFAULT_RUN_BASE / run_id))
    source_gate_path = resolve_path(args.wsta181_source_gate_json)
    bundle_json = resolve_path(args.wsta180_bundle_json)
    bundle_sh = resolve_path(args.wsta180_bundle_sh)
    result: dict[str, Any] = {
        "scope": "WSTA182 readiness status for WSTA181 no-load live observation gate",
        "started_utc": ts,
        "run_dir": rel(run_dir),
        "wsta181_source_gate_json": rel(source_gate_path),
        "wsta180_bundle_json": rel(bundle_json),
        "wsta180_bundle_sh": rel(bundle_sh),
        "safety": safety_flags(),
        "checks": {
            "explicit_status_gate": bool(args.emit_wsta182_readiness_status),
            "private_run_dir": wsta160.is_under(run_dir, PRIVATE_ROOT),
            "source_gate_private": wsta160.is_under(source_gate_path, PRIVATE_ROOT),
            "bundle_json_private": wsta160.is_under(bundle_json, PRIVATE_ROOT),
            "bundle_sh_private": wsta160.is_under(bundle_sh, PRIVATE_ROOT),
            "source_gate_present": source_gate_path.is_file(),
            "bundle_json_present": bundle_json.is_file(),
            "bundle_sh_present": bundle_sh.is_file(),
        },
    }
    if not result["checks"]["private_run_dir"]:
        result["decision"] = "wsta182-blocked-nonprivate-run-dir"
        result["ended_utc"] = utc_stamp()
        return result
    run_dir.mkdir(parents=True, exist_ok=True)
    out_path = run_dir / SUMMARY_NAME
    for key, decision in (
        ("explicit_status_gate", "wsta182-blocked-explicit-status-gate-required"),
        ("source_gate_private", "wsta182-blocked-source-gate-nonprivate"),
        ("bundle_json_private", "wsta182-blocked-bundle-json-nonprivate"),
        ("bundle_sh_private", "wsta182-blocked-bundle-sh-nonprivate"),
        ("source_gate_present", "wsta182-blocked-source-gate-missing"),
        ("bundle_json_present", "wsta182-blocked-bundle-json-missing"),
        ("bundle_sh_present", "wsta182-blocked-bundle-sh-missing"),
    ):
        if not result["checks"][key]:
            result["decision"] = decision
            result["ended_utc"] = utc_stamp()
            write_json(out_path, result)
            return result

    source_gate = load_json(source_gate_path)
    result["source_gate_checks"] = validate_wsta181_source_gate(
        source_gate,
        source_gate_path,
        bundle_json,
        bundle_sh,
    )
    result["checks"]["source_gate_valid"] = all(result["source_gate_checks"].values())
    write_json(out_path, result)
    if not result["checks"]["source_gate_valid"]:
        result["decision"] = "wsta182-blocked-source-gate-invalid"
        result["ended_utc"] = utc_stamp()
        write_json(out_path, result)
        return result

    command = execution_command(run_dir, bundle_json, bundle_sh, args.execution_timeout, args.audit_timeout)
    payload = command_payload(command)
    script_text = "#!/bin/sh\nset -eu\ncd " + shlex.quote(str(REPO_ROOT)) + "\nexec " + " ".join(
        shlex.quote(item) for item in command
    ) + "\n"
    command_checks = validate_execution_command(payload, script_text)
    result["execution_command_checks"] = command_checks
    result["checks"]["execution_command_valid"] = all(command_checks.values())
    result["command"] = {
        "command_json": rel(run_dir / COMMAND_JSON_NAME),
        "command_script": rel(run_dir / COMMAND_SH_NAME),
        "state": payload["state"],
        "executed": False,
        "required_ack_count": len(payload["required_ack_flags"]),
        "expected_decision": payload["expected_outcome"]["decision"],
        "expected_post_run_audit_decision": payload["expected_outcome"]["post_run_audit_decision"],
    }
    if not result["checks"]["execution_command_valid"]:
        result["decision"] = "wsta182-blocked-execution-command-invalid"
        result["ended_utc"] = utc_stamp()
        write_json(out_path, result)
        return result

    status = status_payload(
        source_gate=source_gate,
        source_gate_path=source_gate_path,
        bundle_json=bundle_json,
        bundle_sh=bundle_sh,
        command_json=run_dir / COMMAND_JSON_NAME,
        command_sh=run_dir / COMMAND_SH_NAME,
        command=command,
    )
    result["status"] = {
        "status_json": rel(run_dir / STATUS_JSON_NAME),
        "state": status["state"],
        "blocking_condition": status["blocking_condition"],
    }
    result["safety"]["readiness_status_generated"] = True
    result["safety"]["wsta181_execute_command_generated"] = True
    result["decision"] = PASS_DECISION
    result["ended_utc"] = utc_stamp()
    write_json(run_dir / COMMAND_JSON_NAME, payload)
    (run_dir / COMMAND_SH_NAME).write_text(script_text, encoding="utf-8")
    (run_dir / COMMAND_SH_NAME).chmod(0o755)
    write_json(run_dir / STATUS_JSON_NAME, status)
    write_json(out_path, result)
    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--wsta181-source-gate-json", type=Path, default=DEFAULT_WSTA181_SOURCE_GATE)
    parser.add_argument("--wsta180-bundle-json", type=Path, default=DEFAULT_WSTA180_BUNDLE_JSON)
    parser.add_argument("--wsta180-bundle-sh", type=Path, default=DEFAULT_WSTA180_BUNDLE_SH)
    parser.add_argument("--execution-timeout", type=float, default=1800.0)
    parser.add_argument("--audit-timeout", type=float, default=1800.0)
    parser.add_argument("--emit-wsta182-readiness-status", action="store_true")
    parser.add_argument("--print-full-json", action="store_true")
    return parser


def main_with_args(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        result = run(args)
    except Exception as exc:  # noqa: BLE001
        payload = {"decision": "wsta182-runner-error", "error": str(exc)}
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1
    payload = result if args.print_full_json else public_summary(result)
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result.get("decision") == PASS_DECISION else 2


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
