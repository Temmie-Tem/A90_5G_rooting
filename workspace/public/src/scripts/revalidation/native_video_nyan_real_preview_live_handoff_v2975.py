#!/usr/bin/env python3
"""V2975 live validation for the real Nyan Cat pal8-rle Player HUD preview.

This runner flashes the V2974 Nyan preset image, seeds the private V2973
``A90VSTR2 pal8-rle`` stream and matching bounded PCM audio into runtime cache,
runs ``video demo nyan status|verify|play`` with A/V sync, then rolls back to
the v2321 clean USB-identity checkpoint.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import native_audio_tinyalsa_inventory_live_handoff_v2349 as tiny_live
import native_av_pcm_video_corun_live_handoff_v2882 as av_live
import native_video_gray8_stream_live_handoff_v2893 as video_live

base = video_live.base

RUN_ID = "V2975"
BUILD_TAG = "v2975-nyan-real-preview-live"
DECISION_PREFIX = "v2975-nyan-real-preview"
REPORT_PATH = video_live.ROOT / "docs/reports/NATIVE_INIT_V2975_NYAN_REAL_PREVIEW_LIVE_2026-06-20.md"

CANDIDATE_IMAGE = video_live.ROOT / "workspace/private/inputs/boot_images/boot_linux_v2974_nyan_real_preset.img"
CANDIDATE_VERSION = "0.10.59"
CANDIDATE_TAG = "v2974-nyan-real-preset"
CANDIDATE_SHA256 = "e6ac9bc08829c465e2126654b1f7020eab5e5cfb8491e7fc9d9a297e3b514410"

ASSET_ROOT = video_live.ROOT / "workspace/private/demo-assets/video/v2973-nyancat-pal8-rle-preview"
LOCAL_MANIFEST = ASSET_ROOT / "video-stream/manifest.json"
LOCAL_STREAM = ASSET_ROOT / "video-stream/frames.a90vstr"
LOCAL_AUDIO = ASSET_ROOT / "audio/audio.s16le"

NYAN_ASSET_ID = "nyancat-v2973-pal8-rle-preview"
NYAN_SHA256 = "9a8d91956218acf674b7d99d421467effec442fdde1dbbea8635b8f47085c573"
NYAN_AUDIO_SHA256 = "4c3774553195c04166a3a83de793253696a5bee60afe83a04219419fc28e43de"
NYAN_FRAMES = 300
NYAN_WIDTH = 540
NYAN_HEIGHT = 360
NYAN_FORMAT = "pal8-rle"
PRESET_NAME = "nyan"
PRESENT_MODE = "setcrtc"
LAYOUT = "player-hud"

SYNC_STATUS_PATH = "/cache/a90-audio-play/status.txt"
SYNC_WAIT_MS = 60000
SYNC_START_OFFSET_MS = 450
AUDIO_PROFILE = av_live.PROFILE
AUDIO_MANIFEST = av_live.BUNDLED_REMOTE_MANIFEST
AUDIO_DURATION_MS = 10000
AUDIO_AMPLITUDE_MILLI = 150
AUDIO_PCM_GAIN_MILLI = 780
REMOTE_PLAY_LOG = av_live.REMOTE_PLAY_LOG
REMOTE_AUDIO_DIR = "/cache/a90-runtime/pkg/av/v2973/audio"
REMOTE_AUDIO_PCM = f"{REMOTE_AUDIO_DIR}/nyancat.s16le"

video_live.RUN_ID = RUN_ID
video_live.BUILD_TAG = BUILD_TAG
video_live.REPORT_TITLE = "Native Init V2975 Nyan Real Preview Live Validation"
video_live.DECISION_PREFIX = DECISION_PREFIX
video_live.CANDIDATE_IMAGE = CANDIDATE_IMAGE
video_live.CANDIDATE_VERSION = CANDIDATE_VERSION
video_live.CANDIDATE_TAG = CANDIDATE_TAG
video_live.CANDIDATE_SHA256 = CANDIDATE_SHA256
video_live.REPORT_PATH = REPORT_PATH
video_live.REMOTE_DIR = "/mnt/sdext/a90/runtime/video/v2975"
video_live.REMOTE_MANIFEST = f"{video_live.REMOTE_DIR}/manifest.json"
video_live.REMOTE_STREAM = f"{video_live.REMOTE_DIR}/frames.a90vstr"


def now_slug() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y%m%d-%H%M%S")


def stdout_of(step: dict[str, Any] | None) -> str:
    if not step:
        return ""
    return video_live.stdout_of(step)


def marker_int(text: str, marker: str) -> int | None:
    match = re.search(rf"(?:^|\b){re.escape(marker)}=(-?\d+)\b", text, re.MULTILINE)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def all_true(mapping: dict[str, Any]) -> bool:
    return all(bool(value) for value in mapping.values())


def read_asset_manifest() -> dict[str, Any]:
    return json.loads(LOCAL_MANIFEST.read_text(encoding="utf-8"))


def file_state(path: Path, expected_sha: str | None = None) -> dict[str, Any]:
    state: dict[str, Any] = {"path": video_live.rel(path), "exists": path.exists()}
    if path.exists():
        state["size"] = path.stat().st_size
        digest = video_live.sha256_file(path)
        state["sha256"] = digest
        if expected_sha:
            state["sha256_ok"] = digest == expected_sha
    elif expected_sha:
        state["sha256_ok"] = False
    return state


def preflight_state(args: argparse.Namespace) -> dict[str, Any]:
    manifest_payload: dict[str, Any] = {}
    manifest_ok = False
    try:
        manifest_payload = read_asset_manifest()
        video = manifest_payload.get("video", {}) if isinstance(manifest_payload.get("video"), dict) else {}
        manifest_ok = bool(
            manifest_payload.get("asset_id") == NYAN_ASSET_ID
            and video.get("sha256") == NYAN_SHA256
            and video.get("format") == NYAN_FORMAT
            and int(video.get("stream_version", -1)) == 2
            and int(video.get("frame_count", -1)) == NYAN_FRAMES
            and int(video.get("width", -1)) == NYAN_WIDTH
            and int(video.get("height", -1)) == NYAN_HEIGHT
        )
    except Exception as exc:  # noqa: BLE001 - report precise preflight failure
        manifest_payload = {"error": f"{type(exc).__name__}: {exc}"}
    return {
        "run_id": RUN_ID,
        "candidate": file_state(CANDIDATE_IMAGE, CANDIDATE_SHA256),
        "rollback": file_state(video_live.ROLLBACK_IMAGE, video_live.ROLLBACK_SHA256),
        "fallback_v2237": file_state(video_live.FALLBACK_V2237, video_live.FALLBACK_V2237_SHA256),
        "fallback_v48": file_state(video_live.FALLBACK_V48),
        "flash_helper": file_state(base.FLASH),
        "asset_manifest": file_state(LOCAL_MANIFEST),
        "asset_stream": file_state(LOCAL_STREAM, NYAN_SHA256),
        "asset_audio": file_state(LOCAL_AUDIO, NYAN_AUDIO_SHA256),
        "asset_manifest_ok": manifest_ok,
        "asset_manifest_payload": manifest_payload,
        "remote_cache_root": video_live.REMOTE_CACHE_ROOT,
        "remote_cache_dir": video_live.remote_cache_dir(NYAN_SHA256),
        "remote_audio_pcm": REMOTE_AUDIO_PCM,
        "play_frames": int(args.frames),
        "present_mode": PRESENT_MODE,
        "layout": LAYOUT,
        "sync_status_path": SYNC_STATUS_PATH,
        "hard_boundary": [
            "boot partition only via native_init_flash.py",
            "rollback to v2321 and verify selftest fail=0",
            "private Nyan raw stream/audio remain untracked",
            "KMS dumb-buffer setcrtc/player-HUD path only",
            "no Venus/GPU/raw DSI/panel init/backlight/PMIC/PWM/regulator/GPIO/GDSC",
            "audio amplitude cap remains <=0.2",
        ],
    }


def preflight_ok(state: dict[str, Any]) -> bool:
    return bool(
        state["candidate"].get("sha256_ok")
        and state["rollback"].get("sha256_ok")
        and state["fallback_v2237"].get("sha256_ok")
        and state["fallback_v48"].get("exists")
        and state["flash_helper"].get("exists")
        and state["asset_manifest"].get("exists")
        and state["asset_stream"].get("sha256_ok")
        and state["asset_audio"].get("sha256_ok")
        and state.get("asset_manifest_ok")
    )


def fixture_from_asset() -> dict[str, Any]:
    manifest = read_asset_manifest()
    video = manifest["video"]
    return {
        "asset_id": NYAN_ASSET_ID,
        "manifest_path": video_live.rel(LOCAL_MANIFEST),
        "stream_path": video_live.rel(LOCAL_STREAM),
        "sha256": NYAN_SHA256,
        "format": str(video["format"]),
        "frames": int(video["frame_count"]),
        "width": int(video["width"]),
        "height": int(video["height"]),
        "stride": 0,
        "frame_bytes": int(video.get("max_payload_bytes", 0)),
        "manifest_sha256": video_live.sha256_file(LOCAL_MANIFEST),
        "stream_size": LOCAL_STREAM.stat().st_size,
        "stream_version": int(video.get("stream_version", 2)),
        "palette_count": int(video.get("palette_count", 0)),
        "max_payload_bytes": int(video.get("max_payload_bytes", 0)),
        "encoded_payload_bytes": int(video.get("encoded_payload_bytes", 0)),
        "compression_ratio_milli": int(video.get("compression_ratio_milli", 0)),
    }


def cache_status_summary(text: str) -> dict[str, Any]:
    return {
        "manifest_ok": "video.cache.manifest_ok=1" in text,
        "stream_exists": "video.cache.stream_exists=1" in text,
        "stream_size_match": "video.cache.stream_size_match=1" in text,
        "frames_ok": f"video.cache.frames={NYAN_FRAMES}" in text,
        "format_ok": f"video.cache.format={NYAN_FORMAT}" in text,
        "sha_ok": f"video.cache.sha256={NYAN_SHA256}" in text,
        "size_ok": f"video.cache.size={NYAN_WIDTH}x{NYAN_HEIGHT}" in text,
        "v2_size_sentinel": "video.cache.stream_expected_size=0" in text,
    }


def cache_verify_summary(text: str) -> dict[str, Any]:
    return {
        "sha_checked": "video.cache.verify.sha256_checked=1" in text,
        "sha_match": "video.cache.verify.sha256_match=1" in text,
        "expected_sha": f"video.cache.verify.expected_sha256={NYAN_SHA256}" in text,
        "actual_sha": f"video.cache.verify.actual_sha256={NYAN_SHA256}" in text,
    }


def preset_summary(text: str) -> dict[str, Any]:
    return {
        "preset": f"video.cache.preset={PRESET_NAME}" in text,
        "asset_id": f"video.cache.preset.asset_id={NYAN_ASSET_ID}" in text,
        "sha256": f"video.cache.preset.sha256={NYAN_SHA256}" in text,
    }


def demo_summary(text: str) -> dict[str, Any]:
    return {
        "preset": f"video.demo.preset={PRESET_NAME}" in text,
        "asset_id": f"video.demo.asset_id={NYAN_ASSET_ID}" in text,
        "storage": "video.demo.storage=sd-sha-cache" in text,
        "boot_asset_policy": "video.demo.boot_asset_policy=boot-image-carries-player-not-frames" in text,
    }


def trust_cache_summary(text: str) -> dict[str, Any]:
    return {
        "trust_cache": "video.cache.play.trust_cache=1" in text,
        "sha_checked_zero": "video.cache.verify.sha256_checked=0" in text,
        "sha_match_zero": "video.cache.verify.sha256_match=0" in text,
        "actual_not_checked": "video.cache.verify.actual_sha256=trust-cache-not-checked" in text,
        "default_verify_not_repeated": f"video.cache.verify.actual_sha256={NYAN_SHA256}" not in text,
    }


def sync_summary_setcrtc(text: str) -> dict[str, Any]:
    requested = marker_int(text, "video.cache.play.requested_audio_sync")
    enabled = marker_int(text, "video.stream.audio_sync.enabled")
    ready = marker_int(text, "video.stream.audio_sync.ready")
    wait_ms = marker_int(text, "video.stream.audio_sync.wait_ms")
    start_offset_ms = marker_int(text, "video.stream.audio_sync.start_offset_ms")
    listen_begin_ns = marker_int(text, "video.stream.audio_sync.listen_begin_ns")
    sample_rate = marker_int(text, "video.stream.audio_sync.sample_rate")
    frame_bytes = marker_int(text, "video.stream.audio_sync.frame_bytes")
    total_frames = marker_int(text, "video.stream.audio_sync.total_frames")
    return {
        "requested": requested,
        "enabled": enabled,
        "ready": ready,
        "wait_ms": wait_ms,
        "start_offset_ms": start_offset_ms,
        "listen_begin_ns": listen_begin_ns,
        "sample_rate": sample_rate,
        "frame_bytes": frame_bytes,
        "total_frames": total_frames,
        "status_path_marker": f"video.stream.audio_sync.status_path={SYNC_STATUS_PATH}" in text,
        "drop_policy_none": "video.stream.audio_sync.drop_policy=none" in text,
        "requested_ok": requested == 1,
        "enabled_ok": enabled == 1,
        "ready_ok": ready == 1,
        "wait_ok": wait_ms == SYNC_WAIT_MS,
        "start_offset_ok": start_offset_ms == SYNC_START_OFFSET_MS,
        "listen_begin_present": listen_begin_ns is not None and listen_begin_ns > 0,
        "geometry_ok": sample_rate == 48000 and frame_bytes == 4,
        "duration_present": total_frames is not None and total_frames > 0,
    }


def sync_pass_setcrtc(summary: dict[str, Any]) -> bool:
    required = (
        "requested_ok",
        "enabled_ok",
        "ready_ok",
        "wait_ok",
        "start_offset_ok",
        "status_path_marker",
        "drop_policy_none",
        "listen_begin_present",
        "geometry_ok",
        "duration_present",
    )
    return all(bool(summary.get(key)) for key in required)


def classify_setcrtc_play(text: str, expected_frames: int) -> dict[str, Any]:
    presented = marker_int(text, "video.stream.presented") or 0
    dropped = marker_int(text, "video.stream.dropped_frames")
    if dropped is None:
        dropped = -1
    flip_events = marker_int(text, "video.stream.flip_events") or 0
    elapsed_ns = marker_int(text, "video.stream.elapsed_ns") or 0
    fps_milli = marker_int(text, "video.stream.fps_milli") or 0
    bytes_seen = marker_int(text, "video.stream.bytes") or 0
    accounted = presented + max(dropped, 0)
    trust = trust_cache_summary(text)
    sync = sync_summary_setcrtc(text)
    preset = preset_summary(text)
    demo = demo_summary(text)
    requested_present = f"video.cache.play.requested_present={PRESENT_MODE}" in text
    requested_layout = f"video.cache.play.requested_layout={LAYOUT}" in text
    stream_layout = f"video.stream.layout={LAYOUT}" in text
    present_mode = f"video.stream.present_mode={PRESENT_MODE}" in text
    path_ok = "video.stream.path=kms-dumb-buffer" in text
    pixel_format = f"video.stream.pixel_format={NYAN_FORMAT}" in text
    return {
        "presented": presented,
        "dropped_frames": dropped,
        "accounted_frames": accounted,
        "expected_frames": expected_frames,
        "flip_events": flip_events,
        "elapsed_ns": elapsed_ns,
        "fps_milli": fps_milli,
        "bytes": bytes_seen,
        "frame_accounting_ok": dropped >= 0 and accounted == expected_frames and presented >= 1,
        "no_drops": dropped == 0,
        "setcrtc_flip_ok": flip_events == 0,
        "requested_present_cache_marker": requested_present,
        "requested_layout_cache_marker": requested_layout,
        "stream_layout_marker": stream_layout,
        "present_mode_marker": present_mode,
        "path_ok": path_ok,
        "pixel_format": pixel_format,
        "trust_cache": trust,
        "trust_cache_pass": all_true(trust),
        "preset": preset,
        "preset_pass": all_true(preset),
        "demo": demo,
        "demo_pass": all_true(demo),
        "sync": sync,
        "sync_pass": sync_pass_setcrtc(sync),
        "pass": bool(
            requested_present
            and requested_layout
            and stream_layout
            and present_mode
            and path_ok
            and pixel_format
            and all_true(trust)
            and all_true(preset)
            and all_true(demo)
            and sync_pass_setcrtc(sync)
            and dropped == 0
            and accounted == expected_frames
            and presented == expected_frames
            and flip_events == 0
            and elapsed_ns > 0
            and fps_milli > 0
            and bytes_seen > 0
        ),
    }


def audio_pass_summary(audio_text: str) -> dict[str, Any]:
    summary = av_live.audio_live.classify_pcm_output(audio_text)
    required = (
        "worker_started",
        "worker_done",
        "integrated_done",
        "pcm_done",
        "listen_begin",
        "listen_end",
        "pcm_write_attempted",
        "route_apply_ok",
        "route_reset_ok",
        "safety_amplitude",
        "safety_duration",
        "setcal_all_set",
        "setcal_deallocated",
        "execute_plan_source_pcm",
        "execute_source_pcm",
        "execute_plan_waveform_file",
        "pcm_file_supported",
        "pcm_file_validated",
        "pcm_path_allowed",
    )
    return {
        "summary": summary,
        "pass": all(bool(summary.get(key)) for key in required),
        "required": list(required),
    }


def install_audio_pcm(args: argparse.Namespace,
                      out_dir: Path,
                      steps: list[dict[str, Any]]) -> dict[str, Any]:
    readiness = tiny_live.probe_transfer_readiness(args, out_dir, steps)
    selected = str(readiness.get("selected_transport") or "")
    control_channel = "tcpctl" if selected == "tcpctl" else "bridge"
    result: dict[str, Any] = {
        "transfer_readiness": readiness,
        "selected_transport": selected,
        "control_channel": control_channel,
        "remote": REMOTE_AUDIO_PCM,
        "expected_sha256": NYAN_AUDIO_SHA256,
        "cache_hit": False,
        "uploaded": False,
        "remote_sha_match": False,
    }
    base.run_serial_step(
        out_dir,
        steps,
        "candidate-create-remote-nyan-audio-dir",
        ["run", "/bin/toybox", "mkdir", "-p", REMOTE_AUDIO_DIR],
        timeout=45.0,
        retry_unsafe=True,
    )
    probe = base.run_serial_step(
        out_dir,
        steps,
        "candidate-nyan-audio-pcm-sha256-before-upload",
        ["run", "/bin/toybox", "sha256sum", REMOTE_AUDIO_PCM],
        timeout=60.0,
        retry_unsafe=True,
        allow_error=True,
    )
    result["pre_upload_sha_stdout_path"] = probe.get("stdout_path")
    if NYAN_AUDIO_SHA256 in stdout_of(probe):
        result["cache_hit"] = True
        result["remote_sha_match"] = True
        return result

    install = base.run_step(
        out_dir,
        steps,
        "install-nyan-audio-pcm",
        tiny_live.install_command(
            args,
            LOCAL_AUDIO,
            REMOTE_AUDIO_PCM,
            args.transfer_port + 7,
            control_channel=control_channel,
        ),
        timeout=args.transfer_timeout + 120.0,
    )
    result["install_stdout_path"] = install.get("stdout_path")
    result["uploaded"] = bool(install.get("ok"))
    remote_sha = base.run_serial_step(
        out_dir,
        steps,
        "candidate-nyan-audio-pcm-sha256-after-upload",
        ["run", "/bin/toybox", "sha256sum", REMOTE_AUDIO_PCM],
        timeout=90.0,
        retry_unsafe=True,
        allow_error=True,
    )
    result["post_upload_sha_stdout_path"] = remote_sha.get("stdout_path")
    result["remote_sha_match"] = NYAN_AUDIO_SHA256 in stdout_of(remote_sha)
    return result


def render_report(result: dict[str, Any]) -> str:
    install = result.get("runtime_install", {}) if isinstance(result.get("runtime_install"), dict) else {}
    audio_install = result.get("audio_install", {}) if isinstance(result.get("audio_install"), dict) else {}
    status = result.get("cache_status_summary", {}) if isinstance(result.get("cache_status_summary"), dict) else {}
    verify = result.get("cache_verify_summary", {}) if isinstance(result.get("cache_verify_summary"), dict) else {}
    play = result.get("cache_play_summary", {}) if isinstance(result.get("cache_play_summary"), dict) else {}
    sync = play.get("sync", {}) if isinstance(play.get("sync"), dict) else {}
    audio = result.get("audio_summary", {}) if isinstance(result.get("audio_summary"), dict) else {}
    classifier_fix = result.get("posthoc_classifier_fix", {}) if isinstance(result.get("posthoc_classifier_fix"), dict) else {}
    classifier_lines = [
        "",
        "## Classifier Note",
        "",
        f"- Posthoc classifier fix applied: `{int(bool(classifier_fix.get('applied')))}`",
        f"- Reason: `{classifier_fix.get('reason', 'n/a')}`",
        f"- Cache/audio pass after fix: `{int(bool(classifier_fix.get('cache_play_pass')))}` / `{int(bool(classifier_fix.get('audio_pass')))}`",
    ] if classifier_fix else []
    return "\n".join([
        "# Native Init V2975 Nyan Real Preview Live Validation",
        "",
        "## Summary",
        "",
        f"- Decision: `{result.get('decision')}`",
        f"- Result before rollback: `{int(bool(result.get('pass')))}`",
        f"- Candidate: `{CANDIDATE_TAG}` / `{CANDIDATE_VERSION}` / `{CANDIDATE_SHA256}`",
        f"- Video SHA256: `{NYAN_SHA256}`",
        f"- Audio SHA256: `{NYAN_AUDIO_SHA256}`",
        f"- Slice: `{NYAN_FRAMES}` frames / `{AUDIO_DURATION_MS}` ms audio",
        f"- Present path: `{PRESENT_MODE}` / `{LAYOUT}`",
        f"- Rollback attempted: `{int(bool(result.get('rollback_attempted')))}`",
        f"- Rollback health: version_ok=`{int(bool(result.get('rollback_version_ok')))}` selftest_fail0=`{int(bool(result.get('rollback_selftest_fail0')))}`",
        "",
        "## Runtime Assets",
        "",
        f"- Video cache dir: `{install.get('cache_dir')}`",
        f"- Video cache source: `{install.get('cache_source')}`",
        f"- Video cache hit before upload: `{int(bool(install.get('cache_hit')))}`",
        f"- Video cache uploaded: `{int(bool(install.get('cache_uploaded')))}`",
        f"- Stream size bytes: `{(result.get('fixture') or {}).get('stream_size')}`",
        f"- Compression ratio milli: `{(result.get('fixture') or {}).get('compression_ratio_milli')}`",
        f"- Audio remote PCM: `{REMOTE_AUDIO_PCM}`",
        f"- Audio cache hit before upload: `{int(bool(audio_install.get('cache_hit')))}`",
        f"- Audio uploaded: `{int(bool(audio_install.get('uploaded')))}`",
        f"- Audio remote SHA matched: `{int(bool(audio_install.get('remote_sha_match')))}`",
        f"- Audio transfer: `{audio_install.get('selected_transport')}` control=`{audio_install.get('control_channel')}`",
        "",
        "## Command Results",
        "",
        f"- `video demo nyan status`: rc=`{result.get('cache_status_rc')}` summary=`{status}`",
        f"- `video demo nyan verify`: rc=`{result.get('cache_verify_rc')}` summary=`{verify}`",
        f"- `audio play --pcm-file`: rc=`{result.get('audio_execute_rc')}` worker_done=`{int(bool(result.get('audio_worker_done')))}` pass=`{int(bool(audio.get('pass')))}`",
        f"- `video demo nyan play --trust-cache --layout player-hud --present setcrtc`: rc=`{result.get('cache_play_rc')}` pass=`{int(bool(play.get('pass')))}`",
        f"- Frame accounting: presented=`{play.get('presented')}` dropped=`{play.get('dropped_frames')}` accounted=`{play.get('accounted_frames')}` fps_milli=`{play.get('fps_milli')}` elapsed_ns=`{play.get('elapsed_ns')}`",
        f"- Setcrtc markers: flip_events=`{play.get('flip_events')}` path_ok=`{int(bool(play.get('path_ok')))}` pixel_format=`{int(bool(play.get('pixel_format')))}`",
        f"- Sync markers: `{sync}`",
        *classifier_lines,
        "",
        "## Safety",
        "",
        "- Only the boot partition was flashed, through `native_init_flash.py`; rollback target remained `v2321`.",
        "- Raw Nyan stream/audio and run logs remained private and untracked.",
        "- No Venus, GPU, raw DSI, panel init, backlight, PMIC, PWM, regulator, GPIO, or GDSC path was used.",
        "- Audio was bounded to 10 seconds and amplitude-milli 150.",
        "",
        "## Evidence",
        "",
        f"- Result JSON: `{result.get('result_json')}`",
        f"- Output dir: `{result.get('out_dir')}`",
        "",
    ])


def run_live(args: argparse.Namespace, out_dir: Path, state: dict[str, Any]) -> dict[str, Any]:
    steps: list[dict[str, Any]] = []
    candidate_flash_ok = False
    candidate_flash_attempted = False
    result: dict[str, Any] = {
        "decision": f"{DECISION_PREFIX}-live-started",
        "pass": False,
        "out_dir": video_live.rel(out_dir),
        "preflight": state,
        "play_frames": int(args.frames),
        "steps": steps,
        "rollback_attempted": False,
        "rollback_version_ok": False,
        "rollback_selftest_fail0": False,
    }
    try:
        fixture = fixture_from_asset()
        result["fixture"] = fixture
        base.run_step(
            out_dir,
            steps,
            "verify-current-v2321",
            video_live.flash_command(video_live.ROLLBACK_IMAGE, video_live.ROLLBACK_VERSION, video_live.ROLLBACK_SHA256, from_native=False) + ["--verify-only"],
            timeout=args.flash_timeout,
        )
        candidate_flash_attempted = True
        flash = base.run_step(
            out_dir,
            steps,
            f"flash-{CANDIDATE_TAG}",
            video_live.flash_command(CANDIDATE_IMAGE, CANDIDATE_VERSION, CANDIDATE_SHA256, from_native=True),
            timeout=args.flash_timeout,
        )
        candidate_flash_ok = flash.get("rc") == 0
        version = base.run_serial_step(out_dir, steps, "candidate-version", ["version"], timeout=90.0, retry_unsafe=True)
        status = base.run_serial_step(out_dir, steps, "candidate-status", ["status"], timeout=90.0, retry_unsafe=True)
        selftest = base.run_serial_step(out_dir, steps, "candidate-selftest", ["selftest", "verbose"], timeout=120.0, retry_unsafe=True)
        video_status = base.run_serial_step(out_dir, steps, "candidate-video-status", ["video", "status"], timeout=90.0, retry_unsafe=True)
        audio_status = base.run_serial_step(out_dir, steps, "candidate-audio-status", ["audio", "status"], timeout=90.0, retry_unsafe=True)
        video_status_text = stdout_of(video_status)
        result["candidate_version_ok"] = f"A90 Linux init {CANDIDATE_VERSION} ({CANDIDATE_TAG})" in stdout_of(version)
        result["candidate_status_ok"] = bool(status.get("ok"))
        result["candidate_selftest_fail0"] = video_live.selftest_step_ok(selftest)
        result["candidate_video_status_nyan"] = "video.status.nyan_pal8_rle=1" in video_status_text and "video demo [badapple|badapple-scale|nyan]" in video_status_text
        result["candidate_audio_status_ok"] = "audio.status.version=" in stdout_of(audio_status)
        if not (
            result["candidate_version_ok"]
            and result["candidate_status_ok"]
            and result["candidate_selftest_fail0"]
            and result["candidate_video_status_nyan"]
            and result["candidate_audio_status_ok"]
        ):
            result["decision"] = f"{DECISION_PREFIX}-candidate-health-failed-before-nyan"
            raise RuntimeError("candidate health/video/audio status did not pass")

        result["runtime_install"] = video_live.install_fixture(args, out_dir, steps, fixture)
        install = result["runtime_install"]
        if not (install.get("cache_hit") or install.get("cache_uploaded") or install.get("cache_adopted")):
            result["decision"] = f"{DECISION_PREFIX}-video-cache-seed-failed"
            raise RuntimeError("Nyan stream was not available in SHA-addressed SD cache")

        result["audio_install"] = install_audio_pcm(args, out_dir, steps)
        if not result["audio_install"].get("remote_sha_match"):
            result["decision"] = f"{DECISION_PREFIX}-audio-transfer-sha-mismatch"
            raise RuntimeError("Nyan audio PCM remote SHA mismatch")

        base.run_serial_step(out_dir, steps, "candidate-hide-menu-before-nyan", ["hide"], timeout=45.0, allow_error=True, retry_unsafe=True)
        status_step = base.run_serial_step(out_dir, steps, "candidate-video-demo-nyan-status", ["video", "demo", PRESET_NAME, "status"], timeout=120.0, allow_error=True, retry_unsafe=False)
        status_text = stdout_of(status_step)
        result["cache_status_rc"] = status_step.get("rc")
        result["cache_status_stdout_path"] = status_step.get("stdout_path")
        result["cache_status_summary"] = cache_status_summary(status_text)
        result["cache_status_preset_summary"] = preset_summary(status_text)
        result["cache_status_demo_summary"] = demo_summary(status_text)
        if status_step.get("rc") != 0 or not all_true(result["cache_status_summary"]) or not all_true(result["cache_status_preset_summary"]) or not all_true(result["cache_status_demo_summary"]):
            result["decision"] = f"{DECISION_PREFIX}-cache-status-failed"
            raise RuntimeError("video demo nyan status did not emit required markers")

        verify_step = base.run_serial_step(out_dir, steps, "candidate-video-demo-nyan-verify", ["video", "demo", PRESET_NAME, "verify"], timeout=420.0, allow_error=True, retry_unsafe=False)
        verify_text = stdout_of(verify_step)
        result["cache_verify_rc"] = verify_step.get("rc")
        result["cache_verify_stdout_path"] = verify_step.get("stdout_path")
        result["cache_verify_summary"] = cache_verify_summary(verify_text)
        result["cache_verify_preset_summary"] = preset_summary(verify_text)
        result["cache_verify_demo_summary"] = demo_summary(verify_text)
        if verify_step.get("rc") != 0 or not all_true(result["cache_verify_summary"]) or not all_true(result["cache_verify_preset_summary"]) or not all_true(result["cache_verify_demo_summary"]):
            result["decision"] = f"{DECISION_PREFIX}-cache-verify-failed"
            raise RuntimeError("video demo nyan verify did not emit required markers")

        base.run_serial_step(
            out_dir,
            steps,
            "candidate-clear-audio-play-status-before-nyan",
            ["run", "/bin/busybox", "rm", "-f", SYNC_STATUS_PATH, REMOTE_PLAY_LOG],
            timeout=45.0,
            retry_unsafe=True,
            allow_error=True,
        )
        audio_step = base.run_serial_step(
            out_dir,
            steps,
            "candidate-audio-play-nyan-pcm-execute",
            [
                "audio", "play", AUDIO_PROFILE,
                "--mode", "listen",
                "--duration-ms", str(AUDIO_DURATION_MS),
                "--amplitude-milli", str(AUDIO_AMPLITUDE_MILLI),
                "--manifest", AUDIO_MANIFEST,
                "--pcm-gain-milli", str(AUDIO_PCM_GAIN_MILLI),
                "--pcm-file", REMOTE_AUDIO_PCM,
                "--execute",
            ],
            timeout=120.0,
            retry_unsafe=False,
            allow_error=True,
        )
        audio_execute_text = stdout_of(audio_step)
        result["audio_execute_rc"] = audio_step.get("rc")
        result["audio_execute_stdout_path"] = audio_step.get("stdout_path")
        result["audio_execute_elapsed_sec"] = audio_step.get("elapsed_sec")
        if audio_step.get("rc") != 0 or "audio.play.worker.started=1" not in audio_execute_text:
            result["decision"] = f"{DECISION_PREFIX}-audio-start-failed-before-video"
            raise RuntimeError("Nyan audio PCM-file worker did not start")

        play_step = base.run_serial_step(
            out_dir,
            steps,
            "candidate-video-demo-nyan-player-hud-av-play",
            [
                "video", "demo", PRESET_NAME, "play",
                "--trust-cache",
                "--frames", str(args.frames),
                "--present", PRESENT_MODE,
                "--layout", LAYOUT,
                "--sync-audio-status", SYNC_STATUS_PATH,
                "--sync-wait-ms", str(SYNC_WAIT_MS),
                "--sync-start-offset-ms", str(SYNC_START_OFFSET_MS),
            ],
            timeout=args.stream_timeout,
            allow_error=True,
            retry_unsafe=False,
        )
        play_text = stdout_of(play_step)
        result["cache_play_rc"] = play_step.get("rc")
        result["cache_play_stdout_path"] = play_step.get("stdout_path")
        result["cache_play_elapsed_sec"] = play_step.get("elapsed_sec")
        result["cache_play_summary"] = classify_setcrtc_play(play_text, int(args.frames))

        worker = av_live.audio_live.wait_for_worker_done(out_dir, steps, 180.0)
        result["audio_worker_done"] = bool(worker.get("done"))
        result["audio_worker_attempts"] = worker.get("attempts")
        result["audio_worker_status_stdout_path"] = worker.get("stdout_path")
        log_step = base.run_serial_step(out_dir, steps, "candidate-audio-worker-log", ["run", "/bin/busybox", "cat", REMOTE_PLAY_LOG], timeout=45.0, retry_unsafe=True, allow_error=True)
        audio_log_text = stdout_of(log_step)
        result["audio_worker_log_stdout_path"] = log_step.get("stdout_path")
        audio_text = "\n".join([audio_execute_text, str(worker.get("text") or ""), audio_log_text])
        result["audio_summary"] = audio_pass_summary(audio_text)

        if (
            play_step.get("rc") != 0
            or not result["cache_play_summary"].get("pass")
            or not result["audio_summary"].get("pass")
            or not result["audio_worker_done"]
        ):
            result["decision"] = f"{DECISION_PREFIX}-marker-failed"
            raise RuntimeError("Nyan Player HUD A/V run did not emit required pass markers")

        after = base.run_serial_step(out_dir, steps, "candidate-selftest-after-nyan", ["selftest", "verbose"], timeout=120.0, retry_unsafe=True)
        result["candidate_selftest_after_nyan_fail0"] = video_live.selftest_step_ok(after)
        if not result["candidate_selftest_after_nyan_fail0"]:
            result["decision"] = f"{DECISION_PREFIX}-post-play-selftest-failed"
            raise RuntimeError("post Nyan selftest did not report fail=0")
        result["decision"] = f"{DECISION_PREFIX}-live-pass-before-rollback"
        result["pass"] = True
    except Exception as exc:
        result.setdefault("decision", f"{DECISION_PREFIX}-live-blocked")
        if result["decision"] == f"{DECISION_PREFIX}-live-started":
            result["decision"] = f"{DECISION_PREFIX}-live-blocked"
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
                result["rollback_version_ok"] = video_live.ROLLBACK_VERSION in stdout_of(rollback_version)
                result["rollback_selftest_fail0"] = video_live.selftest_step_ok(rollback_selftest)
        result["result_json"] = video_live.rel(out_dir / "result.json")
        video_live.write_json(out_dir / "result.json", result)
        REPORT_PATH.write_text(render_report(result), encoding="utf-8")
    return result


def parse_args() -> argparse.Namespace:
    parser = video_live.parse_args()
    parser.live = bool(parser.live)
    parser.frames = NYAN_FRAMES
    parser.width = NYAN_WIDTH
    parser.height = NYAN_HEIGHT
    parser.stride = 0
    parser.stream_format = NYAN_FORMAT
    parser.pattern = "nyan"
    parser.fps_num = 30
    parser.fps_den = 1
    parser.disable_cache = False
    parser.adopt_legacy_cache = False
    parser.require_cache_hit = False
    parser.chunk_large_streams = False
    parser.stream_chunk_bytes = min(int(parser.stream_chunk_bytes), 64 * 1024 * 1024)
    parser.stream_timeout = max(float(parser.stream_timeout), 180.0)
    parser.transfer_timeout = max(float(parser.transfer_timeout), 900.0)
    return parser


def dry_run_payload(args: argparse.Namespace, state: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": f"{DECISION_PREFIX}-dry-run" if preflight_ok(state) else f"{DECISION_PREFIX}-preflight-failed",
        "ok": preflight_ok(state),
        "preflight": state,
        "commands": [
            f"verify rollback image {video_live.ROLLBACK_IMAGE}",
            f"flash {CANDIDATE_IMAGE}",
            "version/status/selftest/video status/audio status",
            f"seed {NYAN_SHA256} into {video_live.remote_cache_dir(NYAN_SHA256)}",
            f"install {LOCAL_AUDIO} to {REMOTE_AUDIO_PCM}",
            f"video demo {PRESET_NAME} status",
            f"video demo {PRESET_NAME} verify",
            f"audio play {AUDIO_PROFILE} --duration-ms {AUDIO_DURATION_MS} --amplitude-milli {AUDIO_AMPLITUDE_MILLI} --pcm-gain-milli {AUDIO_PCM_GAIN_MILLI} --pcm-file {REMOTE_AUDIO_PCM} --execute",
            f"video demo {PRESET_NAME} play --trust-cache --frames {args.frames} --present {PRESENT_MODE} --layout {LAYOUT} --sync-audio-status {SYNC_STATUS_PATH} --sync-wait-ms {SYNC_WAIT_MS} --sync-start-offset-ms {SYNC_START_OFFSET_MS}",
            "rollback v2321 and verify selftest fail=0",
        ],
    }


def main() -> int:
    args = parse_args()
    out_dir = video_live.ROOT / f"workspace/private/runs/video/{BUILD_TAG}-{now_slug()}"
    out_dir.mkdir(parents=True, exist_ok=True)
    state = preflight_state(args)
    if not args.live:
        payload = dry_run_payload(args, state)
        video_live.write_json(out_dir / "dry_run.json", payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if payload["ok"] else 1
    if not preflight_ok(state):
        payload = {"decision": f"{DECISION_PREFIX}-preflight-failed", "pass": False, "preflight": state, "out_dir": video_live.rel(out_dir)}
        video_live.write_json(out_dir / "result.json", payload)
        REPORT_PATH.write_text(render_report(payload), encoding="utf-8")
        print(json.dumps({"decision": payload["decision"], "pass": False, "out_dir": video_live.rel(out_dir)}, indent=2, sort_keys=True))
        return 1
    result = run_live(args, out_dir, state)
    print(json.dumps({
        "decision": result.get("decision"),
        "pass": bool(result.get("pass")),
        "out_dir": video_live.rel(out_dir),
        "rollback_version_ok": result.get("rollback_version_ok"),
        "rollback_selftest_fail0": result.get("rollback_selftest_fail0"),
    }, indent=2, sort_keys=True))
    return 0 if (result.get("pass") and result.get("rollback_version_ok") and result.get("rollback_selftest_fail0")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
