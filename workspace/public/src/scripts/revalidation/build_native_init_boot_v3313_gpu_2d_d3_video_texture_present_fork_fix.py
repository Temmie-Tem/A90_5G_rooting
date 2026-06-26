#!/usr/bin/env python3
"""Build V3313 GPU 2D D3 video texture present fork fix."""

from __future__ import annotations

import json
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from _workspace_bootstrap import add_legacy_revalidation_path, repo_root

REPO_ROOT = repo_root()
add_legacy_revalidation_path(REPO_ROOT)

from a90harness.evidence import workspace_private_build_path, workspace_private_input_path
import build_native_init_boot_v3312_gpu_2d_d3_video_texture_present_probe as previous

base = previous.base

CYCLE = "V3313"
INIT_VERSION = "0.11.85"
INIT_BUILD = "v3313-gpu-2d-d3-video-texture-present-fork-fix"
BUILD_TAG = INIT_BUILD
DECISION = "v3313-gpu-2d-d3-video-texture-present-fork-fix-source-build-pass"
BOOT_PARTITION_MAX_BYTES = 64 * 1024 * 1024

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
OBJ_DIR = OUT_DIR / "obj"
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V3313_GPU_2D_D3_VIDEO_TEXTURE_PRESENT_FORK_FIX_SOURCE_BUILD_2026-06-27.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images",
    "boot_linux_v3313_gpu_2d_d3_video_texture_present_fork_fix.img",
    legacy_fallback=False,
)
BASE_BOOT = previous.BOOT_IMAGE
INIT_BINARY = OUT_DIR / "init_v3313_gpu_2d_d3_video_texture_present_fork_fix"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v3313_gpu_2d_d3_video_texture_present_fork_fix.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v609_gpu_2d_d3_video_texture_present_fork_fix"

ENGINE_BINARY = OUT_DIR / "a90_doomgeneric_private_engine_v3313"
ENGINE_ADAPTER_SOURCE = OUT_DIR / "a90_doomgeneric_native_bridge_v3313.c"
ENGINE_ADAPTER_OBJECT = OBJ_DIR / "a90_doomgeneric_native_bridge_v3313.o"
ENGINE_RAMDISK_PATH = "bin/a90_doomgeneric_private_engine_v3313"
ENGINE_REMOTE_PATH = "/" + ENGINE_RAMDISK_PATH
ENGINE_NAME = "doomgeneric-private-link-v3313-gpu-2d-d3-video-texture-present-fork-fix"

FRAME_PATH = "/tmp/a90-doomgeneric-v3313-raw-fallback-frame.xbgr8888"
SHARED_FRAME_PATH = "/tmp/a90-doomgeneric-v3313-shared-frame.bin"
INPUT_STATE_PATH = "/tmp/a90-doomgeneric-v3313-input.state"
INPUT_SOCKET_PATH = "/tmp/a90-doomgeneric-v3313-input.sock"
PACE_SOCKET_PATH = "/tmp/a90-doomgeneric-v3313-pace.sock"
TICK_TELEMETRY_PATH = "/tmp/a90-doomgeneric-v3313-tick-telemetry.txt"
AUDIO_PCM_STREAM_PATH = "/cache/a90-runtime/a90-doomgeneric-v3313-sfx.pcmstream"

FRAME_SCALE = "1:1-demo-hud-large-groups-gpu-2d-d3-video-texture-present-fork-fix"
FRAME_IPC = "shared-mmap-direct-blit-demo-hud-large-groups-gpu-2d-d3-video-texture-present-fork-fix"

SFX_STREAM_MARKER = "a90.doomgeneric.v3313.audio=real-sfx-pcm-stream-gpu-2d-d3-video-texture-present-fork-fix"
SOUND_MODE = "native-doom-sfx-gpu-2d-d3-video-texture-present-fork-fix-v3313"

SFX_BACKEND_SOURCE = OUT_DIR / "a90_doomgeneric_native_sfx_v3313.c"
SDL_MIXER_STUB = OUT_DIR / "SDL_mixer.h"

SCOPE = "gpu-2d-d3-demo-player-texture-blit-present"
D3_COMMAND = (
    "gpu d3-video-texture-present-probe --preset badapple --frames 60 "
    "--timeout-ms 120000 --materialize-devnode"
)
TEXTURED_FS_SHA256 = previous.TEXTURED_FS_SHA256
D0_REFERENCE = previous.D0_REFERENCE
D1_SHADER_GATE = previous.D1_SHADER_GATE
D1_LIVE_BASELINE = previous.D1_LIVE_BASELINE
D2_LIVE_BASELINE = "v3311-d2-realframe-texture-live-pass"
D3_PRESET_SHA256 = previous.D3_PRESET_SHA256


def _rewrite_v3313_text(text: str) -> str:
    replacements = (
        (previous.INIT_VERSION, INIT_VERSION),
        (previous.INIT_BUILD, INIT_BUILD),
        (previous.ENGINE_NAME, ENGINE_NAME),
        (previous.ENGINE_REMOTE_PATH, ENGINE_REMOTE_PATH),
        (previous.SOUND_MODE, SOUND_MODE),
        (previous.SFX_STREAM_MARKER, SFX_STREAM_MARKER),
        (previous.AUDIO_PCM_STREAM_PATH, AUDIO_PCM_STREAM_PATH),
        ("a90-doomgeneric-v3312", "a90-doomgeneric-v3313"),
        ("a90.doomgeneric.v3312", "a90.doomgeneric.v3313"),
        ("v3312", "v3313"),
        ("V3312", "V3313"),
        ("gpu-2d-d3-video-texture-present-probe", "gpu-2d-d3-video-texture-present-fork-fix"),
    )
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def _rewrite_v3313_bytes(item: bytes) -> bytes:
    return _rewrite_v3313_text(item.decode("utf-8")).encode("utf-8")


GPU_D3_VIDEO_MARKERS = (
    b"d3-video-texture-present-probe",
    b"video-texture-present-probe",
    b"gpu.d3.video.scope=gpu-2d-d3-demo-player-texture-blit-present",
    b"gpu.d3.video.label=GPU D3 VIDEO TEXTURE",
    b"gpu.d3.video.command=gpu d3-video-texture-present-probe --preset badapple --frames %u --timeout-ms %d --materialize-devnode",
    b"gpu.d3.video.texture_source=sd-cache-mono1-expanded-to-rgba8-texture-per-frame",
    b"gpu.d3.video.blit_mode=kgsl-textured-quad-scale-to-960x720-linear-readback-kms-copy",
    b"gpu.d3.video.target=%ux%u stride=%u",
    b"gpu.d3.video.result=%s",
    b"video-texture-present-pass",
    b"gpu.d3.video.presented=%u",
    b"gpu.d3.video.fps_milli=%llu",
    b"gpu.d3.video.timing.gpu_wait.avg_us=%llu",
    b"gpu.d3.video.timing.copy.avg_us=%llu",
    b"gpu.d3.video.changed_total=%llu",
    b"GPU D3 TEXTURE",
    b"BAD APPLE GPU BLIT",
)

REQUIRED_STRINGS = tuple(_rewrite_v3313_bytes(item) for item in previous.REQUIRED_STRINGS) + (
    SFX_STREAM_MARKER.encode("ascii"),
    SOUND_MODE.encode("ascii"),
    AUDIO_PCM_STREAM_PATH.encode("ascii"),
    INIT_VERSION.encode("ascii"),
    INIT_BUILD.encode("ascii"),
) + GPU_D3_VIDEO_MARKERS


def _minimal_gpu_d3_manifest() -> dict[str, Any]:
    return {
        "source_baseline": [D0_REFERENCE, D1_SHADER_GATE, D1_LIVE_BASELINE, D2_LIVE_BASELINE],
        "scope": SCOPE,
        "command": D3_COMMAND,
        "candidate_type": "gpu-2d-d3-video-texture-present-fork-fix-candidate",
        "textured_fs_sha256": TEXTURED_FS_SHA256,
        "source_preset": "badapple",
        "source_sha256": D3_PRESET_SHA256,
        "source_width": 480,
        "source_height": 360,
        "source_format": "mono1",
        "target_width": 960,
        "target_height": 720,
        "target_format": "linear XBGR8888-compatible black/white",
        "render_path": "KGSL textured quad, TILE6_3 MRT, A2D linearize, KMS dumb framebuffer copy",
        "expected_result": "video-texture-present-pass",
        "expected_presented_frames": "greater-than-zero",
        "expected_changed_total": "greater-than-zero",
        "timing_required": [
            "fps_milli",
            "read.avg_us",
            "texture.avg_us",
            "gpu_wait.avg_us",
            "readback.avg_us",
            "copy.avg_us",
            "present.avg_us",
            "total.avg_us",
        ],
        "proprietary_blob_attempted": False,
        "power_write_attempted": False,
        "kms_present_attempted": True,
        "next_live_validation": [
            "flash-v3313-through-native-init-flash",
            "post-flash-health-check",
            "video-cache-preset-badapple-status",
            "gpu-d3-video-texture-present-probe-timeout-guard",
            "require-video-texture-present-pass",
            "require-presented-frames-positive",
            "require-changed-total-positive",
            "require-fps-and-stage-timings",
            "post-probe-selftest-and-dmesg-gpu-fault-filter",
        ],
    }


def render_report(
    manifest: dict[str, Any],
    helper_flags: tuple[str, ...],
    init_extra_flags: tuple[str, ...],
) -> str:
    return "\n".join([
        "# Native Init V3313 GPU 2D D3 Video Texture Present Fork Fix Source Build",
        "",
        "## Summary",
        "",
        f"- Cycle: `{CYCLE}`",
        "- Track: GPU accelerated 2D D3, video texture blit into present path.",
        f"- Decision: `{manifest['decision']}`",
        "- Result: PASS",
        "- Device flash: `no` in this build unit.",
        f"- Boot image: `{manifest['boot_image']}`",
        f"- Boot SHA256: `{manifest['boot_sha256']}`",
        f"- Base boot: `{base.rel(BASE_BOOT)}`",
        f"- Init: `A90 Linux init {manifest['init_version']} ({manifest['init_build']})`",
        "",
        "## Included Delta",
        "",
        "- Adds `gpu d3-video-texture-present-probe` to the native GPU command set.",
        "- Reads the Bad Apple SD-cache mono1 stream frame-by-frame and uses the V3311 texture path as an actual video consumer.",
        "- Reuses one child-owned KGSL session across frames, uploads each source frame as a 480x360 RGBA8 texture, renders a textured quad to a 960x720 target, A2D-linearizes it, copies it into the KMS dumb framebuffer, and presents.",
        "- Fixes the V3312 fork child path so only the parent returns through the shell/A90P1 protocol; the child writes summary telemetry to the pipe and exits.",
        "- Raises the D3 probe timeout ceiling to 120000 ms to match the long video-present validation command.",
        "- Reports presented frames, fps, and per-stage read/texture/GPU-wait/readback/copy/present/total timings.",
        "",
        "## D3 Gate",
        "",
        f"- Source preset: `badapple`, SHA256 `{D3_PRESET_SHA256}`, geometry `480x360 mono1`.",
        "- PASS requires `gpu.d3.video.result=video-texture-present-pass`, `presented>0`, `changed_total>0`, and timing telemetry.",
        "- This first D3 gate is still a recoverable probe path, not a new default menu policy.",
        "",
        "## Safety",
        "",
        "- KGSL and KMS work runs in a timeout-guarded child; the parent can kill the worker on timeout.",
        "- No backlight/PWM/PMIC/regulator/GDSC/GPIO write, panel re-init, proprietary blob, or forbidden partition work.",
        "- Boot partition only through `native_init_flash.py` in the live step.",
        "",
        "## Validation",
        "",
        "- `py_compile`: V3313 builder and focused source test.",
        "- `unittest`: V3313 D3 source contract plus V3311 D2 baseline coverage.",
        "- Build: AArch64 helper/native-init compile, preserved-ramdisk overlay, boot image pack, SHA256 capture.",
        "- Marker check: generated boot image contains V3313 identity plus D3 video texture present telemetry.",
        "- Size gate: final boot image must be `<= 67108864` bytes before any flash attempt.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        f"- Textured FS SHA256: `{TEXTURED_FS_SHA256}`",
        f"- D0 reference: `{D0_REFERENCE}`",
        f"- D1 shader gate: `{D1_SHADER_GATE}`",
        f"- D2 live baseline: `{D2_LIVE_BASELINE}`",
        "- Candidate type: `gpu-2d-d3-video-texture-present-fork-fix-candidate`.",
    ]) + "\n"


def v3313_adapter_source() -> str:
    return _rewrite_v3313_text(previous.v3312_adapter_source())


def _write_candidate_manifest(manifest: dict[str, Any]) -> None:
    (OUT_DIR / "gpu-2d-d3-video-texture-present-fork-fix-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "gpu-2d-d3-video-texture-present-fork-fix-candidate",
        "boot_image": base.rel(BOOT_IMAGE),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "live_validation_focus": manifest["gpu_d3"]["next_live_validation"],
        "source_report": base.rel(REPORT_PATH),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-gpu-2d-d3-live-validation",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _patch_previous_builder_globals() -> list[tuple[Any, str, Any]]:
    replacements = {
        "BOOT_PARTITION_MAX_BYTES": BOOT_PARTITION_MAX_BYTES,
        "BASE_BOOT": BASE_BOOT,
        "BOOT_IMAGE": BOOT_IMAGE,
        "INIT_BINARY": INIT_BINARY,
        "RAMDISK_CPIO": RAMDISK_CPIO,
        "HELPER_BINARY": HELPER_BINARY,
        "ENGINE_BINARY": ENGINE_BINARY,
        "ENGINE_RAMDISK_PATH": ENGINE_RAMDISK_PATH,
    }
    saved: list[tuple[Any, str, Any]] = []
    for name, value in replacements.items():
        saved.append((previous, name, getattr(previous, name)))
        setattr(previous, name, value)
    return saved


def _restore_previous_builder_globals(saved: list[tuple[Any, str, Any]]) -> None:
    for module, name, value in reversed(saved):
        setattr(module, name, value)


def _overlay_preserved_v3313_ramdisk() -> dict[str, Any]:
    if not BASE_BOOT.exists():
        raise FileNotFoundError(f"missing V3313 base boot: {BASE_BOOT}")
    if not INIT_BINARY.exists():
        raise FileNotFoundError(f"missing V3313 init binary: {INIT_BINARY}")
    if not HELPER_BINARY.exists():
        raise FileNotFoundError(f"missing V3313 helper binary: {HELPER_BINARY}")
    if not ENGINE_BINARY.exists():
        raise FileNotFoundError(f"missing V3313 DOOM engine binary: {ENGINE_BINARY}")

    with tempfile.TemporaryDirectory(prefix="a90-v3313-overlay-") as temp_name:
        temp_dir = Path(temp_name)
        unpack_dir = temp_dir / "unpack"
        ramdisk_dir = temp_dir / "ramdisk"
        unpack_dir.mkdir()
        ramdisk_dir.mkdir()

        unpack_args_text = base._run(
            [
                "python3",
                base.THIRD_PARTY_MKBOOTIMG / "unpack_bootimg.py",
                "--boot_img",
                BASE_BOOT,
                "--out",
                unpack_dir,
                "--format=mkbootimg",
            ],
            capture=True,
        ).stdout
        mkboot_args = shlex.split(unpack_args_text)

        with (unpack_dir / "ramdisk").open("rb") as handle:
            subprocess.run(
                ["cpio", "-idm", "--no-absolute-filenames"],
                cwd=ramdisk_dir,
                check=True,
                stdin=handle,
                text=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        shutil.copy2(INIT_BINARY, ramdisk_dir / "init")
        (ramdisk_dir / "init").chmod(0o755)

        bin_dir = ramdisk_dir / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(HELPER_BINARY, bin_dir / "a90_android_execns_probe")
        (bin_dir / "a90_android_execns_probe").chmod(0o755)
        for old_engine in (
            "a90_doomgeneric_private_engine_v3204",
            "a90_doomgeneric_private_engine_v3208",
            "a90_doomgeneric_private_engine_v3210",
            "a90_doomgeneric_private_engine_v3303",
            "a90_doomgeneric_private_engine_v3310",
            "a90_doomgeneric_private_engine_v3311",
            "a90_doomgeneric_private_engine_v3312",
        ):
            (bin_dir / old_engine).unlink(missing_ok=True)
        engine_dest = bin_dir / ENGINE_RAMDISK_PATH.split("/", 1)[1]
        shutil.copy2(ENGINE_BINARY, engine_dest)
        engine_dest.chmod(0o755)

        base._set_reproducible_mtime(ramdisk_dir)

        if RAMDISK_CPIO.exists():
            RAMDISK_CPIO.unlink()
        RAMDISK_CPIO.parent.mkdir(parents=True, exist_ok=True)
        base._run(
            [
                "bash",
                "-lc",
                "find . | LC_ALL=C sort | cpio --reproducible -o -H newc > "
                + shlex.quote(str(RAMDISK_CPIO)),
            ],
            cwd=ramdisk_dir,
        )
        RAMDISK_CPIO.chmod(0o600)

        for index, item in enumerate(mkboot_args):
            if item == "--ramdisk":
                mkboot_args[index + 1] = str(RAMDISK_CPIO)
                break
        else:
            raise RuntimeError("V3313 base boot mkbootimg args did not include --ramdisk")

        if BOOT_IMAGE.exists():
            BOOT_IMAGE.unlink()
        base._run(
            [
                "python3",
                base.THIRD_PARTY_MKBOOTIMG / "mkbootimg.py",
                *mkboot_args,
                "--output",
                BOOT_IMAGE,
            ]
        )
        BOOT_IMAGE.chmod(0o600)

    image_size = BOOT_IMAGE.stat().st_size
    if image_size > BOOT_PARTITION_MAX_BYTES:
        raise RuntimeError(
            f"V3313 boot image too large for boot partition: "
            f"{image_size} > {BOOT_PARTITION_MAX_BYTES}"
        )

    base._v3210_require_strings(BOOT_IMAGE)
    listing = base._run(
        ["bash", "-lc", "cpio -it < " + shlex.quote(str(RAMDISK_CPIO))],
        capture=True,
    ).stdout.splitlines()
    required_entries = {
        "init",
        "bin/a90_android_execns_probe",
        ENGINE_RAMDISK_PATH,
        "a90/audio/manifests/audio-setcal-internal-speaker-safe.manifest",
    }
    missing_entries = sorted(required_entries.difference(listing))
    if missing_entries:
        raise RuntimeError(f"missing V3313 overlay ramdisk entries: {missing_entries}")

    return {
        "mode": "preserve-v3312-ramdisk-overlay-v3313-init-helper-engine",
        "base_boot": base.rel(BASE_BOOT),
        "base_boot_sha256": base.sha256_file(BASE_BOOT),
        "boot_sha256": base.sha256_file(BOOT_IMAGE),
        "boot_image_size": image_size,
        "boot_partition_max_bytes": BOOT_PARTITION_MAX_BYTES,
        "ramdisk_cpio": base.rel(RAMDISK_CPIO),
        "ramdisk_sha256": base.sha256_file(RAMDISK_CPIO),
        "overlay_entries": [
            "init",
            "bin/a90_android_execns_probe",
            ENGINE_RAMDISK_PATH,
        ],
        "removed_obsolete_engines": [
            "bin/a90_doomgeneric_private_engine_v3204",
            "bin/a90_doomgeneric_private_engine_v3208",
            "bin/a90_doomgeneric_private_engine_v3210",
            "bin/a90_doomgeneric_private_engine_v3303",
            "bin/a90_doomgeneric_private_engine_v3310",
            "bin/a90_doomgeneric_private_engine_v3311",
            "bin/a90_doomgeneric_private_engine_v3312",
        ],
    }


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
            "candidate_type": "gpu-2d-d3-video-texture-present-fork-fix-candidate",
            "adoption_state": "pending-gpu-2d-d3-live-validation",
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
    manifest["candidate_type"] = "gpu-2d-d3-video-texture-present-fork-fix-candidate"
    manifest["adoption_state"] = "pending-gpu-2d-d3-live-validation"
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
    manifest["gpu_d3"] = _minimal_gpu_d3_manifest()
    manifest["gpu_d3"]["ramdisk_overlay"] = overlay
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
    manifest.update({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "gpu-2d-d3-video-texture-present-fork-fix-candidate",
        "adoption_state": "pending-gpu-2d-d3-live-validation",
        "gpu_d3": _minimal_gpu_d3_manifest(),
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


def _apply_v3313_overrides() -> None:
    previous._apply_v3312_overrides()
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
        "SFX_BACKEND_SOURCE_TEXT": _rewrite_v3313_text(base.SFX_BACKEND_SOURCE_TEXT),
        "REQUIRED_STRINGS": REQUIRED_STRINGS,
        "render_report": render_report,
        "v3210_adapter_source": v3313_adapter_source,
        "_overlay_preserved_v3208_ramdisk": _overlay_preserved_v3313_ramdisk,
        "_postprocess_manifest": _postprocess_manifest,
        "_finalize_manifest_after_overlay": _finalize_manifest_after_overlay,
    }
    for name, value in replacements.items():
        setattr(base, name, value)


def main() -> int:
    _apply_v3313_overrides()
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
