#!/usr/bin/env python3
"""V2432 exact-gated read-only Android/Magisk access probe.

This unit classifies the V2430 `/data/adb/modules` permission failure without
writing under `/data/adb`: boot pinned Android, verify Magisk root, run read-only
Magisk/path/namespace probes through normal shell, `su -c`, and `su -mm -c`,
then roll back to V2321.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import native_audio_acdb_android_measurement_planner_v2396 as v2396
import native_audio_android_route_delta_handoff_v2365 as route


RUN_ID = "V2432"
BUILD_TAG = "v2432-audio-magisk-readonly-probe"
ROOT = v2396.ROOT
DEFAULT_OUT_BASE = ROOT / "workspace/private/runs/audio"
APPROVAL_PHRASE = (
    "AUD-5H-magisk-readonly-probe go: rollbackable Android Magisk access probe, "
    "read-only /data/adb namespace inspection only, no module install, no playback, "
    "rollback to V2321"
)

READ_ONLY_PROBE = r'''
echo A90_MAGISK_PROBE_BEGIN
echo -- identity
id 2>&1 || true
id -Z 2>&1 || true
echo -- magisk
command -v magisk 2>&1 || true
magisk -c 2>&1 || true
magisk -v 2>&1 || true
magisk --path 2>&1 || true
magisk --list 2>&1 || true
echo -- data-adb
ls -ldZ /data /data/adb /data/adb/modules /data/adb/modules_update /data/adb/service.d 2>&1 || true
echo -- stat
stat /data/adb /data/adb/modules /data/adb/modules_update /data/adb/service.d 2>&1 || true
echo -- mounts
mount 2>&1 | grep -E ' /data|/data/adb|magisk' || true
echo -- mountinfo
cat /proc/self/mountinfo 2>&1 | grep -E ' /data |/data/adb|magisk' || true
echo A90_MAGISK_PROBE_END
'''


def rel(path: Path | str) -> str:
    return v2396.rel(path)


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def default_live_out_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return DEFAULT_OUT_BASE / f"{RUN_ID.lower()}-magisk-readonly-probe-{stamp}"


def decision_slug() -> str:
    return f"{RUN_ID.lower()}-magisk-readonly-probe"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def route_args(args: argparse.Namespace) -> argparse.Namespace:
    return v2396.android_args(args)


def ensure_live_approval(args: argparse.Namespace) -> None:
    if args.approval != APPROVAL_PHRASE:
        raise RuntimeError("exact AUD-5H Magisk read-only probe approval phrase is required for --run-live")


def adb_shell(args: argparse.Namespace, command: str) -> list[str]:
    return v2396.adb_base(args) + ["shell", command]


def adb_su_shell(args: argparse.Namespace, command: str) -> list[str]:
    return adb_shell(args, f"su -c {shlex.quote(command)}")


def adb_su_mm_shell(args: argparse.Namespace, command: str) -> list[str]:
    return adb_shell(args, f"su -mm -c {shlex.quote(command)}")


def probe_commands(args: argparse.Namespace) -> list[dict[str, Any]]:
    return [
        {
            "name": "probe-shell-readonly",
            "mode": "adb-shell",
            "command": adb_shell(args, READ_ONLY_PROBE),
        },
        {
            "name": "probe-su-readonly",
            "mode": "su-c",
            "command": adb_su_shell(args, READ_ONLY_PROBE),
        },
        {
            "name": "probe-su-mount-master-readonly",
            "mode": "su-mm-c",
            "command": adb_su_mm_shell(args, READ_ONLY_PROBE),
        },
    ]


def command_safety(payload: dict[str, Any]) -> dict[str, Any]:
    flat = json.dumps(payload.get("commands", payload), sort_keys=True)
    forbidden = {
        "magisk_install_module": "--install-module",
        "magisk_remove_modules": "--remove-modules",
        "module_write_mkdir": "mkdir",
        "module_write_touch": "touch ",
        "module_write_cp": " cp ",
        "module_write_mv": " mv ",
        "module_write_rm": "rm ",
        "module_write_chmod": "chmod",
        "module_write_chown": "chown",
        "playback": "am start",
        "calibration_ioctl": "msm_audio_cal ioctl",
        "fastboot": "fastboot",
        "raw_partition_write": " dd ",
    }
    findings = [{"name": name, "needle": needle} for name, needle in forbidden.items() if needle in flat]
    required = [
        "magisk -c",
        "magisk -v",
        "magisk --path",
        "magisk --list",
        "/data/adb/modules",
        "su -mm -c",
        "rollback_v2321",
    ]
    missing = [needle for needle in required if needle not in flat]
    return {
        "ok": not findings and not missing,
        "findings": findings,
        "missing_required_needles": missing,
        "forbidden": sorted(forbidden),
        "required": required,
    }


def dry_run(args: argparse.Namespace) -> dict[str, Any]:
    rargs = route_args(args)
    android_boot = route.select_android_boot_candidate()
    rollback = route.file_state(route.ROLLBACK_IMAGE, expected_sha256=route.ROLLBACK_SHA256)
    commands = {
        "flash_android": route.flash_android_command(rargs, "<private-run-dir>/android_boot_0600.img"),
        "android_post_handoff_settle": v2396.android_post_handoff_settle_commands(args),
        "read_only_probes": probe_commands(args),
        "android_wait_device_before_rollback": v2396.adb_base(args) + ["wait-for-device"],
        "android_reboot_recovery_for_rollback": route.android_reboot_recovery_command(rargs),
        "rollback_v2321": route.rollback_command(rargs),
    }
    payload: dict[str, Any] = {
        "run_id": RUN_ID,
        "build_tag": BUILD_TAG,
        "decision": f"{decision_slug()}-live-dry-run",
        "generated_at": now_iso(),
        "host_only": True,
        "device_action": "none",
        "approval_phrase_required_for_live": APPROVAL_PHRASE,
        "android_boot": android_boot,
        "rollback": rollback,
        "commands": commands,
        "hard_boundary": [
            "read-only Android/Magisk access probe",
            "no writes under /data/adb",
            "no Magisk module install or remove",
            "no playback, mixer, PCM, ACDB, or calibration ioctl",
            "rollback to V2321 after probes",
        ],
    }
    safety = command_safety(payload)
    payload["command_safety"] = safety
    payload["future_live_ready"] = bool(android_boot.get("ok") and rollback.get("ok") and safety.get("ok"))
    blockers: list[str] = []
    if not android_boot.get("ok"):
        blockers.append("android boot candidate not ready")
    if not rollback.get("ok"):
        blockers.append("rollback image not ready")
    if not safety.get("ok"):
        blockers.append("command safety failed")
    payload["future_live_blockers"] = blockers
    payload["ok"] = bool(android_boot.get("ok") and rollback.get("ok") and safety.get("ok"))
    return payload


def summarize_probe_outputs(out_dir: Path, steps: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "probe_records": [],
        "magisk_binary_seen": False,
        "magisk_version_seen": False,
        "mount_master_supported": False,
        "root_su_supported": False,
        "root_mount_master_supported": False,
        "su_usage_errors": [],
        "data_adb_modules_visible": False,
        "permission_denied_lines": [],
        "root_permission_denied_lines": [],
    }
    for step in steps:
        if not step.get("name", "").startswith("probe-"):
            continue
        stdout_path = ROOT / step.get("stdout", "")
        stderr_rel = step.get("stderr")
        stderr_path = ROOT / stderr_rel if stderr_rel else None
        text = stdout_path.read_text(errors="replace") if stdout_path.exists() else ""
        stderr_text = stderr_path.read_text(errors="replace") if stderr_path and stderr_path.exists() else ""
        is_su_probe = step.get("name") in {"probe-su-readonly", "probe-su-mount-master-readonly"}
        su_usage_error = "MagiskSU" in stderr_text and "option requires an argument" in stderr_text
        identity_is_root = "uid=0(root)" in text
        record = {
            "name": step.get("name"),
            "ok": step.get("ok"),
            "rc": step.get("rc"),
            "stdout": step.get("stdout"),
            "stderr": step.get("stderr"),
            "has_begin_marker": "A90_MAGISK_PROBE_BEGIN" in text,
            "has_end_marker": "A90_MAGISK_PROBE_END" in text,
            "identity_is_root": identity_is_root,
            "su_usage_error": su_usage_error,
            "has_magisk_path": "/magisk" in text or "/data/adb/magisk" in text,
            "has_modules_path": "/data/adb/modules" in text,
            "permission_denied_count": text.lower().count("permission denied"),
        }
        summary["probe_records"].append(record)
        if su_usage_error:
            summary["su_usage_errors"].append({"probe": step.get("name"), "stderr": step.get("stderr")})
        if "magisk" in text and ("magisk -c" not in text):
            summary["magisk_binary_seen"] = True
        if any(token in text.lower() for token in ("magisk", "version")) and step.get("name") != "probe-shell-readonly":
            summary["magisk_version_seen"] = True
        if step.get("name") == "probe-su-readonly" and identity_is_root:
            summary["root_su_supported"] = True
        if step.get("name") == "probe-su-mount-master-readonly" and identity_is_root:
            summary["root_mount_master_supported"] = True
        if step.get("name") == "probe-su-mount-master-readonly" and record["has_begin_marker"] and not su_usage_error:
            summary["mount_master_supported"] = True
        if record["has_modules_path"]:
            summary["data_adb_modules_visible"] = True
        for line in text.splitlines():
            if "permission denied" in line.lower():
                summary["permission_denied_lines"].append({"probe": step.get("name"), "line": line[:240]})
                if identity_is_root:
                    summary["root_permission_denied_lines"].append({"probe": step.get("name"), "line": line[:240]})
    if summary["su_usage_errors"]:
        summary["classification"] = "su-probe-malformed"
    elif not summary["root_su_supported"] and not summary["root_mount_master_supported"]:
        summary["classification"] = "su-root-not-obtained"
    elif summary["root_mount_master_supported"] and not summary["root_permission_denied_lines"]:
        summary["classification"] = "mount-master-readonly-visible-no-denial"
    elif summary["root_mount_master_supported"]:
        summary["classification"] = "mount-master-supported-but-readonly-denials-present"
    elif summary["data_adb_modules_visible"]:
        summary["classification"] = "modules-visible-without-mount-master"
    else:
        summary["classification"] = "magisk-access-probe-inconclusive"
    return summary


def run_live(args: argparse.Namespace) -> dict[str, Any]:
    ensure_live_approval(args)
    plan = dry_run(args)
    if not plan.get("future_live_ready"):
        raise RuntimeError(f"V2432 live inputs are not ready: {plan.get('future_live_blockers')}")
    if not plan.get("command_safety", {}).get("ok"):
        raise RuntimeError(f"V2432 command safety failed: {plan.get('command_safety')}")

    out_dir = args.out_dir or default_live_out_dir()
    out_dir.mkdir(parents=True, exist_ok=False)
    os.chmod(out_dir, 0o700)

    steps: list[dict[str, Any]] = []
    result: dict[str, Any] = {
        "run_id": RUN_ID,
        "build_tag": BUILD_TAG,
        "decision": f"{decision_slug()}-live-started",
        "out_dir": rel(out_dir),
        "approval_ok": True,
        "plan": plan,
        "steps": steps,
        "rolled_back": False,
        "ok": False,
    }
    write_json(out_dir / "result.json", result)

    rargs = route_args(args)
    sealed = route.copy_sealed_android_boot(plan["android_boot"]["selected"], out_dir)
    result["sealed_android_boot"] = sealed
    write_json(out_dir / "result.json", result)

    rollback_needed = False
    try:
        rollback_needed = True
        steps.append(route.run_step(
            "flash-android",
            route.flash_android_command(rargs, str(out_dir / "android_boot_0600.img")),
            out_dir,
            timeout_sec=args.flash_timeout,
        ))
        v2396.run_android_post_handoff_settle(args, out_dir, steps)

        for item in probe_commands(args):
            steps.append(route.run_step(
                item["name"],
                item["command"],
                out_dir,
                timeout_sec=args.adb_command_timeout,
                check=False,
            ))
        result["probe_summary"] = summarize_probe_outputs(out_dir, steps)
        result["decision"] = f"{decision_slug()}-{result['probe_summary']['classification']}-before-rollback"
        result["ok"] = True
    except Exception as error:
        result["decision"] = f"{decision_slug()}-failed-before-rollback"
        result["error"] = str(error)
        result["ok"] = False
    finally:
        if rollback_needed:
            try:
                v2396.rollback_to_v2321_with_android_recovery(args, rargs, out_dir, steps, result)
                if result.get("ok"):
                    suffix = "rollback-pass"
                    if result.get("rollback_fallback"):
                        suffix = f"rollback-pass-{result['rollback_fallback']}"
                    result["decision"] = f"{result['decision']}-{suffix}"
            except Exception as rollback_error:
                result["rollback_fallback_error"] = str(rollback_error)
                write_json(out_dir / "result.json", result)
                raise
            finally:
                write_json(out_dir / "result.json", result)
        else:
            write_json(out_dir / "result.json", result)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="emit the V2432 read-only probe plan; no device action")
    mode.add_argument("--run-live", action="store_true", help="run the exact-gated V2432 read-only Magisk probe")
    parser.add_argument("--adb", default="adb")
    parser.add_argument("--serial")
    parser.add_argument("--stimulus-apk", type=Path, default=v2396.DEFAULT_STIMULUS_APK, help="compatibility field for shared Android helper; not installed or launched")
    parser.add_argument("--android-timeout", type=float, default=420.0)
    parser.add_argument("--adb-command-timeout", type=float, default=120.0)
    parser.add_argument("--flash-timeout", type=float, default=900.0)
    parser.add_argument("--duration-ms", type=int, default=v2396.DEFAULT_DURATION_MS)
    parser.add_argument("--sample-rate", type=int, default=v2396.DEFAULT_SAMPLE_RATE)
    parser.add_argument("--amplitude", type=float, default=v2396.DEFAULT_AMPLITUDE)
    parser.add_argument("--active-delay-sec", type=float, default=0.75)
    parser.add_argument("--post-delay-sec", type=float, default=1.0)
    parser.add_argument("--from-native", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--approval")
    parser.add_argument("--out-dir", type=Path, help="private live output directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.run_live:
        try:
            payload = run_live(args)
        except RuntimeError as error:
            payload = {
                "run_id": RUN_ID,
                "build_tag": BUILD_TAG,
                "decision": f"{decision_slug()}-live-refused",
                "ok": False,
                "rolled_back": False,
                "reason": str(error),
            }
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 1
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if payload.get("ok") and payload.get("rolled_back") else 1

    payload = dry_run(args)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
