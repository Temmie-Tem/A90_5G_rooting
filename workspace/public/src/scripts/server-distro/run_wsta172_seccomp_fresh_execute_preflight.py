#!/usr/bin/env python3
"""WSTA172 fresh pre-execution bundle for the seccomp live observation.

Runs a fresh WSTA169 read-only readiness check, then regenerates the WSTA170
source gate and WSTA171 execution preflight from that fresh readiness proof.
This does not execute the generated WSTA170 command.
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
import run_wsta169_seccomp_live_readiness_readonly as wsta169  # noqa: E402
import run_wsta170_seccomp_live_observation_execute as wsta170  # noqa: E402
import run_wsta171_seccomp_live_observation_execute_preflight as wsta171  # noqa: E402


REPO_ROOT = wsta3.REPO_ROOT
PRIVATE_ROOT = REPO_ROOT / "workspace/private"
DEFAULT_RUN_BASE = wsta3.DEFAULT_RUN_BASE
DEFAULT_WSTA168_COMMAND_JSON = wsta171.DEFAULT_WSTA168_COMMAND_JSON
DEFAULT_WSTA168_COMMAND_SH = wsta171.DEFAULT_WSTA168_COMMAND_SH
PASS_DECISION = "wsta172-seccomp-fresh-execute-preflight-pass"
SUMMARY_NAME = "wsta172_result.json"


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


def safety_flags() -> dict[str, Any]:
    return {
        "device_action": "read-only-status-only",
        "boot_flash": False,
        "native_reboot": False,
        "wifi_connect": False,
        "dhcp": False,
        "public_tunnel": False,
        "public_smoke": False,
        "packet_filter_mutation": False,
        "userdata_touch": False,
        "switch_root": False,
        "wsta170_execute_command_generated": False,
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
        "fresh_readiness": result.get("fresh_readiness", {}),
        "source_gate": result.get("source_gate", {}),
        "execute_preflight": result.get("execute_preflight", {}),
        "checks": result.get("checks", {}),
        "safety": result.get("safety", {}),
    }


def wsta169_args(run_dir: Path, command_json: Path, command_sh: Path, timeout: float) -> argparse.Namespace:
    return argparse.Namespace(
        run_id="wsta172-fresh-wsta169-readiness",
        run_dir=run_dir,
        wsta168_command_json=command_json,
        wsta168_command_sh=command_sh,
        timeout=timeout,
        emit_seccomp_live_readiness_readonly=True,
        print_full_json=False,
    )


def wsta170_args(
    run_dir: Path,
    readiness_json: Path,
    command_json: Path,
    command_sh: Path,
    execution_timeout: float,
) -> argparse.Namespace:
    return argparse.Namespace(
        run_id="wsta172-fresh-wsta170-source-gate",
        run_dir=run_dir,
        wsta169_readiness_json=readiness_json,
        wsta168_command_json=command_json,
        wsta168_command_sh=command_sh,
        execution_timeout=execution_timeout,
        execute_wsta170_no_load_live_observation=False,
        allow_wsta168_command_execution=False,
        ack_readiness_proof_current=False,
        ack_no_correct_wsta161_token=False,
        ack_no_seccomp_load=False,
        ack_cleanup_required=False,
        print_full_json=False,
    )


def wsta171_args(
    run_dir: Path,
    source_gate_json: Path,
    readiness_json: Path,
    command_json: Path,
    command_sh: Path,
    execution_timeout: float,
) -> argparse.Namespace:
    return argparse.Namespace(
        run_id="wsta172-fresh-wsta171-execute-preflight",
        run_dir=run_dir,
        wsta170_source_gate_json=source_gate_json,
        wsta169_readiness_json=readiness_json,
        wsta168_command_json=command_json,
        wsta168_command_sh=command_sh,
        execution_timeout=execution_timeout,
        emit_wsta170_execute_preflight=True,
        print_full_json=False,
    )


def validate_fresh_readiness(result: dict[str, Any], command_json: Path, command_sh: Path) -> dict[str, bool]:
    checks = result.get("checks", {})
    safety = result.get("safety", {})
    return {
        "decision_pass": result.get("decision") == wsta169.PASS_DECISION,
        "command_ready": checks.get("command_ready") is True,
        "bridge_ready": checks.get("bridge_ready") is True,
        "version_ok": checks.get("version_ok") is True,
        "status_ok": checks.get("status_ok") is True,
        "selftest_fail_zero": checks.get("selftest_fail_zero") is True,
        "wsta168_json_path_matches": result.get("wsta168_command_json") == rel(command_json),
        "wsta168_sh_path_matches": result.get("wsta168_command_sh") == rel(command_sh),
        "no_live_execution": safety.get("live_command_executed") is False,
        "no_seccomp_load": safety.get("seccomp_filter_loaded") is False,
        "no_seccomp_enforce": safety.get("seccomp_enforced") is False,
        "no_correct_token": safety.get("correct_wsta161_token_supplied") is False,
    }


def validate_source_gate(result: dict[str, Any], readiness_json: Path, command_json: Path, command_sh: Path) -> dict[str, bool]:
    checks = result.get("checks", {})
    safety = result.get("safety", {})
    return {
        "decision_is_explicit_gate_block": (
            result.get("decision") == "wsta170-blocked-explicit-execution-gate-required"
        ),
        "readiness_proof_valid": checks.get("readiness_proof_valid") is True,
        "command_ready": checks.get("command_ready") is True,
        "wsta169_path_matches": result.get("wsta169_readiness_json") == rel(readiness_json),
        "wsta168_json_path_matches": result.get("wsta168_command_json") == rel(command_json),
        "wsta168_sh_path_matches": result.get("wsta168_command_sh") == rel(command_sh),
        "no_device_action": safety.get("device_action") is False,
        "no_live_execution": safety.get("live_command_executed") is False,
        "no_seccomp_load": safety.get("seccomp_filter_loaded") is False,
        "no_seccomp_enforce": safety.get("seccomp_enforced") is False,
        "no_correct_token": safety.get("correct_wsta161_token_supplied") is False,
    }


def validate_execute_preflight(
    result: dict[str, Any],
    source_gate_json: Path,
    readiness_json: Path,
    command_json: Path,
    command_sh: Path,
) -> dict[str, bool]:
    checks = result.get("checks", {})
    safety = result.get("safety", {})
    command = result.get("command", {})
    return {
        "decision_pass": result.get("decision") == wsta171.PASS_DECISION,
        "source_gate_valid": checks.get("source_gate_valid") is True,
        "readiness_valid": checks.get("readiness_valid") is True,
        "wsta168_command_valid": checks.get("wsta168_command_valid") is True,
        "execution_command_valid": checks.get("execution_command_valid") is True,
        "source_gate_path_matches": result.get("wsta170_source_gate_json") == rel(source_gate_json),
        "wsta169_path_matches": result.get("wsta169_readiness_json") == rel(readiness_json),
        "wsta168_json_path_matches": result.get("wsta168_command_json") == rel(command_json),
        "wsta168_sh_path_matches": result.get("wsta168_command_sh") == rel(command_sh),
        "command_ready_not_executed": command.get("state") == "READY_TO_RUN_NOT_EXECUTED",
        "command_not_executed": command.get("executed") is False,
        "no_live_execution": safety.get("live_command_executed") is False,
        "no_seccomp_load": safety.get("seccomp_filter_loaded") is False,
        "no_seccomp_enforce": safety.get("seccomp_enforced") is False,
        "no_correct_token": safety.get("correct_wsta161_token_supplied") is False,
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    ts = utc_stamp()
    run_id = args.run_id or f"wsta172-seccomp-fresh-execute-preflight-{ts}"
    run_dir = resolve_path(args.run_dir or (DEFAULT_RUN_BASE / run_id))
    command_json = resolve_path(args.wsta168_command_json)
    command_sh = resolve_path(args.wsta168_command_sh)
    result: dict[str, Any] = {
        "scope": "WSTA172 fresh WSTA170 execution preflight bundle",
        "started_utc": ts,
        "run_dir": rel(run_dir),
        "wsta168_command_json": rel(command_json),
        "wsta168_command_sh": rel(command_sh),
        "safety": safety_flags(),
        "checks": {
            "explicit_bundle_gate": bool(args.emit_fresh_wsta170_execute_preflight),
            "private_run_dir": wsta160.is_under(run_dir, PRIVATE_ROOT),
            "wsta168_command_json_private": wsta160.is_under(command_json, PRIVATE_ROOT),
            "wsta168_command_sh_private": wsta160.is_under(command_sh, PRIVATE_ROOT),
            "wsta168_command_json_present": command_json.is_file(),
            "wsta168_command_sh_present": command_sh.is_file(),
        },
    }
    if not result["checks"]["private_run_dir"]:
        result["decision"] = "wsta172-blocked-nonprivate-run-dir"
        result["gate_decision"] = result["decision"]
        result["ended_utc"] = utc_stamp()
        return result
    run_dir.mkdir(parents=True, exist_ok=True)
    out_path = run_dir / SUMMARY_NAME

    for key, decision in (
        ("explicit_bundle_gate", "wsta172-blocked-explicit-bundle-gate-required"),
        ("wsta168_command_json_private", "wsta172-blocked-wsta168-command-json-nonprivate"),
        ("wsta168_command_sh_private", "wsta172-blocked-wsta168-command-sh-nonprivate"),
        ("wsta168_command_json_present", "wsta172-blocked-wsta168-command-json-missing"),
        ("wsta168_command_sh_present", "wsta172-blocked-wsta168-command-sh-missing"),
    ):
        if not result["checks"][key]:
            result["decision"] = decision
            result["gate_decision"] = decision
            result["ended_utc"] = utc_stamp()
            write_json(out_path, result)
            return result

    readiness_dir = run_dir / "wsta169-readiness"
    source_gate_dir = run_dir / "wsta170-source-gate"
    preflight_dir = run_dir / "wsta171-execute-preflight"
    readiness_result = wsta169.run(wsta169_args(readiness_dir, command_json, command_sh, args.readiness_timeout))
    readiness_json = readiness_dir / wsta169.SUMMARY_NAME
    result["fresh_readiness"] = {
        "run_dir": rel(readiness_dir),
        "result_json": rel(readiness_json),
        "decision": readiness_result.get("decision"),
    }
    result["fresh_readiness_checks"] = validate_fresh_readiness(readiness_result, command_json, command_sh)
    result["checks"]["fresh_readiness_valid"] = all(result["fresh_readiness_checks"].values())
    write_json(out_path, result)
    if not result["checks"]["fresh_readiness_valid"]:
        result["decision"] = "wsta172-blocked-fresh-readiness-invalid"
        result["gate_decision"] = result["decision"]
        result["ended_utc"] = utc_stamp()
        write_json(out_path, result)
        return result

    source_result = wsta170.run(
        wsta170_args(source_gate_dir, readiness_json, command_json, command_sh, args.execution_timeout)
    )
    source_gate_json = source_gate_dir / wsta170.SUMMARY_NAME
    result["source_gate"] = {
        "run_dir": rel(source_gate_dir),
        "result_json": rel(source_gate_json),
        "decision": source_result.get("decision"),
    }
    result["source_gate_checks"] = validate_source_gate(source_result, readiness_json, command_json, command_sh)
    result["checks"]["source_gate_valid"] = all(result["source_gate_checks"].values())
    write_json(out_path, result)
    if not result["checks"]["source_gate_valid"]:
        result["decision"] = "wsta172-blocked-source-gate-invalid"
        result["gate_decision"] = result["decision"]
        result["ended_utc"] = utc_stamp()
        write_json(out_path, result)
        return result

    preflight_result = wsta171.run(
        wsta171_args(preflight_dir, source_gate_json, readiness_json, command_json, command_sh, args.execution_timeout)
    )
    result["execute_preflight"] = {
        "run_dir": rel(preflight_dir),
        "result_json": rel(preflight_dir / wsta171.SUMMARY_NAME),
        "decision": preflight_result.get("decision"),
        "command_json": preflight_result.get("command", {}).get("command_json"),
        "command_script": preflight_result.get("command", {}).get("command_script"),
        "command_state": preflight_result.get("command", {}).get("state"),
        "executed": preflight_result.get("command", {}).get("executed"),
    }
    result["execute_preflight_checks"] = validate_execute_preflight(
        preflight_result,
        source_gate_json,
        readiness_json,
        command_json,
        command_sh,
    )
    result["checks"]["execute_preflight_valid"] = all(result["execute_preflight_checks"].values())
    result["safety"]["wsta170_execute_command_generated"] = result["checks"]["execute_preflight_valid"]
    all_ok = all(
        result["checks"][key]
        for key in ("fresh_readiness_valid", "source_gate_valid", "execute_preflight_valid")
    )
    result["decision"] = PASS_DECISION if all_ok else "wsta172-blocked-execute-preflight-invalid"
    result["gate_decision"] = "ok" if result["decision"] == PASS_DECISION else result["decision"]
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
    parser.add_argument("--emit-fresh-wsta170-execute-preflight", action="store_true")
    parser.add_argument("--print-full-json", action="store_true")
    return parser


def main_with_args(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        result = run(args)
    except Exception as exc:  # noqa: BLE001
        payload = {"decision": "wsta172-runner-error", "error": str(exc)}
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1
    payload = result if args.print_full_json else public_summary(result)
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result.get("decision") == PASS_DECISION else 2


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
