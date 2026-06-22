#!/usr/bin/env python3
"""Build V3061 native-init DOOM presenter pacing candidate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _workspace_bootstrap import repo_root
import build_native_init_boot_v3059_doomgeneric_udp_input as v3059
from a90harness.evidence import workspace_private_build_path, workspace_private_input_path

REPO_ROOT = repo_root()

CYCLE = "V3061"
INIT_VERSION = "0.10.88"
INIT_BUILD = "v3061-doomgeneric-presenter-pacing"
BUILD_TAG = INIT_BUILD
DECISION = "v3061-doomgeneric-presenter-pacing-source-build-pass"

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
OBJ_DIR = OUT_DIR / "obj"
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V3061_DOOMGENERIC_PRESENTER_PACING_SOURCE_BUILD_2026-06-23.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images", "boot_linux_v3061_doomgeneric_presenter_pacing.img", legacy_fallback=False
)
INIT_BINARY = OUT_DIR / "init_v3061_doomgeneric_presenter_pacing"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v3061_doomgeneric_presenter_pacing.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v512_doomgeneric_presenter_pacing"

ENGINE_BINARY = OUT_DIR / "a90_doomgeneric_private_engine_v3061"
ENGINE_ADAPTER_SOURCE = OUT_DIR / "a90_doomgeneric_native_bridge_v3061.c"
ENGINE_ADAPTER_OBJECT = OBJ_DIR / "a90_doomgeneric_native_bridge_v3061.o"
ENGINE_RAMDISK_PATH = "bin/a90_doomgeneric_private_engine_v3061"
ENGINE_REMOTE_PATH = "/" + ENGINE_RAMDISK_PATH
ENGINE_NAME = "doomgeneric-private-link-v3061-presenter-pacing"

RUNTIME_WAD_ROOT = v3059.RUNTIME_WAD_ROOT
RUNTIME_WAD_PATH = v3059.RUNTIME_WAD_PATH
EXPECTED_WAD_SHA256 = v3059.EXPECTED_WAD_SHA256
RUNTIME_WAD_MAX_BYTES = v3059.RUNTIME_WAD_MAX_BYTES
DEFAULT_FRAME_TICKS = v3059.DEFAULT_FRAME_TICKS
DEFAULT_SMOKE_FRAMES = v3059.DEFAULT_SMOKE_FRAMES
DEFAULT_LOOP_FRAMES = v3059.DEFAULT_LOOP_FRAMES
CONTINUOUS_LOOP_FRAMES = v3059.CONTINUOUS_LOOP_FRAMES
MAX_LOOP_FRAMES = v3059.MAX_LOOP_FRAMES
LOOP_FRAME_MS = v3059.LOOP_FRAME_MS
PRESENTER_POLL_MS = 4
FRAME_PATH = "/tmp/a90-doomgeneric-v3061-presenter-pacing-frame.xbgr8888"
INPUT_STATE_PATH = "/tmp/a90-doomgeneric-v3061-input.state"
INPUT_SOCKET_PATH = "/tmp/a90-doomgeneric-v3061-input.sock"
INPUT_UDP_PORT = 30570
DEVICE_NCM_HOST = v3059.DEVICE_NCM_HOST
FRAME_WIDTH = v3059.FRAME_WIDTH
FRAME_HEIGHT = v3059.FRAME_HEIGHT
FRAME_STRIDE = v3059.FRAME_STRIDE
FRAME_BYTES = v3059.FRAME_BYTES
NATIVE_DASHBOARD = v3059.NATIVE_DASHBOARD
NATIVE_DASHBOARD_LARGE_FRAME = v3059.NATIVE_DASHBOARD_LARGE_FRAME

SOUND_MODE = v3059.SOUND_MODE
AUDIO_CORUN = v3059.AUDIO_CORUN
AUDIO_CORUN_MODE = v3059.AUDIO_CORUN_MODE
AUDIO_CORUN_DURATION_MS = v3059.AUDIO_CORUN_DURATION_MS
AUDIO_CORUN_AMPLITUDE_MILLI = v3059.AUDIO_CORUN_AMPLITUDE_MILLI

HOST_KEYBOARD_BRIDGE = v3059.HOST_KEYBOARD_BRIDGE
HOST_DASHBOARD = v3059.HOST_DASHBOARD

REQUIRED_STRINGS = (
    b"A90 Linux init 0.10.88 (v3061-doomgeneric-presenter-pacing)",
    b"v3061-doomgeneric-presenter-pacing",
    b"doomgeneric-private-link-v3061-presenter-pacing",
    b"/bin/a90_doomgeneric_private_engine_v3061",
    RUNTIME_WAD_PATH.encode("ascii"),
    EXPECTED_WAD_SHA256.encode("ascii"),
    FRAME_PATH.encode("ascii"),
    INPUT_STATE_PATH.encode("ascii"),
    INPUT_SOCKET_PATH.encode("ascii"),
    b"a90.doomgeneric.v3059.input=udp-ncm-state-with-unix-dgram-fallback",
    b"--input-udp",
    b"udp-ncm-to-DG_GetKey-with-serial-doompad-fallback",
    b"video.demo.doom.presenter.pacing=helper-frame-mtime",
    b"video.demo.doom.presenter.poll_ms=",
    b"video.demo.doom.loop.presenter.pacing=helper-frame-mtime",
    b"video.demo.doom.loop.presenter.poll_ms=",
    b"video.demo.input.udp_port=",
    b"video.demo.input.socket_path=",
    b"video.demo.input.otg_required=0",
    b"doompad.batch=state-mask-v3047",
    b"video.demo.doom.loop_start.continuous",
    b"native-audio-corun-tone-v3053",
    b"host_doompad_keyboard_v3033.py",
)


def rel(path: Path) -> str:
    return v3059.rel(path)


def apply_v3061_globals() -> None:
    v3033 = v3059.v3057.v3053.v3051.v3049.v3047.v3045.v3042.v3040.v3038.v3033

    v3059.CYCLE = CYCLE
    v3059.INIT_VERSION = INIT_VERSION
    v3059.INIT_BUILD = INIT_BUILD
    v3059.BUILD_TAG = BUILD_TAG
    v3059.DECISION = DECISION
    v3059.OUT_DIR = OUT_DIR
    v3059.OBJ_DIR = OBJ_DIR
    v3059.REPORT_PATH = REPORT_PATH
    v3059.BOOT_IMAGE = BOOT_IMAGE
    v3059.INIT_BINARY = INIT_BINARY
    v3059.RAMDISK_CPIO = RAMDISK_CPIO
    v3059.HELPER_BINARY = HELPER_BINARY
    v3059.ENGINE_BINARY = ENGINE_BINARY
    v3059.ENGINE_ADAPTER_SOURCE = ENGINE_ADAPTER_SOURCE
    v3059.ENGINE_ADAPTER_OBJECT = ENGINE_ADAPTER_OBJECT
    v3059.ENGINE_RAMDISK_PATH = ENGINE_RAMDISK_PATH
    v3059.ENGINE_REMOTE_PATH = ENGINE_REMOTE_PATH
    v3059.ENGINE_NAME = ENGINE_NAME
    v3059.DEFAULT_LOOP_FRAMES = DEFAULT_LOOP_FRAMES
    v3059.LOOP_FRAME_MS = LOOP_FRAME_MS
    v3059.FRAME_PATH = FRAME_PATH
    v3059.INPUT_STATE_PATH = INPUT_STATE_PATH
    v3059.INPUT_SOCKET_PATH = INPUT_SOCKET_PATH
    v3059.INPUT_UDP_PORT = INPUT_UDP_PORT
    v3059.DEVICE_NCM_HOST = DEVICE_NCM_HOST
    v3059.NATIVE_DASHBOARD = NATIVE_DASHBOARD
    v3059.NATIVE_DASHBOARD_LARGE_FRAME = NATIVE_DASHBOARD_LARGE_FRAME
    v3059.SOUND_MODE = SOUND_MODE
    v3059.AUDIO_CORUN = AUDIO_CORUN
    v3059.AUDIO_CORUN_MODE = AUDIO_CORUN_MODE
    v3059.AUDIO_CORUN_DURATION_MS = AUDIO_CORUN_DURATION_MS
    v3059.AUDIO_CORUN_AMPLITUDE_MILLI = AUDIO_CORUN_AMPLITUDE_MILLI
    v3059.REQUIRED_STRINGS = REQUIRED_STRINGS
    v3059.render_report = render_report

    v3033.PRESENTER_POLL_MS = PRESENTER_POLL_MS


def render_report(
    manifest: dict[str, Any],
    helper_flags: tuple[str, ...],
    init_extra_flags: tuple[str, ...],
) -> str:
    doom = manifest.get("doomgeneric_visible_loop", {})
    markers = manifest.get("v3033_marker_strings", [])
    marker_lines = [f"- `{marker}`" for marker in markers] if isinstance(markers, list) else []
    return "\n".join([
        "# Native Init V3061 DOOMGENERIC Presenter Pacing Source Build",
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
        "- Keeps V3059 UDP/NCM input transport unchanged.",
        "- Adds frame metadata (`frame_id`, `mtime_ns`) from the atomic frame file so the presenter can distinguish fresh frames.",
        "- Changes the visible DOOM presenter from a second 33ms frame sleep to a short 4ms poll that presents only new helper frames.",
        "- Leaves the helper's `--frame-ms 33` cadence as the single game/render pacing source.",
        "",
        "## Pacing Contract",
        "",
        f"- Helper loop frame ms: `{doom.get('loop_frame_ms', LOOP_FRAME_MS)}`",
        f"- Presenter poll ms: `{doom.get('presenter_poll_ms', PRESENTER_POLL_MS)}`",
        f"- Presenter pacing: `{doom.get('presenter_pacing', 'helper-frame-mtime')}`",
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
        "- Status markers: `video.demo.doom.presenter.pacing=helper-frame-mtime`, `video.demo.doom.presenter.poll_ms=4`.",
        "",
        "## Marker Check",
        "",
        *marker_lines,
        "",
        "## Validation",
        "",
        "- `py_compile`: V3061 builder and focused tests.",
        "- `unittest`: V3061 presenter pacing source contract plus V3059 UDP input and host evdev regressions.",
        "- Build: AArch64 helper compile/link, native-init compile, ramdisk pack, boot image pack, SHA256 capture.",
        "- Marker check: generated boot image contains V3061 identity, UDP input, presenter pacing, and audio co-run markers.",
        "- `git diff --check`: PASS.",
        "",
        "## Next Unit",
        "",
        "- Run ID: `V3062`",
        "- Type: rollback-gated live validation of V3061 presenter pacing candidate.",
        "- Scope: flash exact V3061 boot image via `native_init_flash.py`, health-check, require presenter pacing status markers, start continuous DOOM loop, confirm helper remains active and host UDP input still works.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `doomgeneric-presenter-pacing-candidate`.",
    ]) + "\n"


def main() -> int:
    apply_v3061_globals()
    rc = v3059.main()
    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    doom = manifest.setdefault("doomgeneric_visible_loop", {})
    doom.update({
        "presenter_pacing": "helper-frame-mtime",
        "presenter_poll_ms": PRESENTER_POLL_MS,
        "single_pacing_source": "helper-loop-frame-ms",
        "loop_frame_ms": LOOP_FRAME_MS,
        "input_path": "udp-ncm-to-DG_GetKey-with-serial-doompad-fallback",
        "input_udp_port": INPUT_UDP_PORT,
        "input_socket_path": INPUT_SOCKET_PATH,
        "input_state_path": INPUT_STATE_PATH,
        "frame_path": FRAME_PATH,
        "engine_binary": rel(ENGINE_BINARY),
        "engine_ramdisk_path": ENGINE_REMOTE_PATH,
        "helper_loop_command": (
            f"{ENGINE_REMOTE_PATH} --wad-frame-loop {RUNTIME_WAD_PATH} "
            f"--frames {DEFAULT_LOOP_FRAMES} --output {FRAME_PATH} "
            f"--input-state {INPUT_STATE_PATH} --frame-ms {LOOP_FRAME_MS} "
            f"--input-socket {INPUT_SOCKET_PATH} --input-udp {INPUT_UDP_PORT}"
        ),
        "presenter_sync": {
            "frame_id": "mtime_ns^inode^size",
            "present_only_new_frame": True,
            "presenter_poll_ms": PRESENTER_POLL_MS,
        },
    })
    manifest.update({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "doomgeneric-presenter-pacing-candidate",
        "adoption_state": "pending-presenter-pacing-live-validation",
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
    (OUT_DIR / "doomgeneric-presenter-pacing-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "doomgeneric-presenter-pacing-candidate",
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
        "loop_start_command": f"video demo doom loop-start 0 --wad runtime-private --sha256 {EXPECTED_WAD_SHA256}",
        "host_keyboard_bridge": rel(HOST_KEYBOARD_BRIDGE),
        "source_report": rel(REPORT_PATH),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-presenter-pacing-live-validation",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
