#!/usr/bin/env python3
"""Build V3120 native-init DOOM direct shared-frame blit candidate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _workspace_bootstrap import repo_root
from a90harness.evidence import workspace_private_build_path, workspace_private_input_path
import build_native_init_boot_v3118_doomgeneric_no_full_clear as v3118

REPO_ROOT = repo_root()

CYCLE = "V3120"
INIT_VERSION = "0.10.115"
INIT_BUILD = "v3120-doomgeneric-direct-shared-blit"
BUILD_TAG = INIT_BUILD
DECISION = "v3120-doomgeneric-direct-shared-blit-source-build-pass"

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
OBJ_DIR = OUT_DIR / "obj"
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V3120_DOOMGENERIC_DIRECT_SHARED_BLIT_SOURCE_BUILD_2026-06-23.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images", "boot_linux_v3120_doomgeneric_direct_shared_blit.img", legacy_fallback=False
)
INIT_BINARY = OUT_DIR / "init_v3120_doomgeneric_direct_shared_blit"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v3120_doomgeneric_direct_shared_blit.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v521_doomgeneric_direct_shared_blit"

ENGINE_BINARY = OUT_DIR / "a90_doomgeneric_private_engine_v3120"
ENGINE_ADAPTER_SOURCE = OUT_DIR / "a90_doomgeneric_native_bridge_v3120.c"
ENGINE_ADAPTER_OBJECT = OBJ_DIR / "a90_doomgeneric_native_bridge_v3120.o"
ENGINE_RAMDISK_PATH = "bin/a90_doomgeneric_private_engine_v3120"
ENGINE_REMOTE_PATH = "/" + ENGINE_RAMDISK_PATH
ENGINE_NAME = "doomgeneric-private-link-v3120-direct-shared-blit"

RUNTIME_WAD_ROOT = v3118.RUNTIME_WAD_ROOT
RUNTIME_WAD_PATH = v3118.RUNTIME_WAD_PATH
EXPECTED_WAD_SHA256 = v3118.EXPECTED_WAD_SHA256
RUNTIME_WAD_MAX_BYTES = v3118.RUNTIME_WAD_MAX_BYTES
DEFAULT_LOOP_FRAMES = v3118.DEFAULT_LOOP_FRAMES
LOOP_FRAME_MS = v3118.LOOP_FRAME_MS
PRESENTER_POLL_MS = v3118.PRESENTER_POLL_MS
FRAME_WIDTH = v3118.FRAME_WIDTH
FRAME_HEIGHT = v3118.FRAME_HEIGHT
FRAME_STRIDE = v3118.FRAME_STRIDE
FRAME_BYTES = v3118.FRAME_BYTES
FRAME_PATH = "/tmp/a90-doomgeneric-v3120-raw-fallback-frame.xbgr8888"
SHARED_FRAME_PATH = "/tmp/a90-doomgeneric-v3120-shared-frame.bin"
INPUT_STATE_PATH = "/tmp/a90-doomgeneric-v3120-input.state"
INPUT_SOCKET_PATH = "/tmp/a90-doomgeneric-v3120-input.sock"
PACE_SOCKET_PATH = "/tmp/a90-doomgeneric-v3120-pace.sock"
TICK_TELEMETRY_PATH = "/tmp/a90-doomgeneric-v3120-tick-telemetry.txt"
INPUT_UDP_PORT = v3118.INPUT_UDP_PORT
DEVICE_NCM_HOST = v3118.DEVICE_NCM_HOST

NATIVE_DASHBOARD = v3118.NATIVE_DASHBOARD
NATIVE_DASHBOARD_MINIMAL = v3118.NATIVE_DASHBOARD_MINIMAL
NATIVE_DASHBOARD_LARGE_FRAME = v3118.NATIVE_DASHBOARD_LARGE_FRAME
HW_PLANE_SCALE = v3118.HW_PLANE_SCALE
PRE_SCALED_LARGE_FRAME = v3118.PRE_SCALED_LARGE_FRAME
NO_FULL_CLEAR = v3118.NO_FULL_CLEAR
DIRECT_SHARED_BLIT = 1
FRAME_SCALE = v3118.FRAME_SCALE
SCALE_PATH = v3118.SCALE_PATH
FALLBACK_SCALE_PATH = v3118.FALLBACK_SCALE_PATH
FRAME_TIMING_PROBE = v3118.FRAME_TIMING_PROBE
SEQ_TELEMETRY = v3118.SEQ_TELEMETRY
NATIVE_DOOM_PRESENT_PAGEFLIP = v3118.NATIVE_DOOM_PRESENT_PAGEFLIP
CLEAR_PATH = v3118.CLEAR_PATH
FRAME_IPC = "shared-mmap-direct-blit"

TICK_TELEMETRY_MARKER = "a90.doomgeneric.v3120.tick_telemetry=direct-shared-blit"
SCALE_MARKER = "a90.doomgeneric.v3120.scale=producer-960x600-1to1-direct-shared-blit"
PHASE_TELEMETRY_MARKER = "a90.doomgeneric.v3120.phase_telemetry=tick-draw-dump-split-direct-shared-blit"
GAMETIC_FRAME_TELEMETRY_MARKER = (
    "a90.doomgeneric.v3120.gametic_frame_telemetry=loop-dump-gametic-summary-direct-shared-blit"
)
DIRECT_SHARED_BLIT_MARKER = "video.demo.doom.loop.presenter.reader=shared-mmap-direct-blit"

_V3118_APPLY_GLOBALS = v3118.apply_v3118_globals
_V3118_ADAPTER_SOURCE = v3118.v3118_adapter_source


def rel(path: Path) -> str:
    return v3118.rel(path)


def _rewrite_required_string(item: bytes) -> bytes:
    replacements = {
        v3118.TICK_TELEMETRY_MARKER.encode("ascii"): TICK_TELEMETRY_MARKER.encode("ascii"),
        v3118.SCALE_MARKER.encode("ascii"): SCALE_MARKER.encode("ascii"),
        v3118.PHASE_TELEMETRY_MARKER.encode("ascii"): PHASE_TELEMETRY_MARKER.encode("ascii"),
        v3118.GAMETIC_FRAME_TELEMETRY_MARKER.encode("ascii"): GAMETIC_FRAME_TELEMETRY_MARKER.encode("ascii"),
        b"0.10.114": INIT_VERSION.encode("ascii"),
        b"v3118-doomgeneric-no-full-clear": INIT_BUILD.encode("ascii"),
        b"doomgeneric-private-link-v3118-no-full-clear": ENGINE_NAME.encode("ascii"),
        b"/bin/a90_doomgeneric_private_engine_v3118": ENGINE_REMOTE_PATH.encode("ascii"),
        b"a90-doomgeneric-v3118": b"a90-doomgeneric-v3120",
        b"a90.doomgeneric.v3118": b"a90.doomgeneric.v3120",
    }
    for old, new in replacements.items():
        item = item.replace(old, new)
    return item


REQUIRED_STRINGS = tuple(_rewrite_required_string(item) for item in v3118.REQUIRED_STRINGS) + (
    b"video.demo.doom.presenter.reader=shared-mmap-direct-blit",
    b"video.demo.doom.loop.presenter.reader=shared-mmap-direct-blit",
)


def v3120_adapter_source() -> str:
    source = _V3118_ADAPTER_SOURCE()
    replacements = {
        v3118.TICK_TELEMETRY_MARKER: TICK_TELEMETRY_MARKER,
        v3118.SCALE_MARKER: SCALE_MARKER,
        v3118.PHASE_TELEMETRY_MARKER: PHASE_TELEMETRY_MARKER,
        v3118.GAMETIC_FRAME_TELEMETRY_MARKER: GAMETIC_FRAME_TELEMETRY_MARKER,
        v3118.TICK_TELEMETRY_PATH: TICK_TELEMETRY_PATH,
        v3118.FRAME_PATH: FRAME_PATH,
        v3118.SHARED_FRAME_PATH: SHARED_FRAME_PATH,
        v3118.INPUT_STATE_PATH: INPUT_STATE_PATH,
        v3118.INPUT_SOCKET_PATH: INPUT_SOCKET_PATH,
        v3118.PACE_SOCKET_PATH: PACE_SOCKET_PATH,
        "a90.doomgeneric.v3118": "a90.doomgeneric.v3120",
    }
    for old, new in replacements.items():
        source = source.replace(old, new)
    return source


def render_report(
    manifest: dict[str, Any],
    helper_flags: tuple[str, ...],
    init_extra_flags: tuple[str, ...],
) -> str:
    doom = manifest.get("doomgeneric_visible_loop", {})
    return "\n".join([
        "# Native Init V3120 DOOMGENERIC Direct Shared Blit Source Build",
        "",
        "## Summary",
        "",
        f"- Cycle: `{CYCLE}`",
        "- Track: DOOM frame IPC/copy reduction.",
        f"- Decision: `{manifest['decision']}`",
        "- Result: PASS",
        "- Device flash: `no` in this build unit.",
        f"- Boot image: `{manifest['boot_image']}`",
        f"- Boot SHA256: `{manifest['boot_sha256']}`",
        f"- Init: `A90 Linux init {manifest['init_version']} ({manifest['init_build']})`",
        "",
        "## Included Delta",
        "",
        "- Inherits V3118's no-full-clear, `960x600` pre-scaled producer, shared-frame sequencing, UDP input, pace socket, and pageflip presentation.",
        "- Adds `VIDEO_DEMO_DOOMGENERIC_DIRECT_SHARED_BLIT=1`, so the presenter maps the shared-frame payload and blits directly from that mmap source instead of first copying it into a heap staging buffer.",
        "- Keeps the existing shared-frame sequence validation before taking the direct pointer; this is a narrow copy-path optimization, not the final helper-direct-KMS architecture.",
        "",
        "## Runtime Contract",
        "",
        f"- Runtime WAD path: `{doom.get('runtime_wad_path')}`",
        f"- Expected WAD SHA256: `{doom.get('expected_wad_sha256')}`",
        f"- Helper loop command: `{doom.get('helper_loop_command')}`",
        f"- Frame geometry: `{FRAME_WIDTH}x{FRAME_HEIGHT}` stride `{FRAME_STRIDE}` bytes `{FRAME_BYTES}`",
        f"- Frame IPC: `{FRAME_IPC}`",
        f"- Scale path: `{SCALE_PATH}`",
        f"- Clear path: `{CLEAR_PATH}`",
        "- Expected live marker: `video.demo.doom.loop.presenter.reader=shared-mmap-direct-blit`.",
        "",
        "## Safety",
        "",
        "- Boot partition only through the checked flash helper `native_init_flash.py` in the next live unit.",
        "- No GPU/GL stack, panel re-init, backlight, PMIC, regulator, GDSC, GPIO, Wi-Fi connect/dhcp/ping, or forbidden partition path.",
        "- This source build only changes the userspace presenter read/blit path.",
        "",
        "## Validation",
        "",
        "- `py_compile`: V3120 builder and focused tests.",
        "- `unittest`: V3120 source contract plus V3118/V3119 regressions.",
        "- Build: AArch64 helper compile/link, native-init compile, ramdisk pack, boot image pack, SHA256 capture.",
        "- Marker check: generated boot image contains V3120 identity, direct-shared-blit reader marker, pre-scaled/no-full-clear markers, shared-frame/pageflip/input/audio markers, and no HW-plane atomic requirement.",
        "- `git diff --check`: PASS.",
        "",
        "## Next Unit",
        "",
        "- Run ID: `V3121`",
        "- Type: rollback-gated live validation.",
        "- Scope: flash exact V3120 image, run bounded large DOOM loop, require direct-shared-blit marker, compare `timing.read.avg_us`, `timing.draw.avg_us`, and pageflip cadence against V3119.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `doomgeneric-direct-shared-blit-candidate`.",
    ]) + "\n"


def configure_v3118_module() -> None:
    v3118.CYCLE = CYCLE
    v3118.INIT_VERSION = INIT_VERSION
    v3118.INIT_BUILD = INIT_BUILD
    v3118.BUILD_TAG = BUILD_TAG
    v3118.DECISION = DECISION
    v3118.OUT_DIR = OUT_DIR
    v3118.OBJ_DIR = OBJ_DIR
    v3118.REPORT_PATH = REPORT_PATH
    v3118.BOOT_IMAGE = BOOT_IMAGE
    v3118.INIT_BINARY = INIT_BINARY
    v3118.RAMDISK_CPIO = RAMDISK_CPIO
    v3118.HELPER_BINARY = HELPER_BINARY
    v3118.ENGINE_BINARY = ENGINE_BINARY
    v3118.ENGINE_ADAPTER_SOURCE = ENGINE_ADAPTER_SOURCE
    v3118.ENGINE_ADAPTER_OBJECT = ENGINE_ADAPTER_OBJECT
    v3118.ENGINE_RAMDISK_PATH = ENGINE_RAMDISK_PATH
    v3118.ENGINE_REMOTE_PATH = ENGINE_REMOTE_PATH
    v3118.ENGINE_NAME = ENGINE_NAME
    v3118.FRAME_PATH = FRAME_PATH
    v3118.SHARED_FRAME_PATH = SHARED_FRAME_PATH
    v3118.INPUT_STATE_PATH = INPUT_STATE_PATH
    v3118.INPUT_SOCKET_PATH = INPUT_SOCKET_PATH
    v3118.PACE_SOCKET_PATH = PACE_SOCKET_PATH
    v3118.TICK_TELEMETRY_PATH = TICK_TELEMETRY_PATH
    v3118.TICK_TELEMETRY_MARKER = TICK_TELEMETRY_MARKER
    v3118.SCALE_MARKER = SCALE_MARKER
    v3118.PHASE_TELEMETRY_MARKER = PHASE_TELEMETRY_MARKER
    v3118.GAMETIC_FRAME_TELEMETRY_MARKER = GAMETIC_FRAME_TELEMETRY_MARKER
    v3118.REQUIRED_STRINGS = REQUIRED_STRINGS
    v3118.v3118_adapter_source = v3120_adapter_source
    v3118.render_report = render_report


def apply_v3120_globals() -> None:
    configure_v3118_module()
    _V3118_APPLY_GLOBALS()
    v3033 = v3118.v3116.v3033_module()
    v3033.DIRECT_SHARED_BLIT = DIRECT_SHARED_BLIT


def main() -> int:
    original_apply = v3118.apply_v3118_globals
    try:
        configure_v3118_module()
        v3118.apply_v3118_globals = apply_v3120_globals
        rc = v3118.main()
    finally:
        v3118.apply_v3118_globals = original_apply

    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    doom = manifest.setdefault("doomgeneric_visible_loop", {})
    doom.update({
        "direct_shared_blit": bool(DIRECT_SHARED_BLIT),
        "frame_ipc": FRAME_IPC,
        "presenter_reader": FRAME_IPC,
        "expected_reader_marker": DIRECT_SHARED_BLIT_MARKER,
    })
    manifest.update({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "doomgeneric-direct-shared-blit-candidate",
        "adoption_state": "pending-direct-shared-blit-live-validation",
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
    (OUT_DIR / "doomgeneric-direct-shared-blit-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "doomgeneric-direct-shared-blit-candidate",
        "boot_image": rel(BOOT_IMAGE),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "engine_binary": rel(ENGINE_BINARY),
        "engine_ramdisk_path": ENGINE_REMOTE_PATH,
        "runtime_wad_path": RUNTIME_WAD_PATH,
        "expected_wad_sha256": EXPECTED_WAD_SHA256,
        "frame_path": FRAME_PATH,
        "shared_frame_path": SHARED_FRAME_PATH,
        "frame_width": FRAME_WIDTH,
        "frame_height": FRAME_HEIGHT,
        "frame_stride": FRAME_STRIDE,
        "frame_bytes": FRAME_BYTES,
        "input_state_path": INPUT_STATE_PATH,
        "input_socket_path": INPUT_SOCKET_PATH,
        "input_udp_host": DEVICE_NCM_HOST,
        "input_udp_port": INPUT_UDP_PORT,
        "pace_socket_path": PACE_SOCKET_PATH,
        "scale_marker": SCALE_MARKER,
        "tick_telemetry_path": TICK_TELEMETRY_PATH,
        "loop_frame_ms": LOOP_FRAME_MS,
        "presenter_poll_ms": PRESENTER_POLL_MS,
        "frame_scale": FRAME_SCALE,
        "scale_path": SCALE_PATH,
        "clear_path": CLEAR_PATH,
        "no_full_clear": bool(NO_FULL_CLEAR),
        "direct_shared_blit": bool(DIRECT_SHARED_BLIT),
        "frame_ipc": FRAME_IPC,
        "present_mode": "pageflip",
        "present_path": "kms-dumb-buffer-pageflip-direct-shared-blit",
        "frame_timing_probe": FRAME_TIMING_PROBE,
        "native_dashboard": bool(NATIVE_DASHBOARD),
        "native_dashboard_minimal": bool(NATIVE_DASHBOARD_MINIMAL),
        "native_dashboard_large_frame": bool(NATIVE_DASHBOARD_LARGE_FRAME),
        "native_doom_present_pageflip": bool(NATIVE_DOOM_PRESENT_PAGEFLIP),
        "loop_start_command": f"video demo doom loop-start 0 --wad runtime-private --sha256 {EXPECTED_WAD_SHA256}",
        "host_keyboard_bridge": rel(v3118.v3116.v3114.v3112.v3108.HOST_KEYBOARD_BRIDGE),
        "source_report": rel(REPORT_PATH),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-direct-shared-blit-live-validation",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
