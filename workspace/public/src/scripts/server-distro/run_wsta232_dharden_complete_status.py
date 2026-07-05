#!/usr/bin/env python3
"""WSTA232 host-only D-HARDEN complete operator status.

The 2026-07-05 operator charter closes the A90 server-distro D-harden lane:
seccomp, non-root capability drop, native-uplink root boundary, legacy-iptables
loopback default-drop, cloudflared egress allowlist, and the AppArmor
unavailable/parked decision are already proven.  WSTA232 consumes the private
WSTA231/WSTA108 operator status and emits one D-HARDEN_COMPLETE status with
close-out-only next actions.

This unit is host-only.  It does not touch the device, flash, reboot, connect
Wi-Fi, run DHCP, open a public tunnel, run public smoke, mutate packet filters,
write userdata/rootfs state, load an LSM profile, switch root, or expose/log a
public URL value.
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


REPO_ROOT = wsta88.REPO_ROOT
PRIVATE_ROOT = wsta88.PRIVATE_ROOT
DEFAULT_RUN_BASE = wsta88.DEFAULT_RUN_BASE
DEFAULT_WSTA108_STATUS_JSON = (
    DEFAULT_RUN_BASE
    / "wsta231-server-endgame-status-prune-20260705T2348KST"
    / "wsta108_operator_server_status.json"
)

WSTA108_PASS_DECISION = "wsta108-operator-server-status-source-pass"
PASS_DECISION = "wsta232-dharden-complete-status-source-pass"
COMPLETE_STATE = "D_HARDEN_COMPLETE_DEFAULT_OFF"
RESULT_NAME = "wsta232_result.json"
STATUS_JSON_NAME = "wsta232_dharden_complete_status.json"
STATUS_MD_NAME = "wsta232_dharden_complete_status.md"

SOURCE_NEXT_ACTION = "continue-dpublic-server-endgame-after-cloudflared-egress-live"
CLOSEOUT_NEXT_ACTIONS = [
    "keep-public-exposure-default-off",
    "perform-attended-cold-boot-persistence-smoke-measurement",
    "write-server-distro-epic-close-report",
    "halt-after-server-distro-close-report",
]

REQUIRED_TRUE_CHECKS = (
    "wsta108_pass",
    "server_profile_ready_default_off",
    "public_state_off",
    "default_public_off",
    "blocking_before_enforcement_empty",
    "launcher_remaining_profiles_empty",
    "syscall_remaining_profiles_empty",
    "seccomp_real_services_live_proven",
    "seccomp_filter_loaded",
    "seccomp_enforced",
    "capability_drop_nonroot_services_live_proven",
    "capability_remaining_nonroot_services_empty",
    "native_uplink_boundary_policy_defined",
    "native_uplink_connectivity_stays_native_owned",
    "native_uplink_not_debian_launcher_or_seccomp_target",
    "legacy_iptables_default_drop_policy_defined",
    "attended_default_drop_live_proven",
    "packet_filter_ready",
    "cloudflared_model_defined",
    "cloudflared_runtime_live_proven",
    "cloudflared_egress_allowlist_policy_defined",
    "cloudflared_egress_allowlist_live_proven",
    "cloudflared_egress_manual_stop_public_off",
    "cloudflared_egress_route_values_redacted",
    "apparmor_unavailable_under_current_evidence",
    "apparmor_profile_load_disabled",
    "apparmor_immediate_lever_parked",
    "redaction_clean",
    "source_next_action_seen",
    "closeout_next_actions_only",
)


def rel(path: Path) -> str:
    return wsta88.rel(path)


def utc_stamp() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def resolve_path(path: Path | str) -> Path:
    path_obj = path if isinstance(path, Path) else Path(path)
    return path_obj if path_obj.is_absolute() else REPO_ROOT / path_obj


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


def get_list(payload: dict[str, Any], key: str) -> list[Any]:
    value = payload.get(key)
    return value if isinstance(value, list) else []


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
        "rootfs_mutation": False,
        "switch_root": False,
        "lsm_profile_load": False,
        "server_status_reexecuted": False,
        "wsta88_live_gate_executed": False,
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def template() -> dict[str, Any]:
    return {
        "scope": "WSTA232 host-only D-HARDEN complete operator status",
        "default_mode": "host-only-existing-private-wsta108-status",
        "input": "workspace/private/runs/server-distro/<wsta231-run>/wsta108_operator_server_status.json",
        "command": [
            "python3",
            rel(Path(__file__).resolve()),
            "--emit-dharden-complete-status",
            "--wsta108-server-status-json",
            "workspace/private/runs/server-distro/<wsta231-run>/wsta108_operator_server_status.json",
        ],
        "device_action": False,
        "public_tunnel": False,
        "packet_filter_mutation": False,
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def public_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": result.get("decision"),
        "run_dir": result.get("run_dir"),
        "dharden_complete_status": result.get("dharden_complete_status", {}),
        "checks": result.get("checks", {}),
        "safety": result.get("safety", {}),
    }


def redaction_clean(result_fragment: dict[str, Any], markdown_text: str = "") -> bool:
    findings = wsta88.redaction_findings(result_fragment)
    findings += wsta88.redaction_findings(markdown_text)
    return not bool(findings)


def source_view(status_path: Path, status: dict[str, Any]) -> dict[str, Any]:
    server_status = get_dict(status, "server_status")
    exposure = get_dict(server_status, "exposure")
    hardening = get_dict(server_status, "hardening")
    launcher = get_dict(hardening, "launcher_proof")
    syscall = get_dict(hardening, "syscall_trace_proof")
    cloudflared_egress = get_dict(hardening, "cloudflared_egress_allowlist_live")
    redaction = get_dict(server_status, "redaction")
    return {
        "source_status": rel(status_path),
        "source_decision": status.get("decision"),
        "server_state": server_status.get("state"),
        "public_state": exposure.get("public_state"),
        "default_public_off": exposure.get("default_public_off") is True,
        "blocking_before_enforcement": list(get_list(hardening, "blocking_before_enforcement")),
        "launcher_remaining_profiles": list(get_list(launcher, "remaining_profiles")),
        "syscall_remaining_profiles": list(get_list(syscall, "remaining_profiles")),
        "cloudflared_egress_state": cloudflared_egress.get("state"),
        "operator_next_actions": list(get_list(server_status, "operator_next_actions")),
        "public_url_value_logged": redaction.get("public_url_value_logged"),
        "secret_values_logged": redaction.get("secret_values_logged"),
    }


def closeout_actions_only(actions: list[str]) -> bool:
    forbidden_terms = (
        "seccomp",
        "capability",
        "native-uplink",
        "default-drop",
        "cloudflared-egress",
        "apparmor",
        "hardening-lever",
    )
    return actions == CLOSEOUT_NEXT_ACTIONS and not any(
        any(term in action for term in forbidden_terms) for action in actions
    )


def validate_complete(status_path: Path, status: dict[str, Any]) -> tuple[dict[str, bool], dict[str, Any]]:
    server_status = get_dict(status, "server_status")
    exposure = get_dict(server_status, "exposure")
    hardening = get_dict(server_status, "hardening")
    packet_filter = get_dict(server_status, "packet_filter")
    redaction = get_dict(server_status, "redaction")
    checks = get_dict(status, "checks")
    launcher = get_dict(hardening, "launcher_proof")
    syscall = get_dict(hardening, "syscall_trace_proof")
    seccomp = get_dict(hardening, "seccomp_enforcement_proof")
    capability = get_dict(hardening, "capability_drop_proof")
    native_uplink = get_dict(hardening, "native_uplink_boundary_policy")
    default_drop_policy = get_dict(hardening, "default_drop_hardening_policy")
    attended_default_drop = get_dict(hardening, "attended_default_drop_live")
    cloudflared_policy = get_dict(hardening, "cloudflared_egress_allowlist_policy")
    cloudflared_live = get_dict(hardening, "cloudflared_egress_allowlist_live")
    apparmor = get_dict(hardening, "apparmor_feasibility")
    view = source_view(status_path, status)

    complete_checks: dict[str, bool] = {
        "wsta108_pass": status.get("decision") == WSTA108_PASS_DECISION,
        "server_profile_ready_default_off": server_status.get("state") == "SERVER_PROFILE_READY_DEFAULT_OFF",
        "public_state_off": exposure.get("public_state") == "PUBLIC_OFF",
        "default_public_off": exposure.get("default_public_off") is True,
        "blocking_before_enforcement_empty": get_list(hardening, "blocking_before_enforcement") == [],
        "launcher_remaining_profiles_empty": get_list(launcher, "remaining_profiles") == [],
        "syscall_remaining_profiles_empty": get_list(syscall, "remaining_profiles") == [],
        "seccomp_real_services_live_proven": checks.get("seccomp_real_services_live_proven") is True
        and seccomp.get("seccomp_real_services_live_proven") is True,
        "seccomp_filter_loaded": seccomp.get("seccomp_filter_loaded") is True,
        "seccomp_enforced": seccomp.get("seccomp_enforced") is True,
        "capability_drop_nonroot_services_live_proven": (
            checks.get("capability_drop_nonroot_services_live_proven") is True
            and capability.get("nonroot_services_capability_drop_live_proven") is True
        ),
        "capability_remaining_nonroot_services_empty": get_list(capability, "remaining_nonroot_services") == [],
        "native_uplink_boundary_policy_defined": checks.get("native_uplink_boundary_policy_defined") is True
        and native_uplink.get("native_uplink_boundary_policy_defined") is True,
        "native_uplink_connectivity_stays_native_owned": native_uplink.get("connectivity_stays_native_owned") is True,
        "native_uplink_not_debian_launcher_or_seccomp_target": (
            native_uplink.get("not_debian_launcher_or_seccomp_target") is True
        ),
        "legacy_iptables_default_drop_policy_defined": (
            checks.get("default_drop_hardening_policy_defined") is True
            and default_drop_policy.get("default_drop_hardening_policy_defined") is True
        ),
        "attended_default_drop_live_proven": checks.get("attended_default_drop_live_proven") is True
        and attended_default_drop.get("attended_default_drop_live_proven") is True,
        "packet_filter_ready": packet_filter.get("ready") is True or checks.get("packet_filter_ready") is True,
        "cloudflared_model_defined": checks.get("cloudflared_model_defined") is True,
        "cloudflared_runtime_live_proven": checks.get("cloudflared_runtime_live_proven") is True,
        "cloudflared_egress_allowlist_policy_defined": (
            checks.get("cloudflared_egress_allowlist_policy_defined") is True
            and cloudflared_policy.get("cloudflared_egress_allowlist_policy_defined") is True
        ),
        "cloudflared_egress_allowlist_live_proven": (
            checks.get("cloudflared_egress_allowlist_live_proven") is True
            and cloudflared_live.get("cloudflared_egress_allowlist_live_proven") is True
        ),
        "cloudflared_egress_manual_stop_public_off": (
            cloudflared_live.get("public_state_after_manual_stop") == "PUBLIC_OFF"
            and cloudflared_live.get("manual_stop_cleanup_ok") is True
        ),
        "cloudflared_egress_route_values_redacted": checks.get(
            "cloudflared_egress_allowlist_live_route_values_redacted"
        )
        is True,
        "apparmor_unavailable_under_current_evidence": (
            checks.get("apparmor_unavailable_under_current_evidence") is True
            and apparmor.get("apparmor_unavailable_under_current_evidence") is True
        ),
        "apparmor_profile_load_disabled": checks.get("apparmor_profile_load_disabled") is True
        and apparmor.get("profile_load_allowed") is False,
        "apparmor_immediate_lever_parked": checks.get("apparmor_immediate_lever_parked") is True
        and apparmor.get("preferred_current_hardening_lever") == "legacy-iptables-loopback-default-drop",
        "redaction_clean": (
            checks.get("public_url_value_logged") is False
            and checks.get("secret_values_logged") in (0, "0", None)
            and redaction.get("public_url_value_logged") is False
            and redaction.get("secret_values_logged") in (0, "0", None)
        ),
        "source_next_action_seen": SOURCE_NEXT_ACTION in get_list(server_status, "operator_next_actions"),
        "closeout_next_actions_only": closeout_actions_only(CLOSEOUT_NEXT_ACTIONS),
    }
    return complete_checks, view


def complete_status_payload(status_path: Path, status: dict[str, Any], checks: dict[str, bool], view: dict[str, Any]) -> dict[str, Any]:
    complete = all(checks.get(key) is True for key in REQUIRED_TRUE_CHECKS)
    return {
        "state": COMPLETE_STATE if complete else "D_HARDEN_COMPLETE_BLOCKED",
        "complete": complete,
        "source_status": rel(status_path),
        "source_decision": status.get("decision"),
        "server_state": view.get("server_state"),
        "public_state": view.get("public_state"),
        "public_exposure_default_off": view.get("default_public_off"),
        "landed_levers": {
            "seccomp_real_services": checks.get("seccomp_real_services_live_proven"),
            "capability_drop_nonroot_services": checks.get("capability_drop_nonroot_services_live_proven"),
            "native_uplink_root_boundary": checks.get("native_uplink_boundary_policy_defined"),
            "legacy_iptables_loopback_default_drop": checks.get("attended_default_drop_live_proven"),
            "cloudflared_egress_allowlist": checks.get("cloudflared_egress_allowlist_live_proven"),
            "apparmor_parked_unavailable": checks.get("apparmor_unavailable_under_current_evidence"),
        },
        "remaining_blockers": {
            "blocking_before_enforcement": view.get("blocking_before_enforcement", []),
            "launcher_remaining_profiles": view.get("launcher_remaining_profiles", []),
            "syscall_remaining_profiles": view.get("syscall_remaining_profiles", []),
        },
        "retired_source_next_actions": [SOURCE_NEXT_ACTION],
        "operator_next_actions": CLOSEOUT_NEXT_ACTIONS,
        "recommended_next_unit": (
            "attended-cold-boot-persistence-smoke-measurement"
            if complete
            else "repair-wsta108-dharden-complete-input"
        ),
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def markdown(result: dict[str, Any]) -> str:
    status = get_dict(result, "dharden_complete_status")
    blockers = get_dict(status, "remaining_blockers")
    levers = get_dict(status, "landed_levers")
    return "\n".join([
        "# WSTA232 D-HARDEN Complete Status",
        "",
        f"- Decision: `{result.get('decision')}`",
        f"- State: `{status.get('state')}`",
        f"- Complete: `{status.get('complete')}`",
        f"- Source status: `{status.get('source_status')}`",
        f"- Server state: `{status.get('server_state')}`",
        f"- Public state: `{status.get('public_state')}`",
        f"- Public exposure default-off: `{status.get('public_exposure_default_off')}`",
        f"- Seccomp real services: `{levers.get('seccomp_real_services')}`",
        f"- Capability drop non-root services: `{levers.get('capability_drop_nonroot_services')}`",
        f"- Native uplink root boundary: `{levers.get('native_uplink_root_boundary')}`",
        f"- Legacy iptables default-drop: `{levers.get('legacy_iptables_loopback_default_drop')}`",
        f"- Cloudflared egress allowlist: `{levers.get('cloudflared_egress_allowlist')}`",
        f"- AppArmor parked unavailable: `{levers.get('apparmor_parked_unavailable')}`",
        f"- Blocking-before-enforcement count: `{len(get_list(blockers, 'blocking_before_enforcement'))}`",
        f"- Launcher remaining profile count: `{len(get_list(blockers, 'launcher_remaining_profiles'))}`",
        f"- Syscall remaining profile count: `{len(get_list(blockers, 'syscall_remaining_profiles'))}`",
        f"- Recommended next unit: `{status.get('recommended_next_unit')}`",
        "- Public URL logged: `false`",
        "- Secret values logged: `0`",
        "",
    ])


def fail_result(result: dict[str, Any], out_path: Path, decision: str) -> dict[str, Any]:
    result["decision"] = decision
    result["gate_decision"] = decision
    result["ended_utc"] = utc_stamp()
    write_json(out_path, result)
    return result


def require_private_file(path_arg: Path | None, label: str) -> tuple[Path | None, str | None]:
    if path_arg is None:
        return None, f"wsta232-blocked-{label}-required"
    path = resolve_path(path_arg)
    if not is_under(path, PRIVATE_ROOT):
        return None, f"wsta232-blocked-{label}-nonprivate"
    if not path.is_file():
        return None, f"wsta232-blocked-{label}-missing"
    return path, None


def run(args: argparse.Namespace) -> dict[str, Any]:
    ts = utc_stamp()
    run_id = args.run_id or f"wsta232-dharden-complete-status-{ts}"
    run_dir = resolve_path(args.run_dir or (DEFAULT_RUN_BASE / run_id))
    result: dict[str, Any] = {
        "scope": "WSTA232 host-only D-HARDEN complete operator status",
        "started_utc": ts,
        "run_dir": rel(run_dir),
        "decision": "wsta232-blocked",
        "gate_decision": "not-run",
        "safety": safety_flags(),
        "checks": {},
    }
    if not is_under(run_dir, PRIVATE_ROOT):
        result["decision"] = "wsta232-blocked-nonprivate-run-dir"
        result["gate_decision"] = result["decision"]
        result["ended_utc"] = utc_stamp()
        return result
    run_dir.mkdir(parents=True, exist_ok=True)
    out_path = run_dir / RESULT_NAME

    if args.print_template:
        result["decision"] = "wsta232-template"
        result["template"] = template()
        result["ended_utc"] = utc_stamp()
        return result

    if not args.emit_dharden_complete_status:
        return fail_result(result, out_path, "wsta232-blocked-explicit-emit-dharden-complete-status-required")

    status_path, path_error = require_private_file(args.wsta108_server_status_json, "wsta108-server-status")
    if path_error or status_path is None:
        return fail_result(result, out_path, path_error or "wsta232-blocked-wsta108-server-status")

    try:
        status = load_json(status_path)
    except Exception as exc:  # noqa: BLE001
        result["gate_detail"] = {"error": str(exc)}
        return fail_result(result, out_path, "wsta232-blocked-wsta108-server-status-unreadable")

    checks, view = validate_complete(status_path, status)
    result["checks"] = checks
    result["source_status_public_view"] = view
    complete_status = complete_status_payload(status_path, status, checks, view)
    result["dharden_complete_status"] = complete_status

    if not all(checks.get(key) is True for key in REQUIRED_TRUE_CHECKS):
        result["gate_detail"] = {
            "failed_required_checks": [key for key in REQUIRED_TRUE_CHECKS if checks.get(key) is not True],
        }
        return fail_result(result, out_path, "wsta232-blocked-dharden-complete-incomplete")

    result["decision"] = PASS_DECISION
    result["gate_decision"] = "ok"
    result["ended_utc"] = utc_stamp()
    md = markdown(result)
    if not redaction_clean(public_summary(result), md):
        return fail_result(result, out_path, "wsta232-blocked-redaction-finding")

    write_json(run_dir / STATUS_JSON_NAME, complete_status)
    write_text(run_dir / STATUS_MD_NAME, md)
    write_json(out_path, result)
    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--emit-dharden-complete-status", action="store_true")
    parser.add_argument("--wsta108-server-status-json", type=Path, default=DEFAULT_WSTA108_STATUS_JSON)
    parser.add_argument("--print-template", action="store_true")
    parser.add_argument("--print-full-json", action="store_true")
    return parser


def main_with_args(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        result = run(args)
    except Exception as exc:  # noqa: BLE001
        result = {"decision": "wsta232-runner-error", "error": str(exc)}
    payload = result if args.print_full_json else public_summary(result)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.get("decision") == PASS_DECISION else 1


if __name__ == "__main__":
    raise SystemExit(main_with_args())
