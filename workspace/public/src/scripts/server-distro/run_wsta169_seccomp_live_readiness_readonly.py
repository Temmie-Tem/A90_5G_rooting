#!/usr/bin/env python3
"""WSTA169 read-only readiness check for the seccomp live observation.

This runner verifies host/device readiness for the WSTA168 live command without
executing that command.  It performs only read-only bridge/status/selftest
queries and validates the WSTA168 command artifact remains ready-not-executed.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REVAL_DIR = SCRIPT_DIR.parent / "revalidation"
for _path in (SCRIPT_DIR, REVAL_DIR):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import prepare_wsta3_sta_rootfs as wsta3  # noqa: E402
import run_wsta160_seccomp_full_rootfs_chroot_dry_run as wsta160  # noqa: E402


REPO_ROOT = wsta3.REPO_ROOT
PRIVATE_ROOT = REPO_ROOT / "workspace/private"
DEFAULT_RUN_BASE = wsta3.DEFAULT_RUN_BASE
DEFAULT_WSTA168_COMMAND_JSON = (
    DEFAULT_RUN_BASE
    / "wsta168-seccomp-live-observation-preflight-20260705T1358KST"
    / "wsta168_live_command.json"
)
DEFAULT_WSTA168_COMMAND_SH = (
    DEFAULT_RUN_BASE
    / "wsta168-seccomp-live-observation-preflight-20260705T1358KST"
    / "wsta168_live_command.sh"
)
PASS_DECISION = "wsta169-seccomp-live-readiness-readonly-pass"
SUMMARY_NAME = "wsta169_result.json"
BRIDGE = REVAL_DIR / "a90_bridge.py"
A90CTL = REVAL_DIR / "a90ctl.py"


def rel(path: Path) -> str:
    return wsta3.rel(path)


def utc_stamp() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def write_json(path: Path, payload: Any) -> None:
    wsta3.write_json(path, payload)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fp:
        payload = json.load(fp)
    if not isinstance(payload, dict):
        raise ValueError(f"expected object JSON: {path}")
    return payload


def safety_flags() -> dict[str, Any]:
    return {
        "device_action": "read-only-status-only",
        "boot_flash": False,
        "native_reboot": False,
        "wifi_connect": False,
        "dhcp": False,
        "public_tunnel": False,
        "public_smoke": False,
        "packet_filter_mutation": False,
        "userdata_touch": False,
        "switch_root": False,
        "live_command_executed": False,
        "seccomp_filter_loaded": False,
        "seccomp_enforced": False,
        "correct_wsta161_token_supplied": False,
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def public_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": result.get("decision"),
        "run_dir": result.get("run_dir"),
        "gate_decision": result.get("gate_decision"),
        "readiness": result.get("readiness", {}),
        "checks": result.get("checks", {}),
        "safety": result.get("safety", {}),
    }


def run_host(command: list[str], *, timeout: float) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        timeout=timeout,
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def run_bridge_status(timeout: float) -> dict[str, Any]:
    return run_host([sys.executable, str(BRIDGE), "status", "--json"], timeout=timeout)


def run_a90ctl(command: str, timeout: float) -> dict[str, Any]:
    return run_host([sys.executable, str(A90CTL), command], timeout=timeout)


def parse_bridge(record: dict[str, Any]) -> dict[str, Any]:
    try:
        payload = json.loads(str(record.get("stdout") or "{}"))
    except json.JSONDecodeError:
        payload = {}
    return {
        "bridge_status_json": bool(payload),
        "bridge_process_running": payload.get("bridge_process") == "running",
        "port_listening": payload.get("port_listening") is True,
        "probe_connected": payload.get("bridge_probe") == "connected-no-immediate-error",
        "selected_device_present": bool(payload.get("selected_device")),
        "selected_realpath_present": bool(payload.get("selected_realpath")),
        "raw": payload,
    }


def parse_a90ctl_text(text: str) -> dict[str, Any]:
    return {
        "selftest_fail_zero": "fail=0" in text,
        "transport_ncm_ready": "transport.ncm=ready" in text,
        "storage_sd_mounted": "storage: sd present=yes mounted=yes" in text,
        "runtime_sd": "runtime: backend=sd" in text,
        "version_present": "A90 Linux init" in text,
        "build": (re.search(r"build=([^\s]+)", text) or [None, None])[1],
    }


def validate_command_artifacts(command_json: Path, command_sh: Path) -> dict[str, bool]:
    payload = load_json(command_json) if command_json.is_file() else {}
    script_text = command_sh.read_text(encoding="utf-8") if command_sh.is_file() else ""
    command = payload.get("command", [])
    return {
        "command_json_present": command_json.is_file(),
        "command_sh_present": command_sh.is_file(),
        "schema_ok": payload.get("schema") == "a90-wsta168-seccomp-live-observation-command-v1",
        "ready_not_executed": payload.get("state") == "READY_TO_RUN_NOT_EXECUTED",
        "payload_not_executed": payload.get("executed") is False,
        "command_targets_wsta167": (
            "workspace/public/src/scripts/server-distro/run_wsta167_seccomp_live_observation.py" in command
        ),
        "script_targets_wsta167": "run_wsta167_seccomp_live_observation.py" in script_text,
        "all_ack_flags_present": all(
            flag in command and flag in script_text for flag in payload.get("required_ack_flags", [])
        ),
        "correct_token_absent": "WSTA161-EXPLICIT-ALLOW-SECCOMP-LOAD" not in script_text,
        "expected_no_load": payload.get("expected_outcome", {}).get("seccomp_filter_loaded") is False,
        "expected_no_enforce": payload.get("expected_outcome", {}).get("seccomp_enforced") is False,
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    ts = utc_stamp()
    run_id = args.run_id or f"wsta169-seccomp-live-readiness-readonly-{ts}"
    run_dir = resolve_path(args.run_dir or (DEFAULT_RUN_BASE / run_id))
    command_json = resolve_path(args.wsta168_command_json)
    command_sh = resolve_path(args.wsta168_command_sh)
    result: dict[str, Any] = {
        "scope": "WSTA169 read-only seccomp live readiness",
        "started_utc": ts,
        "run_dir": rel(run_dir),
        "safety": safety_flags(),
        "checks": {
            "explicit_gate": bool(args.emit_seccomp_live_readiness_readonly),
            "private_run_dir": wsta160.is_under(run_dir, PRIVATE_ROOT),
            "command_json_private": wsta160.is_under(command_json, PRIVATE_ROOT),
            "command_sh_private": wsta160.is_under(command_sh, PRIVATE_ROOT),
        },
    }
    for key, decision in (
        ("explicit_gate", "wsta169-blocked-explicit-gate-required"),
        ("private_run_dir", "wsta169-blocked-nonprivate-run-dir"),
        ("command_json_private", "wsta169-blocked-command-json-nonprivate"),
        ("command_sh_private", "wsta169-blocked-command-sh-nonprivate"),
    ):
        if not result["checks"][key]:
            result["decision"] = decision
            result["gate_decision"] = decision
            result["ended_utc"] = utc_stamp()
            return result

    command_checks = validate_command_artifacts(command_json, command_sh)
    bridge_record = run_bridge_status(args.timeout)
    version_record = run_a90ctl("version", args.timeout)
    status_record = run_a90ctl("status", args.timeout)
    selftest_record = run_a90ctl("selftest", args.timeout)
    bridge_parse = parse_bridge(bridge_record)
    version_parse = parse_a90ctl_text(str(version_record.get("stdout") or ""))
    status_parse = parse_a90ctl_text(str(status_record.get("stdout") or ""))
    selftest_parse = parse_a90ctl_text(str(selftest_record.get("stdout") or ""))
    readiness = {
        "bridge": bridge_parse,
        "version": version_parse,
        "status": status_parse,
        "selftest": selftest_parse,
    }
    result.update({
        "wsta168_command_json": rel(command_json),
        "wsta168_command_sh": rel(command_sh),
        "command_checks": command_checks,
        "bridge_status": bridge_record,
        "version": version_record,
        "status": status_record,
        "selftest": selftest_record,
        "readiness": readiness,
    })
    checks = {
        "command_ready": all(command_checks.values()),
        "bridge_ready": (
            bridge_record.get("returncode") == 0
            and bridge_parse["bridge_process_running"]
            and bridge_parse["port_listening"]
            and bridge_parse["probe_connected"]
            and bridge_parse["selected_device_present"]
            and bridge_parse["selected_realpath_present"]
        ),
        "version_ok": version_record.get("returncode") == 0 and version_parse["version_present"],
        "status_ok": (
            status_record.get("returncode") == 0
            and status_parse["selftest_fail_zero"]
            and status_parse["transport_ncm_ready"]
            and status_parse["storage_sd_mounted"]
            and status_parse["runtime_sd"]
        ),
        "selftest_fail_zero": selftest_record.get("returncode") == 0 and selftest_parse["selftest_fail_zero"],
    }
    result["checks"].update(checks)
    all_ok = all(checks.values())
    result["decision"] = PASS_DECISION if all_ok else "wsta169-blocked-readiness-invalid"
    result["gate_decision"] = "ok" if result["decision"] == PASS_DECISION else result["decision"]
    result["ended_utc"] = utc_stamp()
    run_dir.mkdir(parents=True, exist_ok=True)
    write_json(run_dir / SUMMARY_NAME, result)
    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--wsta168-command-json", type=Path, default=DEFAULT_WSTA168_COMMAND_JSON)
    parser.add_argument("--wsta168-command-sh", type=Path, default=DEFAULT_WSTA168_COMMAND_SH)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--emit-seccomp-live-readiness-readonly", action="store_true")
    parser.add_argument("--print-full-json", action="store_true")
    return parser


def main_with_args(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        result = run(args)
    except Exception as exc:  # noqa: BLE001
        payload = {"decision": "wsta169-runner-error", "error": str(exc)}
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1
    payload = result if args.print_full_json else public_summary(result)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.get("decision") == PASS_DECISION else 2


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
