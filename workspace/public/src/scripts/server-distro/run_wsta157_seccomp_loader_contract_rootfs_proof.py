#!/usr/bin/env python3
"""WSTA157 host-only seccomp loader-contract rootfs proof.

Stages the WSTA153 policy and WSTA156 non-loaded filter artifact into a private
rootfs directory, then proves the launcher can observe the artifact while still
keeping enforcement disabled by default.  A second run with
``A90_SERVICE_LAUNCH_SECCOMP_ENFORCE=1`` must fail closed before exec because
the actual loader is not implemented yet.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import prepare_wsta3_sta_rootfs as wsta3  # noqa: E402


REPO_ROOT = wsta3.REPO_ROOT
PRIVATE_ROOT = REPO_ROOT / "workspace/private"
DEFAULT_RUN_BASE = wsta3.DEFAULT_RUN_BASE
DEFAULT_WSTA153_POLICY = wsta3.DEFAULT_SECCOMP_POLICY_SOURCE
DEFAULT_WSTA156_MANIFEST = wsta3.DEFAULT_SECCOMP_FILTER_MANIFEST
DEFAULT_WSTA156_OBJECT = wsta3.DEFAULT_SECCOMP_FILTER_OBJECT
PASS_DECISION = "wsta157-seccomp-loader-contract-rootfs-proof-pass"
SUMMARY_NAME = "wsta157_result.json"
DRY_RUN_STDOUT_NAME = "launcher_artifact_dry_run_stdout.txt"
ENFORCE_STDOUT_NAME = "launcher_enforce_flag_stdout.txt"


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
    wsta3.write_json(path, payload)


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
        "chroot": False,
        "seccomp_filter_built": False,
        "seccomp_filter_loaded": False,
        "seccomp_enforced": False,
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def public_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": result.get("decision"),
        "run_dir": result.get("run_dir"),
        "gate_decision": result.get("gate_decision"),
        "proof": result.get("proof", {}),
        "checks": result.get("checks", {}),
        "safety": result.get("safety", {}),
    }


def make_fake_setpriv(fakebin: Path) -> None:
    fakebin.mkdir(parents=True, exist_ok=True)
    fake = fakebin / "setpriv"
    fake.write_text(
        "#!/bin/sh\n"
        "echo \"fake_setpriv_args=$*\"\n"
        "exit 0\n",
        encoding="utf-8",
    )
    fake.chmod(0o755)


def stage_rootfs(rootfs: Path, policy_path: Path, manifest_path: Path, object_path: Path) -> dict[str, Any]:
    return {
        "service_launcher": wsta3.stage_no_new_privs_launcher(rootfs),
        "service_hardening_policy": wsta3.stage_service_hardening_policy(rootfs),
        "seccomp_launcher_policy": wsta3.stage_seccomp_launcher_policy(rootfs, policy_path, require=True),
        "seccomp_filter_artifact": wsta3.stage_seccomp_filter_artifact(
            rootfs,
            manifest_path,
            object_path,
            require=True,
        ),
        "service_hardening_stage_marker": wsta3.stage_service_hardening_stage_marker(rootfs),
    }


def run_launcher(rootfs: Path, fakebin: Path, *, enforce: bool) -> dict[str, Any]:
    env = os.environ.copy()
    env["PATH"] = f"{fakebin}:{env.get('PATH', '')}"
    env["A90_SERVICE_LAUNCH_SECCOMP_DRY_RUN"] = "1"
    env["A90_SERVICE_LAUNCH_SECCOMP_POLICY"] = str(rootfs / wsta3.TARGET_SECCOMP_POLICY)
    env["A90_SERVICE_LAUNCH_SECCOMP_MAP"] = str(rootfs / wsta3.TARGET_SECCOMP_LAUNCHER_MAP)
    env["A90_SERVICE_LAUNCH_SECCOMP_FILTER_MANIFEST"] = str(rootfs / wsta3.TARGET_SECCOMP_FILTER_MANIFEST)
    env["A90_SERVICE_LAUNCH_SECCOMP_FILTER_OBJECT"] = str(rootfs / wsta3.TARGET_SECCOMP_FILTER_OBJECT)
    if enforce:
        env["A90_SERVICE_LAUNCH_SECCOMP_ENFORCE"] = "1"
    proc = subprocess.run(
        [str(rootfs / wsta3.TARGET_SERVICE_LAUNCHER), "dpublic-hud", "/bin/true"],
        check=False,
        capture_output=True,
        text=True,
        env=env,
        timeout=5.0,
    )
    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def marker_value(stdout: str, key: str) -> str | None:
    prefix = key + "="
    for line in stdout.splitlines():
        if line.startswith(prefix):
            return line.split("=", 1)[1]
    return None


def validate_proof(dry_run: dict[str, Any], enforce_run: dict[str, Any]) -> dict[str, bool]:
    dry_stdout = str(dry_run.get("stdout") or "")
    enforce_stdout = str(enforce_run.get("stdout") or "")
    return {
        "dry_run_returncode_zero": dry_run.get("returncode") == 0,
        "dry_run_artifact_present": marker_value(dry_stdout, "A90WSTA157_SECCOMP_ARTIFACT_PRESENT") == "1",
        "dry_run_enforce_flag_zero": marker_value(dry_stdout, "A90WSTA157_SECCOMP_ENFORCE_FLAG") == "0",
        "dry_run_filter_load_zero": marker_value(dry_stdout, "A90WSTA154_SECCOMP_FILTER_LOAD") == "0",
        "dry_run_profile_hud_intent": (
            marker_value(dry_stdout, "A90WSTA154_SECCOMP_PROFILE")
            == "seccomp-dpublic-hud-intent-observed-v1"
        ),
        "dry_run_exec_reached": "a90_service_launcher_decision=exec" in dry_stdout,
        "dry_run_fake_setpriv_called": "fake_setpriv_args=--no-new-privs --reuid a90hud --regid a90hud" in dry_stdout,
        "enforce_returncode_65": enforce_run.get("returncode") == 65,
        "enforce_artifact_present": marker_value(enforce_stdout, "A90WSTA157_SECCOMP_ARTIFACT_PRESENT") == "1",
        "enforce_flag_one": marker_value(enforce_stdout, "A90WSTA157_SECCOMP_ENFORCE_FLAG") == "1",
        "enforce_blocks_unimplemented": (
            "a90_service_launcher_decision=blocked-seccomp-enforce-unimplemented" in enforce_stdout
        ),
        "enforce_blocks_before_exec": (
            "fake_setpriv_args=" not in enforce_stdout
            and "a90_service_launcher_decision=exec" not in enforce_stdout
        ),
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    ts = utc_stamp()
    run_id = args.run_id or f"wsta157-seccomp-loader-contract-rootfs-proof-{ts}"
    run_dir = resolve_path(args.run_dir or (DEFAULT_RUN_BASE / run_id))
    policy_path = resolve_path(args.wsta153_seccomp_policy_json)
    manifest_path = resolve_path(args.wsta156_filter_manifest_json)
    object_path = resolve_path(args.wsta156_filter_object)
    result: dict[str, Any] = {
        "scope": "WSTA157 host-only seccomp loader-contract rootfs proof",
        "started_utc": ts,
        "run_dir": rel(run_dir),
        "safety": safety_flags(),
        "checks": {
            "explicit_gate": bool(args.emit_seccomp_loader_contract_proof),
            "private_run_dir": is_under(run_dir, PRIVATE_ROOT),
            "policy_json_private": is_under(policy_path, PRIVATE_ROOT),
            "policy_json_present": policy_path.is_file(),
            "filter_manifest_private": is_under(manifest_path, PRIVATE_ROOT),
            "filter_manifest_present": manifest_path.is_file(),
            "filter_object_private": is_under(object_path, PRIVATE_ROOT),
            "filter_object_present": object_path.is_file(),
        },
    }
    for key, decision in (
        ("explicit_gate", "wsta157-blocked-explicit-gate-required"),
        ("private_run_dir", "wsta157-blocked-nonprivate-run-dir"),
        ("policy_json_private", "wsta157-blocked-policy-json-nonprivate"),
        ("policy_json_present", "wsta157-blocked-policy-json-missing"),
        ("filter_manifest_private", "wsta157-blocked-filter-manifest-nonprivate"),
        ("filter_manifest_present", "wsta157-blocked-filter-manifest-missing"),
        ("filter_object_private", "wsta157-blocked-filter-object-nonprivate"),
        ("filter_object_present", "wsta157-blocked-filter-object-missing"),
    ):
        if not result["checks"][key]:
            result["decision"] = decision
            result["gate_decision"] = decision
            result["ended_utc"] = utc_stamp()
            if key.endswith("_present"):
                run_dir.mkdir(parents=True, exist_ok=True)
                write_json(run_dir / SUMMARY_NAME, result)
            return result

    rootfs = run_dir / "rootfs"
    fakebin = run_dir / "fakebin"
    rootfs.mkdir(parents=True, exist_ok=True)
    make_fake_setpriv(fakebin)
    stage = stage_rootfs(rootfs, policy_path, manifest_path, object_path)
    dry_run = run_launcher(rootfs, fakebin, enforce=False)
    enforce_run = run_launcher(rootfs, fakebin, enforce=True)
    proof_checks = validate_proof(dry_run, enforce_run)
    result["stage"] = stage
    result["proof"] = {
        "service": "dpublic-hud",
        "dry_run_stdout_artifact": rel(run_dir / DRY_RUN_STDOUT_NAME),
        "enforce_stdout_artifact": rel(run_dir / ENFORCE_STDOUT_NAME),
        "dry_run_returncode": dry_run.get("returncode"),
        "enforce_returncode": enforce_run.get("returncode"),
        "filter_load_enabled": False,
        "seccomp_enforced": False,
    }
    result["proof_checks"] = proof_checks
    result["checks"].update({f"proof_{key}": value for key, value in proof_checks.items()})
    result["decision"] = PASS_DECISION if all(proof_checks.values()) else "wsta157-blocked-proof-invalid"
    result["gate_decision"] = "ok" if result["decision"] == PASS_DECISION else result["decision"]
    result["ended_utc"] = utc_stamp()
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / DRY_RUN_STDOUT_NAME).write_text(str(dry_run.get("stdout") or ""), encoding="utf-8")
    (run_dir / ENFORCE_STDOUT_NAME).write_text(str(enforce_run.get("stdout") or ""), encoding="utf-8")
    write_json(run_dir / SUMMARY_NAME, result)
    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--wsta153-seccomp-policy-json", type=Path, default=DEFAULT_WSTA153_POLICY)
    parser.add_argument("--wsta156-filter-manifest-json", type=Path, default=DEFAULT_WSTA156_MANIFEST)
    parser.add_argument("--wsta156-filter-object", type=Path, default=DEFAULT_WSTA156_OBJECT)
    parser.add_argument("--emit-seccomp-loader-contract-proof", action="store_true")
    parser.add_argument("--print-full-json", action="store_true")
    return parser


def main_with_args(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        result = run(args)
    except Exception as exc:  # noqa: BLE001
        payload = {"decision": "wsta157-runner-error", "error": str(exc)}
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1
    payload = result if args.print_full_json else public_summary(result)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.get("decision") == PASS_DECISION else 2


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
