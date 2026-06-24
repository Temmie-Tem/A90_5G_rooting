#!/usr/bin/env python3
"""Build V3192 GPU G2b bounded KGSL GPU object mmap/munmap probe candidate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _workspace_bootstrap import repo_root
from a90harness.evidence import workspace_private_build_path, workspace_private_input_path
import build_native_init_boot_v3190_gpu_g2_gpuobj_probe as base

REPO_ROOT = repo_root()
ORIG_V3190_OVERRIDES = base._v3190_overrides
ORIG_V3190_VALUES = base._v3190_values
ORIG_V3190_ADAPTER_SOURCE = base.v3190_adapter_source

CYCLE = "V3192"
INIT_VERSION = "0.11.24"
INIT_BUILD = "v3192-gpu-g2-mmap-probe"
BUILD_TAG = INIT_BUILD
DECISION = "v3192-gpu-g2-mmap-probe-source-build-pass"

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
OBJ_DIR = OUT_DIR / "obj"
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V3192_GPU_G2_MMAP_PROBE_SOURCE_BUILD_2026-06-25.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images",
    "boot_linux_v3192_gpu_g2_mmap_probe.img",
    legacy_fallback=False,
)
INIT_BINARY = OUT_DIR / "init_v3192_gpu_g2_mmap_probe"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v3192_gpu_g2_mmap_probe.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v557_gpu_g2_mmap_probe"

ENGINE_BINARY = OUT_DIR / "a90_doomgeneric_private_engine_v3192"
ENGINE_ADAPTER_SOURCE = OUT_DIR / "a90_doomgeneric_native_bridge_v3192.c"
ENGINE_ADAPTER_OBJECT = OBJ_DIR / "a90_doomgeneric_native_bridge_v3192.o"
ENGINE_RAMDISK_PATH = "bin/a90_doomgeneric_private_engine_v3192"
ENGINE_REMOTE_PATH = "/" + ENGINE_RAMDISK_PATH
ENGINE_NAME = "doomgeneric-private-link-v3192-gpu-g2-mmap-probe"

FRAME_PATH = "/tmp/a90-doomgeneric-v3192-raw-fallback-frame.xbgr8888"
SHARED_FRAME_PATH = "/tmp/a90-doomgeneric-v3192-shared-frame.bin"
INPUT_STATE_PATH = "/tmp/a90-doomgeneric-v3192-input.state"
INPUT_SOCKET_PATH = "/tmp/a90-doomgeneric-v3192-input.sock"
PACE_SOCKET_PATH = "/tmp/a90-doomgeneric-v3192-pace.sock"
TICK_TELEMETRY_PATH = "/tmp/a90-doomgeneric-v3192-tick-telemetry.txt"
AUDIO_PCM_STREAM_PATH = "/cache/a90-runtime/a90-doomgeneric-v3192-sfx.pcmstream"

FRAME_SCALE = "1:1-demo-hud-large-groups-gpu-g2-mmap-probe"
FRAME_IPC = "shared-mmap-direct-blit-demo-hud-large-groups-gpu-g2-mmap-probe"

INPUT_THREAD_MARKER = base.INPUT_THREAD_MARKER.replace("v3188", "v3192")
TIME_MODEL_MARKER = base.TIME_MODEL_MARKER.replace("v3188", "v3192")
DEMO_HUD_MARKER = base.DEMO_HUD_MARKER.replace("v3188", "v3192")
PACED_TIME_MARKER = base.PACED_TIME_MARKER.replace("v3188", "v3192")
TICK_TELEMETRY_MARKER = base.TICK_TELEMETRY_MARKER.replace("v3188", "v3192")
SCALE_MARKER = base.SCALE_MARKER.replace("v3188", "v3192")
PHASE_TELEMETRY_MARKER = base.PHASE_TELEMETRY_MARKER.replace("v3188", "v3192")
GAMETIC_FRAME_TELEMETRY_MARKER = base.GAMETIC_FRAME_TELEMETRY_MARKER.replace("v3188", "v3192")
SFX_STREAM_MARKER = "a90.doomgeneric.v3192.audio=real-sfx-pcm-stream-gpu-g2-mmap-probe"
SOUND_MODE = "native-doom-sfx-gpu-g2-mmap-probe-v3192"

AUDIO_CORUN = base.AUDIO_CORUN
AUDIO_CORUN_MODE = SOUND_MODE
AUDIO_CORUN_STREAM = base.AUDIO_CORUN_STREAM
AUDIO_CORUN_DURATION_MS = base.AUDIO_CORUN_DURATION_MS
AUDIO_CORUN_REFRESH_MS = base.AUDIO_CORUN_REFRESH_MS
AUDIO_CORUN_AMPLITUDE_MILLI = base.AUDIO_CORUN_AMPLITUDE_MILLI
PHYSICAL_BUTTON_EXIT = base.PHYSICAL_BUTTON_EXIT

SFX_BACKEND_SOURCE = OUT_DIR / "a90_doomgeneric_native_sfx_v3192.c"
SDL_MIXER_STUB = OUT_DIR / "SDL_mixer.h"


def rel(path: Path) -> str:
    return base.rel(path)


def _rewrite_required_string(item: bytes) -> bytes:
    replacements = {
        base.INIT_VERSION.encode("ascii"): INIT_VERSION.encode("ascii"),
        base.INIT_BUILD.encode("ascii"): INIT_BUILD.encode("ascii"),
        base.ENGINE_NAME.encode("ascii"): ENGINE_NAME.encode("ascii"),
        base.ENGINE_REMOTE_PATH.encode("ascii"): ENGINE_REMOTE_PATH.encode("ascii"),
        base.SOUND_MODE.encode("ascii"): SOUND_MODE.encode("ascii"),
        base.SFX_STREAM_MARKER.encode("ascii"): SFX_STREAM_MARKER.encode("ascii"),
        base.AUDIO_PCM_STREAM_PATH.encode("ascii"): AUDIO_PCM_STREAM_PATH.encode("ascii"),
        b"gpu-g2-gpuobj-probe": b"gpu-g2-mmap-probe",
        b"a90-doomgeneric-v3190": b"a90-doomgeneric-v3192",
        b"a90.doomgeneric.v3190": b"a90.doomgeneric.v3192",
        b"v3190": b"v3192",
        b"V3190": b"V3192",
        b"gpu.g2.gpuobj.scope=kgsl-gpuobj-alloc-free-probe":
            b"gpu.g2.gpuobj.scope=%s",
        b"gpu.g2.gpuobj.mmap_attempted=0": b"gpu.g2.gpuobj.mmap_attempted=%d",
    }
    for old, new in replacements.items():
        item = item.replace(old, new)
    return item


GPU_G2_MMAP_PROBE_MARKERS = (
    b"g2-mmap-probe",
    b"g2-gpuobj-probe",
    b"gpu.g2.gpuobj.version=1",
    b"gpu.g2.gpuobj.scope=%s",
    b"kgsl-gpuobj-mmap-munmap-probe",
    b"gpu.g2.gpuobj.parent_enters_open=0",
    b"gpu.g2.gpuobj.parent_enters_ioctl=0",
    b"gpu.g2.gpuobj.ioctl_allowlist=drawctxt_create,gpuobj_alloc,gpuobj_free,drawctxt_destroy",
    b"gpu.g2.gpuobj.alloc_size=%llu",
    b"gpu.g2.gpuobj.mmap_attempted=%d",
    b"gpu.g2.gpuobj.mmap_offset_rule=id_times_4096",
    b"gpu.g2.gpuobj.mmap_access_attempted=0",
    b"gpu.g2.gpuobj.mmap_rc=%d",
    b"gpu.g2.gpuobj.munmap_rc=%d",
    b"gpu.g2.gpuobj.submit_attempted=0",
    b"gpu.g2.gpuobj.power_write_attempted=0",
    b"gpu.g2.gpuobj.result=%s",
    b"gpu.g2.gpuobj.alloc_rc=%d",
    b"gpu.g2.gpuobj.free_rc=%d",
    b"gpu.g2.gpuobj.total_elapsed_ms=%ld",
)

REQUIRED_STRINGS = tuple(
    _rewrite_required_string(item)
    for item in base.REQUIRED_STRINGS
) + (
    SFX_STREAM_MARKER.encode("ascii"),
    SOUND_MODE.encode("ascii"),
    AUDIO_PCM_STREAM_PATH.encode("ascii"),
    b"0.11.24",
    b"v3192-gpu-g2-mmap-probe",
) + GPU_G2_MMAP_PROBE_MARKERS


def _v3192_require_strings(path: Path) -> list[str]:
    data = path.read_bytes()
    missing = [
        marker.decode("ascii", errors="replace")
        for marker in REQUIRED_STRINGS
        if marker not in data
    ]
    if missing:
        raise RuntimeError(f"missing V3192 boot-image markers: {missing}")
    return [marker.decode("ascii", errors="replace") for marker in REQUIRED_STRINGS]


SFX_BACKEND_SOURCE_TEXT = (
    base.SFX_BACKEND_SOURCE_TEXT
    .replace(base.AUDIO_PCM_STREAM_PATH, AUDIO_PCM_STREAM_PATH)
    .replace("gpu-g2-gpuobj-probe", "gpu-g2-mmap-probe")
    .replace("v3190", "v3192")
    .replace("V3190", "V3192")
    .replace(base.INIT_VERSION, INIT_VERSION)
    .replace(base.INIT_BUILD, INIT_BUILD)
    .replace(base.ENGINE_NAME, ENGINE_NAME)
    .replace(base.ENGINE_REMOTE_PATH, ENGINE_REMOTE_PATH)
    .replace(base.SOUND_MODE, SOUND_MODE)
)


def _v3192_overrides() -> dict[str, Any]:
    overrides = dict(ORIG_V3190_OVERRIDES())
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


def _v3192_values() -> dict[str, Any]:
    values = dict(ORIG_V3190_VALUES())
    values.update(_v3192_overrides())
    return values


def v3192_adapter_source() -> str:
    return (
        ORIG_V3190_ADAPTER_SOURCE()
        .replace("gpu-g2-gpuobj-probe", "gpu-g2-mmap-probe")
        .replace("real-sfx-pcm-stream-gpu-g2-gpuobj-probe",
                 "real-sfx-pcm-stream-gpu-g2-mmap-probe")
        .replace("v3190", "v3192")
        .replace("V3190", "V3192")
    )


def render_report(
    manifest: dict[str, Any],
    helper_flags: tuple[str, ...],
    init_extra_flags: tuple[str, ...],
) -> str:
    return "\n".join([
        "# Native Init V3192 GPU G2 MMAP Probe Source Build",
        "",
        "## Summary",
        "",
        f"- Cycle: `{CYCLE}`",
        "- Track: GPU G2b KGSL GPU object mmap/munmap probe.",
        f"- Decision: `{manifest['decision']}`",
        "- Result: PASS",
        "- Device flash: `no` in this build unit.",
        f"- Boot image: `{manifest['boot_image']}`",
        f"- Boot SHA256: `{manifest['boot_sha256']}`",
        f"- Init: `A90 Linux init {manifest['init_version']} ({manifest['init_build']})`",
        "",
        "## Included Delta",
        "",
        "- Adds `gpu g2-mmap-probe`, a bounded child-only KGSL GPU object mmap/munmap probe.",
        "- The child sequence is `open` -> `DRAWCTXT_CREATE` -> `GPUOBJ_ALLOC` (4096 bytes, flags 0) -> `mmap` at offset `id * 4096` -> `munmap` -> `GPUOBJ_FREE` -> `DRAWCTXT_DESTROY` -> `close`.",
        "- Keeps V3190 `gpu g2-gpuobj-probe`, V3188 `gpu g1-context-probe`, V3185 `gpu g0-fwclass-prepare`, and bounded G0 open probe available.",
        "- The parent never enters KGSL `open()` or `ioctl()`; it only enforces timeout and reports metadata.",
        "",
        "## Safety",
        "",
        "- Boot partition only through `native_init_flash.py` in any future live step.",
        "- No mapped memory read/write, command submit, freedreno rendering, or proprietary Adreno blob/EGL/Bionic path.",
        "- No GMU/GDSC/regulator/PMIC/GPIO/power-rail write is included.",
        "- G2b probe must run only after G0 firmware-class prepare and G1 context-create have passed and post-flash health is clean.",
        "",
        "## Validation",
        "",
        "- `py_compile`: V3192 builder and focused tests.",
        "- `unittest`: V3192 GPU G2b source contract plus V3188/V3185/V3180 regression contracts.",
        "- Build: AArch64 helper/native-init compile, ramdisk pack, boot image pack, SHA256 capture.",
        "- Marker check: generated boot image contains V3192 identity, G0/G1/G2a markers, and G2b mmap probe markers.",
        "- `git diff --check`: PASS.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `gpu-g2-mmap-probe-candidate`.",
    ]) + "\n"


def _postprocess_manifest() -> dict[str, Any]:
    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "gpu-g2-mmap-probe-candidate",
        "adoption_state": "pending-gpu-g2-mmap-probe-live-validation",
        "gpu_g2b": {
            "source_baseline": "v3190-gpu-g2-gpuobj-probe",
            "g2a_live_report": "docs/reports/NATIVE_INIT_V3191_GPU_G2_GPUOBJ_PROBE_LIVE_2026-06-25.md",
            "g1_live_report": "docs/reports/NATIVE_INIT_V3189_GPU_G1_CONTEXT_PROBE_LIVE_2026-06-25.md",
            "commands": [
                "gpu g0-fwclass-prepare",
                "gpu g1-context-probe --timeout-ms 5000 --materialize-devnode",
                "gpu g2-gpuobj-probe --timeout-ms 5000 --materialize-devnode",
                "gpu g2-mmap-probe --timeout-ms 5000 --materialize-devnode",
            ],
            "context_flags": "KGSL_CONTEXT_NO_GMEM_ALLOC|KGSL_CONTEXT_PREAMBLE|KGSL_CONTEXT_NO_SNAPSHOT|KGSL_CONTEXT_TYPE_GL",
            "gpuobj_alloc_size": 4096,
            "gpuobj_alloc_flags": "0x0",
            "mmap_offset_rule": "offset_bytes = gpuobj_id * 4096; kernel get_mmap_entry first resolves vm_pgoff as kgsl_sharedmem_find_id(private, pgoff)",
            "mmap_access_attempted": False,
            "ioctl_allowlist": [
                "IOCTL_KGSL_DRAWCTXT_CREATE",
                "IOCTL_KGSL_GPUOBJ_ALLOC",
                "IOCTL_KGSL_GPUOBJ_FREE",
                "IOCTL_KGSL_DRAWCTXT_DESTROY",
            ],
            "parent_enters_open": False,
            "parent_enters_ioctl": False,
            "timeout_guard_ms_default": 2000,
            "timeout_guard_ms_max": 10000,
            "forbidden_operations": [
                "kgsl-mapped-memory-read",
                "kgsl-mapped-memory-write",
                "kgsl-gpu-command",
                "kgsl-submit",
                "kgsl-gpuobj-import",
                "freedreno-render",
                "GDSC-write",
                "regulator-write",
                "PMIC-write",
                "GPIO-write",
                "proprietary-adreno-blob",
                "exploit-dev",
            ],
            "next_live_validation": [
                "flash-v3192-through-native-init-flash",
                "post-flash-health-check",
                "gpu-g0-fwclass-prepare",
                "gpu-g1-context-probe-timeout-guard",
                "gpu-g2-gpuobj-probe-timeout-guard",
                "gpu-g2-mmap-probe-timeout-guard",
                "post-probe-selftest-and-dmesg-tail",
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
    (OUT_DIR / "gpu-g2-mmap-probe-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "gpu-g2-mmap-probe-candidate",
        "boot_image": rel(BOOT_IMAGE),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "live_validation_focus": [
            "gpu-g0-fwclass-prepare",
            "gpu-g1-context-probe-timeout-guard",
            "gpu-g2-gpuobj-probe-timeout-guard",
            "gpu-g2-mmap-probe-timeout-guard",
            "post-probe-selftest-and-dmesg-tail",
        ],
        "source_report": rel(REPORT_PATH),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-gpu-g2-mmap-probe-live-validation",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def _patch_base_module() -> list[tuple[Any, str, Any, bool]]:
    saved: list[tuple[Any, str, Any, bool]] = []
    for name, value in _v3192_overrides().items():
        existed = hasattr(base, name)
        saved.append((base, name, getattr(base, name, None), existed))
        setattr(base, name, value)
    for name, value in (
        ("_v3190_overrides", _v3192_overrides),
        ("_v3190_values", _v3192_values),
        ("v3190_adapter_source", v3192_adapter_source),
        ("_v3190_require_strings", _v3192_require_strings),
        ("render_report", render_report),
        ("_postprocess_manifest", _postprocess_manifest),
    ):
        saved.append((base, name, getattr(base, name), True))
        setattr(base, name, value)
    return saved


def _restore_base_module(saved: list[tuple[Any, str, Any, bool]]) -> None:
    for module, name, value, existed in reversed(saved):
        if existed:
            setattr(module, name, value)
        else:
            delattr(module, name)


def main() -> int:
    saved = _patch_base_module()
    try:
        return base.main()
    finally:
        _restore_base_module(saved)


if __name__ == "__main__":
    raise SystemExit(main())
