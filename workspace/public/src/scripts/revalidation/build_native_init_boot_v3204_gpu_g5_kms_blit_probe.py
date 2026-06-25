#!/usr/bin/env python3
"""Build V3204 GPU G5 KMS blit probe from GPU readback."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _workspace_bootstrap import repo_root
from a90harness.evidence import workspace_private_build_path, workspace_private_input_path
import build_native_init_boot_v3194_gpu_g3_noop_submit_probe as base

REPO_ROOT = repo_root()
ORIG_V3194_OVERRIDES = base._v3194_overrides
ORIG_V3194_VALUES = base._v3194_values
ORIG_V3194_ADAPTER_SOURCE = base.v3194_adapter_source

CYCLE = "V3204"
INIT_VERSION = "0.11.30"
INIT_BUILD = "v3204-gpu-g5-kms-blit-probe"
BUILD_TAG = INIT_BUILD
DECISION = "v3204-gpu-g5-kms-blit-probe-source-build-pass"

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
OBJ_DIR = OUT_DIR / "obj"
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V3204_GPU_G5_KMS_BLIT_PROBE_SOURCE_BUILD_2026-06-25.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images",
    "boot_linux_v3204_gpu_g5_kms_blit_probe.img",
    legacy_fallback=False,
)
INIT_BINARY = OUT_DIR / "init_v3204_gpu_g5_kms_blit_probe"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v3204_gpu_g5_kms_blit_probe.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v562_gpu_g5_kms_blit_probe"

ENGINE_BINARY = OUT_DIR / "a90_doomgeneric_private_engine_v3204"
ENGINE_ADAPTER_SOURCE = OUT_DIR / "a90_doomgeneric_native_bridge_v3204.c"
ENGINE_ADAPTER_OBJECT = OBJ_DIR / "a90_doomgeneric_native_bridge_v3204.o"
ENGINE_RAMDISK_PATH = "bin/a90_doomgeneric_private_engine_v3204"
ENGINE_REMOTE_PATH = "/" + ENGINE_RAMDISK_PATH
ENGINE_NAME = "doomgeneric-private-link-v3204-gpu-g5-kms-blit-probe"

FRAME_PATH = "/tmp/a90-doomgeneric-v3204-raw-fallback-frame.xbgr8888"
SHARED_FRAME_PATH = "/tmp/a90-doomgeneric-v3204-shared-frame.bin"
INPUT_STATE_PATH = "/tmp/a90-doomgeneric-v3204-input.state"
INPUT_SOCKET_PATH = "/tmp/a90-doomgeneric-v3204-input.sock"
PACE_SOCKET_PATH = "/tmp/a90-doomgeneric-v3204-pace.sock"
TICK_TELEMETRY_PATH = "/tmp/a90-doomgeneric-v3204-tick-telemetry.txt"
AUDIO_PCM_STREAM_PATH = "/cache/a90-runtime/a90-doomgeneric-v3204-sfx.pcmstream"

FRAME_SCALE = "1:1-demo-hud-large-groups-gpu-g5-kms-blit-probe"
FRAME_IPC = "shared-mmap-direct-blit-demo-hud-large-groups-gpu-g5-kms-blit-probe"

INPUT_THREAD_MARKER = base.INPUT_THREAD_MARKER.replace("v3194", "v3204")
TIME_MODEL_MARKER = base.TIME_MODEL_MARKER.replace("v3194", "v3204")
DEMO_HUD_MARKER = base.DEMO_HUD_MARKER.replace("v3194", "v3204")
PACED_TIME_MARKER = base.PACED_TIME_MARKER.replace("v3194", "v3204")
TICK_TELEMETRY_MARKER = base.TICK_TELEMETRY_MARKER.replace("v3194", "v3204")
SCALE_MARKER = base.SCALE_MARKER.replace("v3194", "v3204")
PHASE_TELEMETRY_MARKER = base.PHASE_TELEMETRY_MARKER.replace("v3194", "v3204")
GAMETIC_FRAME_TELEMETRY_MARKER = base.GAMETIC_FRAME_TELEMETRY_MARKER.replace("v3194", "v3204")
SFX_STREAM_MARKER = "a90.doomgeneric.v3204.audio=real-sfx-pcm-stream-gpu-g5-kms-blit-probe"
SOUND_MODE = "native-doom-sfx-gpu-g5-kms-blit-probe-v3204"

AUDIO_CORUN = base.AUDIO_CORUN
AUDIO_CORUN_MODE = SOUND_MODE
AUDIO_CORUN_STREAM = base.AUDIO_CORUN_STREAM
AUDIO_CORUN_DURATION_MS = base.AUDIO_CORUN_DURATION_MS
AUDIO_CORUN_REFRESH_MS = base.AUDIO_CORUN_REFRESH_MS
AUDIO_CORUN_AMPLITUDE_MILLI = base.AUDIO_CORUN_AMPLITUDE_MILLI
PHYSICAL_BUTTON_EXIT = base.PHYSICAL_BUTTON_EXIT

SFX_BACKEND_SOURCE = OUT_DIR / "a90_doomgeneric_native_sfx_v3204.c"
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
        b"a90-doomgeneric-v3194": b"a90-doomgeneric-v3204",
        b"a90.doomgeneric.v3194": b"a90.doomgeneric.v3204",
        b"v3194": b"v3204",
        b"V3194": b"V3204",
    }
    for old, new in replacements.items():
        item = item.replace(old, new)
    return item


GPU_G4_SOLID_FILL_MARKERS = (
    b"g4-solid-fill-probe",
    b"solid-fill-probe",
    b"gpu.g4.fill.version=1",
    b"gpu.g4.fill.scope=kgsl-a2d-solid-fill-readback-probe",
    b"gpu.g4.fill.parent_enters_open=0",
    b"gpu.g4.fill.parent_enters_ioctl=0",
    b"gpu.g4.fill.ioctl_allowlist=drawctxt_create,gpuobj_alloc,gpuobj_info,gpuobj_sync,gpu_command,timestamp_event,waittimestamp,readtimestamp,gpuobj_free,drawctxt_destroy",
    b"gpu.g4.fill.pm4_source=mesa-freedreno-a6xx-fd6-clear-buffer-cp-blit-a2d-ccu-color-flush-seqno",
    b"gpu.g4.fill.post_blit_event=pc_ccu_flush_color_ts_seqno",
    b"gpu.g4.fill.post_blit_event_payload_dwords=4",
    b"gpu.g4.fill.event_seqno=0x%x",
    b"gpu.g4.fill.cache_invalidate_event=excluded-after-v3197-incident",
    b"gpu.g4.fill.pm4_cp_type4=0x%x",
    b"gpu.g4.fill.pm4_cp_type7=0x%x",
    b"gpu.g4.fill.fmt6_32_uint=0x%x",
    b"gpu.g4.fill.r2d_int32=0x%x",
    b"gpu.g4.fill.tile6_linear=0x%x",
    b"gpu.g4.fill.fill_bytes=%llu",
    b"gpu.g4.fill.expected_fill=0x%x",
    b"gpu.g4.fill.event_alloc_size=%llu",
    b"gpu.g4.fill.rb_dbg_eco_mode=skipped-source-magic-not-in-this-unit",
    b"gpu.g4.fill.render_attempted=1",
    b"gpu.g4.fill.triangle_attempted=0",
    b"gpu.g4.fill.kms_blit_attempted=0",
    b"gpu.g4.fill.power_write_attempted=0",
    b"gpu.g4.fill.proprietary_blob_attempted=0",
    b"gpu.g4.fill.result=%s",
    b"gpu.g4.fill.submit_rc=%d",
    b"gpu.g4.fill.submit_timestamp=%u",
    b"gpu.g4.fill.readback_sync_rc=%d",
    b"gpu.g4.fill.readback_verified=%d",
    b"gpu.g4.fill.readback0=0x%x",
    b"gpu.g4.fill.event_alloc_rc=%d",
    b"gpu.g4.fill.event_info_rc=%d",
    b"gpu.g4.fill.event_info_gpuaddr=0x%llx",
    b"gpu.g4.fill.event_free_rc=%d",
    b"gpu.g4.fill.pm4_dwords=%u",
    b"gpu.g4.fill.total_elapsed_ms=%ld",
)

GPU_G5_KMS_BLIT_MARKERS = (
    b"g5-kms-blit-probe",
    b"kms-blit-probe",
    b"gpu.g5.kms.version=1",
    b"gpu.g5.kms.scope=kgsl-a2d-solid-fill-readback-to-kms-dumb-blit-probe",
    b"gpu.g5.kms.kgsl_path=%s",
    b"gpu.g5.kms.drm_path=/dev/dri/card0",
    b"gpu.g5.kms.timeout_ms=%d",
    b"gpu.g5.kms.parent_enters_kgsl_open=0",
    b"gpu.g5.kms.parent_enters_kgsl_ioctl=0",
    b"gpu.g5.kms.kgsl_source=g4-solid-fill-pc-ccu-flush-color-ts-seqno",
    b"gpu.g5.kms.blit_mode=kgsl-private-buffer-readback-to-kms-dumb-framebuffer",
    b"gpu.g5.kms.zero_copy_attempted=0",
    b"gpu.g5.kms.kms_blit_attempted=1",
    b"gpu.g5.kms.power_write_attempted=0",
    b"gpu.g5.kms.proprietary_blob_attempted=0",
    b"gpu.g5.kms.g4_result=%s",
    b"gpu.g5.kms.g4_readback_verified=%d",
    b"gpu.g5.kms.g4_readback0=0x%x",
    b"gpu.g5.kms.begin_frame_rc=%d",
    b"gpu.g5.kms.fb_width=%u",
    b"gpu.g5.kms.fb_height=%u",
    b"gpu.g5.kms.blit_raw_pixel=0x%x",
    b"gpu.g5.kms.blit_rect=%u,%u,%u,%u",
    b"gpu.g5.kms.present_rc=%d",
    b"gpu.g5.kms.result=%s",
    b"gpu-g5-kms-blit",
)

REQUIRED_STRINGS = tuple(
    _rewrite_required_string(item)
    for item in base.REQUIRED_STRINGS
) + (
    SFX_STREAM_MARKER.encode("ascii"),
    SOUND_MODE.encode("ascii"),
    AUDIO_PCM_STREAM_PATH.encode("ascii"),
    b"0.11.30",
    b"v3204-gpu-g5-kms-blit-probe",
) + GPU_G4_SOLID_FILL_MARKERS + GPU_G5_KMS_BLIT_MARKERS


def _v3204_require_strings(path: Path) -> list[str]:
    data = path.read_bytes()
    missing = [
        marker.decode("ascii", errors="replace")
        for marker in REQUIRED_STRINGS
        if marker not in data
    ]
    if missing:
        raise RuntimeError(f"missing V3204 boot-image markers: {missing}")
    return [marker.decode("ascii", errors="replace") for marker in REQUIRED_STRINGS]


SFX_BACKEND_SOURCE_TEXT = (
    base.SFX_BACKEND_SOURCE_TEXT
    .replace(base.AUDIO_PCM_STREAM_PATH, AUDIO_PCM_STREAM_PATH)
    .replace("gpu-g3-noop-submit-probe", "gpu-g5-kms-blit-probe")
    .replace("real-sfx-pcm-stream-gpu-g3-noop-submit-probe",
             "real-sfx-pcm-stream-gpu-g5-kms-blit-probe")
    .replace("v3194", "v3204")
    .replace("V3194", "V3204")
    .replace(base.INIT_VERSION, INIT_VERSION)
    .replace(base.INIT_BUILD, INIT_BUILD)
    .replace(base.ENGINE_NAME, ENGINE_NAME)
    .replace(base.ENGINE_REMOTE_PATH, ENGINE_REMOTE_PATH)
    .replace(base.SOUND_MODE, SOUND_MODE)
)


def _v3204_overrides() -> dict[str, Any]:
    overrides = dict(ORIG_V3194_OVERRIDES())
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


def _v3204_values() -> dict[str, Any]:
    values = dict(ORIG_V3194_VALUES())
    values.update(_v3204_overrides())
    return values


def v3204_adapter_source() -> str:
    return (
        ORIG_V3194_ADAPTER_SOURCE()
        .replace("gpu-g3-noop-submit-probe", "gpu-g5-kms-blit-probe")
        .replace("real-sfx-pcm-stream-gpu-g3-noop-submit-probe",
                 "real-sfx-pcm-stream-gpu-g5-kms-blit-probe")
        .replace("v3194", "v3204")
        .replace("V3194", "V3204")
    )


def render_report(
    manifest: dict[str, Any],
    helper_flags: tuple[str, ...],
    init_extra_flags: tuple[str, ...],
) -> str:
    return "\n".join([
        "# Native Init V3204 GPU G5 KMS Blit Probe Source Build",
        "",
        "## Summary",
        "",
        f"- Cycle: `{CYCLE}`",
        "- Track: GPU G5 KGSL A6xx A2D solid-fill readback copied into the existing KMS dumb-buffer display path.",
        f"- Decision: `{manifest['decision']}`",
        "- Result: PASS",
        "- Device flash: `no` in this build unit.",
        f"- Boot image: `{manifest['boot_image']}`",
        f"- Boot SHA256: `{manifest['boot_sha256']}`",
        f"- Init: `A90 Linux init {manifest['init_version']} ({manifest['init_build']})`",
        "",
        "## Included Delta",
        "",
        "- Adds `gpu g5-kms-blit-probe` as the next ladder rung after the V3203 G4 live pass.",
        "- Reuses the same bounded G4 child path for KGSL A2D `CP_BLIT`, then copies the verified `0xa5c3f00d` readback pixel into a visible central patch on the existing `/dev/dri/card0` KMS dumb framebuffer.",
        "- Keeps the parent out of KGSL `open()`/`ioctl()`; parent-side work is KMS dumb-buffer begin-frame, CPU copy, and `SETCRTC` present.",
        "- This is not zero-copy KMS/GPU sharing. It is a bounded device-verifiable GPU-rendered-buffer-to-KMS-display bridge using the existing proven display path.",
        "",
        "## Safety",
        "",
        "- Boot partition only through `native_init_flash.py` in any future live step.",
        "- Uses KGSL-direct normal command submission; no proprietary Adreno blob/EGL/Bionic path.",
        "- No GDSC/regulator/PMIC/GPIO/power-rail write is included.",
        "- No triangle, shader, compute grid, zero-copy dmabuf, or KMS GPU-plane sharing is included.",
        "- The render target is a private KGSL GPU object, and readback is limited to the first 16 32-bit words after KGSL `GPUOBJ_SYNC FROM_GPU`.",
        "- `RB_DBG_ECO_CNTL` blit-mode toggling is deliberately skipped because Mesa sources route its value through GPU-specific `fd_dev_info.magic`; this unit does not invent that magic value.",
        "- V3204 does not add new KGSL packet classes beyond the V3203-passed G4 stream. It adds a KMS presentation rung after verified CPU readback.",
        "",
        "## Source Basis",
        "",
        "- Local Samsung KGSL UAPI/driver source: `IOCTL_KGSL_GPU_COMMAND` returns a timestamp, `IOCTL_KGSL_TIMESTAMP_EVENT` can create a fence fd for that timestamp, and `IOCTL_KGSL_GPUOBJ_SYNC` performs cache sync by GPU object id.",
        "- Existing native-init KMS implementation: `a90_kms_begin_frame()` prepares mapped dumb buffers and `a90_kms_present()` presents the active framebuffer on `/dev/dri/card0`.",
        "- Mesa/freedreno PM4 source: type4/type7 odd-parity packet helpers, A6xx `fd6_clear_buffer()` A2D clear path, `CP_SET_MARKER(RM6_BLIT2DSCALE)`, `CP_BLIT(BLIT_OP_SCALE)`, and A6xx register XML enum values.",
        "- Local live evidence: `docs/reports/NATIVE_INIT_V3197_GPU_G4_SOLID_FILL_PROBE_LIVE_INCIDENT_2026-06-25.md` identified the V3196 post-blit event-write tail as unsafe; `docs/reports/NATIVE_INIT_V3199_GPU_G4_SOLID_FILL_NOEVENT_LIVE_2026-06-25.md` showed that removing all post-blit events avoids faults but leaves the target buffer unchanged; `docs/reports/NATIVE_INIT_V3201_GPU_G4_CCU_FLUSH_LIVE_INCIDENT_2026-06-25.md` showed that a one-dword raw CCU event packet is unsafe.",
        "- Mesa references: `https://docs.mesa3d.org/drivers/freedreno.html`, `https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/src/gallium/drivers/freedreno/a6xx/fd6_blitter.cc`, `https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/src/gallium/drivers/freedreno/a6xx/fd6_emit.h`, `https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/src/gallium/drivers/freedreno/a6xx/fd6_barrier.cc`, `https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/src/freedreno/common/freedreno_pm4.h`, `https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/src/freedreno/common/freedreno_gpu_event.h`, `https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/src/freedreno/common/freedreno_devices.py`, `https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/src/freedreno/registers/adreno/adreno_pm4.xml`, `https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/src/freedreno/registers/adreno/a6xx.xml`, `https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/src/freedreno/registers/adreno/a6xx_enums.xml`, `https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/src/freedreno/registers/adreno/adreno_common.xml`.",
        "",
        "## Validation",
        "",
        "- `py_compile`: V3204 builder and focused tests.",
        "- `unittest`: V3204 GPU G5 source contract plus G4/G3/G2 regression contracts.",
        "- Build: AArch64 helper/native-init compile, ramdisk pack, boot image pack, SHA256 capture.",
        "- Marker check: generated boot image contains V3204 identity, G0/G1/G2/G3/G4 markers, and G5 KMS blit markers.",
        "- `git diff --check`: PASS.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `gpu-g5-kms-blit-probe-candidate`.",
    ]) + "\n"


def _postprocess_manifest() -> dict[str, Any]:
    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "gpu-g5-kms-blit-probe-candidate",
        "adoption_state": "pending-gpu-g5-kms-blit-live-validation",
        "gpu_g4": {
            "source_baseline": "v3200-gpu-g4-solid-fill-ccu-flush-probe",
            "incident_report": "docs/reports/NATIVE_INIT_V3197_GPU_G4_SOLID_FILL_PROBE_LIVE_INCIDENT_2026-06-25.md",
            "noevent_live_report": "docs/reports/NATIVE_INIT_V3199_GPU_G4_SOLID_FILL_NOEVENT_LIVE_2026-06-25.md",
            "raw_ccu_flush_incident_report": "docs/reports/NATIVE_INIT_V3201_GPU_G4_CCU_FLUSH_LIVE_INCIDENT_2026-06-25.md",
            "g3_live_report": "docs/reports/NATIVE_INIT_V3195_GPU_G3_NOOP_SUBMIT_PROBE_LIVE_2026-06-25.md",
            "commands": [
                "gpu g0-fwclass-prepare",
                "gpu g1-context-probe --timeout-ms 5000 --materialize-devnode",
                "gpu g2-mmap-probe --timeout-ms 5000 --materialize-devnode",
                "gpu g3-noop-submit-probe --timeout-ms 5000 --materialize-devnode",
                "gpu g4-solid-fill-probe --timeout-ms 5000 --materialize-devnode",
                "gpu g5-kms-blit-probe --timeout-ms 5000 --materialize-devnode",
            ],
            "command_stream": {
                "pm4_source": "Mesa freedreno A6xx fd6_clear_buffer CP_BLIT A2D solid color path with post-blit PC_CCU_FLUSH_COLOR_TS timestamp event",
                "pm4_reference_urls": [
                    "https://docs.mesa3d.org/drivers/freedreno.html",
                    "https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/src/gallium/drivers/freedreno/a6xx/fd6_blitter.cc",
                    "https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/src/gallium/drivers/freedreno/a6xx/fd6_emit.h",
                    "https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/src/gallium/drivers/freedreno/a6xx/fd6_barrier.cc",
                    "https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/src/freedreno/common/freedreno_pm4.h",
                    "https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/src/freedreno/common/freedreno_gpu_event.h",
                    "https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/src/freedreno/common/freedreno_devices.py",
                    "https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/src/freedreno/registers/adreno/adreno_pm4.xml",
                    "https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/src/freedreno/registers/adreno/a6xx.xml",
                    "https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/src/freedreno/registers/adreno/a6xx_enums.xml",
                    "https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/src/freedreno/registers/adreno/adreno_common.xml",
                ],
                "type4": "0x40000000",
                "type7": "0x70000000",
                "cp_set_marker": "0x65",
                "cp_blit": "0x2c",
                "cp_event_write_tail": "pc-ccu-flush-color-ts-timestamp-event-only",
                "post_blit_events": [
                    "PC_CCU_FLUSH_COLOR_TS"
                ],
                "post_blit_event_payload_dwords": 4,
                "post_blit_event_timestamp_bit": True,
                "post_blit_event_seqno": "0x32020001",
                "event_gpuobj": "dedicated-kgsl-gpuobj-in-command-objlist",
                "excluded_post_blit_events": [
                    "DEBUG_LABEL",
                    "CACHE_FLUSH_TS",
                    "CACHE_INVALIDATE"
                ],
                "cp_wait_for_idle": "0x26",
                "fmt6_32_uint": "0x4b",
                "r2d_int32": "0x7",
                "tile6_linear": "0x0",
                "rm6_blit2dscale": 12,
                "blit_op_scale": 3,
                "fill_bytes": 256,
                "expected_fill": "0xa5c3f00d",
                "readback_dwords": 16,
            },
            "ioctl_allowlist": [
                "IOCTL_KGSL_DRAWCTXT_CREATE",
                "IOCTL_KGSL_GPUOBJ_ALLOC",
                "IOCTL_KGSL_GPUOBJ_INFO",
                "IOCTL_KGSL_GPUOBJ_SYNC",
                "IOCTL_KGSL_GPU_COMMAND",
                "IOCTL_KGSL_TIMESTAMP_EVENT",
                "IOCTL_KGSL_DEVICE_WAITTIMESTAMP_CTXTID",
                "IOCTL_KGSL_CMDSTREAM_READTIMESTAMP_CTXTID",
                "IOCTL_KGSL_GPUOBJ_FREE",
                "IOCTL_KGSL_DRAWCTXT_DESTROY",
            ],
            "parent_enters_open": False,
            "parent_enters_ioctl": False,
            "timeout_guard_ms_default": 2000,
            "timeout_guard_ms_max": 10000,
            "waittimestamp_timeout_ms": 1000,
            "readback_sync": "KGSL_GPUMEM_CACHE_FROM_GPU | KGSL_GPUMEM_CACHE_RANGE",
            "rb_dbg_eco_mode": "skipped-source-magic-not-in-this-unit",
            "forbidden_operations": [
                "shader-submit",
                "triangle-render",
                "GDSC-write",
                "regulator-write",
                "PMIC-write",
                "GPIO-write",
                "proprietary-adreno-blob",
                "exploit-dev",
            ],
            "next_live_validation": [
                "flash-v3204-through-native-init-flash",
                "post-flash-health-check",
                "gpu-g0-fwclass-prepare",
                "gpu-g1-context-probe-timeout-guard",
                "gpu-g2-mmap-probe-timeout-guard",
                "gpu-g3-noop-submit-probe-timeout-guard",
                "gpu-g4-solid-fill-probe-timeout-guard",
                "gpu-g5-kms-blit-probe-timeout-guard",
                "post-probe-selftest-and-dmesg-gpu-fault-filter",
            ],
        },
        "gpu_g5": {
            "source_baseline": "v3202-gpu-g4-solid-fill-ccu-seqno-probe",
            "g4_live_report": "docs/reports/NATIVE_INIT_V3203_GPU_G4_CCU_SEQNO_LIVE_PASS_2026-06-25.md",
            "command": "gpu g5-kms-blit-probe --timeout-ms 5000 --materialize-devnode",
            "display_path": "/dev/dri/card0",
            "kms_path": "a90_kms_begin_frame + CPU copy into mapped dumb framebuffer + a90_kms_present",
            "source_buffer_path": "KGSL private GPU object solid fill, GPUOBJ_SYNC FROM_GPU, CPU readback",
            "expected_raw_pixel": "0xa5c3f00d",
            "zero_copy_attempted": False,
            "parent_enters_kgsl_open": False,
            "parent_enters_kgsl_ioctl": False,
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
    (OUT_DIR / "gpu-g5-kms-blit-probe-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "gpu-g5-kms-blit-probe-candidate",
        "boot_image": rel(BOOT_IMAGE),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "live_validation_focus": manifest["gpu_g4"]["next_live_validation"],
        "source_report": rel(REPORT_PATH),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-gpu-g5-kms-blit-live-validation",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def _patch_base_module() -> list[tuple[Any, str, Any, bool]]:
    saved: list[tuple[Any, str, Any, bool]] = []
    for name, value in _v3204_overrides().items():
        existed = hasattr(base, name)
        saved.append((base, name, getattr(base, name, None), existed))
        setattr(base, name, value)
    for name, value in (
        ("_v3194_overrides", _v3204_overrides),
        ("_v3194_values", _v3204_values),
        ("v3194_adapter_source", v3204_adapter_source),
        ("_v3194_require_strings", _v3204_require_strings),
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
