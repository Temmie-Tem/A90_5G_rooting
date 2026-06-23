#!/usr/bin/env python3
"""Build V3104 native-init DOOM presenter-token paced tic candidate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _workspace_bootstrap import repo_root
import build_native_init_boot_v3100_doomgeneric_phase_telemetry as v3100
from a90harness.evidence import workspace_private_build_path, workspace_private_input_path

REPO_ROOT = repo_root()

CYCLE = "V3104"
INIT_VERSION = "0.10.108"
INIT_BUILD = "v3104-doomgeneric-paced-tic"
BUILD_TAG = INIT_BUILD
DECISION = "v3104-doomgeneric-paced-tic-source-build-pass"

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
OBJ_DIR = OUT_DIR / "obj"
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V3104_DOOMGENERIC_PACED_TIC_SOURCE_BUILD_2026-06-23.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images", "boot_linux_v3104_doomgeneric_paced_tic.img", legacy_fallback=False
)
INIT_BINARY = OUT_DIR / "init_v3104_doomgeneric_paced_tic"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v3104_doomgeneric_paced_tic.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v519_doomgeneric_paced_tic"

ENGINE_BINARY = OUT_DIR / "a90_doomgeneric_private_engine_v3104"
ENGINE_ADAPTER_SOURCE = OUT_DIR / "a90_doomgeneric_native_bridge_v3104.c"
ENGINE_ADAPTER_OBJECT = OBJ_DIR / "a90_doomgeneric_native_bridge_v3104.o"
ENGINE_RAMDISK_PATH = "bin/a90_doomgeneric_private_engine_v3104"
ENGINE_REMOTE_PATH = "/" + ENGINE_RAMDISK_PATH
ENGINE_NAME = "doomgeneric-private-link-v3104-paced-tic"

RUNTIME_WAD_ROOT = v3100.RUNTIME_WAD_ROOT
RUNTIME_WAD_PATH = v3100.RUNTIME_WAD_PATH
EXPECTED_WAD_SHA256 = v3100.EXPECTED_WAD_SHA256
RUNTIME_WAD_MAX_BYTES = v3100.RUNTIME_WAD_MAX_BYTES
DEFAULT_FRAME_TICKS = v3100.DEFAULT_FRAME_TICKS
DEFAULT_SMOKE_FRAMES = v3100.DEFAULT_SMOKE_FRAMES
DEFAULT_LOOP_FRAMES = v3100.DEFAULT_LOOP_FRAMES
CONTINUOUS_LOOP_FRAMES = v3100.CONTINUOUS_LOOP_FRAMES
MAX_LOOP_FRAMES = v3100.MAX_LOOP_FRAMES
LOOP_FRAME_MS = v3100.LOOP_FRAME_MS
PRESENTER_POLL_MS = v3100.PRESENTER_POLL_MS
FRAME_PATH = "/tmp/a90-doomgeneric-v3104-raw-fallback-frame.xbgr8888"
SHARED_FRAME_PATH = "/tmp/a90-doomgeneric-v3104-shared-frame.bin"
INPUT_STATE_PATH = "/tmp/a90-doomgeneric-v3104-input.state"
INPUT_SOCKET_PATH = "/tmp/a90-doomgeneric-v3104-input.sock"
INPUT_UDP_PORT = v3100.INPUT_UDP_PORT
DEVICE_NCM_HOST = v3100.DEVICE_NCM_HOST
PACE_SOCKET_PATH = "/tmp/a90-doomgeneric-v3104-pace.sock"
TICK_TELEMETRY_PATH = "/tmp/a90-doomgeneric-v3104-tick-telemetry.txt"
TICK_QUANTUM_US = 28571

PAGEFLIP_MIN_SUBMIT_INTERVAL_MS = v3100.PAGEFLIP_MIN_SUBMIT_INTERVAL_MS
BASELINE_PAGEFLIP_MIN_SUBMIT_INTERVAL_MS = v3100.BASELINE_PAGEFLIP_MIN_SUBMIT_INTERVAL_MS
FRAME_WIDTH = v3100.FRAME_WIDTH
FRAME_HEIGHT = v3100.FRAME_HEIGHT
FRAME_STRIDE = v3100.FRAME_STRIDE
FRAME_BYTES = v3100.FRAME_BYTES
NATIVE_DASHBOARD = v3100.NATIVE_DASHBOARD
NATIVE_DASHBOARD_MINIMAL = v3100.NATIVE_DASHBOARD_MINIMAL
NATIVE_DASHBOARD_LARGE_FRAME = v3100.NATIVE_DASHBOARD_LARGE_FRAME
BASELINE_NATIVE_DASHBOARD_LARGE_FRAME = v3100.BASELINE_NATIVE_DASHBOARD_LARGE_FRAME
NATIVE_DOOM_PRESENT_PAGEFLIP = v3100.NATIVE_DOOM_PRESENT_PAGEFLIP
BASELINE_FRAME_SCALE = v3100.BASELINE_FRAME_SCALE
FRAME_SCALE = v3100.FRAME_SCALE
SCALE_PATH = v3100.SCALE_PATH
REUSE_FRAME_BUFFER = v3100.REUSE_FRAME_BUFFER
DASHBOARD_METRICS_INTERVAL_FRAMES = v3100.DASHBOARD_METRICS_INTERVAL_FRAMES
FRAME_TIMING_PROBE = v3100.FRAME_TIMING_PROBE
SEQ_TELEMETRY = v3100.SEQ_TELEMETRY
BASELINE_BACKGROUND_CANCEL = v3100.BASELINE_BACKGROUND_CANCEL
CANDIDATE_BACKGROUND_CANCEL = v3100.CANDIDATE_BACKGROUND_CANCEL

SOUND_MODE = v3100.SOUND_MODE
AUDIO_CORUN = v3100.AUDIO_CORUN
AUDIO_CORUN_MODE = v3100.AUDIO_CORUN_MODE
AUDIO_CORUN_DURATION_MS = v3100.AUDIO_CORUN_DURATION_MS
AUDIO_CORUN_AMPLITUDE_MILLI = v3100.AUDIO_CORUN_AMPLITUDE_MILLI

HOST_KEYBOARD_BRIDGE = v3100.HOST_KEYBOARD_BRIDGE
HOST_DASHBOARD = v3100.HOST_DASHBOARD
V3059 = v3100.V3059

TICK_TELEMETRY_MARKER = "a90.doomgeneric.v3104.tick_telemetry=paced-tic-phase-summary"
SCALE_1TO1_MARKER = "a90.doomgeneric.v3104.scale=large-frame-off-1to1"
GAMETIC_FRAME_TELEMETRY_MARKER = "a90.doomgeneric.v3104.gametic_frame_telemetry=loop-dump-gametic-summary"
PHASE_TELEMETRY_MARKER = "a90.doomgeneric.v3104.phase_telemetry=tick-draw-dump-split"
PACED_TIME_MARKER = "a90.doomgeneric.v3104.paced_time=presenter-token-doom-tic-quantum"
SEQ_TELEMETRY_CONTRACT = v3100.SEQ_TELEMETRY_CONTRACT
SEQ_TELEMETRY_MODEL = v3100.SEQ_TELEMETRY_MODEL

REQUIRED_STRINGS = (
    b"A90 Linux init 0.10.108 (v3104-doomgeneric-paced-tic)",
    b"v3104-doomgeneric-paced-tic",
    b"doomgeneric-private-link-v3104-paced-tic",
    b"/bin/a90_doomgeneric_private_engine_v3104",
    RUNTIME_WAD_PATH.encode("ascii"),
    EXPECTED_WAD_SHA256.encode("ascii"),
    FRAME_PATH.encode("ascii"),
    SHARED_FRAME_PATH.encode("ascii"),
    INPUT_STATE_PATH.encode("ascii"),
    INPUT_SOCKET_PATH.encode("ascii"),
    PACE_SOCKET_PATH.encode("ascii"),
    TICK_TELEMETRY_PATH.encode("ascii"),
    TICK_TELEMETRY_MARKER.encode("ascii"),
    SCALE_1TO1_MARKER.encode("ascii"),
    GAMETIC_FRAME_TELEMETRY_MARKER.encode("ascii"),
    PHASE_TELEMETRY_MARKER.encode("ascii"),
    PACED_TIME_MARKER.encode("ascii"),
    b"paced_time_model=presenter-token-doom-tic-quantum",
    b"paced_time.quantum_us=%u",
    b"paced_time.advance_calls=%u",
    b"paced_time.paced_ticks_ms=%u",
    b"a90.doomgeneric.v3059.input=udp-ncm-state-with-unix-dgram-fallback",
    b"a90.doomgeneric.v3079.pace=presenter-pageflip-token",
    b"a90.doomgeneric.v3081.frame_ipc=shared-mmap-seq",
    b"--shared-frame",
    b"shared-mmap-copy",
    b"video.demo.doom.dashboard.large_frame=0",
    b"video.demo.doom.dashboard.frame_scale=1:1",
    SEQ_TELEMETRY_CONTRACT.encode("ascii"),
    SEQ_TELEMETRY_MODEL.encode("ascii"),
    b"loop_tick.samples=%u",
    b"loop_tick.gametic_changed=%u",
    b"loop_tick.gametic_repeated=%u",
    b"draw_gametic.samples=%u",
    b"dump_gametic.samples=%u",
    b"video.demo.doom.loop_start.background_cancel=disabled-serial-preserve",
    b"video.demo.doom.loop.timing_probe=1",
    b"native-audio-corun-tone-v3053",
)


def rel(path: Path) -> str:
    return v3100.rel(path)


def v3033_module() -> Any:
    return v3100.v3033_module()


def _replace_required(source: str, old: str, new: str) -> str:
    if old not in source:
        raise RuntimeError(f"missing V3104 adapter source anchor: {old[:96]!r}")
    return source.replace(old, new, 1)


def v3104_adapter_source() -> str:
    source = v3100.v3100_adapter_source()
    replacements = {
        v3100.TICK_TELEMETRY_MARKER: TICK_TELEMETRY_MARKER,
        v3100.SCALE_1TO1_MARKER: SCALE_1TO1_MARKER,
        v3100.GAMETIC_FRAME_TELEMETRY_MARKER: GAMETIC_FRAME_TELEMETRY_MARKER,
        v3100.PHASE_TELEMETRY_MARKER: PHASE_TELEMETRY_MARKER,
        v3100.TICK_TELEMETRY_PATH: TICK_TELEMETRY_PATH,
        v3100.FRAME_PATH: FRAME_PATH,
        v3100.SHARED_FRAME_PATH: SHARED_FRAME_PATH,
        v3100.INPUT_STATE_PATH: INPUT_STATE_PATH,
        v3100.INPUT_SOCKET_PATH: INPUT_SOCKET_PATH,
        v3100.PACE_SOCKET_PATH: PACE_SOCKET_PATH,
    }
    for old, new in replacements.items():
        source = source.replace(old, new)
    source = _replace_required(
        source,
        'const char a90_doomgeneric_v3100_phase_policy[] =\n'
        f'    "{PHASE_TELEMETRY_MARKER}";\n',
        'const char a90_doomgeneric_v3100_phase_policy[] =\n'
        f'    "{PHASE_TELEMETRY_MARKER}";\n'
        'const char a90_doomgeneric_v3104_paced_time_policy[] =\n'
        f'    "{PACED_TIME_MARKER}";\n',
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
        "        marker_checksum(a90_doomgeneric_v3104_paced_time_policy) == 0U) {\n",
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
        '    ok = ok && fprintf(fp, "paced_time.active=%d\\n", paced_time_active) >= 0;\n'
        '    ok = ok && fprintf(fp, "paced_time.quantum_us=%u\\n", A90_DG_PACED_TICK_QUANTUM_US) >= 0;\n'
        '    ok = ok && fprintf(fp, "paced_time.paced_ticks_ms=%u\\n", paced_ticks_ms) >= 0;\n'
        '    ok = ok && fprintf(fp, "paced_time.remainder_us=%u\\n", paced_tick_remainder_us) >= 0;\n'
        '    ok = ok && fprintf(fp, "paced_time.advance_calls=%u\\n", paced_time_advance_calls) >= 0;\n'
        '    ok = ok && fprintf(fp, "paced_time.advance_us_total=%llu\\n",\n'
        '                      (unsigned long long)paced_time_advance_us_total) >= 0;\n',
    )
    return source


def apply_v3104_globals() -> None:
    v3100.apply_v3100_globals()
    base = v3100.v3098.v3096.v3086
    base.CYCLE = CYCLE
    base.INIT_VERSION = INIT_VERSION
    base.INIT_BUILD = INIT_BUILD
    base.BUILD_TAG = BUILD_TAG
    base.DECISION = DECISION
    base.OUT_DIR = OUT_DIR
    base.OBJ_DIR = OBJ_DIR
    base.REPORT_PATH = REPORT_PATH
    base.BOOT_IMAGE = BOOT_IMAGE
    base.INIT_BINARY = INIT_BINARY
    base.RAMDISK_CPIO = RAMDISK_CPIO
    base.HELPER_BINARY = HELPER_BINARY
    base.ENGINE_BINARY = ENGINE_BINARY
    base.ENGINE_ADAPTER_SOURCE = ENGINE_ADAPTER_SOURCE
    base.ENGINE_ADAPTER_OBJECT = ENGINE_ADAPTER_OBJECT
    base.ENGINE_RAMDISK_PATH = ENGINE_RAMDISK_PATH
    base.ENGINE_REMOTE_PATH = ENGINE_REMOTE_PATH
    base.ENGINE_NAME = ENGINE_NAME
    base.FRAME_PATH = FRAME_PATH
    base.SHARED_FRAME_PATH = SHARED_FRAME_PATH
    base.INPUT_STATE_PATH = INPUT_STATE_PATH
    base.INPUT_SOCKET_PATH = INPUT_SOCKET_PATH
    base.PACE_SOCKET_PATH = PACE_SOCKET_PATH
    base.REQUIRED_STRINGS = REQUIRED_STRINGS
    base.render_report = render_report
    base.v3084.v3083.v3081.v3081_adapter_source = v3104_adapter_source
    v3100.v3098.v3096._set_large_frame(NATIVE_DASHBOARD_LARGE_FRAME)
    v3100.v3098.v3096._set_seq_telemetry(SEQ_TELEMETRY)
    base.apply_v3086_globals()
    v3100.v3098.v3096._set_large_frame(NATIVE_DASHBOARD_LARGE_FRAME)
    v3100.v3098.v3096._set_seq_telemetry(SEQ_TELEMETRY)
    base.v3084.v3083.v3081.v3081_adapter_source = v3104_adapter_source
    V3059.v3059_adapter_source = v3104_adapter_source

    v3033 = v3033_module()
    v3033.SHARED_FRAME_PATH = SHARED_FRAME_PATH
    v3033.PACE_SOCKET_PATH = PACE_SOCKET_PATH
    v3033.GAMETIC_PRESENT_ONLY = 0
    v3033.TICK_PACE_INTERVAL_US = 0


def render_report(
    manifest: dict[str, Any],
    helper_flags: tuple[str, ...],
    init_extra_flags: tuple[str, ...],
) -> str:
    doom = manifest.get("doomgeneric_visible_loop", {})
    markers = manifest.get("v3033_marker_strings", [])
    marker_lines = [f"- `{marker}`" for marker in markers] if isinstance(markers, list) else []
    return "\n".join([
        "# Native Init V3104 DOOMGENERIC Paced Tic Source Build",
        "",
        "## Summary",
        "",
        f"- Cycle: `{CYCLE}`",
        "- Track: active Video playback / DOOM tic cadence behavior.",
        f"- Decision: `{manifest['decision']}`",
        "- Result: PASS",
        "- Device flash: `no` in this build unit.",
        f"- Boot image: `{manifest['boot_image']}`",
        f"- Boot SHA256: `{manifest['boot_sha256']}`",
        f"- Init: `A90 Linux init {manifest['init_version']} ({manifest['init_build']})`",
        "",
        "## Included Delta",
        "",
        "- Keeps V3100's 60 Hz pageflip presentation baseline, 1:1 scale, shared-frame sequence telemetry, phase telemetry, audio corun, and UDP/NCM input.",
        "- Changes the DOOM port clock while the helper loop is active: presenter pace tokens advance `DG_GetTicksMs()` by a fixed DOOM tic quantum.",
        f"- Tic quantum: `{TICK_QUANTUM_US} us`, which targets one 35 Hz DOOM tic per presenter token.",
        "- This is a diagnostic/non-original-speed candidate. It asks whether visible stutter disappears when `gametic` changes every displayed frame.",
        "",
        "## Telemetry Contract",
        "",
        f"- Tick telemetry marker: `{TICK_TELEMETRY_MARKER}`",
        f"- Phase telemetry marker: `{PHASE_TELEMETRY_MARKER}`",
        f"- Paced-time marker: `{PACED_TIME_MARKER}`",
        f"- Telemetry path: `{TICK_TELEMETRY_PATH}`",
        "- Key fields: `loop_tick.*`, `draw_gametic.*`, `dump_gametic.*`, `paced_time.*`, and `fake_time_model`.",
        "",
        "## Runtime Contract",
        "",
        f"- Runtime WAD path: `{doom.get('runtime_wad_path')}`",
        f"- Expected WAD SHA256: `{doom.get('expected_wad_sha256')}`",
        f"- Helper loop command: `{doom.get('helper_loop_command')}`",
        f"- Continuous command: `video demo doom loop-start 0 --wad runtime-private --sha256 {EXPECTED_WAD_SHA256}`",
        "",
        "## Marker Check",
        "",
        *marker_lines,
        "",
        "## Validation",
        "",
        "- `py_compile`: V3104 builder and focused tests.",
        "- `unittest`: V3104 source contract plus current DOOM cadence lineage regressions.",
        "- Build: AArch64 helper compile/link, native-init compile, ramdisk pack, boot image pack, SHA256 capture.",
        "- Marker check: generated boot image contains V3104 identity, paced-time markers/fields, phase telemetry, 1:1 scale, sequence telemetry, shared-frame, audio, and UDP input markers.",
        "- `git diff --check`: PASS.",
        "",
        "## Next Unit",
        "",
        "- Run ID: `V3105`",
        "- Type: rollback-gated live validation.",
        "- Scope: flash exact V3104 boot image via `native_init_flash.py`, health-check, run bounded DOOM loops, and compare `loop_tick.gametic_repeated`, pageflip deltas, and perceived speed against V3101/V3103.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `doomgeneric-paced-tic-candidate`.",
    ]) + "\n"


def main() -> int:
    apply_v3104_globals()
    rc = v3100.v3098.v3096.v3086.v3084.main()
    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    doom = manifest.setdefault("doomgeneric_visible_loop", {})
    doom.update({
        "cadence_experiment": "presenter-token-paced-doom-tic",
        "tick_telemetry_marker": TICK_TELEMETRY_MARKER,
        "phase_telemetry_marker": PHASE_TELEMETRY_MARKER,
        "gametic_frame_telemetry_marker": GAMETIC_FRAME_TELEMETRY_MARKER,
        "paced_time_marker": PACED_TIME_MARKER,
        "paced_time_quantum_us": TICK_QUANTUM_US,
        "paced_time_model": "presenter-token-doom-tic-quantum",
        "seq_telemetry_contract": SEQ_TELEMETRY_CONTRACT,
        "seq_telemetry_model": SEQ_TELEMETRY_MODEL,
        "seq_telemetry_enabled": bool(SEQ_TELEMETRY),
        "tick_telemetry_path": TICK_TELEMETRY_PATH,
        "fake_time_model": "DG_SleepMs-request-telemetry-only",
        "native_dashboard_large_frame": bool(NATIVE_DASHBOARD_LARGE_FRAME),
        "baseline_native_dashboard_large_frame": bool(BASELINE_NATIVE_DASHBOARD_LARGE_FRAME),
        "baseline_frame_scale": BASELINE_FRAME_SCALE,
        "frame_scale": FRAME_SCALE,
        "scale_path": SCALE_PATH,
        "helper_loop_command": (
            f"{ENGINE_REMOTE_PATH} --wad-frame-loop {RUNTIME_WAD_PATH} "
            f"--frames {DEFAULT_LOOP_FRAMES} --output {FRAME_PATH} "
            f"--input-state {INPUT_STATE_PATH} --frame-ms {LOOP_FRAME_MS} "
            f"--input-socket {INPUT_SOCKET_PATH} --pace-socket {PACE_SOCKET_PATH} "
            f"--shared-frame {SHARED_FRAME_PATH} --input-udp {INPUT_UDP_PORT}"
        ),
    })
    manifest.update({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "doomgeneric-paced-tic-candidate",
        "adoption_state": "pending-paced-tic-live-validation",
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
    (OUT_DIR / "doomgeneric-paced-tic-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "doomgeneric-paced-tic-candidate",
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
        "input_state_path": INPUT_STATE_PATH,
        "input_socket_path": INPUT_SOCKET_PATH,
        "input_udp_host": DEVICE_NCM_HOST,
        "input_udp_port": INPUT_UDP_PORT,
        "pace_socket_path": PACE_SOCKET_PATH,
        "tick_telemetry_marker": TICK_TELEMETRY_MARKER,
        "phase_telemetry_marker": PHASE_TELEMETRY_MARKER,
        "gametic_frame_telemetry_marker": GAMETIC_FRAME_TELEMETRY_MARKER,
        "paced_time_marker": PACED_TIME_MARKER,
        "paced_time_quantum_us": TICK_QUANTUM_US,
        "paced_time_model": "presenter-token-doom-tic-quantum",
        "seq_telemetry_contract": SEQ_TELEMETRY_CONTRACT,
        "seq_telemetry_model": SEQ_TELEMETRY_MODEL,
        "seq_telemetry_enabled": bool(SEQ_TELEMETRY),
        "tick_telemetry_path": TICK_TELEMETRY_PATH,
        "loop_frame_ms": LOOP_FRAME_MS,
        "presenter_poll_ms": PRESENTER_POLL_MS,
        "pageflip_min_submit_interval_baseline_ms": BASELINE_PAGEFLIP_MIN_SUBMIT_INTERVAL_MS,
        "pageflip_min_submit_interval_ms": PAGEFLIP_MIN_SUBMIT_INTERVAL_MS,
        "frame_ipc": v3100.v3098.v3096.v3086.v3084.v3083.v3081.CANDIDATE_FRAME_IPC,
        "frame_scale": FRAME_SCALE,
        "scale_path": SCALE_PATH,
        "baseline_frame_scale": BASELINE_FRAME_SCALE,
        "background_cancel": CANDIDATE_BACKGROUND_CANCEL,
        "present_mode": "pageflip",
        "present_path": "kms-dumb-buffer-pageflip",
        "frame_timing_probe": FRAME_TIMING_PROBE,
        "fake_time_model": "DG_SleepMs-request-telemetry-only",
        "native_dashboard": bool(NATIVE_DASHBOARD),
        "native_dashboard_minimal": bool(NATIVE_DASHBOARD_MINIMAL),
        "native_dashboard_large_frame": bool(NATIVE_DASHBOARD_LARGE_FRAME),
        "native_doom_present_pageflip": bool(NATIVE_DOOM_PRESENT_PAGEFLIP),
        "loop_start_command": f"video demo doom loop-start 0 --wad runtime-private --sha256 {EXPECTED_WAD_SHA256}",
        "host_keyboard_bridge": rel(HOST_KEYBOARD_BRIDGE),
        "source_report": rel(REPORT_PATH),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-paced-tic-live-validation",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
