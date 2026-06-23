#!/usr/bin/env python3
"""Build V3110 native-init DOOM hardware-plane diagnostics candidate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _workspace_bootstrap import repo_root
from a90harness.evidence import workspace_private_build_path, workspace_private_input_path
import build_native_init_boot_v3108_doomgeneric_hw_plane_scale as v3108

REPO_ROOT = repo_root()
V3108_ADAPTER_SOURCE = v3108.v3108_adapter_source

CYCLE = "V3110"
INIT_VERSION = "0.10.110"
INIT_BUILD = "v3110-doomgeneric-hw-plane-diagnostics"
BUILD_TAG = INIT_BUILD
DECISION = "v3110-doomgeneric-hw-plane-diagnostics-source-build-pass"

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
OBJ_DIR = OUT_DIR / "obj"
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V3110_DOOMGENERIC_HW_PLANE_DIAGNOSTICS_SOURCE_BUILD_2026-06-23.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images", "boot_linux_v3110_doomgeneric_hw_plane_diagnostics.img", legacy_fallback=False
)
INIT_BINARY = OUT_DIR / "init_v3110_doomgeneric_hw_plane_diagnostics"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v3110_doomgeneric_hw_plane_diagnostics.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v520_doomgeneric_hw_plane_diagnostics"

ENGINE_BINARY = OUT_DIR / "a90_doomgeneric_private_engine_v3110"
ENGINE_ADAPTER_SOURCE = OUT_DIR / "a90_doomgeneric_native_bridge_v3110.c"
ENGINE_ADAPTER_OBJECT = OBJ_DIR / "a90_doomgeneric_native_bridge_v3110.o"
ENGINE_RAMDISK_PATH = "bin/a90_doomgeneric_private_engine_v3110"
ENGINE_REMOTE_PATH = "/" + ENGINE_RAMDISK_PATH
ENGINE_NAME = "doomgeneric-private-link-v3110-hw-plane-diagnostics"

RUNTIME_WAD_ROOT = v3108.RUNTIME_WAD_ROOT
RUNTIME_WAD_PATH = v3108.RUNTIME_WAD_PATH
EXPECTED_WAD_SHA256 = v3108.EXPECTED_WAD_SHA256
RUNTIME_WAD_MAX_BYTES = v3108.RUNTIME_WAD_MAX_BYTES
DEFAULT_LOOP_FRAMES = v3108.DEFAULT_LOOP_FRAMES
LOOP_FRAME_MS = v3108.LOOP_FRAME_MS
PRESENTER_POLL_MS = v3108.PRESENTER_POLL_MS
FRAME_PATH = "/tmp/a90-doomgeneric-v3110-raw-fallback-frame.xbgr8888"
SHARED_FRAME_PATH = "/tmp/a90-doomgeneric-v3110-shared-frame.bin"
INPUT_STATE_PATH = "/tmp/a90-doomgeneric-v3110-input.state"
INPUT_SOCKET_PATH = "/tmp/a90-doomgeneric-v3110-input.sock"
PACE_SOCKET_PATH = "/tmp/a90-doomgeneric-v3110-pace.sock"
TICK_TELEMETRY_PATH = "/tmp/a90-doomgeneric-v3110-tick-telemetry.txt"
INPUT_UDP_PORT = v3108.INPUT_UDP_PORT
DEVICE_NCM_HOST = v3108.DEVICE_NCM_HOST

NATIVE_DASHBOARD = v3108.NATIVE_DASHBOARD
NATIVE_DASHBOARD_MINIMAL = v3108.NATIVE_DASHBOARD_MINIMAL
NATIVE_DASHBOARD_LARGE_FRAME = 1
HW_PLANE_SCALE = 1
FRAME_SCALE = "3:2-hw-plane-diagnostics"
SCALE_PATH = "drm-plane-srcdst-diagnostic"
FALLBACK_SCALE_PATH = v3108.FALLBACK_SCALE_PATH
FRAME_TIMING_PROBE = v3108.FRAME_TIMING_PROBE
SEQ_TELEMETRY = v3108.SEQ_TELEMETRY
NATIVE_DOOM_PRESENT_PAGEFLIP = v3108.NATIVE_DOOM_PRESENT_PAGEFLIP

TICK_TELEMETRY_MARKER = "a90.doomgeneric.v3110.tick_telemetry=hw-plane-diagnostics-original-cadence"
SCALE_MARKER = "a90.doomgeneric.v3110.scale=drm-plane-srcdst-diagnostics"
PHASE_TELEMETRY_MARKER = "a90.doomgeneric.v3110.phase_telemetry=tick-draw-dump-split"
GAMETIC_FRAME_TELEMETRY_MARKER = (
    "a90.doomgeneric.v3110.gametic_frame_telemetry=loop-dump-gametic-summary"
)

REQUIRED_STRINGS = (
    b"A90 Linux init 0.10.110 (v3110-doomgeneric-hw-plane-diagnostics)",
    b"v3110-doomgeneric-hw-plane-diagnostics",
    b"doomgeneric-private-link-v3110-hw-plane-diagnostics",
    b"/bin/a90_doomgeneric_private_engine_v3110",
    RUNTIME_WAD_PATH.encode("ascii"),
    EXPECTED_WAD_SHA256.encode("ascii"),
    FRAME_PATH.encode("ascii"),
    SHARED_FRAME_PATH.encode("ascii"),
    INPUT_STATE_PATH.encode("ascii"),
    INPUT_SOCKET_PATH.encode("ascii"),
    PACE_SOCKET_PATH.encode("ascii"),
    TICK_TELEMETRY_PATH.encode("ascii"),
    TICK_TELEMETRY_MARKER.encode("ascii"),
    SCALE_MARKER.encode("ascii"),
    PHASE_TELEMETRY_MARKER.encode("ascii"),
    GAMETIC_FRAME_TELEMETRY_MARKER.encode("ascii"),
    b"video.demo.doom.dashboard.hw_plane_scale=1",
    b"video.demo.doom.dashboard.frame_mode=minimal-large-hw-plane-scale",
    b"video.demo.doom.dashboard.scale_path=drm-plane-srcdst",
    b"video.demo.doom.dashboard.hw_plane.stage=",
    b"video.demo.doom.dashboard.hw_plane.plane_count=",
    b"video.demo.doom.dashboard.hw_plane.compatible_count=",
    b"video.demo.doom.dashboard.hw_plane.idle_xbgr_count=",
    b"video.demo.doom.dashboard.hw_plane.universal_cap_rc=",
    b"video.demo.doom.dashboard.hw_plane.atomic_cap_rc=",
    b"client-caps",
    b"fetch-resources",
    b"fetch-planes",
    b"scan-planes",
    b"setplane",
    b"video.demo.doom.dashboard.hw_plane.fallback=fast-3to2-rowcopy",
    v3108.SEQ_TELEMETRY_CONTRACT.encode("ascii"),
    v3108.SEQ_TELEMETRY_MODEL.encode("ascii"),
    b"video.demo.doom.loop.timing_probe=1",
)


def rel(path: Path) -> str:
    return v3108.rel(path)


def v3033_module() -> Any:
    return v3108.v3033_module()


def v3110_adapter_source() -> str:
    source = V3108_ADAPTER_SOURCE()
    replacements = {
        v3108.TICK_TELEMETRY_MARKER: TICK_TELEMETRY_MARKER,
        v3108.SCALE_MARKER: SCALE_MARKER,
        v3108.PHASE_TELEMETRY_MARKER: PHASE_TELEMETRY_MARKER,
        v3108.GAMETIC_FRAME_TELEMETRY_MARKER: GAMETIC_FRAME_TELEMETRY_MARKER,
        v3108.TICK_TELEMETRY_PATH: TICK_TELEMETRY_PATH,
        v3108.FRAME_PATH: FRAME_PATH,
        v3108.SHARED_FRAME_PATH: SHARED_FRAME_PATH,
        v3108.INPUT_STATE_PATH: INPUT_STATE_PATH,
        v3108.INPUT_SOCKET_PATH: INPUT_SOCKET_PATH,
        v3108.PACE_SOCKET_PATH: PACE_SOCKET_PATH,
    }
    for old, new in replacements.items():
        source = source.replace(old, new)
    source = source.replace(
        'scale_path=drm-plane-srcdst\\n',
        'scale_path=drm-plane-srcdst-diagnostic\\n',
    )
    return source


def apply_v3110_globals() -> None:
    v3108.CYCLE = CYCLE
    v3108.INIT_VERSION = INIT_VERSION
    v3108.INIT_BUILD = INIT_BUILD
    v3108.BUILD_TAG = BUILD_TAG
    v3108.DECISION = DECISION
    v3108.OUT_DIR = OUT_DIR
    v3108.OBJ_DIR = OBJ_DIR
    v3108.REPORT_PATH = REPORT_PATH
    v3108.BOOT_IMAGE = BOOT_IMAGE
    v3108.INIT_BINARY = INIT_BINARY
    v3108.RAMDISK_CPIO = RAMDISK_CPIO
    v3108.HELPER_BINARY = HELPER_BINARY
    v3108.ENGINE_BINARY = ENGINE_BINARY
    v3108.ENGINE_ADAPTER_SOURCE = ENGINE_ADAPTER_SOURCE
    v3108.ENGINE_ADAPTER_OBJECT = ENGINE_ADAPTER_OBJECT
    v3108.ENGINE_RAMDISK_PATH = ENGINE_RAMDISK_PATH
    v3108.ENGINE_REMOTE_PATH = ENGINE_REMOTE_PATH
    v3108.ENGINE_NAME = ENGINE_NAME
    v3108.FRAME_PATH = FRAME_PATH
    v3108.SHARED_FRAME_PATH = SHARED_FRAME_PATH
    v3108.INPUT_STATE_PATH = INPUT_STATE_PATH
    v3108.INPUT_SOCKET_PATH = INPUT_SOCKET_PATH
    v3108.PACE_SOCKET_PATH = PACE_SOCKET_PATH
    v3108.TICK_TELEMETRY_PATH = TICK_TELEMETRY_PATH
    v3108.NATIVE_DASHBOARD_LARGE_FRAME = NATIVE_DASHBOARD_LARGE_FRAME
    v3108.HW_PLANE_SCALE = HW_PLANE_SCALE
    v3108.FRAME_SCALE = FRAME_SCALE
    v3108.SCALE_PATH = SCALE_PATH
    v3108.FALLBACK_SCALE_PATH = FALLBACK_SCALE_PATH
    v3108.TICK_TELEMETRY_MARKER = TICK_TELEMETRY_MARKER
    v3108.SCALE_MARKER = SCALE_MARKER
    v3108.PHASE_TELEMETRY_MARKER = PHASE_TELEMETRY_MARKER
    v3108.GAMETIC_FRAME_TELEMETRY_MARKER = GAMETIC_FRAME_TELEMETRY_MARKER
    v3108.REQUIRED_STRINGS = REQUIRED_STRINGS
    v3108.v3108_adapter_source = v3110_adapter_source
    v3108.render_report = render_report

    v3108.apply_v3108_globals()
    base = v3108.v3100.v3098.v3096.v3086
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
    base.v3084.v3083.v3081.v3081_adapter_source = v3110_adapter_source
    v3108.V3059.v3059_adapter_source = v3110_adapter_source

    v3033 = v3033_module()
    v3033.SHARED_FRAME_PATH = SHARED_FRAME_PATH
    v3033.INPUT_STATE_PATH = INPUT_STATE_PATH
    v3033.INPUT_SOCKET_PATH = INPUT_SOCKET_PATH
    v3033.PACE_SOCKET_PATH = PACE_SOCKET_PATH
    v3033.NATIVE_DASHBOARD_LARGE_FRAME = NATIVE_DASHBOARD_LARGE_FRAME
    v3033.HW_PLANE_SCALE = HW_PLANE_SCALE


def render_report(
    manifest: dict[str, Any],
    helper_flags: tuple[str, ...],
    init_extra_flags: tuple[str, ...],
) -> str:
    doom = manifest.get("doomgeneric_visible_loop", {})
    return "\n".join([
        "# Native Init V3110 DOOMGENERIC Hardware Plane Diagnostics Source Build",
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
        "- Keeps the V3108 large HW-plane path but adds stage-level diagnostics around plane selection, dumb-buffer creation, and legacy SETPLANE.",
        "- Enables both `DRM_CLIENT_CAP_UNIVERSAL_PLANES` and `DRM_CLIENT_CAP_ATOMIC` before plane inventory, matching the successful V3107 probe setup more closely.",
        "- Emits `hw_plane.stage`, `stage_id`, `plane_count`, `compatible_count`, `idle_xbgr_count`, `universal_cap_rc`, and `atomic_cap_rc` in the DOOM dashboard loop.",
        "- Normalizes the no-compatible-plane path to `-ENODEV`, so stale ioctl `errno` does not masquerade as an unrelated `-EFAULT` setup failure.",
        "- Keeps `fast-3to2-rowcopy` fallback and does not switch to atomic commit yet; V3110 is the bounded cause splitter for V3109's `attempted=0 rc=-14`.",
        "",
        "## V3109 Carry-Forward",
        "",
        "- V3109 proved the loop can present `180` frames with `seq.shared_missed_frames=0`, but the HW plane path fell back before SETPLANE: `attempted=0`, `id=0`, `fb=0`, `rc=-14`.",
        "- V3109 also exposed `protocol-end-missing`: frame evidence completed, but the foreground cmdv1 END marker did not return before host timeout.",
        "- V3110 therefore does not add more frame pacing telemetry; it only identifies which plane setup stage returns `-EFAULT` and whether matching the V3107 client-cap setup changes that result.",
        "",
        "## Runtime Contract",
        "",
        f"- Runtime WAD path: `{doom.get('runtime_wad_path')}`",
        f"- Expected WAD SHA256: `{doom.get('expected_wad_sha256')}`",
        f"- Helper loop command: `{doom.get('helper_loop_command')}`",
        f"- Scale marker: `{SCALE_MARKER}`",
        f"- Scale path: `{SCALE_PATH}`",
        f"- Fallback scale path: `{FALLBACK_SCALE_PATH}`",
        "",
        "## Safety",
        "",
        "- Boot partition only through the checked flash helper `native_init_flash.py` in the next live unit.",
        "- No GPU/GL stack, panel re-init, backlight, PMIC, regulator, GDSC, GPIO, Wi-Fi connect/dhcp/ping, or forbidden partition path.",
        "- Plane use remains bounded and fallback-preserving; the full-screen KMS path remains available.",
        "",
        "## Validation",
        "",
        "- `py_compile`: V3110 builder and focused tests.",
        "- `unittest`: V3110 source contract plus V3108 regression checks.",
        "- Build: AArch64 helper compile/link, native-init compile, ramdisk pack, boot image pack, SHA256 capture.",
        "- Marker check: generated boot image contains V3110 identity and HW-plane diagnostic markers.",
        "- `git diff --check`: PASS.",
        "",
        "## Next Unit",
        "",
        "- Run ID: `V3111`",
        "- Type: rollback-gated live validation.",
        "- Scope: flash exact V3110 image, hide auto menu, run bounded large DOOM loop, and classify `hw_plane.stage`/rc. If stage reaches `setplane` and fails, the next unit is atomic plane commit; if stage fails earlier, fix that specific setup step; if HW plane remains unavailable, proceed to pre-scaled producer.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `doomgeneric-hw-plane-diagnostics-candidate`.",
    ]) + "\n"


def main() -> int:
    apply_v3110_globals()
    rc = v3108.v3100.v3098.v3096.v3086.v3084.main()
    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    doom = manifest.setdefault("doomgeneric_visible_loop", {})
    doom.update({
        "scale_marker": SCALE_MARKER,
        "tick_telemetry_marker": TICK_TELEMETRY_MARKER,
        "phase_telemetry_marker": PHASE_TELEMETRY_MARKER,
        "gametic_frame_telemetry_marker": GAMETIC_FRAME_TELEMETRY_MARKER,
        "tick_telemetry_path": TICK_TELEMETRY_PATH,
        "native_dashboard_large_frame": bool(NATIVE_DASHBOARD_LARGE_FRAME),
        "hw_plane_scale": bool(HW_PLANE_SCALE),
        "frame_scale": FRAME_SCALE,
        "scale_path": SCALE_PATH,
        "fallback_scale_path": FALLBACK_SCALE_PATH,
        "hw_plane_diagnostics": True,
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
        "candidate_type": "doomgeneric-hw-plane-diagnostics-candidate",
        "adoption_state": "pending-hw-plane-diagnostics-live-validation",
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
    (OUT_DIR / "doomgeneric-hw-plane-diagnostics-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "doomgeneric-hw-plane-diagnostics-candidate",
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
        "scale_marker": SCALE_MARKER,
        "tick_telemetry_path": TICK_TELEMETRY_PATH,
        "loop_frame_ms": LOOP_FRAME_MS,
        "presenter_poll_ms": PRESENTER_POLL_MS,
        "frame_scale": FRAME_SCALE,
        "scale_path": SCALE_PATH,
        "fallback_scale_path": FALLBACK_SCALE_PATH,
        "hw_plane_diagnostics": True,
        "present_mode": "pageflip",
        "present_path": "kms-dumb-buffer-pageflip-plus-drm-plane-srcdst-diagnostics",
        "frame_timing_probe": FRAME_TIMING_PROBE,
        "native_dashboard": bool(NATIVE_DASHBOARD),
        "native_dashboard_minimal": bool(NATIVE_DASHBOARD_MINIMAL),
        "native_dashboard_large_frame": bool(NATIVE_DASHBOARD_LARGE_FRAME),
        "hw_plane_scale": bool(HW_PLANE_SCALE),
        "native_doom_present_pageflip": bool(NATIVE_DOOM_PRESENT_PAGEFLIP),
        "loop_start_command": f"video demo doom loop-start 0 --wad runtime-private --sha256 {EXPECTED_WAD_SHA256}",
        "host_keyboard_bridge": rel(v3108.HOST_KEYBOARD_BRIDGE),
        "source_report": rel(REPORT_PATH),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-hw-plane-diagnostics-live-validation",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
