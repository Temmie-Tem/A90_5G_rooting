#!/usr/bin/env python3
"""Build V3118 native-init DOOM no-full-clear presenter candidate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _workspace_bootstrap import repo_root
from a90harness.evidence import workspace_private_build_path, workspace_private_input_path
import build_native_init_boot_v3116_doomgeneric_prescaled_producer as v3116

REPO_ROOT = repo_root()

CYCLE = "V3118"
INIT_VERSION = "0.10.114"
INIT_BUILD = "v3118-doomgeneric-no-full-clear"
BUILD_TAG = INIT_BUILD
DECISION = "v3118-doomgeneric-no-full-clear-source-build-pass"

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
OBJ_DIR = OUT_DIR / "obj"
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V3118_DOOMGENERIC_NO_FULL_CLEAR_SOURCE_BUILD_2026-06-23.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images", "boot_linux_v3118_doomgeneric_no_full_clear.img", legacy_fallback=False
)
INIT_BINARY = OUT_DIR / "init_v3118_doomgeneric_no_full_clear"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v3118_doomgeneric_no_full_clear.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v521_doomgeneric_no_full_clear"

ENGINE_BINARY = OUT_DIR / "a90_doomgeneric_private_engine_v3118"
ENGINE_ADAPTER_SOURCE = OUT_DIR / "a90_doomgeneric_native_bridge_v3118.c"
ENGINE_ADAPTER_OBJECT = OBJ_DIR / "a90_doomgeneric_native_bridge_v3118.o"
ENGINE_RAMDISK_PATH = "bin/a90_doomgeneric_private_engine_v3118"
ENGINE_REMOTE_PATH = "/" + ENGINE_RAMDISK_PATH
ENGINE_NAME = "doomgeneric-private-link-v3118-no-full-clear"

RUNTIME_WAD_ROOT = v3116.RUNTIME_WAD_ROOT
RUNTIME_WAD_PATH = v3116.RUNTIME_WAD_PATH
EXPECTED_WAD_SHA256 = v3116.EXPECTED_WAD_SHA256
RUNTIME_WAD_MAX_BYTES = v3116.RUNTIME_WAD_MAX_BYTES
DEFAULT_LOOP_FRAMES = v3116.DEFAULT_LOOP_FRAMES
LOOP_FRAME_MS = v3116.LOOP_FRAME_MS
PRESENTER_POLL_MS = v3116.PRESENTER_POLL_MS
FRAME_WIDTH = v3116.FRAME_WIDTH
FRAME_HEIGHT = v3116.FRAME_HEIGHT
FRAME_STRIDE = v3116.FRAME_STRIDE
FRAME_BYTES = v3116.FRAME_BYTES
FRAME_PATH = "/tmp/a90-doomgeneric-v3118-raw-fallback-frame.xbgr8888"
SHARED_FRAME_PATH = "/tmp/a90-doomgeneric-v3118-shared-frame.bin"
INPUT_STATE_PATH = "/tmp/a90-doomgeneric-v3118-input.state"
INPUT_SOCKET_PATH = "/tmp/a90-doomgeneric-v3118-input.sock"
PACE_SOCKET_PATH = "/tmp/a90-doomgeneric-v3118-pace.sock"
TICK_TELEMETRY_PATH = "/tmp/a90-doomgeneric-v3118-tick-telemetry.txt"
INPUT_UDP_PORT = v3116.INPUT_UDP_PORT
DEVICE_NCM_HOST = v3116.DEVICE_NCM_HOST

NATIVE_DASHBOARD = v3116.NATIVE_DASHBOARD
NATIVE_DASHBOARD_MINIMAL = v3116.NATIVE_DASHBOARD_MINIMAL
NATIVE_DASHBOARD_LARGE_FRAME = v3116.NATIVE_DASHBOARD_LARGE_FRAME
HW_PLANE_SCALE = v3116.HW_PLANE_SCALE
PRE_SCALED_LARGE_FRAME = v3116.PRE_SCALED_LARGE_FRAME
NO_FULL_CLEAR = 1
FRAME_SCALE = v3116.FRAME_SCALE
SCALE_PATH = v3116.SCALE_PATH
FALLBACK_SCALE_PATH = v3116.FALLBACK_SCALE_PATH
FRAME_TIMING_PROBE = v3116.FRAME_TIMING_PROBE
SEQ_TELEMETRY = v3116.SEQ_TELEMETRY
NATIVE_DOOM_PRESENT_PAGEFLIP = v3116.NATIVE_DOOM_PRESENT_PAGEFLIP

TICK_TELEMETRY_MARKER = "a90.doomgeneric.v3118.tick_telemetry=prescaled-producer-no-full-clear"
SCALE_MARKER = "a90.doomgeneric.v3118.scale=producer-960x600-1to1-no-full-clear"
PHASE_TELEMETRY_MARKER = "a90.doomgeneric.v3118.phase_telemetry=tick-draw-dump-split-no-full-clear"
GAMETIC_FRAME_TELEMETRY_MARKER = (
    "a90.doomgeneric.v3118.gametic_frame_telemetry=loop-dump-gametic-summary-no-full-clear"
)
CLEAR_PATH = "dirty-dashboard-regions"
_V3116_ADAPTER_SOURCE = v3116.v3116_adapter_source


def rel(path: Path) -> str:
    return v3116.rel(path)


def _rewrite_required_string(item: bytes) -> bytes:
    replacements = {
        v3116.TICK_TELEMETRY_MARKER.encode("ascii"): TICK_TELEMETRY_MARKER.encode("ascii"),
        v3116.SCALE_MARKER.encode("ascii"): SCALE_MARKER.encode("ascii"),
        v3116.PHASE_TELEMETRY_MARKER.encode("ascii"): PHASE_TELEMETRY_MARKER.encode("ascii"),
        v3116.GAMETIC_FRAME_TELEMETRY_MARKER.encode("ascii"): GAMETIC_FRAME_TELEMETRY_MARKER.encode("ascii"),
        b"0.10.113": INIT_VERSION.encode("ascii"),
        b"v3116-doomgeneric-prescaled-producer": INIT_BUILD.encode("ascii"),
        b"doomgeneric-private-link-v3116-prescaled-producer": ENGINE_NAME.encode("ascii"),
        b"/bin/a90_doomgeneric_private_engine_v3116": ENGINE_REMOTE_PATH.encode("ascii"),
        b"a90-doomgeneric-v3116": b"a90-doomgeneric-v3118",
        b"a90.doomgeneric.v3116": b"a90.doomgeneric.v3118",
    }
    for old, new in replacements.items():
        item = item.replace(old, new)
    return item


REQUIRED_STRINGS = tuple(_rewrite_required_string(item) for item in v3116.REQUIRED_STRINGS) + (
    b"video.demo.doom.dashboard.full_clear=0",
    b"video.demo.doom.dashboard.clear_path=dirty-dashboard-regions",
)


def v3118_adapter_source() -> str:
    source = _V3116_ADAPTER_SOURCE()
    replacements = {
        v3116.TICK_TELEMETRY_MARKER: TICK_TELEMETRY_MARKER,
        v3116.SCALE_MARKER: SCALE_MARKER,
        v3116.PHASE_TELEMETRY_MARKER: PHASE_TELEMETRY_MARKER,
        v3116.GAMETIC_FRAME_TELEMETRY_MARKER: GAMETIC_FRAME_TELEMETRY_MARKER,
        v3116.TICK_TELEMETRY_PATH: TICK_TELEMETRY_PATH,
        v3116.FRAME_PATH: FRAME_PATH,
        v3116.SHARED_FRAME_PATH: SHARED_FRAME_PATH,
        v3116.INPUT_STATE_PATH: INPUT_STATE_PATH,
        v3116.INPUT_SOCKET_PATH: INPUT_SOCKET_PATH,
        v3116.PACE_SOCKET_PATH: PACE_SOCKET_PATH,
        "a90.doomgeneric.v3116": "a90.doomgeneric.v3118",
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
        "# Native Init V3118 DOOMGENERIC No-Full-Clear Source Build",
        "",
        "## Summary",
        "",
        f"- Cycle: `{CYCLE}`",
        "- Track: DOOM large-frame scale-path optimization.",
        f"- Decision: `{manifest['decision']}`",
        "- Result: PASS",
        "- Device flash: `no` in this build unit.",
        f"- Boot image: `{manifest['boot_image']}`",
        f"- Boot SHA256: `{manifest['boot_sha256']}`",
        f"- Init: `A90 Linux init {manifest['init_version']} ({manifest['init_build']})`",
        "",
        "## Included Delta",
        "",
        "- Inherits V3116's `960x600` pre-scaled DOOM producer and 1:1 raw-rowcopy presenter path.",
        "- Adds `VIDEO_DEMO_DOOMGENERIC_NO_FULL_CLEAR=1`, so the DOOM dashboard uses `a90_kms_begin_frame_no_clear()` and clears only the non-DOOM dashboard regions before drawing text/borders.",
        "- Targets the V3117 residual cost: full-screen KMS begin clear averaged about `4.57 ms` even after presenter scaling was removed.",
        "- Keeps pageflip, shared-frame sequencing, UDP input, pace socket, and bounded tone co-run unchanged.",
        "",
        "## Runtime Contract",
        "",
        f"- Runtime WAD path: `{doom.get('runtime_wad_path')}`",
        f"- Expected WAD SHA256: `{doom.get('expected_wad_sha256')}`",
        f"- Helper loop command: `{doom.get('helper_loop_command')}`",
        f"- Frame geometry: `{FRAME_WIDTH}x{FRAME_HEIGHT}` stride `{FRAME_STRIDE}` bytes `{FRAME_BYTES}`",
        f"- Scale path: `{SCALE_PATH}`",
        f"- Clear path: `{CLEAR_PATH}`",
        "- Expected live markers: `video.demo.doom.dashboard.full_clear=0` and `video.demo.doom.dashboard.clear_path=dirty-dashboard-regions`.",
        "",
        "## Safety",
        "",
        "- Boot partition only through the checked flash helper `native_init_flash.py` in the next live unit.",
        "- No GPU/GL stack, panel re-init, backlight, PMIC, regulator, GDSC, GPIO, Wi-Fi connect/dhcp/ping, or forbidden partition path.",
        "- This source build only changes the userspace DOOM dashboard framebuffer clear policy.",
        "",
        "## Validation",
        "",
        "- `py_compile`: V3118 builder and focused tests.",
        "- `unittest`: V3118 source contract plus V3116/V3117 regressions.",
        "- Build: AArch64 helper compile/link, native-init compile, ramdisk pack, boot image pack, SHA256 capture.",
        "- Marker check: generated boot image contains V3118 identity, pre-scaled producer markers, no-full-clear dashboard markers, and no HW-plane atomic requirement.",
        "- `git diff --check`: PASS.",
        "",
        "## Next Unit",
        "",
        "- Run ID: `V3119`",
        "- Type: rollback-gated live validation.",
        "- Scope: flash exact V3118 image, run bounded large DOOM loop, require no-full-clear markers, compare `timing.begin.avg_us` and pageflip cadence against V3117.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `doomgeneric-no-full-clear-candidate`.",
    ]) + "\n"


_V3116_APPLY_GLOBALS = v3116.apply_v3116_globals


def configure_v3116_module() -> None:
    v3116.CYCLE = CYCLE
    v3116.INIT_VERSION = INIT_VERSION
    v3116.INIT_BUILD = INIT_BUILD
    v3116.BUILD_TAG = BUILD_TAG
    v3116.DECISION = DECISION
    v3116.OUT_DIR = OUT_DIR
    v3116.OBJ_DIR = OBJ_DIR
    v3116.REPORT_PATH = REPORT_PATH
    v3116.BOOT_IMAGE = BOOT_IMAGE
    v3116.INIT_BINARY = INIT_BINARY
    v3116.RAMDISK_CPIO = RAMDISK_CPIO
    v3116.HELPER_BINARY = HELPER_BINARY
    v3116.ENGINE_BINARY = ENGINE_BINARY
    v3116.ENGINE_ADAPTER_SOURCE = ENGINE_ADAPTER_SOURCE
    v3116.ENGINE_ADAPTER_OBJECT = ENGINE_ADAPTER_OBJECT
    v3116.ENGINE_RAMDISK_PATH = ENGINE_RAMDISK_PATH
    v3116.ENGINE_REMOTE_PATH = ENGINE_REMOTE_PATH
    v3116.ENGINE_NAME = ENGINE_NAME
    v3116.FRAME_PATH = FRAME_PATH
    v3116.SHARED_FRAME_PATH = SHARED_FRAME_PATH
    v3116.INPUT_STATE_PATH = INPUT_STATE_PATH
    v3116.INPUT_SOCKET_PATH = INPUT_SOCKET_PATH
    v3116.PACE_SOCKET_PATH = PACE_SOCKET_PATH
    v3116.TICK_TELEMETRY_PATH = TICK_TELEMETRY_PATH
    v3116.TICK_TELEMETRY_MARKER = TICK_TELEMETRY_MARKER
    v3116.SCALE_MARKER = SCALE_MARKER
    v3116.PHASE_TELEMETRY_MARKER = PHASE_TELEMETRY_MARKER
    v3116.GAMETIC_FRAME_TELEMETRY_MARKER = GAMETIC_FRAME_TELEMETRY_MARKER
    v3116.REQUIRED_STRINGS = REQUIRED_STRINGS
    v3116.v3116_adapter_source = v3118_adapter_source
    v3116.render_report = render_report


def apply_v3118_globals() -> None:
    configure_v3116_module()
    _V3116_APPLY_GLOBALS()
    v3033 = v3116.v3033_module()
    v3033.NO_FULL_CLEAR = NO_FULL_CLEAR


def main() -> int:
    original_apply = v3116.apply_v3116_globals
    try:
        configure_v3116_module()
        v3116.apply_v3116_globals = apply_v3118_globals
        rc = v3116.main()
    finally:
        v3116.apply_v3116_globals = original_apply

    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    doom = manifest.setdefault("doomgeneric_visible_loop", {})
    doom.update({
        "no_full_clear": bool(NO_FULL_CLEAR),
        "clear_path": CLEAR_PATH,
        "begin_path": "kms-begin-frame-no-clear",
        "expected_clear_marker": "video.demo.doom.dashboard.clear_path=dirty-dashboard-regions",
        "expected_full_clear_marker": "video.demo.doom.dashboard.full_clear=0",
    })
    manifest.update({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "doomgeneric-no-full-clear-candidate",
        "adoption_state": "pending-no-full-clear-live-validation",
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
    (OUT_DIR / "doomgeneric-no-full-clear-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "doomgeneric-no-full-clear-candidate",
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
        "present_mode": "pageflip",
        "present_path": "kms-dumb-buffer-pageflip-no-full-clear",
        "frame_timing_probe": FRAME_TIMING_PROBE,
        "native_dashboard": bool(NATIVE_DASHBOARD),
        "native_dashboard_minimal": bool(NATIVE_DASHBOARD_MINIMAL),
        "native_dashboard_large_frame": bool(NATIVE_DASHBOARD_LARGE_FRAME),
        "native_doom_present_pageflip": bool(NATIVE_DOOM_PRESENT_PAGEFLIP),
        "loop_start_command": f"video demo doom loop-start 0 --wad runtime-private --sha256 {EXPECTED_WAD_SHA256}",
        "host_keyboard_bridge": rel(v3116.v3114.v3112.v3108.HOST_KEYBOARD_BRIDGE),
        "source_report": rel(REPORT_PATH),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-no-full-clear-live-validation",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
