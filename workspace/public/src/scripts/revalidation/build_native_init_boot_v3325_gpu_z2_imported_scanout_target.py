#!/usr/bin/env python3
"""Build V3325 GPU Z2 imported scanout render-target proof."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _workspace_bootstrap import add_legacy_revalidation_path, repo_root

REPO_ROOT = repo_root()
add_legacy_revalidation_path(REPO_ROOT)

from a90harness.evidence import workspace_private_build_path, workspace_private_input_path
import build_native_init_boot_v3321_gpu_m3_hold_timeout_budget as previous

base = previous.base

CYCLE = "V3325"
INIT_VERSION = "0.11.93"
INIT_BUILD = "v3325-gpu-z2-imported-scanout-target"
BUILD_TAG = INIT_BUILD
DECISION = "v3325-gpu-z2-imported-scanout-target-source-build-pass"

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
OBJ_DIR = OUT_DIR / "obj"
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V3325_GPU_Z2_IMPORTED_SCANOUT_TARGET_SOURCE_BUILD_2026-06-27.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images",
    "boot_linux_v3325_gpu_z2_imported_scanout_target.img",
    legacy_fallback=False,
)
BASE_BOOT = previous.BOOT_IMAGE
INIT_BINARY = OUT_DIR / "init_v3325_gpu_z2_imported_scanout_target"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v3325_gpu_z2_imported_scanout_target.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v617_gpu_z2_imported_scanout_target"

ENGINE_BINARY = OUT_DIR / "a90_doomgeneric_private_engine_v3325"
ENGINE_ADAPTER_SOURCE = OUT_DIR / "a90_doomgeneric_native_bridge_v3325.c"
ENGINE_ADAPTER_OBJECT = OBJ_DIR / "a90_doomgeneric_native_bridge_v3325.o"
ENGINE_RAMDISK_PATH = "bin/a90_doomgeneric_private_engine_v3325"
ENGINE_REMOTE_PATH = "/" + ENGINE_RAMDISK_PATH
ENGINE_NAME = "doomgeneric-private-link-v3325-gpu-z2-imported-scanout-target"

FRAME_PATH = "/tmp/a90-doomgeneric-v3325-raw-fallback-frame.xbgr8888"
SHARED_FRAME_PATH = "/tmp/a90-doomgeneric-v3325-shared-frame.bin"
INPUT_STATE_PATH = "/tmp/a90-doomgeneric-v3325-input.state"
INPUT_SOCKET_PATH = "/tmp/a90-doomgeneric-v3325-input.sock"
PACE_SOCKET_PATH = "/tmp/a90-doomgeneric-v3325-pace.sock"
TICK_TELEMETRY_PATH = "/tmp/a90-doomgeneric-v3325-tick-telemetry.txt"
AUDIO_PCM_STREAM_PATH = "/cache/a90-runtime/a90-doomgeneric-v3325-sfx.pcmstream"

FRAME_SCALE = "1:1-demo-hud-large-groups-gpu-z2-imported-scanout-target"
FRAME_IPC = "shared-mmap-direct-blit-demo-hud-large-groups-gpu-z2-imported-scanout-target"

SFX_STREAM_MARKER = "a90.doomgeneric.v3325.audio=real-sfx-pcm-stream-gpu-z2-imported-scanout-target"
SOUND_MODE = "native-doom-sfx-gpu-z2-imported-scanout-target-v3325"

SFX_BACKEND_SOURCE = OUT_DIR / "a90_doomgeneric_native_sfx_v3325.c"
SDL_MIXER_STUB = OUT_DIR / "SDL_mixer.h"

SCOPE = "gpu-z2-imported-scanout-render-target"
Z2_COMMAND = "gpu z2-imported-scanout-target-probe --timeout-ms 60000 --materialize-devnode"
Z2_BASELINE = "v3324-z2-kgsl-dmabuf-import-preflight-pass"


def _rewrite_v3325_text(text: str) -> str:
    replacements = (
        (previous.INIT_VERSION, INIT_VERSION),
        (previous.INIT_BUILD, INIT_BUILD),
        (previous.ENGINE_NAME, ENGINE_NAME),
        (previous.ENGINE_REMOTE_PATH, ENGINE_REMOTE_PATH),
        (previous.SOUND_MODE, SOUND_MODE),
        (previous.SFX_STREAM_MARKER, SFX_STREAM_MARKER),
        (previous.AUDIO_PCM_STREAM_PATH, AUDIO_PCM_STREAM_PATH),
        ("a90-doomgeneric-v3321", "a90-doomgeneric-v3325"),
        ("a90.doomgeneric.v3321", "a90.doomgeneric.v3325"),
        ("v3321", "v3325"),
        ("V3321", "V3325"),
        ("gpu-m3-hold-timeout-budget", "gpu-z2-imported-scanout-target"),
    )
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def _rewrite_v3325_bytes(item: bytes) -> bytes:
    return _rewrite_v3325_text(item.decode("utf-8")).encode("utf-8")


GPU_Z2_IMPORTED_TARGET_MARKERS = (
    b"z2-imported-scanout-target-probe",
    b"imported-scanout-target-probe",
    b"gpu.z2.import.scope=gpu-z2-imported-scanout-render-target",
    b"gpu.z2.import.buffer=drm-msm-scanout-gem-prime-fd-kgsl-dmabuf-import",
    b"gpu.z2.import.blit_mode=kgsl-textured-quad-scale-to-imported-scanout-linear",
    b"gpu.z2.import.kgsl_submit_attempted=1",
    b"gpu.z2.import.kms_adfb2_attempted=1",
    b"gpu.z2.import.kms_copy_attempted=0",
    b"gpu.z2.import.kms_present_attempted=0",
    b"gpu.z2.import.power_write_attempted=0",
    b"gpu.z2.import.proprietary_blob_attempted=0",
    b"gpu.z2.import.drm.addfb2_rc=%d fb_id=%u",
    b"gpu.z2.import.kgsl.info_rc=%d gpuaddr=0x%llx size=%llu flags=0x%llx va_len=%llu",
    b"gpu.z2.import.semantic.match_count=%u",
    b"gpu.z2.import.semantic.output_other_count=%u",
    b"gpu.z2.import.result=%s",
    b"z2-imported-scanout-render-target-pass",
)

REQUIRED_STRINGS = tuple(
    _rewrite_v3325_bytes(item) for item in previous.REQUIRED_STRINGS
) + GPU_Z2_IMPORTED_TARGET_MARKERS


def _minimal_gpu_z2_manifest() -> dict[str, Any]:
    return {
        "scope": SCOPE,
        "command": Z2_COMMAND,
        "expected_result": "z2-imported-scanout-render-target-pass",
        "baseline": Z2_BASELINE,
        "target_width": 960,
        "target_height": 720,
        "target_stride": 3840,
        "target_bytes": 2764800,
        "buffer": "drm-msm-scanout-gem-prime-fd-kgsl-dmabuf-import",
        "copy_attempted": False,
        "kms_present_attempted": False,
        "kms_addfb2_attempted": True,
        "kgsl_submit_attempted": True,
        "power_write_attempted": False,
        "proprietary_blob_attempted": False,
        "pass_requirements": [
            "require-drm-msm-scanout-gem",
            "require-prime-fd-export",
            "require-kms-addfb2-success",
            "require-kgsl-dmabuf-import-success",
            "require-gpu-render-into-imported-scanout-gem",
            "require-changed-count-positive",
            "require-semantic-match-count-64",
            "require-semantic-output-other-count-0",
            "require-no-kms-copy",
            "require-no-kms-present",
            "require-selftest-fail-0-after-probe",
        ],
    }


def render_report(
    manifest: dict[str, Any],
    helper_flags: tuple[str, ...],
    init_extra_flags: tuple[str, ...],
) -> str:
    boot_image = manifest.get("boot_image", base.rel(BOOT_IMAGE))
    boot_sha = manifest.get("boot_sha256", "")
    return "\n".join([
        "# Native Init V3325 GPU Z2 Imported Scanout Target Source Build",
        "",
        f"- Cycle: `{CYCLE}`",
        f"- Decision: `{DECISION}`",
        f"- Init: `A90 Linux init {INIT_VERSION} ({INIT_BUILD})`",
        f"- Boot image: `{boot_image}`",
        f"- Boot SHA256: `{boot_sha}`",
        f"- Base boot: `{base.rel(BASE_BOOT)}`",
        "",
        "## Change",
        "",
        "- Adds `gpu z2-imported-scanout-target-probe [--timeout-ms N] [--materialize-devnode]`.",
        "- Creates a DRM msm `MSM_BO_SCANOUT|MSM_BO_WC` linear GEM, exports it as PRIME, attaches it as an XBGR8888 KMS FB with `ADDFB2`, imports the same dma-buf into KGSL, then renders the M3 textured monitor graph into that imported scanout GEM.",
        "- The probe intentionally does not copy to the existing KMS dumb framebuffer and does not present/pageflip yet; it proves the render target is shared and scanout-eligible before the Z3 pageflip step.",
        "",
        "## Validation Contract",
        "",
        f"- Command: `{Z2_COMMAND}`",
        "- PASS requires `gpu.z2.import.result=z2-imported-scanout-render-target-pass`, `changed_count>0`, semantic match count `64`, semantic output-other count `0`, KGSL import success, KMS `ADDFB2` success, no KMS copy, no KMS present, and post-probe `selftest fail=0`.",
        "- No PMIC/GDSC/regulator/GPIO/backlight write, proprietary blob, EGL/GLES/OpenCL, forbidden partition, or raw flash path is introduced.",
        "",
        "## Static Validation",
        "",
        "- `py_compile`: V3325 builder and focused source test.",
        "- Compile: focused AArch64 native-init compile with existing baseline warnings only.",
        "- Build: AArch64 helper/native-init compile, preserved-ramdisk overlay, boot image pack, SHA256 capture.",
        "- Marker check: generated boot image contains V3325 identity plus Z2 imported scanout target telemetry.",
        "- Size gate: final boot image must be `<= 67108864` bytes before any flash attempt.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        f"- Z2 baseline: `{Z2_BASELINE}`",
        "- Candidate type: `gpu-z2-imported-scanout-target-candidate`.",
    ]) + "\n"


def v3325_adapter_source() -> str:
    return _rewrite_v3325_text(previous.v3321_adapter_source())


def _write_candidate_manifest(manifest: dict[str, Any]) -> None:
    (OUT_DIR / "gpu-z2-imported-scanout-target-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "gpu-z2-imported-scanout-target-candidate",
        "boot_image": base.rel(BOOT_IMAGE),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "live_validation_focus": manifest["gpu_z2"]["pass_requirements"],
        "source_report": base.rel(REPORT_PATH),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-gpu-z2-imported-scanout-target-live-validation",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _overlay_preserved_v3325_ramdisk() -> dict[str, Any]:
    saved: dict[str, Any] = {
        name: getattr(previous, name)
        for name in (
            "BASE_BOOT",
            "INIT_BINARY",
            "HELPER_BINARY",
            "ENGINE_BINARY",
            "RAMDISK_CPIO",
            "BOOT_IMAGE",
            "ENGINE_RAMDISK_PATH",
        )
    }
    replacements = {
        "BASE_BOOT": BASE_BOOT,
        "INIT_BINARY": INIT_BINARY,
        "HELPER_BINARY": HELPER_BINARY,
        "ENGINE_BINARY": ENGINE_BINARY,
        "RAMDISK_CPIO": RAMDISK_CPIO,
        "BOOT_IMAGE": BOOT_IMAGE,
        "ENGINE_RAMDISK_PATH": ENGINE_RAMDISK_PATH,
    }
    for name, value in replacements.items():
        setattr(previous, name, value)
    try:
        overlay = previous._overlay_preserved_v3321_ramdisk()
    finally:
        for name, value in saved.items():
            setattr(previous, name, value)
    overlay["mode"] = "preserve-v3321-ramdisk-overlay-v3325-init-helper-engine"
    overlay["base_boot"] = base.rel(BASE_BOOT)
    overlay["overlay_entries"] = [
        "init",
        "bin/a90_android_execns_probe",
        ENGINE_RAMDISK_PATH,
    ]
    return overlay


def _finalize_manifest_after_overlay(
    overlay: dict[str, Any],
    *,
    base_main_completed: bool,
    base_main_error: str | None = None,
) -> None:
    manifest_path = OUT_DIR / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        manifest = {
            "decision": DECISION,
            "cycle": CYCLE,
            "candidate_tag": INIT_BUILD,
            "candidate_type": "gpu-z2-imported-scanout-target-candidate",
            "adoption_state": "pending-gpu-z2-imported-scanout-target-live-validation",
            "boot_image": base.rel(BOOT_IMAGE),
            "init_version": INIT_VERSION,
            "init_build": INIT_BUILD,
            "helper_sha256": base.sha256_file(HELPER_BINARY),
            "helper_flags": [],
            "init_extra_flags": [],
        }
    manifest["decision"] = DECISION
    manifest["cycle"] = CYCLE
    manifest["candidate_tag"] = INIT_BUILD
    manifest["candidate_type"] = "gpu-z2-imported-scanout-target-candidate"
    manifest["adoption_state"] = "pending-gpu-z2-imported-scanout-target-live-validation"
    manifest["boot_image"] = base.rel(BOOT_IMAGE)
    manifest["init_version"] = INIT_VERSION
    manifest["init_build"] = INIT_BUILD
    manifest["boot_sha256"] = overlay["boot_sha256"]
    manifest["ramdisk_sha256"] = overlay["ramdisk_sha256"]
    manifest["ramdisk_overlay"] = overlay
    manifest["base_main_completed"] = base_main_completed
    if base_main_error:
        manifest["base_main_error"] = base_main_error
    else:
        manifest.pop("base_main_error", None)
    for key in ("gpu_d3", "gpu_m0", "gpu_m1", "gpu_m2", "gpu_m3"):
        manifest.pop(key, None)
    manifest["gpu_z2"] = _minimal_gpu_z2_manifest()
    manifest["gpu_z2"]["ramdisk_overlay"] = overlay
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(
        render_report(
            manifest,
            tuple(manifest.get("helper_flags", ())),
            tuple(manifest.get("init_extra_flags", ())),
        ),
        encoding="utf-8",
    )
    _write_candidate_manifest(manifest)


def _postprocess_manifest() -> dict[str, Any]:
    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.pop("base_main_error", None)
    for key in ("gpu_d3", "gpu_m0", "gpu_m1", "gpu_m2", "gpu_m3"):
        manifest.pop(key, None)
    manifest.update({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "gpu-z2-imported-scanout-target-candidate",
        "adoption_state": "pending-gpu-z2-imported-scanout-target-live-validation",
        "gpu_z2": _minimal_gpu_z2_manifest(),
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
    _write_candidate_manifest(manifest)
    return manifest


def _apply_v3325_overrides() -> None:
    previous._apply_v3321_overrides()
    replacements = {
        "CYCLE": CYCLE,
        "INIT_VERSION": INIT_VERSION,
        "INIT_BUILD": INIT_BUILD,
        "BUILD_TAG": BUILD_TAG,
        "DECISION": DECISION,
        "OUT_DIR": OUT_DIR,
        "OBJ_DIR": OBJ_DIR,
        "REPORT_PATH": REPORT_PATH,
        "BOOT_IMAGE": BOOT_IMAGE,
        "BASE_BOOT": BASE_BOOT,
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
        "SFX_STREAM_MARKER": SFX_STREAM_MARKER,
        "SOUND_MODE": SOUND_MODE,
        "AUDIO_CORUN_MODE": SOUND_MODE,
        "SFX_BACKEND_SOURCE": SFX_BACKEND_SOURCE,
        "SDL_MIXER_STUB": SDL_MIXER_STUB,
        "SFX_BACKEND_SOURCE_TEXT": _rewrite_v3325_text(base.SFX_BACKEND_SOURCE_TEXT),
        "REQUIRED_STRINGS": REQUIRED_STRINGS,
        "render_report": render_report,
        "v3210_adapter_source": v3325_adapter_source,
        "_overlay_preserved_v3208_ramdisk": _overlay_preserved_v3325_ramdisk,
        "_postprocess_manifest": _postprocess_manifest,
        "_finalize_manifest_after_overlay": _finalize_manifest_after_overlay,
    }
    for name, value in replacements.items():
        setattr(base, name, value)


def main() -> int:
    _apply_v3325_overrides()
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
