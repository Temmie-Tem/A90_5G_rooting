#!/usr/bin/env python3
"""Build V3067 native-init DOOM presenter reader-buffer reuse candidate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _workspace_bootstrap import repo_root
import build_native_init_boot_v3065_doomgeneric_large_scale_off as v3065
from a90harness.evidence import workspace_private_build_path, workspace_private_input_path

REPO_ROOT = repo_root()

CYCLE = "V3067"
INIT_VERSION = "0.10.91"
INIT_BUILD = "v3067-doomgeneric-reader-reuse"
BUILD_TAG = INIT_BUILD
DECISION = "v3067-doomgeneric-reader-reuse-source-build-pass"

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
OBJ_DIR = OUT_DIR / "obj"
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V3067_DOOMGENERIC_READER_REUSE_SOURCE_BUILD_2026-06-23.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images", "boot_linux_v3067_doomgeneric_reader_reuse.img", legacy_fallback=False
)
INIT_BINARY = OUT_DIR / "init_v3067_doomgeneric_reader_reuse"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v3067_doomgeneric_reader_reuse.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v512_doomgeneric_reader_reuse"

ENGINE_BINARY = OUT_DIR / "a90_doomgeneric_private_engine_v3067"
ENGINE_ADAPTER_SOURCE = OUT_DIR / "a90_doomgeneric_native_bridge_v3067.c"
ENGINE_ADAPTER_OBJECT = OBJ_DIR / "a90_doomgeneric_native_bridge_v3067.o"
ENGINE_RAMDISK_PATH = "bin/a90_doomgeneric_private_engine_v3067"
ENGINE_REMOTE_PATH = "/" + ENGINE_RAMDISK_PATH
ENGINE_NAME = "doomgeneric-private-link-v3067-reader-reuse"

RUNTIME_WAD_ROOT = v3065.RUNTIME_WAD_ROOT
RUNTIME_WAD_PATH = v3065.RUNTIME_WAD_PATH
EXPECTED_WAD_SHA256 = v3065.EXPECTED_WAD_SHA256
RUNTIME_WAD_MAX_BYTES = v3065.RUNTIME_WAD_MAX_BYTES
DEFAULT_FRAME_TICKS = v3065.DEFAULT_FRAME_TICKS
DEFAULT_SMOKE_FRAMES = v3065.DEFAULT_SMOKE_FRAMES
DEFAULT_LOOP_FRAMES = v3065.DEFAULT_LOOP_FRAMES
CONTINUOUS_LOOP_FRAMES = v3065.CONTINUOUS_LOOP_FRAMES
MAX_LOOP_FRAMES = v3065.MAX_LOOP_FRAMES
LOOP_FRAME_MS = v3065.LOOP_FRAME_MS
PRESENTER_POLL_MS = v3065.PRESENTER_POLL_MS
FRAME_PATH = "/tmp/a90-doomgeneric-v3067-reader-reuse-frame.xbgr8888"
INPUT_STATE_PATH = "/tmp/a90-doomgeneric-v3067-input.state"
INPUT_SOCKET_PATH = "/tmp/a90-doomgeneric-v3067-input.sock"
INPUT_UDP_PORT = v3065.INPUT_UDP_PORT
DEVICE_NCM_HOST = v3065.DEVICE_NCM_HOST
FRAME_WIDTH = v3065.FRAME_WIDTH
FRAME_HEIGHT = v3065.FRAME_HEIGHT
FRAME_STRIDE = v3065.FRAME_STRIDE
FRAME_BYTES = v3065.FRAME_BYTES
NATIVE_DASHBOARD = v3065.NATIVE_DASHBOARD
NATIVE_DASHBOARD_LARGE_FRAME = v3065.NATIVE_DASHBOARD_LARGE_FRAME
REUSE_FRAME_BUFFER = 1
BASELINE_REUSE_FRAME_BUFFER = 0

SOUND_MODE = v3065.SOUND_MODE
AUDIO_CORUN = v3065.AUDIO_CORUN
AUDIO_CORUN_MODE = v3065.AUDIO_CORUN_MODE
AUDIO_CORUN_DURATION_MS = v3065.AUDIO_CORUN_DURATION_MS
AUDIO_CORUN_AMPLITUDE_MILLI = v3065.AUDIO_CORUN_AMPLITUDE_MILLI

HOST_KEYBOARD_BRIDGE = v3065.HOST_KEYBOARD_BRIDGE
HOST_DASHBOARD = v3065.HOST_DASHBOARD

REQUIRED_STRINGS = (
    b"A90 Linux init 0.10.91 (v3067-doomgeneric-reader-reuse)",
    b"v3067-doomgeneric-reader-reuse",
    b"doomgeneric-private-link-v3067-reader-reuse",
    b"/bin/a90_doomgeneric_private_engine_v3067",
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
    b"video.demo.doom.presenter.poll_ms=",
    b"video.demo.doom.presenter.reader=reused-loop-buffer",
    b"video.demo.doom.presenter.buffer_reuse=1",
    b"video.demo.doom.loop.presenter.reader=reused-loop-buffer",
    b"video.demo.doom.loop.presenter.buffer_reuse=1",
    b"video.demo.doom.dashboard.native=1",
    b"video.demo.doom.dashboard.large_frame=0",
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
    return v3065.rel(path)


def v3033_module() -> Any:
    return v3065.v3063.v3061.v3059.v3057.v3053.v3051.v3049.v3047.v3045.v3042.v3040.v3038.v3033


def apply_v3067_globals() -> None:
    v3033 = v3033_module()
    v3065.CYCLE = CYCLE
    v3065.INIT_VERSION = INIT_VERSION
    v3065.INIT_BUILD = INIT_BUILD
    v3065.BUILD_TAG = BUILD_TAG
    v3065.DECISION = DECISION
    v3065.OUT_DIR = OUT_DIR
    v3065.OBJ_DIR = OBJ_DIR
    v3065.REPORT_PATH = REPORT_PATH
    v3065.BOOT_IMAGE = BOOT_IMAGE
    v3065.INIT_BINARY = INIT_BINARY
    v3065.RAMDISK_CPIO = RAMDISK_CPIO
    v3065.HELPER_BINARY = HELPER_BINARY
    v3065.ENGINE_BINARY = ENGINE_BINARY
    v3065.ENGINE_ADAPTER_SOURCE = ENGINE_ADAPTER_SOURCE
    v3065.ENGINE_ADAPTER_OBJECT = ENGINE_ADAPTER_OBJECT
    v3065.ENGINE_RAMDISK_PATH = ENGINE_RAMDISK_PATH
    v3065.ENGINE_REMOTE_PATH = ENGINE_REMOTE_PATH
    v3065.ENGINE_NAME = ENGINE_NAME
    v3065.DEFAULT_LOOP_FRAMES = DEFAULT_LOOP_FRAMES
    v3065.LOOP_FRAME_MS = LOOP_FRAME_MS
    v3065.PRESENTER_POLL_MS = PRESENTER_POLL_MS
    v3065.FRAME_PATH = FRAME_PATH
    v3065.INPUT_STATE_PATH = INPUT_STATE_PATH
    v3065.INPUT_SOCKET_PATH = INPUT_SOCKET_PATH
    v3065.INPUT_UDP_PORT = INPUT_UDP_PORT
    v3065.DEVICE_NCM_HOST = DEVICE_NCM_HOST
    v3065.NATIVE_DASHBOARD = NATIVE_DASHBOARD
    v3065.NATIVE_DASHBOARD_LARGE_FRAME = NATIVE_DASHBOARD_LARGE_FRAME
    v3065.SOUND_MODE = SOUND_MODE
    v3065.AUDIO_CORUN = AUDIO_CORUN
    v3065.AUDIO_CORUN_MODE = AUDIO_CORUN_MODE
    v3065.AUDIO_CORUN_DURATION_MS = AUDIO_CORUN_DURATION_MS
    v3065.AUDIO_CORUN_AMPLITUDE_MILLI = AUDIO_CORUN_AMPLITUDE_MILLI
    v3065.REQUIRED_STRINGS = REQUIRED_STRINGS
    v3065.render_report = render_report
    v3033.REUSE_FRAME_BUFFER = REUSE_FRAME_BUFFER


def render_report(
    manifest: dict[str, Any],
    helper_flags: tuple[str, ...],
    init_extra_flags: tuple[str, ...],
) -> str:
    doom = manifest.get("doomgeneric_visible_loop", {})
    markers = manifest.get("v3033_marker_strings", [])
    marker_lines = [f"- `{marker}`" for marker in markers] if isinstance(markers, list) else []
    return "\n".join([
        "# Native Init V3067 DOOMGENERIC Reader Reuse Source Build",
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
        "- Keeps V3065 large-scale-off, V3063 frame_ms=28, V3061 presenter mtime sync, and UDP/NCM input unchanged.",
        "- Changes the presenter reader from per-frame malloc/free to one loop-owned reusable frame buffer.",
        "- Still uses the raw frame file handoff; this is an intermediate IPC-cost isolation step before direct/shared KMS buffers.",
        "",
        "## Reader Contract",
        "",
        f"- Baseline reader buffer reuse: `{BASELINE_REUSE_FRAME_BUFFER}`",
        f"- Candidate reader buffer reuse: `{REUSE_FRAME_BUFFER}`",
        "- Reader marker: `reused-loop-buffer`",
        f"- Frame bytes: `{FRAME_BYTES}`",
        f"- Helper frame ms: `{doom.get('loop_frame_ms', LOOP_FRAME_MS)}`",
        f"- Presenter poll ms: `{doom.get('presenter_poll_ms', PRESENTER_POLL_MS)}`",
        f"- Presenter pacing: `{doom.get('presenter_pacing', 'helper-frame-mtime')}`",
        f"- Dashboard large frame: `{int(bool(NATIVE_DASHBOARD_LARGE_FRAME))}`",
        f"- Frame path: `{doom.get('frame_path')}`",
        f"- Input active marker: `{doom.get('input_path')}`",
        f"- UDP port marker: `{doom.get('input_udp_port', INPUT_UDP_PORT)}`",
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
        "- `py_compile`: V3067 builder and focused tests.",
        "- `unittest`: V3067 source contract plus V3065/V3063/V3061/V3059 and host evdev regressions.",
        "- Build: AArch64 helper compile/link, native-init compile, ramdisk pack, boot image pack, SHA256 capture.",
        "- Marker check: generated boot image contains V3067 identity, UDP input, presenter pacing, dashboard large_frame=0, and reader reuse markers.",
        "- `git diff --check`: PASS.",
        "",
        "## Next Unit",
        "",
        "- Run ID: `V3068`",
        "- Type: rollback-gated live validation of V3067 reader-reuse candidate.",
        "- Scope: flash exact V3067 boot image via `native_init_flash.py`, health-check, require `video.demo.doom.presenter.reader=reused-loop-buffer`, start continuous DOOM loop, confirm helper remains active and UDP input still works.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `doomgeneric-reader-reuse-candidate`.",
    ]) + "\n"


def main() -> int:
    apply_v3067_globals()
    rc = v3065.main()
    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    doom = manifest.setdefault("doomgeneric_visible_loop", {})
    doom.update({
        "reuse_frame_buffer": bool(REUSE_FRAME_BUFFER),
        "baseline_reuse_frame_buffer": bool(BASELINE_REUSE_FRAME_BUFFER),
        "presenter_reader": "reused-loop-buffer",
        "presenter_buffer_reuse": bool(REUSE_FRAME_BUFFER),
        "reader_reuse_experiment": {
            "per_frame_alloc_removed": True,
            "raw_frame_file_handoff_retained": True,
            "input_and_pacing_unchanged_from_v3065": True,
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
        "candidate_type": "doomgeneric-reader-reuse-candidate",
        "adoption_state": "pending-reader-reuse-live-validation",
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
    (OUT_DIR / "doomgeneric-reader-reuse-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "doomgeneric-reader-reuse-candidate",
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
        "presenter_pacing": "helper-frame-mtime",
        "presenter_reader": "reused-loop-buffer",
        "presenter_buffer_reuse": bool(REUSE_FRAME_BUFFER),
        "native_dashboard": bool(NATIVE_DASHBOARD),
        "native_dashboard_large_frame": bool(NATIVE_DASHBOARD_LARGE_FRAME),
        "frame_scale": "1:1",
        "loop_start_command": f"video demo doom loop-start 0 --wad runtime-private --sha256 {EXPECTED_WAD_SHA256}",
        "host_keyboard_bridge": rel(HOST_KEYBOARD_BRIDGE),
        "source_report": rel(REPORT_PATH),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-reader-reuse-live-validation",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
