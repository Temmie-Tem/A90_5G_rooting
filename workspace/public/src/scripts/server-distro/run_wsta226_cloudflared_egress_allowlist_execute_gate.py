#!/usr/bin/env python3
"""WSTA226 attended cloudflared egress allowlist execute gate.

WSTA223 planned the live gate and WSTA225 propagated the egress flags through
the operator chain.  WSTA226 is the final operator wrapper: by default it
prepares the WSTA88 default-off execute gate, and optional live delegation is
available only behind the full acknowledgement stack plus a private route
artifact containing DNS/TLS egress values.

This unit does not flash or mutate packet filters by default.
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

import run_wsta88_persistent_operator_workflow as wsta88  # noqa: E402
import run_wsta223_cloudflared_egress_allowlist_live_gate_plan as wsta223  # noqa: E402


REPO_ROOT = wsta88.REPO_ROOT
PRIVATE_ROOT = wsta88.PRIVATE_ROOT
DEFAULT_RUN_BASE = wsta88.DEFAULT_RUN_BASE
DEFAULT_WSTA223_RESULT = (
    DEFAULT_RUN_BASE
    / "wsta223-cloudflared-egress-allowlist-live-gate-plan-20260705T222716KST"
    / wsta223.SUMMARY_NAME
)
PASS_DECISION = "wsta226-cloudflared-egress-allowlist-execute-gate-preflight-pass"
LIVE_PASS_DECISION = "wsta226-cloudflared-egress-allowlist-execute-gate-live-pass"
ROUTE_SCHEMA = "a90-wsta226-cloudflared-egress-route-v1"
ROUTE_STATE = "CLOUDFLARED_EGRESS_ROUTE_DERIVED_PRIVATE"
RESULT_NAME = "wsta226_result.json"
GATE_NAME = "wsta226_cloudflared_egress_execute_gate.json"
MARKDOWN_NAME = "wsta226_cloudflared_egress_execute_gate.md"


def rel(path: Path) -> str:
    return wsta88.rel(path)


def utc_stamp() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def is_under(path: Path, root: Path) -> bool:
    return wsta88.is_under(path, root)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fp:
        payload = json.load(fp)
    if not isinstance(payload, dict):
        raise ValueError(f"expected object JSON: {path}")
    return payload


def get_dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def live_requested(args: argparse.Namespace) -> bool:
    return bool(getattr(args, "execute_live_egress_allowlist", False))


def safety_flags(args: argparse.Namespace, live_gate_ok: bool = False) -> dict[str, Any]:
    live = live_requested(args)
    return {
        "device_action": live and live_gate_ok,
        "boot_flash": False,
        "native_reboot": live and live_gate_ok and bool(args.allow_native_reboot),
        "wifi_connect": "wsta88-explicit-live-gated" if live and live_gate_ok else False,
        "dhcp": "wsta88-explicit-live-gated" if live and live_gate_ok else False,
        "public_tunnel": "wsta88-explicit-public-live-gated" if live and live_gate_ok else False,
        "public_smoke": "wsta88-explicit-public-live-gated" if live and live_gate_ok else False,
        "packet_filter_mutation": "wsta88-explicit-egress-allowlist-gated" if live and live_gate_ok else False,
        "userdata_touch": False,
        "switch_root": False,
        "rootfs_mutation": False,
        "lsm_profile_load": False,
        "route_values_logged": False,
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def public_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": result.get("decision"),
        "run_dir": result.get("run_dir"),
        "gate_decision": result.get("gate_decision"),
        "execute_gate": result.get("execute_gate", {}),
        "route_summary": result.get("route_summary", {}),
        "wsta88_redacted": result.get("wsta88_redacted", {}),
        "checks": result.get("checks", {}),
        "safety": result.get("safety", {}),
    }


def require_private_file(path_arg: Path | None, label: str) -> tuple[Path | None, str | None]:
    if path_arg is None:
        return None, f"wsta226-blocked-{label}-required"
    path = resolve_path(path_arg)
    if not is_under(path, PRIVATE_ROOT):
        return None, f"wsta226-blocked-{label}-nonprivate"
    if not path.is_file():
        return None, f"wsta226-blocked-{label}-missing"
    return path, None


def validate_wsta223_result(payload: dict[str, Any]) -> dict[str, bool]:
    plan = get_dict(payload, "live_gate_plan")
    plan_checks = wsta223.validate_plan(plan)
    checks = get_dict(payload, "checks")
    return {
        "decision_pass": payload.get("decision") == wsta223.PASS_DECISION,
        "plan_ready_check": checks.get("plan_ready") is True,
        "plan_schema_ok": plan_checks.get("schema_ok") is True,
        "plan_state_ok": plan_checks.get("state_ok") is True,
        "plan_helper_ops_complete": plan_checks.get("helper_ops_complete") is True,
        "plan_operator_acks_complete": plan_checks.get("operator_acks_complete") is True,
        "plan_route_fail_closed": plan_checks.get("route_fail_closed") is True,
        "plan_owner_scoped_output": plan_checks.get("owner_scoped_output") is True,
        "plan_redaction_clean": plan_checks.get("redaction_clean") is True,
        "redaction_clean": not bool(wsta88.redaction_findings(wsta223.public_summary(payload))),
    }


def route_values(route: dict[str, Any], key: str) -> list[str]:
    value = route.get(key)
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    return []


def validate_route_artifact(payload: dict[str, Any]) -> dict[str, bool]:
    return {
        "schema_ok": payload.get("schema") == ROUTE_SCHEMA,
        "state_ok": payload.get("state") == ROUTE_STATE,
        "dns4_present": bool(route_values(payload, "dns4")),
        "tls4_present": bool(route_values(payload, "tls4")),
        "route_values_private": payload.get("route_values_private") is True,
        "route_values_logged_false": payload.get("route_values_logged") is False,
        "public_url_not_logged": payload.get("public_url_value_logged") is False,
        "secrets_not_logged": payload.get("secret_values_logged") in (0, "0", None),
        "redaction_clean_public_view": not bool(wsta88.redaction_findings(route_summary(payload))),
    }


def route_summary(route: dict[str, Any] | None) -> dict[str, Any]:
    route = route or {}
    return {
        "schema": route.get("schema"),
        "state": route.get("state"),
        "dns4_count": len(route_values(route, "dns4")),
        "tls4_count": len(route_values(route, "tls4")),
        "route_values_private": route.get("route_values_private") is True,
        "route_values_logged": False,
        "route_values_redacted": True,
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def explicit_prepare_gate(args: argparse.Namespace) -> tuple[bool, str]:
    if not args.prepare_attended_egress_gate:
        return False, "wsta226-blocked-prepare-attended-egress-gate-required"
    if not args.ack_credentialed_wifi:
        return False, "wsta226-blocked-credentialed-wifi-ack-required"
    if not args.ack_public_exposure:
        return False, "wsta226-blocked-public-exposure-ack-required"
    return True, "ok"


def explicit_live_gate(args: argparse.Namespace, route: dict[str, Any] | None) -> tuple[bool, str]:
    if not args.execute_live_egress_allowlist:
        return False, "wsta226-blocked-execute-live-egress-allowlist-required"
    if not args.allow_operator_live:
        return False, "wsta226-blocked-operator-live-allow-required"
    if not args.allow_native_reboot:
        return False, "wsta226-blocked-native-reboot-allow-required"
    if not args.allow_public_live:
        return False, "wsta226-blocked-public-live-allow-required"
    if not args.ack_packet_filter_mutation:
        return False, "wsta226-blocked-packet-filter-mutation-ack-required"
    if not args.force_packet_filter_restore_proof:
        return False, "wsta226-blocked-packet-filter-restore-proof-required"
    if not args.force_cloudflared_egress_allowlist_proof:
        return False, "wsta226-blocked-cloudflared-egress-allowlist-proof-required"
    if not args.force_control_plane_proof:
        return False, "wsta226-blocked-control-plane-proof-required"
    if not args.force_public_off_proof:
        return False, "wsta226-blocked-public-off-proof-required"
    if not args.force_ttl_expiry_proof:
        return False, "wsta226-blocked-ttl-expiry-proof-required"
    if not args.force_manual_stop_proof:
        return False, "wsta226-blocked-manual-stop-proof-required"
    if args.native_confirm_token != wsta88.wsta80.wsta58.wsta55.wsta45.wsta25.NATIVE_CONFIRM_TOKEN:
        return False, "wsta226-blocked-native-confirm-token-required"
    if args.public_confirm_token != wsta88.wsta80.wsta58.wsta55.wsta45.PUBLIC_CONFIRM_TOKEN:
        return False, "wsta226-blocked-public-confirm-token-required"
    if route is None:
        return False, "wsta226-blocked-route-artifact-required"
    route_checks = validate_route_artifact(route)
    if not all(route_checks.values()):
        return False, "wsta226-blocked-route-artifact-invalid"
    return True, "ok"


def wsta88_args(args: argparse.Namespace, run_dir: Path, route: dict[str, Any] | None, *, live: bool) -> argparse.Namespace:
    argv = [
        "--run-dir",
        str(run_dir / "wsta88-cloudflared-egress-allowlist"),
        "--prepare-to-execute",
        "--ttl-sec",
        str(args.ttl_sec),
        "--ack-credentialed-wifi",
        "--ack-public-exposure",
        "--native-confirm-token-source",
        "private",
        "--public-confirm-token-source",
        "private",
        "--ready-index",
        str(args.ready_index),
        "--min-initial-seconds-remaining",
        str(args.min_initial_seconds_remaining),
        "--max-sessions",
        str(args.max_sessions),
        "--max-retire-markers",
        str(args.max_retire_markers),
        "--max-packets",
        str(args.max_packets),
        "--max-briefs",
        str(args.max_briefs),
        "--bridge-host",
        args.bridge_host,
        "--bridge-port",
        str(args.bridge_port),
        "--timeout",
        str(args.timeout),
    ]
    if live:
        assert route is not None
        argv.extend([
            "--execute-wsta58-from-status",
            "--allow-operator-live",
            "--allow-native-reboot",
            "--allow-public-live",
            "--ack-packet-filter-mutation",
            "--force-packet-filter-restore-proof",
            "--force-ttl-expiry-proof",
            "--force-manual-stop-proof",
            "--native-confirm-token",
            args.native_confirm_token,
            "--public-confirm-token",
            args.public_confirm_token,
            "--local-image",
            str(args.local_image),
            "--local-image-sha256",
            args.local_image_sha256,
            "--remote-image",
            args.remote_image,
            "--remote-clean-image",
            args.remote_clean_image,
            "--enable-cloudflared-egress-allowlist",
            "--force-cloudflared-egress-allowlist-proof",
        ])
        for value in route_values(route, "dns4"):
            argv.extend(["--cloudflared-egress-dns4", value])
        for value in route_values(route, "tls4"):
            argv.extend(["--cloudflared-egress-tls4", value])
    return wsta88.build_arg_parser().parse_args(argv)


def build_execute_gate(wsta223_path: Path, args: argparse.Namespace, route: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "state": "READY_FOR_ATTENDED_WSTA88_EGRESS_ALLOWLIST_LIVE_GATE",
        "wsta223_live_gate_plan_result": rel(wsta223_path),
        "wsta88_default_off_preflight_required": True,
        "route_artifact_required_for_live": True,
        "route_summary": route_summary(route),
        "optional_live_execution": [
            "--execute-live-egress-allowlist",
            "--allow-operator-live",
            "--allow-native-reboot",
            "--allow-public-live",
            "--ack-packet-filter-mutation",
            "--force-packet-filter-restore-proof",
            "--force-cloudflared-egress-allowlist-proof",
            "--force-control-plane-proof",
            "--force-public-off-proof",
            "--force-ttl-expiry-proof",
            "--force-manual-stop-proof",
            "--native-confirm-token",
            "<native-confirm-token>",
            "--public-confirm-token",
            "<public-confirm-token>",
            "--route-artifact-json",
            "workspace/private/runs/server-distro/<wsta226-route>/cloudflared_egress_route.json",
        ],
        "default_public_off": True,
        "live_execution_requested": False,
        "route_values_logged": False,
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def markdown(result: dict[str, Any]) -> str:
    gate = get_dict(result, "execute_gate")
    route = get_dict(result, "route_summary")
    return "\n".join([
        "# WSTA226 Cloudflared Egress Execute Gate",
        "",
        f"- Decision: `{result.get('decision')}`",
        f"- State: `{gate.get('state')}`",
        f"- Live execution requested: `{str(bool(result.get('checks', {}).get('live_execution_requested'))).lower()}`",
        f"- DNS route count: `{route.get('dns4_count')}`",
        f"- TLS route count: `{route.get('tls4_count')}`",
        "- Route values logged: `false`",
        "- Public URL logged: `false`",
        "",
        "This wrapper delegates only to WSTA88 and does not execute live by default.",
        "",
    ])


def fail_result(result: dict[str, Any], out_path: Path, decision: str) -> dict[str, Any]:
    result["decision"] = decision
    result["gate_decision"] = decision
    result["ended_utc"] = utc_stamp()
    write_json(out_path, result)
    return result


def run(args: argparse.Namespace) -> dict[str, Any]:
    ts = utc_stamp()
    run_id = args.run_id or f"wsta226-cloudflared-egress-allowlist-execute-gate-{ts}"
    run_dir = resolve_path(args.run_dir or (DEFAULT_RUN_BASE / run_id))
    result: dict[str, Any] = {
        "scope": "WSTA226 attended cloudflared egress allowlist execute gate",
        "started_utc": ts,
        "run_dir": rel(run_dir),
        "decision": "wsta226-blocked",
        "gate_decision": "not-run",
        "safety": safety_flags(args),
        "checks": {},
    }
    if not is_under(run_dir, PRIVATE_ROOT):
        result["decision"] = "wsta226-blocked-nonprivate-run-dir"
        result["gate_decision"] = result["decision"]
        result["ended_utc"] = utc_stamp()
        return result
    run_dir.mkdir(parents=True, exist_ok=True)
    out_path = run_dir / RESULT_NAME

    prepare_ok, prepare_decision = explicit_prepare_gate(args)
    result["gate_decision"] = prepare_decision
    if not prepare_ok:
        return fail_result(result, out_path, prepare_decision)

    wsta223_path, plan_error = require_private_file(args.wsta223_result_json, "wsta223-result")
    if plan_error or wsta223_path is None:
        return fail_result(result, out_path, plan_error or "wsta226-blocked-wsta223-result")
    wsta223_result = load_json(wsta223_path)
    plan_checks = validate_wsta223_result(wsta223_result)
    result["checks"].update({f"wsta223_{key}": value for key, value in plan_checks.items()})
    result["checks"]["wsta223_plan_ready"] = all(plan_checks.values())
    if not result["checks"]["wsta223_plan_ready"]:
        return fail_result(result, out_path, "wsta226-blocked-wsta223-plan-incomplete")

    route: dict[str, Any] | None = None
    if args.route_artifact_json is not None:
        route_path, route_error = require_private_file(args.route_artifact_json, "route-artifact")
        if route_error or route_path is None:
            return fail_result(result, out_path, route_error or "wsta226-blocked-route-artifact")
        route = load_json(route_path)
        route_checks = validate_route_artifact(route)
        result["checks"].update({f"route_{key}": value for key, value in route_checks.items()})
        result["checks"]["route_artifact_ready"] = all(route_checks.values())
        if not result["checks"]["route_artifact_ready"]:
            result["route_summary"] = route_summary(route)
            return fail_result(result, out_path, "wsta226-blocked-route-artifact-invalid")

    gate = build_execute_gate(wsta223_path, args, route)
    result["execute_gate"] = gate
    result["route_summary"] = route_summary(route)
    write_json(run_dir / GATE_NAME, gate)

    live_gate_ok = False
    if live_requested(args):
        live_gate_ok, live_decision = explicit_live_gate(args, route)
        result["gate_decision"] = live_decision
        result["safety"] = safety_flags(args, live_gate_ok)
        result["checks"]["live_execution_requested"] = True
        result["checks"]["explicit_live_gate"] = live_gate_ok
        if not live_gate_ok:
            return fail_result(result, out_path, live_decision)
    else:
        result["checks"]["live_execution_requested"] = False
        result["checks"]["explicit_live_gate"] = False

    delegated = wsta88.run(wsta88_args(args, run_dir, route, live=live_gate_ok))
    result["wsta88_redacted"] = wsta88.public_summary(delegated)
    if live_gate_ok:
        result["checks"]["wsta88_live_pass"] = delegated.get("decision") == wsta88.PASS_DECISION
        result["decision"] = LIVE_PASS_DECISION if result["checks"]["wsta88_live_pass"] else "wsta226-blocked-wsta88-live"
    else:
        result["checks"]["wsta88_preflight_pass"] = delegated.get("decision") == wsta88.PREFLIGHT_DECISION
        result["decision"] = PASS_DECISION if result["checks"]["wsta88_preflight_pass"] else "wsta226-blocked-wsta88-preflight"
    result["gate_decision"] = "ok" if result["decision"] in {PASS_DECISION, LIVE_PASS_DECISION} else result["decision"]
    result["ended_utc"] = utc_stamp()

    findings = wsta88.redaction_findings(public_summary(result)) + wsta88.redaction_findings(markdown(result))
    if findings:
        result["decision"] = "wsta226-blocked-redaction-finding"
        result["gate_decision"] = result["decision"]
        result["gate_detail"] = {"findings": sorted(set(findings))}
        result["ended_utc"] = utc_stamp()
        write_json(out_path, result)
        return result

    write_json(out_path, result)
    if result["decision"] in {PASS_DECISION, LIVE_PASS_DECISION}:
        write_text(run_dir / MARKDOWN_NAME, markdown(result))
    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--wsta223-result-json", type=Path, default=DEFAULT_WSTA223_RESULT)
    parser.add_argument("--route-artifact-json", type=Path)
    parser.add_argument("--prepare-attended-egress-gate", action="store_true")
    parser.add_argument("--execute-live-egress-allowlist", action="store_true")
    parser.add_argument("--ack-credentialed-wifi", action="store_true")
    parser.add_argument("--ack-public-exposure", action="store_true")
    parser.add_argument("--allow-operator-live", action="store_true")
    parser.add_argument("--allow-native-reboot", action="store_true")
    parser.add_argument("--allow-public-live", action="store_true")
    parser.add_argument("--ack-packet-filter-mutation", action="store_true")
    parser.add_argument("--force-packet-filter-restore-proof", action="store_true")
    parser.add_argument("--force-cloudflared-egress-allowlist-proof", action="store_true")
    parser.add_argument("--force-control-plane-proof", action="store_true")
    parser.add_argument("--force-public-off-proof", action="store_true")
    parser.add_argument("--force-ttl-expiry-proof", action="store_true")
    parser.add_argument("--force-manual-stop-proof", action="store_true")
    parser.add_argument("--ttl-sec", type=int, default=wsta88.wsta72.SHORT_SESSION_MAX_TTL_SEC)
    parser.add_argument("--ready-index", type=int, default=0)
    parser.add_argument("--min-initial-seconds-remaining", type=int, default=wsta88.wsta72.wsta71.wsta65.DEFAULT_MIN_INITIAL_SECONDS_REMAINING)
    parser.add_argument("--max-sessions", type=int, default=wsta88.wsta72.wsta67.DEFAULT_MAX_SESSIONS)
    parser.add_argument("--max-retire-markers", type=int, default=wsta88.wsta72.wsta67.DEFAULT_MAX_SESSIONS)
    parser.add_argument("--max-packets", type=int, default=wsta88.wsta75.DEFAULT_MAX_PACKETS)
    parser.add_argument("--max-briefs", type=int, default=wsta88.wsta77.DEFAULT_MAX_BRIEFS)
    parser.add_argument("--bridge-host", default="127.0.0.1")
    parser.add_argument("--bridge-port", type=int, default=54321)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--local-image", type=Path, default=wsta88.wsta80.wsta58.wsta55.wsta45.wsta43.wsta42.DEFAULT_LOCAL_IMAGE)
    parser.add_argument("--local-image-sha256", default=wsta88.wsta80.wsta58.wsta55.wsta45.wsta43.wsta42.DEFAULT_LOCAL_IMAGE_SHA256)
    parser.add_argument("--remote-image", default=wsta88.wsta80.wsta58.wsta55.wsta45.wsta43.wsta42.DEFAULT_REMOTE_IMAGE)
    parser.add_argument("--remote-clean-image", default=wsta88.wsta80.wsta58.wsta55.wsta45.wsta43.wsta42.DEFAULT_REMOTE_CLEAN_IMAGE)
    parser.add_argument("--native-confirm-token", default="")
    parser.add_argument("--public-confirm-token", default="")
    parser.add_argument("--print-full-json", action="store_true")
    return parser


def main_with_args(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        result = run(args)
    except Exception as exc:  # noqa: BLE001
        result = {"decision": "wsta226-runner-error", "error": str(exc)}
    payload = result if args.print_full_json else public_summary(result)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.get("decision") in {PASS_DECISION, LIVE_PASS_DECISION} else 2


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
