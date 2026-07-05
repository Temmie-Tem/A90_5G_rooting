#!/usr/bin/env python3
"""WSTA188 host-only WSTA187 no-load live operator packet.

WSTA187 is the canonical fresh no-load live orchestrator.  WSTA188 promotes it
to an operator packet: it runs a fresh WSTA187 source-gate proof, then writes a
private default-off command packet and reusable shell wrapper for one attended
WSTA187 no-load live run.

WSTA188 never executes the WSTA187 live path.  It performs no device action,
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
import run_wsta187_fresh_wsta185_orchestrator as wsta187  # noqa: E402


REPO_ROOT = wsta3.REPO_ROOT
PRIVATE_ROOT = REPO_ROOT / "workspace/private"
DEFAULT_RUN_BASE = wsta3.DEFAULT_RUN_BASE
DEFAULT_WSTA168_COMMAND_JSON = wsta187.DEFAULT_WSTA168_COMMAND_JSON
DEFAULT_WSTA168_COMMAND_SH = wsta187.DEFAULT_WSTA168_COMMAND_SH
PASS_DECISION = "wsta188-wsta187-operator-packet-pass"
SUMMARY_NAME = "wsta188_result.json"
PACKET_JSON_NAME = "wsta188_operator_packet.json"
PACKET_SH_NAME = "wsta188_operator_packet.sh"
PACKET_MD_NAME = "wsta188_operator_packet.md"


ACK_FLAGS = [
    "--execute-wsta187-fresh-orchestrator",
    "--allow-wsta185-handoff-execution",
    "--ack-fresh-sequence",
    "--ack-no-correct-wsta161-token",
    "--ack-no-seccomp-load",
    "--ack-cleanup-required",
]


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
        "wsta187_source_gate_executed": False,
        "wsta187_live_command_executed": False,
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


def template() -> dict[str, Any]:
    return {
        "scope": "WSTA188 host-only WSTA187 no-load live operator packet",
        "default_mode": "host-only-source-gate-and-render-operator-packet",
        "command": [
            "python3",
            rel(Path(__file__).resolve()),
            "--prepare-wsta188-operator-packet",
        ],
        "live_execution": "not-run-by-wsta188",
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def public_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": result.get("decision"),
        "run_dir": result.get("run_dir"),
        "operator_packet": result.get("operator_packet", {}),
        "checks": result.get("checks", {}),
        "safety": result.get("safety", {}),
    }


def wsta187_source_args(
    args: argparse.Namespace,
    run_dir: Path,
    command_json: Path,
    command_sh: Path,
) -> argparse.Namespace:
    return argparse.Namespace(
        run_id="wsta188-wsta187-source-gate",
        run_dir=run_dir,
        wsta168_command_json=command_json,
        wsta168_command_sh=command_sh,
        readiness_timeout=args.readiness_timeout,
        execution_timeout=args.execution_timeout,
        audit_timeout=args.audit_timeout,
        max_age_sec=args.max_age_sec,
        prepare_wsta187_fresh_orchestrator=True,
        execute_wsta187_fresh_orchestrator=False,
        allow_wsta185_handoff_execution=False,
        ack_fresh_sequence=False,
        ack_no_correct_wsta161_token=False,
        ack_no_seccomp_load=False,
        ack_cleanup_required=False,
        print_full_json=False,
    )


def validate_wsta187_source(result: dict[str, Any]) -> dict[str, bool]:
    checks = result.get("checks", {})
    safety = result.get("safety", {})
    return {
        "decision_is_execution_gate_block": result.get("decision") == "wsta187-blocked-explicit-execution-gate-required",
        "wsta177_source_valid": checks.get("wsta177_source_valid") is True,
        "wsta178_preflight_valid": checks.get("wsta178_preflight_valid") is True,
        "wsta180_bundle_valid": checks.get("wsta180_bundle_valid") is True,
        "wsta184_handoff_valid": checks.get("wsta184_handoff_valid") is True,
        "wsta185_source_valid": checks.get("wsta185_source_valid") is True,
        "explicit_execution_gate_closed": checks.get("explicit_execution_gate") is False,
        "no_live_execution": safety.get("live_command_executed") is False,
        "no_wsta185_execution": safety.get("wsta185_execute_command_executed") is False,
        "no_seccomp_load": safety.get("seccomp_filter_loaded") is False,
        "no_seccomp_enforce": safety.get("seccomp_enforced") is False,
        "no_correct_token": safety.get("correct_wsta161_token_supplied") is False,
    }


def live_command_template(command_json: Path, command_sh: Path) -> list[str]:
    return [
        "python3",
        "workspace/public/src/scripts/server-distro/run_wsta187_fresh_wsta185_orchestrator.py",
        "--run-id",
        "wsta187-fresh-wsta185-orchestrator-live-<fresh-timestamp>",
        "--wsta168-command-json",
        rel(command_json),
        "--wsta168-command-sh",
        rel(command_sh),
        "--prepare-wsta187-fresh-orchestrator",
        *ACK_FLAGS,
        "--print-full-json",
    ]


def command_script(command_json: Path, command_sh: Path) -> str:
    return "\n".join([
        "#!/bin/sh",
        "set -eu",
        f"cd '{REPO_ROOT}'",
        "ts=$(date +%Y%m%dT%H%M%SKST)",
        'export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-/tmp/a90_pycache}"',
        "exec python3 workspace/public/src/scripts/server-distro/run_wsta187_fresh_wsta185_orchestrator.py \\",
        '  --run-id "wsta187-fresh-wsta185-orchestrator-live-${ts}" \\',
        f"  --wsta168-command-json '{rel(command_json)}' \\",
        f"  --wsta168-command-sh '{rel(command_sh)}' \\",
        "  --prepare-wsta187-fresh-orchestrator \\",
        "  --execute-wsta187-fresh-orchestrator \\",
        "  --allow-wsta185-handoff-execution \\",
        "  --ack-fresh-sequence \\",
        "  --ack-no-correct-wsta161-token \\",
        "  --ack-no-seccomp-load \\",
        "  --ack-cleanup-required \\",
        "  --print-full-json",
        "",
    ])


def markdown(packet: dict[str, Any]) -> str:
    lines = [
        "# WSTA187 No-Load Live Operator Packet",
        "",
        f"- State: `{packet.get('state')}`",
        f"- Source gate: `{packet.get('source_wsta187_result')}`",
        f"- Command script: `{packet.get('live_command_script')}`",
        f"- Required acknowledgements: `{len(packet.get('operator_acknowledgements_required') or [])}`",
        f"- Default off: `{str(packet.get('default_off')).lower()}`",
        f"- Live executed by WSTA188: `{str(packet.get('live_execution_requested')).lower()}`",
        "",
        "## Safety Boundary",
        "",
        "- no boot flash",
        "- no native reboot",
        "- no Wi-Fi connect or DHCP",
        "- no public tunnel",
        "- no packet filter mutation",
        "- no seccomp load or enforce",
        "- no correct WSTA161 token",
        "",
        "## Next Action",
        "",
        "Run the generated private shell script only during an attended no-load live observation.",
        "The script creates a fresh WSTA187 run id at execution time.",
        "",
    ]
    return "\n".join(lines)


def validate_packet(packet: dict[str, Any], script_text: str) -> dict[str, bool]:
    command = packet.get("live_command_template", [])
    command_text = json.dumps(command, sort_keys=True) + "\n" + script_text
    return {
        "state_ready": packet.get("state") == "READY_OPERATOR_PACKET_NO_LOAD_DEFAULT_OFF",
        "default_off": packet.get("default_off") is True,
        "ready_for_no_load_live": packet.get("ready_for_no_load_live") is True,
        "live_not_executed": packet.get("live_execution_requested") is False,
        "command_is_list": isinstance(command, list) and all(isinstance(item, str) for item in command),
        "command_targets_wsta187": "run_wsta187_fresh_wsta185_orchestrator.py" in command_text,
        "command_has_prepare_gate": "--prepare-wsta187-fresh-orchestrator" in command_text,
        "command_has_execute_gate": "--execute-wsta187-fresh-orchestrator" in command_text,
        "command_has_all_ack_flags": all(flag in command_text for flag in ACK_FLAGS),
        "script_uses_fresh_timestamp": "date +%Y%m%dT%H%M%SKST" in script_text and "${ts}" in script_text,
        "script_uses_pycache_prefix": "PYTHONPYCACHEPREFIX" in script_text,
        "no_flash_surface": ("native_" + "init_flash.py") not in command_text,
        "no_correct_token_literal": "WSTA161-EXPLICIT-ALLOW-SECCOMP-LOAD" not in command_text,
        "no_external_network_inputs": (
            "cloudflared" not in command_text
            and ("ss" + "id=") not in command_text.lower()
            and ("ps" + "k=") not in command_text.lower()
            and "dhcp" not in command_text.lower()
        ),
        "secret_values_logged_zero": packet.get("secret_values_logged") == 0,
        "public_url_not_logged": packet.get("public_url_value_logged") is False,
    }


def build_packet(
    run_dir: Path,
    source_result: dict[str, Any],
    command_json: Path,
    command_sh: Path,
) -> tuple[dict[str, Any], str]:
    packet_json = run_dir / PACKET_JSON_NAME
    packet_sh = run_dir / PACKET_SH_NAME
    packet_md = run_dir / PACKET_MD_NAME
    script_text = command_script(command_json, command_sh)
    packet = {
        "schema": "a90-wsta188-wsta187-no-load-operator-packet-v1",
        "state": "READY_OPERATOR_PACKET_NO_LOAD_DEFAULT_OFF",
        "ready_for_no_load_live": True,
        "default_off": True,
        "source_wsta187_result": source_result.get("stages", {}).get("wsta185", {}).get("result_json"),
        "source_wsta187_run_dir": source_result.get("run_dir"),
        "source_wsta187_decision": source_result.get("decision"),
        "live_command_template": live_command_template(command_json, command_sh),
        "live_command_script": rel(packet_sh),
        "operator_acknowledgements_required": ACK_FLAGS,
        "operator_preflight_checks": [
            "run-wsta188-immediately-before-attended-live-observation",
            "confirm-WSTA187-source-gate-valid",
            "confirm-final-selftest-fail-zero-after-live-run",
        ],
        "abort_conditions": [
            "source-gate-not-pass",
            "bridge-or-device-health-unclear",
            "operator-not-present",
            "unexpected-seccomp-load-request",
            "unexpected-correct-token-request",
        ],
        "cleanup_expectations": [
            "WSTA167 work image restored to clean hash",
            "no public tunnel to retire",
            "no packet filter state to restore",
        ],
        "safety_boundary": {
            "boot_flash": False,
            "native_reboot": False,
            "wifi_connect": False,
            "dhcp": False,
            "public_tunnel": False,
            "packet_filter_mutation": False,
            "seccomp_filter_loaded": False,
            "seccomp_enforced": False,
            "correct_wsta161_token_supplied": False,
        },
        "live_execution_requested": False,
        "public_url_value_logged": False,
        "secret_values_logged": 0,
        "json_path": rel(packet_json),
        "markdown_path": rel(packet_md),
    }
    return packet, script_text


def classify(result: dict[str, Any]) -> str:
    checks = result.get("checks", {})
    ordered = (
        ("explicit_prepare_gate", "wsta188-blocked-explicit-prepare-gate-required"),
        ("wsta168_command_json_private", "wsta188-blocked-wsta168-command-json-nonprivate"),
        ("wsta168_command_sh_private", "wsta188-blocked-wsta168-command-sh-nonprivate"),
        ("wsta168_command_json_present", "wsta188-blocked-wsta168-command-json-missing"),
        ("wsta168_command_sh_present", "wsta188-blocked-wsta168-command-sh-missing"),
        ("wsta187_source_gate_valid", "wsta188-blocked-wsta187-source-gate-invalid"),
        ("operator_packet_valid", "wsta188-blocked-operator-packet-invalid"),
    )
    for key, decision in ordered:
        if not checks.get(key):
            return decision
    return PASS_DECISION


def run(args: argparse.Namespace) -> dict[str, Any]:
    ts = utc_stamp()
    run_id = args.run_id or f"wsta188-wsta187-operator-packet-{ts}"
    run_dir = resolve_path(args.run_dir or (DEFAULT_RUN_BASE / run_id))
    wsta168_command_json = resolve_path(args.wsta168_command_json)
    wsta168_command_sh = resolve_path(args.wsta168_command_sh)
    result: dict[str, Any] = {
        "scope": "WSTA188 host-only WSTA187 no-load live operator packet",
        "started_utc": ts,
        "run_dir": rel(run_dir),
        "wsta168_command_json": rel(wsta168_command_json),
        "wsta168_command_sh": rel(wsta168_command_sh),
        "safety": safety_flags(),
        "checks": {
            "explicit_prepare_gate": bool(args.prepare_wsta188_operator_packet),
            "private_run_dir": wsta160.is_under(run_dir, PRIVATE_ROOT),
            "wsta168_command_json_private": wsta160.is_under(wsta168_command_json, PRIVATE_ROOT),
            "wsta168_command_sh_private": wsta160.is_under(wsta168_command_sh, PRIVATE_ROOT),
            "wsta168_command_json_present": wsta168_command_json.is_file(),
            "wsta168_command_sh_present": wsta168_command_sh.is_file(),
        },
    }
    if not result["checks"]["private_run_dir"]:
        result["decision"] = "wsta188-blocked-nonprivate-run-dir"
        result["ended_utc"] = utc_stamp()
        return result
    run_dir.mkdir(parents=True, exist_ok=True)
    out_path = run_dir / SUMMARY_NAME
    for key in (
        "explicit_prepare_gate",
        "wsta168_command_json_private",
        "wsta168_command_sh_private",
        "wsta168_command_json_present",
        "wsta168_command_sh_present",
    ):
        if not result["checks"][key]:
            result["decision"] = classify(result)
            result["ended_utc"] = utc_stamp()
            write_json(out_path, result)
            return result

    source_dir = run_dir / "wsta187-source-gate"
    source_result = wsta187.run(wsta187_source_args(args, source_dir, wsta168_command_json, wsta168_command_sh))
    result["source_wsta187"] = {
        "run_dir": rel(source_dir),
        "result_json": rel(source_dir / wsta187.SUMMARY_NAME),
        "decision": source_result.get("decision"),
    }
    result["wsta187_source_checks"] = validate_wsta187_source(source_result)
    result["checks"]["wsta187_source_gate_valid"] = all(result["wsta187_source_checks"].values())
    result["safety"]["wsta187_source_gate_executed"] = True
    write_json(out_path, result)
    if not result["checks"]["wsta187_source_gate_valid"]:
        result["decision"] = classify(result)
        result["ended_utc"] = utc_stamp()
        write_json(out_path, result)
        return result

    packet, script_text = build_packet(run_dir, source_result, wsta168_command_json, wsta168_command_sh)
    packet_json = run_dir / PACKET_JSON_NAME
    packet_sh = run_dir / PACKET_SH_NAME
    packet_md = run_dir / PACKET_MD_NAME
    result["operator_packet_checks"] = validate_packet(packet, script_text)
    result["checks"]["operator_packet_valid"] = all(result["operator_packet_checks"].values())
    result["operator_packet"] = packet
    result["decision"] = classify(result)
    result["ended_utc"] = utc_stamp()
    if result["checks"]["operator_packet_valid"]:
        write_json(packet_json, result)
        write_text(packet_sh, script_text)
        packet_sh.chmod(0o700)
        write_text(packet_md, markdown(packet))
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
    parser.add_argument("--prepare-wsta188-operator-packet", action="store_true")
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
        payload = {"decision": "wsta188-runner-error", "error": str(exc)}
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1
    payload = result if args.print_full_json else public_summary(result)
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result.get("decision") == PASS_DECISION else 2


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
