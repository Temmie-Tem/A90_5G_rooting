#!/usr/bin/env python3
"""WSTA168 host-only preflight for the seccomp live observation.

Consumes the WSTA167 no-live-gate proof and emits the exact command packet for
the later WSTA167 live observation.  This unit does not contact the device and
does not execute that command.
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
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import prepare_wsta3_sta_rootfs as wsta3  # noqa: E402
import run_wsta160_seccomp_full_rootfs_chroot_dry_run as wsta160  # noqa: E402
import run_wsta167_seccomp_live_observation as wsta167  # noqa: E402


REPO_ROOT = wsta3.REPO_ROOT
PRIVATE_ROOT = REPO_ROOT / "workspace/private"
DEFAULT_RUN_BASE = wsta3.DEFAULT_RUN_BASE
DEFAULT_WSTA167_PROOF = (
    DEFAULT_RUN_BASE
    / "wsta167-seccomp-live-observation-source-gate-20260705T1354KST"
    / "wsta167_result.json"
)
PASS_DECISION = "wsta168-seccomp-live-observation-preflight-pass"
SUMMARY_NAME = "wsta168_result.json"
COMMAND_JSON_NAME = "wsta168_live_command.json"
COMMAND_SH_NAME = "wsta168_live_command.sh"


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
        "host_preflight_only": True,
        "live_command_generated": True,
        "live_command_executed": False,
        "seccomp_filter_loaded": False,
        "seccomp_enforced": False,
        "correct_wsta161_token_in_command": False,
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def public_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": result.get("decision"),
        "run_dir": result.get("run_dir"),
        "gate_decision": result.get("gate_decision"),
        "command": result.get("command", {}),
        "checks": result.get("checks", {}),
        "safety": result.get("safety", {}),
    }


def validate_wsta167_proof(proof: dict[str, Any]) -> dict[str, bool]:
    safety = proof.get("safety", {})
    checks = proof.get("checks", {})
    contract_checks = proof.get("contract_checks", {})
    return {
        "decision_is_no_live_gate_block": proof.get("decision") == "wsta167-blocked-seccomp-live-observation-required",
        "contract_valid": checks.get("contract_valid") is True,
        "local_inputs_present": checks.get("local_inputs_present") is True,
        "explicit_live_gate_false": checks.get("explicit_live_gate") is False,
        "device_action_false": safety.get("device_action") is False,
        "seccomp_filter_loaded_false": safety.get("seccomp_filter_loaded") is False,
        "seccomp_enforced_false": safety.get("seccomp_enforced") is False,
        "correct_token_false": safety.get("correct_wsta161_token_supplied") is False,
        "all_contract_checks_true": bool(contract_checks) and all(value is True for value in contract_checks.values()),
    }


def live_command(run_dir: Path) -> list[str]:
    return [
        "python3",
        "workspace/public/src/scripts/server-distro/run_wsta167_seccomp_live_observation.py",
        "--run-id",
        "wsta168-seccomp-live-observation-execute",
        "--run-dir",
        rel(run_dir / "wsta167-live-run"),
        "--execute-seccomp-live-observation",
        "--allow-seccomp-live-observation",
        "--ack-no-correct-wsta161-token",
        "--ack-no-seccomp-load",
        "--ack-cleanup-required",
    ]


def live_command_payload(command: list[str]) -> dict[str, Any]:
    return {
        "schema": "a90-wsta168-seccomp-live-observation-command-v1",
        "state": "READY_TO_RUN_NOT_EXECUTED",
        "command": command,
        "required_ack_flags": [
            "--execute-seccomp-live-observation",
            "--allow-seccomp-live-observation",
            "--ack-no-correct-wsta161-token",
            "--ack-no-seccomp-load",
            "--ack-cleanup-required",
        ],
        "expected_outcome": {
            "decision": "wsta167-seccomp-live-observation-pass",
            "seccomp_filter_loaded": False,
            "seccomp_enforced": False,
            "correct_wsta161_token_supplied": False,
            "scenario_returncode": 65,
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


def validate_command(payload: dict[str, Any]) -> dict[str, bool]:
    command = payload.get("command", [])
    text = " ".join(str(item) for item in command)
    required = payload.get("required_ack_flags", [])
    expected = payload.get("expected_outcome", {})
    return {
        "schema_ok": payload.get("schema") == "a90-wsta168-seccomp-live-observation-command-v1",
        "ready_not_executed": payload.get("state") == "READY_TO_RUN_NOT_EXECUTED",
        "command_targets_wsta167": (
            "workspace/public/src/scripts/server-distro/run_wsta167_seccomp_live_observation.py" in command
        ),
        "all_ack_flags_present": all(flag in command for flag in required),
        "correct_token_literal_absent": "WSTA161-EXPLICIT-ALLOW-SECCOMP-LOAD" not in text,
        "no_external_network_inputs": "cloudflared" not in text and "wifi" not in text.lower() and "dhcp" not in text.lower(),
        "expected_no_load": expected.get("seccomp_filter_loaded") is False,
        "expected_no_enforce": expected.get("seccomp_enforced") is False,
        "expected_no_correct_token": expected.get("correct_wsta161_token_supplied") is False,
        "expected_scenario_rc_65": expected.get("scenario_returncode") == 65,
        "not_executed": payload.get("executed") is False,
        "secret_values_logged_zero": payload.get("secret_values_logged") == 0,
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    ts = utc_stamp()
    run_id = args.run_id or f"wsta168-seccomp-live-observation-preflight-{ts}"
    run_dir = resolve_path(args.run_dir or (DEFAULT_RUN_BASE / run_id))
    proof_path = resolve_path(args.wsta167_proof_json)
    result: dict[str, Any] = {
        "scope": "WSTA168 host-only seccomp live-observation preflight",
        "started_utc": ts,
        "run_dir": rel(run_dir),
        "safety": safety_flags(),
        "checks": {
            "explicit_gate": bool(args.emit_seccomp_live_preflight),
            "private_run_dir": wsta160.is_under(run_dir, PRIVATE_ROOT),
            "wsta167_proof_private": wsta160.is_under(proof_path, PRIVATE_ROOT),
            "wsta167_proof_present": proof_path.is_file(),
        },
    }
    for key, decision in (
        ("explicit_gate", "wsta168-blocked-explicit-gate-required"),
        ("private_run_dir", "wsta168-blocked-nonprivate-run-dir"),
        ("wsta167_proof_private", "wsta168-blocked-wsta167-proof-nonprivate"),
        ("wsta167_proof_present", "wsta168-blocked-wsta167-proof-missing"),
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
    proof_checks = validate_wsta167_proof(proof)
    command = live_command(run_dir)
    payload = live_command_payload(command)
    command_checks = validate_command(payload)
    result["wsta167_proof"] = rel(proof_path)
    result["proof_checks"] = proof_checks
    result["command_checks"] = command_checks
    result["command"] = {
        "command_json": rel(run_dir / COMMAND_JSON_NAME),
        "command_script": rel(run_dir / COMMAND_SH_NAME),
        "state": payload["state"],
        "executed": False,
        "required_ack_count": len(payload["required_ack_flags"]),
        "expected_decision": payload["expected_outcome"]["decision"],
        "expected_seccomp_filter_loaded": False,
        "expected_seccomp_enforced": False,
    }
    result["checks"].update({f"proof_{key}": value for key, value in proof_checks.items()})
    result["checks"].update({f"command_{key}": value for key, value in command_checks.items()})
    all_ok = all(proof_checks.values()) and all(command_checks.values())
    result["decision"] = PASS_DECISION if all_ok else "wsta168-blocked-preflight-invalid"
    result["gate_decision"] = "ok" if result["decision"] == PASS_DECISION else result["decision"]
    result["ended_utc"] = utc_stamp()
    run_dir.mkdir(parents=True, exist_ok=True)
    write_json(run_dir / COMMAND_JSON_NAME, payload)
    (run_dir / COMMAND_SH_NAME).write_text(
        "#!/bin/sh\nset -eu\ncd " + shlex.quote(str(REPO_ROOT)) + "\nexec " + " ".join(
            shlex.quote(item) for item in command
        ) + "\n",
        encoding="utf-8",
    )
    (run_dir / COMMAND_SH_NAME).chmod(0o755)
    write_json(run_dir / SUMMARY_NAME, result)
    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--wsta167-proof-json", type=Path, default=DEFAULT_WSTA167_PROOF)
    parser.add_argument("--emit-seccomp-live-preflight", action="store_true")
    parser.add_argument("--print-full-json", action="store_true")
    return parser


def main_with_args(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        result = run(args)
    except Exception as exc:  # noqa: BLE001
        payload = {"decision": "wsta168-runner-error", "error": str(exc)}
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1
    payload = result if args.print_full_json else public_summary(result)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.get("decision") == PASS_DECISION else 2


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
