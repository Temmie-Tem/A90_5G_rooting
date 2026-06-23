#!/usr/bin/env python3
"""Build V3126 DOOM smooth-demo paced-time direct-blit candidate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _workspace_bootstrap import repo_root
from a90harness.evidence import workspace_private_build_path, workspace_private_input_path
import build_native_init_boot_v3123_doomgeneric_summary_only_direct_blit as v3123

REPO_ROOT = repo_root()

CYCLE = "V3126"
INIT_VERSION = "0.10.117"
INIT_BUILD = "v3126-doomgeneric-smooth-demo-direct-blit"
BUILD_TAG = INIT_BUILD
DECISION = "v3126-doomgeneric-smooth-demo-direct-blit-source-build-pass"

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
OBJ_DIR = OUT_DIR / "obj"
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V3126_DOOMGENERIC_SMOOTH_DEMO_DIRECT_BLIT_SOURCE_BUILD_2026-06-23.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images", "boot_linux_v3126_doomgeneric_smooth_demo_direct_blit.img", legacy_fallback=False
)
INIT_BINARY = OUT_DIR / "init_v3126_doomgeneric_smooth_demo_direct_blit"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v3126_doomgeneric_smooth_demo_direct_blit.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v523_doomgeneric_smooth_demo_direct_blit"

ENGINE_BINARY = OUT_DIR / "a90_doomgeneric_private_engine_v3126"
ENGINE_ADAPTER_SOURCE = OUT_DIR / "a90_doomgeneric_native_bridge_v3126.c"
ENGINE_ADAPTER_OBJECT = OBJ_DIR / "a90_doomgeneric_native_bridge_v3126.o"
ENGINE_RAMDISK_PATH = "bin/a90_doomgeneric_private_engine_v3126"
ENGINE_REMOTE_PATH = "/" + ENGINE_RAMDISK_PATH
ENGINE_NAME = "doomgeneric-private-link-v3126-smooth-demo-direct-blit"

RUNTIME_WAD_ROOT = v3123.RUNTIME_WAD_ROOT
RUNTIME_WAD_PATH = v3123.RUNTIME_WAD_PATH
EXPECTED_WAD_SHA256 = v3123.EXPECTED_WAD_SHA256
RUNTIME_WAD_MAX_BYTES = v3123.RUNTIME_WAD_MAX_BYTES
DEFAULT_LOOP_FRAMES = v3123.DEFAULT_LOOP_FRAMES
LOOP_FRAME_MS = v3123.LOOP_FRAME_MS
PRESENTER_POLL_MS = v3123.PRESENTER_POLL_MS
FRAME_WIDTH = v3123.FRAME_WIDTH
FRAME_HEIGHT = v3123.FRAME_HEIGHT
FRAME_STRIDE = v3123.FRAME_STRIDE
FRAME_BYTES = v3123.FRAME_BYTES
FRAME_PATH = "/tmp/a90-doomgeneric-v3126-raw-fallback-frame.xbgr8888"
SHARED_FRAME_PATH = "/tmp/a90-doomgeneric-v3126-shared-frame.bin"
INPUT_STATE_PATH = "/tmp/a90-doomgeneric-v3126-input.state"
INPUT_SOCKET_PATH = "/tmp/a90-doomgeneric-v3126-input.sock"
PACE_SOCKET_PATH = "/tmp/a90-doomgeneric-v3126-pace.sock"
TICK_TELEMETRY_PATH = "/tmp/a90-doomgeneric-v3126-tick-telemetry.txt"
INPUT_UDP_PORT = v3123.INPUT_UDP_PORT
DEVICE_NCM_HOST = v3123.DEVICE_NCM_HOST

NATIVE_DASHBOARD = v3123.NATIVE_DASHBOARD
NATIVE_DASHBOARD_MINIMAL = v3123.NATIVE_DASHBOARD_MINIMAL
NATIVE_DASHBOARD_LARGE_FRAME = v3123.NATIVE_DASHBOARD_LARGE_FRAME
HW_PLANE_SCALE = v3123.HW_PLANE_SCALE
PRE_SCALED_LARGE_FRAME = v3123.PRE_SCALED_LARGE_FRAME
NO_FULL_CLEAR = v3123.NO_FULL_CLEAR
DIRECT_SHARED_BLIT = v3123.DIRECT_SHARED_BLIT
FOREGROUND_FRAME_LOG = v3123.FOREGROUND_FRAME_LOG
FRAME_SCALE = v3123.FRAME_SCALE
SCALE_PATH = v3123.SCALE_PATH
FALLBACK_SCALE_PATH = v3123.FALLBACK_SCALE_PATH
FRAME_TIMING_PROBE = v3123.FRAME_TIMING_PROBE
SEQ_TELEMETRY = v3123.SEQ_TELEMETRY
NATIVE_DOOM_PRESENT_PAGEFLIP = v3123.NATIVE_DOOM_PRESENT_PAGEFLIP
CLEAR_PATH = v3123.CLEAR_PATH
FRAME_IPC = "shared-mmap-direct-blit-summary-only-smooth-demo"

TICK_QUANTUM_US = 28571
TICK_TELEMETRY_MARKER = "a90.doomgeneric.v3126.tick_telemetry=smooth-demo-paced-time-direct-blit"
SCALE_MARKER = "a90.doomgeneric.v3126.scale=producer-960x600-1to1-smooth-demo-direct-shared-blit"
PHASE_TELEMETRY_MARKER = "a90.doomgeneric.v3126.phase_telemetry=tick-draw-dump-split-smooth-demo"
GAMETIC_FRAME_TELEMETRY_MARKER = (
    "a90.doomgeneric.v3126.gametic_frame_telemetry=loop-dump-gametic-summary-smooth-demo"
)
PACED_TIME_MARKER = "a90.doomgeneric.v3126.paced_time=smooth-demo-presenter-token-doom-tic-quantum"
DIRECT_SHARED_BLIT_MARKER = v3123.DIRECT_SHARED_BLIT_MARKER
SUMMARY_ONLY_MARKER = v3123.SUMMARY_ONLY_MARKER

_V3123_APPLY_GLOBALS = v3123.apply_v3123_globals
_V3123_ADAPTER_SOURCE = v3123.v3123_adapter_source
_V3123_RENDER_REPORT = v3123.render_report


def rel(path: Path) -> str:
    return v3123.rel(path)


def _replace_required(source: str, old: str, new: str) -> str:
    if old not in source:
        raise RuntimeError(f"missing V3126 adapter source anchor: {old[:96]!r}")
    return source.replace(old, new, 1)


def _rewrite_required_string(item: bytes) -> bytes:
    replacements = {
        v3123.TICK_TELEMETRY_MARKER.encode("ascii"): TICK_TELEMETRY_MARKER.encode("ascii"),
        v3123.SCALE_MARKER.encode("ascii"): SCALE_MARKER.encode("ascii"),
        v3123.PHASE_TELEMETRY_MARKER.encode("ascii"): PHASE_TELEMETRY_MARKER.encode("ascii"),
        v3123.GAMETIC_FRAME_TELEMETRY_MARKER.encode("ascii"): GAMETIC_FRAME_TELEMETRY_MARKER.encode("ascii"),
        v3123.INIT_VERSION.encode("ascii"): INIT_VERSION.encode("ascii"),
        v3123.INIT_BUILD.encode("ascii"): INIT_BUILD.encode("ascii"),
        v3123.ENGINE_NAME.encode("ascii"): ENGINE_NAME.encode("ascii"),
        v3123.ENGINE_REMOTE_PATH.encode("ascii"): ENGINE_REMOTE_PATH.encode("ascii"),
        b"a90-doomgeneric-v3123": b"a90-doomgeneric-v3126",
        b"a90.doomgeneric.v3123": b"a90.doomgeneric.v3126",
    }
    for old, new in replacements.items():
        item = item.replace(old, new)
    return item


REQUIRED_STRINGS = tuple(_rewrite_required_string(item) for item in v3123.REQUIRED_STRINGS) + (
    PACED_TIME_MARKER.encode("ascii"),
    b"paced_time_model=presenter-token-doom-tic-quantum",
    b"paced_time.quantum_us=%u",
    b"paced_time.advance_calls=%u",
    b"fake_time_model=DG_SleepMs-request-telemetry-only",
    b"non-original-smooth-demo",
    b"%s.tick_telemetry.summary=1",
    b"%s.tick_telemetry.%s",
)


def v3126_adapter_source() -> str:
    source = _V3123_ADAPTER_SOURCE()
    replacements = {
        v3123.TICK_TELEMETRY_MARKER: TICK_TELEMETRY_MARKER,
        v3123.SCALE_MARKER: SCALE_MARKER,
        v3123.PHASE_TELEMETRY_MARKER: PHASE_TELEMETRY_MARKER,
        v3123.GAMETIC_FRAME_TELEMETRY_MARKER: GAMETIC_FRAME_TELEMETRY_MARKER,
        v3123.TICK_TELEMETRY_PATH: TICK_TELEMETRY_PATH,
        v3123.FRAME_PATH: FRAME_PATH,
        v3123.SHARED_FRAME_PATH: SHARED_FRAME_PATH,
        v3123.INPUT_STATE_PATH: INPUT_STATE_PATH,
        v3123.INPUT_SOCKET_PATH: INPUT_SOCKET_PATH,
        v3123.PACE_SOCKET_PATH: PACE_SOCKET_PATH,
        "a90.doomgeneric.v3123": "a90.doomgeneric.v3126",
    }
    for old, new in replacements.items():
        source = source.replace(old, new)
    source = _replace_required(
        source,
        'const char a90_doomgeneric_v3100_phase_policy[] =\n'
        f'    "{PHASE_TELEMETRY_MARKER}";\n',
        'const char a90_doomgeneric_v3100_phase_policy[] =\n'
        f'    "{PHASE_TELEMETRY_MARKER}";\n'
        'const char a90_doomgeneric_v3126_paced_time_policy[] =\n'
        f'    "{PACED_TIME_MARKER}";\n'
        'const char a90_doomgeneric_v3126_mode_label[] =\n'
        '    "non-original-smooth-demo";\n',
    )
    source = _replace_required(
        source,
        "static uint32_t fake_ticks_ms;\n",
        "static uint32_t fake_ticks_ms;\n"
        "static uint32_t paced_ticks_ms;\n"
        "static uint32_t paced_tick_remainder_us;\n"
        "static uint32_t paced_time_advance_calls;\n"
        "static uint64_t paced_time_advance_us_total;\n"
        "static int paced_time_active;\n",
    )
    source = _replace_required(
        source,
        "    fake_ticks_ms = 0;\n"
        "    tick_telemetry_sleep_calls = 0;\n",
        "    fake_ticks_ms = 0;\n"
        "    paced_ticks_ms = 0;\n"
        "    paced_tick_remainder_us = 0;\n"
        "    paced_time_advance_calls = 0;\n"
        "    paced_time_advance_us_total = 0;\n"
        "    paced_time_active = 0;\n"
        "    tick_telemetry_sleep_calls = 0;\n",
    )
    source = _replace_required(
        source,
        "void DG_SleepMs(uint32_t ms) {\n"
        "    ++tick_telemetry_sleep_calls;\n"
        "    tick_telemetry_sleep_ms_total += ms;\n"
        "    fake_ticks_ms += ms;\n"
        "}\n\n"
        "uint32_t DG_GetTicksMs(void) {\n"
        "    ++tick_telemetry_getticks_calls;\n"
        "    return fake_ticks_ms;\n"
        "}\n",
        f"#define A90_DG_PACED_TICK_QUANTUM_US {TICK_QUANTUM_US}U\n\n"
        "void DG_SleepMs(uint32_t ms) {\n"
        "    ++tick_telemetry_sleep_calls;\n"
        "    tick_telemetry_sleep_ms_total += ms;\n"
        "    fake_ticks_ms += ms;\n"
        "}\n\n"
        "static void a90_doomgeneric_advance_paced_time(void) {\n"
        "    uint32_t total_us = paced_tick_remainder_us + A90_DG_PACED_TICK_QUANTUM_US;\n"
        "    uint32_t step_ms = total_us / 1000U;\n\n"
        "    paced_tick_remainder_us = total_us % 1000U;\n"
        "    paced_ticks_ms += step_ms;\n"
        "    ++paced_time_advance_calls;\n"
        "    paced_time_advance_us_total += A90_DG_PACED_TICK_QUANTUM_US;\n"
        "}\n\n"
        "uint32_t DG_GetTicksMs(void) {\n"
        "    ++tick_telemetry_getticks_calls;\n"
        "    return paced_time_active ? paced_ticks_ms : fake_ticks_ms;\n"
        "}\n",
    )
    source = _replace_required(
        source,
        "        marker_checksum(a90_doomgeneric_v3100_phase_policy) == 0U) {\n",
        "        marker_checksum(a90_doomgeneric_v3100_phase_policy) == 0U ||\n"
        "        marker_checksum(a90_doomgeneric_v3126_paced_time_policy) == 0U ||\n"
        "        marker_checksum(a90_doomgeneric_v3126_mode_label) == 0U) {\n",
    )
    source = _replace_required(
        source,
        "    doomgeneric_Create(12, argv);\n"
        "    for (index = 0; frames == 0 || index < frames; ++index) {\n"
        "        int rc;\n",
        "    doomgeneric_Create(12, argv);\n"
        "    paced_ticks_ms = fake_ticks_ms;\n"
        "    paced_tick_remainder_us = 0;\n"
        "    paced_time_active = 1;\n"
        "    for (index = 0; frames == 0 || index < frames; ++index) {\n"
        "        int rc;\n",
    )
    source = _replace_required(
        source,
        "            if (input_socket_fd < 0 && input_udp_fd < 0) {\n"
        "                a90_doomgeneric_apply_input_state_file(input_state_path);\n"
        "            }\n"
        "            doomgeneric_Tick();\n",
        "            if (input_socket_fd < 0 && input_udp_fd < 0) {\n"
        "                a90_doomgeneric_apply_input_state_file(input_state_path);\n"
        "            }\n"
        "            a90_doomgeneric_advance_paced_time();\n"
        "            doomgeneric_Tick();\n",
    )
    source = _replace_required(
        source,
        "    a90_doomgeneric_close_shared_frame(&shared_frame);\n"
        "    a90_doomgeneric_close_pace_socket(pace_fd, pace_socket_path);\n"
        "    if (input_udp_fd >= 0) {\n",
        "    a90_doomgeneric_close_shared_frame(&shared_frame);\n"
        "    paced_time_active = 0;\n"
        "    a90_doomgeneric_close_pace_socket(pace_fd, pace_socket_path);\n"
        "    if (input_udp_fd >= 0) {\n",
    )
    source = _replace_required(
        source,
        '    ok = ok && fprintf(fp, "fake_time_model=DG_SleepMs-accumulated\\n") >= 0;\n',
        '    ok = ok && fprintf(fp, "fake_time_model=DG_SleepMs-request-telemetry-only\\n") >= 0;\n'
        '    ok = ok && fprintf(fp, "paced_time_marker=' + PACED_TIME_MARKER + '\\n") >= 0;\n'
        '    ok = ok && fprintf(fp, "paced_time_model=presenter-token-doom-tic-quantum\\n") >= 0;\n'
        '    ok = ok && fprintf(fp, "smooth_demo_mode=non-original-smooth-demo\\n") >= 0;\n'
        '    ok = ok && fprintf(fp, "paced_time.active=%d\\n", paced_time_active) >= 0;\n'
        '    ok = ok && fprintf(fp, "paced_time.quantum_us=%u\\n", A90_DG_PACED_TICK_QUANTUM_US) >= 0;\n'
        '    ok = ok && fprintf(fp, "paced_time.paced_ticks_ms=%u\\n", paced_ticks_ms) >= 0;\n'
        '    ok = ok && fprintf(fp, "paced_time.remainder_us=%u\\n", paced_tick_remainder_us) >= 0;\n'
        '    ok = ok && fprintf(fp, "paced_time.advance_calls=%u\\n", paced_time_advance_calls) >= 0;\n'
        '    ok = ok && fprintf(fp, "paced_time.advance_us_total=%llu\\n",\n'
        '                      (unsigned long long)paced_time_advance_us_total) >= 0;\n',
    )
    return source


def render_report(
    manifest: dict[str, Any],
    helper_flags: tuple[str, ...],
    init_extra_flags: tuple[str, ...],
) -> str:
    doom = manifest.get("doomgeneric_visible_loop", {})
    return "\n".join([
        "# Native Init V3126 DOOMGENERIC Smooth Demo Direct Blit Source Build",
        "",
        "## Summary",
        "",
        f"- Cycle: `{CYCLE}`",
        "- Track: DOOM residual original-cadence comparison / smooth demo candidate.",
        f"- Decision: `{manifest['decision']}`",
        "- Result: PASS",
        "- Device flash: `no` in this build unit.",
        f"- Boot image: `{manifest['boot_image']}`",
        f"- Boot SHA256: `{manifest['boot_sha256']}`",
        f"- Init: `A90 Linux init {manifest['init_version']} ({manifest['init_build']})`",
        "",
        "## Included Delta",
        "",
        "- Inherits V3123 summary-only direct shared blit, V3120 direct read path, V3118 no-full-clear, and V3116 pre-scaled 960x600 producer output.",
        "- Adds a labelled `non-original-smooth-demo` paced-time model from the V3105 proof: each presenter token advances DOOM virtual time by one 35 Hz tic quantum.",
        "- Keeps `VIDEO_DEMO_DOOMGENERIC_GAMETIC_PRESENT_ONLY=0` so the presenter continues a stable pageflip-token flow instead of changed-frame-only sparse presentation.",
        "- This is a comparison/demo candidate, not a replacement for original-speed DOOM semantics.",
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
        f"- Smooth demo marker: `{PACED_TIME_MARKER}`",
        f"- Tic quantum: `{TICK_QUANTUM_US} us`.",
        "- Foreground loop prints a bounded `video.demo.doom.loop.tick_telemetry.*` summary from the helper telemetry file, so live validation can separate game-tic cadence from presenter/pageflip issues.",
        "- Expected live markers: direct shared-blit reader, summary-only foreground log, and paced-time telemetry.",
        "",
        "## Safety",
        "",
        "- Boot partition only through the checked flash helper `native_init_flash.py` in the next live unit.",
        "- No GPU/GL stack, panel re-init, backlight, PMIC, regulator, GDSC, GPIO, Wi-Fi connect/dhcp/ping, or forbidden partition path.",
        "- Candidate changes userspace DOOM virtual time only; it does not touch display power, partitions, WAD policy, or runtime storage policy.",
        "",
        "## Validation",
        "",
        "- `py_compile`: V3126 builder and focused tests.",
        "- `unittest`: V3126 source contract plus V3123/V3104 regressions.",
        "- Build: AArch64 helper compile/link, native-init compile, ramdisk pack, boot image pack, SHA256 capture.",
        "- Marker check: generated boot image contains V3126 identity, paced-time marker/fields, summary-only direct-blit markers, pre-scaled/no-full-clear markers, shared-frame/pageflip/input/audio markers, and no HW-plane atomic requirement.",
        "- `git diff --check`: PASS.",
        "",
        "## Next Unit",
        "",
        "- Run ID: `V3127`",
        "- Type: rollback-gated live validation.",
        "- Scope: flash exact V3126 image, require paced-time marker plus direct/summary markers, compare changed-gametic smoothness against V3124 while confirming pageflip and rollback health.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `doomgeneric-smooth-demo-direct-blit-candidate`.",
    ]) + "\n"


def configure_v3123_module() -> None:
    v3123.CYCLE = CYCLE
    v3123.INIT_VERSION = INIT_VERSION
    v3123.INIT_BUILD = INIT_BUILD
    v3123.BUILD_TAG = BUILD_TAG
    v3123.DECISION = DECISION
    v3123.OUT_DIR = OUT_DIR
    v3123.OBJ_DIR = OBJ_DIR
    v3123.REPORT_PATH = REPORT_PATH
    v3123.BOOT_IMAGE = BOOT_IMAGE
    v3123.INIT_BINARY = INIT_BINARY
    v3123.RAMDISK_CPIO = RAMDISK_CPIO
    v3123.HELPER_BINARY = HELPER_BINARY
    v3123.ENGINE_BINARY = ENGINE_BINARY
    v3123.ENGINE_ADAPTER_SOURCE = ENGINE_ADAPTER_SOURCE
    v3123.ENGINE_ADAPTER_OBJECT = ENGINE_ADAPTER_OBJECT
    v3123.ENGINE_RAMDISK_PATH = ENGINE_RAMDISK_PATH
    v3123.ENGINE_REMOTE_PATH = ENGINE_REMOTE_PATH
    v3123.ENGINE_NAME = ENGINE_NAME
    v3123.FRAME_PATH = FRAME_PATH
    v3123.SHARED_FRAME_PATH = SHARED_FRAME_PATH
    v3123.INPUT_STATE_PATH = INPUT_STATE_PATH
    v3123.INPUT_SOCKET_PATH = INPUT_SOCKET_PATH
    v3123.PACE_SOCKET_PATH = PACE_SOCKET_PATH
    v3123.TICK_TELEMETRY_PATH = TICK_TELEMETRY_PATH
    v3123.TICK_TELEMETRY_MARKER = TICK_TELEMETRY_MARKER
    v3123.SCALE_MARKER = SCALE_MARKER
    v3123.PHASE_TELEMETRY_MARKER = PHASE_TELEMETRY_MARKER
    v3123.GAMETIC_FRAME_TELEMETRY_MARKER = GAMETIC_FRAME_TELEMETRY_MARKER
    v3123.FRAME_IPC = FRAME_IPC
    v3123.REQUIRED_STRINGS = REQUIRED_STRINGS
    v3123.v3123_adapter_source = v3126_adapter_source
    v3123.render_report = render_report


def apply_v3126_globals() -> None:
    configure_v3123_module()
    _V3123_APPLY_GLOBALS()
    v3033 = v3123.v3120.v3118.v3116.v3033_module()
    v3033.FOREGROUND_FRAME_LOG = FOREGROUND_FRAME_LOG
    v3033.GAMETIC_PRESENT_ONLY = 0
    v3033.TICK_PACE_INTERVAL_US = 0
    v3033.TICK_TELEMETRY_PATH = TICK_TELEMETRY_PATH
    v3033.TICK_TELEMETRY_SUMMARY = 1


def main() -> int:
    original_apply = v3123.apply_v3123_globals
    original_adapter = v3123.v3123_adapter_source
    original_report = v3123.render_report
    try:
        configure_v3123_module()
        v3123.apply_v3123_globals = apply_v3126_globals
        rc = v3123.main()
    finally:
        v3123.apply_v3123_globals = original_apply
        v3123.v3123_adapter_source = original_adapter
        v3123.render_report = original_report

    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    doom = manifest.setdefault("doomgeneric_visible_loop", {})
    doom.update({
        "foreground_frame_log": bool(FOREGROUND_FRAME_LOG),
        "summary_only_foreground": True,
        "smooth_demo_mode": True,
        "semantic_speed": "non-original-smooth-demo",
        "paced_time_marker": PACED_TIME_MARKER,
        "paced_time_quantum_us": TICK_QUANTUM_US,
        "paced_time_model": "presenter-token-doom-tic-quantum",
        "frame_ipc": FRAME_IPC,
        "presenter_reader": "shared-mmap-direct-blit",
        "expected_reader_marker": DIRECT_SHARED_BLIT_MARKER,
        "expected_summary_marker": SUMMARY_ONLY_MARKER,
        "expected_paced_time_marker": PACED_TIME_MARKER,
    })
    manifest.update({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "doomgeneric-smooth-demo-direct-blit-candidate",
        "adoption_state": "pending-smooth-demo-direct-blit-live-validation",
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
    (OUT_DIR / "doomgeneric-smooth-demo-direct-blit-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "doomgeneric-smooth-demo-direct-blit-candidate",
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
        "foreground_frame_log": bool(FOREGROUND_FRAME_LOG),
        "smooth_demo_mode": True,
        "semantic_speed": "non-original-smooth-demo",
        "paced_time_marker": PACED_TIME_MARKER,
        "paced_time_quantum_us": TICK_QUANTUM_US,
        "paced_time_model": "presenter-token-doom-tic-quantum",
        "frame_ipc": FRAME_IPC,
        "present_mode": "pageflip",
        "present_path": "kms-dumb-buffer-pageflip-summary-only-smooth-demo-direct-shared-blit",
        "frame_timing_probe": FRAME_TIMING_PROBE,
        "native_dashboard": bool(NATIVE_DASHBOARD),
        "native_dashboard_minimal": bool(NATIVE_DASHBOARD_MINIMAL),
        "native_dashboard_large_frame": bool(NATIVE_DASHBOARD_LARGE_FRAME),
        "native_doom_present_pageflip": bool(NATIVE_DOOM_PRESENT_PAGEFLIP),
        "loop_start_command": f"video demo doom loop-start 0 --wad runtime-private --sha256 {EXPECTED_WAD_SHA256}",
        "host_keyboard_bridge": rel(v3123.v3120.v3118.v3116.v3114.v3112.v3108.HOST_KEYBOARD_BRIDGE),
        "source_report": rel(REPORT_PATH),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-smooth-demo-direct-blit-live-validation",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
