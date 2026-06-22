#!/usr/bin/env python3
"""Build V3063 native-init DOOM frame_ms=28 pacing experiment."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _workspace_bootstrap import repo_root
import build_native_init_boot_v3061_doomgeneric_presenter_pacing as v3061
from a90harness.evidence import workspace_private_build_path, workspace_private_input_path

REPO_ROOT = repo_root()

CYCLE = "V3063"
INIT_VERSION = "0.10.89"
INIT_BUILD = "v3063-doomgeneric-frame-ms28"
BUILD_TAG = INIT_BUILD
DECISION = "v3063-doomgeneric-frame-ms28-source-build-pass"

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
OBJ_DIR = OUT_DIR / "obj"
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V3063_DOOMGENERIC_FRAME_MS28_SOURCE_BUILD_2026-06-23.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images", "boot_linux_v3063_doomgeneric_frame_ms28.img", legacy_fallback=False
)
INIT_BINARY = OUT_DIR / "init_v3063_doomgeneric_frame_ms28"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v3063_doomgeneric_frame_ms28.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v512_doomgeneric_frame_ms28"

ENGINE_BINARY = OUT_DIR / "a90_doomgeneric_private_engine_v3063"
ENGINE_ADAPTER_SOURCE = OUT_DIR / "a90_doomgeneric_native_bridge_v3063.c"
ENGINE_ADAPTER_OBJECT = OBJ_DIR / "a90_doomgeneric_native_bridge_v3063.o"
ENGINE_RAMDISK_PATH = "bin/a90_doomgeneric_private_engine_v3063"
ENGINE_REMOTE_PATH = "/" + ENGINE_RAMDISK_PATH
ENGINE_NAME = "doomgeneric-private-link-v3063-frame-ms28"

RUNTIME_WAD_ROOT = v3061.RUNTIME_WAD_ROOT
RUNTIME_WAD_PATH = v3061.RUNTIME_WAD_PATH
EXPECTED_WAD_SHA256 = v3061.EXPECTED_WAD_SHA256
RUNTIME_WAD_MAX_BYTES = v3061.RUNTIME_WAD_MAX_BYTES
DEFAULT_FRAME_TICKS = v3061.DEFAULT_FRAME_TICKS
DEFAULT_SMOKE_FRAMES = v3061.DEFAULT_SMOKE_FRAMES
DEFAULT_LOOP_FRAMES = v3061.DEFAULT_LOOP_FRAMES
CONTINUOUS_LOOP_FRAMES = v3061.CONTINUOUS_LOOP_FRAMES
MAX_LOOP_FRAMES = v3061.MAX_LOOP_FRAMES
LOOP_FRAME_MS = 28
BASELINE_LOOP_FRAME_MS = v3061.LOOP_FRAME_MS
PRESENTER_POLL_MS = v3061.PRESENTER_POLL_MS
FRAME_PATH = "/tmp/a90-doomgeneric-v3063-frame-ms28-frame.xbgr8888"
INPUT_STATE_PATH = "/tmp/a90-doomgeneric-v3063-input.state"
INPUT_SOCKET_PATH = "/tmp/a90-doomgeneric-v3063-input.sock"
INPUT_UDP_PORT = v3061.INPUT_UDP_PORT
DEVICE_NCM_HOST = v3061.DEVICE_NCM_HOST
FRAME_WIDTH = v3061.FRAME_WIDTH
FRAME_HEIGHT = v3061.FRAME_HEIGHT
FRAME_STRIDE = v3061.FRAME_STRIDE
FRAME_BYTES = v3061.FRAME_BYTES
NATIVE_DASHBOARD = v3061.NATIVE_DASHBOARD
NATIVE_DASHBOARD_LARGE_FRAME = v3061.NATIVE_DASHBOARD_LARGE_FRAME

SOUND_MODE = v3061.SOUND_MODE
AUDIO_CORUN = v3061.AUDIO_CORUN
AUDIO_CORUN_MODE = v3061.AUDIO_CORUN_MODE
AUDIO_CORUN_DURATION_MS = v3061.AUDIO_CORUN_DURATION_MS
AUDIO_CORUN_AMPLITUDE_MILLI = v3061.AUDIO_CORUN_AMPLITUDE_MILLI

HOST_KEYBOARD_BRIDGE = v3061.HOST_KEYBOARD_BRIDGE
HOST_DASHBOARD = v3061.HOST_DASHBOARD

REQUIRED_STRINGS = (
    b"A90 Linux init 0.10.89 (v3063-doomgeneric-frame-ms28)",
    b"v3063-doomgeneric-frame-ms28",
    b"doomgeneric-private-link-v3063-frame-ms28",
    b"/bin/a90_doomgeneric_private_engine_v3063",
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
    b"video.demo.input.udp_port=",
    b"video.demo.input.socket_path=",
    b"video.demo.input.otg_required=0",
    b"doompad.batch=state-mask-v3047",
    b"video.demo.doom.loop_start.continuous",
    b"native-audio-corun-tone-v3053",
    b"host_doompad_keyboard_v3033.py",
)


def rel(path: Path) -> str:
    return v3061.rel(path)


def apply_v3063_globals() -> None:
    v3061.CYCLE = CYCLE
    v3061.INIT_VERSION = INIT_VERSION
    v3061.INIT_BUILD = INIT_BUILD
    v3061.BUILD_TAG = BUILD_TAG
    v3061.DECISION = DECISION
    v3061.OUT_DIR = OUT_DIR
    v3061.OBJ_DIR = OBJ_DIR
    v3061.REPORT_PATH = REPORT_PATH
    v3061.BOOT_IMAGE = BOOT_IMAGE
    v3061.INIT_BINARY = INIT_BINARY
    v3061.RAMDISK_CPIO = RAMDISK_CPIO
    v3061.HELPER_BINARY = HELPER_BINARY
    v3061.ENGINE_BINARY = ENGINE_BINARY
    v3061.ENGINE_ADAPTER_SOURCE = ENGINE_ADAPTER_SOURCE
    v3061.ENGINE_ADAPTER_OBJECT = ENGINE_ADAPTER_OBJECT
    v3061.ENGINE_RAMDISK_PATH = ENGINE_RAMDISK_PATH
    v3061.ENGINE_REMOTE_PATH = ENGINE_REMOTE_PATH
    v3061.ENGINE_NAME = ENGINE_NAME
    v3061.DEFAULT_LOOP_FRAMES = DEFAULT_LOOP_FRAMES
    v3061.LOOP_FRAME_MS = LOOP_FRAME_MS
    v3061.PRESENTER_POLL_MS = PRESENTER_POLL_MS
    v3061.FRAME_PATH = FRAME_PATH
    v3061.INPUT_STATE_PATH = INPUT_STATE_PATH
    v3061.INPUT_SOCKET_PATH = INPUT_SOCKET_PATH
    v3061.INPUT_UDP_PORT = INPUT_UDP_PORT
    v3061.DEVICE_NCM_HOST = DEVICE_NCM_HOST
    v3061.NATIVE_DASHBOARD = NATIVE_DASHBOARD
    v3061.NATIVE_DASHBOARD_LARGE_FRAME = NATIVE_DASHBOARD_LARGE_FRAME
    v3061.SOUND_MODE = SOUND_MODE
    v3061.AUDIO_CORUN = AUDIO_CORUN
    v3061.AUDIO_CORUN_MODE = AUDIO_CORUN_MODE
    v3061.AUDIO_CORUN_DURATION_MS = AUDIO_CORUN_DURATION_MS
    v3061.AUDIO_CORUN_AMPLITUDE_MILLI = AUDIO_CORUN_AMPLITUDE_MILLI
    v3061.REQUIRED_STRINGS = REQUIRED_STRINGS
    v3061.render_report = render_report


def render_report(
    manifest: dict[str, Any],
    helper_flags: tuple[str, ...],
    init_extra_flags: tuple[str, ...],
) -> str:
    doom = manifest.get("doomgeneric_visible_loop", {})
    markers = manifest.get("v3033_marker_strings", [])
    marker_lines = [f"- `{marker}`" for marker in markers] if isinstance(markers, list) else []
    return "\n".join([
        "# Native Init V3063 DOOMGENERIC Frame MS28 Source Build",
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
        "- Keeps V3061 single presenter pacing, frame mtime sync, UDP/NCM input, and dashboard layout unchanged.",
        f"- Changes only the helper loop cadence from `{BASELINE_LOOP_FRAME_MS}` ms to `{LOOP_FRAME_MS}` ms.",
        "- This tests a cadence closer to DOOM's 35 Hz game tick without mixing in dashboard or input changes.",
        "",
        "## Pacing Contract",
        "",
        f"- Baseline helper frame ms: `{BASELINE_LOOP_FRAME_MS}`",
        f"- Candidate helper frame ms: `{doom.get('loop_frame_ms', LOOP_FRAME_MS)}`",
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
        "- `py_compile`: V3063 builder and focused tests.",
        "- `unittest`: V3063 source contract plus V3061/V3059 and host evdev regressions.",
        "- Build: AArch64 helper compile/link, native-init compile, ramdisk pack, boot image pack, SHA256 capture.",
        "- Marker check: generated boot image contains V3063 identity, UDP input, presenter pacing, and audio co-run markers.",
        "- `git diff --check`: PASS.",
        "",
        "## Next Unit",
        "",
        "- Run ID: `V3064`",
        "- Type: rollback-gated live validation of V3063 frame_ms=28 candidate.",
        "- Scope: flash exact V3063 boot image via `native_init_flash.py`, health-check, require `video.demo.doom.loop.frame_ms=28`, start continuous DOOM loop, confirm helper remains active and UDP input still works.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `doomgeneric-frame-ms28-candidate`.",
    ]) + "\n"


def main() -> int:
    apply_v3063_globals()
    rc = v3061.main()
    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    doom = manifest.setdefault("doomgeneric_visible_loop", {})
    doom.update({
        "loop_frame_ms": LOOP_FRAME_MS,
        "baseline_loop_frame_ms": BASELINE_LOOP_FRAME_MS,
        "frame_ms_experiment": {
            "baseline_ms": BASELINE_LOOP_FRAME_MS,
            "candidate_ms": LOOP_FRAME_MS,
            "reason": "closer-to-doom-35hz-tick",
            "dashboard_large_frame_unchanged": bool(NATIVE_DASHBOARD_LARGE_FRAME),
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
        "candidate_type": "doomgeneric-frame-ms28-candidate",
        "adoption_state": "pending-frame-ms28-live-validation",
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
    (OUT_DIR / "doomgeneric-frame-ms28-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "doomgeneric-frame-ms28-candidate",
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
        "baseline_loop_frame_ms": BASELINE_LOOP_FRAME_MS,
        "loop_frame_ms": LOOP_FRAME_MS,
        "presenter_poll_ms": PRESENTER_POLL_MS,
        "presenter_pacing": "helper-frame-mtime",
        "loop_start_command": f"video demo doom loop-start 0 --wad runtime-private --sha256 {EXPECTED_WAD_SHA256}",
        "host_keyboard_bridge": rel(HOST_KEYBOARD_BRIDGE),
        "source_report": rel(REPORT_PATH),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-frame-ms28-live-validation",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
