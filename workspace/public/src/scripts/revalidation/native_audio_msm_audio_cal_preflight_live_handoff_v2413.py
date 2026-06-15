#!/usr/bin/env python3
"""V2413 exact-gated live runner for AUD-5C /dev/msm_audio_cal preflight.

This is the first live execution of the V2411/V2412 N2 gate.  It reuses the
proven V2334 ADSP + /dev/snd materialization window, inventories the dynamic
msm_audio_cal misc node, materializes a temporary runtime devnode if needed,
performs one open/close-only probe, snapshots bounded dmesg, cleans up the
runtime node if this runner created it, and rolls back to V2321.

No calibration ioctl, ACDB payload, mixer route write, PCM playback, Android
handoff, or Magisk action is executed by this runner.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import native_audio_msm_audio_cal_preflight_gate_v2412 as gate
import native_audio_snd_nodes_preflight_handoff_v2335 as snd

RUN_ID = "V2413"
BUILD_TAG = "v2413-audio-msm-audio-cal-preflight-live"
APPROVAL_PHRASE = gate.REQUIRED_APPROVAL_PHRASE
OUT_DIR_PREFIX = "v2413-msm-audio-cal-preflight"
CREATED_MARKER = "/dev/.a90_msm_audio_cal_v2413_created"
ADSP_ACCEPTED_MARKER = "audio.adsp_boot_once.retry=forbidden"
ADSP_END_MARKER = "A90P1 END seq="
ADSP_FAILURE_MARKERS = (
    "audio.adsp_boot_once.refused=",
    "audio.adsp_boot_once.write=open_failed",
    "audio.adsp_boot_once.write=failed",
    "audio.adsp_boot_once.write=close_failed",
)
PROHIBITED_LIVE_TOKENS = (
    "AUDIO_ALLOCATE_CALIBRATION",
    "AUDIO_DEALLOCATE_CALIBRATION",
    "AUDIO_PREPARE_CALIBRATION",
    "AUDIO_SET_CALIBRATION",
    "AUDIO_GET_CALIBRATION",
    "AUDIO_POST_CALIBRATION",
    "AUDIO_SET_RTAC",
    "AUDIO_GET_RTAC",
    " ioctl",
    "tinyplay",
    "tinymix",
    "tinypcminfo",
    "pcm_write",
    "SNDRV_PCM_IOCTL_WRITEI_FRAMES",
    "audio.primary",
    "libacdbloader",
    "magisk",
    "su -c",
    "app_process",
    "am start",
    "adsprpc",
    "/efs",
    "/sec_efs",
    "/dev/block",
    " dd ",
)


def rel(path: Path) -> str:
    return snd.rel(path)


def write_json(path: Path, payload: Any) -> None:
    snd.write_json(path, payload)


def stdout_of(step: dict[str, Any]) -> str:
    return snd.stdout_of(step)


def step_text(step: dict[str, Any]) -> str:
    return stdout_of(step) or str(step.get("stdout_tail") or "")


def classify_adsp_boot_once_step(step: dict[str, Any]) -> dict[str, Any]:
    text = step_text(step)
    failure_markers = [marker for marker in ADSP_FAILURE_MARKERS if marker in text]
    accepted_marker = ADSP_ACCEPTED_MARKER in text
    end_marker = ADSP_END_MARKER in text
    protocol_ok = end_marker and "status=ok" in text
    accepted = accepted_marker and not failure_markers
    if protocol_ok and accepted:
        decision = "accepted-protocol-ok"
    elif accepted:
        decision = "accepted-protocol-marker-lost"
    elif failure_markers:
        decision = "rejected-or-write-failed"
    else:
        decision = "unknown-no-accepted-marker"
    return {
        "decision": decision,
        "accepted": accepted,
        "accepted_marker": accepted_marker,
        "end_marker": end_marker,
        "protocol_ok": protocol_ok,
        "failure_markers": failure_markers,
        "stdout_path": step.get("stdout_path"),
        "stdout_tail": text[-1000:],
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
            f"if [ -e {CREATED_MARKER} ]; then cat {CREATED_MARKER} | sed 's/^/A90_MSM_AUDIO_CAL_CREATED_MARKER /'; fi",
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
            "  rm -f " + CREATED_MARKER,
            "  mknod /dev/msm_audio_cal c 10 \"$minor\" || exit $?",
            "  chmod 0600 /dev/msm_audio_cal || true",
            "  echo \"minor=$minor\" > " + CREATED_MARKER,
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
            f"if [ -e {CREATED_MARKER} ]; then",
            "  marker_minor=$(sed -n 's/^minor=//p' " + CREATED_MARKER + " | head -n1)",
            "  misc_minor=$(awk '$2==\"msm_audio_cal\"{print $1; exit}' /proc/misc 2>/dev/null || true)",
            "  if [ -e /dev/msm_audio_cal ] && [ -n \"$marker_minor\" ] && [ \"$marker_minor\" = \"$misc_minor\" ]; then",
            "    rm -f /dev/msm_audio_cal " + CREATED_MARKER,
            "    echo A90_MSM_AUDIO_CAL_CLEANUP_REMOVED created_minor=$marker_minor",
            "  else",
            "    rm -f " + CREATED_MARKER,
            "    echo A90_MSM_AUDIO_CAL_CLEANUP_MARKER_ONLY marker_minor=$marker_minor misc_minor=$misc_minor",
            "  fi",
            "else",
            "  echo A90_MSM_AUDIO_CAL_CLEANUP_NO_MARKER_KEEP_NODE",
            "fi",
            "echo A90_MSM_AUDIO_CAL_CLEANUP_END",
        ]
    )


def bounded_dmesg_script(lines: int) -> str:
    return f"dmesg | tail -n {int(lines)}"


def live_shell_commands(args: argparse.Namespace) -> list[dict[str, Any]]:
    commands = [
        {"name": "msm-audio-cal-inventory-before-materialize", "native_command": ["run", "/bin/busybox", "sh", "-c", inventory_script()]},
        {"name": "msm-audio-cal-materialize-if-needed", "native_command": ["run", "/bin/busybox", "sh", "-c", materialize_script()]},
    ]
    if args.include_open_probe:
        commands.append({"name": "msm-audio-cal-open-only", "native_command": ["run", "/bin/busybox", "sh", "-c", open_only_script()]})
    commands.extend(
        [
            {"name": "msm-audio-cal-inventory-after-open", "native_command": ["run", "/bin/busybox", "sh", "-c", inventory_script()]},
            {"name": "msm-audio-cal-dmesg-tail", "native_command": ["run", "/bin/busybox", "sh", "-c", bounded_dmesg_script(args.dmesg_tail_lines)], "timeout": args.dmesg_timeout},
            {"name": "msm-audio-cal-cleanup", "native_command": ["run", "/bin/busybox", "sh", "-c", cleanup_script()]},
            {"name": "msm-audio-cal-inventory-after-cleanup", "native_command": ["run", "/bin/busybox", "sh", "-c", inventory_script()]},
        ]
    )
    return commands


def command_safety(commands: list[dict[str, Any]]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    joined_all = "\n".join(" ".join(map(str, command["native_command"])) for command in commands)
    for token in PROHIBITED_LIVE_TOKENS:
        if token in joined_all:
            findings.append({"prohibited_token": token})
    if "mknod /dev/msm_audio_cal c 10" not in joined_all:
        findings.append({"reason": "expected runtime mknod materialization command missing"})
    if "exec 3< \"$node\"" not in joined_all:
        findings.append({"reason": "expected O_RDONLY open-only probe missing"})
    return {
        "ok": not findings,
        "findings": findings,
        "hard_boundaries": [
            "no calibration ioctl",
            "no ACDB payload",
            "no mixer route write",
            "no PCM playback/write",
            "no Android or Magisk action",
            "rollback to V2321 after candidate window",
        ],
    }


def preflight_state(args: argparse.Namespace) -> dict[str, Any]:
    commands = live_shell_commands(args)
    safety = command_safety(commands)
    snd_state = snd.preflight_state()
    return {
        "run_id": RUN_ID,
        "build_tag": BUILD_TAG,
        "approval_phrase_required": APPROVAL_PHRASE,
        "snd_materialization_preflight": snd_state,
        "preflight_ok": snd.preflight_ok(snd_state),
        "commands": [
            {"name": command["name"], "native_command": command["native_command"]} for command in commands
        ],
        "command_safety": safety,
        "ok": bool(snd.preflight_ok(snd_state) and safety.get("ok")),
        "magisk_strategy": {
            "native_runtime_dependency": False,
            "v2413_uses_magisk": False,
            "fallback_only": "M0/M1 remain Android-good measurement options only after this native open-only discriminator proves more payload capture is needed.",
        },
    }


def dry_run_payload(args: argparse.Namespace) -> dict[str, Any]:
    state = preflight_state(args)
    return {
        "decision": "v2413-msm-audio-cal-preflight-live-runner-dry-run" if state["ok"] else "v2413-msm-audio-cal-preflight-live-runner-blocked",
        "ok": bool(state["ok"]),
        "device_action": "none",
        "preflight": state,
        "live_sequence": [
            "verify resident V2321 plus selftest fail=0",
            "flash V2334 snd-nodes candidate via checked helper",
            "verify candidate version/status/selftest",
            "run ADSP + /dev/snd materialization path",
            "inventory /proc/misc and /dev/msm_audio_cal",
            "materialize runtime /dev/msm_audio_cal from /proc/misc minor if missing",
            "perform one open/close-only probe",
            "capture bounded dmesg tail and cleanup runtime node if created",
            "rollback to V2321 and verify selftest fail=0",
        ],
    }


def verify_live_approval(args: argparse.Namespace) -> None:
    if args.approval != APPROVAL_PHRASE:
        raise SystemExit("refusing live run: exact --approval phrase required:\n" + APPROVAL_PHRASE)


def run_cal_command(args: argparse.Namespace, out_dir: Path, steps: list[dict[str, Any]], command: dict[str, Any]) -> dict[str, Any]:
    return snd.run_serial_transport_step(
        out_dir,
        steps,
        command["name"],
        args,
        command["native_command"],
        timeout=float(command.get("timeout") or args.command_timeout),
        retry_observation=False,
    )


def live_run(args: argparse.Namespace, state: dict[str, Any]) -> dict[str, Any]:
    verify_live_approval(args)
    if not state.get("ok"):
        raise SystemExit("refusing live run: V2413 preflight failed")

    out_dir = snd.ROOT / f"workspace/private/runs/audio/{OUT_DIR_PREFIX}-{snd.now_slug()}"
    out_dir.mkdir(parents=True, exist_ok=False)
    steps: list[dict[str, Any]] = []
    result: dict[str, Any] = {
        "decision": "v2413-msm-audio-cal-preflight-live-started",
        "out_dir": rel(out_dir),
        "preflight": state,
        "steps": steps,
        "rolled_back": False,
    }
    write_json(out_dir / "preflight.json", state)
    candidate_flashed = False
    try:
        snd.run_step(
            out_dir,
            steps,
            "preflight-current-v2321-verify",
            snd.flash_command(snd.ROLLBACK_IMAGE, snd.ROLLBACK_VERSION, snd.ROLLBACK_SHA256, from_native=False) + ["--verify-only"],
            timeout=args.flash_timeout,
        )
        current_selftest = snd.run_a90ctl_observation(args, out_dir, steps, "preflight-current-selftest", ["selftest", "verbose"], timeout=120.0)
        if not snd.selftest_ok(stdout_of(current_selftest)):
            raise RuntimeError("resident preflight selftest did not report fail=0")

        snd.run_step(
            out_dir,
            steps,
            "flash-v2334-candidate",
            snd.flash_command(snd.CANDIDATE_IMAGE, snd.CANDIDATE_VERSION, snd.CANDIDATE_SHA256, from_native=True),
            timeout=args.flash_timeout,
        )
        candidate_flashed = True

        version = snd.run_a90ctl_observation(args, out_dir, steps, "candidate-version", ["version"], timeout=90.0)
        if snd.CANDIDATE_VERSION not in stdout_of(version):
            raise RuntimeError("candidate version output did not contain expected version")
        snd.run_a90ctl_observation(args, out_dir, steps, "candidate-status", ["status"], timeout=90.0)
        candidate_selftest = snd.run_a90ctl_observation(args, out_dir, steps, "candidate-selftest", ["selftest", "verbose"], timeout=120.0)
        if not snd.selftest_ok(stdout_of(candidate_selftest)):
            raise RuntimeError("candidate selftest did not report fail=0")

        pre_adsp = snd.run_a90ctl_observation(args, out_dir, steps, "candidate-audio-adsp-status-before", ["audio", "adsp-status"], timeout=90.0)
        pre_snd = snd.run_a90ctl_observation(args, out_dir, steps, "candidate-audio-snd-status-before", ["audio", "snd-status"], timeout=90.0)
        result["initial_audio"] = snd.classify_audio_status(stdout_of(pre_adsp) + "\n" + stdout_of(pre_snd))
        if not (result["initial_audio"]["has_audio_card"] and result["initial_audio"]["has_sound_class_control"]):
            snd.run_menu_settle_step(out_dir, steps, "settle-before-adsp-boot-once", args)
            adsp_boot_step = snd.run_serial_transport_step(
                out_dir,
                steps,
                "candidate-adsp-boot-once",
                args,
                ["audio", "adsp-boot-once", snd.ADSP_TOKEN],
                timeout=90.0,
                retry_observation=False,
                allow_error=True,
            )
            result["adsp_boot_once"] = classify_adsp_boot_once_step(adsp_boot_step)
            if not result["adsp_boot_once"].get("accepted"):
                raise RuntimeError(f"candidate ADSP boot-once did not show accepted marker: {result['adsp_boot_once']}")

        result["card_wait"] = snd.wait_for_audio_card(args, out_dir, steps)
        before_materialize = snd.run_a90ctl_observation(args, out_dir, steps, "snd-status-before-materialize", ["audio", "snd-status"], timeout=90.0)
        result["before_materialize"] = snd.classify_audio_status(stdout_of(before_materialize))
        snd.run_menu_settle_step(out_dir, steps, "settle-before-snd-materialize-once", args)
        materialize = snd.run_serial_transport_step(
            out_dir,
            steps,
            "snd-materialize-once",
            args,
            ["audio", "snd-materialize-once", snd.SND_TOKEN],
            timeout=90.0,
            retry_observation=False,
        )
        result["snd_materialize_tail"] = stdout_of(materialize)[-4000:]
        after_materialize = snd.run_a90ctl_observation(args, out_dir, steps, "snd-status-after-materialize", ["audio", "snd-status"], timeout=90.0)
        after = snd.classify_audio_status(stdout_of(after_materialize))
        result["after_materialize"] = after
        if not (after["has_dev_snd_control"] and after["has_dev_snd_pcm"]):
            raise RuntimeError("materialization did not produce control+pcm /dev/snd nodes")

        cal_steps = []
        for command in live_shell_commands(args):
            step = run_cal_command(args, out_dir, steps, command)
            cal_steps.append({"name": command["name"], "ok": step.get("ok"), "stdout_path": step.get("stdout_path"), "stdout_tail": step.get("stdout_tail")})
        result["msm_audio_cal_preflight"] = cal_steps
        combined_cal_text = "\n".join(stdout_of(step) for step in steps if str(step.get("name", "")).startswith("msm-audio-cal"))
        result["msm_audio_cal_classification"] = classify_msm_audio_cal_text(combined_cal_text)
        if not result["msm_audio_cal_classification"].get("opened"):
            raise RuntimeError(f"msm_audio_cal open-only probe did not open: {result['msm_audio_cal_classification']}")

        final_candidate_selftest = snd.run_a90ctl_observation(args, out_dir, steps, "candidate-selftest-after-msm-audio-cal", ["selftest", "verbose"], timeout=120.0)
        if not snd.selftest_ok(stdout_of(final_candidate_selftest)):
            raise RuntimeError("candidate final selftest did not report fail=0")
        result["decision"] = "v2413-msm-audio-cal-preflight-live-pass-before-rollback"
    except Exception as exc:
        result["decision"] = "v2413-msm-audio-cal-preflight-live-blocked"
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)
        raise
    finally:
        if candidate_flashed:
            rollback_record = snd.run_step(
                out_dir,
                steps,
                "rollback-v2321",
                snd.flash_command(snd.ROLLBACK_IMAGE, snd.ROLLBACK_VERSION, snd.ROLLBACK_SHA256, from_native=True),
                timeout=args.flash_timeout,
                allow_error=True,
            )
            result["rolled_back"] = bool(rollback_record.get("ok"))
            try:
                rollback_version = snd.run_a90ctl_observation(args, out_dir, steps, "rollback-version", ["version"], timeout=90.0)
                rollback_selftest = snd.run_a90ctl_observation(args, out_dir, steps, "rollback-selftest", ["selftest", "verbose"], timeout=120.0)
                result["rollback_version_ok"] = snd.ROLLBACK_VERSION in stdout_of(rollback_version)
                result["rollback_selftest_fail0"] = snd.selftest_ok(stdout_of(rollback_selftest))
            except Exception as exc:  # noqa: BLE001 - preserve rollback diagnostics.
                result["rollback_health_error"] = str(exc)
        write_json(out_dir / "result.json", result)
    return result


def classify_msm_audio_cal_text(text: str) -> dict[str, Any]:
    misc_match = re.search(r"A90_MSM_AUDIO_CAL_MISC minor=(\d+)", text)
    materialized = "A90_MSM_AUDIO_CAL_MATERIALIZE_OK" in text
    materialized_created = "A90_MSM_AUDIO_CAL_MATERIALIZE_OK" in text and "created=1" in text
    opened_rdonly = "A90_MSM_AUDIO_CAL_OPEN_OK mode=O_RDONLY" in text
    opened_rdwr = "A90_MSM_AUDIO_CAL_OPEN_OK mode=O_RDWR" in text
    no_misc = "A90_MSM_AUDIO_CAL_NO_MISC" in text
    cleanup_removed = "A90_MSM_AUDIO_CAL_CLEANUP_REMOVED" in text
    return {
        "minor": misc_match.group(1) if misc_match else None,
        "misc_registered": bool(misc_match),
        "materialized": materialized,
        "materialized_created": materialized_created,
        "opened": bool(opened_rdonly or opened_rdwr),
        "opened_mode": "O_RDONLY" if opened_rdonly else ("O_RDWR" if opened_rdwr else None),
        "no_misc": no_misc,
        "cleanup_removed_created_node": cleanup_removed,
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="verify artifacts and print live plan; no device action")
    mode.add_argument("--run-live", action="store_true", help="run exact-gated AUD-5C live preflight")
    parser.add_argument("--approval", default="")
    parser.add_argument("--bridge-host", default="127.0.0.1")
    parser.add_argument("--bridge-port", type=int, default=54321)
    parser.add_argument("--command-timeout", type=float, default=90.0)
    parser.add_argument("--dmesg-timeout", type=float, default=90.0)
    parser.add_argument("--dmesg-tail-lines", type=int, default=160)
    parser.add_argument("--flash-timeout", type=float, default=420.0)
    parser.add_argument("--card-timeout", type=float, default=90.0)
    parser.add_argument("--poll-interval", type=float, default=3.0)
    parser.add_argument("--menu-settle-sec", type=float, default=1.5)
    parser.add_argument("--include-open-probe", action=argparse.BooleanOptionalAction, default=True)
    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()
    if not args.run_live:
        payload = dry_run_payload(args)
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if payload.get("ok") else 1
    state = preflight_state(args)
    result = live_run(args, state)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.get("rollback_selftest_fail0") else 1


if __name__ == "__main__":
    raise SystemExit(main())
