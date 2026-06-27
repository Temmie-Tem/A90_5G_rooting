#!/usr/bin/env python3
"""Build V3329 GPU Z3 atomic imported scanout plane-present candidate."""

from __future__ import annotations

import json
from typing import Any

from _workspace_bootstrap import add_legacy_revalidation_path, repo_root

REPO_ROOT = repo_root()
add_legacy_revalidation_path(REPO_ROOT)

from a90harness.evidence import workspace_private_build_path, workspace_private_input_path
import build_native_init_boot_v3328_gpu_z3_kms_master_fd_plane_present as previous

base = previous.base

CYCLE = "V3329"
INIT_VERSION = "0.11.97"
INIT_BUILD = "v3329-gpu-z3-atomic-plane-present"
BUILD_TAG = INIT_BUILD
DECISION = "v3329-gpu-z3-atomic-plane-present-source-build-pass"

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
OBJ_DIR = OUT_DIR / "obj"
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V3329_GPU_Z3_ATOMIC_PLANE_PRESENT_SOURCE_BUILD_2026-06-27.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images",
    "boot_linux_v3329_gpu_z3_atomic_plane_present.img",
    legacy_fallback=False,
)
BASE_BOOT = previous.BOOT_IMAGE
INIT_BINARY = OUT_DIR / "init_v3329_gpu_z3_atomic_plane_present"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v3329_gpu_z3_atomic_plane_present.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v621_gpu_z3_atomic_plane_present"

ENGINE_BINARY = OUT_DIR / "a90_doomgeneric_private_engine_v3329"
ENGINE_ADAPTER_SOURCE = OUT_DIR / "a90_doomgeneric_native_bridge_v3329.c"
ENGINE_ADAPTER_OBJECT = OBJ_DIR / "a90_doomgeneric_native_bridge_v3329.o"
ENGINE_RAMDISK_PATH = "bin/a90_doomgeneric_private_engine_v3329"
ENGINE_REMOTE_PATH = "/" + ENGINE_RAMDISK_PATH
ENGINE_NAME = "doomgeneric-private-link-v3329-gpu-z3-atomic-plane-present"

FRAME_PATH = "/tmp/a90-doomgeneric-v3329-raw-fallback-frame.xbgr8888"
SHARED_FRAME_PATH = "/tmp/a90-doomgeneric-v3329-shared-frame.bin"
INPUT_STATE_PATH = "/tmp/a90-doomgeneric-v3329-input.state"
INPUT_SOCKET_PATH = "/tmp/a90-doomgeneric-v3329-input.sock"
PACE_SOCKET_PATH = "/tmp/a90-doomgeneric-v3329-pace.sock"
TICK_TELEMETRY_PATH = "/tmp/a90-doomgeneric-v3329-tick-telemetry.txt"
AUDIO_PCM_STREAM_PATH = "/cache/a90-runtime/a90-doomgeneric-v3329-sfx.pcmstream"

FRAME_SCALE = "1:1-demo-hud-large-groups-gpu-z3-atomic-plane-present"
FRAME_IPC = "shared-mmap-direct-blit-demo-hud-large-groups-gpu-z3-atomic-plane-present"

SFX_STREAM_MARKER = "a90.doomgeneric.v3329.audio=real-sfx-pcm-stream-gpu-z3-atomic-plane-present"
SOUND_MODE = "native-doom-sfx-gpu-z3-atomic-plane-present-v3329"

SFX_BACKEND_SOURCE = OUT_DIR / "a90_doomgeneric_native_sfx_v3329.c"
SDL_MIXER_STUB = OUT_DIR / "SDL_mixer.h"

Z3_COMMAND = previous.Z3_COMMAND


def _rewrite_v3329_text(text: str) -> str:
    replacements = (
        (previous.INIT_VERSION, INIT_VERSION),
        (previous.INIT_BUILD, INIT_BUILD),
        (previous.ENGINE_NAME, ENGINE_NAME),
        (previous.ENGINE_REMOTE_PATH, ENGINE_REMOTE_PATH),
        (previous.SOUND_MODE, SOUND_MODE),
        (previous.SFX_STREAM_MARKER, SFX_STREAM_MARKER),
        (previous.AUDIO_PCM_STREAM_PATH, AUDIO_PCM_STREAM_PATH),
        ("a90-doomgeneric-v3328", "a90-doomgeneric-v3329"),
        ("a90.doomgeneric.v3328", "a90.doomgeneric.v3329"),
        ("v3328", "v3329"),
        ("V3328", "V3329"),
        ("gpu-z3-kms-master-fd-plane-present", "gpu-z3-atomic-plane-present"),
    )
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def _rewrite_v3329_bytes(item: bytes) -> bytes:
    return _rewrite_v3329_text(item.decode("utf-8")).encode("utf-8")


REQUIRED_STRINGS = tuple(_rewrite_v3329_bytes(item) for item in previous.REQUIRED_STRINGS) + (
    b"gpu.z3.scanout.kms.atomic_props_rc=",
    b"gpu.z3.scanout.kms.atomic_commit_rc=",
    b"z3-imported-scanout-plane-present-pass",
)


def _minimal_gpu_z3_manifest() -> dict[str, Any]:
    manifest = dict(previous._minimal_gpu_z3_manifest())
    manifest["baseline"] = "v3328-z3-plane-present-setplane-einval"
    manifest["plane_present_fix"] = "atomic-plane-commit-first-with-legacy-setplane-fallback"
    return manifest


def render_report(
    manifest: dict[str, Any],
    helper_flags: tuple[str, ...],
    init_extra_flags: tuple[str, ...],
) -> str:
    boot_image = manifest.get("boot_image", base.rel(BOOT_IMAGE))
    boot_sha = manifest.get("boot_sha256", "")
    return "\n".join([
        "# Native Init V3329 GPU Z3 Atomic Plane Present Source Build",
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
        "- Fixes the V3328 Z3 legacy `SETPLANE` `-22` path by fetching plane atomic properties and trying `DRM_IOCTL_MODE_ATOMIC` first.",
        "- Keeps the V3328 KMS master fd fix and leaves legacy `DRM_IOCTL_MODE_SETPLANE` as a fallback if atomic commit is unavailable.",
        "- The GPU render/import path remains unchanged: DRM msm scanout GEM -> PRIME -> KGSL dma-buf import -> monitor graph render -> semantic readback -> direct plane present.",
        "",
        "## Validation Contract",
        "",
        f"- Command: `{Z3_COMMAND}`",
        "- PASS requires the Z2 imported render-target proof, KMS plane selection, `kms.present_rc=0`, no KMS copy, positive hold, clean plane disable/RMFB/GEM cleanup, and post-probe `selftest fail=0`.",
        "- No PMIC/GDSC/regulator/GPIO/backlight write, proprietary blob, EGL/GLES/OpenCL, forbidden partition, or raw flash path is introduced.",
        "",
        "## Static Validation",
        "",
        "- `py_compile`: V3329 builder and focused source test.",
        "- Unit tests: V3329 focused source contract plus Z3/Z2 regression contracts.",
        "- Build: AArch64 helper/native-init compile, preserved-ramdisk overlay, boot image pack, SHA256 capture.",
        "- Marker check: generated boot image contains V3329 identity plus Z3 atomic plane-present telemetry.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `gpu-z3-atomic-plane-present-candidate`.",
    ]) + "\n"


def v3329_adapter_source() -> str:
    return _rewrite_v3329_text(previous.v3328_adapter_source())


def _write_candidate_manifest(manifest: dict[str, Any]) -> None:
    (OUT_DIR / "gpu-z3-atomic-plane-present-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "gpu-z3-atomic-plane-present-candidate",
        "boot_image": base.rel(BOOT_IMAGE),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "live_validation_focus": manifest["gpu_z3"]["pass_requirements"],
        "source_report": base.rel(REPORT_PATH),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-gpu-z3-atomic-plane-present-live-validation",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _overlay_preserved_v3329_ramdisk() -> dict[str, Any]:
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
        overlay = previous._overlay_preserved_v3328_ramdisk()
    finally:
        for name, value in saved.items():
            setattr(previous, name, value)
    overlay["mode"] = "preserve-v3328-ramdisk-overlay-v3329-init-helper-engine"
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
            "candidate_type": "gpu-z3-atomic-plane-present-candidate",
            "adoption_state": "pending-gpu-z3-atomic-plane-present-live-validation",
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
    manifest["candidate_type"] = "gpu-z3-atomic-plane-present-candidate"
    manifest["adoption_state"] = "pending-gpu-z3-atomic-plane-present-live-validation"
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
        "candidate_type": "gpu-z3-atomic-plane-present-candidate",
        "adoption_state": "pending-gpu-z3-atomic-plane-present-live-validation",
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


def _apply_v3329_overrides() -> None:
    previous._apply_v3328_overrides()
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
        "SFX_BACKEND_SOURCE_TEXT": _rewrite_v3329_text(base.SFX_BACKEND_SOURCE_TEXT),
        "REQUIRED_STRINGS": REQUIRED_STRINGS,
        "render_report": render_report,
        "v3210_adapter_source": v3329_adapter_source,
        "_overlay_preserved_v3208_ramdisk": _overlay_preserved_v3329_ramdisk,
        "_postprocess_manifest": _postprocess_manifest,
        "_finalize_manifest_after_overlay": _finalize_manifest_after_overlay,
    }
    for name, value in replacements.items():
        setattr(base, name, value)


def main() -> int:
    _apply_v3329_overrides()
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
