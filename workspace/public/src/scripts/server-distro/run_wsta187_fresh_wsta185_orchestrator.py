#!/usr/bin/env python3
"""WSTA187 fresh WSTA185 no-load live orchestrator.

Builds the fresh WSTA execution sequence in one bounded run:

  WSTA177 source gate -> WSTA178 rebased packet -> WSTA180 bundle ->
  WSTA184 expiring handoff -> WSTA185 source gate or execution.

By default it is inert unless the explicit prepare gate is supplied.  With only
the prepare gate it stops at the WSTA185 source gate.  The full WSTA187
acknowledgement set is required to execute WSTA185.
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
import run_wsta177_seccomp_one_shot_execute_gate as wsta177  # noqa: E402
import run_wsta178_seccomp_one_shot_execute_preflight as wsta178  # noqa: E402
import run_wsta180_seccomp_live_handoff_bundle as wsta180  # noqa: E402
import run_wsta184_seccomp_expiring_execute_handoff as wsta184  # noqa: E402
import run_wsta185_seccomp_expiring_handoff_execute_gate as wsta185  # noqa: E402


REPO_ROOT = wsta3.REPO_ROOT
PRIVATE_ROOT = REPO_ROOT / "workspace/private"
DEFAULT_RUN_BASE = wsta3.DEFAULT_RUN_BASE
DEFAULT_WSTA168_COMMAND_JSON = wsta177.DEFAULT_WSTA168_COMMAND_JSON
DEFAULT_WSTA168_COMMAND_SH = wsta177.DEFAULT_WSTA168_COMMAND_SH
PASS_DECISION = "wsta187-fresh-wsta185-orchestrator-pass"
SUMMARY_NAME = "wsta187_result.json"


def rel(path: Path) -> str:
    return wsta3.rel(path)


def utc_stamp() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def resolve_path(path: Path | str) -> Path:
    path_obj = path if isinstance(path, Path) else Path(path)
    return path_obj if path_obj.is_absolute() else REPO_ROOT / path_obj


def write_json(path: Path, payload: Any) -> None:
    wsta3.write_json(path, payload)


def explicit_execution_gate(args: argparse.Namespace) -> tuple[bool, str]:
    if not args.prepare_wsta187_fresh_orchestrator:
        return False, "wsta187-blocked-explicit-prepare-gate-required"
    if not args.execute_wsta187_fresh_orchestrator:
        return False, "wsta187-blocked-explicit-execution-gate-required"
    if not args.allow_wsta185_handoff_execution:
        return False, "wsta187-blocked-wsta185-handoff-execution-allow-required"
    if not args.ack_fresh_sequence:
        return False, "wsta187-blocked-fresh-sequence-ack-required"
    if not args.ack_no_correct_wsta161_token:
        return False, "wsta187-blocked-no-correct-token-ack-required"
    if not args.ack_no_seccomp_load:
        return False, "wsta187-blocked-no-seccomp-load-ack-required"
    if not args.ack_cleanup_required:
        return False, "wsta187-blocked-cleanup-ack-required"
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
        "wsta177_source_gate_generated": False,
        "wsta178_execute_command_generated": False,
        "wsta180_handoff_bundle_generated": False,
        "wsta184_expiring_handoff_generated": False,
        "wsta185_source_gate_validated": False,
        "wsta185_execute_command_executed": False,
        "wsta181_execute_command_executed": False,
        "wsta178_execute_command_executed": False,
        "wsta177_execute_command_executed": False,
        "wsta175_execute_command_executed": False,
        "wsta170_execute_command_executed": False,
        "post_run_audit_executed": False,
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
        "stages": result.get("stages", {}),
        "checks": result.get("checks", {}),
        "safety": result.get("safety", {}),
    }


def wsta177_args(args: argparse.Namespace, run_dir: Path, command_json: Path, command_sh: Path) -> argparse.Namespace:
    return argparse.Namespace(
        run_id="wsta187-wsta177-source-gate",
        run_dir=run_dir,
        wsta168_command_json=command_json,
        wsta168_command_sh=command_sh,
        readiness_timeout=args.readiness_timeout,
        execution_timeout=args.execution_timeout,
        max_age_sec=args.max_age_sec,
        prepare_wsta177_one_shot=True,
        execute_wsta177_one_shot=False,
        allow_wsta175_command_execution=False,
        ack_fresh_preflight=False,
        ack_no_correct_wsta161_token=False,
        ack_no_seccomp_load=False,
        ack_cleanup_required=False,
        print_full_json=False,
    )


def wsta178_args(
    args: argparse.Namespace,
    run_dir: Path,
    source_gate_json: Path,
    command_json: Path,
    command_sh: Path,
) -> argparse.Namespace:
    return argparse.Namespace(
        run_id="wsta187-wsta178-preflight",
        run_dir=run_dir,
        wsta177_source_gate_json=source_gate_json,
        wsta168_command_json=command_json,
        wsta168_command_sh=command_sh,
        readiness_timeout=args.readiness_timeout,
        execution_timeout=args.execution_timeout,
        max_age_sec=args.max_age_sec,
        emit_wsta177_execute_preflight=True,
        print_full_json=False,
    )


def wsta180_args(args: argparse.Namespace, run_dir: Path, command_json: Path, command_sh: Path) -> argparse.Namespace:
    del args
    return argparse.Namespace(
        run_id="wsta187-wsta180-bundle",
        run_dir=run_dir,
        wsta178_command_json=command_json,
        wsta178_command_sh=command_sh,
        emit_wsta180_handoff_bundle=True,
        print_full_json=False,
    )


def wsta184_args(args: argparse.Namespace, run_dir: Path, bundle_json: Path, bundle_sh: Path) -> argparse.Namespace:
    return argparse.Namespace(
        run_id="wsta187-wsta184-expiring-handoff",
        run_dir=run_dir,
        wsta180_bundle_json=bundle_json,
        wsta180_bundle_sh=bundle_sh,
        execution_timeout=args.execution_timeout,
        audit_timeout=args.audit_timeout,
        max_age_sec=args.max_age_sec,
        emit_expiring_handoff=True,
        print_full_json=False,
    )


def wsta185_args(args: argparse.Namespace, run_dir: Path, handoff_json: Path, *, execute: bool) -> argparse.Namespace:
    return argparse.Namespace(
        run_id="wsta187-wsta185-execute" if execute else "wsta187-wsta185-source-gate",
        run_dir=run_dir,
        handoff_json=handoff_json,
        execution_timeout=args.execution_timeout,
        execute_wsta185_handoff=execute,
        allow_wsta181_command_execution=execute,
        ack_handoff_fresh=execute,
        ack_no_correct_wsta161_token=execute,
        ack_no_seccomp_load=execute,
        ack_cleanup_required=execute,
        print_full_json=False,
    )


def validate_wsta177_source(result: dict[str, Any]) -> dict[str, bool]:
    checks = result.get("checks", {})
    safety = result.get("safety", {})
    return {
        "decision_is_execution_gate_block": result.get("decision") == "wsta177-blocked-explicit-execution-gate-required",
        "fresh_preflight_valid": checks.get("fresh_preflight_valid") is True,
        "execution_command_valid": checks.get("execution_command_valid") is True,
        "no_live_execution": safety.get("live_command_executed") is False,
        "no_wsta175_execution": safety.get("wsta175_execute_command_executed") is False,
        "no_wsta170_execution": safety.get("wsta170_execute_command_executed") is False,
        "no_seccomp_load": safety.get("seccomp_filter_loaded") is False,
        "no_seccomp_enforce": safety.get("seccomp_enforced") is False,
        "no_correct_token": safety.get("correct_wsta161_token_supplied") is False,
    }


def validate_wsta178_preflight(result: dict[str, Any]) -> dict[str, bool]:
    checks = result.get("checks", {})
    command = result.get("command", {})
    rebased = result.get("rebased_wsta168_command", {})
    safety = result.get("safety", {})
    return {
        "decision_pass": result.get("decision") == wsta178.PASS_DECISION,
        "source_gate_valid": checks.get("source_gate_valid") is True,
        "rebased_wsta168_command_valid": checks.get("rebased_wsta168_command_valid") is True,
        "execution_command_valid": checks.get("execution_command_valid") is True,
        "command_json_present": bool(command.get("command_json") and resolve_path(command["command_json"]).is_file()),
        "command_script_present": bool(command.get("command_script") and resolve_path(command["command_script"]).is_file()),
        "rebased_run_dir_present": bool(rebased.get("wsta167_run_dir")),
        "no_live_execution": safety.get("live_command_executed") is False,
        "no_seccomp_load": safety.get("seccomp_filter_loaded") is False,
    }


def validate_wsta180_bundle(result: dict[str, Any]) -> dict[str, bool]:
    checks = result.get("checks", {})
    bundle = result.get("bundle", {})
    safety = result.get("safety", {})
    return {
        "decision_pass": result.get("decision") == wsta180.PASS_DECISION,
        "pre_run_missing_result": checks.get("pre_run_audit_missing_result") is True,
        "execution_packet_valid": checks.get("execution_packet_valid") is True,
        "post_run_audit_command_valid": checks.get("post_run_audit_command_valid") is True,
        "bundle_valid": checks.get("bundle_valid") is True,
        "bundle_json_present": bool(bundle.get("bundle_json") and resolve_path(bundle["bundle_json"]).is_file()),
        "bundle_script_present": bool(bundle.get("operator_commands_script") and resolve_path(bundle["operator_commands_script"]).is_file()),
        "no_live_execution": safety.get("live_command_executed") is False,
        "no_seccomp_load": safety.get("seccomp_filter_loaded") is False,
    }


def validate_wsta184_handoff(result: dict[str, Any]) -> dict[str, bool]:
    checks = result.get("checks", {})
    handoff = result.get("handoff", {})
    safety = result.get("safety", {})
    return {
        "decision_pass": result.get("decision") == wsta184.PASS_DECISION,
        "fresh_readiness_valid": checks.get("fresh_readiness_valid") is True,
        "freshness_valid": checks.get("freshness_valid") is True,
        "readiness_valid": checks.get("readiness_valid") is True,
        "command_valid": checks.get("command_valid") is True,
        "handoff_present": bool(handoff.get("handoff_json") and resolve_path(handoff["handoff_json"]).is_file()),
        "handoff_not_executed": handoff.get("executed") is False,
        "no_live_execution": safety.get("live_command_executed") is False,
        "no_seccomp_load": safety.get("seccomp_filter_loaded") is False,
    }


def validate_wsta185_source(result: dict[str, Any]) -> dict[str, bool]:
    checks = result.get("checks", {})
    safety = result.get("safety", {})
    return {
        "decision_is_execution_gate_block": result.get("decision") == "wsta185-blocked-explicit-execution-gate-required",
        "handoff_valid": checks.get("handoff_valid") is True,
        "command_artifacts_valid": checks.get("command_artifacts_valid") is True,
        "freshness_valid": checks.get("freshness_valid") is True,
        "no_live_execution": safety.get("live_command_executed") is False,
        "no_wsta181_execution": safety.get("wsta181_execute_command_executed") is False,
        "no_seccomp_load": safety.get("seccomp_filter_loaded") is False,
        "no_seccomp_enforce": safety.get("seccomp_enforced") is False,
        "no_correct_token": safety.get("correct_wsta161_token_supplied") is False,
    }


def validate_wsta185_execution(result: dict[str, Any]) -> dict[str, bool]:
    checks = result.get("checks", {})
    safety = result.get("safety", {})
    nested = result.get("wsta181_result", {})
    deep = nested.get("deep_audit", {}) if isinstance(nested, dict) else {}
    return {
        "decision_pass": result.get("decision") == wsta185.PASS_DECISION,
        "execution_returncode_ok": checks.get("execution_returncode_ok") is True,
        "wsta181_result_valid": checks.get("wsta181_result_valid") is True,
        "wsta181_decision_pass": nested.get("decision") == wsta185.wsta181.PASS_DECISION,
        "post_run_audit_decision_pass": nested.get("post_run_audit_decision") == wsta185.wsta181.wsta179.PASS_DECISION,
        "deep_wsta167_pass": deep.get("wsta167_decision_pass") is True,
        "deep_wsta170_pass": deep.get("wsta170_decision_pass") is True,
        "deep_wsta175_pass": deep.get("wsta175_decision_pass") is True,
        "wsta181_executed": safety.get("wsta181_execute_command_executed") is True,
        "wsta178_executed": safety.get("wsta178_execute_command_executed") is True,
        "wsta177_executed": safety.get("wsta177_execute_command_executed") is True,
        "wsta175_executed": safety.get("wsta175_execute_command_executed") is True,
        "wsta170_executed": safety.get("wsta170_execute_command_executed") is True,
        "no_flash": safety.get("boot_flash") is False,
        "no_reboot": safety.get("native_reboot") is False,
        "no_wifi": safety.get("wifi_connect") is False,
        "no_dhcp": safety.get("dhcp") is False,
        "no_public_tunnel": safety.get("public_tunnel") is False,
        "no_packet_filter_mutation": safety.get("packet_filter_mutation") is False,
        "no_seccomp_load": safety.get("seccomp_filter_loaded") is False,
        "no_seccomp_enforce": safety.get("seccomp_enforced") is False,
        "no_correct_token": safety.get("correct_wsta161_token_supplied") is False,
    }


def validate_wsta185_preexecution(result: dict[str, Any]) -> dict[str, bool]:
    checks = result.get("checks", {})
    return {
        "handoff_valid": checks.get("handoff_valid") is True,
        "command_artifacts_valid": checks.get("command_artifacts_valid") is True,
        "freshness_valid": checks.get("freshness_valid") is True,
    }


def classify(result: dict[str, Any]) -> str:
    checks = result.get("checks", {})
    ordered = (
        ("explicit_prepare_gate", "wsta187-blocked-explicit-prepare-gate-required"),
        ("wsta177_source_valid", "wsta187-blocked-wsta177-source-invalid"),
        ("wsta178_preflight_valid", "wsta187-blocked-wsta178-preflight-invalid"),
        ("wsta180_bundle_valid", "wsta187-blocked-wsta180-bundle-invalid"),
        ("wsta184_handoff_valid", "wsta187-blocked-wsta184-handoff-invalid"),
        ("wsta185_source_valid", "wsta187-blocked-wsta185-source-invalid"),
        ("explicit_execution_gate", result.get("gate_decision") or "wsta187-blocked-explicit-execution-gate-required"),
        ("wsta185_execution_valid", "wsta187-blocked-wsta185-execution-invalid"),
    )
    for key, decision in ordered:
        if not checks.get(key):
            return str(decision)
    return PASS_DECISION


def _stage_summary(path: Path, result: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_dir": rel(path),
        "result_json": rel(path / result_name_for(result)),
        "decision": result.get("decision"),
    }


def result_name_for(result: dict[str, Any]) -> str:
    scope = str(result.get("scope", ""))
    if "WSTA185" in scope:
        return wsta185.SUMMARY_NAME
    if "WSTA184" in scope:
        return wsta184.SUMMARY_NAME
    if "WSTA180" in scope:
        return wsta180.SUMMARY_NAME
    if "WSTA178" in scope:
        return wsta178.SUMMARY_NAME
    if "WSTA177" in scope:
        return wsta177.SUMMARY_NAME
    return "result.json"


def run(args: argparse.Namespace) -> dict[str, Any]:
    ts = utc_stamp()
    run_id = args.run_id or f"wsta187-fresh-wsta185-orchestrator-{ts}"
    run_dir = resolve_path(args.run_dir or (DEFAULT_RUN_BASE / run_id))
    wsta168_command_json = resolve_path(args.wsta168_command_json)
    wsta168_command_sh = resolve_path(args.wsta168_command_sh)
    gate_ok, gate_decision = explicit_execution_gate(args)
    result: dict[str, Any] = {
        "scope": "WSTA187 fresh WSTA185 no-load live orchestrator",
        "started_utc": ts,
        "run_dir": rel(run_dir),
        "wsta168_command_json": rel(wsta168_command_json),
        "wsta168_command_sh": rel(wsta168_command_sh),
        "gate_decision": gate_decision,
        "safety": safety_flags(gate_ok),
        "stages": {},
        "checks": {
            "explicit_prepare_gate": bool(args.prepare_wsta187_fresh_orchestrator),
            "explicit_execution_gate": gate_ok,
            "private_run_dir": wsta160.is_under(run_dir, PRIVATE_ROOT),
            "wsta168_command_json_private": wsta160.is_under(wsta168_command_json, PRIVATE_ROOT),
            "wsta168_command_sh_private": wsta160.is_under(wsta168_command_sh, PRIVATE_ROOT),
            "wsta168_command_json_present": wsta168_command_json.is_file(),
            "wsta168_command_sh_present": wsta168_command_sh.is_file(),
        },
    }
    if not result["checks"]["private_run_dir"]:
        result["decision"] = "wsta187-blocked-nonprivate-run-dir"
        result["ended_utc"] = utc_stamp()
        return result
    run_dir.mkdir(parents=True, exist_ok=True)
    out_path = run_dir / SUMMARY_NAME
    for key, decision in (
        ("explicit_prepare_gate", "wsta187-blocked-explicit-prepare-gate-required"),
        ("wsta168_command_json_private", "wsta187-blocked-wsta168-command-json-nonprivate"),
        ("wsta168_command_sh_private", "wsta187-blocked-wsta168-command-sh-nonprivate"),
        ("wsta168_command_json_present", "wsta187-blocked-wsta168-command-json-missing"),
        ("wsta168_command_sh_present", "wsta187-blocked-wsta168-command-sh-missing"),
    ):
        if not result["checks"][key]:
            result["decision"] = decision
            result["ended_utc"] = utc_stamp()
            write_json(out_path, result)
            return result

    w177_dir = run_dir / "wsta177-source-gate"
    w177_result = wsta177.run(wsta177_args(args, w177_dir, wsta168_command_json, wsta168_command_sh))
    result["stages"]["wsta177_source_gate"] = _stage_summary(w177_dir, w177_result)
    result["wsta177_source_checks"] = validate_wsta177_source(w177_result)
    result["checks"]["wsta177_source_valid"] = all(result["wsta177_source_checks"].values())
    result["safety"]["wsta177_source_gate_generated"] = result["checks"]["wsta177_source_valid"]
    write_json(out_path, result)
    if not result["checks"]["wsta177_source_valid"]:
        result["decision"] = classify(result)
        result["ended_utc"] = utc_stamp()
        write_json(out_path, result)
        return result

    w178_dir = run_dir / "wsta178-one-shot-preflight"
    w178_result = wsta178.run(
        wsta178_args(args, w178_dir, w177_dir / wsta177.SUMMARY_NAME, wsta168_command_json, wsta168_command_sh)
    )
    result["stages"]["wsta178_preflight"] = _stage_summary(w178_dir, w178_result)
    result["stages"]["wsta178_preflight"]["command_json"] = w178_result.get("command", {}).get("command_json")
    result["stages"]["wsta178_preflight"]["command_script"] = w178_result.get("command", {}).get("command_script")
    result["stages"]["wsta178_preflight"]["rebased_wsta167_run_dir"] = (
        w178_result.get("rebased_wsta168_command", {}).get("wsta167_run_dir")
    )
    result["wsta178_preflight_checks"] = validate_wsta178_preflight(w178_result)
    result["checks"]["wsta178_preflight_valid"] = all(result["wsta178_preflight_checks"].values())
    result["safety"]["wsta178_execute_command_generated"] = result["checks"]["wsta178_preflight_valid"]
    write_json(out_path, result)
    if not result["checks"]["wsta178_preflight_valid"]:
        result["decision"] = classify(result)
        result["ended_utc"] = utc_stamp()
        write_json(out_path, result)
        return result

    command_json = resolve_path(w178_result["command"]["command_json"])
    command_sh = resolve_path(w178_result["command"]["command_script"])
    w180_dir = run_dir / "wsta180-live-handoff-bundle"
    w180_result = wsta180.run(wsta180_args(args, w180_dir, command_json, command_sh))
    result["stages"]["wsta180_bundle"] = _stage_summary(w180_dir, w180_result)
    result["stages"]["wsta180_bundle"]["bundle_json"] = w180_result.get("bundle", {}).get("bundle_json")
    result["stages"]["wsta180_bundle"]["bundle_script"] = w180_result.get("bundle", {}).get("operator_commands_script")
    result["wsta180_bundle_checks"] = validate_wsta180_bundle(w180_result)
    result["checks"]["wsta180_bundle_valid"] = all(result["wsta180_bundle_checks"].values())
    result["safety"]["wsta180_handoff_bundle_generated"] = result["checks"]["wsta180_bundle_valid"]
    write_json(out_path, result)
    if not result["checks"]["wsta180_bundle_valid"]:
        result["decision"] = classify(result)
        result["ended_utc"] = utc_stamp()
        write_json(out_path, result)
        return result

    bundle_json = resolve_path(w180_result["bundle"]["bundle_json"])
    bundle_sh = resolve_path(w180_result["bundle"]["operator_commands_script"])
    w184_dir = run_dir / "wsta184-expiring-handoff"
    w184_result = wsta184.run(wsta184_args(args, w184_dir, bundle_json, bundle_sh))
    result["stages"]["wsta184_handoff"] = _stage_summary(w184_dir, w184_result)
    result["stages"]["wsta184_handoff"]["handoff_json"] = w184_result.get("handoff", {}).get("handoff_json")
    result["stages"]["wsta184_handoff"]["expires_utc"] = w184_result.get("handoff", {}).get("expires_utc")
    result["wsta184_handoff_checks"] = validate_wsta184_handoff(w184_result)
    result["checks"]["wsta184_handoff_valid"] = all(result["wsta184_handoff_checks"].values())
    result["safety"]["wsta184_expiring_handoff_generated"] = result["checks"]["wsta184_handoff_valid"]
    write_json(out_path, result)
    if not result["checks"]["wsta184_handoff_valid"]:
        result["decision"] = classify(result)
        result["ended_utc"] = utc_stamp()
        write_json(out_path, result)
        return result

    handoff_json = resolve_path(w184_result["handoff"]["handoff_json"])
    w185_dir = run_dir / ("wsta185-live-run" if gate_ok else "wsta185-source-gate")
    w185_result = wsta185.run(wsta185_args(args, w185_dir, handoff_json, execute=gate_ok))
    result["stages"]["wsta185"] = _stage_summary(w185_dir, w185_result)
    result["stages"]["wsta185"]["wsta181_result_json"] = w185_result.get("handoff", {}).get("wsta181_result_json")
    result["wsta185_source_checks"] = (
        validate_wsta185_preexecution(w185_result) if gate_ok else validate_wsta185_source(w185_result)
    )
    result["checks"]["wsta185_source_valid"] = all(result["wsta185_source_checks"].values())
    result["safety"]["wsta185_source_gate_validated"] = True
    if gate_ok:
        result["wsta185_execution_checks"] = validate_wsta185_execution(w185_result)
        result["checks"]["wsta185_execution_valid"] = all(result["wsta185_execution_checks"].values())
        for key in (
            "wsta181_execute_command_executed",
            "wsta178_execute_command_executed",
            "wsta177_execute_command_executed",
            "wsta175_execute_command_executed",
            "wsta170_execute_command_executed",
            "post_run_audit_executed",
            "live_command_executed",
        ):
            result["safety"][key] = bool(w185_result.get("safety", {}).get(key) is True)
        result["safety"]["wsta185_execute_command_executed"] = True
        result["safety"]["device_action"] = w185_result.get("safety", {}).get("device_action") or True
    else:
        result["checks"]["wsta185_execution_valid"] = False
        result["wsta185_execution_checks"] = {}
    write_json(out_path, result)
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
    parser.add_argument("--audit-timeout", type=float, default=1800.0)
    parser.add_argument("--max-age-sec", type=int, default=900)
    parser.add_argument("--prepare-wsta187-fresh-orchestrator", action="store_true")
    parser.add_argument("--execute-wsta187-fresh-orchestrator", action="store_true")
    parser.add_argument("--allow-wsta185-handoff-execution", action="store_true")
    parser.add_argument("--ack-fresh-sequence", action="store_true")
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
        payload = {"decision": "wsta187-runner-error", "error": str(exc)}
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1
    payload = result if args.print_full_json else public_summary(result)
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result.get("decision") == PASS_DECISION else 2


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
