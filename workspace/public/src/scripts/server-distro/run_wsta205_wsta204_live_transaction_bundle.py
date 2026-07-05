#!/usr/bin/env python3
"""WSTA205 host-only WSTA204 live transaction bundle.

Consumes a private WSTA204 live-result verifier artifact, re-runs WSTA204 from
the same WSTA203 audit, and emits a default-off private transaction script that
will later run the current WSTA200 handoff wrapper and immediately verify the
resulting WSTA198 live result with WSTA204.  WSTA205 never executes that
transaction script.
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
import run_wsta204_wsta203_live_result_verifier as wsta204  # noqa: E402


REPO_ROOT = wsta3.REPO_ROOT
PRIVATE_ROOT = REPO_ROOT / "workspace/private"
DEFAULT_RUN_BASE = wsta3.DEFAULT_RUN_BASE
DEFAULT_WSTA204_VERIFIER_JSON = (
    DEFAULT_RUN_BASE
    / "wsta204-wsta198-live-result-verifier-20260705T181121KST"
    / wsta204.VERIFIER_JSON_NAME
)
PASS_DECISION = "wsta205-wsta204-live-transaction-bundle-source-pass"
SUMMARY_NAME = "wsta205_result.json"
TRANSACTION_JSON_NAME = "wsta205_wsta204_live_transaction_bundle.json"
TRANSACTION_SH_NAME = "wsta205_run_wsta200_and_verify.sh"
TRANSACTION_MD_NAME = "wsta205_wsta204_live_transaction_bundle.md"
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
        "wsta204_recheck_executed": False,
        "wsta205_transaction_script_generated": False,
        "wsta205_transaction_script_executed": False,
        "wsta200_handoff_shell_executed": False,
        "wsta198_live_command_executed": False,
        "wsta204_verify_mode_executed": False,
        "ssh_chroot_transport": False,
        "dropbear_over_ncm": False,
        "fresh_native_health_checked": False,
        "post_run_native_health_checked": False,
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
        "scope": "WSTA205 host-only WSTA204 live transaction bundle",
        "default_mode": "emit-private-default-off-live-transaction-bundle",
        "input": "workspace/private/runs/server-distro/<wsta204-run>/wsta204_wsta198_live_result_verifier.json",
        "command": [
            "python3",
            rel(Path(__file__).resolve()),
            "--source-wsta204-verifier-json",
            "workspace/private/runs/server-distro/<wsta204-run>/wsta204_wsta198_live_result_verifier.json",
            "--emit-wsta205-live-transaction-bundle",
        ],
        "live_execution": "not-run-by-wsta205",
        "private_token_env": wsta193.PRIVATE_TOKEN_ENV,
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def public_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": result.get("decision"),
        "run_dir": result.get("run_dir"),
        "live_transaction_bundle": result.get("live_transaction_bundle", {}),
        "checks": result.get("checks", {}),
        "safety": result.get("safety", {}),
    }


def private_token_status() -> dict[str, bool]:
    value = os.environ.get(wsta193.PRIVATE_TOKEN_ENV)
    return {
        "private_token_env_present": value is not None,
        "private_token_matches_wsta161": value == wsta161.LOAD_TOKEN,
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
        "wsta200_handoff_shell_executed_false": safety.get("wsta200_handoff_shell_executed") is False,
        "wsta198_live_command_executed_false": safety.get("wsta198_live_command_executed") is False,
        "live_command_executed_false": safety.get("live_command_executed") is False,
        "correct_token_supplied_false": safety.get("correct_wsta161_token_supplied") is False,
        "seccomp_loaded_false": safety.get("seccomp_filter_loaded") is False,
        "seccomp_enforced_false": safety.get("seccomp_enforced") is False,
        "secret_values_zero": safety.get("secret_values_logged") == 0,
        "public_url_not_logged": safety.get("public_url_value_logged") is False,
    }


def stable_verifier_view(verifier: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_wsta203_audit": verifier.get("source_wsta203_audit"),
        "wsta200_handoff_json": verifier.get("wsta200_handoff_json"),
        "handoff_command_script": verifier.get("handoff_command_script"),
        "wsta198_live_command_script": verifier.get("wsta198_live_command_script"),
        "selected_transport": verifier.get("selected_transport"),
        "canary_service": verifier.get("canary_service"),
        "audit_current": verifier.get("audit_current"),
        "audit_stable_view_match": verifier.get("audit_stable_view_match"),
        "ready_for_post_live_verification": verifier.get("ready_for_post_live_verification"),
        "expected_wsta198_decision": verifier.get("expected_wsta198_decision"),
        "required_live_checks": verifier.get("required_live_checks"),
        "required_live_safety_true": verifier.get("required_live_safety_true"),
        "required_live_safety_false": verifier.get("required_live_safety_false"),
        "required_canary_markers": verifier.get("required_canary_markers"),
        "operator_acknowledgements_required": verifier.get("operator_acknowledgements_required"),
        "operator_preflight_checks": verifier.get("operator_preflight_checks"),
        "abort_conditions": verifier.get("abort_conditions"),
        "cleanup_expectations": verifier.get("cleanup_expectations"),
        "default_off": verifier.get("default_off"),
        "live_execution_requested": verifier.get("live_execution_requested"),
        "public_url_value_logged": verifier.get("public_url_value_logged"),
        "secret_values_logged": verifier.get("secret_values_logged"),
    }


def unwrap_verifier_payload(payload: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    if isinstance(payload.get("live_result_verifier"), dict):
        return payload["live_result_verifier"], payload
    if payload.get("schema") == "a90-wsta204-wsta198-live-result-verifier-v1":
        return payload, {"decision": wsta204.SOURCE_PASS_DECISION, "safety": safety_flags()}
    return None, payload


def validate_verifier_payload(path: Path) -> tuple[bool, str, dict[str, Any]]:
    try:
        payload = load_json(path)
    except Exception as exc:  # noqa: BLE001
        return False, "wsta205-blocked-verifier-unreadable", {"error": str(exc)}
    verifier, result_payload = unwrap_verifier_payload(payload)
    if not isinstance(verifier, dict):
        return False, "wsta205-blocked-verifier-missing", {"payload_decision": payload.get("decision")}
    source_audit = resolve_path(verifier.get("source_wsta203_audit", ""))
    handoff_script = resolve_path(verifier.get("handoff_command_script", ""))
    wsta198_script = resolve_path(verifier.get("wsta198_live_command_script", ""))
    verifier_script_path = resolve_path(verifier.get("verifier_script", ""))
    handoff_script_text = handoff_script.read_text(encoding="utf-8") if handoff_script.is_file() else ""
    verifier_script_text = verifier_script_path.read_text(encoding="utf-8") if verifier_script_path.is_file() else ""
    safety = result_payload.get("safety", {}) if isinstance(result_payload.get("safety"), dict) else {}
    mutation = no_mutation_safety(safety)
    serialized = json.dumps(payload, sort_keys=True) + "\n" + handoff_script_text + "\n" + verifier_script_text
    checks = {
        "verifier_private": wsta160.is_under(path, PRIVATE_ROOT),
        "decision_pass": result_payload.get("decision") in (None, wsta204.SOURCE_PASS_DECISION),
        "verifier_state_current": verifier.get("state") in (
            "POST_LIVE_RESULT_VERIFIER_READY_TOKEN_READY_DEFAULT_OFF",
            "POST_LIVE_RESULT_VERIFIER_READY_TOKEN_REQUIRED_DEFAULT_OFF",
        ),
        "audit_current": verifier.get("audit_current") is True,
        "audit_stable_view_match": verifier.get("audit_stable_view_match") is True,
        "ready_for_post_live_verification": verifier.get("ready_for_post_live_verification") is True,
        "source_audit_private": wsta160.is_under(source_audit, PRIVATE_ROOT),
        "source_audit_present": source_audit.is_file(),
        "handoff_script_private": wsta160.is_under(handoff_script, PRIVATE_ROOT),
        "handoff_script_present": handoff_script.is_file(),
        "handoff_script_executable": handoff_script.is_file() and bool(handoff_script.stat().st_mode & 0o100),
        "wsta198_script_private": wsta160.is_under(wsta198_script, PRIVATE_ROOT),
        "wsta198_script_present": wsta198_script.is_file(),
        "wsta198_script_executable": wsta198_script.is_file() and bool(wsta198_script.stat().st_mode & 0o100),
        "verifier_script_private": wsta160.is_under(verifier_script_path, PRIVATE_ROOT),
        "verifier_script_present": verifier_script_path.is_file(),
        "verifier_script_executable": verifier_script_path.is_file() and bool(verifier_script_path.stat().st_mode & 0o100),
        "expected_decision_ok": verifier.get("expected_wsta198_decision") == wsta198.LIVE_PASS_DECISION,
        "required_live_checks_complete": verifier.get("required_live_checks") == wsta204.REQUIRED_LIVE_CHECKS,
        "required_live_safety_true_complete": verifier.get("required_live_safety_true") == wsta204.REQUIRED_LIVE_SAFETY_TRUE,
        "required_live_safety_false_complete": verifier.get("required_live_safety_false") == wsta204.REQUIRED_LIVE_SAFETY_FALSE,
        "required_canary_markers_complete": verifier.get("required_canary_markers") == wsta204.REQUIRED_CANARY_MARKERS,
        "ack_stack_matches_wsta198": verifier.get("operator_acknowledgements_required") == wsta198.ACK_FLAGS,
        "handoff_script_requires_private_token_env": f"${{{wsta193.PRIVATE_TOKEN_ENV}:?private-token-required}}" in handoff_script_text,
        "handoff_script_execs_wsta198_wrapper": str(verifier.get("wsta198_live_command_script")) in handoff_script_text,
        "verifier_script_invokes_wsta204_verify": "--verify-wsta204-live-result" in verifier_script_text,
        "token_value_not_included": verifier.get("token_value_included") is False,
        "correct_token_not_supplied": verifier.get("correct_wsta161_token_supplied") is False,
        "correct_token_not_in_artifact": verifier.get("correct_wsta161_token_in_artifact") is False,
        "default_off": verifier.get("default_off") is True,
        "live_not_requested": verifier.get("live_execution_requested") is False,
        "no_mutation_safety": all(mutation.values()),
        "no_flash_surface": ("native_" + "init_flash.py") not in serialized,
        "no_token_literal": FORBIDDEN_TOKEN_PREFIX not in serialized,
        "no_external_network_inputs": wsta198.no_external_network_inputs(serialized),
        "secret_values_zero": verifier.get("secret_values_logged") == 0,
        "public_url_not_logged": verifier.get("public_url_value_logged") is False,
    }
    if not all(checks.values()):
        return False, "wsta205-blocked-verifier-invalid", {
            "payload": payload,
            "verifier": verifier,
            "checks": checks,
            "mutation_checks": mutation,
        }
    return True, "ok", {
        "payload": payload,
        "verifier": verifier,
        "checks": checks,
        "source_audit": source_audit,
        "handoff_script": handoff_script,
        "wsta198_script": wsta198_script,
        "verifier_script": verifier_script_path,
    }


def wsta204_recheck_args(run_dir: Path, audit_path: Path) -> argparse.Namespace:
    return argparse.Namespace(
        run_id="wsta205-wsta204-recheck",
        run_dir=run_dir,
        source_wsta203_audit_json=audit_path,
        wsta198_live_result_json=None,
        emit_wsta204_live_result_verifier=True,
        verify_wsta204_live_result=False,
        print_template=False,
        print_full_json=False,
    )


def validate_recheck(recheck: dict[str, Any]) -> dict[str, bool]:
    checks = recheck.get("checks", {}) if isinstance(recheck.get("checks"), dict) else {}
    safety = recheck.get("safety", {}) if isinstance(recheck.get("safety"), dict) else {}
    verifier = recheck.get("live_result_verifier", {}) if isinstance(recheck.get("live_result_verifier"), dict) else {}
    mutation = no_mutation_safety(safety)
    return {
        "decision_pass": recheck.get("decision") == wsta204.SOURCE_PASS_DECISION,
        "audit_valid": checks.get("audit_valid") is True,
        "wsta203_recheck_valid": checks.get("wsta203_recheck_valid") is True,
        "audit_stable_view_match": checks.get("audit_stable_view_match") is True,
        "live_result_verifier_valid": checks.get("live_result_verifier_valid") is True,
        "audit_current": verifier.get("audit_current") is True,
        "ready_for_post_live_verification": verifier.get("ready_for_post_live_verification") is True,
        "no_mutation_safety": all(mutation.values()),
    }


def transaction_script(verifier_path: Path, handoff_script: Path) -> str:
    return "\n".join([
        "#!/bin/sh",
        "set -eu",
        f"cd '{REPO_ROOT}'",
        "ts=$(date +%Y%m%dT%H%M%SKST)",
        'export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-/tmp/a90_pycache}"',
        f': "${{{wsta193.PRIVATE_TOKEN_ENV}:?private-token-required}}"',
        'SELF_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)',
        'STATUS_OUT="${SELF_DIR}/wsta205_preflight_wsta204_${ts}.json"',
        'LIVE_OUT="${SELF_DIR}/wsta205_wsta198_live_stdout_${ts}.json"',
        'LIVE_PATH_TXT="${SELF_DIR}/wsta205_wsta198_live_result_path_${ts}.txt"',
        'VERIFY_OUT="${SELF_DIR}/wsta205_wsta204_verify_${ts}.json"',
        "python3 workspace/public/src/scripts/server-distro/run_wsta204_wsta203_live_result_verifier.py \\",
        f"  --source-wsta203-audit-json '{rel(verifier_path)}' \\",
        "  --emit-wsta204-live-result-verifier \\",
        '  --run-id "wsta205-preflight-wsta204-${ts}" \\',
        '  --print-full-json > "$STATUS_OUT"',
        "python3 - \"$STATUS_OUT\" <<'PY'",
        "import json, sys",
        "payload = json.load(open(sys.argv[1], 'r', encoding='utf-8'))",
        "verifier = payload.get('live_result_verifier') or {}",
        "assert payload.get('decision') == 'wsta204-wsta203-live-result-verifier-source-pass', payload.get('decision')",
        "assert verifier.get('ready_for_immediate_live_execute') is True, verifier",
        "assert verifier.get('private_token_env_present') is True, verifier",
        "assert verifier.get('private_token_matches_wsta161') is True, verifier",
        "assert payload.get('safety', {}).get('live_command_executed') is False, payload.get('safety')",
        "PY",
        f"'{rel(handoff_script)}' > \"$LIVE_OUT\"",
        "python3 - \"$LIVE_OUT\" \"$LIVE_PATH_TXT\" <<'PY'",
        "import json, pathlib, sys",
        "payload = json.load(open(sys.argv[1], 'r', encoding='utf-8'))",
        "assert payload.get('decision') == 'wsta198-seccomp-load-canary-ssh-adapter-live-pass', payload.get('decision')",
        "run_dir = payload.get('run_dir')",
        "assert isinstance(run_dir, str) and run_dir, payload",
        "result_path = pathlib.Path(run_dir) / 'wsta198_result.json'",
        "assert result_path.is_file(), str(result_path)",
        "pathlib.Path(sys.argv[2]).write_text(str(result_path) + '\\n', encoding='utf-8')",
        "PY",
        "python3 workspace/public/src/scripts/server-distro/run_wsta204_wsta203_live_result_verifier.py \\",
        f"  --source-wsta203-audit-json '{rel(verifier_path)}' \\",
        "  --verify-wsta204-live-result \\",
        '  --wsta198-live-result-json "$(cat "$LIVE_PATH_TXT")" \\',
        '  --run-id "wsta205-postverify-wsta204-${ts}" \\',
        '  --print-full-json > "$VERIFY_OUT"',
        "python3 - \"$VERIFY_OUT\" <<'PY'",
        "import json, sys",
        "payload = json.load(open(sys.argv[1], 'r', encoding='utf-8'))",
        "verification = payload.get('live_result_verification') or {}",
        "assert payload.get('decision') == 'wsta204-wsta198-live-result-verify-pass', payload.get('decision')",
        "assert verification.get('state') == 'WSTA198_LIVE_RESULT_ACCEPTED', verification",
        "PY",
        'printf "%s\\n" "$VERIFY_OUT"',
        "",
    ])


def build_bundle(
    verifier_path: Path,
    verifier: dict[str, Any],
    recheck_result: dict[str, Any],
    recheck_path: Path,
    token_checks: dict[str, bool],
    out_json: Path,
    out_sh: Path,
    out_md: Path,
) -> dict[str, Any]:
    recheck_verifier = recheck_result.get("live_result_verifier", {})
    current = bool(
        recheck_result.get("decision") == wsta204.SOURCE_PASS_DECISION
        and isinstance(recheck_verifier, dict)
        and stable_verifier_view(verifier) == stable_verifier_view(recheck_verifier)
    )
    token_ready = bool(token_checks.get("private_token_env_present") and token_checks.get("private_token_matches_wsta161"))
    state = "STALE_WSTA204_VERIFIER_RECHECK_REQUIRED"
    if current and token_ready:
        state = "LIVE_TRANSACTION_BUNDLE_READY_TOKEN_READY_DEFAULT_OFF"
    elif current:
        state = "LIVE_TRANSACTION_BUNDLE_READY_TOKEN_REQUIRED_DEFAULT_OFF"
    return {
        "schema": "a90-wsta205-wsta204-live-transaction-bundle-v1",
        "state": state,
        "source_wsta204_verifier": rel(verifier_path),
        "fresh_wsta204_recheck_result": rel(recheck_path),
        "transaction_script": rel(out_sh),
        "handoff_command_script": verifier.get("handoff_command_script"),
        "wsta198_live_command_script": verifier.get("wsta198_live_command_script"),
        "wsta204_verifier_script": verifier.get("verifier_script"),
        "selected_transport": verifier.get("selected_transport"),
        "canary_service": verifier.get("canary_service"),
        "expected_wsta198_decision": verifier.get("expected_wsta198_decision"),
        "expected_wsta204_verify_decision": wsta204.VERIFY_PASS_DECISION,
        "verifier_current": current,
        "verifier_stable_view_match": current,
        "ready_for_transaction_execution": current,
        "ready_for_immediate_live_execute": current and token_ready,
        "private_token_env": wsta193.PRIVATE_TOKEN_ENV,
        "private_token_env_present": token_checks.get("private_token_env_present") is True,
        "private_token_matches_wsta161": token_checks.get("private_token_matches_wsta161") is True,
        "token_value_included": False,
        "correct_wsta161_token_supplied": False,
        "correct_wsta161_token_in_artifact": False,
        "transaction_steps": [
            "require-private-token-env",
            "rerun-wsta204-source-preflight-and-require-token-ready",
            "execute-existing-private-wsta200-handoff-wrapper",
            "extract-private-wsta198-result-json-path",
            "run-wsta204-verify-mode-on-wsta198-result",
            "require-wsta204-live-result-accepted",
        ],
        "operator_acknowledgements_required": verifier.get("operator_acknowledgements_required") or [],
        "operator_preflight_checks": [
            "WSTA205-emitted-single-live-transaction-bundle",
            "WSTA205-rechecked-WSTA204-from-current-WSTA203-audit",
            "operator-must-deliberately-run-private-transaction-script",
            *(verifier.get("operator_preflight_checks") or []),
        ],
        "abort_conditions": verifier.get("abort_conditions") or [],
        "cleanup_expectations": verifier.get("cleanup_expectations") or [],
        "json_path": rel(out_json),
        "markdown_path": rel(out_md),
        "default_off": True,
        "live_execution_requested": False,
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def validate_bundle(bundle: dict[str, Any], script_text: str) -> dict[str, bool]:
    serialized = json.dumps(bundle, sort_keys=True) + "\n" + script_text
    return {
        "schema_ok": bundle.get("schema") == "a90-wsta205-wsta204-live-transaction-bundle-v1",
        "state_current": bundle.get("state") in (
            "LIVE_TRANSACTION_BUNDLE_READY_TOKEN_READY_DEFAULT_OFF",
            "LIVE_TRANSACTION_BUNDLE_READY_TOKEN_REQUIRED_DEFAULT_OFF",
        ),
        "verifier_current": bundle.get("verifier_current") is True,
        "verifier_stable_view_match": bundle.get("verifier_stable_view_match") is True,
        "ready_for_transaction_execution": bundle.get("ready_for_transaction_execution") is True,
        "script_has_strict_shell": script_text.startswith("#!/bin/sh\nset -eu\n"),
        "script_requires_private_token_env": f"${{{wsta193.PRIVATE_TOKEN_ENV}:?private-token-required}}" in script_text,
        "script_reruns_wsta204_source": "--emit-wsta204-live-result-verifier" in script_text,
        "script_requires_token_ready": "ready_for_immediate_live_execute" in script_text,
        "script_executes_handoff_wrapper": str(bundle.get("handoff_command_script")) in script_text,
        "script_extracts_wsta198_result": "wsta198_result.json" in script_text,
        "script_runs_wsta204_verify": "--verify-wsta204-live-result" in script_text,
        "script_requires_wsta204_verify_pass": wsta204.VERIFY_PASS_DECISION in script_text,
        "transaction_steps_complete": bundle.get("transaction_steps") == [
            "require-private-token-env",
            "rerun-wsta204-source-preflight-and-require-token-ready",
            "execute-existing-private-wsta200-handoff-wrapper",
            "extract-private-wsta198-result-json-path",
            "run-wsta204-verify-mode-on-wsta198-result",
            "require-wsta204-live-result-accepted",
        ],
        "token_value_not_included": bundle.get("token_value_included") is False,
        "correct_token_not_supplied": bundle.get("correct_wsta161_token_supplied") is False,
        "correct_token_not_in_artifact": bundle.get("correct_wsta161_token_in_artifact") is False,
        "ack_stack_matches_wsta198": bundle.get("operator_acknowledgements_required") == wsta198.ACK_FLAGS,
        "default_off": bundle.get("default_off") is True,
        "live_not_requested": bundle.get("live_execution_requested") is False,
        "no_flash_surface": ("native_" + "init_flash.py") not in serialized,
        "no_token_literal": FORBIDDEN_TOKEN_PREFIX not in serialized,
        "no_external_network_inputs": wsta198.no_external_network_inputs(serialized),
        "secret_values_zero": bundle.get("secret_values_logged") == 0,
        "public_url_not_logged": bundle.get("public_url_value_logged") is False,
    }


def markdown(bundle: dict[str, Any]) -> str:
    lines = [
        "# WSTA204 Live Transaction Bundle",
        "",
        f"- State: `{bundle.get('state')}`",
        f"- Verifier current: `{str(bundle.get('verifier_current')).lower()}`",
        f"- Ready for transaction execution: `{str(bundle.get('ready_for_transaction_execution')).lower()}`",
        f"- Ready for immediate live execute: `{str(bundle.get('ready_for_immediate_live_execute')).lower()}`",
        f"- Token env present: `{str(bundle.get('private_token_env_present')).lower()}`",
        f"- Token matches expected: `{str(bundle.get('private_token_matches_wsta161')).lower()}`",
        f"- Transaction script: `{bundle.get('transaction_script')}`",
        "",
        "## Boundary",
        "",
        "WSTA205 emits the transaction script only. It does not run WSTA200, WSTA198, or WSTA204 verify mode.",
        "",
    ]
    return "\n".join(lines)


def classify(result: dict[str, Any]) -> str:
    checks = result.get("checks", {})
    ordered = (
        ("explicit_emit_gate", "wsta205-blocked-explicit-emit-gate-required"),
        ("private_run_dir", "wsta205-blocked-nonprivate-run-dir"),
        ("verifier_private", "wsta205-blocked-verifier-nonprivate"),
        ("verifier_present", "wsta205-blocked-verifier-missing"),
        ("verifier_valid", result.get("verifier_error") or "wsta205-blocked-verifier-invalid"),
        ("wsta204_recheck_valid", "wsta205-blocked-wsta204-recheck-invalid"),
        ("verifier_stable_view_match", "wsta205-blocked-verifier-drift"),
        ("live_transaction_bundle_valid", "wsta205-blocked-live-transaction-bundle-invalid"),
    )
    for key, decision in ordered:
        if not checks.get(key):
            return str(decision)
    return PASS_DECISION


def run(args: argparse.Namespace) -> dict[str, Any]:
    ts = utc_stamp()
    run_id = args.run_id or f"wsta205-wsta204-live-transaction-bundle-{ts}"
    run_dir = resolve_path(args.run_dir or (DEFAULT_RUN_BASE / run_id))
    verifier_path = resolve_path(args.source_wsta204_verifier_json)
    result: dict[str, Any] = {
        "scope": "WSTA205 host-only WSTA204 live transaction bundle",
        "started_utc": ts,
        "run_dir": rel(run_dir),
        "source_wsta204_verifier_json": rel(verifier_path),
        "safety": safety_flags(),
        "checks": {
            "explicit_emit_gate": bool(args.emit_wsta205_live_transaction_bundle),
            "private_run_dir": wsta160.is_under(run_dir, PRIVATE_ROOT),
            "verifier_private": wsta160.is_under(verifier_path, PRIVATE_ROOT),
            "verifier_present": verifier_path.is_file(),
        },
    }
    if not result["checks"]["private_run_dir"]:
        result["decision"] = classify(result)
        result["ended_utc"] = utc_stamp()
        return result
    run_dir.mkdir(parents=True, exist_ok=True)
    out_path = run_dir / SUMMARY_NAME
    for key in ("explicit_emit_gate", "verifier_private", "verifier_present"):
        if not result["checks"][key]:
            result["decision"] = classify(result)
            result["ended_utc"] = utc_stamp()
            write_json(out_path, result)
            return result

    valid, decision, verifier_info = validate_verifier_payload(verifier_path)
    result["verifier_checks"] = verifier_info.get("checks", {})
    result["checks"]["verifier_valid"] = valid
    result["verifier_error"] = None if valid else decision
    write_json(out_path, result)
    if not valid:
        result["decision"] = classify(result)
        result["ended_utc"] = utc_stamp()
        write_json(out_path, result)
        return result

    recheck_dir = run_dir / "wsta204-recheck"
    recheck_result = wsta204.run(wsta204_recheck_args(recheck_dir, verifier_info["source_audit"]))
    result["safety"]["wsta204_recheck_executed"] = True
    result["wsta204_recheck"] = {
        "run_dir": rel(recheck_dir),
        "result_json": rel(recheck_dir / wsta204.SUMMARY_NAME),
        "verifier_json": rel(recheck_dir / wsta204.VERIFIER_JSON_NAME),
        "decision": recheck_result.get("decision"),
    }
    result["wsta204_recheck_checks"] = validate_recheck(recheck_result)
    result["checks"]["wsta204_recheck_valid"] = all(result["wsta204_recheck_checks"].values())
    result["checks"]["verifier_stable_view_match"] = bool(
        result["checks"]["wsta204_recheck_valid"]
        and stable_verifier_view(verifier_info["verifier"]) == stable_verifier_view(recheck_result["live_result_verifier"])
    )
    result["token_checks"] = private_token_status()
    write_json(out_path, result)
    if not (result["checks"]["wsta204_recheck_valid"] and result["checks"]["verifier_stable_view_match"]):
        result["decision"] = classify(result)
        result["ended_utc"] = utc_stamp()
        write_json(out_path, result)
        return result

    transaction_json = run_dir / TRANSACTION_JSON_NAME
    transaction_sh = run_dir / TRANSACTION_SH_NAME
    transaction_md = run_dir / TRANSACTION_MD_NAME
    script_text = transaction_script(verifier_info["source_audit"], verifier_info["handoff_script"])
    bundle = build_bundle(
        verifier_path,
        verifier_info["verifier"],
        recheck_result,
        recheck_dir / wsta204.SUMMARY_NAME,
        result["token_checks"],
        transaction_json,
        transaction_sh,
        transaction_md,
    )
    result["live_transaction_bundle_checks"] = validate_bundle(bundle, script_text)
    result["checks"]["live_transaction_bundle_valid"] = all(result["live_transaction_bundle_checks"].values())
    result["live_transaction_bundle"] = bundle
    if result["checks"]["live_transaction_bundle_valid"]:
        write_json(transaction_json, result)
        write_text(transaction_sh, script_text)
        transaction_sh.chmod(0o700)
        write_text(transaction_md, markdown(bundle))
        result["safety"]["wsta205_transaction_script_generated"] = True
    result["decision"] = classify(result)
    result["ended_utc"] = utc_stamp()
    write_json(out_path, result)
    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--source-wsta204-verifier-json", type=Path, default=DEFAULT_WSTA204_VERIFIER_JSON)
    parser.add_argument("--emit-wsta205-live-transaction-bundle", action="store_true")
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
        payload = {"decision": "wsta205-runner-error", "error": str(exc)}
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1
    payload = result if args.print_full_json else public_summary(result)
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result.get("decision") == PASS_DECISION else 2


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
