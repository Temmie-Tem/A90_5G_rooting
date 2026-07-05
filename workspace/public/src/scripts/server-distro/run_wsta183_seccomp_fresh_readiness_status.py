#!/usr/bin/env python3
"""WSTA183 fresh readiness wrapper for the no-load live observation.

Runs a fresh WSTA181 source-gate check against the WSTA180 handoff bundle, then
feeds that fresh source-gate result into WSTA182 to emit the readiness/status
artifact and WSTA181 execution packet.  This unit never executes WSTA181.
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
import run_wsta181_seccomp_handoff_execute_audit_gate as wsta181  # noqa: E402
import run_wsta182_seccomp_live_readiness_status as wsta182  # noqa: E402


REPO_ROOT = wsta3.REPO_ROOT
PRIVATE_ROOT = REPO_ROOT / "workspace/private"
DEFAULT_RUN_BASE = wsta3.DEFAULT_RUN_BASE
DEFAULT_WSTA180_BUNDLE_JSON = wsta181.DEFAULT_WSTA180_BUNDLE_JSON
DEFAULT_WSTA180_BUNDLE_SH = wsta181.DEFAULT_WSTA180_BUNDLE_SH
PASS_DECISION = "wsta183-seccomp-fresh-readiness-status-pass"
SUMMARY_NAME = "wsta183_result.json"


def rel(path: Path) -> str:
    return wsta3.rel(path)


def utc_stamp() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def resolve_path(path: Path | str) -> Path:
    path_obj = path if isinstance(path, Path) else Path(path)
    return path_obj if path_obj.is_absolute() else REPO_ROOT / path_obj


def write_json(path: Path, payload: Any) -> None:
    wsta3.write_json(path, payload)


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
        "fresh_source_gate_generated": False,
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
        "fresh_source_gate": result.get("fresh_source_gate", {}),
        "readiness": result.get("readiness", {}),
        "checks": result.get("checks", {}),
        "safety": result.get("safety", {}),
    }


def wsta181_source_args(
    run_dir: Path,
    bundle_json: Path,
    bundle_sh: Path,
    execution_timeout: float,
    audit_timeout: float,
) -> argparse.Namespace:
    return argparse.Namespace(
        run_id="wsta183-wsta181-source-gate",
        run_dir=run_dir,
        wsta180_bundle_json=bundle_json,
        wsta180_bundle_sh=bundle_sh,
        execution_timeout=execution_timeout,
        audit_timeout=audit_timeout,
        execute_wsta181_handoff=False,
        allow_wsta178_command_execution=False,
        ack_handoff_ready=False,
        ack_no_correct_wsta161_token=False,
        ack_no_seccomp_load=False,
        ack_post_run_audit_required=False,
        ack_cleanup_required=False,
        print_full_json=False,
    )


def wsta182_status_args(
    run_dir: Path,
    source_gate_json: Path,
    bundle_json: Path,
    bundle_sh: Path,
    execution_timeout: float,
    audit_timeout: float,
) -> argparse.Namespace:
    return argparse.Namespace(
        run_id="wsta183-wsta182-readiness-status",
        run_dir=run_dir,
        wsta181_source_gate_json=source_gate_json,
        wsta180_bundle_json=bundle_json,
        wsta180_bundle_sh=bundle_sh,
        execution_timeout=execution_timeout,
        audit_timeout=audit_timeout,
        emit_wsta182_readiness_status=True,
        print_full_json=False,
    )


def validate_fresh_source_gate(result: dict[str, Any], bundle_json: Path, bundle_sh: Path) -> dict[str, bool]:
    checks = result.get("checks", {})
    safety = result.get("safety", {})
    return {
        "decision_is_explicit_gate_block": (
            result.get("decision") == "wsta181-blocked-explicit-execution-gate-required"
        ),
        "gate_decision_is_explicit_gate_block": (
            result.get("gate_decision") == "wsta181-blocked-explicit-execution-gate-required"
        ),
        "bundle_path_matches": result.get("wsta180_bundle_json") == rel(bundle_json),
        "bundle_script_matches": result.get("wsta180_bundle_sh") == rel(bundle_sh),
        "handoff_bundle_valid": checks.get("handoff_bundle_valid") is True,
        "execution_packet_valid": checks.get("execution_packet_valid") is True,
        "post_run_audit_command_valid": checks.get("post_run_audit_command_valid") is True,
        "no_live_execution": safety.get("live_command_executed") is False,
        "no_wsta181_execution": safety.get("wsta181_execute_command_executed") is not True,
        "no_wsta178_execution": safety.get("wsta178_execute_command_executed") is False,
        "no_wsta177_execution": safety.get("wsta177_execute_command_executed") is False,
        "no_seccomp_load": safety.get("seccomp_filter_loaded") is False,
        "no_seccomp_enforce": safety.get("seccomp_enforced") is False,
        "no_correct_token": safety.get("correct_wsta161_token_supplied") is False,
    }


def validate_readiness(result: dict[str, Any], source_gate_json: Path, bundle_json: Path, bundle_sh: Path) -> dict[str, bool]:
    checks = result.get("checks", {})
    safety = result.get("safety", {})
    command = result.get("command", {})
    status = result.get("status", {})
    return {
        "decision_pass": result.get("decision") == wsta182.PASS_DECISION,
        "source_gate_path_matches": result.get("wsta181_source_gate_json") == rel(source_gate_json),
        "bundle_path_matches": result.get("wsta180_bundle_json") == rel(bundle_json),
        "bundle_script_matches": result.get("wsta180_bundle_sh") == rel(bundle_sh),
        "source_gate_valid": checks.get("source_gate_valid") is True,
        "execution_command_valid": checks.get("execution_command_valid") is True,
        "status_ready": status.get("state") == "READY_FOR_EXPLICIT_OPERATOR_APPROVAL",
        "blocking_condition_ok": status.get("blocking_condition") == "explicit-wsta181-operator-approval-required",
        "command_ready": command.get("state") == "READY_TO_RUN_NOT_EXECUTED",
        "command_not_executed": command.get("executed") is False,
        "no_live_execution": safety.get("live_command_executed") is False,
        "no_wsta181_execution": safety.get("wsta181_execute_command_executed") is False,
        "no_wsta178_execution": safety.get("wsta178_execute_command_executed") is False,
        "no_seccomp_load": safety.get("seccomp_filter_loaded") is False,
        "no_seccomp_enforce": safety.get("seccomp_enforced") is False,
        "no_correct_token": safety.get("correct_wsta161_token_supplied") is False,
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    ts = utc_stamp()
    run_id = args.run_id or f"wsta183-seccomp-fresh-readiness-status-{ts}"
    run_dir = resolve_path(args.run_dir or (DEFAULT_RUN_BASE / run_id))
    bundle_json = resolve_path(args.wsta180_bundle_json)
    bundle_sh = resolve_path(args.wsta180_bundle_sh)
    result: dict[str, Any] = {
        "scope": "WSTA183 fresh readiness wrapper for WSTA181 no-load live observation",
        "started_utc": ts,
        "run_dir": rel(run_dir),
        "wsta180_bundle_json": rel(bundle_json),
        "wsta180_bundle_sh": rel(bundle_sh),
        "safety": safety_flags(),
        "checks": {
            "explicit_fresh_readiness_gate": bool(args.emit_wsta183_fresh_readiness),
            "private_run_dir": wsta160.is_under(run_dir, PRIVATE_ROOT),
            "bundle_json_private": wsta160.is_under(bundle_json, PRIVATE_ROOT),
            "bundle_sh_private": wsta160.is_under(bundle_sh, PRIVATE_ROOT),
            "bundle_json_present": bundle_json.is_file(),
            "bundle_sh_present": bundle_sh.is_file(),
        },
    }
    if not result["checks"]["private_run_dir"]:
        result["decision"] = "wsta183-blocked-nonprivate-run-dir"
        result["ended_utc"] = utc_stamp()
        return result
    run_dir.mkdir(parents=True, exist_ok=True)
    out_path = run_dir / SUMMARY_NAME
    for key, decision in (
        ("explicit_fresh_readiness_gate", "wsta183-blocked-explicit-fresh-readiness-gate-required"),
        ("bundle_json_private", "wsta183-blocked-bundle-json-nonprivate"),
        ("bundle_sh_private", "wsta183-blocked-bundle-sh-nonprivate"),
        ("bundle_json_present", "wsta183-blocked-bundle-json-missing"),
        ("bundle_sh_present", "wsta183-blocked-bundle-sh-missing"),
    ):
        if not result["checks"][key]:
            result["decision"] = decision
            result["ended_utc"] = utc_stamp()
            write_json(out_path, result)
            return result

    source_dir = run_dir / "fresh-wsta181-source-gate"
    source_result = wsta181.run(
        wsta181_source_args(
            source_dir,
            bundle_json,
            bundle_sh,
            args.execution_timeout,
            args.audit_timeout,
        )
    )
    source_json = source_dir / wsta181.SUMMARY_NAME
    result["fresh_source_gate"] = {
        "run_dir": rel(source_dir),
        "result_json": rel(source_json),
        "decision": source_result.get("decision"),
    }
    result["fresh_source_gate_checks"] = validate_fresh_source_gate(source_result, bundle_json, bundle_sh)
    result["checks"]["fresh_source_gate_valid"] = all(result["fresh_source_gate_checks"].values())
    result["safety"]["fresh_source_gate_generated"] = True
    write_json(out_path, result)
    if not result["checks"]["fresh_source_gate_valid"]:
        result["decision"] = "wsta183-blocked-fresh-source-gate-invalid"
        result["ended_utc"] = utc_stamp()
        write_json(out_path, result)
        return result

    readiness_dir = run_dir / "fresh-wsta182-readiness-status"
    readiness_result = wsta182.run(
        wsta182_status_args(
            readiness_dir,
            source_json,
            bundle_json,
            bundle_sh,
            args.execution_timeout,
            args.audit_timeout,
        )
    )
    result["readiness"] = {
        "run_dir": rel(readiness_dir),
        "result_json": rel(readiness_dir / wsta182.SUMMARY_NAME),
        "decision": readiness_result.get("decision"),
        "status_json": readiness_result.get("status", {}).get("status_json"),
        "command_json": readiness_result.get("command", {}).get("command_json"),
        "command_script": readiness_result.get("command", {}).get("command_script"),
        "state": readiness_result.get("status", {}).get("state"),
    }
    result["readiness_checks"] = validate_readiness(readiness_result, source_json, bundle_json, bundle_sh)
    result["checks"]["readiness_valid"] = all(result["readiness_checks"].values())
    result["safety"]["readiness_status_generated"] = result["checks"]["readiness_valid"]
    result["safety"]["wsta181_execute_command_generated"] = result["checks"]["readiness_valid"]
    result["decision"] = PASS_DECISION if result["checks"]["readiness_valid"] else "wsta183-blocked-readiness-invalid"
    result["ended_utc"] = utc_stamp()
    write_json(out_path, result)
    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--wsta180-bundle-json", type=Path, default=DEFAULT_WSTA180_BUNDLE_JSON)
    parser.add_argument("--wsta180-bundle-sh", type=Path, default=DEFAULT_WSTA180_BUNDLE_SH)
    parser.add_argument("--execution-timeout", type=float, default=1800.0)
    parser.add_argument("--audit-timeout", type=float, default=1800.0)
    parser.add_argument("--emit-wsta183-fresh-readiness", action="store_true")
    parser.add_argument("--print-full-json", action="store_true")
    return parser


def main_with_args(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        result = run(args)
    except Exception as exc:  # noqa: BLE001
        payload = {"decision": "wsta183-runner-error", "error": str(exc)}
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1
    payload = result if args.print_full_json else public_summary(result)
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result.get("decision") == PASS_DECISION else 2


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
