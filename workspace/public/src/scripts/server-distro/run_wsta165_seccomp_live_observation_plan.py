#!/usr/bin/env python3
"""WSTA165 host-only seccomp live-observation plan.

Consumes the WSTA164 chroot proof and emits a structured plan for the later
device-side observation of the staged apply/load-env gates.  This unit does not
contact the device and never includes the correct WSTA161 load token in the
plan.  It only records the expected no-load observations and stop conditions.
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

import prepare_wsta3_sta_rootfs as wsta3  # noqa: E402
import run_wsta160_seccomp_full_rootfs_chroot_dry_run as wsta160  # noqa: E402
import run_wsta164_seccomp_load_env_contract_chroot_proof as wsta164  # noqa: E402


REPO_ROOT = wsta3.REPO_ROOT
PRIVATE_ROOT = REPO_ROOT / "workspace/private"
DEFAULT_RUN_BASE = wsta3.DEFAULT_RUN_BASE
DEFAULT_WSTA164_PROOF = (
    DEFAULT_RUN_BASE
    / "wsta164-seccomp-load-env-contract-chroot-proof-20260705T1329KST"
    / "wsta164_result.json"
)
PASS_DECISION = "wsta165-seccomp-live-observation-plan-pass"
SUMMARY_NAME = "wsta165_result.json"
PLAN_NAME = "wsta165_live_observation_plan.json"


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
        "host_plan_only": True,
        "seccomp_filter_loaded": False,
        "seccomp_enforced": False,
        "correct_wsta161_token_in_plan": False,
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def public_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": result.get("decision"),
        "run_dir": result.get("run_dir"),
        "gate_decision": result.get("gate_decision"),
        "proof_checks": result.get("proof_checks", {}),
        "plan": result.get("plan", {}),
        "safety": result.get("safety", {}),
    }


def proof_pass_checks(proof: dict[str, Any]) -> dict[str, bool]:
    checks = proof.get("checks", {})
    proof_checks = proof.get("proof_checks", {})
    proof_meta = proof.get("proof", {})
    return {
        "wsta164_decision_pass": proof.get("decision") == wsta164.PASS_DECISION,
        "wsta164_all_proof_checks_true": bool(proof_checks) and all(value is True for value in proof_checks.values()),
        "wsta164_launcher_has_load_gate": checks.get("launcher_has_wsta164_load_gate") is True,
        "wsta164_launcher_forwards_load_env": checks.get("launcher_forwards_load_env") is True,
        "wsta164_launcher_does_not_hardcode_token": checks.get("launcher_does_not_hardcode_wsta161_token") is True,
        "wsta164_correct_token_not_supplied": proof_meta.get("correct_wsta161_token_supplied") is False,
        "wsta164_filter_load_disabled": proof_meta.get("filter_load_enabled") is False,
        "wsta164_seccomp_not_enforced": proof_meta.get("seccomp_enforced") is False,
        "wsta164_no_gate_no_load_attempt": proof_checks.get("no_gate_no_load_attempt") is True,
        "wsta164_missing_token_no_load_attempt": proof_checks.get("missing_token_no_load_attempt") is True,
        "wsta164_wrong_token_no_load_attempt": proof_checks.get("wrong_token_no_load_attempt") is True,
    }


def observation_plan() -> dict[str, Any]:
    base_env = {
        "A90_SERVICE_LAUNCH_SECCOMP_DRY_RUN": "1",
        "A90_SERVICE_LAUNCH_SECCOMP_ENFORCE": "1",
        "A90_SERVICE_LAUNCH_SECCOMP_HELPER_MODE": "apply",
        "A90_SERVICE_LAUNCH_SECCOMP_HELPER_APPLY_GATE": "WSTA163-ALLOW-HELPER-APPLY",
    }
    return {
        "schema": "a90-wsta165-seccomp-live-observation-plan-v1",
        "state": "HOST_ONLY_PLAN_NOT_EXECUTED",
        "service": "dpublic-hud",
        "launcher_command": ["/usr/local/bin/a90-service-launch", "dpublic-hud", "/bin/true"],
        "correct_wsta161_token_supplied": False,
        "seccomp_filter_load_expected": False,
        "seccomp_enforcement_expected": False,
        "scenarios": [
            {
                "name": "no-load-env-gate",
                "env": dict(base_env),
                "expected_markers": [
                    "A90WSTA164_SECCOMP_LOAD_ENV_GATE=0",
                    "A90WSTA161_SECCOMP_LOAD=0",
                    "a90_seccomp_loader_decision=blocked-load-gate-required",
                    "a90_service_launcher_decision=blocked-seccomp-helper-apply-failed",
                ],
                "forbidden_markers": [
                    "A90WSTA161_SECCOMP_LOAD_ATTEMPT=1",
                    "a90_service_launcher_decision=exec",
                    "fake_setpriv_args=",
                ],
            },
            {
                "name": "load-env-gate-missing-token",
                "env": {
                    **base_env,
                    "A90_SERVICE_LAUNCH_SECCOMP_LOAD_GATE": "WSTA164-ALLOW-SECCOMP-LOAD-ENV",
                },
                "expected_markers": [
                    "A90WSTA164_SECCOMP_LOAD_ENV_GATE=1",
                    "a90_service_launcher_decision=blocked-seccomp-helper-load-token-required",
                ],
                "forbidden_markers": [
                    "A90WSTA161_LOADER_GATED_APPLY=1",
                    "A90WSTA161_SECCOMP_LOAD_ATTEMPT=1",
                    "a90_service_launcher_decision=exec",
                    "fake_setpriv_args=",
                ],
            },
            {
                "name": "load-env-gate-wrong-token",
                "env": {
                    **base_env,
                    "A90_SERVICE_LAUNCH_SECCOMP_LOAD_GATE": "WSTA164-ALLOW-SECCOMP-LOAD-ENV",
                    "A90_SERVICE_LAUNCH_SECCOMP_LOAD_TOKEN": "intentionally-wrong-token",
                },
                "expected_markers": [
                    "A90WSTA164_SECCOMP_LOAD_ENV_GATE=1",
                    "A90WSTA164_SECCOMP_LOAD_TOKEN_PRESENT=1",
                    "A90WSTA161_SECCOMP_LOAD=0",
                    "a90_seccomp_loader_decision=blocked-load-token-required",
                    "a90_service_launcher_decision=blocked-seccomp-helper-apply-failed",
                ],
                "forbidden_markers": [
                    "A90WSTA161_SECCOMP_LOAD_ATTEMPT=1",
                    "a90_seccomp_loader_decision=loaded",
                    "a90_service_launcher_decision=exec",
                    "fake_setpriv_args=",
                ],
            },
        ],
        "stop_conditions": [
            "any scenario prints A90WSTA161_SECCOMP_LOAD_ATTEMPT=1",
            "any scenario reaches a90_service_launcher_decision=exec",
            "any scenario omits its expected block marker",
            "any live pre/post native health check regresses",
            "operator has not supplied the separate live-observation gate",
        ],
        "forbidden_inputs": [
            "correct WSTA161 load token",
            "public tunnel gates",
            "Wi-Fi connect/DHCP gates",
            "packet-filter mutation gates",
        ],
        "secret_values_logged": 0,
    }


def validate_plan(plan: dict[str, Any]) -> dict[str, bool]:
    serialized = json.dumps(plan, sort_keys=True)
    scenario_names = [item.get("name") for item in plan.get("scenarios", [])]
    return {
        "schema_ok": plan.get("schema") == "a90-wsta165-seccomp-live-observation-plan-v1",
        "host_only_state": plan.get("state") == "HOST_ONLY_PLAN_NOT_EXECUTED",
        "three_scenarios": scenario_names == [
            "no-load-env-gate",
            "load-env-gate-missing-token",
            "load-env-gate-wrong-token",
        ],
        "correct_token_not_supplied": plan.get("correct_wsta161_token_supplied") is False,
        "filter_load_not_expected": plan.get("seccomp_filter_load_expected") is False,
        "enforcement_not_expected": plan.get("seccomp_enforcement_expected") is False,
        "load_attempt_forbidden": "A90WSTA161_SECCOMP_LOAD_ATTEMPT=1" in serialized,
        "only_wrong_token_placeholder": "intentionally-wrong-token" in serialized,
        "secret_values_logged_zero": plan.get("secret_values_logged") == 0,
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    ts = utc_stamp()
    run_id = args.run_id or f"wsta165-seccomp-live-observation-plan-{ts}"
    run_dir = resolve_path(args.run_dir or (DEFAULT_RUN_BASE / run_id))
    proof_path = resolve_path(args.wsta164_proof_json)
    result: dict[str, Any] = {
        "scope": "WSTA165 host-only seccomp live-observation plan",
        "started_utc": ts,
        "run_dir": rel(run_dir),
        "safety": safety_flags(),
        "checks": {
            "explicit_gate": bool(args.emit_seccomp_live_observation_plan),
            "private_run_dir": wsta160.is_under(run_dir, PRIVATE_ROOT),
            "wsta164_proof_private": wsta160.is_under(proof_path, PRIVATE_ROOT),
            "wsta164_proof_present": proof_path.is_file(),
        },
    }
    for key, decision in (
        ("explicit_gate", "wsta165-blocked-explicit-gate-required"),
        ("private_run_dir", "wsta165-blocked-nonprivate-run-dir"),
        ("wsta164_proof_private", "wsta165-blocked-wsta164-proof-nonprivate"),
        ("wsta164_proof_present", "wsta165-blocked-wsta164-proof-missing"),
    ):
        if not result["checks"][key]:
            result["decision"] = decision
            result["gate_decision"] = decision
            result["ended_utc"] = utc_stamp()
            if key.endswith("_present"):
                run_dir.mkdir(parents=True, exist_ok=True)
                write_json(run_dir / SUMMARY_NAME, result)
            return result

    proof = load_json(proof_path)
    proof_checks = proof_pass_checks(proof)
    plan = observation_plan()
    plan_checks = validate_plan(plan)
    result["wsta164_proof"] = rel(proof_path)
    result["proof_checks"] = proof_checks
    result["plan"] = {
        "plan_artifact": rel(run_dir / PLAN_NAME),
        "scenario_count": len(plan["scenarios"]),
        "state": plan["state"],
        "correct_wsta161_token_supplied": plan["correct_wsta161_token_supplied"],
        "seccomp_filter_load_expected": plan["seccomp_filter_load_expected"],
        "seccomp_enforcement_expected": plan["seccomp_enforcement_expected"],
    }
    result["plan_checks"] = plan_checks
    result["checks"].update({f"proof_{key}": value for key, value in proof_checks.items()})
    result["checks"].update({f"plan_{key}": value for key, value in plan_checks.items()})
    all_ok = all(proof_checks.values()) and all(plan_checks.values())
    result["decision"] = PASS_DECISION if all_ok else "wsta165-blocked-plan-invalid"
    result["gate_decision"] = "ok" if result["decision"] == PASS_DECISION else result["decision"]
    result["ended_utc"] = utc_stamp()
    run_dir.mkdir(parents=True, exist_ok=True)
    write_json(run_dir / PLAN_NAME, plan)
    write_json(run_dir / SUMMARY_NAME, result)
    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--wsta164-proof-json", type=Path, default=DEFAULT_WSTA164_PROOF)
    parser.add_argument("--emit-seccomp-live-observation-plan", action="store_true")
    parser.add_argument("--print-full-json", action="store_true")
    return parser


def main_with_args(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        result = run(args)
    except Exception as exc:  # noqa: BLE001
        payload = {"decision": "wsta165-runner-error", "error": str(exc)}
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1
    payload = result if args.print_full_json else public_summary(result)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.get("decision") == PASS_DECISION else 2


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
