#!/usr/bin/env python3
"""Build V3139 DOOM sectioned demo HUD over the V3137 readable HUD stack."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _workspace_bootstrap import repo_root
from a90harness.evidence import workspace_private_build_path, workspace_private_input_path
import build_native_init_boot_v3137_doomgeneric_demo_hud_readable as v3137

REPO_ROOT = repo_root()
_V3137_ADAPTER_SOURCE_TEXT = v3137.v3137_adapter_source()

CYCLE = "V3139"
INIT_VERSION = "0.10.123"
INIT_BUILD = "v3139-doomgeneric-demo-hud-sectioned"
BUILD_TAG = INIT_BUILD
DECISION = "v3139-doomgeneric-demo-hud-sectioned-source-build-pass"

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
OBJ_DIR = OUT_DIR / "obj"
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V3139_DOOMGENERIC_DEMO_HUD_SECTIONED_SOURCE_BUILD_2026-06-24.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images", "boot_linux_v3139_doomgeneric_demo_hud_sectioned.img", legacy_fallback=False
)
INIT_BINARY = OUT_DIR / "init_v3139_doomgeneric_demo_hud_sectioned"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v3139_doomgeneric_demo_hud_sectioned.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v529_doomgeneric_demo_hud_sectioned"

ENGINE_BINARY = OUT_DIR / "a90_doomgeneric_private_engine_v3139"
ENGINE_ADAPTER_SOURCE = OUT_DIR / "a90_doomgeneric_native_bridge_v3139.c"
ENGINE_ADAPTER_OBJECT = OBJ_DIR / "a90_doomgeneric_native_bridge_v3139.o"
ENGINE_RAMDISK_PATH = "bin/a90_doomgeneric_private_engine_v3139"
ENGINE_REMOTE_PATH = "/" + ENGINE_RAMDISK_PATH
ENGINE_NAME = "doomgeneric-private-link-v3139-demo-hud-sectioned"

FRAME_PATH = "/tmp/a90-doomgeneric-v3139-raw-fallback-frame.xbgr8888"
SHARED_FRAME_PATH = "/tmp/a90-doomgeneric-v3139-shared-frame.bin"
INPUT_STATE_PATH = "/tmp/a90-doomgeneric-v3139-input.state"
INPUT_SOCKET_PATH = "/tmp/a90-doomgeneric-v3139-input.sock"
PACE_SOCKET_PATH = "/tmp/a90-doomgeneric-v3139-pace.sock"
TICK_TELEMETRY_PATH = "/tmp/a90-doomgeneric-v3139-tick-telemetry.txt"

INPUT_THREAD_MARKER = v3137.INPUT_THREAD_MARKER.replace("v3137", "v3139")
TIME_MODEL_MARKER = v3137.TIME_MODEL_MARKER.replace("v3137", "v3139")
DEMO_HUD_MARKER = "a90.doomgeneric.v3139.demo_hud=sectioned-hw-doom-input"

RUNTIME_WAD_PATH = v3137.RUNTIME_WAD_PATH
EXPECTED_WAD_SHA256 = v3137.EXPECTED_WAD_SHA256
FRAME_WIDTH = v3137.FRAME_WIDTH
FRAME_HEIGHT = v3137.FRAME_HEIGHT
FRAME_STRIDE = v3137.FRAME_STRIDE
FRAME_BYTES = v3137.FRAME_BYTES
FRAME_IPC = "shared-mmap-direct-blit-demo-hud-sectioned-monotonic-input-thread"
INPUT_UDP_PORT = v3137.INPUT_UDP_PORT
DEVICE_NCM_HOST = v3137.DEVICE_NCM_HOST

DASHBOARD_METRICS_INTERVAL_FRAMES = v3137.DASHBOARD_METRICS_INTERVAL_FRAMES
DASHBOARD_STATUS_INTERVAL_FRAMES = v3137.DASHBOARD_STATUS_INTERVAL_FRAMES
NATIVE_DASHBOARD = v3137.NATIVE_DASHBOARD
NATIVE_DASHBOARD_MINIMAL = v3137.NATIVE_DASHBOARD_MINIMAL
NATIVE_DASHBOARD_LARGE_FRAME = v3137.NATIVE_DASHBOARD_LARGE_FRAME
NATIVE_DEMO_HUD = v3137.NATIVE_DEMO_HUD
NATIVE_DEMO_HUD_FAST = v3137.NATIVE_DEMO_HUD_FAST
NATIVE_DEMO_HUD_READABLE = 1
NATIVE_DEMO_HUD_SECTIONED = 1
NATIVE_DEMO_HUD_LARGE_GROUPS = 0
PRE_SCALED_LARGE_FRAME = v3137.PRE_SCALED_LARGE_FRAME
FRAME_SCALE = "1:1-demo-hud-sectioned"
SCALE_PATH = "producer-960x600-raw-rowcopy-demo-hud-sectioned"

PACED_TIME_MARKER = v3137.PACED_TIME_MARKER.replace("v3137", "v3139")
TICK_TELEMETRY_MARKER = v3137.TICK_TELEMETRY_MARKER.replace("v3137", "v3139")
SCALE_MARKER = "a90.doomgeneric.v3139.scale=producer-960x600-1to1-demo-hud-sectioned"
PHASE_TELEMETRY_MARKER = v3137.PHASE_TELEMETRY_MARKER.replace("v3137", "v3139")
GAMETIC_FRAME_TELEMETRY_MARKER = v3137.GAMETIC_FRAME_TELEMETRY_MARKER.replace("v3137", "v3139")


def rel(path: Path) -> str:
    return v3137.rel(path)


def _rewrite_required_string(item: bytes) -> bytes:
    replacements = {
        v3137.INIT_VERSION.encode("ascii"): INIT_VERSION.encode("ascii"),
        v3137.INIT_BUILD.encode("ascii"): INIT_BUILD.encode("ascii"),
        v3137.ENGINE_NAME.encode("ascii"): ENGINE_NAME.encode("ascii"),
        v3137.ENGINE_REMOTE_PATH.encode("ascii"): ENGINE_REMOTE_PATH.encode("ascii"),
        v3137.DEMO_HUD_MARKER.encode("ascii"): DEMO_HUD_MARKER.encode("ascii"),
        v3137.SCALE_MARKER.encode("ascii"): SCALE_MARKER.encode("ascii"),
        b"a90-doomgeneric-v3137": b"a90-doomgeneric-v3139",
        b"a90.doomgeneric.v3137": b"a90.doomgeneric.v3139",
        b"v3137": b"v3139",
    }
    for old, new in replacements.items():
        item = item.replace(old, new)
    return item


_DROPPED_INHERITED_MARKERS = (
    b"video.demo.doom.dashboard.layout=top-frame-compact-metrics-input-footer",
    b"video.demo.doom.dashboard.text_scale=title5-main3-small2",
    b"compact cached HUD",
    b"HOST USB-NCM UDP EVDEV keyboard",
)

REQUIRED_STRINGS = tuple(
    item
    for item in (_rewrite_required_string(item) for item in v3137.REQUIRED_STRINGS)
    if item not in _DROPPED_INHERITED_MARKERS
) + (
    b"video.demo.doom.dashboard.layout=top-frame-sectioned-hw-doom-input-footer",
    b"video.demo.doom.dashboard.sectioned_info=1",
    b"video.demo.doom.dashboard.text_scale=section3-main3-small2",
    b"sectioned HW / DOOM / key input HUD",
    b"HW INFO",
    b"DOOM INFO",
    b"KEY INPUT",
    b"USB-NCM UDP EVDEV keyboard",
)


def v3139_adapter_source() -> str:
    source = _V3137_ADAPTER_SOURCE_TEXT
    source = source.replace("v3137", "v3139").replace("V3137", "V3139")
    source = source.replace(
        "a90.doomgeneric.v3139.scale=producer-960x600-1to1-demo-hud-readable",
        SCALE_MARKER,
    )
    source = source.replace(
        "a90.doomgeneric.v3139.demo_hud=fast-readable-spacing-title5-main3",
        DEMO_HUD_MARKER,
    )
    return source


def render_report(
    manifest: dict[str, Any],
    helper_flags: tuple[str, ...],
    init_extra_flags: tuple[str, ...],
) -> str:
    doom = manifest.get("doomgeneric_visible_loop", {})
    return "\n".join([
        "# Native Init V3139 DOOMGENERIC Sectioned Demo HUD Source Build",
        "",
        "## Summary",
        "",
        f"- Cycle: `{CYCLE}`",
        "- Track: DOOM native demo presentation over the V3137 readable HUD stack.",
        f"- Decision: `{manifest['decision']}`",
        "- Result: PASS",
        "- Device flash: `no` in this build unit.",
        f"- Boot image: `{manifest['boot_image']}`",
        f"- Boot SHA256: `{manifest['boot_sha256']}`",
        f"- Init: `A90 Linux init {manifest['init_version']} ({manifest['init_build']})`",
        "",
        "## Included Delta",
        "",
        "- Keeps the V3137 input, timing, pageflip, metrics cache, targeted redraw, and readable text scale.",
        "- Adds `A90_DOOMGENERIC_NATIVE_DEMO_HUD_SECTIONED=1` for sectioned demo layout.",
        "- Groups the lower HUD into `HW INFO`, `DOOM INFO`, and `KEY INPUT` sections.",
        "- Makes CPU/GPU and FPS rows primary scale-3 lines, with memory, battery, WAD, and host-script details as scale-2 support lines.",
        f"- Demo HUD marker: `{DEMO_HUD_MARKER}`",
        "",
        "## Runtime Contract",
        "",
        f"- Runtime WAD path: `{doom.get('runtime_wad_path')}`",
        f"- Expected WAD SHA256: `{doom.get('expected_wad_sha256')}`",
        f"- Frame geometry: `{FRAME_WIDTH}x{FRAME_HEIGHT}` stride `{FRAME_STRIDE}` bytes `{FRAME_BYTES}`",
        f"- Frame IPC: `{FRAME_IPC}`",
        f"- Dashboard metrics interval frames: `{DASHBOARD_METRICS_INTERVAL_FRAMES}`",
        f"- Dashboard status interval frames: `{DASHBOARD_STATUS_INTERVAL_FRAMES}`",
        "",
        "## Safety",
        "",
        "- Boot partition only through `native_init_flash.py` in the live step.",
        "- No GPU/GL stack, panel re-init, PMIC, regulator, GDSC, GPIO, Wi-Fi connect/dhcp/ping, or forbidden partition path.",
        "- Changes are limited to userspace native-init HUD layout flags/strings plus private DOOM helper identity.",
        "",
        "## Validation",
        "",
        "- `py_compile`: V3139 builder and focused tests.",
        "- `unittest`: V3139 source contract plus V3137/V3135/V3133 focused regressions.",
        "- Build: AArch64 helper/native-init compile, ramdisk pack, boot image pack, SHA256 capture.",
        "- Marker check: generated boot image contains V3139 identity, sectioned HUD markers, and inherited V3137 fast HUD markers.",
        "- `git diff --check`: PASS.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `doomgeneric-demo-hud-sectioned-candidate`.",
    ]) + "\n"


_PATCHED_V3137_ATTRS = (
    "CYCLE",
    "INIT_VERSION",
    "INIT_BUILD",
    "BUILD_TAG",
    "DECISION",
    "OUT_DIR",
    "OBJ_DIR",
    "REPORT_PATH",
    "BOOT_IMAGE",
    "INIT_BINARY",
    "RAMDISK_CPIO",
    "HELPER_BINARY",
    "ENGINE_BINARY",
    "ENGINE_ADAPTER_SOURCE",
    "ENGINE_ADAPTER_OBJECT",
    "ENGINE_RAMDISK_PATH",
    "ENGINE_REMOTE_PATH",
    "ENGINE_NAME",
    "FRAME_PATH",
    "SHARED_FRAME_PATH",
    "INPUT_STATE_PATH",
    "INPUT_SOCKET_PATH",
    "PACE_SOCKET_PATH",
    "TICK_TELEMETRY_PATH",
    "INPUT_THREAD_MARKER",
    "TIME_MODEL_MARKER",
    "DEMO_HUD_MARKER",
    "PACED_TIME_MARKER",
    "TICK_TELEMETRY_MARKER",
    "SCALE_MARKER",
    "PHASE_TELEMETRY_MARKER",
    "GAMETIC_FRAME_TELEMETRY_MARKER",
    "FRAME_IPC",
    "REQUIRED_STRINGS",
    "NATIVE_DEMO_HUD_READABLE",
    "NATIVE_DEMO_HUD_SECTIONED",
    "NATIVE_DEMO_HUD_LARGE_GROUPS",
    "FRAME_SCALE",
    "SCALE_PATH",
)


def configure_v3139_module() -> dict[str, Any]:
    saved = {name: getattr(v3137, name) for name in _PATCHED_V3137_ATTRS}
    saved["v3137_adapter_source"] = v3137.v3137_adapter_source
    saved["render_report"] = v3137.render_report
    for name in _PATCHED_V3137_ATTRS:
        setattr(v3137, name, globals()[name])
    v3137.v3137_adapter_source = v3139_adapter_source
    v3137.render_report = render_report
    return saved


def restore_v3137_module(saved: dict[str, Any]) -> None:
    for name in _PATCHED_V3137_ATTRS:
        setattr(v3137, name, saved[name])
    v3137.v3137_adapter_source = saved["v3137_adapter_source"]
    v3137.render_report = saved["render_report"]


def main() -> int:
    saved = configure_v3139_module()
    try:
        rc = v3137.main()
    finally:
        restore_v3137_module(saved)

    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    doom = manifest.setdefault("doomgeneric_visible_loop", {})
    doom.update({
        "demo_hud_sectioned": True,
        "demo_hud_marker": DEMO_HUD_MARKER,
        "native_demo_hud_readable": True,
        "native_demo_hud_sectioned": True,
        "frame_scale": FRAME_SCALE,
        "scale_path": SCALE_PATH,
        "frame_ipc": FRAME_IPC,
    })
    manifest.update({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "doomgeneric-demo-hud-sectioned-candidate",
        "adoption_state": "pending-demo-hud-sectioned-live-validation",
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
    (OUT_DIR / "doomgeneric-demo-hud-sectioned-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "doomgeneric-demo-hud-sectioned-candidate",
        "boot_image": rel(BOOT_IMAGE),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "runtime_wad_path": RUNTIME_WAD_PATH,
        "expected_wad_sha256": EXPECTED_WAD_SHA256,
        "frame_path": FRAME_PATH,
        "shared_frame_path": SHARED_FRAME_PATH,
        "input_state_path": INPUT_STATE_PATH,
        "input_socket_path": INPUT_SOCKET_PATH,
        "input_udp_host": DEVICE_NCM_HOST,
        "input_udp_port": INPUT_UDP_PORT,
        "demo_hud_marker": DEMO_HUD_MARKER,
        "native_demo_hud_sectioned": True,
        "source_report": rel(REPORT_PATH),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-demo-hud-sectioned-live-validation",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
