#!/usr/bin/env python3
"""WSTA177 one-shot execution gate for the no-load seccomp observation.

Runs WSTA176 to create a fresh WSTA175 execution packet immediately before
execution.  By default it stops after validating that packet.  Only the full
WSTA177 acknowledgement set executes the generated command.
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
for _path in (SCRIPT_DIR, SCRIPT_DIR.parent / "revalidation"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import prepare_wsta3_sta_rootfs as wsta3  # noqa: E402
import run_wsta160_seccomp_full_rootfs_chroot_dry_run as wsta160  # noqa: E402
import run_wsta175_seccomp_handoff_execute_gate as wsta175  # noqa: E402
import run_wsta176_seccomp_handoff_execute_preflight as wsta176  # noqa: E402


REPO_ROOT = wsta3.REPO_ROOT
PRIVATE_ROOT = REPO_ROOT / "workspace/private"
DEFAULT_RUN_BASE = wsta3.DEFAULT_RUN_BASE
DEFAULT_WSTA168_COMMAND_JSON = wsta176.DEFAULT_WSTA168_COMMAND_JSON
DEFAULT_WSTA168_COMMAND_SH = wsta176.DEFAULT_WSTA168_COMMAND_SH
PASS_DECISION = "wsta177-seccomp-one-shot-execute-pass"
SUMMARY_NAME = "wsta177_result.json"


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


def explicit_execution_gate(args: argparse.Namespace) -> tuple[bool, str]:
    if not args.execute_wsta177_one_shot:
        return False, "wsta177-blocked-explicit-execution-gate-required"
    if not args.allow_wsta175_command_execution:
        return False, "wsta177-blocked-wsta175-command-execution-allow-required"
    if not args.ack_fresh_preflight:
        return False, "wsta177-blocked-fresh-preflight-ack-required"
    if not args.ack_no_correct_wsta161_token:
        return False, "wsta177-blocked-no-correct-token-ack-required"
    if not args.ack_no_seccomp_load:
        return False, "wsta177-blocked-no-seccomp-load-ack-required"
    if not args.ack_cleanup_required:
        return False, "wsta177-blocked-cleanup-ack-required"
    return True, "ok"


def safety_flags(gate_ok: bool) -> dict[str, Any]:
    return {
        "device_action_requested": gate_ok,
        "device_action": "read-only-status-only" if not gate_ok else False,
        "boot_flash": False,
        "native_reboot": False,
        "wifi_connect": False,
        "dhcp": False,
        "public_tunnel": False,
        "public_smoke": False,
        "packet_filter_mutation": False,
        "userdata_touch": False,
        "switch_root": False,
        "fresh_preflight_generated": False,
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
        "gate_decision": result.get("gate_decision"),
        "fresh_preflight": result.get("fresh_preflight", {}),
        "checks": result.get("checks", {}),
        "execution": {
            "returncode": result.get("execution", {}).get("returncode"),
            "wsta175_result": result.get("wsta175_result_path"),
            "wsta175_decision": result.get("wsta175_result", {}).get("decision"),
        },
        "safety": result.get("safety", {}),
    }


def wsta176_args(
    run_dir: Path,
    command_json: Path,
    command_sh: Path,
    readiness_timeout: float,
    execution_timeout: float,
    max_age_sec: int,
) -> argparse.Namespace:
    return argparse.Namespace(
        run_id="wsta177-wsta176-handoff-execute-preflight",
        run_dir=run_dir,
        wsta168_command_json=command_json,
        wsta168_command_sh=command_sh,
        readiness_timeout=readiness_timeout,
        execution_timeout=execution_timeout,
        max_age_sec=max_age_sec,
        emit_wsta175_execute_preflight=True,
        print_full_json=False,
    )


def command_run_dir(command: list[str]) -> Path | None:
    try:
        idx = command.index("--run-dir")
        value = command[idx + 1]
    except (ValueError, IndexError):
        return None
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


def validate_fresh_preflight(result: dict[str, Any], command_json: Path, command_sh: Path) -> dict[str, bool]:
    checks = result.get("checks", {})
    safety = result.get("safety", {})
    command = result.get("command", {})
    return {
        "decision_pass": result.get("decision") == wsta176.PASS_DECISION,
        "gate_ok": result.get("gate_decision") == "ok",
        "fresh_handoff_valid": checks.get("fresh_handoff_valid") is True,
        "source_gate_valid": checks.get("source_gate_valid") is True,
        "execution_command_valid": checks.get("execution_command_valid") is True,
        "wsta168_json_path_matches": result.get("wsta168_command_json") == rel(command_json),
        "wsta168_sh_path_matches": result.get("wsta168_command_sh") == rel(command_sh),
        "command_ready": command.get("state") == "READY_TO_RUN_NOT_EXECUTED",
        "command_not_executed": command.get("executed") is False,
        "command_json_present": bool(command.get("command_json") and resolve_path(command["command_json"]).is_file()),
        "command_script_present": bool(command.get("command_script") and resolve_path(command["command_script"]).is_file()),
        "no_live_execution": safety.get("live_command_executed") is False,
        "no_wsta175_execution": safety.get("wsta175_execute_command_executed") is False,
        "no_wsta170_execution": safety.get("wsta170_execute_command_executed") is False,
        "no_seccomp_load": safety.get("seccomp_filter_loaded") is False,
        "no_seccomp_enforce": safety.get("seccomp_enforced") is False,
        "no_correct_token": safety.get("correct_wsta161_token_supplied") is False,
    }


def validate_execution_command(command_payload: dict[str, Any], script_text: str) -> dict[str, bool]:
    command = command_payload.get("command", [])
    text = " ".join(str(item) for item in command) + script_text
    required = command_payload.get("required_ack_flags", [])
    expected = command_payload.get("expected_outcome", {})
    return {
        "schema_ok": command_payload.get("schema") == "a90-wsta176-wsta175-execute-command-v1",
        "ready_not_executed": command_payload.get("state") == "READY_TO_RUN_NOT_EXECUTED",
        "not_executed": command_payload.get("executed") is False,
        "command_is_string_list": isinstance(command, list) and all(isinstance(item, str) for item in command),
        "command_targets_wsta175": (
            "workspace/public/src/scripts/server-distro/run_wsta175_seccomp_handoff_execute_gate.py" in command
        ),
        "all_ack_flags_present": all(flag in command and flag in script_text for flag in required),
        "correct_token_literal_absent": "WSTA161-EXPLICIT-ALLOW-SECCOMP-LOAD" not in text,
        "no_external_network_inputs": (
            "cloudflared" not in text and "wifi" not in text.lower() and "dhcp" not in text.lower()
        ),
        "expected_wsta175_pass": expected.get("decision") == wsta175.PASS_DECISION,
        "expected_wsta170_pass": expected.get("nested_wsta170_decision") == wsta175.wsta170.PASS_DECISION,
        "expected_wsta167_pass": expected.get("nested_wsta167_decision") == wsta175.wsta170.wsta167.PASS_DECISION,
        "expected_no_seccomp_load": expected.get("seccomp_filter_loaded") is False,
        "expected_no_seccomp_enforce": expected.get("seccomp_enforced") is False,
        "expected_no_correct_token": expected.get("correct_wsta161_token_supplied") is False,
    }


def validate_wsta175_result(result: dict[str, Any]) -> dict[str, bool]:
    safety = result.get("safety", {})
    checks = result.get("checks", {})
    return {
        "decision_pass": result.get("decision") == wsta175.PASS_DECISION,
        "handoff_valid": checks.get("handoff_valid") is True,
        "handoff_fresh": checks.get("handoff_fresh") is True,
        "command_artifacts_valid": checks.get("command_artifacts_valid") is True,
        "execution_returncode_ok": checks.get("execution_returncode_ok") is True,
        "wsta170_result_present": checks.get("wsta170_result_present") is True,
        "wsta170_result_valid": checks.get("wsta170_result_valid") is True,
        "no_seccomp_load": safety.get("seccomp_filter_loaded") is False,
        "no_seccomp_enforce": safety.get("seccomp_enforced") is False,
        "no_correct_token": safety.get("correct_wsta161_token_supplied") is False,
        "no_flash": safety.get("boot_flash") is False,
        "no_reboot": safety.get("native_reboot") is False,
        "no_wifi": safety.get("wifi_connect") is False,
        "no_dhcp": safety.get("dhcp") is False,
        "no_public_tunnel": safety.get("public_tunnel") is False,
        "no_packet_filter_mutation": safety.get("packet_filter_mutation") is False,
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
        ("explicit_prepare_gate", "wsta177-blocked-explicit-prepare-gate-required"),
        ("fresh_preflight_valid", "wsta177-blocked-fresh-preflight-invalid"),
        ("execution_command_valid", "wsta177-blocked-execution-command-invalid"),
        ("explicit_execution_gate", "wsta177-blocked-explicit-execution-gate-required"),
        ("execution_returncode_ok", "wsta177-blocked-execution-returncode"),
        ("wsta175_result_present", "wsta177-blocked-wsta175-result-missing"),
        ("wsta175_result_valid", "wsta177-blocked-wsta175-result-invalid"),
    )
    for key, decision in ordered:
        if not checks.get(key):
            return decision
    return PASS_DECISION


def run(args: argparse.Namespace) -> dict[str, Any]:
    ts = utc_stamp()
    run_id = args.run_id or f"wsta177-seccomp-one-shot-execute-gate-{ts}"
    run_dir = resolve_path(args.run_dir or (DEFAULT_RUN_BASE / run_id))
    wsta168_command_json = resolve_path(args.wsta168_command_json)
    wsta168_command_sh = resolve_path(args.wsta168_command_sh)
    gate_ok, gate_decision = explicit_execution_gate(args)
    result: dict[str, Any] = {
        "scope": "WSTA177 one-shot no-load seccomp execution gate",
        "started_utc": ts,
        "run_dir": rel(run_dir),
        "wsta168_command_json": rel(wsta168_command_json),
        "wsta168_command_sh": rel(wsta168_command_sh),
        "gate_decision": gate_decision,
        "safety": safety_flags(gate_ok),
        "checks": {
            "explicit_prepare_gate": bool(args.prepare_wsta177_one_shot),
            "explicit_execution_gate": gate_ok,
            "private_run_dir": wsta160.is_under(run_dir, PRIVATE_ROOT),
            "wsta168_command_json_private": wsta160.is_under(wsta168_command_json, PRIVATE_ROOT),
            "wsta168_command_sh_private": wsta160.is_under(wsta168_command_sh, PRIVATE_ROOT),
            "wsta168_command_json_present": wsta168_command_json.is_file(),
            "wsta168_command_sh_present": wsta168_command_sh.is_file(),
        },
    }
    if not result["checks"]["private_run_dir"]:
        result["decision"] = "wsta177-blocked-nonprivate-run-dir"
        result["ended_utc"] = utc_stamp()
        return result
    run_dir.mkdir(parents=True, exist_ok=True)
    out_path = run_dir / SUMMARY_NAME
    for key, decision in (
        ("explicit_prepare_gate", "wsta177-blocked-explicit-prepare-gate-required"),
        ("wsta168_command_json_private", "wsta177-blocked-wsta168-command-json-nonprivate"),
        ("wsta168_command_sh_private", "wsta177-blocked-wsta168-command-sh-nonprivate"),
        ("wsta168_command_json_present", "wsta177-blocked-wsta168-command-json-missing"),
        ("wsta168_command_sh_present", "wsta177-blocked-wsta168-command-sh-missing"),
    ):
        if not result["checks"][key]:
            result["decision"] = decision
            result["ended_utc"] = utc_stamp()
            write_json(out_path, result)
            return result

    fresh_dir = run_dir / "wsta176-handoff-execute-preflight"
    fresh_result = wsta176.run(
        wsta176_args(
            fresh_dir,
            wsta168_command_json,
            wsta168_command_sh,
            args.readiness_timeout,
            args.execution_timeout,
            int(args.max_age_sec),
        )
    )
    command_json = resolve_path(fresh_result.get("command", {}).get("command_json", ""))
    command_script = resolve_path(fresh_result.get("command", {}).get("command_script", ""))
    result["fresh_preflight"] = {
        "run_dir": rel(fresh_dir),
        "result_json": rel(fresh_dir / wsta176.SUMMARY_NAME),
        "decision": fresh_result.get("decision"),
        "command_json": rel(command_json) if str(command_json) else None,
        "command_script": rel(command_script) if str(command_script) else None,
        "handoff_json": fresh_result.get("command", {}).get("handoff_json"),
    }
    fresh_checks = validate_fresh_preflight(fresh_result, wsta168_command_json, wsta168_command_sh)
    result["fresh_preflight_checks"] = fresh_checks
    result["checks"]["fresh_preflight_valid"] = all(fresh_checks.values())
    write_json(out_path, result)
    if not result["checks"]["fresh_preflight_valid"]:
        result["decision"] = classify(result)
        result["ended_utc"] = utc_stamp()
        write_json(out_path, result)
        return result

    command_payload = load_json(command_json)
    script_text = command_script.read_text(encoding="utf-8")
    command_checks = validate_execution_command(command_payload, script_text)
    result["execution_command_checks"] = command_checks
    result["checks"]["execution_command_valid"] = all(command_checks.values())
    result["safety"]["fresh_preflight_generated"] = result["checks"]["fresh_preflight_valid"]
    write_json(out_path, result)
    if not result["checks"]["execution_command_valid"] or not gate_ok:
        result["decision"] = classify(result)
        result["ended_utc"] = utc_stamp()
        write_json(out_path, result)
        return result

    command = command_payload["command"]
    wsta175_run_dir = command_run_dir(command)
    wsta175_result_path = wsta175_run_dir / wsta175.SUMMARY_NAME if wsta175_run_dir else None
    result["wsta175_result_path"] = rel(wsta175_result_path) if wsta175_result_path else None
    result["safety"]["device_action"] = "wsta177-one-shot-no-load-live-observation"
    result["safety"]["wsta175_execute_command_executed"] = True
    result["safety"]["live_command_executed"] = True
    result["execution"] = run_generated_command(command, timeout=args.execution_timeout)
    result["checks"]["execution_returncode_ok"] = result["execution"].get("returncode") == 0
    result["checks"]["wsta175_result_present"] = bool(wsta175_result_path and wsta175_result_path.is_file())
    if result["checks"]["wsta175_result_present"] and wsta175_result_path is not None:
        wsta175_result = load_json(wsta175_result_path)
        result["wsta175_result"] = wsta175_result
        result["wsta175_checks"] = validate_wsta175_result(wsta175_result)
        result["checks"]["wsta175_result_valid"] = all(result["wsta175_checks"].values())
        result["safety"]["wsta170_execute_command_executed"] = bool(
            wsta175_result.get("safety", {}).get("wsta170_execute_command_executed") is True
        )
    else:
        result["wsta175_result"] = {}
        result["wsta175_checks"] = {}
        result["checks"]["wsta175_result_valid"] = False
    result["decision"] = classify(result)
    result["ended_utc"] = utc_stamp()
    write_json(out_path, result)
    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--wsta168-command-json", type=Path, default=DEFAULT_WSTA168_COMMAND_JSON)
    parser.add_argument("--wsta168-command-sh", type=Path, default=DEFAULT_WSTA168_COMMAND_SH)
    parser.add_argument("--readiness-timeout", type=float, default=20.0)
    parser.add_argument("--execution-timeout", type=float, default=1800.0)
    parser.add_argument("--max-age-sec", type=int, default=900)
    parser.add_argument("--prepare-wsta177-one-shot", action="store_true")
    parser.add_argument("--execute-wsta177-one-shot", action="store_true")
    parser.add_argument("--allow-wsta175-command-execution", action="store_true")
    parser.add_argument("--ack-fresh-preflight", action="store_true")
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
        payload = {"decision": "wsta177-runner-error", "error": str(exc)}
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1
    payload = result if args.print_full_json else public_summary(result)
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result.get("decision") == PASS_DECISION else 2


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
