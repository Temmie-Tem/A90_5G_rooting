#!/usr/bin/env python3
"""WSTA151 host-only summary for the Dropbear admin syscall trace proof."""

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
import run_wsta151_dropbear_admin_syscall_trace as wsta151  # noqa: E402


REPO_ROOT = wsta3.REPO_ROOT
PRIVATE_ROOT = REPO_ROOT / "workspace/private"
DEFAULT_RUN_BASE = wsta3.DEFAULT_RUN_BASE
PASS_DECISION = wsta151.PASS_DECISION
RESULT_NAME = "wsta151_dropbear_admin_syscall_trace_live.json"
CORE_SYSCALLS = wsta151.CORE_SYSCALLS
ACCEPT_SYSCALLS = wsta151.ACCEPT_SYSCALLS


def rel(path: Path) -> str:
    return wsta3.rel(path)


def utc_stamp() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fp:
        payload = json.load(fp)
    if not isinstance(payload, dict):
        raise ValueError(f"expected object JSON: {path}")
    return payload


def safety() -> dict[str, Any]:
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
        "public_url_value_logged": False,
        "admin_public_key_value_logged": False,
        "secret_values_logged": 0,
    }


def validate_source_result(source: dict[str, Any]) -> dict[str, bool]:
    checks = source.get("checks") if isinstance(source.get("checks"), dict) else {}
    profile = source.get("syscall_profile") if isinstance(source.get("syscall_profile"), dict) else {}
    trace_artifacts = (
        profile.get("trace_artifacts")
        if isinstance(profile.get("trace_artifacts"), dict)
        else {}
    )
    syscalls = profile.get("syscall_names") if isinstance(profile.get("syscall_names"), list) else []
    final_version = source.get("final_version") if isinstance(source.get("final_version"), dict) else {}
    final_selftest = source.get("final_selftest") if isinstance(source.get("final_selftest"), dict) else {}
    safety_record = source.get("safety") if isinstance(source.get("safety"), dict) else {}
    no_forbidden_mutation = all(
        safety_record.get(key) is False
        for key in (
            "boot_flash",
            "native_reboot",
            "wifi_connect",
            "dhcp",
            "public_tunnel",
            "public_smoke",
            "packet_filter_mutation",
            "userdata_touch",
            "switch_root",
        )
    )
    return {
        "source_decision_pass": source.get("decision") == wsta151.PASS_DECISION,
        "source_no_forbidden_device_mutation": no_forbidden_mutation,
        "strace_image_sha_match": source.get("local_image_sha256") == wsta151.WSTA115_STRACE_IMAGE_SHA256,
        "admin_boundary_proven": bool(
            checks.get("admin_trace_stage_pass")
            and checks.get("admin_ssh_pass")
            and checks.get("root_ssh_rejected")
            and profile.get("admin_login_uid_gid_proven")
            and profile.get("root_ssh_rejected")
            and profile.get("root_authorized_keys_absent")
        ),
        "daemon_policy_proven": bool(
            profile.get("service") == "dropbear-admin-usb"
            and profile.get("scope") == "dropbear-admin-usb-daemon"
            and profile.get("daemon_privilege_model") == "root-boundary-auth-daemon"
            and profile.get("network_scope") == "usb-ncm-admin-only"
            and profile.get("password_login_disabled")
            and profile.get("root_login_disabled")
            and profile.get("forwarding_disabled")
        ),
        "core_syscalls_proven": bool(
            checks.get("syscall_core_observed")
            and profile.get("core_syscalls_observed")
            and all(name in syscalls for name in wsta151.CORE_SYSCALLS)
        ),
        "accept_syscall_proven": bool(
            checks.get("syscall_accept_observed")
            and profile.get("accept_observed")
            and any(name in syscalls for name in wsta151.ACCEPT_SYSCALLS)
        ),
        "trace_artifacts_saved": bool(checks.get("trace_artifact_saved") and trace_artifacts.get("all_saved")),
        "log_policy_clean": bool(checks.get("dropbear_log_policy_clean")),
        "cleanup_ok": bool(
            checks.get("trace_cleanup_ok")
            and checks.get("chroot_cleanup_ok")
            and checks.get("final_selftest_fail_zero")
        ),
        "final_health_clean": bool(
            checks.get("final_selftest_fail_zero")
            and "v3402-dpublic-hud-presenter-restart-policy" in str(final_version.get("text") or "")
            and "selftest: pass=12 warn=1 fail=0" in str(final_selftest.get("text") or "")
        ),
        "redaction_clean": bool(
            source.get("public_url_value_logged") is not True
            and source.get("admin_public_key_value_logged") is not True
            and int(source.get("secret_values_logged") or 0) == 0
            and profile.get("public_url_value_logged") is False
            and profile.get("admin_public_key_value_logged") is False
            and int(profile.get("secret_values_logged") or 0) == 0
        ),
    }


def summarize_source(source: dict[str, Any], source_path: Path) -> dict[str, Any]:
    profile = source.get("syscall_profile") if isinstance(source.get("syscall_profile"), dict) else {}
    trace_artifacts = (
        profile.get("trace_artifacts")
        if isinstance(profile.get("trace_artifacts"), dict)
        else {}
    )
    raw_trace = trace_artifacts.get("raw_trace") if isinstance(trace_artifacts.get("raw_trace"), dict) else {}
    syscall_list = (
        trace_artifacts.get("syscall_list")
        if isinstance(trace_artifacts.get("syscall_list"), dict)
        else {}
    )
    dropbear_log = (
        trace_artifacts.get("dropbear_log")
        if isinstance(trace_artifacts.get("dropbear_log"), dict)
        else {}
    )
    proof = {
        "schema": "a90-wsta151-dropbear-admin-syscall-trace-live-v1",
        "source_json": rel(source_path),
        "source_run_dir": source.get("run_dir"),
        "service": "dropbear-admin-usb",
        "scope": "dropbear-admin-usb-daemon",
        "daemon": profile.get("daemon"),
        "daemon_privilege_model": profile.get("daemon_privilege_model"),
        "bind": profile.get("bind"),
        "network_scope": profile.get("network_scope"),
        "uid": 3903,
        "gid": 3903,
        "admin_login_uid_gid_proven": bool(profile.get("admin_login_uid_gid_proven")),
        "root_ssh_rejected": bool(profile.get("root_ssh_rejected")),
        "root_authorized_keys_absent": bool(profile.get("root_authorized_keys_absent")),
        "password_login_disabled": bool(profile.get("password_login_disabled")),
        "root_login_disabled": bool(profile.get("root_login_disabled")),
        "forwarding_disabled": bool(profile.get("forwarding_disabled")),
        "core_syscalls_observed": bool(profile.get("core_syscalls_observed")),
        "accept_observed": bool(profile.get("accept_observed")),
        "core_syscalls": list(profile.get("core_syscalls") or []),
        "accept_syscalls": list(profile.get("accept_syscalls") or []),
        "syscall_count": int(profile.get("syscall_count") or 0),
        "syscall_names": list(profile.get("syscall_names") or []),
        "trace_artifacts_saved": bool(trace_artifacts.get("all_saved")),
        "raw_trace_sha256": raw_trace.get("sha256"),
        "syscall_list_sha256": syscall_list.get("sha256"),
        "dropbear_log_sha256": dropbear_log.get("sha256"),
        "checks": validate_source_result(source),
        "public_url_value_logged": False,
        "admin_public_key_value_logged": False,
        "secret_values_logged": 0,
    }
    proof["decision"] = PASS_DECISION if all(proof["checks"].values()) else "wsta151-dropbear-admin-syscall-trace-live-fail"
    return proof


def run(args: argparse.Namespace) -> dict[str, Any]:
    ts = utc_stamp()
    run_id = args.run_id or f"wsta151-dropbear-admin-syscall-trace-summary-{ts}"
    run_dir = resolve_path(args.run_dir or (DEFAULT_RUN_BASE / run_id))
    result: dict[str, Any] = {
        "scope": "WSTA151 host-only Dropbear admin syscall trace summary",
        "started_utc": ts,
        "run_dir": rel(run_dir),
        "safety": safety(),
        "checks": {
            "explicit_gate": bool(args.summarize_wsta151_dropbear_admin_trace),
            "private_run_dir": is_under(run_dir, PRIVATE_ROOT),
        },
    }
    if not result["checks"]["explicit_gate"]:
        result["decision"] = "wsta151-summary-blocked-explicit-gate-required"
        result["ended_utc"] = utc_stamp()
        return result
    if not result["checks"]["private_run_dir"]:
        result["decision"] = "wsta151-summary-blocked-nonprivate-run-dir"
        result["ended_utc"] = utc_stamp()
        return result
    source_json = resolve_path(args.source_json)
    if not source_json.is_file():
        result["decision"] = "wsta151-summary-blocked-source-json-missing"
        result["source_json"] = rel(source_json)
        result["ended_utc"] = utc_stamp()
        return result
    source = load_json(source_json)
    proof = summarize_source(source, source_json)
    result["proof"] = proof
    result["decision"] = proof["decision"]
    result["checks"].update({
        "source_json_present": True,
        "source_result_valid": proof["decision"] == PASS_DECISION,
        "redaction_clean": bool(proof["checks"].get("redaction_clean")),
    })
    result["ended_utc"] = utc_stamp()
    run_dir.mkdir(parents=True, exist_ok=True)
    write_json(run_dir / RESULT_NAME, proof)
    write_json(run_dir / "wsta151_summary_result.json", result)
    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument(
        "--source-json",
        type=Path,
        default=DEFAULT_RUN_BASE / "wsta151-dropbear-admin-syscall-trace-live-20260705T113918KST" / "wsta151_result.json",
    )
    parser.add_argument("--summarize-wsta151-dropbear-admin-trace", action="store_true")
    return parser


def main_with_args(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        result = run(args)
    except Exception as exc:  # noqa: BLE001
        result = {"decision": "wsta151-summary-runner-error", "error": str(exc)}
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("decision") == PASS_DECISION else 2


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
