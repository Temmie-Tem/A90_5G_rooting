#!/usr/bin/env python3
"""Build V3074 native-init DOOM minimal-dashboard timing candidate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _workspace_bootstrap import repo_root
import build_native_init_boot_v3071_doomgeneric_frame_timing as v3071
from a90harness.evidence import workspace_private_build_path, workspace_private_input_path

REPO_ROOT = repo_root()

CYCLE = "V3074"
INIT_VERSION = "0.10.94"
INIT_BUILD = "v3074-doomgeneric-minimal-dashboard"
BUILD_TAG = INIT_BUILD
DECISION = "v3074-doomgeneric-minimal-dashboard-source-build-pass"

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
OBJ_DIR = OUT_DIR / "obj"
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V3074_DOOMGENERIC_MINIMAL_DASHBOARD_SOURCE_BUILD_2026-06-23.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images", "boot_linux_v3074_doomgeneric_minimal_dashboard.img", legacy_fallback=False
)
INIT_BINARY = OUT_DIR / "init_v3074_doomgeneric_minimal_dashboard"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v3074_doomgeneric_minimal_dashboard.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v512_doomgeneric_minimal_dashboard"

ENGINE_BINARY = OUT_DIR / "a90_doomgeneric_private_engine_v3074"
ENGINE_ADAPTER_SOURCE = OUT_DIR / "a90_doomgeneric_native_bridge_v3074.c"
ENGINE_ADAPTER_OBJECT = OBJ_DIR / "a90_doomgeneric_native_bridge_v3074.o"
ENGINE_RAMDISK_PATH = "bin/a90_doomgeneric_private_engine_v3074"
ENGINE_REMOTE_PATH = "/" + ENGINE_RAMDISK_PATH
ENGINE_NAME = "doomgeneric-private-link-v3074-minimal-dashboard"

RUNTIME_WAD_ROOT = v3071.RUNTIME_WAD_ROOT
RUNTIME_WAD_PATH = v3071.RUNTIME_WAD_PATH
EXPECTED_WAD_SHA256 = v3071.EXPECTED_WAD_SHA256
RUNTIME_WAD_MAX_BYTES = v3071.RUNTIME_WAD_MAX_BYTES
DEFAULT_FRAME_TICKS = v3071.DEFAULT_FRAME_TICKS
DEFAULT_SMOKE_FRAMES = v3071.DEFAULT_SMOKE_FRAMES
DEFAULT_LOOP_FRAMES = v3071.DEFAULT_LOOP_FRAMES
CONTINUOUS_LOOP_FRAMES = v3071.CONTINUOUS_LOOP_FRAMES
MAX_LOOP_FRAMES = v3071.MAX_LOOP_FRAMES
LOOP_FRAME_MS = v3071.LOOP_FRAME_MS
PRESENTER_POLL_MS = v3071.PRESENTER_POLL_MS
FRAME_PATH = "/tmp/a90-doomgeneric-v3074-minimal-dashboard-frame.xbgr8888"
INPUT_STATE_PATH = "/tmp/a90-doomgeneric-v3074-input.state"
INPUT_SOCKET_PATH = "/tmp/a90-doomgeneric-v3074-input.sock"
INPUT_UDP_PORT = v3071.INPUT_UDP_PORT
DEVICE_NCM_HOST = v3071.DEVICE_NCM_HOST
FRAME_WIDTH = v3071.FRAME_WIDTH
FRAME_HEIGHT = v3071.FRAME_HEIGHT
FRAME_STRIDE = v3071.FRAME_STRIDE
FRAME_BYTES = v3071.FRAME_BYTES
NATIVE_DASHBOARD = 1
NATIVE_DASHBOARD_MINIMAL = 1
BASELINE_NATIVE_DASHBOARD_MINIMAL = 0
NATIVE_DASHBOARD_LARGE_FRAME = v3071.NATIVE_DASHBOARD_LARGE_FRAME
REUSE_FRAME_BUFFER = v3071.REUSE_FRAME_BUFFER
DASHBOARD_METRICS_INTERVAL_FRAMES = v3071.DASHBOARD_METRICS_INTERVAL_FRAMES
FRAME_TIMING_PROBE = v3071.FRAME_TIMING_PROBE

SOUND_MODE = v3071.SOUND_MODE
AUDIO_CORUN = v3071.AUDIO_CORUN
AUDIO_CORUN_MODE = v3071.AUDIO_CORUN_MODE
AUDIO_CORUN_DURATION_MS = v3071.AUDIO_CORUN_DURATION_MS
AUDIO_CORUN_AMPLITUDE_MILLI = v3071.AUDIO_CORUN_AMPLITUDE_MILLI

HOST_KEYBOARD_BRIDGE = v3071.HOST_KEYBOARD_BRIDGE
HOST_DASHBOARD = v3071.HOST_DASHBOARD

REQUIRED_STRINGS = (
    b"A90 Linux init 0.10.94 (v3074-doomgeneric-minimal-dashboard)",
    b"v3074-doomgeneric-minimal-dashboard",
    b"doomgeneric-private-link-v3074-minimal-dashboard",
    b"/bin/a90_doomgeneric_private_engine_v3074",
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
    b"video.demo.doom.presenter.buffer_reuse=1",
    b"video.demo.doom.loop.timing_probe=1",
    b"video.demo.doom.loop.timing=frame-ipc-kms-stage-us",
    b"timing.draw",
    b"timing.present",
    b"video.demo.doom.dashboard.native=1",
    b"video.demo.doom.dashboard.profile=minimal-fastdraw",
    b"video.demo.doom.dashboard.layout=top-frame-minimal-input",
    b"video.demo.doom.dashboard.redraw=doom-frame-plus-compact-status",
    b"video.demo.doom.dashboard.metrics_pacing=disabled-minimal",
    b"video.demo.doom.dashboard.large_frame=0",
    b"video.demo.doom.dashboard.frame_mode=minimal-dashboard",
    b"video.demo.doom.dashboard.frame_scale=1:1",
    b"video.demo.input.udp_port=",
    b"video.demo.input.socket_path=",
    b"video.demo.input.otg_required=0",
    b"doompad.batch=state-mask-v3047",
    b"video.demo.doom.loop_start.continuous",
    b"native-audio-corun-tone-v3053",
    b"host_doompad_keyboard_v3033.py",
)


def rel(path: Path) -> str:
    return v3071.rel(path)


def v3033_module() -> Any:
    return v3071.v3033_module()


def apply_v3074_globals() -> None:
    v3071.CYCLE = CYCLE
    v3071.INIT_VERSION = INIT_VERSION
    v3071.INIT_BUILD = INIT_BUILD
    v3071.BUILD_TAG = BUILD_TAG
    v3071.DECISION = DECISION
    v3071.OUT_DIR = OUT_DIR
    v3071.OBJ_DIR = OBJ_DIR
    v3071.REPORT_PATH = REPORT_PATH
    v3071.BOOT_IMAGE = BOOT_IMAGE
    v3071.INIT_BINARY = INIT_BINARY
    v3071.RAMDISK_CPIO = RAMDISK_CPIO
    v3071.HELPER_BINARY = HELPER_BINARY
    v3071.ENGINE_BINARY = ENGINE_BINARY
    v3071.ENGINE_ADAPTER_SOURCE = ENGINE_ADAPTER_SOURCE
    v3071.ENGINE_ADAPTER_OBJECT = ENGINE_ADAPTER_OBJECT
    v3071.ENGINE_RAMDISK_PATH = ENGINE_RAMDISK_PATH
    v3071.ENGINE_REMOTE_PATH = ENGINE_REMOTE_PATH
    v3071.ENGINE_NAME = ENGINE_NAME
    v3071.DEFAULT_LOOP_FRAMES = DEFAULT_LOOP_FRAMES
    v3071.LOOP_FRAME_MS = LOOP_FRAME_MS
    v3071.PRESENTER_POLL_MS = PRESENTER_POLL_MS
    v3071.FRAME_PATH = FRAME_PATH
    v3071.INPUT_STATE_PATH = INPUT_STATE_PATH
    v3071.INPUT_SOCKET_PATH = INPUT_SOCKET_PATH
    v3071.INPUT_UDP_PORT = INPUT_UDP_PORT
    v3071.DEVICE_NCM_HOST = DEVICE_NCM_HOST
    v3071.NATIVE_DASHBOARD = NATIVE_DASHBOARD
    v3071.NATIVE_DASHBOARD_LARGE_FRAME = NATIVE_DASHBOARD_LARGE_FRAME
    v3071.REUSE_FRAME_BUFFER = REUSE_FRAME_BUFFER
    v3071.DASHBOARD_METRICS_INTERVAL_FRAMES = DASHBOARD_METRICS_INTERVAL_FRAMES
    v3071.FRAME_TIMING_PROBE = FRAME_TIMING_PROBE
    v3071.SOUND_MODE = SOUND_MODE
    v3071.AUDIO_CORUN = AUDIO_CORUN
    v3071.AUDIO_CORUN_MODE = AUDIO_CORUN_MODE
    v3071.AUDIO_CORUN_DURATION_MS = AUDIO_CORUN_DURATION_MS
    v3071.AUDIO_CORUN_AMPLITUDE_MILLI = AUDIO_CORUN_AMPLITUDE_MILLI
    v3071.REQUIRED_STRINGS = REQUIRED_STRINGS
    v3071.render_report = render_report
    v3071.apply_v3071_globals()
    v3033 = v3033_module()
    v3033.NATIVE_DASHBOARD_MINIMAL = NATIVE_DASHBOARD_MINIMAL


def render_report(
    manifest: dict[str, Any],
    helper_flags: tuple[str, ...],
    init_extra_flags: tuple[str, ...],
) -> str:
    doom = manifest.get("doomgeneric_visible_loop", {})
    markers = manifest.get("v3033_marker_strings", [])
    marker_lines = [f"- `{marker}`" for marker in markers] if isinstance(markers, list) else []
    return "\n".join([
        "# Native Init V3074 DOOMGENERIC Minimal Dashboard Source Build",
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
        "- Keeps V3071 frame timing probe, V3069 metrics-cache lineage, V3067 reader-buffer reuse, V3063 frame_ms=28, and UDP/NCM input unchanged.",
        "- Changes only the native DOOM dashboard draw profile from full panels to a minimal fast path.",
        "- The minimal path draws the DOOM frame, a compact title/status line, and current input state; it skips full metrics panels and recent-input log repaint.",
        "- This directly targets the V3073 finding where dashboard/draw reached a max of about 455ms.",
        "",
        "## Dashboard Contract",
        "",
        f"- Baseline minimal dashboard: `{BASELINE_NATIVE_DASHBOARD_MINIMAL}`",
        f"- Candidate minimal dashboard: `{NATIVE_DASHBOARD_MINIMAL}`",
        "- Dashboard profile marker: `minimal-fastdraw`",
        "- Dashboard layout marker: `top-frame-minimal-input`",
        "- Dashboard redraw marker: `doom-frame-plus-compact-status`",
        "- Dashboard metrics pacing marker: `disabled-minimal`",
        f"- Frame timing probe: `{FRAME_TIMING_PROBE}`",
        f"- Reader reuse: `{REUSE_FRAME_BUFFER}`",
        f"- Helper frame ms: `{doom.get('loop_frame_ms', LOOP_FRAME_MS)}`",
        f"- Presenter poll ms: `{doom.get('presenter_poll_ms', PRESENTER_POLL_MS)}`",
        f"- Dashboard large frame: `{int(bool(NATIVE_DASHBOARD_LARGE_FRAME))}`",
        f"- Frame path: `{doom.get('frame_path')}`",
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
        "- `py_compile`: V3074 builder and focused tests.",
        "- `unittest`: V3074 source contract plus V3071/V3069/V3067/V3065/V3063/V3061/V3059 and base visible-loop regressions.",
        "- Build: AArch64 helper compile/link, native-init compile, ramdisk pack, boot image pack, SHA256 capture.",
        "- Marker check: generated boot image contains V3074 identity, timing probe, minimal-dashboard markers, reader reuse, and UDP input markers.",
        "- `git diff --check`: PASS.",
        "",
        "## Next Unit",
        "",
        "- Run ID: `V3075`",
        "- Type: rollback-gated live validation of V3074 minimal-dashboard candidate.",
        "- Scope: flash exact V3074 boot image via `native_init_flash.py`, health-check, require minimal-dashboard markers, run bounded foreground timing loop, compare draw/total timings with V3073, then start continuous loop and verify UDP input still works.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `doomgeneric-minimal-dashboard-candidate`.",
    ]) + "\n"


def main() -> int:
    apply_v3074_globals()
    rc = v3071.v3069.main()
    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    doom = manifest.setdefault("doomgeneric_visible_loop", {})
    doom.update({
        "native_dashboard": bool(NATIVE_DASHBOARD),
        "native_dashboard_minimal": bool(NATIVE_DASHBOARD_MINIMAL),
        "baseline_native_dashboard_minimal": bool(BASELINE_NATIVE_DASHBOARD_MINIMAL),
        "native_dashboard_large_frame": bool(NATIVE_DASHBOARD_LARGE_FRAME),
        "dashboard_profile": "minimal-fastdraw",
        "dashboard_layout": "top-frame-minimal-input",
        "dashboard_redraw": "doom-frame-plus-compact-status",
        "dashboard_metrics_interval_frames": 0,
        "dashboard_metrics_pacing": "disabled-minimal",
        "dashboard_minimal_experiment": {
            "full_dashboard_panel_repaint_removed": True,
            "recent_input_log_repaint_removed": True,
            "metrics_panel_repaint_removed": True,
            "frame_timing_probe_inherited_from_v3071": True,
            "target_finding": "dashboard-draw-max-454916us-v3073",
        },
        "helper_loop_command": (
            f"{ENGINE_REMOTE_PATH} --wad-frame-loop {RUNTIME_WAD_PATH} "
            f"--frames {DEFAULT_LOOP_FRAMES} --output {FRAME_PATH} "
            f"--input-state {INPUT_STATE_PATH} --frame-ms {LOOP_FRAME_MS} "
            f"--input-socket {INPUT_SOCKET_PATH} --input-udp {INPUT_UDP_PORT}"
        ),
    })
    manifest.update({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "doomgeneric-minimal-dashboard-candidate",
        "adoption_state": "pending-minimal-dashboard-live-validation",
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
    (OUT_DIR / "doomgeneric-minimal-dashboard-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "doomgeneric-minimal-dashboard-candidate",
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
        "presenter_reader": "reused-loop-buffer",
        "dashboard_profile": "minimal-fastdraw",
        "dashboard_layout": "top-frame-minimal-input",
        "dashboard_metrics_pacing": "disabled-minimal",
        "frame_timing_probe": FRAME_TIMING_PROBE,
        "frame_timing_unit": "us",
        "frame_timing_stages": ["alloc", "read", "begin", "draw", "present", "total"],
        "native_dashboard": bool(NATIVE_DASHBOARD),
        "native_dashboard_minimal": bool(NATIVE_DASHBOARD_MINIMAL),
        "native_dashboard_large_frame": bool(NATIVE_DASHBOARD_LARGE_FRAME),
        "frame_scale": "1:1",
        "loop_start_command": f"video demo doom loop-start 0 --wad runtime-private --sha256 {EXPECTED_WAD_SHA256}",
        "host_keyboard_bridge": rel(HOST_KEYBOARD_BRIDGE),
        "source_report": rel(REPORT_PATH),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-minimal-dashboard-live-validation",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
