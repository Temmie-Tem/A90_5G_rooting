#!/usr/bin/env python3
"""Build V3327 GPU Z3 imported scanout plane-present candidate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _workspace_bootstrap import add_legacy_revalidation_path, repo_root

REPO_ROOT = repo_root()
add_legacy_revalidation_path(REPO_ROOT)

from a90harness.evidence import workspace_private_build_path, workspace_private_input_path
import build_native_init_boot_v3326_gpu_z2_imported_scanout_pass_gate as previous

base = previous.base

CYCLE = "V3327"
INIT_VERSION = "0.11.95"
INIT_BUILD = "v3327-gpu-z3-imported-scanout-plane-present"
BUILD_TAG = INIT_BUILD
DECISION = "v3327-gpu-z3-imported-scanout-plane-present-source-build-pass"

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
OBJ_DIR = OUT_DIR / "obj"
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V3327_GPU_Z3_IMPORTED_SCANOUT_PLANE_PRESENT_SOURCE_BUILD_2026-06-27.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images",
    "boot_linux_v3327_gpu_z3_imported_scanout_plane_present.img",
    legacy_fallback=False,
)
BASE_BOOT = previous.BOOT_IMAGE
INIT_BINARY = OUT_DIR / "init_v3327_gpu_z3_imported_scanout_plane_present"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v3327_gpu_z3_imported_scanout_plane_present.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v619_gpu_z3_imported_scanout_plane_present"

ENGINE_BINARY = OUT_DIR / "a90_doomgeneric_private_engine_v3327"
ENGINE_ADAPTER_SOURCE = OUT_DIR / "a90_doomgeneric_native_bridge_v3327.c"
ENGINE_ADAPTER_OBJECT = OBJ_DIR / "a90_doomgeneric_native_bridge_v3327.o"
ENGINE_RAMDISK_PATH = "bin/a90_doomgeneric_private_engine_v3327"
ENGINE_REMOTE_PATH = "/" + ENGINE_RAMDISK_PATH
ENGINE_NAME = "doomgeneric-private-link-v3327-gpu-z3-imported-scanout-plane-present"

FRAME_PATH = "/tmp/a90-doomgeneric-v3327-raw-fallback-frame.xbgr8888"
SHARED_FRAME_PATH = "/tmp/a90-doomgeneric-v3327-shared-frame.bin"
INPUT_STATE_PATH = "/tmp/a90-doomgeneric-v3327-input.state"
INPUT_SOCKET_PATH = "/tmp/a90-doomgeneric-v3327-input.sock"
PACE_SOCKET_PATH = "/tmp/a90-doomgeneric-v3327-pace.sock"
TICK_TELEMETRY_PATH = "/tmp/a90-doomgeneric-v3327-tick-telemetry.txt"
AUDIO_PCM_STREAM_PATH = "/cache/a90-runtime/a90-doomgeneric-v3327-sfx.pcmstream"

FRAME_SCALE = "1:1-demo-hud-large-groups-gpu-z3-imported-scanout-plane-present"
FRAME_IPC = "shared-mmap-direct-blit-demo-hud-large-groups-gpu-z3-imported-scanout-plane-present"

SFX_STREAM_MARKER = "a90.doomgeneric.v3327.audio=real-sfx-pcm-stream-gpu-z3-imported-scanout-plane-present"
SOUND_MODE = "native-doom-sfx-gpu-z3-imported-scanout-plane-present-v3327"

SFX_BACKEND_SOURCE = OUT_DIR / "a90_doomgeneric_native_sfx_v3327.c"
SDL_MIXER_STUB = OUT_DIR / "SDL_mixer.h"

Z3_COMMAND = (
    "gpu z3-imported-scanout-plane-probe --timeout-ms 60000 "
    "--hold-ms 12000 --materialize-devnode"
)


def _rewrite_v3327_text(text: str) -> str:
    replacements = (
        (previous.INIT_VERSION, INIT_VERSION),
        (previous.INIT_BUILD, INIT_BUILD),
        (previous.ENGINE_NAME, ENGINE_NAME),
        (previous.ENGINE_REMOTE_PATH, ENGINE_REMOTE_PATH),
        (previous.SOUND_MODE, SOUND_MODE),
        (previous.SFX_STREAM_MARKER, SFX_STREAM_MARKER),
        (previous.AUDIO_PCM_STREAM_PATH, AUDIO_PCM_STREAM_PATH),
        ("a90-doomgeneric-v3326", "a90-doomgeneric-v3327"),
        ("a90.doomgeneric.v3326", "a90.doomgeneric.v3327"),
        ("v3326", "v3327"),
        ("V3326", "V3327"),
        ("gpu-z2-imported-scanout-pass-gate", "gpu-z3-imported-scanout-plane-present"),
    )
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def _rewrite_v3327_bytes(item: bytes) -> bytes:
    return _rewrite_v3327_text(item.decode("utf-8")).encode("utf-8")


REQUIRED_STRINGS = tuple(_rewrite_v3327_bytes(item) for item in previous.REQUIRED_STRINGS) + (
    b"z3-imported-scanout-plane-probe",
    b"gpu.z3.scanout.kms_copy_attempted=0",
    b"gpu.z3.scanout.kms_present_attempted=1",
    b"z3-imported-scanout-plane-present-pass",
)


def _minimal_gpu_z3_manifest() -> dict[str, Any]:
    return {
        "baseline": "v3326-z2-imported-scanout-target-live-pass",
        "command": Z3_COMMAND,
        "expected_result": "z3-imported-scanout-plane-present-pass",
        "present_mode": "legacy-overlay-plane-setplane",
        "target": {
            "format": "XBGR8888",
            "width": 960,
            "height": 720,
            "stride": 3840,
        },
        "pass_requirements": [
            "z2-imported-scanout-render-target-pass-equivalent",
            "drm-msm-scanout-gem-addfb2-success",
            "kgsl-dmabuf-import-success",
            "kms-plane-select-success",
            "kms-present-rc-0",
            "kms-copy-attempted-0",
            "hold-ms-positive",
            "post-probe-selftest-fail-0",
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
        "# Native Init V3327 GPU Z3 Imported Scanout Plane Present Source Build",
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
        "- Adds `gpu z3-imported-scanout-plane-probe [--timeout-ms N] [--hold-ms N] [--materialize-devnode]`.",
        "- Reuses the V3326 DRM msm scanout GEM -> PRIME -> KGSL dma-buf imported render target path, then presents the same `ADDFB2` framebuffer directly on an idle XBGR8888 KMS plane using `DRM_IOCTL_MODE_SETPLANE`.",
        "- The probe clears/presents a black primary base, centers the `960x720` imported framebuffer on the panel without a CPU copy, holds it for operator visual confirmation, then disables the plane before cleanup.",
        "",
        "## Validation Contract",
        "",
        f"- Command: `{Z3_COMMAND}`",
        "- PASS requires the Z2 imported render-target proof, KMS plane selection, `kms.present_rc=0`, no KMS copy, positive hold, clean plane disable/RMFB/GEM cleanup, and post-probe `selftest fail=0`.",
        "- No PMIC/GDSC/regulator/GPIO/backlight write, proprietary blob, EGL/GLES/OpenCL, forbidden partition, or raw flash path is introduced.",
        "",
        "## Static Validation",
        "",
        "- `py_compile`: V3327 builder and focused source test.",
        "- Unit tests: V3327 focused source contract plus V3326/V3325 source contracts.",
        "- Build: AArch64 helper/native-init compile, preserved-ramdisk overlay, boot image pack, SHA256 capture.",
        "- Marker check: generated boot image contains V3327 identity plus Z3 imported scanout plane-present telemetry.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `gpu-z3-imported-scanout-plane-present-candidate`.",
    ]) + "\n"


def v3327_adapter_source() -> str:
    return _rewrite_v3327_text(previous.v3326_adapter_source())


def _write_candidate_manifest(manifest: dict[str, Any]) -> None:
    (OUT_DIR / "gpu-z3-imported-scanout-plane-present-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "gpu-z3-imported-scanout-plane-present-candidate",
        "boot_image": base.rel(BOOT_IMAGE),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "live_validation_focus": manifest["gpu_z3"]["pass_requirements"],
        "source_report": base.rel(REPORT_PATH),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-gpu-z3-imported-scanout-plane-present-live-validation",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _overlay_preserved_v3327_ramdisk() -> dict[str, Any]:
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
        overlay = previous._overlay_preserved_v3326_ramdisk()
    finally:
        for name, value in saved.items():
            setattr(previous, name, value)
    overlay["mode"] = "preserve-v3326-ramdisk-overlay-v3327-init-helper-engine"
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
            "candidate_type": "gpu-z3-imported-scanout-plane-present-candidate",
            "adoption_state": "pending-gpu-z3-imported-scanout-plane-present-live-validation",
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
    manifest["candidate_type"] = "gpu-z3-imported-scanout-plane-present-candidate"
    manifest["adoption_state"] = "pending-gpu-z3-imported-scanout-plane-present-live-validation"
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
    for key in ("gpu_d3", "gpu_m0", "gpu_m1", "gpu_m2", "gpu_m3", "gpu_z2"):
        manifest.pop(key, None)
    manifest["gpu_z3"] = _minimal_gpu_z3_manifest()
    manifest["gpu_z3"]["ramdisk_overlay"] = overlay
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
    for key in ("gpu_d3", "gpu_m0", "gpu_m1", "gpu_m2", "gpu_m3", "gpu_z2"):
        manifest.pop(key, None)
    manifest.update({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "gpu-z3-imported-scanout-plane-present-candidate",
        "adoption_state": "pending-gpu-z3-imported-scanout-plane-present-live-validation",
        "gpu_z3": _minimal_gpu_z3_manifest(),
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


def _apply_v3327_overrides() -> None:
    previous._apply_v3326_overrides()
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
        "SFX_BACKEND_SOURCE_TEXT": _rewrite_v3327_text(base.SFX_BACKEND_SOURCE_TEXT),
        "REQUIRED_STRINGS": REQUIRED_STRINGS,
        "render_report": render_report,
        "v3210_adapter_source": v3327_adapter_source,
        "_overlay_preserved_v3208_ramdisk": _overlay_preserved_v3327_ramdisk,
        "_postprocess_manifest": _postprocess_manifest,
        "_finalize_manifest_after_overlay": _finalize_manifest_after_overlay,
    }
    for name, value in replacements.items():
        setattr(base, name, value)


def main() -> int:
    _apply_v3327_overrides()
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
