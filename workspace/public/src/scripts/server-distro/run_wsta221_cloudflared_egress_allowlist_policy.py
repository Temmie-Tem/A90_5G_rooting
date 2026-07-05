#!/usr/bin/env python3
"""WSTA221 host-only cloudflared egress allowlist hardening policy.

WSTA220 made the attended legacy-iptables default-drop path visible in operator
status.  This unit selects the next hardening layer without mutating packet
filters: a future cloudflared-specific egress allowlist live gate.  It consumes
the WSTA220 operator status plus WSTA122 cloudflared model and WSTA125
cloudflared runtime proof, then emits a fail-closed policy contract for the next
runner.

This unit is host-only.  It does not touch the device, flash, reboot, connect
Wi-Fi, run DHCP, open a public tunnel, mutate packet filters, write userdata,
switch root, mount a rootfs, or load an LSM profile.
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
import run_wsta122_cloudflared_service_model as wsta122  # noqa: E402
import run_wsta125_native_upstream_cloudflared_runtime as wsta125  # noqa: E402


REPO_ROOT = wsta88.REPO_ROOT
PRIVATE_ROOT = wsta88.PRIVATE_ROOT
DEFAULT_RUN_BASE = wsta88.DEFAULT_RUN_BASE
DEFAULT_WSTA220_OPERATOR_STATUS = (
    DEFAULT_RUN_BASE
    / "wsta220-operator-status-attended-default-drop-live-fullest-20260705T220310KST"
    / "wsta108_operator_server_status.json"
)
DEFAULT_WSTA122_CLOUDFLARED_MODEL = (
    DEFAULT_RUN_BASE
    / "wsta122-cloudflared-service-model-20260705T045720KST"
    / "wsta122_cloudflared_service_model.json"
)
DEFAULT_WSTA125_CLOUDFLARED_RUNTIME = (
    DEFAULT_RUN_BASE
    / "wsta125-native-upstream-cloudflared-runtime-live-v4-20260705T062106KST"
    / "wsta125_result.json"
)

PASS_DECISION = "wsta221-cloudflared-egress-allowlist-policy-source-pass"
POLICY_SCHEMA = "a90-wsta221-cloudflared-egress-allowlist-policy-v1"
POLICY_STATE = "CLOUDFLARED_EGRESS_ALLOWLIST_HARDENING_POLICY_DEFINED"
WSTA108_PASS_DECISION = "wsta108-operator-server-status-source-pass"
WSTA216_POLICY_STATE = "LEGACY_IPTABLES_DEFAULT_DROP_HARDENING_POLICY_DEFINED"
WSTA219_LIVE_STATE = "LEGACY_IPTABLES_DEFAULT_DROP_ATTENDED_LIVE_PROVEN"
POLICY_NAME = "wsta221_cloudflared_egress_allowlist_policy.json"
SUMMARY_NAME = "wsta221_result.json"
MARKDOWN_NAME = "wsta221_cloudflared_egress_allowlist_policy.md"
SERVICE = "cloudflared-quick-tunnel"
SERVICE_USER = "a90tunnel"
SERVICE_UID = 3902
SERVICE_GID = 3902
HARDENING_LEVER = "legacy-iptables-cloudflared-egress-allowlist"
REQUIRED_NEXT_ACTIONS = (
    "continue-next-hardening-layer-after-attended-default-drop-live",
    "move-to-next-hardening-layer-after-attended-default-drop-live",
)
REQUIRED_RUNTIME_CHECKS = (
    "egress_route_ready",
    "cloudflared_uid_gid_pass",
    "cloudflared_no_new_privs_pass",
    "cloudflared_cap_eff_zero_pass",
    "cloudflared_command_shape_pass",
    "cloudflared_outbound_only_pass",
    "private_url_artifact_saved",
    "trace_file_nonempty",
    "syscall_profile_nonempty",
    "syscall_core_observed",
    "trace_artifact_saved",
    "runtime_cleanup_ok",
    "packet_filter_restore_pass",
    "final_selftest_fail_zero",
)


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


def safety_flags() -> dict[str, Any]:
    return {
        "device_action": False,
        "boot_flash": False,
        "native_reboot": False,
        "wifi_connect": False,
        "wifi_association": False,
        "dhcp": False,
        "ping": False,
        "public_tunnel": False,
        "public_smoke": False,
        "packet_filter_mutation": False,
        "userdata_touch": False,
        "switch_root": False,
        "rootfs_mutation": False,
        "lsm_profile_load": False,
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def public_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": result.get("decision"),
        "run_dir": result.get("run_dir"),
        "gate_decision": result.get("gate_decision"),
        "policy": result.get("policy", {}),
        "checks": result.get("checks", {}),
        "safety": result.get("safety", {}),
    }


def validate_operator_status(status: dict[str, Any]) -> dict[str, bool]:
    server_status = get_dict(status, "server_status")
    exposure = get_dict(server_status, "exposure")
    hardening = get_dict(server_status, "hardening")
    attended = get_dict(hardening, "attended_default_drop_live")
    default_drop = get_dict(hardening, "default_drop_hardening_policy")
    cloud_model = get_dict(hardening, "cloudflared_model")
    cloud_runtime = get_dict(hardening, "cloudflared_runtime")
    apparmor = get_dict(hardening, "apparmor_feasibility")
    checks = get_dict(status, "checks")
    next_actions = set(str(item) for item in server_status.get("operator_next_actions") or [])
    return {
        "decision_pass": status.get("decision") == WSTA108_PASS_DECISION,
        "public_state_off": exposure.get("public_state") == "PUBLIC_OFF",
        "default_public_off": exposure.get("default_public_off") is True,
        "attended_default_drop_live_proven": (
            attended.get("state") == WSTA219_LIVE_STATE
            and attended.get("attended_default_drop_live_proven") is True
        ),
        "default_drop_policy_defined": (
            default_drop.get("state") == WSTA216_POLICY_STATE
            and default_drop.get("default_drop_hardening_policy_defined") is True
        ),
        "cloudflared_model_defined": cloud_model.get("model_defined") is True,
        "cloudflared_runtime_live_proven": cloud_runtime.get("cloudflared_live_proven") is True,
        "cloudflared_runtime_private_url_redacted": (
            cloud_runtime.get("private_url_redacted") is True
        ),
        "apparmor_parked": (
            apparmor.get("apparmor_unavailable_under_current_evidence") is True
            and apparmor.get("profile_load_allowed") is False
        ),
        "required_next_actions_present": set(REQUIRED_NEXT_ACTIONS).issubset(next_actions),
        "status_checks_agree": (
            checks.get("attended_default_drop_live_proven") is True
            and checks.get("cloudflared_runtime_live_proven") is True
            and checks.get("cloudflared_model_defined") is True
            and checks.get("apparmor_immediate_lever_parked") is True
        ),
        "redaction_clean": not bool(wsta88.redaction_findings(status)),
    }


def validate_cloudflared_model(model_result: dict[str, Any]) -> dict[str, bool]:
    model = get_dict(model_result, "cloudflared_service_model")
    identity = get_dict(model, "target_identity")
    exposure = get_dict(model, "default_exposure")
    network = get_dict(model, "network")
    launcher = get_dict(model, "launcher_policy")
    credentials = get_dict(model, "credentials")
    runtime = get_dict(model, "runtime_files")
    recomputed = wsta122.validate_model(model)
    return {
        "decision_pass": model_result.get("decision") == wsta122.PASS_DECISION,
        "recomputed_model_checks_all_true": bool(recomputed)
        and all(value is True for value in recomputed.values()),
        "service_matches": model.get("service") == SERVICE,
        "identity_a90tunnel": (
            identity.get("user") == SERVICE_USER
            and identity.get("uid") == SERVICE_UID
            and identity.get("gid") == SERVICE_GID
        ),
        "daemon_nonroot_outbound": model.get("daemon_privilege_model") == "non-root-outbound-client",
        "default_public_off": (
            exposure.get("public_default") == "off"
            and exposure.get("start_requires_operator_live_gate") is True
            and exposure.get("boot_autostart_without_enable_file") is False
        ),
        "launcher_no_new_privs_caps_zero": (
            launcher.get("target_user") == SERVICE_USER
            and launcher.get("no_new_privs") is True
            and launcher.get("effective_capabilities") == "zero"
        ),
        "outbound_only_model": (
            network.get("outbound_tunnel_client") is True
            and network.get("public_inbound_listener") is False
            and network.get("origin_scope") == "loopback-only"
            and network.get("metrics_scope") == "loopback-ephemeral"
        ),
        "packet_filter_precondition_default_drop": (
            network.get("packet_filter_precondition")
            == "loopback-default-drop-before-public-start"
        ),
        "quick_tunnel_has_no_named_secret": (
            credentials.get("quick_tunnel_accountless") is True
            and credentials.get("named_tunnel_credentials_required") is False
            and credentials.get("token_in_command") is False
        ),
        "runtime_url_private": (
            runtime.get("url_file_mode") == "0600"
            and runtime.get("public_url_committable") is False
        ),
        "redaction_clean": (
            model.get("public_url_value_logged") is False
            and model.get("secret_values_logged") == 0
            and credentials.get("secret_values_logged") == 0
        ),
    }


def validate_runtime(runtime_result: dict[str, Any]) -> dict[str, bool]:
    checks = get_dict(runtime_result, "checks")
    probe = get_dict(runtime_result, "runtime_probe")
    parsed = get_dict(probe, "parsed")
    egress = get_dict(runtime_result, "egress_route_preflight")
    private_url = get_dict(runtime_result, "private_url_artifact")
    return {
        "decision_pass": runtime_result.get("decision") == wsta125.PASS_DECISION,
        "required_runtime_checks_all_true": all(checks.get(key) is True for key in REQUIRED_RUNTIME_CHECKS),
        "runtime_probe_passed": probe.get("returncode") == 0 and parsed.get("runtime_done") is True,
        "uid_gid_3902": parsed.get("uid_3902") is True and parsed.get("gid_3902") is True,
        "no_new_privs_and_caps_zero": (
            parsed.get("no_new_privs") is True and parsed.get("cap_eff_zero") is True
        ),
        "command_shape": (
            parsed.get("command_has_tunnel") is True
            and parsed.get("command_no_autoupdate") is True
            and parsed.get("command_origin") is True
            and parsed.get("command_metrics") is True
        ),
        "outbound_only_observed": (
            parsed.get("outbound_only") is True
            and parsed.get("outbound_observed") is True
            and parsed.get("established_outbound") is True
        ),
        "no_nonloopback_listener": parsed.get("cloudflared_listen_nonloopback") in (False, None),
        "egress_route_ready": (
            egress.get("ready") is True
            and egress.get("route_ok") is True
            and egress.get("target_redacted") is True
        ),
        "syscall_profile_has_connect": (
            parsed.get("syscall_profile_nonempty") is True
            and "connect" in (parsed.get("syscall_names") or [])
            and "socket" in (parsed.get("syscall_names") or [])
        ),
        "private_url_redacted": (
            private_url.get("url_artifact_saved") is True
            and private_url.get("stdout_redacted") is True
            and private_url.get("public_url_value_logged") is False
        ),
        "cleanup_and_restore_ok": (
            checks.get("runtime_cleanup_ok") is True
            and checks.get("packet_filter_restore_pass") is True
            and checks.get("final_selftest_fail_zero") is True
        ),
        "redaction_clean": (
            checks.get("public_url_value_logged") is False
            and checks.get("secret_values_logged") == 0
            and private_url.get("public_url_value_logged") is False
            and private_url.get("secret_values_logged") == 0
            and get_dict(runtime_result, "safety").get("public_url_value_logged") is False
            and get_dict(runtime_result, "safety").get("secret_values_logged") == 0
        ),
    }


def build_policy(
    operator_status: dict[str, Any],
    model_result: dict[str, Any],
    runtime_result: dict[str, Any],
) -> dict[str, Any]:
    model = get_dict(model_result, "cloudflared_service_model")
    network = get_dict(model, "network")
    parsed = get_dict(get_dict(runtime_result, "runtime_probe"), "parsed")
    return {
        "schema": POLICY_SCHEMA,
        "state": POLICY_STATE,
        "hardening_lever": HARDENING_LEVER,
        "service": SERVICE,
        "backend": "legacy-iptables",
        "policy": "cloudflared-egress-allowlist",
        "activation": "explicit-operator-gated-after-default-drop",
        "default_public_off": True,
        "live_execution_requested": False,
        "packet_filter_mutation_by_wsta221": False,
        "source_status": {
            "operator_status_run_dir": operator_status.get("run_dir"),
            "cloudflared_model_run_dir": model_result.get("run_dir"),
            "cloudflared_runtime_run_dir": runtime_result.get("run_dir"),
        },
        "target_identity": {
            "user": SERVICE_USER,
            "uid": SERVICE_UID,
            "gid": SERVICE_GID,
        },
        "network_model": {
            "origin_scope": network.get("origin_scope"),
            "metrics_scope": network.get("metrics_scope"),
            "public_inbound_listener": False,
            "outbound_tunnel_client": True,
            "runtime_outbound_observed": bool(parsed.get("outbound_observed")),
            "runtime_established_outbound_observed": bool(parsed.get("established_outbound")),
        },
        "policy_contract": {
            "preserve_existing_input_default_drop": True,
            "apply_after_loopback_default_drop": True,
            "save_existing_rules_before_mutation": True,
            "restore_exact_rules_before_public_off_success": True,
            "control_plane_must_survive_apply": True,
            "fail_closed_if_owner_match_unavailable": True,
            "fail_closed_if_dns_or_tls_route_unresolved": True,
            "forbid_public_url_logging": True,
            "forbid_secret_logging": True,
        },
        "candidate_rule_shape": {
            "chain": "OUTPUT",
            "owner_match": {"uid_owner": SERVICE_UID, "user": SERVICE_USER},
            "allow_loopback": True,
            "allow_established_related": True,
            "allow_dns": "route-resolved-live-preflight-required",
            "allow_tls": "route-resolved-live-preflight-required",
            "default_for_service": "REJECT-or-DROP-after-live-preflight",
            "global_output_default": "unchanged-until-live-proof",
        },
        "next_live_gate_requirements": [
            "preflight iptables owner match and rule restore support",
            "derive redacted DNS/TLS egress route in live session",
            "apply egress allowlist only after loopback default-drop is active",
            "prove cloudflared public smoke still works",
            "prove non-cloudflared service traffic is not accidentally opened",
            "prove USB/NCM control plane survives apply",
            "restore exact rules before PUBLIC_OFF success",
        ],
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def validate_policy(policy: dict[str, Any]) -> dict[str, bool]:
    contract = get_dict(policy, "policy_contract")
    target = get_dict(policy, "target_identity")
    shape = get_dict(policy, "candidate_rule_shape")
    owner = get_dict(shape, "owner_match")
    return {
        "schema_ok": policy.get("schema") == POLICY_SCHEMA,
        "state_ok": policy.get("state") == POLICY_STATE,
        "hardening_lever_ok": policy.get("hardening_lever") == HARDENING_LEVER,
        "service_ok": policy.get("service") == SERVICE,
        "backend_ok": policy.get("backend") == "legacy-iptables",
        "policy_ok": policy.get("policy") == "cloudflared-egress-allowlist",
        "activation_explicit": policy.get("activation") == "explicit-operator-gated-after-default-drop",
        "default_public_off": policy.get("default_public_off") is True,
        "no_live_execution": policy.get("live_execution_requested") is False,
        "no_mutation_here": policy.get("packet_filter_mutation_by_wsta221") is False,
        "target_identity_ok": (
            target.get("user") == SERVICE_USER
            and target.get("uid") == SERVICE_UID
            and target.get("gid") == SERVICE_GID
        ),
        "owner_match_fail_closed": (
            owner.get("uid_owner") == SERVICE_UID
            and contract.get("fail_closed_if_owner_match_unavailable") is True
        ),
        "preserves_default_drop": (
            contract.get("preserve_existing_input_default_drop") is True
            and contract.get("apply_after_loopback_default_drop") is True
        ),
        "restore_exact_required": contract.get("restore_exact_rules_before_public_off_success") is True,
        "control_plane_required": contract.get("control_plane_must_survive_apply") is True,
        "redaction_required": (
            contract.get("forbid_public_url_logging") is True
            and contract.get("forbid_secret_logging") is True
            and policy.get("public_url_value_logged") is False
            and policy.get("secret_values_logged") == 0
        ),
    }


def markdown(result: dict[str, Any]) -> str:
    policy = get_dict(result, "policy")
    checks = get_dict(result, "checks")
    return "\n".join([
        "# WSTA221 Cloudflared Egress Allowlist Policy",
        "",
        f"- Decision: `{result.get('decision')}`",
        f"- State: `{policy.get('state')}`",
        f"- Hardening lever: `{policy.get('hardening_lever')}`",
        f"- Service: `{policy.get('service')}`",
        f"- Backend: `{policy.get('backend')}`",
        f"- Live execution requested: `{str(bool(policy.get('live_execution_requested'))).lower()}`",
        f"- Packet-filter mutation here: `{str(bool(policy.get('packet_filter_mutation_by_wsta221'))).lower()}`",
        f"- Operator status ready: `{str(bool(checks.get('operator_status_ready'))).lower()}`",
        f"- Cloudflared model ready: `{str(bool(checks.get('cloudflared_model_ready'))).lower()}`",
        f"- Cloudflared runtime ready: `{str(bool(checks.get('cloudflared_runtime_ready'))).lower()}`",
        "",
        "## Next Live Gate Requirements",
        "",
        *[f"- `{item}`" for item in policy.get("next_live_gate_requirements", [])],
        "",
    ]) + "\n"


def fail_result(result: dict[str, Any], out_path: Path, decision: str) -> dict[str, Any]:
    result["decision"] = decision
    result["gate_decision"] = decision
    result["ended_utc"] = utc_stamp()
    write_json(out_path, result)
    return result


def require_private_file(path_arg: Path, label: str) -> tuple[Path | None, str | None]:
    path = resolve_path(path_arg)
    if not is_under(path, PRIVATE_ROOT):
        return None, f"wsta221-blocked-{label}-nonprivate"
    if not path.is_file():
        return None, f"wsta221-blocked-{label}-missing"
    return path, None


def run(args: argparse.Namespace) -> dict[str, Any]:
    ts = utc_stamp()
    run_id = args.run_id or f"wsta221-cloudflared-egress-allowlist-policy-{ts}"
    run_dir = args.run_dir or (DEFAULT_RUN_BASE / run_id)
    if not run_dir.is_absolute():
        run_dir = REPO_ROOT / run_dir
    run_dir.mkdir(parents=True, exist_ok=True)
    out_path = run_dir / SUMMARY_NAME
    result: dict[str, Any] = {
        "scope": "WSTA221 host-only cloudflared egress allowlist hardening policy",
        "started_utc": ts,
        "run_dir": rel(run_dir),
        "gate_decision": "source-gate" if args.emit_egress_allowlist_policy else "blocked",
        "safety": safety_flags(),
        "checks": {},
    }

    if not args.emit_egress_allowlist_policy:
        return fail_result(result, out_path, "wsta221-blocked-explicit-gate-required")
    if not is_under(run_dir, PRIVATE_ROOT):
        return fail_result(result, out_path, "wsta221-blocked-nonprivate-run-dir")

    status_path, status_error = require_private_file(args.wsta220_operator_status_json, "wsta220-operator-status")
    model_path, model_error = require_private_file(args.wsta122_cloudflared_model_json, "wsta122-cloudflared-model")
    runtime_path, runtime_error = require_private_file(args.wsta125_cloudflared_runtime_json, "wsta125-cloudflared-runtime")
    for error in (status_error, model_error, runtime_error):
        if error:
            return fail_result(result, out_path, error)
    assert status_path is not None
    assert model_path is not None
    assert runtime_path is not None

    operator_status = load_json(status_path)
    model_result = load_json(model_path)
    runtime_result = load_json(runtime_path)
    operator_checks = validate_operator_status(operator_status)
    model_checks = validate_cloudflared_model(model_result)
    runtime_checks = validate_runtime(runtime_result)
    policy = build_policy(operator_status, model_result, runtime_result)
    policy_checks = validate_policy(policy)
    result["policy"] = policy
    result["checks"] = {
        **{f"operator_{key}": value for key, value in operator_checks.items()},
        **{f"model_{key}": value for key, value in model_checks.items()},
        **{f"runtime_{key}": value for key, value in runtime_checks.items()},
        **{f"policy_{key}": value for key, value in policy_checks.items()},
        "operator_status_ready": all(operator_checks.values()),
        "cloudflared_model_ready": all(model_checks.values()),
        "cloudflared_runtime_ready": all(runtime_checks.values()),
        "policy_ready": all(policy_checks.values()),
    }
    if not result["checks"]["operator_status_ready"]:
        return fail_result(result, out_path, "wsta221-blocked-operator-status-incomplete")
    if not result["checks"]["cloudflared_model_ready"]:
        return fail_result(result, out_path, "wsta221-blocked-cloudflared-model-incomplete")
    if not result["checks"]["cloudflared_runtime_ready"]:
        return fail_result(result, out_path, "wsta221-blocked-cloudflared-runtime-incomplete")
    if not result["checks"]["policy_ready"]:
        return fail_result(result, out_path, "wsta221-blocked-policy-incomplete")

    findings = wsta88.redaction_findings(public_summary(result)) + wsta88.redaction_findings(markdown(result))
    if findings:
        result["gate_detail"] = {"findings": sorted(set(findings))}
        return fail_result(result, out_path, "wsta221-blocked-redaction-finding")

    result["decision"] = PASS_DECISION
    result["gate_decision"] = "ok"
    result["ended_utc"] = utc_stamp()
    write_json(run_dir / POLICY_NAME, policy)
    write_json(out_path, result)
    write_text(run_dir / MARKDOWN_NAME, markdown(result))
    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--emit-egress-allowlist-policy", action="store_true")
    parser.add_argument("--wsta220-operator-status-json", type=Path, default=DEFAULT_WSTA220_OPERATOR_STATUS)
    parser.add_argument("--wsta122-cloudflared-model-json", type=Path, default=DEFAULT_WSTA122_CLOUDFLARED_MODEL)
    parser.add_argument("--wsta125-cloudflared-runtime-json", type=Path, default=DEFAULT_WSTA125_CLOUDFLARED_RUNTIME)
    parser.add_argument("--print-full-json", action="store_true")
    return parser


def main_with_args(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    result = run(args)
    if args.print_full_json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(json.dumps(public_summary(result), indent=2, sort_keys=True))
    return 0 if result.get("decision") == PASS_DECISION else 2


if __name__ == "__main__":
    raise SystemExit(main_with_args())
