#!/usr/bin/env python3
"""WSTA155 host-only launcher seccomp dry-run rootfs proof.

Stages the WSTA155 launcher dry-run policy files into a private rootfs
directory, runs ``a90-service-launch`` with a fake ``setpriv`` binary, and
proves the WSTA154 dry-run markers are observable before exec.  It also proves a
missing seccomp launcher map blocks before exec.  No chroot, device action,
filter build, filter load, or seccomp enforcement occurs.
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
PASS_DECISION = "wsta155-seccomp-launcher-dry-run-rootfs-proof-pass"
SUMMARY_NAME = "wsta155_result.json"
STDOUT_NAME = "launcher_dry_run_stdout.txt"
MISSING_MAP_STDOUT_NAME = "launcher_missing_map_stdout.txt"


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


def make_fake_setpriv(fakebin: Path) -> Path:
    fakebin.mkdir(parents=True, exist_ok=True)
    fake = fakebin / "setpriv"
    fake.write_text(
        "#!/bin/sh\n"
        "echo \"fake_setpriv_args=$*\"\n"
        "exit 0\n",
        encoding="utf-8",
    )
    fake.chmod(0o755)
    return fake


def stage_rootfs(rootfs: Path, policy_path: Path) -> dict[str, Any]:
    return {
        "service_launcher": wsta3.stage_no_new_privs_launcher(rootfs),
        "service_hardening_policy": wsta3.stage_service_hardening_policy(rootfs),
        "seccomp_launcher_policy": wsta3.stage_seccomp_launcher_policy(rootfs, policy_path, require=True),
        "service_hardening_stage_marker": wsta3.stage_service_hardening_stage_marker(rootfs),
    }


def run_launcher(rootfs: Path, fakebin: Path, *, service: str = "dpublic-hud") -> dict[str, Any]:
    env = os.environ.copy()
    env["PATH"] = f"{fakebin}:{env.get('PATH', '')}"
    env["A90_SERVICE_LAUNCH_SECCOMP_DRY_RUN"] = "1"
    env["A90_SERVICE_LAUNCH_SECCOMP_POLICY"] = str(rootfs / wsta3.TARGET_SECCOMP_POLICY)
    env["A90_SERVICE_LAUNCH_SECCOMP_MAP"] = str(rootfs / wsta3.TARGET_SECCOMP_LAUNCHER_MAP)
    proc = subprocess.run(
        [str(rootfs / wsta3.TARGET_SERVICE_LAUNCHER), service, "/bin/true"],
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


def validate_proof(primary: dict[str, Any], missing_map: dict[str, Any]) -> dict[str, bool]:
    stdout = str(primary.get("stdout") or "")
    missing_stdout = str(missing_map.get("stdout") or "")
    return {
        "primary_returncode_zero": primary.get("returncode") == 0,
        "policy_present_marker": marker_value(stdout, "A90WSTA154_SECCOMP_POLICY_PRESENT") == "1",
        "dry_run_only_marker": marker_value(stdout, "A90WSTA154_SECCOMP_DRY_RUN_ONLY") == "1",
        "filter_load_disabled_marker": marker_value(stdout, "A90WSTA154_SECCOMP_FILTER_LOAD") == "0",
        "hud_service_marker": marker_value(stdout, "A90WSTA154_SECCOMP_SERVICE") == "dpublic-hud",
        "hud_policy_service_marker": (
            marker_value(stdout, "A90WSTA154_SECCOMP_POLICY_SERVICE") == "dpublic-hud-intent"
        ),
        "hud_profile_marker": (
            marker_value(stdout, "A90WSTA154_SECCOMP_PROFILE")
            == "seccomp-dpublic-hud-intent-observed-v1"
        ),
        "hud_allowlist_count_nonzero": (marker_value(stdout, "A90WSTA154_SECCOMP_ALLOWLIST_COUNT") or "0") != "0",
        "launcher_exec_marker": "a90_service_launcher_decision=exec" in stdout,
        "fake_setpriv_called_after_markers": "fake_setpriv_args=--no-new-privs --reuid a90hud --regid a90hud" in stdout,
        "missing_map_returncode_65": missing_map.get("returncode") == 65,
        "missing_map_blocks_before_exec": (
            "a90_service_launcher_decision=blocked-seccomp-map-missing" in missing_stdout
            and "fake_setpriv_args=" not in missing_stdout
        ),
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    ts = utc_stamp()
    run_id = args.run_id or f"wsta155-seccomp-launcher-dry-run-rootfs-proof-{ts}"
    run_dir = resolve_path(args.run_dir or (DEFAULT_RUN_BASE / run_id))
    policy_path = resolve_path(args.wsta153_seccomp_policy_json)
    result: dict[str, Any] = {
        "scope": "WSTA155 host-only launcher seccomp dry-run rootfs proof",
        "started_utc": ts,
        "run_dir": rel(run_dir),
        "safety": safety_flags(),
        "checks": {
            "explicit_gate": bool(args.emit_seccomp_launcher_dry_run_proof),
            "private_run_dir": is_under(run_dir, PRIVATE_ROOT),
            "policy_json_private": is_under(policy_path, PRIVATE_ROOT),
            "policy_json_present": policy_path.is_file(),
        },
    }
    if not result["checks"]["explicit_gate"]:
        result["decision"] = "wsta155-blocked-explicit-gate-required"
        result["gate_decision"] = result["decision"]
        result["ended_utc"] = utc_stamp()
        return result
    if not result["checks"]["private_run_dir"]:
        result["decision"] = "wsta155-blocked-nonprivate-run-dir"
        result["gate_decision"] = result["decision"]
        result["ended_utc"] = utc_stamp()
        return result
    if not result["checks"]["policy_json_private"]:
        result["decision"] = "wsta155-blocked-policy-json-nonprivate"
        result["gate_decision"] = result["decision"]
        result["ended_utc"] = utc_stamp()
        return result
    if not result["checks"]["policy_json_present"]:
        result["decision"] = "wsta155-blocked-policy-json-missing"
        result["gate_decision"] = result["decision"]
        result["ended_utc"] = utc_stamp()
        run_dir.mkdir(parents=True, exist_ok=True)
        write_json(run_dir / SUMMARY_NAME, result)
        return result

    rootfs = run_dir / "rootfs"
    missing_rootfs = run_dir / "missing-map-rootfs"
    fakebin = run_dir / "fakebin"
    rootfs.mkdir(parents=True, exist_ok=True)
    missing_rootfs.mkdir(parents=True, exist_ok=True)
    make_fake_setpriv(fakebin)
    stage = stage_rootfs(rootfs, policy_path)
    missing_stage = stage_rootfs(missing_rootfs, policy_path)
    (missing_rootfs / wsta3.TARGET_SECCOMP_LAUNCHER_MAP).unlink()
    primary = run_launcher(rootfs, fakebin)
    missing_map = run_launcher(missing_rootfs, fakebin)
    proof_checks = validate_proof(primary, missing_map)
    result["stage"] = {
        "service_launcher": stage["service_launcher"],
        "seccomp_launcher_policy": stage["seccomp_launcher_policy"],
        "service_hardening_stage_marker": stage["service_hardening_stage_marker"],
        "missing_map_stage_seccomp": missing_stage["seccomp_launcher_policy"],
    }
    result["proof"] = {
        "service": "dpublic-hud",
        "stdout_artifact": rel(run_dir / STDOUT_NAME),
        "missing_map_stdout_artifact": rel(run_dir / MISSING_MAP_STDOUT_NAME),
        "primary_returncode": primary.get("returncode"),
        "missing_map_returncode": missing_map.get("returncode"),
        "filter_load_enabled": False,
        "seccomp_enforced": False,
    }
    result["proof_checks"] = proof_checks
    result["checks"].update({f"proof_{key}": value for key, value in proof_checks.items()})
    result["decision"] = PASS_DECISION if all(proof_checks.values()) else "wsta155-blocked-proof-invalid"
    result["gate_decision"] = "ok" if result["decision"] == PASS_DECISION else result["decision"]
    result["ended_utc"] = utc_stamp()
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / STDOUT_NAME).write_text(str(primary.get("stdout") or ""), encoding="utf-8")
    (run_dir / MISSING_MAP_STDOUT_NAME).write_text(str(missing_map.get("stdout") or ""), encoding="utf-8")
    write_json(run_dir / SUMMARY_NAME, result)
    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--wsta153-seccomp-policy-json", type=Path, default=DEFAULT_WSTA153_POLICY)
    parser.add_argument("--emit-seccomp-launcher-dry-run-proof", action="store_true")
    parser.add_argument("--print-full-json", action="store_true")
    return parser


def main_with_args(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        result = run(args)
    except Exception as exc:  # noqa: BLE001
        payload = {"decision": "wsta155-runner-error", "error": str(exc)}
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1
    payload = result if args.print_full_json else public_summary(result)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.get("decision") == PASS_DECISION else 2


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
