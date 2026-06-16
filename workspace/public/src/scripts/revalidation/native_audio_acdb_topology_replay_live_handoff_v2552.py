#!/usr/bin/env python3
"""V2552 exact-gated native ACDB topology replay live handoff with ION devnode materialization.

Default mode is dry-run. Live mode reuses the V2334 ADSP+/dev/snd materialization
path, stages the V2549 execute helper plus the pinned V2547 payload, applies the
V2407 app-type and V2377 speaker route, starts topology replay, runs one bounded
PCM probe during the helper hold window, captures deallocate evidence, resets the
route, and rolls back to V2321.
"""

from __future__ import annotations

import argparse
import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import native_audio_acdb_topology_replay_live_handoff_v2550 as planmod
import native_audio_speaker_pilot_live_handoff_v2379 as speaker
import native_audio_snd_nodes_preflight_handoff_v2335 as snd

RUN_ID = "V2552"
BUILD_TAG = "v2552-audio-acdb-topology-replay-ion-live-handoff"
APPROVAL_PHRASE = planmod.FUTURE_APPROVAL_PHRASE
DMESG_TAIL_LINE_COUNT = 260


def rel(path: Path) -> str:
    return snd.rel(path)


def now_slug() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y%m%d-%H%M%S")


def stdout_of(step: dict[str, Any]) -> str:
    return snd.stdout_of(step)


def write_json(path: Path, payload: Any) -> None:
    snd.write_json(path, payload)


def args_for_plan(args: argparse.Namespace) -> argparse.Namespace:
    return argparse.Namespace(**vars(args))


def verify_live_approval(args: argparse.Namespace) -> None:
    if args.approval != APPROVAL_PHRASE:
        raise SystemExit("refusing live run: exact --approval phrase required:\n" + APPROVAL_PHRASE)


def dry_run_payload(args: argparse.Namespace) -> dict[str, Any]:
    payload = planmod.plan(args_for_plan(args))
    payload.update(
        {
            "decision": "v2552-acdb-topology-replay-ion-live-handoff-dry-run",
            "run_id": RUN_ID,
            "build_tag": BUILD_TAG,
            "source_plan_run_id": planmod.RUN_ID,
            "live_runner_implemented": True,
            "live_runner_default": "dry-run",
            "live_approval_phrase": APPROVAL_PHRASE,
        }
    )
    return payload


def run_selftest_fail0_observation(args: argparse.Namespace, out_dir: Path, steps: list[dict[str, Any]], name: str) -> dict[str, Any]:
    last_step: dict[str, Any] | None = None
    for attempt in range(1, 4):
        step = snd.run_a90ctl_observation(
            args,
            out_dir,
            steps,
            f"{name}-content-attempt-{attempt}",
            ["selftest", "verbose"],
            timeout=120.0,
            attempts=1,
            delay_sec=1.0,
        )
        last_step = step
        if snd.selftest_ok(stdout_of(step)):
            return step
    raise RuntimeError(f"{name} did not report fail=0 after content retries: {last_step.get('stdout_path') if last_step else 'no-step'}")

def raw_tool_path(name: str, args: argparse.Namespace) -> Path:
    raw_manifest = speaker.load_raw_tinyalsa_manifest(args.tinyalsa_manifest)
    return speaker.raw_tool_path(raw_manifest, name)


def pcm_probe_path(args: argparse.Namespace) -> Path:
    manifest = speaker.load_pcm_probe_manifest(args.pcm_probe_manifest)
    return speaker.pcm_probe_tool_path(manifest)


def install_runtime_artifacts(args: argparse.Namespace, out_dir: Path, steps: list[dict[str, Any]], pcm_path: Path) -> dict[str, Any]:
    readiness = speaker.tiny_live.probe_transfer_readiness(args, out_dir, steps)
    selected = readiness["selected_transport"]
    control_channel = "tcpctl" if selected == "tcpctl" else "bridge"
    artifacts = [
        ("helper", args.helper, planmod.REMOTE_HELPER, args.transfer_port),
        ("payload", args.payload, planmod.REMOTE_PAYLOAD, args.transfer_port + 1),
        ("tinymix", raw_tool_path("tinymix", args), planmod.REMOTE_TINYMIX, args.transfer_port + 2),
        ("pcm_probe", pcm_probe_path(args), planmod.REMOTE_PCM_PROBE, args.transfer_port + 3),
        ("pilot_wav", pcm_path, planmod.REMOTE_PCM, args.transfer_port + 4),
    ]
    result: dict[str, Any] = {
        "transfer_readiness": readiness,
        "selected_transport": selected,
        "control_channel": control_channel,
        "artifacts": {},
    }
    for name, local_path, remote_path, port in artifacts:
        step = speaker.run_host_step(
            out_dir,
            steps,
            f"install-{name}",
            speaker.tiny_live.install_command(args, local_path, remote_path, port, control_channel=control_channel),
            timeout=args.transfer_timeout + 60.0,
        )
        result["artifacts"][name] = {"ok": bool(step.get("ok")), "remote": remote_path, "stdout_path": step.get("stdout_path")}
    return result


def run_remote_shell(args: argparse.Namespace, out_dir: Path, steps: list[dict[str, Any]], name: str, script: str, *, timeout: float, allow_error: bool = False) -> dict[str, Any]:
    return speaker.run_tool_command(
        args,
        out_dir,
        steps,
        name,
        [args.device_busybox, "sh", "-c", script],
        use_tcpctl=False,
        timeout=timeout,
        allow_error=allow_error,
    )


def cleanup_script(wait_sec: int) -> str:
    return "\n".join(
        [
            "set -u",
            "i=0",
            f"while [ $i -lt {int(wait_sec)} ]; do",
            f"  if grep -q 'AUDIO_DEALLOCATE_CALIBRATION' {planmod.REMOTE_HELPER_STDERR} 2>/dev/null; then break; fi",
            "  if ! pgrep -f a90_acdb_replay_execute_v2549 >/dev/null 2>&1; then break; fi",
            "  i=$((i+1))",
            "  sleep 1",
            "done",
            planmod.remote_wait_cleanup_script(),
        ]
    )


def runtime_cleanup_script() -> str:
    return "\n".join(
        [
            "set -u",
            f"rm -rf {planmod.REMOTE_DIR}",
            "echo A90_ACDB_REPLAY_RUNTIME_CLEANUP_DONE",
        ]
    )


def run_acdb_replay_and_pcm(args: argparse.Namespace, out_dir: Path, steps: list[dict[str, Any]], state: dict[str, Any]) -> dict[str, Any]:
    pcm_path = out_dir / "pilot_48k_s16le_stereo_0p02_1s.wav"
    pcm = speaker.generate_pilot_wav(pcm_path, duration_ms=args.duration_ms, amplitude=args.amplitude)
    result: dict[str, Any] = {
        "pilot_wav": pcm,
        "install": {},
        "route_apply": [],
        "route_reset": [],
        "playback_attempted": False,
        "helper_started": False,
    }
    install = install_runtime_artifacts(args, out_dir, steps, pcm_path)
    result["install"] = install
    use_tcpctl = install["selected_transport"] == "tcpctl"
    route_use_tcpctl = args.route_transport == "tcpctl"
    plan = state["v2550_plan"]
    baseline_step: dict[str, Any] | None = None
    post_reset_step: dict[str, Any] | None = None
    helper_started = False
    deferred_error: Exception | None = None
    try:
        try:
            baseline_step = speaker.run_tool_command(
                args,
                out_dir,
                steps,
                "tinymix-all-values-before-acdb-replay",
                [planmod.REMOTE_TINYMIX, "-D", str(args.card), "--all-values"],
                use_tcpctl=use_tcpctl,
                timeout=args.mixer_timeout,
                allow_error=True,
            )
            result["baseline_snapshot"] = {"ok": bool(baseline_step.get("ok")), "stdout_path": baseline_step.get("stdout_path")}
            if not baseline_step.get("ok"):
                raise RuntimeError(f"baseline tinymix snapshot failed: {baseline_step.get('remote_tool_result')}")
            app_type = plan.get("app_type_command")
            if app_type:
                step = speaker.run_tool_command(
                    args,
                    out_dir,
                    steps,
                    app_type["name"],
                    [str(part) for part in app_type["argv"]],
                    use_tcpctl=route_use_tcpctl,
                    timeout=args.mixer_timeout,
                    allow_error=True,
                    failure_markers=("Invalid mixer control",),
                )
                result["app_type_gate"] = {"ok": bool(step.get("ok")), "stdout_path": step.get("stdout_path"), "remote_tool_result": step.get("remote_tool_result")}
                if not step.get("ok"):
                    raise RuntimeError(f"App Type gate failed: {step.get('remote_tool_result')}")
            for command in plan["route_apply_commands"]:
                step = speaker.run_tool_command(
                    args,
                    out_dir,
                    steps,
                    command["name"],
                    [str(part) for part in command["argv"]],
                    use_tcpctl=route_use_tcpctl,
                    timeout=args.mixer_timeout,
                    allow_error=True,
                    failure_markers=("Invalid mixer control",),
                )
                result["route_apply"].append({"name": command["name"], "ok": bool(step.get("ok")), "stdout_path": step.get("stdout_path"), "remote_tool_result": step.get("remote_tool_result")})
                if not step.get("ok"):
                    raise RuntimeError(f"route apply failed: {command['name']}: {step.get('remote_tool_result')}")
            replay_step = run_remote_shell(
                args,
                out_dir,
                steps,
                "acdb-topology-replay-start-wait-set-ok",
                planmod.remote_replay_script(args.hold_sec),
                timeout=args.replay_start_timeout,
                allow_error=True,
            )
            result["replay_start"] = {"ok": bool(replay_step.get("ok")), "stdout_path": replay_step.get("stdout_path"), "remote_tool_result": replay_step.get("remote_tool_result")}
            if not replay_step.get("ok"):
                raise RuntimeError(f"ACDB replay did not reach SET ok: {replay_step.get('remote_tool_result')}")
            helper_started = True
            result["helper_started"] = True
            result["playback_attempted"] = True
            playback = plan["playback_command"]
            playback_step = speaker.run_tool_command(
                args,
                out_dir,
                steps,
                playback["name"],
                [str(part) for part in playback["argv"]],
                use_tcpctl=use_tcpctl,
                timeout=args.playback_timeout,
                allow_error=True,
                failure_markers=("Error playing sample", "A90_PCM_PROBE_WRITE_ERROR", "A90_PCM_PROBE_PCM_OPEN_ERROR"),
            )
            result["playback"] = {"ok": bool(playback_step.get("ok")), "stdout_path": playback_step.get("stdout_path"), "remote_tool_result": playback_step.get("remote_tool_result")}
            if not playback_step.get("ok"):
                raise RuntimeError(f"PCM probe failed: {playback_step.get('remote_tool_result')}")
        except Exception as exc:  # noqa: BLE001
            deferred_error = exc
            if result.get("playback_attempted"):
                dmesg_step = run_remote_shell(args, out_dir, steps, "dmesg-after-acdb-playback-failure-before-reset", f"dmesg | tail -n {DMESG_TAIL_LINE_COUNT}", timeout=args.mixer_timeout, allow_error=True)
                result["playback_failure_dmesg"] = {"ok": bool(dmesg_step.get("ok")), "stdout_path": dmesg_step.get("stdout_path")}
    finally:
        if helper_started:
            cleanup = run_remote_shell(
                args,
                out_dir,
                steps,
                "acdb-helper-wait-deallocate-and-cleanup",
                cleanup_script(args.hold_sec + 15),
                timeout=args.hold_sec + 30,
                allow_error=True,
            )
            result["helper_cleanup"] = {"ok": bool(cleanup.get("ok")), "stdout_path": cleanup.get("stdout_path"), "remote_tool_result": cleanup.get("remote_tool_result")}
            if not cleanup.get("ok") and deferred_error is None:
                deferred_error = RuntimeError(f"ACDB helper cleanup/deallocate failed: {cleanup.get('remote_tool_result')}")
        for command in plan["route_reset_commands"]:
            step = speaker.run_tool_command(
                args,
                out_dir,
                steps,
                command["name"],
                [str(part) for part in command["argv"]],
                use_tcpctl=route_use_tcpctl,
                timeout=args.mixer_timeout,
                allow_error=True,
                failure_markers=("Invalid mixer control",),
            )
            result["route_reset"].append({"name": command["name"], "ok": bool(step.get("ok")), "stdout_path": step.get("stdout_path"), "remote_tool_result": step.get("remote_tool_result")})
        post_reset_step = speaker.run_tool_command(
            args,
            out_dir,
            steps,
            "tinymix-all-values-after-acdb-reset",
            [planmod.REMOTE_TINYMIX, "-D", str(args.card), "--all-values"],
            use_tcpctl=use_tcpctl,
            timeout=args.mixer_timeout,
            allow_error=True,
        )
        result["post_reset_snapshot"] = {"ok": bool(post_reset_step.get("ok")), "stdout_path": post_reset_step.get("stdout_path")}
        runtime_cleanup = run_remote_shell(
            args,
            out_dir,
            steps,
            "runtime-dir-cleanup-after-reset",
            runtime_cleanup_script(),
            timeout=args.mixer_timeout,
            allow_error=True,
        )
        result["runtime_cleanup"] = {"ok": bool(runtime_cleanup.get("ok")), "stdout_path": runtime_cleanup.get("stdout_path"), "remote_tool_result": runtime_cleanup.get("remote_tool_result")}
    if baseline_step and baseline_step.get("ok") and post_reset_step and post_reset_step.get("ok"):
        result["route_reset_verification"] = speaker.route_reset_verification(
            speaker.step_text(baseline_step), speaker.step_text(post_reset_step), plan["route_reset_commands"]
        )
        if not result["route_reset_verification"].get("ok") and deferred_error is None:
            deferred_error = RuntimeError("route reset verification failed")
    if not all(item.get("ok") for item in result["route_reset"]) and deferred_error is None:
        deferred_error = RuntimeError("one or more route reset commands failed")
    if deferred_error is not None:
        result["blocked_error_type"] = type(deferred_error).__name__
        result["blocked_error"] = str(deferred_error)
        raise speaker.SpeakerPilotBlocked(str(deferred_error), result) from deferred_error
    return result


def live_run(args: argparse.Namespace, state: dict[str, Any]) -> dict[str, Any]:
    verify_live_approval(args)
    if not state.get("ok"):
        raise SystemExit("refusing live run: V2552 dry-run preflight failed")
    out_dir = snd.ROOT / f"workspace/private/runs/audio/v2552-acdb-topology-replay-ion-{now_slug()}"
    out_dir.mkdir(parents=True, exist_ok=False)
    steps: list[dict[str, Any]] = []
    result: dict[str, Any] = {
        "decision": "v2552-acdb-topology-replay-ion-live-started",
        "out_dir": rel(out_dir),
        "preflight": state,
        "steps": steps,
        "rolled_back": False,
    }
    write_json(out_dir / "preflight.json", state)
    candidate_flashed = False
    try:
        speaker.run_host_step(out_dir, steps, "preflight-current-v2321-verify", snd.flash_command(snd.ROLLBACK_IMAGE, snd.ROLLBACK_VERSION, snd.ROLLBACK_SHA256, from_native=False) + ["--verify-only"], timeout=args.flash_timeout)
        current_selftest = run_selftest_fail0_observation(args, out_dir, steps, "preflight-current-selftest")
        speaker.run_host_step(out_dir, steps, "flash-v2334-candidate", snd.flash_command(snd.CANDIDATE_IMAGE, snd.CANDIDATE_VERSION, snd.CANDIDATE_SHA256, from_native=True), timeout=args.flash_timeout)
        candidate_flashed = True
        version = snd.run_a90ctl_observation(args, out_dir, steps, "candidate-version", ["version"], timeout=90.0)
        if snd.CANDIDATE_VERSION not in stdout_of(version):
            raise RuntimeError("candidate version output did not contain expected version")
        snd.run_a90ctl_observation(args, out_dir, steps, "candidate-status", ["status"], timeout=90.0)
        candidate_selftest = run_selftest_fail0_observation(args, out_dir, steps, "candidate-selftest")
        pre_adsp = snd.run_a90ctl_observation(args, out_dir, steps, "candidate-audio-adsp-status-before", ["audio", "adsp-status"], timeout=90.0)
        pre_snd = snd.run_a90ctl_observation(args, out_dir, steps, "candidate-audio-snd-status-before", ["audio", "snd-status"], timeout=90.0)
        result["initial_audio"] = snd.classify_audio_status(stdout_of(pre_adsp) + "\n" + stdout_of(pre_snd))
        if not (result["initial_audio"]["has_audio_card"] and result["initial_audio"]["has_sound_class_control"]):
            snd.run_menu_settle_step(out_dir, steps, "settle-before-adsp-boot-once", args)
            adsp_boot_step = snd.run_serial_transport_step(out_dir, steps, "candidate-adsp-boot-once", args, ["audio", "adsp-boot-once", snd.ADSP_TOKEN], timeout=90.0, retry_observation=False, allow_error=True)
            result["adsp_boot_once"] = speaker.classify_adsp_boot_once_step(adsp_boot_step)
            if not result["adsp_boot_once"].get("accepted"):
                raise RuntimeError(f"candidate ADSP boot-once did not show accepted marker: {result['adsp_boot_once']}")
        result["card_wait"] = snd.wait_for_audio_card(args, out_dir, steps)
        snd.run_menu_settle_step(out_dir, steps, "settle-before-snd-materialize-once", args)
        materialize = snd.run_serial_transport_step(out_dir, steps, "snd-materialize-once", args, ["audio", "snd-materialize-once", snd.SND_TOKEN], timeout=90.0, retry_observation=False)
        result["materialize_tail"] = stdout_of(materialize)[-4000:]
        after_materialize = snd.run_a90ctl_observation(args, out_dir, steps, "snd-status-after-materialize", ["audio", "snd-status"], timeout=90.0)
        after = snd.classify_audio_status(stdout_of(after_materialize))
        result["after_materialize"] = after
        if not (after["has_dev_snd_control"] and after["has_dev_snd_pcm"]):
            raise RuntimeError("materialization did not produce control+pcm /dev/snd nodes")
        try:
            result["acdb_topology_replay"] = run_acdb_replay_and_pcm(args, out_dir, steps, state)
        except speaker.SpeakerPilotBlocked as exc:
            result["acdb_topology_replay"] = exc.partial_result
            raise
        final_candidate_selftest = run_selftest_fail0_observation(args, out_dir, steps, "candidate-selftest-after-acdb-replay")
        result["decision"] = "v2552-acdb-topology-replay-ion-live-pass-before-rollback"
    except Exception as exc:  # noqa: BLE001
        result["decision"] = "v2552-acdb-topology-replay-ion-live-blocked"
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)
        raise
    finally:
        if candidate_flashed:
            rollback_record = speaker.run_host_step(out_dir, steps, "rollback-v2321", snd.flash_command(snd.ROLLBACK_IMAGE, snd.ROLLBACK_VERSION, snd.ROLLBACK_SHA256, from_native=True), timeout=args.flash_timeout, allow_error=True)
            result["rolled_back"] = bool(rollback_record.get("ok"))
            try:
                rollback_version = snd.run_a90ctl_observation(args, out_dir, steps, "rollback-version", ["version"], timeout=90.0)
                rollback_selftest = run_selftest_fail0_observation(args, out_dir, steps, "rollback-selftest")
                result["rollback_version_ok"] = snd.ROLLBACK_VERSION in stdout_of(rollback_version)
                result["rollback_selftest_fail0"] = snd.selftest_ok(stdout_of(rollback_selftest))
            except Exception as exc:  # noqa: BLE001
                result["rollback_health_error"] = str(exc)
        write_json(out_dir / "result.json", result)
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--run-live", action="store_true")
    parser.add_argument("--approval", default="")
    parser.add_argument("--manifest-path", type=Path, default=snd.ROOT / "workspace/private/builds/audio" / BUILD_TAG / "manifest.json")
    parser.add_argument("--helper", type=Path, default=planmod.DEFAULT_HELPER)
    parser.add_argument("--payload", type=Path, default=planmod.v2549.STABLE_PAYLOAD)
    parser.add_argument("--hold-sec", type=int, default=10)
    parser.add_argument("--replay-start-timeout", type=float, default=45.0)
    parser.add_argument("--tinyalsa-manifest", type=Path, default=speaker.inv.MANIFEST)
    parser.add_argument("--pcm-probe-manifest", type=Path, default=speaker.pcm_probe.DEFAULT_MANIFEST)
    parser.add_argument("--evidence-dir", type=Path, default=speaker.recipe.DEFAULT_EVIDENCE_DIR)
    parser.add_argument("--bridge-host", default="127.0.0.1")
    parser.add_argument("--bridge-port", type=int, default=54321)
    parser.add_argument("--device-ip", default="192.168.7.2")
    parser.add_argument("--host-ip", default="192.168.7.1")
    parser.add_argument("--host-prefix", type=int, default=24)
    parser.add_argument("--tcp-port", type=int, default=2325)
    parser.add_argument("--command-timeout", type=float, default=60.0)
    parser.add_argument("--tcp-timeout", type=float, default=30.0)
    parser.add_argument("--device-toolbox", default=speaker.DEFAULT_DEVICE_TOOLBOX)
    parser.add_argument("--device-busybox", default=speaker.DEFAULT_DEVICE_BUSYBOX)
    parser.add_argument("--flash-timeout", type=float, default=900.0)
    parser.add_argument("--card-timeout", type=float, default=70.0)
    parser.add_argument("--poll-interval", type=float, default=2.0)
    parser.add_argument("--menu-settle-sec", type=float, default=1.0)
    parser.add_argument("--transfer-port", type=int, default=18240)
    parser.add_argument("--transfer-delay", type=float, default=1.0)
    parser.add_argument("--transfer-timeout", type=float, default=120.0)
    parser.add_argument("--repair-host-ncm", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--ncm-setup-timeout", type=float, default=120.0)
    parser.add_argument("--ncm-interface-timeout", type=float, default=20.0)
    parser.add_argument("--ncm-setup-sudo", default="sudo -n")
    parser.add_argument("--inventory-transport", choices=("auto", "tcpctl", "serial"), default="auto")
    parser.add_argument("--card", type=int, default=0)
    parser.add_argument("--route-transport", choices=("serial", "tcpctl"), default="serial")
    parser.add_argument("--mixer-timeout", type=float, default=45.0)
    parser.add_argument("--playback-timeout", type=float, default=25.0)
    parser.add_argument("--duration-ms", type=int, default=speaker.DEFAULT_DURATION_MS)
    parser.add_argument("--amplitude", type=float, default=speaker.DEFAULT_AMPLITUDE)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    state = dry_run_payload(args)
    state["v2550_plan"] = planmod.plan(args)
    write_json(args.manifest_path, state)
    if args.dry_run:
        print(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if state.get("ok") else 2
    result = live_run(args, copy.deepcopy(state))
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.get("decision") == "v2552-acdb-topology-replay-ion-live-pass-before-rollback" else 1


if __name__ == "__main__":
    raise SystemExit(main())
