#!/usr/bin/env python3
"""Build V3319 GPU M2 live system monitor graph probe."""

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
import build_native_init_boot_v3318_gpu_m1_monitor_dashboard as previous

base = previous.base

CYCLE = "V3319"
INIT_VERSION = "0.11.90"
INIT_BUILD = "v3319-gpu-m2-monitor-live-graphs"
BUILD_TAG = INIT_BUILD
DECISION = "v3319-gpu-m2-monitor-live-graphs-source-build-pass"
BOOT_PARTITION_MAX_BYTES = 64 * 1024 * 1024

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
OBJ_DIR = OUT_DIR / "obj"
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V3319_GPU_M2_MONITOR_LIVE_GRAPHS_SOURCE_BUILD_2026-06-27.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images",
    "boot_linux_v3319_gpu_m2_monitor_live_graphs.img",
    legacy_fallback=False,
)
BASE_BOOT = previous.BOOT_IMAGE
INIT_BINARY = OUT_DIR / "init_v3319_gpu_m2_monitor_live_graphs"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v3319_gpu_m2_monitor_live_graphs.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v613_gpu_m2_monitor_live_graphs"

ENGINE_BINARY = OUT_DIR / "a90_doomgeneric_private_engine_v3319"
ENGINE_ADAPTER_SOURCE = OUT_DIR / "a90_doomgeneric_native_bridge_v3319.c"
ENGINE_ADAPTER_OBJECT = OBJ_DIR / "a90_doomgeneric_native_bridge_v3319.o"
ENGINE_RAMDISK_PATH = "bin/a90_doomgeneric_private_engine_v3319"
ENGINE_REMOTE_PATH = "/" + ENGINE_RAMDISK_PATH
ENGINE_NAME = "doomgeneric-private-link-v3319-gpu-m2-monitor-live-graphs"

FRAME_PATH = "/tmp/a90-doomgeneric-v3319-raw-fallback-frame.xbgr8888"
SHARED_FRAME_PATH = "/tmp/a90-doomgeneric-v3319-shared-frame.bin"
INPUT_STATE_PATH = "/tmp/a90-doomgeneric-v3319-input.state"
INPUT_SOCKET_PATH = "/tmp/a90-doomgeneric-v3319-input.sock"
PACE_SOCKET_PATH = "/tmp/a90-doomgeneric-v3319-pace.sock"
TICK_TELEMETRY_PATH = "/tmp/a90-doomgeneric-v3319-tick-telemetry.txt"
AUDIO_PCM_STREAM_PATH = "/cache/a90-runtime/a90-doomgeneric-v3319-sfx.pcmstream"

FRAME_SCALE = "1:1-demo-hud-large-groups-gpu-m2-monitor-live-graphs"
FRAME_IPC = "shared-mmap-direct-blit-demo-hud-large-groups-gpu-m2-monitor-live-graphs"

SFX_STREAM_MARKER = "a90.doomgeneric.v3319.audio=real-sfx-pcm-stream-gpu-m2-monitor-live-graphs"
SOUND_MODE = "native-doom-sfx-gpu-m2-monitor-live-graphs-v3319"

SFX_BACKEND_SOURCE = OUT_DIR / "a90_doomgeneric_native_sfx_v3319.c"
SDL_MIXER_STUB = OUT_DIR / "SDL_mixer.h"

SCOPE = "gpu-m2-live-monitor-graphs-textured-2d"
M2_COMMAND = "gpu m2-monitor-live-graph-probe --frames 12 --interval-ms 200 --timeout-ms 60000 --hold-ms 5000 --materialize-devnode"
M2_NODE_ENUM_BASELINE = "v3316-gpu-m0-system-monitor-node-enum-pass"
M2_SAMPLER_BASELINE = "v3317-gpu-m0-monitor-sampler-live-pass"
M2_DASHBOARD_BASELINE = "v3318-gpu-m1-monitor-dashboard-live-pass"


def _rewrite_v3319_text(text: str) -> str:
    replacements = (
        (previous.INIT_VERSION, INIT_VERSION),
        (previous.INIT_BUILD, INIT_BUILD),
        (previous.ENGINE_NAME, ENGINE_NAME),
        (previous.ENGINE_REMOTE_PATH, ENGINE_REMOTE_PATH),
        (previous.SOUND_MODE, SOUND_MODE),
        (previous.SFX_STREAM_MARKER, SFX_STREAM_MARKER),
        (previous.AUDIO_PCM_STREAM_PATH, AUDIO_PCM_STREAM_PATH),
        ("a90-doomgeneric-v3318", "a90-doomgeneric-v3319"),
        ("a90.doomgeneric.v3318", "a90.doomgeneric.v3319"),
        ("v3318", "v3319"),
        ("V3318", "V3319"),
        ("gpu-m1-monitor-dashboard", "gpu-m2-monitor-live-graphs"),
    )
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def _rewrite_v3319_bytes(item: bytes) -> bytes:
    return _rewrite_v3319_text(item.decode("utf-8")).encode("utf-8")


GPU_M2_MONITOR_MARKERS = (
    b"m2-monitor-live-graph-probe",
    b"monitor-live-graph-probe",
    b"gpu.m2.graph.scope=",
    b"gpu.m2.graph.texture_source=live-monitor-mono1-graph-cpu-gpu-mem-temp",
    b"gpu.m2.graph.blit_mode=kgsl-textured-quad-scale-to-960x720-linear-readback-kms-copy",
    b"gpu.m2.graph.power_write_attempted=0",
    b"gpu.m2.graph.proprietary_blob_attempted=0",
    b"gpu.m2.graph.kgsl_submit_attempted=1",
    b"gpu.m2.graph.kms_present_attempted=1",
    b"gpu.m2.graph.graph_pixels_set=%u",
    b"gpu.m2.graph.cpu.count=%u",
    b"gpu.m2.graph.cluster.count=%u",
    b"gpu.m2.graph.present_rc=%d",
    b"gpu.m2.graph.semantic.match_count=%u",
    b"gpu.m2.graph.result=%s",
    b"monitor-live-graph-pass",
)

REQUIRED_STRINGS = tuple(
    _rewrite_v3319_bytes(item)
    for item in previous.REQUIRED_STRINGS
    if b"gpu.m1.monitor" not in item
    and b"m1-monitor" not in item
    and b"monitor-dashboard" not in item
) + (
    SFX_STREAM_MARKER.encode("ascii"),
    SOUND_MODE.encode("ascii"),
    AUDIO_PCM_STREAM_PATH.encode("ascii"),
    INIT_VERSION.encode("ascii"),
    INIT_BUILD.encode("ascii"),
) + GPU_M2_MONITOR_MARKERS


def _minimal_gpu_m2_manifest() -> dict[str, Any]:
    return {
        "source_baseline": [M2_NODE_ENUM_BASELINE, M2_SAMPLER_BASELINE, M2_DASHBOARD_BASELINE],
        "scope": SCOPE,
        "command": M2_COMMAND,
        "candidate_type": "gpu-m2-monitor-live-graphs-candidate",
        "data_sources": [
            "/sys/devices/system/cpu/cpu*/topology",
            "/sys/devices/system/cpu/cpu*/cpufreq",
            "/proc/stat",
            "/proc/meminfo",
            "/proc/loadavg",
            "/sys/class/kgsl/kgsl-3d0",
            "/sys/class/thermal",
            "/sys/class/power_supply/battery",
        ],
        "cluster_detect_source": "cpufreq/related_cpus plus cpuinfo/scaling max frequency",
        "history_capacity": 16,
        "default_frames": 12,
        "default_interval_ms": 200,
        "default_hold_ms": 5000,
        "default_timeout_ms": 60000,
        "expected_result": "monitor-live-graph-pass",
        "power_write_attempted": False,
        "kgsl_submit_attempted": True,
        "kms_present_attempted": True,
        "proprietary_blob_attempted": False,
        "next_live_validation": [
            "flash-v3319-through-native-init-flash",
            "post-flash-health-check",
            "gpu-m2-monitor-live-graph-probe-default",
            "require-monitor-live-graph-pass",
            "require-presented-frames-12",
            "require-graph-pixels-positive",
            "require-kgsl-submit-attempted",
            "require-cpu-count-8",
            "require-cluster-count-3",
            "require-kms-present-rc-0",
            "require-semantic-match-count-64",
            "post-probe-selftest",
        ],
    }


def render_report(
    manifest: dict[str, Any],
    helper_flags: tuple[str, ...],
    init_extra_flags: tuple[str, ...],
) -> str:
    return "\n".join([
        "# Native Init V3319 GPU M2 Monitor Live Graphs Source Build",
        "",
        "## Summary",
        "",
        f"- Cycle: `{CYCLE}`",
        "- Track: GPU rung 3, M2 GPU-accelerated live system-monitor graphs.",
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
        "- Extends `a90_monitor.c/.h` with a scalar graph series API and mono1 graph-frame renderer for CPU, GPU, memory, and temperature lanes.",
        "- Adds `gpu m2-monitor-live-graph-probe [--frames N] [--interval-ms N] [--timeout-ms N] [--hold-ms N] [--materialize-devnode]`.",
        "- Reuses the proven D3 GPU 2D textured-quad path: CPU builds the live mono1 graph source texture, KGSL samples/scales it to a 960x720 linear target, and KMS presents it.",
        "",
        "## M2 Gate",
        "",
        f"- Command: `{M2_COMMAND}`",
        "- PASS requires `gpu.m2.graph.result=monitor-live-graph-pass`, 12 presented frames, positive graph pixels, semantic match count 64, `present_rc=0`, and `selftest fail=0` after the probe.",
        "- This is a real KGSL submit path (`kgsl_submit_attempted=1`) plus KMS present, with no power/sysfs writes.",
        "",
        "## Safety",
        "",
        "- Monitor telemetry sources are read-only `/proc` and `/sys` reads.",
        "- Live KGSL validation may use the existing G0 firmware-cache/devnode materialization path; no power/display sysfs write is part of M2.",
        "- No backlight/PWM/PMIC/regulator/GDSC/GPIO write, panel re-init, proprietary blob, Wi-Fi connect, DHCP, or ping.",
        "- Boot partition only through `native_init_flash.py` in the live step.",
        "",
        "## Validation",
        "",
        "- `py_compile`: V3319 builder and focused source test.",
        "- `unittest`: V3319 M2 source/dispatch/builder contract.",
        "- Compile: focused AArch64 native-init compile with existing baseline warnings only.",
        "- Build: AArch64 helper/native-init compile, preserved-ramdisk overlay, boot image pack, SHA256 capture.",
        "- Marker check: generated boot image contains V3319 identity plus M2 live-graph telemetry.",
        "- Size gate: final boot image must be `<= 67108864` bytes before any flash attempt.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        f"- Node enum baseline: `{M2_NODE_ENUM_BASELINE}`",
        f"- M0 sampler baseline: `{M2_SAMPLER_BASELINE}`",
        f"- M1 dashboard baseline: `{M2_DASHBOARD_BASELINE}`",
        "- Candidate type: `gpu-m2-monitor-live-graphs-candidate`.",
    ]) + "\n"


def v3319_adapter_source() -> str:
    return _rewrite_v3319_text(previous.v3318_adapter_source())


def _write_candidate_manifest(manifest: dict[str, Any]) -> None:
    (OUT_DIR / "gpu-m2-monitor-live-graphs-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "gpu-m2-monitor-live-graphs-candidate",
        "boot_image": base.rel(BOOT_IMAGE),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "live_validation_focus": manifest["gpu_m2"]["next_live_validation"],
        "source_report": base.rel(REPORT_PATH),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-gpu-m2-monitor-live-graphs-live-validation",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _overlay_preserved_v3319_ramdisk() -> dict[str, Any]:
    if not BASE_BOOT.exists():
        raise FileNotFoundError(f"missing V3319 base boot: {BASE_BOOT}")
    if not INIT_BINARY.exists():
        raise FileNotFoundError(f"missing V3319 init binary: {INIT_BINARY}")
    if not HELPER_BINARY.exists():
        raise FileNotFoundError(f"missing V3319 helper binary: {HELPER_BINARY}")
    if not ENGINE_BINARY.exists():
        raise FileNotFoundError(f"missing V3319 DOOM engine binary: {ENGINE_BINARY}")

    with tempfile.TemporaryDirectory(prefix="a90-v3319-overlay-") as temp_name:
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
            "a90_doomgeneric_private_engine_v3313",
            "a90_doomgeneric_private_engine_v3314",
            "a90_doomgeneric_private_engine_v3315",
            "a90_doomgeneric_private_engine_v3317",
            "a90_doomgeneric_private_engine_v3318",
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
            raise RuntimeError("V3319 base boot mkbootimg args did not include --ramdisk")

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
            f"V3319 boot image too large for boot partition: "
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
        raise RuntimeError(f"missing V3319 overlay ramdisk entries: {missing_entries}")

    return {
        "mode": "preserve-v3318-ramdisk-overlay-v3319-init-helper-engine",
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
            "bin/a90_doomgeneric_private_engine_v3313",
            "bin/a90_doomgeneric_private_engine_v3314",
            "bin/a90_doomgeneric_private_engine_v3315",
            "bin/a90_doomgeneric_private_engine_v3317",
            "bin/a90_doomgeneric_private_engine_v3318",
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
            "candidate_type": "gpu-m2-monitor-live-graphs-candidate",
            "adoption_state": "pending-gpu-m2-monitor-live-graphs-live-validation",
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
    manifest["candidate_type"] = "gpu-m2-monitor-live-graphs-candidate"
    manifest["adoption_state"] = "pending-gpu-m2-monitor-live-graphs-live-validation"
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
    manifest.pop("gpu_d3", None)
    manifest.pop("gpu_m0", None)
    manifest.pop("gpu_m1", None)
    manifest["gpu_m2"] = _minimal_gpu_m2_manifest()
    manifest["gpu_m2"]["ramdisk_overlay"] = overlay
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
    manifest.pop("gpu_d3", None)
    manifest.pop("gpu_m0", None)
    manifest.pop("gpu_m1", None)
    manifest.update({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "gpu-m2-monitor-live-graphs-candidate",
        "adoption_state": "pending-gpu-m2-monitor-live-graphs-live-validation",
        "gpu_m2": _minimal_gpu_m2_manifest(),
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


def _apply_v3319_overrides() -> None:
    previous._apply_v3318_overrides()
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
        "SFX_BACKEND_SOURCE_TEXT": _rewrite_v3319_text(base.SFX_BACKEND_SOURCE_TEXT),
        "REQUIRED_STRINGS": REQUIRED_STRINGS,
        "render_report": render_report,
        "v3210_adapter_source": v3319_adapter_source,
        "_overlay_preserved_v3208_ramdisk": _overlay_preserved_v3319_ramdisk,
        "_postprocess_manifest": _postprocess_manifest,
        "_finalize_manifest_after_overlay": _finalize_manifest_after_overlay,
    }
    for name, value in replacements.items():
        setattr(base, name, value)


def main() -> int:
    _apply_v3319_overrides()
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
