#!/usr/bin/env python3
"""WSTA200 host-only WSTA199 operator handoff packet.

Consumes a WSTA199 WSTA198-adapter status result, re-runs WSTA199 from the
same WSTA198 adapter, and emits a private default-off operator handoff packet
plus shell wrapper for a future attended WSTA198 live canary.  WSTA200 never
executes the live canary and never supplies the WSTA161 token to the device.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
for _path in (SCRIPT_DIR, SCRIPT_DIR.parent / "revalidation"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import prepare_wsta3_sta_rootfs as wsta3  # noqa: E402
import run_wsta160_seccomp_full_rootfs_chroot_dry_run as wsta160  # noqa: E402
import run_wsta161_seccomp_loader_gated_apply_helper as wsta161  # noqa: E402
import run_wsta193_seccomp_correct_token_canary_source as wsta193  # noqa: E402
import run_wsta198_seccomp_load_canary_ssh_adapter as wsta198  # noqa: E402
import run_wsta199_wsta198_adapter_status as wsta199  # noqa: E402


REPO_ROOT = wsta3.REPO_ROOT
PRIVATE_ROOT = REPO_ROOT / "workspace/private"
DEFAULT_RUN_BASE = wsta3.DEFAULT_RUN_BASE
DEFAULT_WSTA199_STATUS_JSON = (
    DEFAULT_RUN_BASE
    / "wsta199-wsta198-adapter-status-20260705T173455KST"
    / wsta199.STATUS_JSON_NAME
)
PASS_DECISION = "wsta200-wsta199-operator-handoff-pass"
SUMMARY_NAME = "wsta200_result.json"
HANDOFF_JSON_NAME = "wsta200_wsta199_operator_handoff.json"
HANDOFF_SH_NAME = "wsta200_wsta199_operator_handoff.sh"
HANDOFF_MD_NAME = "wsta200_wsta199_operator_handoff.md"
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
        "wsta199_recheck_executed": False,
        "wsta198_live_command_executed": False,
        "ssh_chroot_transport": False,
        "dropbear_over_ncm": False,
        "fresh_native_health_checked": False,
        "post_run_native_health_checked": False,
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
        "scope": "WSTA200 host-only WSTA199 operator handoff packet",
        "default_mode": "host-only-render-operator-handoff",
        "input": "workspace/private/runs/server-distro/<wsta199-run>/wsta199_wsta198_adapter_status.json",
        "command": [
            "python3",
            rel(Path(__file__).resolve()),
            "--wsta199-status-json",
            "workspace/private/runs/server-distro/<wsta199-run>/wsta199_wsta198_adapter_status.json",
            "--prepare-wsta200-operator-handoff",
        ],
        "live_execution": "not-run-by-wsta200",
        "private_token_env": wsta193.PRIVATE_TOKEN_ENV,
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def public_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": result.get("decision"),
        "run_dir": result.get("run_dir"),
        "operator_handoff": result.get("operator_handoff", {}),
        "checks": result.get("checks", {}),
        "safety": result.get("safety", {}),
    }


def private_token_status() -> dict[str, bool]:
    value = os.environ.get(wsta193.PRIVATE_TOKEN_ENV)
    return {
        "private_token_env_present": value is not None,
        "private_token_matches_wsta161": value == wsta161.LOAD_TOKEN,
    }


def stable_status_view(status: dict[str, Any]) -> dict[str, Any]:
    return {
        "adapter_current": status.get("adapter_current"),
        "ready_for_attended_live_handoff": status.get("ready_for_attended_live_handoff"),
        "packet_match": status.get("packet_match"),
        "template_match": status.get("template_match"),
        "selected_transport": status.get("selected_transport"),
        "canary_service": status.get("canary_service"),
        "live_command_script": status.get("live_command_script"),
        "operator_acknowledgements_required": status.get("operator_acknowledgements_required"),
        "operator_preflight_checks": status.get("operator_preflight_checks"),
        "abort_conditions": status.get("abort_conditions"),
        "cleanup_expectations": status.get("cleanup_expectations"),
        "default_off": status.get("default_off"),
        "live_execution_requested": status.get("live_execution_requested"),
        "public_url_value_logged": status.get("public_url_value_logged"),
        "secret_values_logged": status.get("secret_values_logged"),
    }


def no_mutation_safety(safety: dict[str, Any]) -> dict[str, bool]:
    return {
        "device_action_false": safety.get("device_action") is False,
        "boot_flash_false": safety.get("boot_flash") is False,
        "native_reboot_false": safety.get("native_reboot") is False,
        "wifi_connect_false": safety.get("wifi_connect") is False,
        "dhcp_false": safety.get("dhcp") is False,
        "public_tunnel_false": safety.get("public_tunnel") is False,
        "packet_filter_mutation_false": safety.get("packet_filter_mutation") is False,
        "userdata_touch_false": safety.get("userdata_touch") is False,
        "switch_root_false": safety.get("switch_root") is False,
        "live_command_executed_false": safety.get("live_command_executed") is False,
        "correct_token_supplied_false": safety.get("correct_wsta161_token_supplied") is False,
        "seccomp_loaded_false": safety.get("seccomp_filter_loaded") is False,
        "seccomp_enforced_false": safety.get("seccomp_enforced") is False,
        "secret_values_zero": safety.get("secret_values_logged") == 0,
        "public_url_not_logged": safety.get("public_url_value_logged") is False,
    }


def validate_status_payload(path: Path) -> tuple[bool, str, dict[str, Any]]:
    try:
        payload = load_json(path)
    except Exception as exc:  # noqa: BLE001
        return False, "wsta200-blocked-status-unreadable", {"error": str(exc)}
    status = payload.get("adapter_status")
    if not isinstance(status, dict):
        return False, "wsta200-blocked-status-missing", {"payload_decision": payload.get("decision")}
    adapter_path = resolve_path(status.get("wsta198_adapter_json", ""))
    script_path = resolve_path(status.get("live_command_script", ""))
    safety = payload.get("safety", {}) if isinstance(payload.get("safety"), dict) else {}
    mutation = no_mutation_safety(safety)
    serialized = json.dumps(status, sort_keys=True)
    checks = {
        "status_private": wsta160.is_under(path, PRIVATE_ROOT),
        "decision_pass": payload.get("decision") == wsta199.PASS_DECISION,
        "status_state_current": status.get("state") in (
            "ADAPTER_CURRENT_OPERATOR_TOKEN_REQUIRED_DEFAULT_OFF",
            "READY_TO_RUN_WSTA198_ATTENDED_LIVE_DEFAULT_OFF",
        ),
        "adapter_current": status.get("adapter_current") is True,
        "ready_for_attended_live_handoff": status.get("ready_for_attended_live_handoff") is True,
        "packet_match": status.get("packet_match") is True,
        "template_match": status.get("template_match") is True,
        "default_off": status.get("default_off") is True,
        "live_not_requested": status.get("live_execution_requested") is False,
        "adapter_private": wsta160.is_under(adapter_path, PRIVATE_ROOT),
        "adapter_present": adapter_path.is_file(),
        "script_private": wsta160.is_under(script_path, PRIVATE_ROOT),
        "script_present": script_path.is_file(),
        "script_executable": script_path.is_file() and bool(script_path.stat().st_mode & 0o100),
        "operator_ack_stack_matches_wsta198": status.get("operator_acknowledgements_required") == wsta198.ACK_FLAGS,
        "no_mutation_safety": all(mutation.values()),
        "no_token_literal": FORBIDDEN_TOKEN_PREFIX not in serialized,
        "no_external_network_inputs": wsta198.no_external_network_inputs(serialized),
        "secret_values_zero": status.get("secret_values_logged") == 0,
        "public_url_not_logged": status.get("public_url_value_logged") is False,
    }
    if not all(checks.values()):
        return False, "wsta200-blocked-status-invalid", {
            "payload": payload,
            "status": status,
            "checks": checks,
            "mutation_checks": mutation,
        }
    return True, "ok", {
        "payload": payload,
        "status": status,
        "adapter_path": adapter_path,
        "script_path": script_path,
        "checks": checks,
    }


def wsta199_recheck_args(run_dir: Path, adapter_path: Path) -> argparse.Namespace:
    return argparse.Namespace(
        run_id="wsta200-wsta199-recheck",
        run_dir=run_dir,
        wsta198_adapter_json=adapter_path,
        print_template=False,
        print_full_json=False,
    )


def validate_recheck(recheck: dict[str, Any]) -> dict[str, bool]:
    checks = recheck.get("checks", {}) if isinstance(recheck.get("checks"), dict) else {}
    safety = recheck.get("safety", {}) if isinstance(recheck.get("safety"), dict) else {}
    status = recheck.get("adapter_status", {}) if isinstance(recheck.get("adapter_status"), dict) else {}
    mutation = no_mutation_safety(safety)
    return {
        "decision_pass": recheck.get("decision") == wsta199.PASS_DECISION,
        "adapter_valid": checks.get("adapter_valid") is True,
        "wsta198_recheck_valid": checks.get("wsta198_recheck_valid") is True,
        "adapter_status_valid": checks.get("adapter_status_valid") is True,
        "adapter_current": status.get("adapter_current") is True,
        "ready_for_attended_live_handoff": status.get("ready_for_attended_live_handoff") is True,
        "packet_match": status.get("packet_match") is True,
        "template_match": status.get("template_match") is True,
        "no_mutation_safety": all(mutation.values()),
    }


def handoff_script(adapter_path: Path, status_path: Path, live_script_path: Path) -> str:
    return "\n".join([
        "#!/bin/sh",
        "set -eu",
        f"cd '{REPO_ROOT}'",
        "ts=$(date +%Y%m%dT%H%M%SKST)",
        'export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-/tmp/a90_pycache}"',
        f': "${{{wsta193.PRIVATE_TOKEN_ENV}:?private-token-required}}"',
        'SELF_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)',
        'STATUS_OUT="${SELF_DIR}/wsta200_preflight_wsta199_status_${ts}.json"',
        "python3 workspace/public/src/scripts/server-distro/run_wsta199_wsta198_adapter_status.py \\",
        f"  --wsta198-adapter-json '{rel(adapter_path)}' \\",
        '  --run-id "wsta200-preflight-wsta199-${ts}" \\',
        '  --print-full-json > "$STATUS_OUT"',
        "python3 - \"$STATUS_OUT\" <<'PY'",
        "import json, sys",
        "path = sys.argv[1]",
        "payload = json.load(open(path, 'r', encoding='utf-8'))",
        "status = payload.get('adapter_status') or {}",
        "assert payload.get('decision') == 'wsta199-wsta198-adapter-status-pass', payload.get('decision')",
        "assert status.get('adapter_current') is True, status",
        "assert status.get('ready_for_attended_live_handoff') is True, status",
        "assert status.get('packet_match') is True and status.get('template_match') is True, status",
        "assert (payload.get('safety') or {}).get('live_command_executed') is False, payload.get('safety')",
        "PY",
        f"# Source status used when this handoff was rendered: {rel(status_path)}",
        f"exec '{rel(live_script_path)}'",
        "",
    ])


def build_handoff(
    run_dir: Path,
    status_path: Path,
    status: dict[str, Any],
    recheck_result: dict[str, Any],
    recheck_path: Path,
    adapter_path: Path,
    live_script_path: Path,
    token_checks: dict[str, bool],
) -> tuple[dict[str, Any], str]:
    handoff_json = run_dir / HANDOFF_JSON_NAME
    handoff_sh = run_dir / HANDOFF_SH_NAME
    handoff_md = run_dir / HANDOFF_MD_NAME
    token_ready = bool(token_checks.get("private_token_env_present") and token_checks.get("private_token_matches_wsta161"))
    state = (
        "READY_OPERATOR_HANDOFF_WSTA198_ATTENDED_LIVE"
        if token_ready
        else "READY_OPERATOR_HANDOFF_WSTA198_TOKEN_REQUIRED_DEFAULT_OFF"
    )
    script_text = handoff_script(adapter_path, status_path, live_script_path)
    handoff = {
        "schema": "a90-wsta200-wsta199-operator-handoff-v1",
        "state": state,
        "source_wsta199_status": rel(status_path),
        "fresh_wsta199_recheck_result": rel(recheck_path),
        "wsta198_adapter_json": rel(adapter_path),
        "wsta198_live_command_script": rel(live_script_path),
        "handoff_command_script": rel(handoff_sh),
        "selected_transport": status.get("selected_transport"),
        "canary_service": status.get("canary_service"),
        "adapter_current": True,
        "ready_for_attended_live_handoff": True,
        "ready_for_immediate_live_execute": token_ready,
        "private_token_env": wsta193.PRIVATE_TOKEN_ENV,
        "private_token_env_present_at_render_time": token_checks.get("private_token_env_present") is True,
        "private_token_matches_wsta161_at_render_time": token_checks.get("private_token_matches_wsta161") is True,
        "token_value_included": False,
        "correct_wsta161_token_supplied": False,
        "operator_acknowledgements_required": status.get("operator_acknowledgements_required") or [],
        "operator_preflight_checks": [
            "run-wsta200-handoff-immediately-before-attended-live",
            "wrapper-reruns-wsta199-before-wsta198-live",
            "private-token-env-present-at-execution-time",
            "WSTA198-performs-fresh-native-health-before-and-after-canary",
            *(status.get("operator_preflight_checks") or []),
        ],
        "abort_conditions": status.get("abort_conditions") or [],
        "cleanup_expectations": status.get("cleanup_expectations") or [],
        "status_stable_view_match": stable_status_view(status) == stable_status_view(recheck_result["adapter_status"]),
        "live_execution_requested": False,
        "seccomp_filter_loaded": False,
        "seccomp_enforced": False,
        "public_url_value_logged": False,
        "secret_values_logged": 0,
        "json_path": rel(handoff_json),
        "markdown_path": rel(handoff_md),
    }
    return handoff, script_text


def validate_handoff(handoff: dict[str, Any], script_text: str) -> dict[str, bool]:
    serialized = json.dumps(handoff, sort_keys=True) + "\n" + script_text
    return {
        "schema_ok": handoff.get("schema") == "a90-wsta200-wsta199-operator-handoff-v1",
        "state_ready": handoff.get("state") in (
            "READY_OPERATOR_HANDOFF_WSTA198_ATTENDED_LIVE",
            "READY_OPERATOR_HANDOFF_WSTA198_TOKEN_REQUIRED_DEFAULT_OFF",
        ),
        "adapter_current": handoff.get("adapter_current") is True,
        "ready_for_attended_live_handoff": handoff.get("ready_for_attended_live_handoff") is True,
        "token_value_not_included": handoff.get("token_value_included") is False,
        "correct_token_not_supplied": handoff.get("correct_wsta161_token_supplied") is False,
        "ack_stack_matches_wsta198": handoff.get("operator_acknowledgements_required") == wsta198.ACK_FLAGS,
        "status_stable_view_match": handoff.get("status_stable_view_match") is True,
        "script_requires_private_token_env": f"${{{wsta193.PRIVATE_TOKEN_ENV}:?private-token-required}}" in script_text,
        "script_reruns_wsta199": "run_wsta199_wsta198_adapter_status.py" in script_text,
        "script_execs_wsta198_private_wrapper": str(handoff.get("wsta198_live_command_script")) in script_text,
        "live_not_requested": handoff.get("live_execution_requested") is False,
        "seccomp_not_loaded": handoff.get("seccomp_filter_loaded") is False,
        "seccomp_not_enforced": handoff.get("seccomp_enforced") is False,
        "no_flash_surface": ("native_" + "init_flash.py") not in serialized,
        "no_token_literal": FORBIDDEN_TOKEN_PREFIX not in serialized,
        "no_external_network_inputs": wsta198.no_external_network_inputs(serialized),
        "secret_values_zero": handoff.get("secret_values_logged") == 0,
        "public_url_not_logged": handoff.get("public_url_value_logged") is False,
    }


def handoff_markdown(handoff: dict[str, Any]) -> str:
    lines = [
        "# WSTA200 WSTA198 Live Operator Handoff",
        "",
        f"- State: `{handoff.get('state')}`",
        f"- Source WSTA199 status: `{handoff.get('source_wsta199_status')}`",
        f"- WSTA198 wrapper: `{handoff.get('wsta198_live_command_script')}`",
        f"- Handoff script: `{handoff.get('handoff_command_script')}`",
        f"- Ready for attended handoff: `{str(handoff.get('ready_for_attended_live_handoff')).lower()}`",
        f"- Ready for immediate execute: `{str(handoff.get('ready_for_immediate_live_execute')).lower()}`",
        f"- Private token env: `{handoff.get('private_token_env')}`",
        "",
        "## Boundary",
        "",
        "WSTA200 renders an operator handoff only. It does not execute the WSTA198 live canary.",
        "",
    ]
    return "\n".join(lines)


def classify(result: dict[str, Any]) -> str:
    checks = result.get("checks", {})
    ordered = (
        ("explicit_prepare_gate", "wsta200-blocked-explicit-prepare-gate-required"),
        ("private_run_dir", "wsta200-blocked-nonprivate-run-dir"),
        ("status_private", "wsta200-blocked-status-nonprivate"),
        ("status_present", "wsta200-blocked-status-missing"),
        ("status_valid", result.get("status_error") or "wsta200-blocked-status-invalid"),
        ("wsta199_recheck_valid", "wsta200-blocked-wsta199-recheck-invalid"),
        ("status_stable_view_match", "wsta200-blocked-status-drift"),
        ("operator_handoff_valid", "wsta200-blocked-operator-handoff-invalid"),
    )
    for key, decision in ordered:
        if not checks.get(key):
            return str(decision)
    return PASS_DECISION


def run(args: argparse.Namespace) -> dict[str, Any]:
    ts = utc_stamp()
    run_id = args.run_id or f"wsta200-wsta199-operator-handoff-{ts}"
    run_dir = resolve_path(args.run_dir or (DEFAULT_RUN_BASE / run_id))
    status_path = resolve_path(args.wsta199_status_json)
    result: dict[str, Any] = {
        "scope": "WSTA200 host-only WSTA199 operator handoff packet",
        "started_utc": ts,
        "run_dir": rel(run_dir),
        "wsta199_status_json": rel(status_path),
        "safety": safety_flags(),
        "checks": {
            "explicit_prepare_gate": bool(args.prepare_wsta200_operator_handoff),
            "private_run_dir": wsta160.is_under(run_dir, PRIVATE_ROOT),
            "status_private": wsta160.is_under(status_path, PRIVATE_ROOT),
            "status_present": status_path.is_file(),
        },
    }
    if not result["checks"]["private_run_dir"]:
        result["decision"] = classify(result)
        result["ended_utc"] = utc_stamp()
        return result
    run_dir.mkdir(parents=True, exist_ok=True)
    out_path = run_dir / SUMMARY_NAME
    for key in ("explicit_prepare_gate", "status_private", "status_present"):
        if not result["checks"][key]:
            result["decision"] = classify(result)
            result["ended_utc"] = utc_stamp()
            write_json(out_path, result)
            return result

    valid, decision, status_info = validate_status_payload(status_path)
    result["status_checks"] = status_info.get("checks", {})
    result["checks"]["status_valid"] = valid
    result["status_error"] = None if valid else decision
    write_json(out_path, result)
    if not valid:
        result["decision"] = classify(result)
        result["ended_utc"] = utc_stamp()
        write_json(out_path, result)
        return result

    recheck_dir = run_dir / "wsta199-recheck"
    recheck_result = wsta199.run(wsta199_recheck_args(recheck_dir, status_info["adapter_path"]))
    result["safety"]["wsta199_recheck_executed"] = True
    result["wsta199_recheck"] = {
        "run_dir": rel(recheck_dir),
        "result_json": rel(recheck_dir / wsta199.SUMMARY_NAME),
        "status_json": rel(recheck_dir / wsta199.STATUS_JSON_NAME),
        "decision": recheck_result.get("decision"),
    }
    result["wsta199_recheck_checks"] = validate_recheck(recheck_result)
    result["checks"]["wsta199_recheck_valid"] = all(result["wsta199_recheck_checks"].values())
    result["checks"]["status_stable_view_match"] = bool(
        result["checks"]["wsta199_recheck_valid"]
        and stable_status_view(status_info["status"]) == stable_status_view(recheck_result["adapter_status"])
    )
    result["token_checks"] = private_token_status()
    write_json(out_path, result)
    if not (result["checks"]["wsta199_recheck_valid"] and result["checks"]["status_stable_view_match"]):
        result["decision"] = classify(result)
        result["ended_utc"] = utc_stamp()
        write_json(out_path, result)
        return result

    handoff, script_text = build_handoff(
        run_dir,
        status_path,
        status_info["status"],
        recheck_result,
        recheck_dir / wsta199.SUMMARY_NAME,
        status_info["adapter_path"],
        status_info["script_path"],
        result["token_checks"],
    )
    result["operator_handoff_checks"] = validate_handoff(handoff, script_text)
    result["checks"]["operator_handoff_valid"] = all(result["operator_handoff_checks"].values())
    result["operator_handoff"] = {
        "handoff_json": rel(run_dir / HANDOFF_JSON_NAME),
        "handoff_shell": rel(run_dir / HANDOFF_SH_NAME),
        "handoff_markdown": rel(run_dir / HANDOFF_MD_NAME),
        "state": handoff["state"],
        "ready_for_attended_live_handoff": handoff["ready_for_attended_live_handoff"],
        "ready_for_immediate_live_execute": handoff["ready_for_immediate_live_execute"],
        "private_token_env": handoff["private_token_env"],
        "correct_wsta161_token_supplied": False,
        "live_execution_requested": False,
        "seccomp_filter_loaded": False,
        "seccomp_enforced": False,
    }
    if result["checks"]["operator_handoff_valid"]:
        write_json(run_dir / HANDOFF_JSON_NAME, handoff)
        write_text(run_dir / HANDOFF_SH_NAME, script_text)
        (run_dir / HANDOFF_SH_NAME).chmod(0o700)
        write_text(run_dir / HANDOFF_MD_NAME, handoff_markdown(handoff))
    result["safety"]["live_command_generated"] = result["checks"]["operator_handoff_valid"]
    result["decision"] = classify(result)
    result["ended_utc"] = utc_stamp()
    write_json(out_path, result)
    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--wsta199-status-json", type=Path, default=DEFAULT_WSTA199_STATUS_JSON)
    parser.add_argument("--prepare-wsta200-operator-handoff", action="store_true")
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
        payload = {"decision": "wsta200-runner-error", "error": str(exc)}
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1
    payload = result if args.print_full_json else public_summary(result)
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result.get("decision") == PASS_DECISION else 2


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
