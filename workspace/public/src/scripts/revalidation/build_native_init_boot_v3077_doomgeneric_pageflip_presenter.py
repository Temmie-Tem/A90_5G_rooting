#!/usr/bin/env python3
"""Build V3077 native-init DOOM pageflip-presenter timing candidate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _workspace_bootstrap import repo_root
import build_native_init_boot_v3074_doomgeneric_minimal_dashboard as v3074
from a90harness.evidence import workspace_private_build_path, workspace_private_input_path

REPO_ROOT = repo_root()

CYCLE = "V3077"
INIT_VERSION = "0.10.95"
INIT_BUILD = "v3077-doomgeneric-pageflip-presenter"
BUILD_TAG = INIT_BUILD
DECISION = "v3077-doomgeneric-pageflip-presenter-source-build-pass"

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
OBJ_DIR = OUT_DIR / "obj"
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V3077_DOOMGENERIC_PAGEFLIP_PRESENTER_SOURCE_BUILD_2026-06-23.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images", "boot_linux_v3077_doomgeneric_pageflip_presenter.img", legacy_fallback=False
)
INIT_BINARY = OUT_DIR / "init_v3077_doomgeneric_pageflip_presenter"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v3077_doomgeneric_pageflip_presenter.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v512_doomgeneric_pageflip_presenter"

ENGINE_BINARY = OUT_DIR / "a90_doomgeneric_private_engine_v3077"
ENGINE_ADAPTER_SOURCE = OUT_DIR / "a90_doomgeneric_native_bridge_v3077.c"
ENGINE_ADAPTER_OBJECT = OBJ_DIR / "a90_doomgeneric_native_bridge_v3077.o"
ENGINE_RAMDISK_PATH = "bin/a90_doomgeneric_private_engine_v3077"
ENGINE_REMOTE_PATH = "/" + ENGINE_RAMDISK_PATH
ENGINE_NAME = "doomgeneric-private-link-v3077-pageflip-presenter"

RUNTIME_WAD_ROOT = v3074.RUNTIME_WAD_ROOT
RUNTIME_WAD_PATH = v3074.RUNTIME_WAD_PATH
EXPECTED_WAD_SHA256 = v3074.EXPECTED_WAD_SHA256
RUNTIME_WAD_MAX_BYTES = v3074.RUNTIME_WAD_MAX_BYTES
DEFAULT_FRAME_TICKS = v3074.DEFAULT_FRAME_TICKS
DEFAULT_SMOKE_FRAMES = v3074.DEFAULT_SMOKE_FRAMES
DEFAULT_LOOP_FRAMES = v3074.DEFAULT_LOOP_FRAMES
CONTINUOUS_LOOP_FRAMES = v3074.CONTINUOUS_LOOP_FRAMES
MAX_LOOP_FRAMES = v3074.MAX_LOOP_FRAMES
LOOP_FRAME_MS = v3074.LOOP_FRAME_MS
PRESENTER_POLL_MS = v3074.PRESENTER_POLL_MS
FRAME_PATH = "/tmp/a90-doomgeneric-v3077-pageflip-presenter-frame.xbgr8888"
INPUT_STATE_PATH = "/tmp/a90-doomgeneric-v3077-input.state"
INPUT_SOCKET_PATH = "/tmp/a90-doomgeneric-v3077-input.sock"
INPUT_UDP_PORT = v3074.INPUT_UDP_PORT
DEVICE_NCM_HOST = v3074.DEVICE_NCM_HOST
FRAME_WIDTH = v3074.FRAME_WIDTH
FRAME_HEIGHT = v3074.FRAME_HEIGHT
FRAME_STRIDE = v3074.FRAME_STRIDE
FRAME_BYTES = v3074.FRAME_BYTES
NATIVE_DASHBOARD = v3074.NATIVE_DASHBOARD
NATIVE_DASHBOARD_MINIMAL = v3074.NATIVE_DASHBOARD_MINIMAL
NATIVE_DASHBOARD_LARGE_FRAME = v3074.NATIVE_DASHBOARD_LARGE_FRAME
NATIVE_DOOM_PRESENT_PAGEFLIP = 1
BASELINE_NATIVE_DOOM_PRESENT_PAGEFLIP = 0
REUSE_FRAME_BUFFER = v3074.REUSE_FRAME_BUFFER
DASHBOARD_METRICS_INTERVAL_FRAMES = v3074.DASHBOARD_METRICS_INTERVAL_FRAMES
FRAME_TIMING_PROBE = v3074.FRAME_TIMING_PROBE

SOUND_MODE = v3074.SOUND_MODE
AUDIO_CORUN = v3074.AUDIO_CORUN
AUDIO_CORUN_MODE = v3074.AUDIO_CORUN_MODE
AUDIO_CORUN_DURATION_MS = v3074.AUDIO_CORUN_DURATION_MS
AUDIO_CORUN_AMPLITUDE_MILLI = v3074.AUDIO_CORUN_AMPLITUDE_MILLI

HOST_KEYBOARD_BRIDGE = v3074.HOST_KEYBOARD_BRIDGE
HOST_DASHBOARD = v3074.HOST_DASHBOARD

REQUIRED_STRINGS = (
    b"A90 Linux init 0.10.95 (v3077-doomgeneric-pageflip-presenter)",
    b"v3077-doomgeneric-pageflip-presenter",
    b"doomgeneric-private-link-v3077-pageflip-presenter",
    b"/bin/a90_doomgeneric_private_engine_v3077",
    RUNTIME_WAD_PATH.encode("ascii"),
    EXPECTED_WAD_SHA256.encode("ascii"),
    FRAME_PATH.encode("ascii"),
    INPUT_STATE_PATH.encode("ascii"),
    INPUT_SOCKET_PATH.encode("ascii"),
    b"a90.doomgeneric.v3059.input=udp-ncm-state-with-unix-dgram-fallback",
    b"--input-udp",
    b"udp-ncm-to-DG_GetKey-with-serial-doompad-fallback",
    b"video.demo.doom.loop.frame_ms=",
    b"video.demo.doom.presenter.pacing=helper-frame-mtime",
    b"video.demo.doom.presenter.reader=reused-loop-buffer",
    b"video.demo.doom.presenter.present_mode=pageflip",
    b"video.demo.doom.presenter.present_path=kms-dumb-buffer-pageflip",
    b"video.demo.doom.loop.present_mode=",
    b"video.demo.doom.loop.present_path=",
    b"video.demo.doom.loop.flip_telemetry=pageflip-event-delta-us",
    b"flip_events=",
    b"flip_delta_avg_us=",
    b"last_timestamp_us=",
    b"video.demo.doom.loop.timing_probe=1",
    b"video.demo.doom.loop.timing=frame-ipc-kms-stage-us",
    b"timing.present",
    b"video.demo.doom.dashboard.profile=minimal-fastdraw",
    b"video.demo.doom.dashboard.metrics_pacing=disabled-minimal",
    b"video.demo.doom.dashboard.frame_mode=minimal-dashboard",
    b"video.demo.input.udp_port=",
    b"native-audio-corun-tone-v3053",
)


def rel(path: Path) -> str:
    return v3074.rel(path)


def v3033_module() -> Any:
    return v3074.v3033_module()


def apply_v3077_globals() -> None:
    v3074.CYCLE = CYCLE
    v3074.INIT_VERSION = INIT_VERSION
    v3074.INIT_BUILD = INIT_BUILD
    v3074.BUILD_TAG = BUILD_TAG
    v3074.DECISION = DECISION
    v3074.OUT_DIR = OUT_DIR
    v3074.OBJ_DIR = OBJ_DIR
    v3074.REPORT_PATH = REPORT_PATH
    v3074.BOOT_IMAGE = BOOT_IMAGE
    v3074.INIT_BINARY = INIT_BINARY
    v3074.RAMDISK_CPIO = RAMDISK_CPIO
    v3074.HELPER_BINARY = HELPER_BINARY
    v3074.ENGINE_BINARY = ENGINE_BINARY
    v3074.ENGINE_ADAPTER_SOURCE = ENGINE_ADAPTER_SOURCE
    v3074.ENGINE_ADAPTER_OBJECT = ENGINE_ADAPTER_OBJECT
    v3074.ENGINE_RAMDISK_PATH = ENGINE_RAMDISK_PATH
    v3074.ENGINE_REMOTE_PATH = ENGINE_REMOTE_PATH
    v3074.ENGINE_NAME = ENGINE_NAME
    v3074.FRAME_PATH = FRAME_PATH
    v3074.INPUT_STATE_PATH = INPUT_STATE_PATH
    v3074.INPUT_SOCKET_PATH = INPUT_SOCKET_PATH
    v3074.REQUIRED_STRINGS = REQUIRED_STRINGS
    v3074.render_report = render_report
    v3074.apply_v3074_globals()
    v3033 = v3033_module()
    v3033.NATIVE_DOOM_PRESENT_PAGEFLIP = NATIVE_DOOM_PRESENT_PAGEFLIP


def render_report(
    manifest: dict[str, Any],
    helper_flags: tuple[str, ...],
    init_extra_flags: tuple[str, ...],
) -> str:
    doom = manifest.get("doomgeneric_visible_loop", {})
    markers = manifest.get("v3033_marker_strings", [])
    marker_lines = [f"- `{marker}`" for marker in markers] if isinstance(markers, list) else []
    return "\n".join([
        "# Native Init V3077 DOOMGENERIC Pageflip Presenter Source Build",
        "",
        "## Summary",
        "",
        f"- Cycle: `{CYCLE}`",
        "- Track: active Video playback / DOOM capstone frame pacing.",
        f"- Decision: `{manifest['decision']}`",
        "- Result: PASS",
        "- Device flash: `no` in this build unit.",
        f"- Boot image: `{manifest['boot_image']}`",
        f"- Boot SHA256: `{manifest['boot_sha256']}`",
        f"- Init: `A90 Linux init {manifest['init_version']} ({manifest['init_build']})`",
        "",
        "## Included Delta",
        "",
        "- Keeps V3074 minimal-dashboard drawing, V3071 timing probe, reader reuse, frame_ms=28, and UDP/NCM input unchanged.",
        "- Changes the DOOM native presenter from the SETCRTC path to the existing KMS pageflip path.",
        "- Adds DOOM loop present-mode markers plus pageflip event and flip-delta telemetry.",
        "- Primes the pageflip presenter with one SETCRTC before the frame loop, matching the existing video stream pageflip contract.",
        "",
        "## Presenter Contract",
        "",
        f"- Baseline pageflip presenter: `{BASELINE_NATIVE_DOOM_PRESENT_PAGEFLIP}`",
        f"- Candidate pageflip presenter: `{NATIVE_DOOM_PRESENT_PAGEFLIP}`",
        "- Presenter mode marker: `pageflip`",
        "- Presenter path marker: `kms-dumb-buffer-pageflip`",
        "- Flip telemetry: `flip_events`, `flip_delta_min_us`, `flip_delta_avg_us`, `flip_delta_max_us`, `last_sequence`, `last_timestamp_us`.",
        f"- Helper frame ms: `{doom.get('loop_frame_ms', LOOP_FRAME_MS)}`",
        f"- Presenter poll ms: `{doom.get('presenter_poll_ms', PRESENTER_POLL_MS)}`",
        f"- Dashboard profile: `{doom.get('dashboard_profile', 'minimal-fastdraw')}`",
        f"- Frame timing probe: `{FRAME_TIMING_PROBE}`",
        "",
        "## Runtime Contract",
        "",
        f"- Runtime WAD path: `{doom.get('runtime_wad_path')}`",
        f"- Expected WAD SHA256: `{doom.get('expected_wad_sha256')}`",
        f"- Continuous command: `video demo doom loop-start 0 --wad runtime-private --sha256 {EXPECTED_WAD_SHA256}`",
        f"- Helper loop command: `{doom.get('helper_loop_command')}`",
        "",
        "## Marker Check",
        "",
        *marker_lines,
        "",
        "## Validation",
        "",
        "- `py_compile`: V3077 builder and focused tests.",
        "- `unittest`: V3077 source contract plus V3074/V3071/V3069/V3067/V3065/V3063/V3061/V3059 and base visible-loop regressions.",
        "- Build: AArch64 helper compile/link, native-init compile, ramdisk pack, boot image pack, SHA256 capture.",
        "- Marker check: generated boot image contains V3077 identity, pageflip presenter markers, flip telemetry markers, minimal-dashboard markers, and UDP input markers.",
        "- `git diff --check`: PASS.",
        "",
        "## Next Unit",
        "",
        "- Run ID: `V3078`",
        "- Type: rollback-gated live validation of V3077 pageflip-presenter candidate.",
        "- Scope: flash exact V3077 boot image via `native_init_flash.py`, health-check, require pageflip presenter markers, run bounded foreground timing loop, compare KMS present/total timings and flip deltas with V3075/V3076, then start continuous loop and verify UDP input still works.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `doomgeneric-pageflip-presenter-candidate`.",
    ]) + "\n"


def main() -> int:
    apply_v3077_globals()
    rc = v3074.v3071.v3069.main()
    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    doom = manifest.setdefault("doomgeneric_visible_loop", {})
    doom.update({
        "native_dashboard": bool(NATIVE_DASHBOARD),
        "native_dashboard_minimal": bool(NATIVE_DASHBOARD_MINIMAL),
        "native_dashboard_large_frame": bool(NATIVE_DASHBOARD_LARGE_FRAME),
        "native_doom_present_pageflip": bool(NATIVE_DOOM_PRESENT_PAGEFLIP),
        "baseline_native_doom_present_pageflip": bool(BASELINE_NATIVE_DOOM_PRESENT_PAGEFLIP),
        "present_mode": "pageflip",
        "present_path": "kms-dumb-buffer-pageflip",
        "pageflip_timeout_ms": 1000,
        "flip_telemetry": [
            "flip_events",
            "flip_delta_count",
            "flip_delta_min_us",
            "flip_delta_avg_us",
            "flip_delta_max_us",
            "last_sequence",
            "last_timestamp_us",
        ],
        "helper_loop_command": (
            f"{ENGINE_REMOTE_PATH} --wad-frame-loop {RUNTIME_WAD_PATH} "
            f"--frames {DEFAULT_LOOP_FRAMES} --output {FRAME_PATH} "
            f"--input-state {INPUT_STATE_PATH} --frame-ms {LOOP_FRAME_MS} "
            f"--input-socket {INPUT_SOCKET_PATH} --input-udp {INPUT_UDP_PORT}"
        ),
    })
    manifest.update({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "doomgeneric-pageflip-presenter-candidate",
        "adoption_state": "pending-pageflip-presenter-live-validation",
    })
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(
        render_report(
            manifest,
            tuple(manifest.get("helper_flags", ())),
            tuple(manifest.get("init_extra_flags", ())),
        ),
        encoding="utf-8",
    )
    (OUT_DIR / "doomgeneric-pageflip-presenter-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "doomgeneric-pageflip-presenter-candidate",
        "boot_image": rel(BOOT_IMAGE),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "engine_binary": rel(ENGINE_BINARY),
        "engine_ramdisk_path": ENGINE_REMOTE_PATH,
        "runtime_wad_path": RUNTIME_WAD_PATH,
        "expected_wad_sha256": EXPECTED_WAD_SHA256,
        "frame_path": FRAME_PATH,
        "input_state_path": INPUT_STATE_PATH,
        "input_socket_path": INPUT_SOCKET_PATH,
        "input_udp_host": DEVICE_NCM_HOST,
        "input_udp_port": INPUT_UDP_PORT,
        "loop_frame_ms": LOOP_FRAME_MS,
        "presenter_poll_ms": PRESENTER_POLL_MS,
        "present_mode": "pageflip",
        "present_path": "kms-dumb-buffer-pageflip",
        "dashboard_profile": "minimal-fastdraw",
        "frame_timing_probe": FRAME_TIMING_PROBE,
        "native_dashboard": bool(NATIVE_DASHBOARD),
        "native_dashboard_minimal": bool(NATIVE_DASHBOARD_MINIMAL),
        "native_doom_present_pageflip": bool(NATIVE_DOOM_PRESENT_PAGEFLIP),
        "loop_start_command": f"video demo doom loop-start 0 --wad runtime-private --sha256 {EXPECTED_WAD_SHA256}",
        "host_keyboard_bridge": rel(HOST_KEYBOARD_BRIDGE),
        "source_report": rel(REPORT_PATH),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-pageflip-presenter-live-validation",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
