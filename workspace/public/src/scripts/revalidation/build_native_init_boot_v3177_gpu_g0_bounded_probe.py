#!/usr/bin/env python3
"""Build V3177 GPU G0 bounded KGSL-open probe candidate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _workspace_bootstrap import repo_root
from a90harness.evidence import workspace_private_build_path, workspace_private_input_path
import build_native_init_boot_v3175_badapple_nyan_silence_tail as base

REPO_ROOT = repo_root()

CYCLE = "V3177"
INIT_VERSION = "0.11.19"
INIT_BUILD = "v3177-gpu-g0-bounded-probe"
BUILD_TAG = INIT_BUILD
DECISION = "v3177-gpu-g0-bounded-probe-source-build-pass"

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
OBJ_DIR = OUT_DIR / "obj"
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V3177_GPU_G0_BOUNDED_PROBE_SOURCE_BUILD_2026-06-25.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images",
    "boot_linux_v3177_gpu_g0_bounded_probe.img",
    legacy_fallback=False,
)
INIT_BINARY = OUT_DIR / "init_v3177_gpu_g0_bounded_probe"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v3177_gpu_g0_bounded_probe.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v552_gpu_g0_bounded_probe"

ENGINE_BINARY = OUT_DIR / "a90_doomgeneric_private_engine_v3177"
ENGINE_ADAPTER_SOURCE = OUT_DIR / "a90_doomgeneric_native_bridge_v3177.c"
ENGINE_ADAPTER_OBJECT = OBJ_DIR / "a90_doomgeneric_native_bridge_v3177.o"
ENGINE_RAMDISK_PATH = "bin/a90_doomgeneric_private_engine_v3177"
ENGINE_REMOTE_PATH = "/" + ENGINE_RAMDISK_PATH
ENGINE_NAME = "doomgeneric-private-link-v3177-gpu-g0-bounded-probe"

FRAME_PATH = "/tmp/a90-doomgeneric-v3177-raw-fallback-frame.xbgr8888"
SHARED_FRAME_PATH = "/tmp/a90-doomgeneric-v3177-shared-frame.bin"
INPUT_STATE_PATH = "/tmp/a90-doomgeneric-v3177-input.state"
INPUT_SOCKET_PATH = "/tmp/a90-doomgeneric-v3177-input.sock"
PACE_SOCKET_PATH = "/tmp/a90-doomgeneric-v3177-pace.sock"
TICK_TELEMETRY_PATH = "/tmp/a90-doomgeneric-v3177-tick-telemetry.txt"
AUDIO_PCM_STREAM_PATH = "/cache/a90-runtime/a90-doomgeneric-v3177-sfx.pcmstream"

FRAME_SCALE = "1:1-demo-hud-large-groups-gpu-g0-bounded-probe"
FRAME_IPC = "shared-mmap-direct-blit-demo-hud-large-groups-gpu-g0-bounded-probe"

INPUT_THREAD_MARKER = base.INPUT_THREAD_MARKER.replace("v3175", "v3177")
TIME_MODEL_MARKER = base.TIME_MODEL_MARKER.replace("v3175", "v3177")
DEMO_HUD_MARKER = base.DEMO_HUD_MARKER.replace("v3175", "v3177")
PACED_TIME_MARKER = base.PACED_TIME_MARKER.replace("v3175", "v3177")
TICK_TELEMETRY_MARKER = base.TICK_TELEMETRY_MARKER.replace("v3175", "v3177")
SCALE_MARKER = base.SCALE_MARKER.replace("v3175", "v3177")
PHASE_TELEMETRY_MARKER = base.PHASE_TELEMETRY_MARKER.replace("v3175", "v3177")
GAMETIC_FRAME_TELEMETRY_MARKER = base.GAMETIC_FRAME_TELEMETRY_MARKER.replace("v3175", "v3177")
SFX_STREAM_MARKER = "a90.doomgeneric.v3177.audio=real-sfx-pcm-stream-gpu-g0-bounded-probe"
SOUND_MODE = "native-doom-sfx-gpu-g0-bounded-probe-v3177"

AUDIO_CORUN = base.AUDIO_CORUN
AUDIO_CORUN_MODE = SOUND_MODE
AUDIO_CORUN_STREAM = base.AUDIO_CORUN_STREAM
AUDIO_CORUN_DURATION_MS = base.AUDIO_CORUN_DURATION_MS
AUDIO_CORUN_REFRESH_MS = base.AUDIO_CORUN_REFRESH_MS
AUDIO_CORUN_AMPLITUDE_MILLI = base.AUDIO_CORUN_AMPLITUDE_MILLI
PHYSICAL_BUTTON_EXIT = base.PHYSICAL_BUTTON_EXIT

SFX_BACKEND_SOURCE = OUT_DIR / "a90_doomgeneric_native_sfx_v3177.c"
SDL_MIXER_STUB = OUT_DIR / "SDL_mixer.h"

VIDEO_PLAYER_HUD_METRICS_INTERVAL_FRAMES = base.VIDEO_PLAYER_HUD_METRICS_INTERVAL_FRAMES
VIDEO_PLAYER_HUD_STORAGE_INTERVAL_FRAMES = base.VIDEO_PLAYER_HUD_STORAGE_INTERVAL_FRAMES
VIDEO_PLAYER_HUD_TEXT_INTERVAL_FRAMES = base.VIDEO_PLAYER_HUD_TEXT_INTERVAL_FRAMES
VIDEO_PLAYER_HUD_FULL_REPAINT_INTERVAL_FRAMES = base.VIDEO_PLAYER_HUD_FULL_REPAINT_INTERVAL_FRAMES
VIDEO_PLAYER_HUD_TELEMETRY_MIN_SLACK_NS = base.VIDEO_PLAYER_HUD_TELEMETRY_MIN_SLACK_NS
VIDEO_PLAYER_HUD_LIVE_TELEMETRY = base.VIDEO_PLAYER_HUD_LIVE_TELEMETRY
VIDEO_PLAYER_HUD_DYNAMIC_TEXT = base.VIDEO_PLAYER_HUD_DYNAMIC_TEXT

BASE_OVERRIDES = base._v3175_overrides
BASE_VALUES = base._v3175_values
BASE_ADAPTER_SOURCE_TEXT = base.v3175_adapter_source()


def rel(path: Path) -> str:
    return base.rel(path)


def _rewrite_v3177_text(text: str) -> str:
    return (
        text.replace(base.AUDIO_PCM_STREAM_PATH, AUDIO_PCM_STREAM_PATH)
        .replace("badapple-nyan-silence-tail", "gpu-g0-bounded-probe")
        .replace("v3175", "v3177")
        .replace("V3175", "V3177")
        .replace(base.INIT_VERSION, INIT_VERSION)
        .replace(base.INIT_BUILD, INIT_BUILD)
        .replace(base.ENGINE_NAME, ENGINE_NAME)
        .replace(base.ENGINE_REMOTE_PATH, ENGINE_REMOTE_PATH)
        .replace(base.SOUND_MODE, SOUND_MODE)
    )


SFX_BACKEND_SOURCE_TEXT = _rewrite_v3177_text(base.SFX_BACKEND_SOURCE_TEXT)


def _rewrite_required_string(item: bytes) -> bytes:
    replacements = {
        base.INIT_VERSION.encode("ascii"): INIT_VERSION.encode("ascii"),
        base.INIT_BUILD.encode("ascii"): INIT_BUILD.encode("ascii"),
        base.ENGINE_NAME.encode("ascii"): ENGINE_NAME.encode("ascii"),
        base.ENGINE_REMOTE_PATH.encode("ascii"): ENGINE_REMOTE_PATH.encode("ascii"),
        base.SOUND_MODE.encode("ascii"): SOUND_MODE.encode("ascii"),
        base.SFX_STREAM_MARKER.encode("ascii"): SFX_STREAM_MARKER.encode("ascii"),
        base.AUDIO_PCM_STREAM_PATH.encode("ascii"): AUDIO_PCM_STREAM_PATH.encode("ascii"),
        b"badapple-nyan-silence-tail": b"gpu-g0-bounded-probe",
        b"a90-doomgeneric-v3175": b"a90-doomgeneric-v3177",
        b"a90.doomgeneric.v3175": b"a90.doomgeneric.v3177",
        b"v3175": b"v3177",
        b"V3175": b"V3177",
    }
    for old, new in replacements.items():
        item = item.replace(old, new)
    return item


GPU_G0_BOOT_MARKERS = (
    b"gpu [g0-status|g0-open-probe",
    b"gpu.g0.scope=kgsl-open-hang-diagnosis",
    b"gpu.g0.safety=read-only-status-plus-bounded-open-probe",
    b"gpu.g0.bright_line.no_power_writes=1",
    b"gpu.g0.bright_line.no_ioctl=1",
    b"gpu.g0.bright_line.no_mmap=1",
    b"gpu.g0.open.parent_enters_open=0",
    b"gpu.g0.open.ioctl_attempted=0",
    b"gpu.g0.open.mmap_attempted=0",
    b"gpu.g0.open.power_write_attempted=0",
    b"gpu.g0.open.result=%s",
    b"gpu.g0.open.error=timeout-too-large max_ms=%d",
    b"--materialize-devnode",
)


_RETIRED_BASE_MARKERS = (
    b"menu.demo.badapple.audio_duration_ms=232803",
    b"menu.demo.badapple.audio_tail_pad_ms=710",
    b"menu.demo.badapple.audio_duration_ms=232093",
    b"menu.demo.badapple.audio_tail_pad_ms=0",
    b"menu.demo.badapple.audio_duration_source=pcm-file-size",
    b"menu.demo.nyan.audio_duration_ms=10000",
    b"menu.demo.nyan.audio_tail_pad_ms=0",
    b"menu.demo.nyan.audio_duration_source=pcm-file-size",
)


REQUIRED_STRINGS = tuple(
    _rewrite_required_string(item)
    for item in base.REQUIRED_STRINGS
    if not any(marker in item for marker in _RETIRED_BASE_MARKERS)
) + (
    SFX_STREAM_MARKER.encode("ascii"),
    SOUND_MODE.encode("ascii"),
    AUDIO_PCM_STREAM_PATH.encode("ascii"),
    b"0.11.19",
    b"v3177-gpu-g0-bounded-probe",
) + GPU_G0_BOOT_MARKERS


def _v3177_require_strings(path: Path) -> list[str]:
    data = path.read_bytes()
    missing = [
        marker.decode("ascii", errors="replace")
        for marker in REQUIRED_STRINGS
        if marker not in data
    ]
    if missing:
        raise RuntimeError(f"missing V3177 boot-image markers: {missing}")
    return [marker.decode("ascii", errors="replace") for marker in REQUIRED_STRINGS]


def _v3177_overrides() -> dict[str, Any]:
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


def _v3177_values() -> dict[str, Any]:
    values = dict(BASE_VALUES())
    values.update(_v3177_overrides())
    return values


def _v3177_adapter_source_from_patched_v3148() -> str:
    return (
        BASE_ADAPTER_SOURCE_TEXT
        .replace("real-sfx-pcm-stream-badapple-nyan-silence-tail",
                 "real-sfx-pcm-stream-gpu-g0-bounded-probe")
        .replace("v3175", "v3177")
        .replace("V3175", "V3177")
    )


def v3177_adapter_source() -> str:
    return _v3177_adapter_source_from_patched_v3148()


def render_report(
    manifest: dict[str, Any],
    helper_flags: tuple[str, ...],
    init_extra_flags: tuple[str, ...],
) -> str:
    return "\n".join([
        "# Native Init V3177 GPU G0 Bounded Probe Source Build",
        "",
        "## Summary",
        "",
        f"- Cycle: `{CYCLE}`",
        "- Track: GPU G0 KGSL open-hang diagnosis.",
        f"- Decision: `{manifest['decision']}`",
        "- Result: PASS",
        "- Device flash: `no` in this build unit.",
        f"- Boot image: `{manifest['boot_image']}`",
        f"- Boot SHA256: `{manifest['boot_sha256']}`",
        f"- Init: `A90 Linux init {manifest['init_version']} ({manifest['init_build']})`",
        "",
        "## Included Delta",
        "",
        "- Builds the committed V3175 Bad Apple/Nyan silence-tail baseline with the GPU G0 bounded-probe command surface.",
        "- Keeps G0 limited to read-only status plus a forked-child, timeout-guarded `open(\"/dev/kgsl-3d0\")` probe.",
        "- The parent never enters the potentially hanging KGSL open and reports timeout/return metadata.",
        "- No KGSL ioctl, mmap, freedreno submit, G1 allocation, or power/GDSC/regulator/PMIC/GPIO write is included.",
        "- Optional `--materialize-devnode` only creates `/dev/kgsl-3d0` from the read-only sysfs major/minor.",
        "",
        "## Host-Side Diagnosis Link",
        "",
        "- Root-cause source audit: `docs/reports/NATIVE_INIT_V3176_GPU_G0_HOST_SOURCE_AUDIT_2026-06-25.md`.",
        "- Next live evidence point: `gpu g0-status` followed by one bounded `gpu g0-open-probe --timeout-ms 2000 --materialize-devnode` run.",
        "",
        "## Safety",
        "",
        "- Boot partition only through `native_init_flash.py` in any future live step.",
        "- No PMIC, regulator, GDSC, GPIO, power-rail writes, forbidden partition path, proprietary Adreno blob/EGL/Bionic path, or exploit work.",
        "- G0 open is strictly timeout-guarded; parent never enters the blocking KGSL open.",
        "",
        "## Validation",
        "",
        "- `py_compile`: V3177 builder and focused tests.",
        "- `unittest`: V3177 GPU G0 bounded-probe source contract.",
        "- Build: AArch64 helper/native-init compile, ramdisk pack, boot image pack, SHA256 capture.",
        "- Marker check: generated boot image contains V3177 identity and G0 bounded-probe markers.",
        "- `git diff --check`: PASS.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `gpu-g0-bounded-probe-candidate`.",
    ]) + "\n"


def _postprocess_manifest() -> dict[str, Any]:
    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "gpu-g0-bounded-probe-candidate",
        "adoption_state": "pending-gpu-g0-bounded-live-validation",
        "gpu_g0": {
            "source_baseline": "v3175-badapple-nyan-silence-tail",
            "host_source_audit": "docs/reports/NATIVE_INIT_V3176_GPU_G0_HOST_SOURCE_AUDIT_2026-06-25.md",
            "commands": [
                "gpu g0-status",
                "gpu g0-open-probe --timeout-ms 2000 --materialize-devnode",
            ],
            "open_probe_parent_enters_open": False,
            "open_probe_timeout_guard_ms_default": 2000,
            "open_probe_timeout_guard_ms_max": 10000,
            "forbidden_operations": [
                "kgsl-ioctl",
                "kgsl-mmap",
                "kgsl-gpuobj-alloc",
                "freedreno-submit",
                "GDSC-write",
                "regulator-write",
                "PMIC-write",
                "GPIO-write",
                "proprietary-adreno-blob",
                "exploit-dev",
            ],
            "next_live_validation": [
                "gpu-g0-status",
                "gpu-g0-open-probe-timeout-guard",
                "firmware-visibility-vs-gmu-power-domain-classification",
            ],
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
    (OUT_DIR / "gpu-g0-bounded-probe-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "gpu-g0-bounded-probe-candidate",
        "boot_image": rel(BOOT_IMAGE),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "live_validation_focus": [
            "gpu-g0-status",
            "gpu-g0-open-probe-timeout-guard",
            "no-ioctl-no-mmap-no-power-write",
        ],
        "source_report": rel(REPORT_PATH),
        "host_source_audit": "docs/reports/NATIVE_INIT_V3176_GPU_G0_HOST_SOURCE_AUDIT_2026-06-25.md",
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-gpu-g0-bounded-live-validation",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def _apply_v3177_globals() -> list[tuple[Any, str, Any, bool]]:
    saved: list[tuple[Any, str, Any, bool]] = []
    for name, value in _v3177_overrides().items():
        existed = hasattr(base, name)
        saved.append((base, name, getattr(base, name, None), existed))
        setattr(base, name, value)
    for name, value in (
        ("_v3175_overrides", _v3177_overrides),
        ("_v3175_values", _v3177_values),
        ("_v3175_adapter_source_from_patched_v3148", _v3177_adapter_source_from_patched_v3148),
        ("v3175_adapter_source", v3177_adapter_source),
        ("_v3175_v3033_require_strings", _v3177_require_strings),
        ("render_report", render_report),
        ("_postprocess_manifest", _postprocess_manifest),
    ):
        saved.append((base, name, getattr(base, name), True))
        setattr(base, name, value)
    return saved


def _restore_v3177_globals(saved: list[tuple[Any, str, Any, bool]]) -> None:
    for module, name, value, existed in reversed(saved):
        if existed:
            setattr(module, name, value)
        else:
            delattr(module, name)


def main() -> int:
    saved = _apply_v3177_globals()
    try:
        return base.main()
    finally:
        _restore_v3177_globals(saved)


if __name__ == "__main__":
    raise SystemExit(main())
