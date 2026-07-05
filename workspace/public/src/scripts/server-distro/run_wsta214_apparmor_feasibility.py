#!/usr/bin/env python3
"""WSTA214 host-only AppArmor feasibility audit.

Consumes existing D0/Debian-eye public summaries plus public rootfs staging
source files and decides whether AppArmor is a viable immediate D-harden lever.

This unit is host-only.  It does not touch the device, flash, reboot, connect
Wi-Fi, run DHCP, open a public tunnel, mutate packet filters, write userdata,
switch root, mount a rootfs, install packages, or load any LSM profile.
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

import run_wsta89_hardening_readiness_audit as wsta89  # noqa: E402


REPO_ROOT = wsta89.REPO_ROOT
PRIVATE_ROOT = wsta89.PRIVATE_ROOT
DEFAULT_RUN_BASE = wsta89.DEFAULT_RUN_BASE
DEFAULT_D0_SUMMARY = wsta89.DEFAULT_D0_SUMMARY
DEFAULT_DEBIAN_EYE_SUMMARY = wsta89.DEFAULT_DEBIAN_EYE_SUMMARY
DEFAULT_SOURCE_PATHS = (
    SCRIPT_DIR / "build_debian_aarch64_rootfs.py",
    SCRIPT_DIR / "prepare_wsta3_sta_rootfs.py",
)
PASS_DECISION = "wsta214-apparmor-feasibility-source-pass"
AUDIT_SCHEMA = "a90-wsta214-apparmor-feasibility-v1"
AUDIT_STATE_UNAVAILABLE = "APPARMOR_NOT_AVAILABLE_UNDER_CURRENT_EVIDENCE"
AUDIT_STATE_READY = "APPARMOR_PROFILE_SOURCE_FEASIBLE"
RESULT_NAME = "wsta214_apparmor_feasibility.json"
SUMMARY_NAME = "wsta214_result.json"
MARKDOWN_NAME = "wsta214_apparmor_feasibility.md"


def rel(path: Path) -> str:
    return wsta89.rel(path)


def utc_stamp() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def is_under(path: Path, root: Path) -> bool:
    return wsta89.is_under(path, root)


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
        "rootfs_mount": False,
        "package_install": False,
        "lsm_profile_load": False,
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def public_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": result.get("decision"),
        "run_dir": result.get("run_dir"),
        "gate_decision": result.get("gate_decision"),
        "apparmor": result.get("apparmor", {}),
        "checks": result.get("checks", {}),
        "safety": result.get("safety", {}),
    }


def config_value(d0: dict[str, Any], key: str) -> str:
    return str((d0.get("kernel_config") or {}).get(key, "missing"))


def source_mentions(source_paths: list[Path], patterns: tuple[str, ...]) -> dict[str, bool]:
    joined = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in source_paths)
    lowered = joined.lower()
    return {pattern: pattern.lower() in lowered for pattern in patterns}


def userspace_absent_from_debian_eye(debian_eye: dict[str, Any] | None) -> dict[str, bool | None]:
    absent = (
        debian_eye.get("vendor_userspace_absent", {})
        if isinstance(debian_eye, dict) and isinstance(debian_eye.get("vendor_userspace_absent"), dict)
        else {}
    )
    return {
        "apparmor": absent.get("apparmor"),
        "apparmor_parser": absent.get("apparmor_parser"),
        "aa-status": absent.get("aa-status"),
    }


def build_apparmor_audit(d0_path: Path,
                         d0: dict[str, Any],
                         debian_eye_path: Path,
                         debian_eye: dict[str, Any],
                         source_paths: list[Path]) -> dict[str, Any]:
    apparmor_cfg = config_value(d0, "CONFIG_SECURITY_APPARMOR")
    securityfs_cfg = config_value(d0, "CONFIG_SECURITYFS")
    default_security = config_value(d0, "CONFIG_DEFAULT_SECURITY")
    lsm = d0.get("lsm") if isinstance(d0.get("lsm"), dict) else {}
    proc_security = d0.get("proc_security") if isinstance(d0.get("proc_security"), dict) else {}
    mentions = source_mentions(source_paths, ("apparmor", "apparmor_parser", "aa-status"))
    userspace_absent = userspace_absent_from_debian_eye(debian_eye)
    kernel_ready = apparmor_cfg == "y"
    runtime_observed = bool(
        lsm.get("apparmor_enabled")
        or lsm.get("apparmor_listed")
        or proc_security.get("apparmor_present")
    )
    userspace_staged = any(mentions.values())
    if kernel_ready and (runtime_observed or userspace_staged):
        state = AUDIT_STATE_READY
        recommendation = "profile-source-can-start-after-live-lsm-and-parser-proof"
    else:
        state = AUDIT_STATE_UNAVAILABLE
        recommendation = "do-not-use-apparmor-as-immediate-d-harden-lever"
    missing = []
    if not kernel_ready:
        missing.append("CONFIG_SECURITY_APPARMOR=y")
    if not runtime_observed:
        missing.append("runtime LSM/AppArmor presence")
    if not userspace_staged:
        missing.append("apparmor userspace/parser staged in Debian rootfs")
    return {
        "schema": AUDIT_SCHEMA,
        "state": state,
        "source_evidence": {
            "d0_public_summary": rel(d0_path),
            "debian_eye_public_summary": rel(debian_eye_path),
            "rootfs_source_files": [rel(path) for path in source_paths],
        },
        "kernel": {
            "CONFIG_SECURITY_APPARMOR": apparmor_cfg,
            "CONFIG_SECURITYFS": securityfs_cfg,
            "CONFIG_DEFAULT_SECURITY": default_security,
            "kernel_config_ready": kernel_ready,
        },
        "runtime": {
            "lsm_summary_present": bool(lsm),
            "proc_security_summary_present": bool(proc_security),
            "apparmor_runtime_observed": runtime_observed,
        },
        "userspace": {
            "apparmor_source_mentions": mentions,
            "apparmor_userspace_staged": userspace_staged,
            "debian_eye_absent_observations": userspace_absent,
        },
        "profile_source": {
            "ready": state == AUDIT_STATE_READY,
            "blocked_missing_evidence": missing,
            "load_profiles_allowed": False,
            "reason": "WSTA214 is an audit only; loading profiles requires a separate explicit live gate",
        },
        "recommendation": recommendation,
        "preferred_current_hardening_lever": (
            "legacy-iptables-loopback-default-drop"
            if state == AUDIT_STATE_UNAVAILABLE
            else "apparmor-profile-source-after-live-proof"
        ),
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def validate_audit(audit: dict[str, Any]) -> dict[str, bool]:
    kernel = audit.get("kernel") if isinstance(audit.get("kernel"), dict) else {}
    runtime = audit.get("runtime") if isinstance(audit.get("runtime"), dict) else {}
    userspace = audit.get("userspace") if isinstance(audit.get("userspace"), dict) else {}
    profile = audit.get("profile_source") if isinstance(audit.get("profile_source"), dict) else {}
    unavailable = audit.get("state") == AUDIT_STATE_UNAVAILABLE
    ready = audit.get("state") == AUDIT_STATE_READY
    return {
        "schema_ok": audit.get("schema") == AUDIT_SCHEMA,
        "state_known": audit.get("state") in {AUDIT_STATE_UNAVAILABLE, AUDIT_STATE_READY},
        "kernel_config_recorded": "CONFIG_SECURITY_APPARMOR" in kernel,
        "runtime_observation_recorded": "apparmor_runtime_observed" in runtime,
        "userspace_staging_recorded": "apparmor_userspace_staged" in userspace,
        "unavailable_has_blocking_evidence": (
            not unavailable
            or (
                kernel.get("kernel_config_ready") is False
                and profile.get("ready") is False
                and bool(profile.get("blocked_missing_evidence"))
            )
        ),
        "ready_requires_kernel_and_runtime_or_userspace": (
            not ready
            or (
                kernel.get("kernel_config_ready") is True
                and (
                    runtime.get("apparmor_runtime_observed") is True
                    or userspace.get("apparmor_userspace_staged") is True
                )
            )
        ),
        "profile_load_stays_disabled": profile.get("load_profiles_allowed") is False,
        "redaction_clean": not bool(wsta89.redaction_findings(audit)),
    }


def markdown(audit: dict[str, Any], result: dict[str, Any]) -> str:
    kernel = audit.get("kernel", {})
    runtime = audit.get("runtime", {})
    userspace = audit.get("userspace", {})
    profile = audit.get("profile_source", {})
    lines = [
        "# WSTA214 AppArmor Feasibility",
        "",
        f"- Decision: `{result.get('decision')}`",
        f"- State: `{audit.get('state')}`",
        f"- Recommendation: `{audit.get('recommendation')}`",
        f"- Preferred current hardening lever: `{audit.get('preferred_current_hardening_lever')}`",
        "- Device action: `false`",
        "",
        "## Kernel",
        "",
        f"- CONFIG_SECURITY_APPARMOR: `{kernel.get('CONFIG_SECURITY_APPARMOR')}`",
        f"- CONFIG_SECURITYFS: `{kernel.get('CONFIG_SECURITYFS')}`",
        f"- CONFIG_DEFAULT_SECURITY: `{kernel.get('CONFIG_DEFAULT_SECURITY')}`",
        f"- Kernel config ready: `{str(bool(kernel.get('kernel_config_ready'))).lower()}`",
        "",
        "## Runtime And Userspace",
        "",
        f"- Runtime AppArmor observed: `{str(bool(runtime.get('apparmor_runtime_observed'))).lower()}`",
        f"- AppArmor userspace staged: `{str(bool(userspace.get('apparmor_userspace_staged'))).lower()}`",
        f"- Profile source ready: `{str(bool(profile.get('ready'))).lower()}`",
        f"- Profile load allowed: `{str(bool(profile.get('load_profiles_allowed'))).lower()}`",
        "",
        "## Missing Evidence",
        "",
    ]
    for item in profile.get("blocked_missing_evidence") or []:
        lines.append(f"- {item}")
    lines.extend(["", "## Checks", ""])
    for key, value in result.get("checks", {}).items():
        lines.append(f"- {key}: `{str(bool(value)).lower()}`")
    lines.append("")
    return "\n".join(lines)


def run(args: argparse.Namespace) -> dict[str, Any]:
    ts = utc_stamp()
    run_id = args.run_id or f"wsta214-apparmor-feasibility-{ts}"
    run_dir = resolve_path(args.run_dir or (DEFAULT_RUN_BASE / run_id))
    d0_path = resolve_path(args.d0_public_summary_json)
    debian_eye_path = resolve_path(args.debian_eye_public_summary_json)
    source_paths = [resolve_path(path) for path in args.source_path]
    result: dict[str, Any] = {
        "scope": "WSTA214 host-only AppArmor feasibility audit",
        "started_utc": ts,
        "run_dir": rel(run_dir),
        "safety": safety_flags(),
        "checks": {
            "explicit_gate": bool(args.audit_apparmor_feasibility),
            "private_run_dir": is_under(run_dir, PRIVATE_ROOT),
            "d0_summary_private": is_under(d0_path, PRIVATE_ROOT),
            "debian_eye_summary_private": is_under(debian_eye_path, PRIVATE_ROOT),
            "source_paths_public": all(is_under(path, REPO_ROOT) for path in source_paths),
            "d0_summary_present": d0_path.is_file(),
            "debian_eye_summary_present": debian_eye_path.is_file(),
            "source_paths_present": all(path.is_file() for path in source_paths),
        },
    }
    if not result["checks"]["explicit_gate"]:
        result["decision"] = "wsta214-blocked-explicit-gate-required"
        result["gate_decision"] = result["decision"]
        result["ended_utc"] = utc_stamp()
        return result
    for key, decision in [
        ("private_run_dir", "wsta214-blocked-nonprivate-run-dir"),
        ("d0_summary_private", "wsta214-blocked-d0-summary-nonprivate"),
        ("debian_eye_summary_private", "wsta214-blocked-debian-eye-summary-nonprivate"),
        ("source_paths_public", "wsta214-blocked-source-path-outside-repo"),
        ("d0_summary_present", "wsta214-blocked-d0-summary-missing"),
        ("debian_eye_summary_present", "wsta214-blocked-debian-eye-summary-missing"),
        ("source_paths_present", "wsta214-blocked-source-path-missing"),
    ]:
        if not result["checks"][key]:
            result["decision"] = decision
            result["gate_decision"] = decision
            result["ended_utc"] = utc_stamp()
            if result["checks"]["private_run_dir"]:
                run_dir.mkdir(parents=True, exist_ok=True)
                write_json(run_dir / SUMMARY_NAME, result)
            return result

    d0 = load_json(d0_path)
    debian_eye = load_json(debian_eye_path)
    audit = build_apparmor_audit(d0_path, d0, debian_eye_path, debian_eye, source_paths)
    audit_checks = validate_audit(audit)
    result["apparmor"] = {
        "schema": audit.get("schema"),
        "state": audit.get("state"),
        "recommendation": audit.get("recommendation"),
        "preferred_current_hardening_lever": audit.get("preferred_current_hardening_lever"),
        "kernel_config_ready": audit.get("kernel", {}).get("kernel_config_ready"),
        "runtime_observed": audit.get("runtime", {}).get("apparmor_runtime_observed"),
        "userspace_staged": audit.get("userspace", {}).get("apparmor_userspace_staged"),
        "profile_source_ready": audit.get("profile_source", {}).get("ready"),
    }
    result["checks"].update({f"audit_{key}": value for key, value in audit_checks.items()})
    result["decision"] = PASS_DECISION if all(audit_checks.values()) else "wsta214-blocked-audit-invalid"
    result["gate_decision"] = "ok" if result["decision"] == PASS_DECISION else result["decision"]
    result["ended_utc"] = utc_stamp()
    run_dir.mkdir(parents=True, exist_ok=True)
    write_json(run_dir / RESULT_NAME, audit)
    write_text(run_dir / MARKDOWN_NAME, markdown(audit, result))
    write_json(run_dir / SUMMARY_NAME, result)
    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--d0-public-summary-json", type=Path, default=DEFAULT_D0_SUMMARY)
    parser.add_argument("--debian-eye-public-summary-json", type=Path, default=DEFAULT_DEBIAN_EYE_SUMMARY)
    parser.add_argument("--source-path", type=Path, action="append", default=list(DEFAULT_SOURCE_PATHS))
    parser.add_argument("--audit-apparmor-feasibility", action="store_true")
    parser.add_argument("--print-full-json", action="store_true")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    result = run(args)
    payload = result if args.print_full_json else public_summary(result)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.get("decision") == PASS_DECISION else 1


if __name__ == "__main__":
    raise SystemExit(main())
