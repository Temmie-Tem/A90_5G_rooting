#!/usr/bin/env python3
"""V2877 live handoff for the V2876 KMS page-flip probe.

This runner flashes the V2876 candidate, runs one bounded `video flipprobe`,
then rolls back to v2321 and verifies selftest fail=0.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from _workspace_bootstrap import repo_root
import native_audio_v2798_readiness_replay_live_handoff_v2801 as base

ROOT = repo_root()
RUN_ID = "V2877"
BUILD_TAG = "v2877-video-flipprobe-live"
CANDIDATE_IMAGE = ROOT / "workspace/private/inputs/boot_images/boot_linux_v2876_video_flipprobe.img"
CANDIDATE_VERSION = "0.10.24"
CANDIDATE_TAG = "v2876-video-flipprobe"
CANDIDATE_SHA256 = "2431eac000e5591709d6203130ab57e44d27d8597686aa8775dfc1b471fe759a"
ROLLBACK_VERSION = "0.9.285"
ROLLBACK_IMAGE = ROOT / "workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img"
ROLLBACK_SHA256 = "ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb"
FALLBACK_V2237 = ROOT / "workspace/private/inputs/boot_images/boot_linux_v2237_supplicant_terminate_poll.img"
FALLBACK_V2237_SHA256 = "b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f"
FALLBACK_V48 = ROOT / "workspace/private/inputs/boot_images/boot_linux_v48.img"
REPORT_PATH = ROOT / "docs/reports/NATIVE_INIT_V2877_VIDEO_FLIPPROBE_LIVE_2026-06-19.md"
SELFTEST_FAIL0_RE = re.compile(r"\bfail=0\b")
PRESENTED_RE = re.compile(r"video\.flipprobe\.presented=(\d+)")
FLIP_EVENTS_RE = re.compile(r"video\.flipprobe\.flip_events=(\d+)")


def rel(path: Path) -> str:
    return base.rel(path)


def now_slug() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y%m%d-%H%M%S")


def sha256_file(path: Path) -> str:
    return base.sha256_file(path)


def write_json(path: Path, payload: Any) -> None:
    base.write_json(path, payload)


def stdout_of(step: dict[str, Any]) -> str:
    return base.stdout_of(step)


def file_state(path: Path, expected_sha: str | None = None) -> dict[str, Any]:
    state: dict[str, Any] = {"path": rel(path), "exists": path.exists()}
    if path.exists():
        state["size"] = path.stat().st_size
        digest = sha256_file(path)
        state["sha256"] = digest
        if expected_sha:
            state["sha256_ok"] = digest == expected_sha
    elif expected_sha:
        state["sha256_ok"] = False
    return state


def selftest_step_ok(step: dict[str, Any]) -> bool:
    return bool(SELFTEST_FAIL0_RE.search(stdout_of(step))) or base.protocol_selftest_ok(step)


def flash_command(image: Path, expect_version: str, expect_sha: str, *, from_native: bool) -> list[str]:
    command = [
        "python3",
        rel(base.FLASH),
        rel(image),
        "--expect-version",
        expect_version,
        "--expect-sha256",
        expect_sha,
        "--expect-readback-sha256",
        expect_sha,
        "--verify-protocol",
        "selftest",
        "--bridge-timeout",
        "300",
        "--recovery-timeout",
        "300",
    ]
    if from_native:
        command.append("--from-native")
    return command


def preflight_state(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "run_id": RUN_ID,
        "candidate": file_state(CANDIDATE_IMAGE, CANDIDATE_SHA256),
        "rollback": file_state(ROLLBACK_IMAGE, ROLLBACK_SHA256),
        "fallback_v2237": file_state(FALLBACK_V2237, FALLBACK_V2237_SHA256),
        "fallback_v48": file_state(FALLBACK_V48),
        "flash_helper": file_state(base.FLASH),
        "flipprobe_frames": args.frames,
        "hard_boundary": [
            "boot partition only via native_init_flash.py",
            "rollback to v2321 and verify selftest fail=0",
            "KMS dumb-buffer page-flip probe only",
            "no Venus/KGSL/raw DSI/panel init/backlight/PMIC/PWM/regulator/GPIO/GDSC",
        ],
    }


def preflight_ok(state: dict[str, Any]) -> bool:
    return bool(
        state["candidate"].get("sha256_ok")
        and state["rollback"].get("sha256_ok")
        and state["fallback_v2237"].get("sha256_ok")
        and state["fallback_v48"].get("exists")
        and state["flash_helper"].get("exists")
    )


def classify_flipprobe(text: str, expected_frames: int) -> dict[str, Any]:
    presented_match = PRESENTED_RE.search(text)
    events_match = FLIP_EVENTS_RE.search(text)
    presented = int(presented_match.group(1)) if presented_match else 0
    flip_events = int(events_match.group(1)) if events_match else 0
    return {
        "presented": presented,
        "flip_events": flip_events,
        "expected_frames": expected_frames,
        "path_ok": "video.flipprobe.path=kms-dumb-buffer-pageflip" in text,
        "ioctl_marker": "video.flipprobe.ioctl=DRM_IOCTL_MODE_PAGE_FLIP" in text,
        "pixel_format": "video.flipprobe.pixel_format=xbgr8888" in text,
        "pass": presented == expected_frames
        and flip_events == expected_frames
        and "video.flipprobe.path=kms-dumb-buffer-pageflip" in text
        and "video.flipprobe.ioctl=DRM_IOCTL_MODE_PAGE_FLIP" in text
        and "video.flipprobe.pixel_format=xbgr8888" in text,
    }


def render_report(result: dict[str, Any]) -> str:
    preflight = result.get("preflight", {}) if isinstance(result.get("preflight"), dict) else {}
    summary = result.get("flipprobe_summary", {}) if isinstance(result.get("flipprobe_summary"), dict) else {}
    return "\n".join([
        "# Native Init V2877 Video Page-Flip Probe Live Validation",
        "",
        "## Summary",
        "",
        f"- Cycle: `{RUN_ID}`",
        "- Track: active Video playback pipeline on the existing KMS display.",
        f"- Decision: `{result.get('decision')}`",
        f"- Result: `{'PASS' if result.get('pass') else 'FAIL'}`",
        f"- Candidate: `{CANDIDATE_TAG}` / `{CANDIDATE_VERSION}`",
        f"- Candidate image: `{rel(CANDIDATE_IMAGE)}`",
        f"- Candidate SHA256: `{CANDIDATE_SHA256}`",
        f"- Rollback attempted: `{int(bool(result.get('rollback_attempted')))}`",
        f"- Rollback health: version_ok=`{int(bool(result.get('rollback_version_ok')))}` selftest_fail0=`{int(bool(result.get('rollback_selftest_fail0')))}`",
        "",
        "## Flipprobe Result",
        "",
        f"- Frames requested: `{preflight.get('flipprobe_frames')}`",
        f"- Presented frames: `{summary.get('presented')}` / `{summary.get('expected_frames')}`",
        f"- Flip events: `{summary.get('flip_events')}` / `{summary.get('expected_frames')}`",
        f"- IOCTL marker: `{int(bool(summary.get('ioctl_marker')))}`",
        f"- Pixel format marker: `{int(bool(summary.get('pixel_format')))}`",
        f"- Page-flip path marker: `{int(bool(summary.get('path_ok')))}`",
        f"- Flipprobe stdout: `{result.get('flipprobe_stdout_path')}`",
        "",
        "## Safety",
        "",
        "- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py`.",
        "- Only the boot partition was flashed; candidate was rolled back to `v2321` after validation.",
        "- The command exercised DRM page-flip on the existing KMS dumb-buffer path only.",
        "- No Venus, KGSL, raw DSI, panel init, backlight, PMIC, PWM, regulator, GPIO, or GDSC path was used.",
        "",
    ])


def dry_run_payload(args: argparse.Namespace, state: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": "v2877-video-flipprobe-live-dry-run" if preflight_ok(state) else "v2877-video-flipprobe-live-blocked",
        "ok": preflight_ok(state),
        "preflight": state,
        "commands": {
            "verify_current": flash_command(ROLLBACK_IMAGE, ROLLBACK_VERSION, ROLLBACK_SHA256, from_native=False) + ["--verify-only"],
            "flash_candidate": flash_command(CANDIDATE_IMAGE, CANDIDATE_VERSION, CANDIDATE_SHA256, from_native=True),
            "video_status": ["video", "status"],
            "flipprobe": ["video", "flipprobe", str(args.frames)],
            "rollback": flash_command(ROLLBACK_IMAGE, ROLLBACK_VERSION, ROLLBACK_SHA256, from_native=True),
        },
    }


def run_live(args: argparse.Namespace, out_dir: Path, state: dict[str, Any]) -> dict[str, Any]:
    steps: list[dict[str, Any]] = []
    candidate_flash_attempted = False
    candidate_flash_ok = False
    result: dict[str, Any] = {
        "decision": "v2877-video-flipprobe-live-started",
        "pass": False,
        "preflight": state,
        "steps": steps,
        "rollback_attempted": False,
        "rollback_version_ok": False,
        "rollback_selftest_fail0": False,
    }
    try:
        base.run_step(
            out_dir,
            steps,
            "verify-current-v2321",
            flash_command(ROLLBACK_IMAGE, ROLLBACK_VERSION, ROLLBACK_SHA256, from_native=False) + ["--verify-only"],
            timeout=args.flash_timeout,
        )
        candidate_flash_attempted = True
        flash = base.run_step(
            out_dir,
            steps,
            "flash-v2876-video-flipprobe",
            flash_command(CANDIDATE_IMAGE, CANDIDATE_VERSION, CANDIDATE_SHA256, from_native=True),
            timeout=args.flash_timeout,
        )
        candidate_flash_ok = flash.get("rc") == 0
        version = base.run_serial_step(out_dir, steps, "candidate-version", ["version"], timeout=90.0, retry_unsafe=True)
        status = base.run_serial_step(out_dir, steps, "candidate-status", ["status"], timeout=90.0, retry_unsafe=True)
        selftest = base.run_serial_step(out_dir, steps, "candidate-selftest", ["selftest", "verbose"], timeout=120.0, retry_unsafe=True)
        video_status = base.run_serial_step(out_dir, steps, "candidate-video-status", ["video", "status"], timeout=90.0, retry_unsafe=True)
        base.run_serial_step(out_dir, steps, "candidate-hide-menu", ["hide"], timeout=45.0, allow_error=True, retry_unsafe=True)
        result["candidate_version_ok"] = CANDIDATE_VERSION in stdout_of(version)
        result["candidate_status_path"] = status.get("stdout_path")
        result["candidate_selftest_fail0"] = selftest_step_ok(selftest)
        result["candidate_video_status_ok"] = "video.status.next_flipprobe=" in stdout_of(video_status)
        if not (result["candidate_version_ok"] and result["candidate_selftest_fail0"] and result["candidate_video_status_ok"]):
            result["decision"] = "v2877-video-flipprobe-candidate-health-failed-before-probe"
            raise RuntimeError("candidate health/video status did not pass")
        flipprobe = base.run_serial_step(
            out_dir,
            steps,
            "candidate-video-flipprobe",
            ["video", "flipprobe", str(args.frames)],
            timeout=args.flipprobe_timeout,
            allow_error=True,
            retry_unsafe=False,
        )
        text = stdout_of(flipprobe)
        result["flipprobe_rc"] = flipprobe.get("rc")
        result["flipprobe_stdout_path"] = flipprobe.get("stdout_path")
        result["flipprobe_summary"] = classify_flipprobe(text, args.frames)
        if flipprobe.get("rc") != 0 or not result["flipprobe_summary"].get("pass"):
            result["decision"] = "v2877-video-flipprobe-failed-before-rollback"
            raise RuntimeError("video flipprobe command did not emit required pass markers")
        after = base.run_serial_step(out_dir, steps, "candidate-selftest-after-flipprobe", ["selftest", "verbose"], timeout=120.0, retry_unsafe=True)
        result["candidate_selftest_after_flipprobe_fail0"] = selftest_step_ok(after)
        if not result["candidate_selftest_after_flipprobe_fail0"]:
            result["decision"] = "v2877-video-flipprobe-post-probe-selftest-failed"
            raise RuntimeError("candidate post-flipprobe selftest did not report fail=0")
        result["decision"] = "v2877-video-flipprobe-live-pass-before-rollback"
        result["pass"] = True
    except Exception as exc:
        if result["decision"] == "v2877-video-flipprobe-live-started":
            result["decision"] = "v2877-video-flipprobe-live-blocked"
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)
    finally:
        if candidate_flash_attempted:
            result["rollback_attempted"] = True
            rollback = base.rollback_v2321(out_dir, steps, from_native=candidate_flash_ok, timeout=args.flash_timeout)
            result["rollback_step_ok"] = bool(rollback.get("success"))
            result["rollback_attempts"] = rollback.get("attempts", [])
            result["rollback_recovery_fallback_used"] = bool(rollback.get("used_recovery_fallback"))
            if rollback.get("success"):
                rollback_version = base.run_serial_step(out_dir, steps, "rollback-version", ["version"], timeout=90.0, retry_unsafe=True, allow_error=True)
                rollback_selftest = base.run_serial_step(out_dir, steps, "rollback-selftest", ["selftest", "verbose"], timeout=120.0, retry_unsafe=True, allow_error=True)
                result["rollback_version_ok"] = ROLLBACK_VERSION in stdout_of(rollback_version)
                result["rollback_selftest_fail0"] = selftest_step_ok(rollback_selftest)
        write_json(out_dir / "result.json", result)
        REPORT_PATH.write_text(render_report(result), encoding="utf-8")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--frames", type=int, default=12)
    parser.add_argument("--flash-timeout", type=float, default=900.0)
    parser.add_argument("--flipprobe-timeout", type=float, default=180.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = ROOT / f"workspace/private/runs/video/v2877-video-flipprobe-live-{now_slug()}"
    out_dir.mkdir(parents=True, exist_ok=True)
    state = preflight_state(args)
    if not args.live:
        payload = dry_run_payload(args, state)
        write_json(out_dir / "dry_run.json", payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if payload["ok"] else 1
    if not preflight_ok(state):
        payload = {
            "decision": "v2877-video-flipprobe-live-preflight-failed-no-flash",
            "pass": False,
            "preflight": state,
        }
        write_json(out_dir / "result.json", payload)
        REPORT_PATH.write_text(render_report(payload), encoding="utf-8")
        print(json.dumps({"decision": payload["decision"], "pass": False, "out_dir": rel(out_dir)}, indent=2, sort_keys=True))
        return 1
    result = run_live(args, out_dir, state)
    final_pass = bool(result.get("pass")) and bool(result.get("rollback_version_ok")) and bool(result.get("rollback_selftest_fail0"))
    print(json.dumps({
        "decision": result.get("decision"),
        "pass": final_pass,
        "out_dir": rel(out_dir),
        "rollback_version_ok": result.get("rollback_version_ok"),
        "rollback_selftest_fail0": result.get("rollback_selftest_fail0"),
    }, indent=2, sort_keys=True))
    return 0 if final_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
