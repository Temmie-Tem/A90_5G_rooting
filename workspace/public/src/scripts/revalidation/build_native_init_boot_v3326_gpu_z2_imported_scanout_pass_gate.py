#!/usr/bin/env python3
"""Build V3326 GPU Z2 imported scanout pass-gate fix."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _workspace_bootstrap import add_legacy_revalidation_path, repo_root

REPO_ROOT = repo_root()
add_legacy_revalidation_path(REPO_ROOT)

from a90harness.evidence import workspace_private_build_path, workspace_private_input_path
import build_native_init_boot_v3325_gpu_z2_imported_scanout_target as previous

base = previous.base

CYCLE = "V3326"
INIT_VERSION = "0.11.94"
INIT_BUILD = "v3326-gpu-z2-imported-scanout-pass-gate"
BUILD_TAG = INIT_BUILD
DECISION = "v3326-gpu-z2-imported-scanout-pass-gate-source-build-pass"

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
OBJ_DIR = OUT_DIR / "obj"
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V3326_GPU_Z2_IMPORTED_SCANOUT_PASS_GATE_SOURCE_BUILD_2026-06-27.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images",
    "boot_linux_v3326_gpu_z2_imported_scanout_pass_gate.img",
    legacy_fallback=False,
)
BASE_BOOT = previous.BOOT_IMAGE
INIT_BINARY = OUT_DIR / "init_v3326_gpu_z2_imported_scanout_pass_gate"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v3326_gpu_z2_imported_scanout_pass_gate.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v618_gpu_z2_imported_scanout_pass_gate"

ENGINE_BINARY = OUT_DIR / "a90_doomgeneric_private_engine_v3326"
ENGINE_ADAPTER_SOURCE = OUT_DIR / "a90_doomgeneric_native_bridge_v3326.c"
ENGINE_ADAPTER_OBJECT = OBJ_DIR / "a90_doomgeneric_native_bridge_v3326.o"
ENGINE_RAMDISK_PATH = "bin/a90_doomgeneric_private_engine_v3326"
ENGINE_REMOTE_PATH = "/" + ENGINE_RAMDISK_PATH
ENGINE_NAME = "doomgeneric-private-link-v3326-gpu-z2-imported-scanout-pass-gate"

FRAME_PATH = "/tmp/a90-doomgeneric-v3326-raw-fallback-frame.xbgr8888"
SHARED_FRAME_PATH = "/tmp/a90-doomgeneric-v3326-shared-frame.bin"
INPUT_STATE_PATH = "/tmp/a90-doomgeneric-v3326-input.state"
INPUT_SOCKET_PATH = "/tmp/a90-doomgeneric-v3326-input.sock"
PACE_SOCKET_PATH = "/tmp/a90-doomgeneric-v3326-pace.sock"
TICK_TELEMETRY_PATH = "/tmp/a90-doomgeneric-v3326-tick-telemetry.txt"
AUDIO_PCM_STREAM_PATH = "/cache/a90-runtime/a90-doomgeneric-v3326-sfx.pcmstream"

FRAME_SCALE = "1:1-demo-hud-large-groups-gpu-z2-imported-scanout-pass-gate"
FRAME_IPC = "shared-mmap-direct-blit-demo-hud-large-groups-gpu-z2-imported-scanout-pass-gate"

SFX_STREAM_MARKER = "a90.doomgeneric.v3326.audio=real-sfx-pcm-stream-gpu-z2-imported-scanout-pass-gate"
SOUND_MODE = "native-doom-sfx-gpu-z2-imported-scanout-pass-gate-v3326"

SFX_BACKEND_SOURCE = OUT_DIR / "a90_doomgeneric_native_sfx_v3326.c"
SDL_MIXER_STUB = OUT_DIR / "SDL_mixer.h"

Z2_COMMAND = previous.Z2_COMMAND


def _rewrite_v3326_text(text: str) -> str:
    replacements = (
        (previous.INIT_VERSION, INIT_VERSION),
        (previous.INIT_BUILD, INIT_BUILD),
        (previous.ENGINE_NAME, ENGINE_NAME),
        (previous.ENGINE_REMOTE_PATH, ENGINE_REMOTE_PATH),
        (previous.SOUND_MODE, SOUND_MODE),
        (previous.SFX_STREAM_MARKER, SFX_STREAM_MARKER),
        (previous.AUDIO_PCM_STREAM_PATH, AUDIO_PCM_STREAM_PATH),
        ("a90-doomgeneric-v3325", "a90-doomgeneric-v3326"),
        ("a90.doomgeneric.v3325", "a90.doomgeneric.v3326"),
        ("v3325", "v3326"),
        ("V3325", "V3326"),
        ("gpu-z2-imported-scanout-target", "gpu-z2-imported-scanout-pass-gate"),
    )
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def _rewrite_v3326_bytes(item: bytes) -> bytes:
    return _rewrite_v3326_text(item.decode("utf-8")).encode("utf-8")


REQUIRED_STRINGS = tuple(_rewrite_v3326_bytes(item) for item in previous.REQUIRED_STRINGS)


def _minimal_gpu_z2_manifest() -> dict[str, Any]:
    manifest = dict(previous._minimal_gpu_z2_manifest())
    manifest["baseline"] = "v3325-imported-target-live-telemetry-pass-gate-bug"
    manifest["pass_gate_fix"] = "remove-result_rc-self-reference-before-final-result-assignment"
    return manifest


def render_report(
    manifest: dict[str, Any],
    helper_flags: tuple[str, ...],
    init_extra_flags: tuple[str, ...],
) -> str:
    boot_image = manifest.get("boot_image", base.rel(BOOT_IMAGE))
    boot_sha = manifest.get("boot_sha256", "")
    return "\n".join([
        "# Native Init V3326 GPU Z2 Imported Scanout Pass Gate Source Build",
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
        "- Fixes the V3325 Z2 imported-target pass gate by removing the self-reference on `summary.result_rc` before the child assigns the final result.",
        "- The render path remains the same: DRM msm scanout GEM -> PRIME fd -> KGSL dma-buf import -> M3 textured monitor graph render -> readback semantic validation, with no KMS copy and no KMS present.",
        "",
        "## V3325 Evidence Behind This Fix",
        "",
        "- V3325 live telemetry already showed the functional proof passed: `ADDFB2=0`, KGSL import/info `0`, `render_rc=0`, `changed_count=691200`, semantic match `64/64`, output-other `0`, and cleanup `0`.",
        "- The only failing field was `gpu.z2.import.result=z2-imported-scanout-render-target-failed` because the pass predicate required `summary.result_rc == 0` while `result_rc` was still initialized to `-EIO`.",
        "",
        "## Validation Contract",
        "",
        f"- Command: `{Z2_COMMAND}`",
        "- PASS requires `gpu.z2.import.result=z2-imported-scanout-render-target-pass`, `changed_count>0`, semantic match count `64`, semantic output-other count `0`, KGSL import success, KMS `ADDFB2` success, no KMS copy, no KMS present, and post-probe `selftest fail=0`.",
        "- No PMIC/GDSC/regulator/GPIO/backlight write, proprietary blob, EGL/GLES/OpenCL, forbidden partition, or raw flash path is introduced.",
        "",
        "## Static Validation",
        "",
        "- `py_compile`: V3326 builder and focused source test.",
        "- Unit tests: V3326 focused source contract, V3325 source contract, and V3321 M3 regression contract.",
        "- Build: AArch64 helper/native-init compile, preserved-ramdisk overlay, boot image pack, SHA256 capture.",
        "- Marker check: generated boot image contains V3326 identity plus Z2 imported scanout target telemetry.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `gpu-z2-imported-scanout-pass-gate-candidate`.",
    ]) + "\n"


def v3326_adapter_source() -> str:
    return _rewrite_v3326_text(previous.v3325_adapter_source())


def _write_candidate_manifest(manifest: dict[str, Any]) -> None:
    (OUT_DIR / "gpu-z2-imported-scanout-pass-gate-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "gpu-z2-imported-scanout-pass-gate-candidate",
        "boot_image": base.rel(BOOT_IMAGE),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "live_validation_focus": manifest["gpu_z2"]["pass_requirements"],
        "source_report": base.rel(REPORT_PATH),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-gpu-z2-imported-scanout-pass-gate-live-validation",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _overlay_preserved_v3326_ramdisk() -> dict[str, Any]:
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
        overlay = previous._overlay_preserved_v3325_ramdisk()
    finally:
        for name, value in saved.items():
            setattr(previous, name, value)
    overlay["mode"] = "preserve-v3325-ramdisk-overlay-v3326-init-helper-engine"
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
            "candidate_type": "gpu-z2-imported-scanout-pass-gate-candidate",
            "adoption_state": "pending-gpu-z2-imported-scanout-pass-gate-live-validation",
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
    manifest["candidate_type"] = "gpu-z2-imported-scanout-pass-gate-candidate"
    manifest["adoption_state"] = "pending-gpu-z2-imported-scanout-pass-gate-live-validation"
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
        "candidate_type": "gpu-z2-imported-scanout-pass-gate-candidate",
        "adoption_state": "pending-gpu-z2-imported-scanout-pass-gate-live-validation",
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


def _apply_v3326_overrides() -> None:
    previous._apply_v3325_overrides()
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
        "SFX_BACKEND_SOURCE_TEXT": _rewrite_v3326_text(base.SFX_BACKEND_SOURCE_TEXT),
        "REQUIRED_STRINGS": REQUIRED_STRINGS,
        "render_report": render_report,
        "v3210_adapter_source": v3326_adapter_source,
        "_overlay_preserved_v3208_ramdisk": _overlay_preserved_v3326_ramdisk,
        "_postprocess_manifest": _postprocess_manifest,
        "_finalize_manifest_after_overlay": _finalize_manifest_after_overlay,
    }
    for name, value in replacements.items():
        setattr(base, name, value)


def main() -> int:
    _apply_v3326_overrides()
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
