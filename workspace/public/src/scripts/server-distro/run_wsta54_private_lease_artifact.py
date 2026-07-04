#!/usr/bin/env python3
"""WSTA54 host-only private lease artifact generator.

This runner consumes a WSTA53 redacted plan result and materializes a private
lease artifact under ``workspace/private``.  It performs no live/device action:
no native reboot, Wi-Fi association, DHCP, tunnel start, public smoke, userdata
operation, switch-root, or flash.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import secrets
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_wsta53_persistent_exposure_plan as wsta53  # noqa: E402


REPO_ROOT = wsta53.REPO_ROOT
PRIVATE_ROOT = REPO_ROOT / "workspace" / "private"
DEFAULT_RUN_BASE = wsta53.DEFAULT_RUN_BASE
PASS_DECISION = "wsta54-private-lease-artifact-pass"
PRIVATE_LEASE_SCHEMA = "a90-wsta-private-lease-artifact-v1"
REDACTED_MARKER_SCHEMA = "a90-wsta-redacted-lease-marker-v1"
FORBIDDEN_PUBLIC_FIELDS = wsta53.FORBIDDEN_PUBLIC_FIELDS
FORBIDDEN_TEXT_PATTERNS = (
    "trycloudflare.com",
    "ssid=",
    "psk=",
    "http://",
    "https://",
)


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def utc_now() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc)


def utc_stamp(value: _dt.datetime | None = None) -> str:
    return (value or utc_now()).strftime("%Y%m%dT%H%M%SZ")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def resolve_run_dir(args: argparse.Namespace, ts: str) -> Path:
    run_id = args.run_id or f"wsta54-private-lease-artifact-{ts}"
    run_dir = args.run_dir or (DEFAULT_RUN_BASE / run_id)
    return resolve_path(run_dir)


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def forbidden_fields(payload: Any) -> list[str]:
    found: list[str] = []

    def walk(value: Any, prefix: str = "") -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_prefix = f"{prefix}.{key}" if prefix else str(key)
                if str(key).lower() in FORBIDDEN_PUBLIC_FIELDS:
                    found.append(child_prefix)
                walk(child, child_prefix)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{prefix}[{index}]")

    walk(payload)
    return sorted(found)


def redaction_findings(payload: Any) -> list[str]:
    text = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    lowered = text.lower()
    findings = [f"forbidden-text:{item}" for item in FORBIDDEN_TEXT_PATTERNS if item in lowered]
    for field in forbidden_fields(payload):
        findings.append(f"forbidden-field:{field}")
    return sorted(set(findings))


def template() -> dict[str, Any]:
    return {
        "scope": "WSTA54 host-only private lease artifact generation",
        "input": {
            "wsta53_result_json": "workspace/private/runs/server-distro/<wsta53-run>/wsta53_result.json",
            "required_wsta53_decision": wsta53.PASS_DECISION,
        },
        "output": {
            "private_lease_schema": PRIVATE_LEASE_SCHEMA,
            "redacted_marker_schema": REDACTED_MARKER_SCHEMA,
            "private_lease_artifact": "workspace/private/runs/server-distro/<wsta54-run>/wsta54_private_lease.json",
            "redacted_marker": "workspace/private/runs/server-distro/<wsta54-run>/wsta54_redacted_lease_marker.json",
            "result": "workspace/private/runs/server-distro/<wsta54-run>/wsta54_result.json",
        },
        "live_action": False,
        "future_live_allowed": False,
    }


def live_safety_flags() -> dict[str, Any]:
    return {
        "device_action": False,
        "boot_flash": False,
        "native_reboot": False,
        "wifi_connect": False,
        "dhcp": False,
        "public_tunnel": False,
        "public_smoke": False,
        "userdata_touch": False,
        "switch_root": False,
        "native_confirm_token_value_logged": False,
        "public_confirm_token_value_logged": False,
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def validate_wsta53_result(payload: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
    findings = redaction_findings(payload)
    if findings:
        return False, "wsta54-blocked-wsta53-redaction-finding", {"findings": findings}
    if payload.get("decision") != wsta53.PASS_DECISION:
        return False, "wsta54-blocked-wsta53-not-pass", {"decision": payload.get("decision")}
    request = dict(payload.get("request_redacted") or {})
    plan = dict(payload.get("plan_redacted") or {})
    safety = dict(payload.get("safety") or {})
    if plan.get("wsta54_private_artifact_ready") is not True:
        return False, "wsta54-blocked-artifact-ready-marker-missing", {}
    if plan.get("future_live_allowed") is not False:
        return False, "wsta54-blocked-wsta53-must-not-authorize-live", {}
    if plan.get("public_url_value_logged") is not False:
        return False, "wsta54-blocked-public-url-logged", {}
    if plan.get("secret_values_logged") not in (0, "0", None):
        return False, "wsta54-blocked-secret-values-logged", {}
    if request.get("schema") != wsta53.LEASE_SCHEMA:
        return False, "wsta54-blocked-schema", {"schema": request.get("schema")}
    if request.get("mode") != wsta53.LEASE_MODE:
        return False, "wsta54-blocked-mode", {"mode": request.get("mode")}
    try:
        ttl_sec = int(request.get("ttl_sec"))
    except (TypeError, ValueError):
        return False, "wsta54-blocked-ttl-invalid", {"ttl_sec": request.get("ttl_sec")}
    if ttl_sec <= 0 or ttl_sec > wsta53.MAX_TTL_SEC:
        return False, "wsta54-blocked-ttl-out-of-range", {
            "ttl_sec": ttl_sec,
            "maximum_lease_ttl_sec": wsta53.MAX_TTL_SEC,
        }
    if request.get("operator_ack_credentialed_wifi") is not True:
        return False, "wsta54-blocked-credentialed-wifi-ack-required", {}
    if request.get("operator_ack_public_exposure") is not True:
        return False, "wsta54-blocked-public-exposure-ack-required", {}
    if request.get("native_confirm_token_source") != "private":
        return False, "wsta54-blocked-native-confirm-token-private-source-required", {}
    if request.get("public_confirm_token_source") != "private":
        return False, "wsta54-blocked-public-confirm-token-private-source-required", {}
    if request.get("public_url_storage") != "workspace/private-only":
        return False, "wsta54-blocked-public-url-private-storage-required", {}
    for key, expected in live_safety_flags().items():
        if safety.get(key) != expected:
            return False, "wsta54-blocked-wsta53-live-safety-flag", {
                "flag": key,
                "expected": expected,
                "observed": safety.get(key),
            }
    return True, "ok", {
        "ttl_sec": ttl_sec,
        "request": request,
        "plan": plan,
    }


def private_lease_artifact(
    source_path: Path,
    wsta53_result: dict[str, Any],
    detail: dict[str, Any],
    issued: _dt.datetime,
) -> dict[str, Any]:
    ttl_sec = int(detail["ttl_sec"])
    expires = issued + _dt.timedelta(seconds=ttl_sec)
    plan = detail["plan"]
    return {
        "schema": PRIVATE_LEASE_SCHEMA,
        "source_contract": "wsta52-persistent-exposure-design",
        "source_wsta53_result_json": rel(source_path),
        "source_wsta53_decision": wsta53_result.get("decision"),
        "mode": wsta53.LEASE_MODE,
        "state": "ARMED_PRIVATE_LEASE",
        "lease_id": f"wsta54-{secrets.token_hex(8)}",
        "issued_utc": utc_stamp(issued),
        "expires_utc": utc_stamp(expires),
        "ttl_sec": ttl_sec,
        "maximum_lease_ttl_sec": wsta53.MAX_TTL_SEC,
        "profile_label_redacted": "wsta-persistent-dpublic",
        "operator_identity_marker": "operator-approved-private-source",
        "confirm_token_sources": {
            "native": "private",
            "public": "private",
        },
        "public_url_storage": "workspace/private-only",
        "public_url_value_logged": False,
        "secret_values_logged": 0,
        "default_state": "public-off",
        "boot_autostart_without_valid_private_lease": False,
        "renewal_requires_host_gate": True,
        "wsta54_live_allowed": False,
        "wsta55_explicit_live_gate_required": True,
        "host_only_preflight": {
            "wsta53_pass": True,
            "lease_ttl_within_cap": True,
            "credentialed_wifi_ack": True,
            "public_exposure_ack": True,
            "native_confirm_token_private": True,
            "public_confirm_token_private": True,
            "private_run_dir_required": True,
            "bridge_status_ok": "deferred-to-wsta55-live-gate",
            "selftest_fail_zero": "deferred-to-wsta55-live-gate",
            "wsta45_preflight_pass": "deferred-to-wsta55-live-gate",
            "wsta28_scan_green_recent": "deferred-to-wsta55-live-gate",
        },
        "cleanup_required": list(plan.get("cleanup_required") or []),
    }


def redacted_marker(artifact: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": REDACTED_MARKER_SCHEMA,
        "source_contract": artifact["source_contract"],
        "mode": artifact["mode"],
        "state": artifact["state"],
        "lease_id_present": True,
        "lease_id_value_redacted": True,
        "issued_utc": artifact["issued_utc"],
        "expires_utc": artifact["expires_utc"],
        "ttl_sec": artifact["ttl_sec"],
        "default_state": artifact["default_state"],
        "renewal_requires_host_gate": True,
        "public_url_value_logged": False,
        "secret_values_logged": 0,
        "wsta55_explicit_live_gate_required": True,
    }


def public_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": result.get("decision"),
        "run_dir": result.get("run_dir"),
        "gate_decision": result.get("gate_decision"),
        "source_wsta53_result_json": result.get("source_wsta53_result_json"),
        "private_lease_artifact": result.get("private_lease_artifact"),
        "redacted_marker": result.get("redacted_marker"),
        "lease_redacted": result.get("lease_redacted", {}),
        "safety": result.get("safety", {}),
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    started = utc_now()
    ts = utc_stamp(started)
    run_dir = resolve_run_dir(args, ts)
    base: dict[str, Any] = {
        "scope": "WSTA54 host-only private lease artifact generation",
        "started_utc": ts,
        "run_dir": rel(run_dir),
        "decision": "wsta54-blocked",
        "gate_decision": "not-run",
        "safety": live_safety_flags(),
    }
    if not is_under(run_dir, PRIVATE_ROOT):
        base["decision"] = "wsta54-blocked-nonprivate-run-dir"
        base["gate_decision"] = base["decision"]
        base["ended_utc"] = utc_stamp()
        return base

    run_dir.mkdir(parents=True, exist_ok=True)
    out_path = run_dir / "wsta54_result.json"
    if args.wsta53_result_json is None:
        base["decision"] = "wsta54-blocked-wsta53-result-required"
        base["gate_decision"] = base["decision"]
        base["ended_utc"] = utc_stamp()
        write_json(out_path, base)
        return base

    source_path = resolve_path(args.wsta53_result_json)
    base["source_wsta53_result_json"] = rel(source_path)
    if not is_under(source_path, PRIVATE_ROOT):
        base["decision"] = "wsta54-blocked-nonprivate-wsta53-result"
        base["gate_decision"] = base["decision"]
        base["ended_utc"] = utc_stamp()
        write_json(out_path, base)
        return base

    try:
        wsta53_result = load_json(source_path)
    except Exception as exc:  # noqa: BLE001
        base["decision"] = "wsta54-blocked-wsta53-result-unreadable"
        base["gate_decision"] = base["decision"]
        base["gate_detail"] = {"error": str(exc)}
        base["ended_utc"] = utc_stamp()
        write_json(out_path, base)
        return base

    gate_ok, gate_decision, detail = validate_wsta53_result(wsta53_result)
    base["gate_decision"] = gate_decision
    base["gate_detail"] = detail
    if not gate_ok:
        base["decision"] = gate_decision
        base["ended_utc"] = utc_stamp()
        write_json(out_path, base)
        return base

    artifact_path = run_dir / "wsta54_private_lease.json"
    marker_path = run_dir / "wsta54_redacted_lease_marker.json"
    artifact = private_lease_artifact(source_path, wsta53_result, detail, started)
    marker = redacted_marker(artifact)
    findings = redaction_findings(public_summary({**base, "lease_redacted": marker}))
    if findings:
        base["decision"] = "wsta54-blocked-public-summary-redaction-finding"
        base["gate_decision"] = base["decision"]
        base["gate_detail"] = {"findings": findings}
        base["ended_utc"] = utc_stamp()
        write_json(out_path, base)
        return base

    write_json(artifact_path, artifact)
    write_json(marker_path, marker)
    base.update({
        "decision": PASS_DECISION,
        "private_lease_artifact": rel(artifact_path),
        "redacted_marker": rel(marker_path),
        "lease_redacted": marker,
        "private_lease_contains_lease_id": True,
        "lease_id_value_redacted_from_result": True,
        "ended_utc": utc_stamp(),
    })
    write_json(out_path, base)
    return base


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--wsta53-result-json", type=Path)
    parser.add_argument("--print-template", action="store_true")
    parser.add_argument("--print-full-json", action="store_true")
    return parser


def main_with_args(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    if args.print_template:
        print(json.dumps(template(), indent=2, sort_keys=True))
        return 0
    result = run(args)
    payload = result if args.print_full_json else public_summary(result)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.get("decision") == PASS_DECISION else 2


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
