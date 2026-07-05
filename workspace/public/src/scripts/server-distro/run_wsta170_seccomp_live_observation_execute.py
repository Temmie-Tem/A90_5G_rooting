#!/usr/bin/env python3
"""WSTA170 gated executor for the WSTA168 no-load live observation.

This runner consumes the WSTA169 read-only readiness proof and the WSTA168
command artifacts.  By default it is inert and returns a blocked decision after
validating those inputs.  Only the full explicit acknowledgement set executes
the generated WSTA167 no-load live observation command.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REVAL_DIR = SCRIPT_DIR.parent / "revalidation"
for _path in (SCRIPT_DIR, REVAL_DIR):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import prepare_wsta3_sta_rootfs as wsta3  # noqa: E402
import run_wsta160_seccomp_full_rootfs_chroot_dry_run as wsta160  # noqa: E402
import run_wsta167_seccomp_live_observation as wsta167  # noqa: E402
import run_wsta169_seccomp_live_readiness_readonly as wsta169  # noqa: E402


REPO_ROOT = wsta3.REPO_ROOT
PRIVATE_ROOT = REPO_ROOT / "workspace/private"
DEFAULT_RUN_BASE = wsta3.DEFAULT_RUN_BASE
DEFAULT_WSTA169_PROOF = (
    DEFAULT_RUN_BASE
    / "wsta169-seccomp-live-readiness-readonly-20260705T135709KST"
    / "wsta169_result.json"
)
DEFAULT_WSTA168_COMMAND_JSON = wsta169.DEFAULT_WSTA168_COMMAND_JSON
DEFAULT_WSTA168_COMMAND_SH = wsta169.DEFAULT_WSTA168_COMMAND_SH
PASS_DECISION = "wsta170-seccomp-live-observation-execute-pass"
SUMMARY_NAME = "wsta170_result.json"


def rel(path: Path) -> str:
    return wsta3.rel(path)


def utc_stamp() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def write_json(path: Path, payload: Any) -> None:
    wsta3.write_json(path, payload)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fp:
        payload = json.load(fp)
    if not isinstance(payload, dict):
        raise ValueError(f"expected object JSON: {path}")
    return payload


def explicit_execution_gate(args: argparse.Namespace) -> tuple[bool, str]:
    if not args.execute_wsta170_no_load_live_observation:
        return False, "wsta170-blocked-explicit-execution-gate-required"
    if not args.allow_wsta168_command_execution:
        return False, "wsta170-blocked-wsta168-command-execution-allow-required"
    if not args.ack_readiness_proof_current:
        return False, "wsta170-blocked-readiness-proof-current-ack-required"
    if not args.ack_no_correct_wsta161_token:
        return False, "wsta170-blocked-no-correct-token-ack-required"
    if not args.ack_no_seccomp_load:
        return False, "wsta170-blocked-no-seccomp-load-ack-required"
    if not args.ack_cleanup_required:
        return False, "wsta170-blocked-cleanup-ack-required"
    return True, "ok"


def safety_flags(gate_ok: bool) -> dict[str, Any]:
    return {
        "device_action_requested": gate_ok,
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
        "gate_decision": result.get("gate_decision"),
        "checks": result.get("checks", {}),
        "execution": {
            "returncode": result.get("execution", {}).get("returncode"),
            "nested_result": result.get("nested_result_path"),
            "nested_decision": result.get("nested_result", {}).get("decision"),
        },
        "safety": result.get("safety", {}),
    }


def validate_readiness_proof(proof: dict[str, Any], command_json: Path, command_sh: Path) -> dict[str, bool]:
    checks = proof.get("checks", {})
    safety = proof.get("safety", {})
    command_checks = proof.get("command_checks", {})
    return {
        "decision_pass": proof.get("decision") == wsta169.PASS_DECISION,
        "explicit_readiness_gate": checks.get("explicit_gate") is True,
        "command_ready": checks.get("command_ready") is True,
        "bridge_ready": checks.get("bridge_ready") is True,
        "version_ok": checks.get("version_ok") is True,
        "status_ok": checks.get("status_ok") is True,
        "selftest_fail_zero": checks.get("selftest_fail_zero") is True,
        "command_json_matches": proof.get("wsta168_command_json") == rel(command_json),
        "command_sh_matches": proof.get("wsta168_command_sh") == rel(command_sh),
        "proof_command_checks_true": bool(command_checks) and all(value is True for value in command_checks.values()),
        "proof_no_live_execution": safety.get("live_command_executed") is False,
        "proof_no_seccomp_load": safety.get("seccomp_filter_loaded") is False,
        "proof_no_seccomp_enforce": safety.get("seccomp_enforced") is False,
        "proof_no_correct_token": safety.get("correct_wsta161_token_supplied") is False,
    }


def command_run_dir(command: list[str]) -> Path | None:
    try:
        idx = command.index("--run-dir")
        value = command[idx + 1]
    except (ValueError, IndexError):
        return None
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


def validate_command_payload(payload: dict[str, Any], command_json: Path, command_sh: Path) -> dict[str, bool]:
    command = payload.get("command", [])
    command_text = " ".join(str(item) for item in command)
    nested_run_dir = command_run_dir(command) if all(isinstance(item, str) for item in command) else None
    artifact_checks = wsta169.validate_command_artifacts(command_json, command_sh)
    return {
        **artifact_checks,
        "command_is_string_list": isinstance(command, list) and all(isinstance(item, str) for item in command),
        "command_targets_wsta167_exact": (
            "workspace/public/src/scripts/server-distro/run_wsta167_seccomp_live_observation.py" in command
        ),
        "command_has_execute_gate": "--execute-seccomp-live-observation" in command,
        "command_has_allow_gate": "--allow-seccomp-live-observation" in command,
        "command_has_no_correct_token_ack": "--ack-no-correct-wsta161-token" in command,
        "command_has_no_load_ack": "--ack-no-seccomp-load" in command,
        "command_has_cleanup_ack": "--ack-cleanup-required" in command,
        "command_excludes_correct_token": "WSTA161-EXPLICIT-ALLOW-SECCOMP-LOAD" not in command_text,
        "command_excludes_public_tunnel": "cloudflared" not in command_text and "tunnel" not in command_text.lower(),
        "nested_run_dir_private": bool(nested_run_dir and wsta160.is_under(nested_run_dir, PRIVATE_ROOT)),
    }


def validate_nested_result(nested: dict[str, Any]) -> dict[str, bool]:
    safety = nested.get("safety", {})
    checks = nested.get("checks", {})
    return {
        "nested_decision_pass": nested.get("decision") == wsta167.PASS_DECISION,
        "nested_observation_pass": checks.get("observation_pass") is True,
        "nested_cleanup_ok": checks.get("chroot_cleanup_ok") is True,
        "nested_final_selftest_fail_zero": checks.get("final_selftest_fail_zero") is True,
        "nested_no_seccomp_load": safety.get("seccomp_filter_loaded") is False,
        "nested_no_seccomp_enforce": safety.get("seccomp_enforced") is False,
        "nested_no_correct_token": safety.get("correct_wsta161_token_supplied") is False,
        "nested_no_flash": safety.get("boot_flash") is False,
        "nested_no_reboot": safety.get("native_reboot") is False,
        "nested_no_wifi": safety.get("wifi_connect") is False,
        "nested_no_dhcp": safety.get("dhcp") is False,
        "nested_no_public_tunnel": safety.get("public_tunnel") is False,
        "nested_no_packet_filter_mutation": safety.get("packet_filter_mutation") is False,
    }


def run_generated_command(command: list[str], *, timeout: float) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        timeout=timeout,
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def classify(result: dict[str, Any]) -> str:
    checks = result.get("checks", {})
    ordered = (
        ("explicit_execution_gate", "wsta170-blocked-explicit-execution-gate-required"),
        ("readiness_proof_valid", "wsta170-blocked-readiness-proof-invalid"),
        ("command_ready", "wsta170-blocked-command-invalid"),
        ("execution_returncode_ok", "wsta170-blocked-execution-returncode"),
        ("nested_result_present", "wsta170-blocked-nested-result-missing"),
        ("nested_result_valid", "wsta170-blocked-nested-result-invalid"),
    )
    for key, decision in ordered:
        if not checks.get(key):
            return decision
    return PASS_DECISION


def run(args: argparse.Namespace) -> dict[str, Any]:
    ts = utc_stamp()
    run_id = args.run_id or f"wsta170-seccomp-live-observation-execute-{ts}"
    run_dir = resolve_path(args.run_dir or (DEFAULT_RUN_BASE / run_id))
    readiness_proof = resolve_path(args.wsta169_readiness_json)
    command_json = resolve_path(args.wsta168_command_json)
    command_sh = resolve_path(args.wsta168_command_sh)
    gate_ok, gate_decision = explicit_execution_gate(args)
    result: dict[str, Any] = {
        "scope": "WSTA170 gated no-load seccomp live observation executor",
        "started_utc": ts,
        "run_dir": rel(run_dir),
        "gate_decision": gate_decision,
        "wsta169_readiness_json": rel(readiness_proof),
        "wsta168_command_json": rel(command_json),
        "wsta168_command_sh": rel(command_sh),
        "safety": safety_flags(gate_ok),
        "checks": {
            "explicit_execution_gate": gate_ok,
            "private_run_dir": wsta160.is_under(run_dir, PRIVATE_ROOT),
            "readiness_proof_private": wsta160.is_under(readiness_proof, PRIVATE_ROOT),
            "command_json_private": wsta160.is_under(command_json, PRIVATE_ROOT),
            "command_sh_private": wsta160.is_under(command_sh, PRIVATE_ROOT),
            "readiness_proof_present": readiness_proof.is_file(),
            "command_json_present": command_json.is_file(),
            "command_sh_present": command_sh.is_file(),
        },
    }
    if not result["checks"]["private_run_dir"]:
        result["decision"] = "wsta170-blocked-nonprivate-run-dir"
        result["ended_utc"] = utc_stamp()
        return result
    run_dir.mkdir(parents=True, exist_ok=True)
    out_path = run_dir / SUMMARY_NAME

    for key, decision in (
        ("readiness_proof_private", "wsta170-blocked-readiness-proof-nonprivate"),
        ("command_json_private", "wsta170-blocked-command-json-nonprivate"),
        ("command_sh_private", "wsta170-blocked-command-sh-nonprivate"),
        ("readiness_proof_present", "wsta170-blocked-readiness-proof-missing"),
        ("command_json_present", "wsta170-blocked-command-json-missing"),
        ("command_sh_present", "wsta170-blocked-command-sh-missing"),
    ):
        if not result["checks"][key]:
            result["decision"] = decision
            result["ended_utc"] = utc_stamp()
            write_json(out_path, result)
            return result

    readiness = load_json(readiness_proof)
    command_payload = load_json(command_json)
    readiness_checks = validate_readiness_proof(readiness, command_json, command_sh)
    command_checks = validate_command_payload(command_payload, command_json, command_sh)
    result["readiness_checks"] = readiness_checks
    result["command_checks"] = command_checks
    result["checks"]["readiness_proof_valid"] = all(readiness_checks.values())
    result["checks"]["command_ready"] = all(command_checks.values())
    write_json(out_path, result)

    if not gate_ok or not result["checks"]["readiness_proof_valid"] or not result["checks"]["command_ready"]:
        result["decision"] = classify(result)
        result["ended_utc"] = utc_stamp()
        write_json(out_path, result)
        return result

    command = command_payload["command"]
    nested_run_dir = command_run_dir(command)
    nested_result_path = nested_run_dir / wsta167.RESULT_NAME if nested_run_dir else None
    result["nested_result_path"] = rel(nested_result_path) if nested_result_path else None
    result["safety"]["device_action"] = "wsta167-no-load-live-observation"
    result["safety"]["live_command_executed"] = True
    result["execution"] = run_generated_command(command, timeout=args.execution_timeout)
    result["checks"]["execution_returncode_ok"] = result["execution"].get("returncode") == 0
    result["checks"]["nested_result_present"] = bool(nested_result_path and nested_result_path.is_file())
    if result["checks"]["nested_result_present"] and nested_result_path is not None:
        nested = load_json(nested_result_path)
        nested_checks = validate_nested_result(nested)
        result["nested_result"] = nested
        result["nested_checks"] = nested_checks
        result["checks"]["nested_result_valid"] = all(nested_checks.values())
    else:
        result["nested_result"] = {}
        result["nested_checks"] = {}
        result["checks"]["nested_result_valid"] = False
    result["decision"] = classify(result)
    result["ended_utc"] = utc_stamp()
    write_json(out_path, result)
    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--wsta169-readiness-json", type=Path, default=DEFAULT_WSTA169_PROOF)
    parser.add_argument("--wsta168-command-json", type=Path, default=DEFAULT_WSTA168_COMMAND_JSON)
    parser.add_argument("--wsta168-command-sh", type=Path, default=DEFAULT_WSTA168_COMMAND_SH)
    parser.add_argument("--execution-timeout", type=float, default=1800.0)
    parser.add_argument("--execute-wsta170-no-load-live-observation", action="store_true")
    parser.add_argument("--allow-wsta168-command-execution", action="store_true")
    parser.add_argument("--ack-readiness-proof-current", action="store_true")
    parser.add_argument("--ack-no-correct-wsta161-token", action="store_true")
    parser.add_argument("--ack-no-seccomp-load", action="store_true")
    parser.add_argument("--ack-cleanup-required", action="store_true")
    parser.add_argument("--print-full-json", action="store_true")
    return parser


def main_with_args(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        result = run(args)
    except Exception as exc:  # noqa: BLE001
        payload = {"decision": "wsta170-runner-error", "error": str(exc)}
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1
    payload = result if args.print_full_json else public_summary(result)
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result.get("decision") == PASS_DECISION else 2


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
