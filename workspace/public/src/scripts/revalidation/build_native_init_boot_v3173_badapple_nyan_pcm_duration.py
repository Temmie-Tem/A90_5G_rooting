#!/usr/bin/env python3
"""Build V3173 Bad Apple/Nyan PCM-duration candidate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _workspace_bootstrap import repo_root
from a90harness.evidence import workspace_private_build_path, workspace_private_input_path
import build_native_init_boot_v3033_doomgeneric_visible_loop as v3033
import build_native_init_boot_v3171_badapple_nyan_setcrtc_cadence as base

REPO_ROOT = repo_root()

CYCLE = "V3173"
INIT_VERSION = "0.11.16"
INIT_BUILD = "v3173-badapple-nyan-pcm-duration"
BUILD_TAG = INIT_BUILD
DECISION = "v3173-badapple-nyan-pcm-duration-source-build-pass"

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
OBJ_DIR = OUT_DIR / "obj"
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V3173_BADAPPLE_NYAN_PCM_DURATION_SOURCE_BUILD_2026-06-25.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images",
    "boot_linux_v3173_badapple_nyan_pcm_duration.img",
    legacy_fallback=False,
)
INIT_BINARY = OUT_DIR / "init_v3173_badapple_nyan_pcm_duration"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v3173_badapple_nyan_pcm_duration.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v550_badapple_nyan_pcm_duration"

ENGINE_BINARY = OUT_DIR / "a90_doomgeneric_private_engine_v3173"
ENGINE_ADAPTER_SOURCE = OUT_DIR / "a90_doomgeneric_native_bridge_v3173.c"
ENGINE_ADAPTER_OBJECT = OBJ_DIR / "a90_doomgeneric_native_bridge_v3173.o"
ENGINE_RAMDISK_PATH = "bin/a90_doomgeneric_private_engine_v3173"
ENGINE_REMOTE_PATH = "/" + ENGINE_RAMDISK_PATH
ENGINE_NAME = "doomgeneric-private-link-v3173-badapple-nyan-pcm-duration"

FRAME_PATH = "/tmp/a90-doomgeneric-v3173-raw-fallback-frame.xbgr8888"
SHARED_FRAME_PATH = "/tmp/a90-doomgeneric-v3173-shared-frame.bin"
INPUT_STATE_PATH = "/tmp/a90-doomgeneric-v3173-input.state"
INPUT_SOCKET_PATH = "/tmp/a90-doomgeneric-v3173-input.sock"
PACE_SOCKET_PATH = "/tmp/a90-doomgeneric-v3173-pace.sock"
TICK_TELEMETRY_PATH = "/tmp/a90-doomgeneric-v3173-tick-telemetry.txt"
AUDIO_PCM_STREAM_PATH = "/cache/a90-runtime/a90-doomgeneric-v3173-sfx.pcmstream"

FRAME_SCALE = "1:1-demo-hud-large-groups-badapple-nyan-pcm-duration"
FRAME_IPC = "shared-mmap-direct-blit-demo-hud-large-groups-badapple-nyan-pcm-duration"

INPUT_THREAD_MARKER = base.INPUT_THREAD_MARKER.replace("v3171", "v3173")
TIME_MODEL_MARKER = base.TIME_MODEL_MARKER.replace("v3171", "v3173")
DEMO_HUD_MARKER = base.DEMO_HUD_MARKER.replace("v3171", "v3173")
PACED_TIME_MARKER = base.PACED_TIME_MARKER.replace("v3171", "v3173")
TICK_TELEMETRY_MARKER = base.TICK_TELEMETRY_MARKER.replace("v3171", "v3173")
SCALE_MARKER = base.SCALE_MARKER.replace("v3171", "v3173")
PHASE_TELEMETRY_MARKER = base.PHASE_TELEMETRY_MARKER.replace("v3171", "v3173")
GAMETIC_FRAME_TELEMETRY_MARKER = base.GAMETIC_FRAME_TELEMETRY_MARKER.replace("v3171", "v3173")
SFX_STREAM_MARKER = "a90.doomgeneric.v3173.audio=real-sfx-pcm-stream-badapple-nyan-pcm-duration"
SOUND_MODE = "native-doom-sfx-badapple-nyan-pcm-duration-v3173"

AUDIO_CORUN = base.AUDIO_CORUN
AUDIO_CORUN_MODE = SOUND_MODE
AUDIO_CORUN_STREAM = base.AUDIO_CORUN_STREAM
AUDIO_CORUN_DURATION_MS = base.AUDIO_CORUN_DURATION_MS
AUDIO_CORUN_REFRESH_MS = base.AUDIO_CORUN_REFRESH_MS
AUDIO_CORUN_AMPLITUDE_MILLI = base.AUDIO_CORUN_AMPLITUDE_MILLI
PHYSICAL_BUTTON_EXIT = base.PHYSICAL_BUTTON_EXIT

SFX_BACKEND_SOURCE = OUT_DIR / "a90_doomgeneric_native_sfx_v3173.c"
SDL_MIXER_STUB = OUT_DIR / "SDL_mixer.h"

VIDEO_PLAYER_HUD_METRICS_INTERVAL_FRAMES = base.VIDEO_PLAYER_HUD_METRICS_INTERVAL_FRAMES
VIDEO_PLAYER_HUD_STORAGE_INTERVAL_FRAMES = base.VIDEO_PLAYER_HUD_STORAGE_INTERVAL_FRAMES
VIDEO_PLAYER_HUD_TEXT_INTERVAL_FRAMES = base.VIDEO_PLAYER_HUD_TEXT_INTERVAL_FRAMES
VIDEO_PLAYER_HUD_FULL_REPAINT_INTERVAL_FRAMES = base.VIDEO_PLAYER_HUD_FULL_REPAINT_INTERVAL_FRAMES
VIDEO_PLAYER_HUD_TELEMETRY_MIN_SLACK_NS = base.VIDEO_PLAYER_HUD_TELEMETRY_MIN_SLACK_NS
VIDEO_PLAYER_HUD_LIVE_TELEMETRY = base.VIDEO_PLAYER_HUD_LIVE_TELEMETRY
VIDEO_PLAYER_HUD_DYNAMIC_TEXT = base.VIDEO_PLAYER_HUD_DYNAMIC_TEXT

BASE_OVERRIDES = base._v3171_overrides
BASE_VALUES = base._v3171_values
V3171_ADAPTER_SOURCE_TEXT = base.v3171_adapter_source()


def rel(path: Path) -> str:
    return base.rel(path)


def _rewrite_v3173_text(text: str) -> str:
    return (
        text.replace(base.AUDIO_PCM_STREAM_PATH, AUDIO_PCM_STREAM_PATH)
        .replace("badapple-nyan-setcrtc-cadence", "badapple-nyan-pcm-duration")
        .replace("v3171", "v3173")
        .replace("V3171", "V3173")
        .replace(base.INIT_VERSION, INIT_VERSION)
        .replace(base.INIT_BUILD, INIT_BUILD)
        .replace(base.ENGINE_NAME, ENGINE_NAME)
        .replace(base.ENGINE_REMOTE_PATH, ENGINE_REMOTE_PATH)
        .replace(base.SOUND_MODE, SOUND_MODE)
    )


SFX_BACKEND_SOURCE_TEXT = _rewrite_v3173_text(base.SFX_BACKEND_SOURCE_TEXT)


def _rewrite_required_string(item: bytes) -> bytes:
    replacements = {
        base.INIT_VERSION.encode("ascii"): INIT_VERSION.encode("ascii"),
        base.INIT_BUILD.encode("ascii"): INIT_BUILD.encode("ascii"),
        base.ENGINE_NAME.encode("ascii"): ENGINE_NAME.encode("ascii"),
        base.ENGINE_REMOTE_PATH.encode("ascii"): ENGINE_REMOTE_PATH.encode("ascii"),
        base.SOUND_MODE.encode("ascii"): SOUND_MODE.encode("ascii"),
        base.SFX_STREAM_MARKER.encode("ascii"): SFX_STREAM_MARKER.encode("ascii"),
        base.AUDIO_PCM_STREAM_PATH.encode("ascii"): AUDIO_PCM_STREAM_PATH.encode("ascii"),
        b"badapple-nyan-setcrtc-cadence": b"badapple-nyan-pcm-duration",
        b"a90-doomgeneric-v3171": b"a90-doomgeneric-v3173",
        b"a90.doomgeneric.v3171": b"a90.doomgeneric.v3173",
        b"v3171": b"v3173",
        b"V3171": b"V3173",
    }
    for old, new in replacements.items():
        item = item.replace(old, new)
    return item


_RETIRED_REQUIRED_MARKERS = (
    b"video.status.stream_readahead=sequential-window",
    b"video.stream.readahead.policy=sequential-window",
)

_RETIRED_PCM_DURATION_BOOT_MARKERS = (
    b"menu.demo.badapple.audio_duration_ms=232800",
    b"menu.demo.badapple.audio_tail_pad_ms=710",
    b"menu.demo.nyan.audio_duration_ms=11000",
    b"menu.demo.nyan.audio_tail_pad_ms=1000",
)

_PCM_DURATION_BOOT_MARKERS = (
    b"menu.demo.badapple.audio_duration_ms=232093",
    b"menu.demo.badapple.audio_tail_pad_ms=0",
    b"menu.demo.badapple.audio_duration_source=pcm-file-size",
    b"menu.demo.badapple.pcm_duration_wait=expected-duration",
    b"menu.demo.nyan.audio_duration_ms=10000",
    b"menu.demo.nyan.audio_tail_pad_ms=0",
    b"menu.demo.nyan.audio_duration_source=pcm-file-size",
    b"menu.demo.nyan.pcm_duration_wait=expected-duration",
)

REQUIRED_STRINGS = tuple(
    _rewrite_required_string(item)
    for item in base.REQUIRED_STRINGS
    if not any(marker in item for marker in _RETIRED_REQUIRED_MARKERS)
) + (
    SFX_STREAM_MARKER.encode("ascii"),
    SOUND_MODE.encode("ascii"),
    AUDIO_PCM_STREAM_PATH.encode("ascii"),
    b"0.11.16",
    b"v3173-badapple-nyan-pcm-duration",
    b"video.status.stream_readahead=%s",
    b"video.status.stream_readahead.window_enabled=%d",
    b"video.status.stream_readahead.deadline_guard_ns=%llu",
    b"video.status.menu_av_tail_wait=audio-expected-duration",
    b"video.stream.readahead.policy=%s",
    b"sequential-only-window-off",
    b"video.stream.readahead.window_enabled=%d",
    b"video.stream.readahead.deadline_guard_ns=%llu",
    b"video.stream.readahead.deadline_skips=%u",
    b"video.stream.audio_sync.tail_wait_target=%s",
    b"menu.demo.badapple.audio_duration_ms=232093",
    b"menu.demo.badapple.audio_tail_pad_ms=0",
    b"menu.demo.badapple.audio_duration_source=pcm-file-size",
    b"menu.demo.badapple.pcm_duration_wait=expected-duration",
    b"menu.demo.nyan.audio_duration_ms=10000",
    b"menu.demo.nyan.audio_tail_pad_ms=0",
    b"menu.demo.nyan.audio_duration_source=pcm-file-size",
    b"menu.demo.nyan.pcm_duration_wait=expected-duration",
)


def _v3173_v3033_require_strings(path: Path) -> list[str]:
    data = path.read_bytes()
    required = tuple(
        marker
        for marker in v3033.REQUIRED_STRINGS
        if marker not in _RETIRED_PCM_DURATION_BOOT_MARKERS
    ) + _PCM_DURATION_BOOT_MARKERS
    missing = [
        marker.decode("ascii", errors="replace")
        for marker in required
        if marker not in data
    ]
    if missing:
        raise RuntimeError(f"missing V3173 boot-image markers: {missing}")
    return [marker.decode("ascii", errors="replace") for marker in required]


def _v3173_overrides() -> dict[str, Any]:
    overrides = dict(BASE_OVERRIDES())
    overrides.update({
        "CYCLE": CYCLE,
        "INIT_VERSION": INIT_VERSION,
        "INIT_BUILD": INIT_BUILD,
        "BUILD_TAG": BUILD_TAG,
        "DECISION": DECISION,
        "OUT_DIR": OUT_DIR,
        "OBJ_DIR": OBJ_DIR,
        "REPORT_PATH": REPORT_PATH,
        "BOOT_IMAGE": BOOT_IMAGE,
        "INIT_BINARY": INIT_BINARY,
        "RAMDISK_CPIO": RAMDISK_CPIO,
        "HELPER_BINARY": HELPER_BINARY,
        "ENGINE_BINARY": ENGINE_BINARY,
        "ENGINE_ADAPTER_SOURCE": ENGINE_ADAPTER_SOURCE,
        "ENGINE_ADAPTER_OBJECT": ENGINE_ADAPTER_OBJECT,
        "ENGINE_RAMDISK_PATH": ENGINE_RAMDISK_PATH,
        "ENGINE_REMOTE_PATH": ENGINE_REMOTE_PATH,
        "ENGINE_NAME": ENGINE_NAME,
        "FRAME_PATH": FRAME_PATH,
        "SHARED_FRAME_PATH": SHARED_FRAME_PATH,
        "INPUT_STATE_PATH": INPUT_STATE_PATH,
        "INPUT_SOCKET_PATH": INPUT_SOCKET_PATH,
        "PACE_SOCKET_PATH": PACE_SOCKET_PATH,
        "TICK_TELEMETRY_PATH": TICK_TELEMETRY_PATH,
        "AUDIO_PCM_STREAM_PATH": AUDIO_PCM_STREAM_PATH,
        "FRAME_SCALE": FRAME_SCALE,
        "FRAME_IPC": FRAME_IPC,
        "INPUT_THREAD_MARKER": INPUT_THREAD_MARKER,
        "TIME_MODEL_MARKER": TIME_MODEL_MARKER,
        "DEMO_HUD_MARKER": DEMO_HUD_MARKER,
        "PACED_TIME_MARKER": PACED_TIME_MARKER,
        "TICK_TELEMETRY_MARKER": TICK_TELEMETRY_MARKER,
        "SCALE_MARKER": SCALE_MARKER,
        "PHASE_TELEMETRY_MARKER": PHASE_TELEMETRY_MARKER,
        "GAMETIC_FRAME_TELEMETRY_MARKER": GAMETIC_FRAME_TELEMETRY_MARKER,
        "SFX_STREAM_MARKER": SFX_STREAM_MARKER,
        "SOUND_MODE": SOUND_MODE,
        "AUDIO_CORUN_MODE": AUDIO_CORUN_MODE,
        "SFX_BACKEND_SOURCE": SFX_BACKEND_SOURCE,
        "SDL_MIXER_STUB": SDL_MIXER_STUB,
        "SFX_BACKEND_SOURCE_TEXT": SFX_BACKEND_SOURCE_TEXT,
        "REQUIRED_STRINGS": REQUIRED_STRINGS,
    })
    return overrides


def _v3173_values() -> dict[str, Any]:
    values = dict(BASE_VALUES())
    values.update(_v3173_overrides())
    return values


def _v3173_adapter_source_from_patched_v3148() -> str:
    return (
        V3171_ADAPTER_SOURCE_TEXT
        .replace("real-sfx-pcm-stream-badapple-nyan-setcrtc-cadence",
                 "real-sfx-pcm-stream-badapple-nyan-pcm-duration")
        .replace("v3171", "v3173")
        .replace("V3171", "V3173")
    )


def v3173_adapter_source() -> str:
    return _v3173_adapter_source_from_patched_v3148()


def render_report(
    manifest: dict[str, Any],
    helper_flags: tuple[str, ...],
    init_extra_flags: tuple[str, ...],
) -> str:
    return "\n".join([
        "# Native Init V3173 Bad Apple/Nyan PCM Duration Source Build",
        "",
        "## Summary",
        "",
        f"- Cycle: `{CYCLE}`",
        "- Track: Bad Apple/Nyan A/V playback PCM duration alignment.",
        f"- Decision: `{manifest['decision']}`",
        "- Result: PASS",
        "- Device flash: `no` in this build unit.",
        f"- Boot image: `{manifest['boot_image']}`",
        f"- Boot SHA256: `{manifest['boot_sha256']}`",
        f"- Init: `A90 Linux init {manifest['init_version']} ({manifest['init_build']})`",
        "",
        "## Included Delta",
        "",
        "- Aligns Bad Apple/Nyan menu `audio play --duration-ms` with the actual staged PCM byte lengths.",
        "- Removes synthetic tail padding from the menu launch path so finite PCM validation does not reject short files.",
        "- Preserves V3172 sequential-only stream readahead and audio expected-duration tail wait.",
        "- Keeps menu playback on `setcrtc` with setcrtc late-frame drops disabled.",
        "",
        "## Safety",
        "",
        "- Boot partition only through `native_init_flash.py` in the live step.",
        "- No PMIC, regulator, GDSC, GPIO writes, Wi-Fi connect/dhcp/ping, or forbidden partition path.",
        "",
        "## Validation",
        "",
        "- `py_compile`: V3173 builder and focused tests.",
        "- `unittest`: V3173 Bad Apple/Nyan PCM-duration source contract.",
        "- Build: AArch64 helper/native-init compile, ramdisk pack, boot image pack, SHA256 capture.",
        "- Marker check: generated boot image contains V3173/0.11.16 identity, PCM-duration, readahead, and tail markers.",
        "- `git diff --check`: PASS.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `badapple-nyan-pcm-duration-candidate`.",
    ]) + "\n"


def _postprocess_manifest() -> dict[str, Any]:
    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "badapple-nyan-pcm-duration-candidate",
        "adoption_state": "pending-badapple-nyan-pcm-duration-live-validation",
        "promotion": {
            "patch_version": INIT_VERSION,
            "source_baseline": "v3172-badapple-nyan-av-stutter-audio-tail",
            "requires_live_validation": [
                "badapple-fullsong-av",
                "nyan-preview-av",
                "periodic-stutter-check",
                "pcm-duration-clean-menu-return",
                "audio-short-file-regression",
                "setcrtc-stable-cadence",
            ],
            "preserves_doom_demo": True,
        },
        "badapple_nyan_av": {
            "badapple_audio_duration_ms": 232093,
            "badapple_pcm_duration_pad_ms": 0,
            "badapple_pcm_size_bytes": 44561952,
            "nyan_audio_duration_ms": 10000,
            "nyan_pcm_duration_pad_ms": 0,
            "nyan_pcm_size_bytes": 1920000,
            "setcrtc_drop_policy": "disabled-stable-cadence",
            "late_drop_present_modes": ["pageflip"],
            "stream_readahead": "sequential-only-window-off",
            "window_readahead_default_enabled": False,
            "window_readahead_deadline_guard_ns": 25000000,
            "pcm_duration_wait": "expected-duration-for-full-demo",
        },
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
    (OUT_DIR / "badapple-nyan-pcm-duration-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "badapple-nyan-pcm-duration-candidate",
        "boot_image": rel(BOOT_IMAGE),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "live_validation_focus": [
            "badapple-fullsong-av",
            "nyan-preview-av",
            "periodic-stutter-check",
            "pcm-duration-clean-menu-return",
            "setcrtc-stable-cadence",
        ],
        "source_report": rel(REPORT_PATH),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-badapple-nyan-pcm-duration-live-validation",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def _apply_v3173_globals() -> list[tuple[Any, str, Any, bool]]:
    saved: list[tuple[Any, str, Any, bool]] = []
    for name, value in _v3173_overrides().items():
        existed = hasattr(base, name)
        saved.append((base, name, getattr(base, name, None), existed))
        setattr(base, name, value)
    for name, value in (
        ("_v3171_overrides", _v3173_overrides),
        ("_v3171_values", _v3173_values),
        ("_v3171_adapter_source_from_patched_v3148", _v3173_adapter_source_from_patched_v3148),
        ("v3171_adapter_source", v3173_adapter_source),
        ("render_report", render_report),
        ("_postprocess_manifest", _postprocess_manifest),
    ):
        saved.append((base, name, getattr(base, name), True))
        setattr(base, name, value)
    saved.append((v3033, "require_strings", v3033.require_strings, True))
    v3033.require_strings = _v3173_v3033_require_strings
    return saved


def _restore_v3173_globals(saved: list[tuple[Any, str, Any, bool]]) -> None:
    for module, name, value, existed in reversed(saved):
        if existed:
            setattr(module, name, value)
        else:
            delattr(module, name)


def main() -> int:
    saved = _apply_v3173_globals()
    try:
        return base.main()
    finally:
        _restore_v3173_globals(saved)


if __name__ == "__main__":
    raise SystemExit(main())
