#!/usr/bin/env python3
"""V2806 deploy-first ADSP publication discriminator.

V2805 proved the path works when direct ADSP/card publication happens before
runtime ACDB artifact staging. V2806 flips only that ordering: it stages the
same runtime artifacts first, then runs standalone `audio adsp-boot-once` and
polls for the ASoC card/control. It does not run SET-cal, route, PCM, or play.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from _workspace_bootstrap import repo_root
import native_audio_adsp_kick_no_wait_live_handoff_v2804 as base
import native_audio_card_first_play_live_handoff_v2805 as card_first

ROOT = repo_root()
CYCLE = "V2806"
REPORT_PATH = ROOT / "docs/reports/NATIVE_INIT_V2806_AUDIO_DEPLOY_FIRST_ADSP_PROBE_LIVE_2026-06-19.md"
ADSP_TOKEN = card_first.ADSP_TOKEN


def rel(path: Path | str | None) -> str | None:
    if path is None:
        return None
    p = Path(path)
    try:
        return str(p.resolve().relative_to(ROOT))
    except Exception:
        return str(path)


def now_slug() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y%m%d-%H%M%S")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def stdout_of(step: dict[str, Any] | None) -> str:
    return base.stdout_of(step) if step is not None else ""


def preflight_state() -> dict[str, Any]:
    state = base.preflight_state()
    state["cycle"] = CYCLE
    state["report_path"] = rel(REPORT_PATH)
    state["discriminator"] = "runtime-acdb-deploy-before-standalone-adsp"
    state["live_scope"] = [
        "boot partition only via native_init_flash.py",
        "flash V2804 candidate only; no new boot artifact",
        "stage runtime ACDB artifacts before direct ADSP boot",
        "run direct audio adsp-boot-once after deploy",
        "poll read-only audio status until sound card/control publication",
        "no audio play, no route, no SET-cal ioctl, no PCM",
        "rollback to v2321 and verify selftest fail=0",
    ]
    return state


def preflight_ok(state: dict[str, Any]) -> bool:
    return base.preflight_ok(state)


def live_run(args: argparse.Namespace, state: dict[str, Any]) -> dict[str, Any]:
    if not preflight_ok(state):
        raise SystemExit("refusing live run: preflight failed")
    deploy_plan = read_json(base.DEPLOY_PLAN)
    candidate_sha = str(state["candidate"]["sha256"])
    out_dir = ROOT / f"workspace/private/runs/audio/v2806-audio-deploy-first-adsp-probe-{now_slug()}"
    out_dir.mkdir(parents=True, exist_ok=False)
    native_manifest_path = base.materialize_native_manifest(out_dir, deploy_plan)
    write_json(out_dir / "preflight.json", state)
    steps: list[dict[str, Any]] = []
    result: dict[str, Any] = {
        "cycle": CYCLE,
        "decision": "v2806-audio-deploy-first-adsp-probe-live-started",
        "out_dir": rel(out_dir),
        "candidate_sha256": candidate_sha,
        "candidate_tag": base.CANDIDATE_TAG,
        "candidate_version": base.CANDIDATE_VERSION,
        "native_manifest_path": rel(native_manifest_path),
        "native_manifest_sha256": base.sha256_file(native_manifest_path),
        "direct_adsp_command": f"audio adsp-boot-once {ADSP_TOKEN}",
        "steps": steps,
        "rollback_attempted": False,
        "rollback_recovery_fallback_used": False,
        "rollback_version_ok": False,
        "rollback_selftest_fail0": False,
    }
    candidate_flash_attempted = False
    candidate_flash_ok = False
    try:
        base.run_step(
            out_dir,
            steps,
            "preflight-current-v2321-verify",
            base.flash_command(base.ROLLBACK_IMAGE, base.ROLLBACK_VERSION, base.ROLLBACK_SHA256, from_native=False) + ["--verify-only"],
            timeout=args.flash_timeout,
        )
        current_selftest = base.run_serial_step(
            out_dir,
            steps,
            "preflight-current-selftest",
            ["selftest", "verbose"],
            timeout=120.0,
            retry_unsafe=True,
        )
        result["preflight_current_selftest_fail0"] = base.selftest_step_ok(current_selftest)
        if not result["preflight_current_selftest_fail0"]:
            raise RuntimeError("resident preflight selftest did not report fail=0")

        candidate_flash_attempted = True
        base.run_step(
            out_dir,
            steps,
            "flash-v2804-candidate",
            base.flash_command(base.CANDIDATE_IMAGE, base.CANDIDATE_VERSION, candidate_sha, from_native=True),
            timeout=args.flash_timeout,
        )
        candidate_flash_ok = True

        version = base.run_serial_step(out_dir, steps, "candidate-version", ["version"], timeout=90.0, retry_unsafe=True)
        result["candidate_version_ok"] = base.CANDIDATE_VERSION in stdout_of(version)
        if not result["candidate_version_ok"]:
            raise RuntimeError("candidate version output did not contain expected version")
        base.run_serial_step(out_dir, steps, "candidate-status", ["status"], timeout=90.0, retry_unsafe=True)
        candidate_selftest = base.run_serial_step(
            out_dir,
            steps,
            "candidate-selftest",
            ["selftest", "verbose"],
            timeout=120.0,
            retry_unsafe=True,
        )
        result["candidate_selftest_fail0"] = base.selftest_step_ok(candidate_selftest)
        if not result["candidate_selftest_fail0"]:
            raise RuntimeError("candidate selftest did not report fail=0")

        result["status_before_deploy"] = card_first.capture_audio_status(out_dir, steps, "before-deploy")
        result["runtime_artifacts"] = base.install_runtime_artifacts(args, out_dir, steps, deploy_plan, native_manifest_path)
        result["status_after_deploy_before_adsp"] = card_first.capture_audio_status(out_dir, steps, "after-deploy-before-adsp")
        card_first.hide_auto_menu(out_dir, steps, "before-direct-adsp-after-deploy")
        direct = base.run_serial_step(
            out_dir,
            steps,
            "candidate-audio-direct-adsp-boot-once-after-deploy",
            ["audio", "adsp-boot-once", ADSP_TOKEN],
            timeout=120.0,
            retry_unsafe=False,
            allow_error=True,
        )
        direct_text = stdout_of(direct)
        result["direct_adsp_stdout_path"] = direct.get("stdout_path")
        result["direct_adsp_rc"] = direct.get("rc")
        result["direct_adsp_accepted"] = (
            "audio.adsp_boot_once.write=accepted" in direct_text
            or "audio.adsp_boot_once.refused=already-up-or-sound-present" in direct_text
        )
        if not result["direct_adsp_accepted"]:
            result["decision"] = "v2806-deploy-first-direct-adsp-refused-before-rollback"
            raise RuntimeError("direct ADSP boot after deploy did not report accepted/already-up")

        card_wait = card_first.wait_for_sound_card(
            out_dir,
            steps,
            count=args.card_poll_count,
            interval=args.card_poll_interval,
        )
        result["card_wait"] = card_wait
        result["card_ready_after_deploy_adsp"] = bool(card_wait.get("ready"))
        result["decision"] = (
            "v2806-deploy-first-direct-adsp-card-present-before-rollback"
            if result["card_ready_after_deploy_adsp"]
            else "v2806-deploy-first-direct-adsp-no-card-before-rollback"
        )
        dmesg_tail = base.run_serial_step(
            out_dir,
            steps,
            "candidate-dmesg-audio-tail",
            ["run", "/bin/busybox", "sh", "-c", "dmesg | tail -n 240"],
            timeout=90.0,
            retry_unsafe=True,
            allow_error=True,
        )
        result["dmesg_audio_tail_stdout_path"] = dmesg_tail.get("stdout_path")
    except Exception as exc:
        if result["decision"] == "v2806-audio-deploy-first-adsp-probe-live-started":
            result["decision"] = "v2806-deploy-first-live-blocked"
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)
        raise
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
                result["rollback_version_ok"] = base.ROLLBACK_VERSION in stdout_of(rollback_version)
                result["rollback_selftest_fail0"] = base.selftest_step_ok(rollback_selftest)
        write_json(out_dir / "result.json", result)
        REPORT_PATH.write_text(render_report(result), encoding="utf-8")
    return result


def render_report(result: dict[str, Any]) -> str:
    card_wait = result.get("card_wait") or {}
    before = (result.get("status_before_deploy") or {}).get("summary") or {}
    after_deploy = (result.get("status_after_deploy_before_adsp") or {}).get("summary") or {}
    installed = result.get("runtime_artifacts", {}).get("installed", []) if isinstance(result.get("runtime_artifacts"), dict) else []
    installed_lines = [f"- `{item.get('kind')}` `{item.get('remote')}`" for item in installed] or ["- No runtime artifact installs recorded."]
    return "\n".join([
        "# Native Init V2806 Audio Deploy-First ADSP Probe Live Handoff",
        "",
        "## Summary",
        "",
        f"- Cycle: `{CYCLE}`",
        "- Track: audio core closure gate discriminator.",
        f"- Decision: `{result.get('decision')}`",
        f"- Result directory: `{result.get('out_dir')}`",
        f"- Candidate tag/version: `{base.CANDIDATE_TAG}` / `{base.CANDIDATE_VERSION}`",
        f"- Candidate image SHA256: `{result.get('candidate_sha256')}`",
        f"- Rollback attempted: `{int(bool(result.get('rollback_attempted')))}`",
        f"- Rollback recovery fallback used: `{int(bool(result.get('rollback_recovery_fallback_used')))}`",
        f"- Rollback health: version_ok=`{int(bool(result.get('rollback_version_ok')))}` selftest_fail0=`{int(bool(result.get('rollback_selftest_fail0')))}`",
        "",
        "## Discriminator Evidence",
        "",
        f"- Runtime artifact staging happened before direct ADSP boot: `1`",
        f"- Pre-deploy card/control: `{int(bool(before.get('has_sound_card')))} / {int(bool(before.get('has_sound_control')))}`",
        f"- After-deploy before-ADSP card/control: `{int(bool(after_deploy.get('has_sound_card')))} / {int(bool(after_deploy.get('has_sound_control')))}`",
        f"- Direct ADSP command: `{result.get('direct_adsp_command')}`",
        f"- Direct ADSP rc/accepted: `{result.get('direct_adsp_rc')}` / `{int(bool(result.get('direct_adsp_accepted')))}`",
        f"- Direct ADSP stdout: `{result.get('direct_adsp_stdout_path')}`",
        f"- Card ready after deploy+ADSP: `{int(bool(result.get('card_ready_after_deploy_adsp')))}` after `{card_wait.get('attempts')}` polls",
        f"- Card poll last summary: `{json.dumps((card_wait.get('last') or {}).get('summary') or {}, ensure_ascii=False, sort_keys=True)}`",
        f"- Dmesg audio tail: `{result.get('dmesg_audio_tail_stdout_path')}`",
        "",
        "## Runtime Artifacts",
        "",
        f"- Deploy plan: `{rel(base.DEPLOY_PLAN)}`",
        f"- Native manifest remote path: `{base.REMOTE_NATIVE_MANIFEST}`",
        f"- Native manifest SHA256: `{result.get('native_manifest_sha256')}`",
        *installed_lines,
        "",
        "## Safety",
        "",
        "- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py`.",
        "- Only the boot partition is flashed; runtime ACDB files are staged under `/cache` before direct ADSP boot.",
        "- No forbidden partitions are touched.",
        "- This discriminator does not run `audio play`, route writes, SET-cal ioctls, PCM, or playback.",
        "- Public report is metadata-only; private ACDB payloads and raw command transcripts stay under `workspace/private/`.",
        "",
    ])


def dry_run_payload(args: argparse.Namespace, state: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": "v2806-deploy-first-adsp-probe-live-dry-run",
        "preflight_ok": preflight_ok(state),
        "preflight": state,
        "commands": {
            "verify_current": base.flash_command(base.ROLLBACK_IMAGE, base.ROLLBACK_VERSION, base.ROLLBACK_SHA256, from_native=False) + ["--verify-only"],
            "flash_candidate": base.flash_command(base.CANDIDATE_IMAGE, base.CANDIDATE_VERSION, str(state["candidate"].get("sha256") or ""), from_native=True),
            "install_count": state.get("deploy_artifact_count", 0) + 1,
            "direct_adsp_boot_after_deploy": ["audio", "adsp-boot-once", ADSP_TOKEN],
            "card_poll": ["audio", "adsp-status"],
            "rollback": base.flash_command(base.ROLLBACK_IMAGE, base.ROLLBACK_VERSION, base.ROLLBACK_SHA256, from_native=True),
        },
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--run-live", action="store_true")
    parser.add_argument("--bridge-host", default="127.0.0.1")
    parser.add_argument("--bridge-port", type=int, default=54321)
    parser.add_argument("--device-ip", default="192.168.7.2")
    parser.add_argument("--host-ip", default="192.168.7.1")
    parser.add_argument("--host-prefix", type=int, default=24)
    parser.add_argument("--tcp-port", type=int, default=2325)
    parser.add_argument("--command-timeout", type=float, default=60.0)
    parser.add_argument("--tcp-timeout", type=float, default=30.0)
    parser.add_argument("--device-toolbox", default=base.tiny_live.DEFAULT_DEVICE_TOOLBOX)
    parser.add_argument("--flash-timeout", type=float, default=900.0)
    parser.add_argument("--transfer-port", type=int, default=18351)
    parser.add_argument("--transfer-delay", type=float, default=1.0)
    parser.add_argument("--transfer-timeout", type=float, default=120.0)
    parser.add_argument("--repair-host-ncm", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--ncm-setup-timeout", type=float, default=120.0)
    parser.add_argument("--ncm-interface-timeout", type=float, default=20.0)
    parser.add_argument("--ncm-setup-sudo", default="sudo -n")
    parser.add_argument("--inventory-transport", choices=("auto", "tcpctl", "serial"), default="auto")
    parser.add_argument("--card-poll-count", type=int, default=35)
    parser.add_argument("--card-poll-interval", type=float, default=2.0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    state = preflight_state()
    if args.dry_run:
        print(json.dumps(dry_run_payload(args, state), ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if preflight_ok(state) else 2
    result = live_run(args, state)
    print(json.dumps({
        "decision": result.get("decision"),
        "out_dir": result.get("out_dir"),
        "card_ready_after_deploy_adsp": result.get("card_ready_after_deploy_adsp"),
        "rollback_version_ok": result.get("rollback_version_ok"),
        "rollback_selftest_fail0": result.get("rollback_selftest_fail0"),
    }, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if (
        result.get("card_ready_after_deploy_adsp")
        and result.get("rollback_version_ok")
        and result.get("rollback_selftest_fail0")
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
