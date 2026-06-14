#!/usr/bin/env python3
"""V2412 host-only planner for /dev/msm_audio_cal preflight.

This script does not touch the device by default. It turns the V2411 design into
a reviewable future live plan for AUD-5C: reproduce the proven V2334 ADSP +
/dev/snd materialization window, inventory the msm_audio_cal misc device, and at
most perform one open/close-only probe in a later exact-gated run.

No audio calibration ioctl, ACDB payload, mixer route write, PCM playback, audio
HAL, Magisk runtime dependency, or Android boot is executed by this planner.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import native_audio_snd_nodes_preflight_handoff_v2335 as snd

RUN_ID = "V2412"
BUILD_TAG = "v2412-audio-msm-audio-cal-preflight-gate"
REQUIRED_APPROVAL_PHRASE = (
    "AUD-5C-msm-audio-cal-preflight go: one-shot /dev/msm_audio_cal "
    "existence/open-only inventory on V2334, no AUDIO_SET ioctls, no ACDB payload, "
    "no playback, rollback to V2321"
)
V2411_REPORT = snd.ROOT / "docs/reports/NATIVE_INIT_V2411_AUDIO_MSM_AUDIO_CAL_PREFLIGHT_DESIGN_2026-06-15.md"
FUTURE_LIVE_RUNNER_STATUS = "planned-not-executed-by-v2412"
PROHIBITED_COMMAND_TOKENS = (
    "AUDIO_ALLOCATE_CALIBRATION",
    "AUDIO_DEALLOCATE_CALIBRATION",
    "AUDIO_PREPARE_CALIBRATION",
    "AUDIO_SET_CALIBRATION",
    "AUDIO_GET_CALIBRATION",
    "AUDIO_POST_CALIBRATION",
    "AUDIO_SET_RTAC",
    "AUDIO_GET_RTAC",
    "ioctl",
    "tinyplay",
    "tinymix",
    "tinypcminfo",
    "pcm_write",
    "SNDRV_PCM_IOCTL_WRITEI_FRAMES",
    "mixer_paths",
    "audio.primary",
    "libacdbloader",
    "magisk --install-module",
    "su -c",
    "app_process",
    "am start",
    "adsprpc",
    "/efs",
    "/sec_efs",
    "/dev/block",
    " dd ",
)
OPEN_ONLY_ALLOWED_PATTERNS = (
    re.compile(r"exec 3< \"\$node\""),
    re.compile(r"exec 3<> \"\$node\""),
)


def rel(path: Path) -> str:
    return snd.rel(path)


def serial_shell_command(args: argparse.Namespace, name: str, script: str, *, timeout: float | None = None) -> dict[str, Any]:
    timeout_value = args.command_timeout if timeout is None else timeout
    argv = ["/bin/sh", "-c", script]
    return {
        "name": name,
        "transport": "serial-cmdv1x",
        "argv": argv,
        "a90ctl": snd.a90ctl_command(
            args,
            ["run", *argv],
            hide_on_busy=True,
            timeout=timeout_value,
        ),
        "mutates_audio_calibration": False,
        "uses_audio_ioctl": False,
        "uses_acdb_payload": False,
        "uses_playback": False,
        "not_executed_by_v2412": True,
    }


def inventory_script() -> str:
    return "\n".join(
        [
            "set -u",
            "echo A90_MSM_AUDIO_CAL_INVENTORY_BEGIN",
            "if [ -r /proc/misc ]; then",
            "  awk '$2==\"msm_audio_cal\"{print \"A90_MSM_AUDIO_CAL_MISC minor=\" $1}' /proc/misc || true",
            "else",
            "  echo A90_MSM_AUDIO_CAL_PROC_MISC_MISSING",
            "fi",
            "if [ -e /dev/msm_audio_cal ]; then",
            "  ls -l /dev/msm_audio_cal 2>&1 | sed 's/^/A90_MSM_AUDIO_CAL_LS /'",
            "  /bin/toybox stat -c 'A90_MSM_AUDIO_CAL_STAT mode=%a type=%F major_minor=%t:%T' /dev/msm_audio_cal 2>&1 || true",
            "else",
            "  echo A90_MSM_AUDIO_CAL_NODE_MISSING",
            "fi",
            "echo A90_MSM_AUDIO_CAL_INVENTORY_END",
        ]
    )


def materialize_script() -> str:
    return "\n".join(
        [
            "set -u",
            "echo A90_MSM_AUDIO_CAL_MATERIALIZE_BEGIN",
            "minor=$(awk '$2==\"msm_audio_cal\"{print $1; exit}' /proc/misc 2>/dev/null || true)",
            "if [ -z \"$minor\" ]; then echo A90_MSM_AUDIO_CAL_NO_MISC; exit 3; fi",
            "created=0",
            "if [ ! -e /dev/msm_audio_cal ]; then",
            "  mknod /dev/msm_audio_cal c 10 \"$minor\" || exit $?",
            "  chmod 0600 /dev/msm_audio_cal || true",
            "  created=1",
            "fi",
            "ls -l /dev/msm_audio_cal 2>&1 | sed 's/^/A90_MSM_AUDIO_CAL_LS /'",
            "echo A90_MSM_AUDIO_CAL_MATERIALIZE_OK minor=$minor created=$created",
            "echo A90_MSM_AUDIO_CAL_MATERIALIZE_END",
        ]
    )


def open_only_script() -> str:
    return "\n".join(
        [
            "set -u",
            "node=/dev/msm_audio_cal",
            "echo A90_MSM_AUDIO_CAL_OPEN_BEGIN",
            "if [ ! -e \"$node\" ]; then echo A90_MSM_AUDIO_CAL_OPEN_NODE_MISSING; exit 4; fi",
            "if exec 3< \"$node\"; then",
            "  echo A90_MSM_AUDIO_CAL_OPEN_OK mode=O_RDONLY",
            "  exec 3<&-",
            "  echo A90_MSM_AUDIO_CAL_OPEN_END",
            "  exit 0",
            "fi",
            "ro_rc=$?",
            "echo A90_MSM_AUDIO_CAL_OPEN_FAIL mode=O_RDONLY rc=$ro_rc",
            "if exec 3<> \"$node\"; then",
            "  echo A90_MSM_AUDIO_CAL_OPEN_OK mode=O_RDWR",
            "  exec 3>&-",
            "  echo A90_MSM_AUDIO_CAL_OPEN_END",
            "  exit 0",
            "fi",
            "rw_rc=$?",
            "echo A90_MSM_AUDIO_CAL_OPEN_FAIL mode=O_RDWR rc=$rw_rc",
            "echo A90_MSM_AUDIO_CAL_OPEN_END",
            "exit $rw_rc",
        ]
    )


def cleanup_script() -> str:
    return "\n".join(
        [
            "set -u",
            "echo A90_MSM_AUDIO_CAL_CLEANUP_BEGIN",
            "minor=$(awk '$2==\"msm_audio_cal\"{print $1; exit}' /proc/misc 2>/dev/null || true)",
            "if [ -n \"$minor\" ] && [ -e /dev/msm_audio_cal ]; then",
            "  actual=$(ls -l /dev/msm_audio_cal 2>/dev/null | awk '{print $(NF-1)}' | tr -d ',')",
            "  if [ \"$actual\" = \"10\" ]; then echo A90_MSM_AUDIO_CAL_CLEANUP_KEEP_MISC_NODE; else echo A90_MSM_AUDIO_CAL_CLEANUP_SKIP actual_major=$actual; fi",
            "fi",
            "echo A90_MSM_AUDIO_CAL_CLEANUP_END",
        ]
    )


def bounded_dmesg_script(lines: int) -> str:
    return f"dmesg | tail -n {int(lines)}"


def planned_cal_preflight_commands(args: argparse.Namespace) -> list[dict[str, Any]]:
    commands = [
        serial_shell_command(args, "msm-audio-cal-inventory-before-materialize", inventory_script()),
        serial_shell_command(args, "msm-audio-cal-materialize-if-needed", materialize_script()),
    ]
    if args.include_open_probe:
        commands.append(serial_shell_command(args, "msm-audio-cal-open-only", open_only_script()))
    commands.extend(
        [
            serial_shell_command(args, "msm-audio-cal-inventory-after-open", inventory_script()),
            serial_shell_command(args, "msm-audio-cal-dmesg-tail", bounded_dmesg_script(args.dmesg_tail_lines), timeout=args.dmesg_timeout),
            serial_shell_command(args, "msm-audio-cal-cleanup", cleanup_script()),
        ]
    )
    return commands


def command_safety(commands: list[dict[str, Any]]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    for command in commands:
        argv = [str(part) for part in command.get("argv", [])]
        joined = " ".join(argv)
        for token in PROHIBITED_COMMAND_TOKENS:
            if token in joined:
                findings.append({"command": command.get("name"), "prohibited_token": token, "argv": argv})
        if "mknod /dev/msm_audio_cal c 10" in joined:
            # Runtime devnode materialization is allowed by V2411; it is not a partition write.
            pass
        if "exec 3" in joined and not any(pattern.search(joined) for pattern in OPEN_ONLY_ALLOWED_PATTERNS):
            findings.append({"command": command.get("name"), "reason": "unexpected fd operation", "argv": argv})
        if any(flag in joined for flag in (" ioctl", "tinyplay", "pcm_write")):
            findings.append({"command": command.get("name"), "reason": "calibration/playback token present", "argv": argv})
    return {
        "ok": not findings,
        "findings": findings,
        "prohibited_tokens": list(PROHIBITED_COMMAND_TOKENS),
        "allowed_runtime_mutations": [
            "temporary /dev/msm_audio_cal mknod from /proc/misc minor",
            "chmod on that runtime devnode",
            "one open/close-only probe when include_open_probe is true",
        ],
        "hard_boundaries": [
            "no calibration ioctl",
            "no ACDB payload",
            "no mixer route write",
            "no PCM playback/write",
            "no Android/Magisk action in V2412",
            "rollback to V2321 required for any future live run",
        ],
    }


def preflight_state(args: argparse.Namespace) -> dict[str, Any]:
    snd_state = snd.preflight_state()
    commands = planned_cal_preflight_commands(args)
    safety = command_safety(commands)
    return {
        "run_id": RUN_ID,
        "build_tag": BUILD_TAG,
        "host_only": True,
        "source_report": {"path": rel(V2411_REPORT), "exists": V2411_REPORT.exists()},
        "approval_phrase_required_for_future_live": REQUIRED_APPROVAL_PHRASE,
        "snd_materialization_preflight": snd_state,
        "cal_preflight_commands": commands,
        "command_safety": safety,
        "include_open_probe": bool(args.include_open_probe),
        "ok": bool(V2411_REPORT.exists() and snd.preflight_ok(snd_state) and safety.get("ok")),
        "magisk_strategy": {
            "native_runtime_dependency": False,
            "default": "M0 transient Android-good measurement helper only",
            "m1_temporary_boot_module": "M1 temporary boot module reserved only if M0 misses early /dev/msm_audio_cal payloads",
            "v2412_uses_magisk": False,
        },
    }


def dry_run_payload(args: argparse.Namespace) -> dict[str, Any]:
    state = preflight_state(args)
    return {
        "decision": "v2412-msm-audio-cal-preflight-gate-dry-run" if state["ok"] else "v2412-msm-audio-cal-preflight-gate-blocked",
        "ok": bool(state["ok"]),
        "device_action": "none",
        "future_live_runner_status": FUTURE_LIVE_RUNNER_STATUS,
        "preflight": state,
        "materialization_plan": snd.dry_run_plan(state["snd_materialization_preflight"]),
        "future_live_sequence": [
            "verify resident V2321 and selftest fail=0",
            "flash V2334 audio snd-nodes candidate through checked helper",
            "verify candidate version/status/selftest",
            "run token-gated ADSP/snd materialization path",
            "run msm_audio_cal inventory/materialize/open-only commands over serial cmdv1x",
            "rollback to V2321 through checked helper",
            "verify rollback selftest fail=0",
        ],
    }


def verify_live_approval(args: argparse.Namespace) -> None:
    if args.approval != REQUIRED_APPROVAL_PHRASE:
        raise SystemExit(
            "refusing live run: exact --approval phrase required:\n"
            f"{REQUIRED_APPROVAL_PHRASE}"
        )


def live_refusal_payload(args: argparse.Namespace) -> dict[str, Any]:
    verify_live_approval(args)
    state = preflight_state(args)
    return {
        "decision": "v2412-live-not-executed-source-only-gate-ready",
        "ok": bool(state["ok"]),
        "device_action": "none",
        "reason": "V2412 intentionally wires the exact gate and dry-run plan only; execute live in the next bounded V-iteration after this source is reviewed and committed.",
        "approval_phrase_matched": True,
        "preflight": state,
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="print host-only future live plan; default")
    mode.add_argument("--run-live", action="store_true", help="exact-gated placeholder; V2412 does not execute device actions")
    parser.add_argument("--approval", default="")
    parser.add_argument("--bridge-host", default="127.0.0.1")
    parser.add_argument("--bridge-port", type=int, default=54321)
    parser.add_argument("--command-timeout", type=float, default=90.0)
    parser.add_argument("--dmesg-timeout", type=float, default=90.0)
    parser.add_argument("--dmesg-tail-lines", type=int, default=160)
    parser.add_argument("--include-open-probe", action=argparse.BooleanOptionalAction, default=True)
    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()
    if args.run_live:
        payload = live_refusal_payload(args)
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if payload.get("ok") else 1
    payload = dry_run_payload(args)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
