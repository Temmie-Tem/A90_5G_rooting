#!/usr/bin/env python3
"""Build V3047 native-init doomgeneric batch input candidate."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from _workspace_bootstrap import repo_root
import build_native_init_boot_v3045_doomgeneric_continuous_loop as v3045
from a90harness.evidence import workspace_private_build_path, workspace_private_input_path

REPO_ROOT = repo_root()

CYCLE = "V3047"
INIT_VERSION = "0.10.82"
INIT_BUILD = "v3047-doomgeneric-batch-input"
BUILD_TAG = INIT_BUILD
DECISION = "v3047-doomgeneric-batch-input-source-build-pass"

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
OBJ_DIR = OUT_DIR / "obj"
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V3047_DOOMGENERIC_BATCH_INPUT_SOURCE_BUILD_2026-06-22.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images", "boot_linux_v3047_doomgeneric_batch_input.img", legacy_fallback=False
)
INIT_BINARY = OUT_DIR / "init_v3047_doomgeneric_batch_input"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v3047_doomgeneric_batch_input.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v512_doomgeneric_batch_input"

ENGINE_BINARY = OUT_DIR / "a90_doomgeneric_private_engine_v3047"
ENGINE_ADAPTER_SOURCE = OUT_DIR / "a90_doomgeneric_native_bridge_v3047.c"
ENGINE_ADAPTER_OBJECT = OBJ_DIR / "a90_doomgeneric_native_bridge_v3047.o"
ENGINE_RAMDISK_PATH = "bin/a90_doomgeneric_private_engine_v3047"
ENGINE_REMOTE_PATH = "/" + ENGINE_RAMDISK_PATH
ENGINE_NAME = "doomgeneric-private-link-v3047-batch-input"

RUNTIME_WAD_ROOT = v3045.RUNTIME_WAD_ROOT
RUNTIME_WAD_PATH = v3045.RUNTIME_WAD_PATH
EXPECTED_WAD_SHA256 = v3045.EXPECTED_WAD_SHA256
RUNTIME_WAD_MAX_BYTES = v3045.RUNTIME_WAD_MAX_BYTES
DEFAULT_FRAME_TICKS = v3045.DEFAULT_FRAME_TICKS
DEFAULT_SMOKE_FRAMES = v3045.DEFAULT_SMOKE_FRAMES
DEFAULT_LOOP_FRAMES = v3045.DEFAULT_LOOP_FRAMES
CONTINUOUS_LOOP_FRAMES = v3045.CONTINUOUS_LOOP_FRAMES
MAX_LOOP_FRAMES = v3045.MAX_LOOP_FRAMES
LOOP_FRAME_MS = v3045.LOOP_FRAME_MS
FRAME_PATH = "/tmp/a90-doomgeneric-v3047-batch-input-frame.xbgr8888"
INPUT_STATE_PATH = "/tmp/a90-doomgeneric-v3047-input.state"
FRAME_WIDTH = v3045.FRAME_WIDTH
FRAME_HEIGHT = v3045.FRAME_HEIGHT
FRAME_STRIDE = v3045.FRAME_STRIDE
FRAME_BYTES = v3045.FRAME_BYTES
NATIVE_DASHBOARD = v3045.NATIVE_DASHBOARD
NATIVE_DASHBOARD_LARGE_FRAME = v3045.NATIVE_DASHBOARD_LARGE_FRAME
LARGE_FRAME_WIDTH = v3045.LARGE_FRAME_WIDTH
LARGE_FRAME_HEIGHT = v3045.LARGE_FRAME_HEIGHT
LARGE_FRAME_SCALE = v3045.LARGE_FRAME_SCALE

HOST_KEYBOARD_BRIDGE = v3045.HOST_KEYBOARD_BRIDGE
HOST_DASHBOARD = v3045.HOST_DASHBOARD
BASE_V3045_ADAPTER_SOURCE = v3045.v3045_adapter_source

REQUIRED_STRINGS = (
    b"A90 Linux init 0.10.82 (v3047-doomgeneric-batch-input)",
    b"v3047-doomgeneric-batch-input",
    b"doomgeneric-private-link-v3047-batch-input",
    b"/bin/a90_doomgeneric_private_engine_v3047",
    RUNTIME_WAD_PATH.encode("ascii"),
    EXPECTED_WAD_SHA256.encode("ascii"),
    FRAME_PATH.encode("ascii"),
    INPUT_STATE_PATH.encode("ascii"),
    b"--wad-frame-loop",
    b"--input-state",
    b"--frame-ms",
    b"a90.doomgeneric.v3045.continuous_loop=33ms-loop-start-zero-continuous",
    b"a90.doomgeneric.v3045.loop=input-state-file-to-DG_GetKey-33ms-continuous",
    b"a90.doomgeneric.v3045.frame_color=rb-swap-to-xbgr8888",
    b"a90.doomgeneric.v3045.loop_frames_zero=continuous",
    b"doompad.batch=state-mask-v3047",
    b"doompad.mask.bits=forward:0 back:1 left:2 right:3 fire:4 use:5 menu:6 run:7",
    b"doompad.state_batch seq=",
    b"doompad state <seq> <mask>",
    b"video.demo.doom.loop_start.continuous",
    b"video.demo.doom.loop_status.continuous",
    b"video.demo.doom.dashboard.native=1",
    b"video.demo.doom.dashboard.presenter_log=quiet-per-frame",
    b"host_doompad_dashboard_v3035.py",
    b"host_doompad_keyboard_v3033.py",
    b"video.demo.input.otg_required=0",
)


def rel(path: Path) -> str:
    return v3045.rel(path)


def v3047_adapter_source() -> str:
    return BASE_V3045_ADAPTER_SOURCE()


def configure_v3047_globals() -> None:
    v3045.CYCLE = CYCLE
    v3045.INIT_VERSION = INIT_VERSION
    v3045.INIT_BUILD = INIT_BUILD
    v3045.BUILD_TAG = BUILD_TAG
    v3045.DECISION = DECISION
    v3045.OUT_DIR = OUT_DIR
    v3045.OBJ_DIR = OBJ_DIR
    v3045.REPORT_PATH = REPORT_PATH
    v3045.BOOT_IMAGE = BOOT_IMAGE
    v3045.INIT_BINARY = INIT_BINARY
    v3045.RAMDISK_CPIO = RAMDISK_CPIO
    v3045.HELPER_BINARY = HELPER_BINARY
    v3045.ENGINE_BINARY = ENGINE_BINARY
    v3045.ENGINE_ADAPTER_SOURCE = ENGINE_ADAPTER_SOURCE
    v3045.ENGINE_ADAPTER_OBJECT = ENGINE_ADAPTER_OBJECT
    v3045.ENGINE_RAMDISK_PATH = ENGINE_RAMDISK_PATH
    v3045.ENGINE_REMOTE_PATH = ENGINE_REMOTE_PATH
    v3045.ENGINE_NAME = ENGINE_NAME
    v3045.DEFAULT_LOOP_FRAMES = DEFAULT_LOOP_FRAMES
    v3045.LOOP_FRAME_MS = LOOP_FRAME_MS
    v3045.FRAME_PATH = FRAME_PATH
    v3045.INPUT_STATE_PATH = INPUT_STATE_PATH
    v3045.NATIVE_DASHBOARD = NATIVE_DASHBOARD
    v3045.NATIVE_DASHBOARD_LARGE_FRAME = NATIVE_DASHBOARD_LARGE_FRAME
    v3045.REQUIRED_STRINGS = REQUIRED_STRINGS
    v3045.v3045_adapter_source = v3047_adapter_source
    v3045.render_report = render_report


def render_report(
    manifest: dict[str, Any],
    helper_flags: tuple[str, ...],
    init_extra_flags: tuple[str, ...],
) -> str:
    doom = manifest.get("doomgeneric_visible_loop", {})
    markers = manifest.get("v3033_marker_strings", [])
    marker_lines = [f"- `{marker}`" for marker in markers] if isinstance(markers, list) else []
    return "\n".join([
        "# Native Init V3047 DOOMGENERIC Batch Input Source Build",
        "",
        "## Summary",
        "",
        f"- Cycle: `{CYCLE}`",
        "- Track: active Video playback / DOOM capstone.",
        f"- Decision: `{manifest['decision']}`",
        "- Result: PASS",
        "- Device flash: `no` in this build unit.",
        "- Device action: `none` in this build unit.",
        f"- Boot image: `{manifest['boot_image']}`",
        f"- Boot SHA256: `{manifest['boot_sha256']}`",
        f"- Init: `A90 Linux init {manifest['init_version']} ({manifest['init_build']})`",
        "",
        "## Included Delta",
        "",
        "- Keeps V3045 continuous DOOM loop behavior and V3042 33ms/color/dashboard improvements.",
        "- Adds `doompad state <seq> <mask>` as a batch input command.",
        "- Defines mask bits as `forward:0 back:1 left:2 right:3 fire:4 use:5 menu:6 run:7`.",
        "- Updates host keyboard/dashboard tooling to prefer batch state commands while leaving `--legacy-key-events` for old residents.",
        "- Lowers host defaults to `hold-ms=110` and `poll-ms=10` for tighter release timing.",
        "- Host input remains serial-only; no OTG keyboard, evdev injection, uinput, or host USB HID injection is introduced.",
        "",
        "## Batch Input Contract",
        "",
        "- Native command: `doompad state <seq> <mask>`",
        "- Status marker: `doompad.batch=state-mask-v3047`",
        "- Output marker: `doompad.state_batch seq=<seq> mask=0xXX active=<0|1>`",
        "- Host key down/up transport: `doompad state`, not one command per role edge.",
        "- Legacy fallback: `--legacy-key-events` keeps `doompad key <role> <0|1>`.",
        "",
        "## Runtime WAD / Loop Contract",
        "",
        f"- Runtime WAD path: `{doom.get('runtime_wad_path')}`",
        f"- Expected WAD SHA256: `{doom.get('expected_wad_sha256')}`",
        f"- WAD files in ramdisk: `{doom.get('ramdisk_wad_file_count')}`",
        f"- WAD bytes embedded in boot image: `{doom.get('wad_embedded_in_boot')}`",
        f"- Continuous command: `video demo doom loop-start 0 --wad runtime-private --sha256 {EXPECTED_WAD_SHA256}`",
        f"- Helper loop frame ms: `{doom.get('loop_frame_ms')}`",
        f"- Frame path: `{doom.get('frame_path')}`",
        f"- Input state path: `{doom.get('input_state_path')}`",
        "",
        "## Host Tooling",
        "",
        f"- Host keyboard bridge: `{rel(HOST_KEYBOARD_BRIDGE)}`",
        f"- Host dashboard: `{rel(HOST_DASHBOARD)}`",
        "- Default hold ms: `110`",
        "- Default poll ms: `10`",
        "",
        "## Private Engine Helper",
        "",
        f"- Bundled helper path: `{doom.get('engine_ramdisk_path')}`",
        f"- V3047 engine binary: `{doom.get('engine_binary')}`",
        f"- V3047 engine SHA256: `{doom.get('engine_binary_sha256')}`",
        f"- V3047 engine bytes: `{doom.get('engine_binary_bytes')}`",
        f"- Helper bundled in ramdisk: `{int(bool(doom.get('helper_bundled_in_ramdisk')))}`",
        "",
        "## Marker Check",
        "",
        *marker_lines,
        "",
        "## Safety",
        "",
        "- No device action was performed by this builder.",
        "- No flash, serial live command, Wi-Fi action, sysfs write, evdev injection, uinput, PMIC, regulator, backlight, GPIO, GDSC, or forbidden partition path is touched.",
        "- WAD/IWAD bytes remain only on the runtime SD path and are not copied into public, ramdisk, boot image, reports, or generated source.",
        "- The generated boot image and helper are private/untracked. Public output is limited to source, tests, host tooling, and this metadata-only report.",
        "- Rollback target remains `v2321-usb-clean-identity-rodata` for the next live unit.",
        "",
        "## Host Validation",
        "",
        "- `py_compile`: builder, dependent host scripts, and focused tests.",
        "- `unittest`: V3047 batch-input tests plus host keyboard/dashboard regressions.",
        "- Build: AArch64 static private doomgeneric helper compile/link, native-init compile, ramdisk pack, boot image pack, SHA256 capture.",
        "- Marker check: generated boot image contains V3047 batch-input markers, helper path, input-state path, SD WAD path/hash, and continuous-loop markers.",
        "- Ramdisk inventory: helper path present and WAD file count is zero.",
        "- `git diff --check`: PASS.",
        "",
        "## Next Unit",
        "",
        "- Run ID: `V3048`",
        "- Type: rollback-gated live validation of V3047 batch-input candidate.",
        "- Scope: flash only the exact V3047 boot image through `native_init_flash.py`, health-check, run `doompad state` masks for single and multi-key states, then validate host keyboard/dashboard batch input against a continuous DOOM loop.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `doomgeneric-batch-input-candidate`.",
    ]) + "\n"


def main() -> int:
    if not HOST_DASHBOARD.is_file():
        raise RuntimeError(f"missing host dashboard: {HOST_DASHBOARD}")
    configure_v3047_globals()
    return v3045.main()


if __name__ == "__main__":
    raise SystemExit(main())
