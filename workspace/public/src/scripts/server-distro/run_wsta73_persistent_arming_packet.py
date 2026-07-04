#!/usr/bin/env python3
"""WSTA73 host-only persistent arming packet.

WSTA72 builds the private prepare-to-arm run tree.  WSTA73 turns that run into
a compact operator arming packet, but first reruns WSTA71 so a stale
prepare-to-arm artifact cannot be treated as fresh.

The packet contains the WSTA58 command template, required placeholder
replacements, abort conditions, and cleanup expectations.  It never executes the
WSTA58 live gate.  It performs no device action, native reboot, Wi-Fi
association, DHCP, public tunnel, public smoke, userdata action, switch-root, or
flash.
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

import run_wsta71_persistent_launch_readiness_audit as wsta71  # noqa: E402
import run_wsta72_persistent_prepare_to_arm as wsta72  # noqa: E402


REPO_ROOT = wsta72.REPO_ROOT
PRIVATE_ROOT = wsta72.PRIVATE_ROOT
DEFAULT_RUN_BASE = wsta72.DEFAULT_RUN_BASE
PASS_DECISION = "wsta73-persistent-arming-packet-pass"


def rel(path: Path) -> str:
    return wsta72.rel(path)


def utc_now() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc)


def utc_stamp(value: _dt.datetime | None = None) -> str:
    return (value or utc_now()).strftime("%Y%m%dT%H%M%SZ")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def is_under(path: Path, root: Path) -> bool:
    return wsta72.is_under(path, root)


def safety_flags() -> dict[str, Any]:
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


def template() -> dict[str, Any]:
    return {
        "scope": "WSTA73 host-only persistent arming packet",
        "default_mode": "host-only-revalidate-and-render-packet",
        "input": "workspace/private/runs/server-distro/<wsta72-run>/wsta72_prepare_to_arm.json",
        "command": [
            "python3",
            rel(Path(__file__).resolve()),
            "--wsta72-prepare-to-arm-json",
            "workspace/private/runs/server-distro/<wsta72-run>/wsta72_prepare_to_arm.json",
        ],
        "live_execution": "not-run-by-wsta73",
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def public_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": result.get("decision"),
        "run_dir": result.get("run_dir"),
        "gate_decision": result.get("gate_decision"),
        "arming_packet": result.get("arming_packet", {}),
        "checks": result.get("checks", {}),
        "safety": result.get("safety", {}),
    }


def redaction_findings(payload: Any) -> list[str]:
    return wsta72.redaction_findings(payload)


def require_private_path(value: Any, label: str) -> tuple[Path | None, str | None]:
    if isinstance(value, Path):
        candidate = value
    elif isinstance(value, str) and value:
        candidate = Path(value)
    else:
        return None, f"wsta73-blocked-{label}-missing"
    path = resolve_path(candidate)
    if not is_under(path, PRIVATE_ROOT):
        return None, f"wsta73-blocked-{label}-nonprivate"
    if not path.exists():
        return None, f"wsta73-blocked-{label}-missing"
    return path, None


def validate_prepare_to_arm(path: Path) -> tuple[bool, str, dict[str, Any]]:
    try:
        payload = load_json(path)
    except Exception as exc:  # noqa: BLE001
        return False, "wsta73-blocked-prepare-to-arm-unreadable", {"error": str(exc)}
    if payload.get("decision") != wsta72.PASS_DECISION:
        return False, "wsta73-blocked-prepare-to-arm-not-pass", {"decision": payload.get("decision")}
    pipeline = payload.get("pipeline")
    if not isinstance(pipeline, dict):
        return False, "wsta73-blocked-pipeline-missing", {}
    if pipeline.get("state") != "READY_TO_ARM_DEFAULT_OFF":
        return False, "wsta73-blocked-pipeline-not-ready", {"state": pipeline.get("state")}
    if pipeline.get("default_public_off") is not True:
        return False, "wsta73-blocked-default-public-off-missing", {}
    if pipeline.get("live_execution_requested") is not False:
        return False, "wsta73-blocked-live-execution-requested", {}
    if pipeline.get("public_url_value_logged") is not False:
        return False, "wsta73-blocked-public-url-logged", {}
    if pipeline.get("secret_values_logged") not in (0, "0", None):
        return False, "wsta73-blocked-secret-values-logged", {}
    launch_path, path_error = require_private_path(pipeline.get("wsta70_launch_manifest"), "launch-manifest")
    if path_error or launch_path is None:
        return False, path_error or "wsta73-blocked-launch-manifest", {}
    readiness_path, path_error = require_private_path(pipeline.get("wsta71_launch_readiness"), "launch-readiness")
    if path_error or readiness_path is None:
        return False, path_error or "wsta73-blocked-launch-readiness", {}
    return True, "ok", {
        "payload": payload,
        "pipeline": pipeline,
        "launch_path": launch_path,
        "readiness_path": readiness_path,
    }


def wsta71_args(run_dir: Path,
                launch_path: Path,
                min_remaining: int | None,
                now_utc: str | None) -> argparse.Namespace:
    argv = [
        "--run-dir",
        str(run_dir),
        "--wsta70-launch-manifest-json",
        str(launch_path),
    ]
    if min_remaining is not None:
        argv.extend(["--min-initial-seconds-remaining", str(min_remaining)])
    if now_utc:
        argv.extend(["--now-utc", now_utc])
    return wsta71.build_arg_parser().parse_args(argv)


def min_remaining_from_args(args: argparse.Namespace, pipeline: dict[str, Any]) -> int | None:
    if args.min_initial_seconds_remaining is not None:
        return int(args.min_initial_seconds_remaining)
    value = pipeline.get("min_initial_seconds_remaining")
    if value is None:
        return None
    return int(value)


def build_packet(prepare_path: Path,
                 pipeline: dict[str, Any],
                 recheck_result: dict[str, Any],
                 recheck_path: Path,
                 packet_json: Path,
                 packet_md: Path) -> dict[str, Any]:
    readiness = recheck_result.get("readiness") or {}
    command = readiness.get("live_command_template") or []
    return {
        "state": "ARMING_PACKET_READY_DEFAULT_OFF",
        "wsta72_prepare_to_arm": rel(prepare_path),
        "wsta71_recheck_result": rel(recheck_path),
        "source_wsta71_launch_readiness": pipeline.get("wsta71_launch_readiness"),
        "selected_wsta64_result": readiness.get("selected_wsta64_result"),
        "selected_wsta63_result": readiness.get("selected_wsta63_result"),
        "wsta65_session_state": readiness.get("wsta65_session_state"),
        "ready_for_live": bool(readiness.get("ready_for_live")),
        "initial_seconds_remaining": readiness.get("initial_seconds_remaining"),
        "min_initial_seconds_remaining": readiness.get("min_initial_seconds_remaining"),
        "wsta58_live_command_template": command,
        "operator_required_replacements": [
            "<native-confirm-token>",
            "<public-confirm-token>",
        ],
        "operator_acknowledgements_required": [
            "--allow-operator-live",
            "--allow-native-reboot",
            "--allow-public-live",
            "--ack-credentialed-wifi",
            "--ack-public-exposure",
            "--force-ttl-expiry-proof",
            "--force-manual-stop-proof",
        ],
        "abort_conditions": [
            "wsta71_recheck_not_pass",
            "initial_seconds_remaining_below_minimum",
            "command_template_missing_placeholders",
            "operator_does_not_intend_public_exposure",
            "operator_does_not_have_current_private_confirm_tokens",
        ],
        "cleanup_expectations": [
            "WSTA58 runs two WSTA55 short public proofs",
            "WSTA58 requires final manual-stop cleanup",
            "WSTA58 must return public state to PUBLIC_OFF",
            "WSTA48 redaction aggregate must pass",
        ],
        "json_path": rel(packet_json),
        "markdown_path": rel(packet_md),
        "default_public_off": True,
        "live_execution_requested": False,
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def markdown(packet: dict[str, Any]) -> str:
    command = " ".join(str(part) for part in packet.get("wsta58_live_command_template") or [])
    lines = [
        "# WSTA Persistent Arming Packet",
        "",
        f"- State: `{packet.get('state')}`",
        f"- WSTA72 prepare-to-arm: `{packet.get('wsta72_prepare_to_arm')}`",
        f"- WSTA71 recheck: `{packet.get('wsta71_recheck_result')}`",
        f"- WSTA65 state: `{packet.get('wsta65_session_state')}`",
        f"- Initial seconds remaining: `{packet.get('initial_seconds_remaining')}`",
        "- Live execution requested: `false`",
        "- Default public state: `PUBLIC_OFF`",
        "",
        "## Operator Replacements",
        "",
    ]
    for item in packet.get("operator_required_replacements", []):
        lines.append(f"- `{item}`")
    lines.extend([
        "",
        "## Required Acknowledgements",
        "",
    ])
    for item in packet.get("operator_acknowledgements_required", []):
        lines.append(f"- `{item}`")
    lines.extend([
        "",
        "## Abort Conditions",
        "",
    ])
    for item in packet.get("abort_conditions", []):
        lines.append(f"- `{item}`")
    lines.extend([
        "",
        "## Cleanup Expectations",
        "",
    ])
    for item in packet.get("cleanup_expectations", []):
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## WSTA58 Command Template",
        "",
        "```text",
        command,
        "```",
        "",
        "This packet is not live execution. Replace placeholders only when explicitly running WSTA58.",
        "",
    ])
    return "\n".join(lines)


def run(args: argparse.Namespace) -> dict[str, Any]:
    started = utc_now()
    ts = utc_stamp(started)
    run_id = args.run_id or f"wsta73-persistent-arming-packet-{ts}"
    run_dir = args.run_dir or (DEFAULT_RUN_BASE / run_id)
    run_dir = resolve_path(run_dir)
    result: dict[str, Any] = {
        "scope": "WSTA73 host-only persistent arming packet",
        "started_utc": ts,
        "run_dir": rel(run_dir),
        "decision": "wsta73-blocked",
        "gate_decision": "not-run",
        "safety": safety_flags(),
    }
    if not is_under(run_dir, PRIVATE_ROOT):
        result["decision"] = "wsta73-blocked-nonprivate-run-dir"
        result["gate_decision"] = result["decision"]
        result["ended_utc"] = utc_stamp()
        return result
    run_dir.mkdir(parents=True, exist_ok=True)
    out_json = run_dir / "wsta73_arming_packet.json"
    out_md = run_dir / "wsta73_arming_packet.md"

    if args.wsta72_prepare_to_arm_json is None:
        result["decision"] = "wsta73-blocked-prepare-to-arm-required"
        result["gate_decision"] = result["decision"]
        result["ended_utc"] = utc_stamp()
        write_json(out_json, result)
        return result
    prepare_path, path_error = require_private_path(args.wsta72_prepare_to_arm_json, "prepare-to-arm")
    if path_error or prepare_path is None:
        result["decision"] = path_error or "wsta73-blocked-prepare-to-arm"
        result["gate_decision"] = result["decision"]
        result["ended_utc"] = utc_stamp()
        write_json(out_json, result)
        return result
    valid, decision, detail = validate_prepare_to_arm(prepare_path)
    if not valid:
        result["decision"] = decision
        result["gate_decision"] = decision
        result["gate_detail"] = detail
        result["ended_utc"] = utc_stamp()
        write_json(out_json, result)
        return result

    pipeline = detail["pipeline"]
    launch_path = detail["launch_path"]
    recheck_dir = run_dir / "wsta71-recheck"
    recheck = wsta71.run(wsta71_args(
        recheck_dir,
        launch_path,
        min_remaining_from_args(args, pipeline),
        args.now_utc,
    ))
    recheck_path = recheck_dir / "wsta71_launch_readiness.json"
    readiness = recheck.get("readiness") or {}
    if (
        recheck.get("decision") != wsta71.PASS_DECISION
        or readiness.get("state") != "READY_TO_ARM_DEFAULT_OFF"
        or readiness.get("ready_for_live") is not True
    ):
        result["decision"] = "wsta73-blocked-wsta71-recheck"
        result["gate_decision"] = result["decision"]
        result["gate_detail"] = {
            "wsta71_decision": recheck.get("decision"),
            "state": readiness.get("state"),
            "session_state": readiness.get("wsta65_session_state"),
            "wsta71_gate_detail": recheck.get("gate_detail", {}),
            "wsta71_result": rel(recheck_path),
        }
        result["ended_utc"] = utc_stamp()
        write_json(out_json, result)
        return result

    packet = build_packet(prepare_path, pipeline, recheck, recheck_path, out_json, out_md)
    result.update({
        "decision": PASS_DECISION,
        "gate_decision": "ok",
        "arming_packet": packet,
        "checks": {
            "prepare_to_arm_private": True,
            "wsta71_recheck_pass": True,
            "command_template_placeholders_only": True,
            "default_public_off": True,
            "live_execution_requested": False,
            "public_url_value_logged": False,
            "secret_values_logged": 0,
        },
    })
    md_text = markdown(packet)
    findings = redaction_findings(public_summary(result))
    md_findings = redaction_findings({"markdown": md_text})
    if findings or md_findings:
        result["decision"] = "wsta73-blocked-redaction-finding"
        result["gate_decision"] = result["decision"]
        result["gate_detail"] = {"findings": sorted(set(findings + md_findings))}
        result["ended_utc"] = utc_stamp()
        write_json(out_json, result)
        return result

    result["ended_utc"] = utc_stamp()
    write_json(out_json, result)
    write_text(out_md, md_text)
    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--wsta72-prepare-to-arm-json", type=Path)
    parser.add_argument("--min-initial-seconds-remaining", type=int)
    parser.add_argument("--now-utc")
    parser.add_argument("--print-template", action="store_true")
    parser.add_argument("--print-full-json", action="store_true")
    return parser


def main_with_args(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    if args.print_template:
        print(json.dumps(template(), indent=2, sort_keys=True))
        return 0
    try:
        result = run(args)
    except Exception as exc:  # noqa: BLE001
        payload = {"decision": "wsta73-runner-error", "error": str(exc)}
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1
    payload = result if args.print_full_json else public_summary(result)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.get("decision") == PASS_DECISION else 2


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
