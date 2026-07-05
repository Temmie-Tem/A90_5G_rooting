#!/usr/bin/env python3
"""WSTA163 host-only chroot proof for launcher helper-apply gate.

Stages the WSTA161 gated-apply helper into a private full rootfs and proves the
service launcher has a future ``helper --apply`` path that is itself gated.  The
first chroot run blocks before invoking the helper because the launcher apply
gate is missing.  The second supplies the launcher apply gate, invokes the
helper with ``--apply``, and proves the WSTA161 helper still blocks before any
seccomp load attempt because the helper load token is absent.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import prepare_wsta3_sta_rootfs as wsta3  # noqa: E402
import run_wsta160_seccomp_full_rootfs_chroot_dry_run as wsta160  # noqa: E402
import run_wsta162_seccomp_gated_apply_full_rootfs_chroot_dry_run as wsta162  # noqa: E402


REPO_ROOT = wsta3.REPO_ROOT
PRIVATE_ROOT = REPO_ROOT / "workspace/private"
DEFAULT_RUN_BASE = wsta3.DEFAULT_RUN_BASE
DEFAULT_SOURCE_ROOTFS = wsta3.DEFAULT_SOURCE_ROOTFS
DEFAULT_WSTA153_POLICY = wsta3.DEFAULT_SECCOMP_POLICY_SOURCE
DEFAULT_WSTA156_MANIFEST = wsta3.DEFAULT_SECCOMP_FILTER_MANIFEST
DEFAULT_WSTA156_OBJECT = wsta3.DEFAULT_SECCOMP_FILTER_OBJECT
DEFAULT_WSTA161_MANIFEST = wsta162.DEFAULT_WSTA161_MANIFEST
DEFAULT_WSTA161_HELPER = wsta162.DEFAULT_WSTA161_HELPER
PASS_DECISION = "wsta163-seccomp-helper-apply-gate-chroot-proof-pass"
SUMMARY_NAME = "wsta163_result.json"
MISSING_GATE_STDOUT_NAME = "helper_apply_missing_gate_stdout.txt"
HELPER_BLOCK_STDOUT_NAME = "helper_apply_helper_block_stdout.txt"


def rel(path: Path) -> str:
    return wsta3.rel(path)


def utc_stamp() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def write_json(path: Path, payload: Any) -> None:
    wsta3.write_json(path, payload)


def safety_flags() -> dict[str, Any]:
    flags = wsta162.safety_flags()
    flags["seccomp_helper_apply_path_exercised_without_load_token"] = True
    return flags


def public_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": result.get("decision"),
        "run_dir": result.get("run_dir"),
        "gate_decision": result.get("gate_decision"),
        "proof": result.get("proof", {}),
        "checks": result.get("checks", {}),
        "safety": result.get("safety", {}),
    }


def run_chroot_launcher_apply(unshare_cmd: str, rootfs: Path, *, include_apply_gate: bool) -> dict[str, Any]:
    env_items = [
        "PATH=/fakebin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        "A90_SERVICE_LAUNCH_SECCOMP_DRY_RUN=1",
        "A90_SERVICE_LAUNCH_SECCOMP_ENFORCE=1",
        "A90_SERVICE_LAUNCH_SECCOMP_HELPER_MODE=apply",
    ]
    if include_apply_gate:
        env_items.append("A90_SERVICE_LAUNCH_SECCOMP_HELPER_APPLY_GATE=WSTA163-ALLOW-HELPER-APPLY")
    command = [
        unshare_cmd,
        "-r",
        "chroot",
        str(rootfs),
        "/usr/bin/env",
        "-i",
        *env_items,
        "/usr/local/bin/a90-service-launch",
        "dpublic-hud",
        "/bin/true",
    ]
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        timeout=30.0,
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def validate_proof(missing_gate_run: dict[str, Any], helper_block_run: dict[str, Any]) -> dict[str, bool]:
    missing_stdout = str(missing_gate_run.get("stdout") or "")
    helper_stdout = str(helper_block_run.get("stdout") or "")
    return {
        "missing_gate_returncode_65": missing_gate_run.get("returncode") == 65,
        "missing_gate_mode_apply": wsta160.marker_value(missing_stdout, "A90WSTA163_SECCOMP_HELPER_MODE") == "apply",
        "missing_gate_blocks_before_helper": (
            "a90_service_launcher_decision=blocked-seccomp-helper-apply-gate-required" in missing_stdout
        ),
        "missing_gate_no_helper_output": "A90WSTA161_LOADER_GATED_APPLY=1" not in missing_stdout,
        "helper_block_returncode_65": helper_block_run.get("returncode") == 65,
        "helper_block_mode_apply": wsta160.marker_value(helper_stdout, "A90WSTA163_SECCOMP_HELPER_MODE") == "apply",
        "helper_invoked_apply": wsta160.marker_value(helper_stdout, "A90WSTA161_LOADER_GATED_APPLY") == "1",
        "helper_load_zero": wsta160.marker_value(helper_stdout, "A90WSTA161_SECCOMP_LOAD") == "0",
        "helper_hud_profile": "service=dpublic-hud policy_service=dpublic-hud-intent" in helper_stdout,
        "helper_blocks_load_gate": "a90_seccomp_loader_decision=blocked-load-gate-required" in helper_stdout,
        "helper_no_load_attempt": "A90WSTA161_SECCOMP_LOAD_ATTEMPT=1" not in helper_stdout,
        "launcher_reports_helper_apply_failed": (
            "a90_service_launcher_decision=blocked-seccomp-helper-apply-failed" in helper_stdout
        ),
        "helper_blocks_before_exec": (
            "fake_setpriv_args=" not in helper_stdout
            and "a90_service_launcher_decision=exec" not in helper_stdout
        ),
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    ts = utc_stamp()
    run_id = args.run_id or f"wsta163-seccomp-helper-apply-gate-chroot-proof-{ts}"
    run_dir = resolve_path(args.run_dir or (DEFAULT_RUN_BASE / run_id))
    paths = {
        "source_rootfs": resolve_path(args.source_rootfs),
        "policy_json": resolve_path(args.wsta153_seccomp_policy_json),
        "filter_manifest": resolve_path(args.wsta156_filter_manifest_json),
        "filter_object": resolve_path(args.wsta156_filter_object),
        "helper_manifest": resolve_path(args.wsta161_loader_helper_manifest_json),
        "helper_binary": resolve_path(args.wsta161_loader_helper),
    }
    unshare_path = shutil.which(args.unshare)
    result: dict[str, Any] = {
        "scope": "WSTA163 host-only seccomp helper apply gate chroot proof",
        "started_utc": ts,
        "run_dir": rel(run_dir),
        "safety": safety_flags(),
        "checks": {
            "explicit_gate": bool(args.execute_helper_apply_gate_chroot_proof),
            "private_run_dir": wsta160.is_under(run_dir, PRIVATE_ROOT),
            "source_rootfs_private": wsta160.is_under(paths["source_rootfs"], PRIVATE_ROOT),
            "source_rootfs_present": paths["source_rootfs"].is_dir(),
            "policy_json_private": wsta160.is_under(paths["policy_json"], PRIVATE_ROOT),
            "policy_json_present": paths["policy_json"].is_file(),
            "filter_manifest_private": wsta160.is_under(paths["filter_manifest"], PRIVATE_ROOT),
            "filter_manifest_present": paths["filter_manifest"].is_file(),
            "filter_object_private": wsta160.is_under(paths["filter_object"], PRIVATE_ROOT),
            "filter_object_present": paths["filter_object"].is_file(),
            "helper_manifest_private": wsta160.is_under(paths["helper_manifest"], PRIVATE_ROOT),
            "helper_manifest_present": paths["helper_manifest"].is_file(),
            "helper_binary_private": wsta160.is_under(paths["helper_binary"], PRIVATE_ROOT),
            "helper_binary_present": paths["helper_binary"].is_file(),
            "unshare_present": bool(unshare_path),
        },
    }
    for key, decision in (
        ("explicit_gate", "wsta163-blocked-explicit-gate-required"),
        ("private_run_dir", "wsta163-blocked-nonprivate-run-dir"),
        ("source_rootfs_private", "wsta163-blocked-source-rootfs-nonprivate"),
        ("source_rootfs_present", "wsta163-blocked-source-rootfs-missing"),
        ("policy_json_private", "wsta163-blocked-policy-json-nonprivate"),
        ("policy_json_present", "wsta163-blocked-policy-json-missing"),
        ("filter_manifest_private", "wsta163-blocked-filter-manifest-nonprivate"),
        ("filter_manifest_present", "wsta163-blocked-filter-manifest-missing"),
        ("filter_object_private", "wsta163-blocked-filter-object-nonprivate"),
        ("filter_object_present", "wsta163-blocked-filter-object-missing"),
        ("helper_manifest_private", "wsta163-blocked-helper-manifest-nonprivate"),
        ("helper_manifest_present", "wsta163-blocked-helper-manifest-missing"),
        ("helper_binary_private", "wsta163-blocked-helper-binary-nonprivate"),
        ("helper_binary_present", "wsta163-blocked-helper-binary-missing"),
        ("unshare_present", "wsta163-blocked-unshare-missing"),
    ):
        if not result["checks"][key]:
            result["decision"] = decision
            result["gate_decision"] = decision
            result["ended_utc"] = utc_stamp()
            if key.endswith("_present"):
                run_dir.mkdir(parents=True, exist_ok=True)
                write_json(run_dir / SUMMARY_NAME, result)
            return result

    run_dir.mkdir(parents=True, exist_ok=True)
    rootfs = run_dir / "rootfs"
    wsta3.d4c.verify_rootfs(paths["source_rootfs"])
    wsta3.copy_rootfs(paths["source_rootfs"], rootfs)
    stage = wsta160.stage_full_rootfs(
        rootfs,
        paths["policy_json"],
        paths["filter_manifest"],
        paths["filter_object"],
        paths["helper_manifest"],
        paths["helper_binary"],
    )
    wsta3.d4c.verify_rootfs(rootfs)
    result["stage"] = stage
    result["checks"]["helper_schema_is_wsta161"] = (
        stage["seccomp_loader_helper"].get("helper_schema")
        == "a90-wsta161-seccomp-loader-gated-apply-helper-v1"
    )
    result["checks"]["helper_apply_code_compiled"] = stage["seccomp_loader_helper"].get("apply_code_compiled") is True
    wsta160.make_fake_setpriv(rootfs)
    missing_gate_run = run_chroot_launcher_apply(args.unshare, rootfs, include_apply_gate=False)
    helper_block_run = run_chroot_launcher_apply(args.unshare, rootfs, include_apply_gate=True)
    proof_checks = validate_proof(missing_gate_run, helper_block_run)
    result["proof"] = {
        "rootfs": rel(rootfs),
        "default_helper_path_inside_chroot": "/" + str(wsta3.TARGET_SECCOMP_LOADER_HELPER),
        "helper_schema": stage["seccomp_loader_helper"].get("helper_schema"),
        "missing_gate_stdout_artifact": rel(run_dir / MISSING_GATE_STDOUT_NAME),
        "helper_block_stdout_artifact": rel(run_dir / HELPER_BLOCK_STDOUT_NAME),
        "missing_gate_returncode": missing_gate_run.get("returncode"),
        "helper_block_returncode": helper_block_run.get("returncode"),
        "filter_load_enabled": False,
        "seccomp_enforced": False,
    }
    result["proof_checks"] = proof_checks
    result["checks"].update({f"proof_{key}": value for key, value in proof_checks.items()})
    result["decision"] = PASS_DECISION if all(proof_checks.values()) else "wsta163-blocked-proof-invalid"
    result["gate_decision"] = "ok" if result["decision"] == PASS_DECISION else result["decision"]
    result["ended_utc"] = utc_stamp()
    (run_dir / MISSING_GATE_STDOUT_NAME).write_text(str(missing_gate_run.get("stdout") or ""), encoding="utf-8")
    (run_dir / HELPER_BLOCK_STDOUT_NAME).write_text(str(helper_block_run.get("stdout") or ""), encoding="utf-8")
    write_json(run_dir / SUMMARY_NAME, result)
    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--source-rootfs", type=Path, default=DEFAULT_SOURCE_ROOTFS)
    parser.add_argument("--wsta153-seccomp-policy-json", type=Path, default=DEFAULT_WSTA153_POLICY)
    parser.add_argument("--wsta156-filter-manifest-json", type=Path, default=DEFAULT_WSTA156_MANIFEST)
    parser.add_argument("--wsta156-filter-object", type=Path, default=DEFAULT_WSTA156_OBJECT)
    parser.add_argument("--wsta161-loader-helper-manifest-json", type=Path, default=DEFAULT_WSTA161_MANIFEST)
    parser.add_argument("--wsta161-loader-helper", type=Path, default=DEFAULT_WSTA161_HELPER)
    parser.add_argument("--unshare", default="unshare")
    parser.add_argument("--execute-helper-apply-gate-chroot-proof", action="store_true")
    parser.add_argument("--print-full-json", action="store_true")
    return parser


def main_with_args(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        result = run(args)
    except Exception as exc:  # noqa: BLE001
        payload = {"decision": "wsta163-runner-error", "error": str(exc)}
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1
    payload = result if args.print_full_json else public_summary(result)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.get("decision") == PASS_DECISION else 2


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
