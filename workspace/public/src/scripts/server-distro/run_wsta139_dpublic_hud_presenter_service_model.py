#!/usr/bin/env python3
"""WSTA139 host-only durable native HUD presenter service model.

WSTA137 proved that the native/root-owned HUD presenter can validate a bounded
intent, present through KMS, and reject forbidden/stale intent data.  This unit
does not perform device action.  It turns that live proof into the next service
contract: a native/root presenter process that survives the Debian handoff while
Debian remains only the non-root intent producer.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import shlex
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import prepare_wsta3_sta_rootfs as wsta3  # noqa: E402
import run_wsta130_dpublic_hud_presenter_model as wsta130  # noqa: E402
import run_wsta137_dpublic_native_presenter_live_summary as wsta137  # noqa: E402


REPO_ROOT = wsta3.REPO_ROOT
PRIVATE_ROOT = REPO_ROOT / "workspace/private"
DEFAULT_RUN_BASE = wsta3.DEFAULT_RUN_BASE
PASS_DECISION = "wsta139-dpublic-hud-presenter-service-model-source-pass"
RESULT_NAME = "wsta139_dpublic_hud_presenter_service_model.json"

MODEL_SCHEMA = "a90-wsta139-dpublic-hud-presenter-service-model-v1"
MODEL_STATE = "DPUBLIC_HUD_DURABLE_NATIVE_PRESENTER_SERVICE_SOURCE_DEFINED"
SERVICE = "dpublic-hud"
SERVICE_NAME = "native-dpublic-hud-presenter"
CONTROL = "dpublic-hud-presenter-service"
PRESENTER = "dpublic-hud-presenter"
RUN_DIR = wsta130.RUN_DIR
INTENT_FILE = wsta130.INTENT_FILE
PRESENTER_PID_FILE = RUN_DIR + "/hud-presenter.pid"
PRESENTER_LOG_FILE = RUN_DIR + "/hud-presenter.log"
PRESENTER_STATUS_FILE = RUN_DIR + "/hud-presenter.status"
STALE_AFTER_MS = wsta130.STALE_AFTER_MS


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
    return json.loads(path.read_text(encoding="utf-8"))


def require_private_file(path: Path | None, label: str) -> tuple[Path | None, str | None]:
    if path is None:
        return None, f"wsta139-blocked-{label}-required"
    resolved = resolve_path(path)
    if not is_under(resolved, PRIVATE_ROOT):
        return None, f"wsta139-blocked-{label}-nonprivate"
    if not resolved.is_file():
        return None, f"wsta139-blocked-{label}-missing"
    return resolved, None


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
        "drm_open": False,
        "kms_setcrtc": False,
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def proof_checks_all_true(result: dict[str, Any], checks: dict[str, bool]) -> bool:
    supplied = result.get("checks") if isinstance(result.get("checks"), dict) else {}
    return bool(
        supplied
        and all(value is True for value in supplied.values())
        and all(value is True for value in checks.values())
    )


def precondition_summary(
    wsta130_result: dict[str, Any],
    wsta137_result: dict[str, Any],
) -> dict[str, Any]:
    wsta130_model = (
        wsta130_result.get("presenter_architecture_model")
        if isinstance(wsta130_result.get("presenter_architecture_model"), dict)
        else {}
    )
    wsta137_present = (
        wsta137_result.get("present_proof")
        if isinstance(wsta137_result.get("present_proof"), dict)
        else {}
    )
    wsta137_validate = (
        wsta137_result.get("validate_proof")
        if isinstance(wsta137_result.get("validate_proof"), dict)
        else {}
    )
    return {
        "wsta130_decision": wsta130_result.get("decision"),
        "wsta130_model_state": wsta130_model.get("state"),
        "wsta130_proof_run_dir": wsta130_result.get("run_dir"),
        "wsta137_decision": wsta137_result.get("decision"),
        "wsta137_proof_run_dir": wsta137_result.get("run_dir"),
        "wsta137_source_run_dir": wsta137_result.get("source_run_dir"),
        "wsta137_candidate": wsta137_result.get("candidate"),
        "wsta137_present_sequence": wsta137_present.get("sequence"),
        "wsta137_present_framebuffer": wsta137_present.get("framebuffer"),
        "wsta137_present_crtc": wsta137_present.get("crtc"),
        "wsta137_validate_sequence": wsta137_validate.get("sequence"),
    }


def start_command() -> list[str]:
    return [
        CONTROL,
        "start",
        "--intent",
        INTENT_FILE,
        "--pid-file",
        PRESENTER_PID_FILE,
        "--status-file",
        PRESENTER_STATUS_FILE,
        "--stale-after-ms",
        str(STALE_AFTER_MS),
    ]


def stop_command() -> list[str]:
    return [CONTROL, "stop", "--pid-file", PRESENTER_PID_FILE, "--release-drm"]


def status_command() -> list[str]:
    return [CONTROL, "status", "--pid-file", PRESENTER_PID_FILE, "--status-file", PRESENTER_STATUS_FILE]


def service_model(
    wsta130_result: dict[str, Any],
    wsta137_result: dict[str, Any],
) -> dict[str, Any]:
    intent_schema = wsta130.intent_schema()
    return {
        "schema": MODEL_SCHEMA,
        "state": MODEL_STATE,
        "service": SERVICE,
        "preconditions": precondition_summary(wsta130_result, wsta137_result),
        "native_presenter_service": {
            "name": SERVICE_NAME,
            "control": CONTROL,
            "presenter_binary": PRESENTER,
            "owner": "native-init",
            "privilege_model": "root-owned-kms-presenter",
            "process_model": "forked-native-child-survives-switch-root",
            "start_phase": "native-pre-switch-root",
            "survives_debian_handoff": True,
            "pid_file": PRESENTER_PID_FILE,
            "log_file": PRESENTER_LOG_FILE,
            "status_file": PRESENTER_STATUS_FILE,
            "start_command": start_command(),
            "stop_command": stop_command(),
            "status_command": status_command(),
            "bounded_shutdown": {
                "sigterm_ms": 1000,
                "sigkill_ms": 1000,
                "release_drm_on_stop": True,
                "remove_pid_file": True,
            },
        },
        "drm_ownership": {
            "device_node": wsta130.DRM_NODE,
            "sole_owner": SERVICE_NAME,
            "debian_opens_drm": False,
            "debian_direct_kms": False,
            "autohud_stop_before_start": True,
            "handoff_cleanup_policy": {
                "kill_legacy_init_drm_children": True,
                "preserve_durable_presenter_when_armed": True,
                "fail_if_unexpected_drm_holder": True,
            },
            "forbidden_power_writes": [
                "backlight",
                "pmic",
                "gpio",
                "regulator",
                "gdsc",
            ],
        },
        "handoff_contract": {
            "runtime_dir": RUN_DIR,
            "runtime_dir_owner": "root:a90hud",
            "runtime_dir_mode": "1770",
            "intent_file": INTENT_FILE,
            "intent_file_mode": "0640",
            "producer_user": wsta130.USER,
            "producer_uid": 3904,
            "producer_gid": 3904,
            "producer_role": "debian-nonroot-intent-writer-only",
            "producer_no_drm": True,
            "producer_no_network": True,
            "native_reads_intent_after_handoff": True,
        },
        "intent_watch": {
            "transport": "bounded-atomic-json-intent-file",
            "intent_schema": intent_schema["schema"],
            "max_bytes": intent_schema["max_bytes"],
            "stale_after_ms": STALE_AFTER_MS,
            "poll_ms": 100,
            "latest_sequence_wins": True,
            "reject_unknown_fields": True,
            "forbidden_fields": intent_schema["forbidden_fields"],
            "no_shell_expansion": True,
            "no_path_open_from_intent": True,
            "no_public_url_rendering": True,
        },
        "lifecycle": {
            "start": "native starts presenter before switch_root when operator arms D-public HUD",
            "handoff": "switch_root preserves durable presenter and skips Debian direct KMS",
            "debian_ready": "Debian firstboot writes fresh intent only",
            "update": "presenter drains latest valid sequence and ignores stale intent",
            "stop": "operator stop releases DRM, removes pid/status files, and allows native rollback",
            "crash": "status marks degraded; no automatic public exposure or restart loop without operator policy",
        },
        "proof_plan": [
            {
                "id": "pre_handoff_presenter_started",
                "evidence": "native status shows presenter pid and DRM fd before switch_root",
            },
            {
                "id": "post_handoff_same_presenter_alive",
                "evidence": "Debian PID1 is running and the same presenter pid still owns /dev/dri/card0",
            },
            {
                "id": "debian_has_no_drm_fd",
                "evidence": "a90hud intent producer and Debian services have no /dev/dri/card0 fd",
            },
            {
                "id": "fresh_intent_consumed_after_handoff",
                "evidence": "Debian writes a new sequence and presenter status reports that sequence presented",
            },
            {
                "id": "reject_paths_after_handoff",
                "evidence": "forbidden command and stale monotonic intent still reject",
            },
            {
                "id": "cleanup_releases_drm",
                "evidence": "stop removes presenter pid and no process holds /dev/dri/card0",
            },
        ],
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def validate_model(model: dict[str, Any]) -> dict[str, bool]:
    service = (
        model.get("native_presenter_service")
        if isinstance(model.get("native_presenter_service"), dict)
        else {}
    )
    drm = model.get("drm_ownership") if isinstance(model.get("drm_ownership"), dict) else {}
    cleanup = (
        drm.get("handoff_cleanup_policy")
        if isinstance(drm.get("handoff_cleanup_policy"), dict)
        else {}
    )
    handoff = model.get("handoff_contract") if isinstance(model.get("handoff_contract"), dict) else {}
    watch = model.get("intent_watch") if isinstance(model.get("intent_watch"), dict) else {}
    lifecycle = model.get("lifecycle") if isinstance(model.get("lifecycle"), dict) else {}
    proof_plan = model.get("proof_plan") if isinstance(model.get("proof_plan"), list) else []
    proof_ids = {
        entry.get("id")
        for entry in proof_plan
        if isinstance(entry, dict)
    }
    forbidden = watch.get("forbidden_fields") if isinstance(watch.get("forbidden_fields"), list) else []
    return {
        "schema_ok": model.get("schema") == MODEL_SCHEMA,
        "state_ok": model.get("state") == MODEL_STATE,
        "preconditions_embedded": isinstance(model.get("preconditions"), dict),
        "native_root_service_survives_handoff": (
            service.get("owner") == "native-init"
            and service.get("privilege_model") == "root-owned-kms-presenter"
            and service.get("process_model") == "forked-native-child-survives-switch-root"
            and service.get("start_phase") == "native-pre-switch-root"
            and service.get("survives_debian_handoff") is True
        ),
        "control_commands_defined": (
            service.get("start_command") == start_command()
            and service.get("stop_command") == stop_command()
            and service.get("status_command") == status_command()
        ),
        "bounded_shutdown_releases_drm": (
            isinstance(service.get("bounded_shutdown"), dict)
            and service["bounded_shutdown"].get("release_drm_on_stop") is True
            and service["bounded_shutdown"].get("sigterm_ms") <= 1000
            and service["bounded_shutdown"].get("sigkill_ms") <= 1000
        ),
        "sole_drm_owner_policy": (
            drm.get("device_node") == wsta130.DRM_NODE
            and drm.get("sole_owner") == SERVICE_NAME
            and drm.get("debian_opens_drm") is False
            and drm.get("debian_direct_kms") is False
        ),
        "handoff_cleanup_preserves_presenter": (
            cleanup.get("kill_legacy_init_drm_children") is True
            and cleanup.get("preserve_durable_presenter_when_armed") is True
            and cleanup.get("fail_if_unexpected_drm_holder") is True
        ),
        "no_power_writes": all(
            name in (drm.get("forbidden_power_writes") or [])
            for name in ("backlight", "pmic", "gpio", "regulator", "gdsc")
        ),
        "debian_intent_only_contract": (
            handoff.get("runtime_dir") == RUN_DIR
            and handoff.get("runtime_dir_mode") == "1770"
            and handoff.get("intent_file") == INTENT_FILE
            and handoff.get("producer_user") == wsta130.USER
            and handoff.get("producer_no_drm") is True
            and handoff.get("producer_no_network") is True
            and handoff.get("native_reads_intent_after_handoff") is True
        ),
        "intent_watch_fail_closed": (
            watch.get("transport") == "bounded-atomic-json-intent-file"
            and watch.get("intent_schema") == "a90-dpublic-hud-intent-v1"
            and int(watch.get("max_bytes") or 0) <= wsta130.MAX_INTENT_BYTES
            and int(watch.get("stale_after_ms") or 0) <= STALE_AFTER_MS
            and watch.get("latest_sequence_wins") is True
            and watch.get("reject_unknown_fields") is True
            and watch.get("no_shell_expansion") is True
            and watch.get("no_path_open_from_intent") is True
            and watch.get("no_public_url_rendering") is True
            and all(name in forbidden for name in ("command", "path", "url", "ssid", "psk", "token", "secret"))
        ),
        "lifecycle_covers_start_handoff_update_stop": all(
            key in lifecycle for key in ("start", "handoff", "debian_ready", "update", "stop", "crash")
        ),
        "proof_plan_covers_handoff_drm_intent_cleanup": all(
            key in proof_ids
            for key in (
                "pre_handoff_presenter_started",
                "post_handoff_same_presenter_alive",
                "debian_has_no_drm_fd",
                "fresh_intent_consumed_after_handoff",
                "reject_paths_after_handoff",
                "cleanup_releases_drm",
            )
        ),
        "no_public_url_logged": model.get("public_url_value_logged") is False,
        "no_secret_values_logged": model.get("secret_values_logged") == 0,
    }


def model_passes(checks: dict[str, bool]) -> bool:
    return all(value is True for value in checks.values())


def contract_plan_shell() -> str:
    start = " ".join(shlex.quote(item) for item in start_command())
    stop = " ".join(shlex.quote(item) for item in stop_command())
    return f"""
set -eu
echo A90WSTA139_DURABLE_PRESENTER_MODEL_BEGIN
echo A90WSTA139_SERVICE={shlex.quote(SERVICE_NAME)}
echo A90WSTA139_START={shlex.quote(start)}
echo A90WSTA139_STOP={shlex.quote(stop)}
echo A90WSTA139_SURVIVES_HANDOFF=1
echo A90WSTA139_DEBIAN_DRM_OPEN=0
echo A90WSTA139_INTENT_FILE={shlex.quote(INTENT_FILE)}
echo A90WSTA139_PROOF_PLAN=pre-handoff,post-handoff,no-debian-drm,fresh-intent,reject,cleanup
echo A90WSTA139_DURABLE_PRESENTER_MODEL_DONE
""".strip()


def template() -> dict[str, Any]:
    return {
        "scope": "WSTA139 host-only D-public durable native HUD presenter service model",
        "default_mode": "host-only-source-model",
        "command": [
            "python3",
            rel(Path(__file__).resolve()),
            "--emit-service-model",
            "--wsta130-hud-presenter-model-json",
            "workspace/private/runs/server-distro/<wsta130-run>/wsta130_dpublic_hud_presenter_model.json",
            "--wsta137-hud-presenter-live-proof-json",
            "workspace/private/runs/server-distro/<wsta137-run>/wsta137_dpublic_native_presenter_live.json",
        ],
        "device_action": False,
        "public_tunnel": False,
        "drm_open": False,
        "kms_setcrtc": False,
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    ts = utc_stamp()
    run_id = args.run_id or f"wsta139-dpublic-hud-presenter-service-model-{ts}"
    run_dir = resolve_path(args.run_dir or (DEFAULT_RUN_BASE / run_id))
    result: dict[str, Any] = {
        "scope": "WSTA139 host-only D-public durable native HUD presenter service model",
        "started_utc": ts,
        "run_dir": rel(run_dir),
        "decision": "wsta139-blocked",
        "gate_decision": "not-run",
        "safety": safety(),
    }
    if not is_under(run_dir, PRIVATE_ROOT):
        result["decision"] = "wsta139-blocked-nonprivate-run-dir"
        result["gate_decision"] = result["decision"]
        result["ended_utc"] = utc_stamp()
        return result
    run_dir.mkdir(parents=True, exist_ok=True)
    out_json = run_dir / RESULT_NAME

    if not args.emit_service_model:
        result["decision"] = "wsta139-blocked-emit-service-model-required"
        result["gate_decision"] = result["decision"]
        result["ended_utc"] = utc_stamp()
        write_json(out_json, result)
        return result

    wsta130_path, wsta130_error = require_private_file(
        args.wsta130_hud_presenter_model_json,
        "wsta130-hud-presenter-model",
    )
    if wsta130_error or wsta130_path is None:
        result["decision"] = wsta130_error or "wsta139-blocked-wsta130-hud-presenter-model"
        result["gate_decision"] = result["decision"]
        result["ended_utc"] = utc_stamp()
        write_json(out_json, result)
        return result

    wsta137_path, wsta137_error = require_private_file(
        args.wsta137_hud_presenter_live_proof_json,
        "wsta137-hud-presenter-live-proof",
    )
    if wsta137_error or wsta137_path is None:
        result["decision"] = wsta137_error or "wsta139-blocked-wsta137-hud-presenter-live-proof"
        result["gate_decision"] = result["decision"]
        result["ended_utc"] = utc_stamp()
        write_json(out_json, result)
        return result

    wsta130_result = load_json(wsta130_path)
    wsta137_result = load_json(wsta137_path)
    wsta130_model = (
        wsta130_result.get("presenter_architecture_model")
        if isinstance(wsta130_result.get("presenter_architecture_model"), dict)
        else {}
    )
    if (
        wsta130_result.get("decision") != wsta130.PASS_DECISION
        or not proof_checks_all_true(wsta130_result, wsta130.validate_model(wsta130_model))
    ):
        result["decision"] = "wsta139-blocked-wsta130-model-not-pass"
        result["gate_decision"] = result["decision"]
        result["ended_utc"] = utc_stamp()
        write_json(out_json, result)
        return result
    if (
        wsta137_result.get("decision") != wsta137.PASS_DECISION
        or not proof_checks_all_true(wsta137_result, wsta137.validate_proof(wsta137_result))
    ):
        result["decision"] = "wsta139-blocked-wsta137-live-proof-not-pass"
        result["gate_decision"] = result["decision"]
        result["ended_utc"] = utc_stamp()
        write_json(out_json, result)
        return result

    model = service_model(wsta130_result, wsta137_result)
    checks = validate_model(model)
    result["service_model"] = model
    result["contract_plan_shell"] = contract_plan_shell()
    result["checks"] = checks
    if not model_passes(checks):
        result["decision"] = "wsta139-blocked-model-validation"
        result["gate_decision"] = result["decision"]
        result["ended_utc"] = utc_stamp()
        write_json(out_json, result)
        return result

    result["decision"] = PASS_DECISION
    result["gate_decision"] = "ok"
    result["ended_utc"] = utc_stamp()
    write_json(out_json, result)
    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--emit-service-model", action="store_true")
    parser.add_argument("--wsta130-hud-presenter-model-json", type=Path)
    parser.add_argument("--wsta137-hud-presenter-live-proof-json", type=Path)
    parser.add_argument("--print-template", action="store_true")
    return parser


def main_with_args(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    if args.print_template:
        print(json.dumps(template(), indent=2, sort_keys=True))
        return 0
    try:
        result = run(args)
    except Exception as exc:  # noqa: BLE001
        payload = {"decision": "wsta139-runner-error", "error": str(exc)}
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("decision") == PASS_DECISION else 2


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
