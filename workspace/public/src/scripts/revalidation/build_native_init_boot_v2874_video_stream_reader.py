#!/usr/bin/env python3
"""Build V2874 native-init video stream reader candidate.

V2874 keeps the V2871 full-frame blit path and adds the first raw-stride
A90VSTR1 frame-stream reader: `video stream --manifest PATH --video-only`.
Live validation is a separate V-iteration.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _workspace_bootstrap import repo_root
import build_native_init_boot_v2859_audio_changelog_latest_refresh as v2859
from a90harness.evidence import workspace_private_build_path, workspace_private_input_path

REPO_ROOT = repo_root()

CYCLE = "V2874"
INIT_VERSION = "0.10.23"
INIT_BUILD = "v2874-video-stream-reader"
BUILD_TAG = INIT_BUILD
DECISION = "v2874-video-stream-reader-source-build-pass"

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V2874_VIDEO_STREAM_READER_SOURCE_BUILD_2026-06-19.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images", "boot_linux_v2874_video_stream_reader.img", legacy_fallback=False
)
INIT_BINARY = OUT_DIR / "init_v2874_video_stream_reader"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v2874_video_stream_reader.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v455_video_stream_reader"

REQUIRED_STRINGS = (
    b"video.status.kms.stride=",
    b"video.status.kms.map_size=",
    b"video.status.kms.pixel_format=xbgr8888",
    b"video.status.next_blitbench=video blitbench [frames<=240]",
    b"video.status.next_stream=video stream --manifest PATH --video-only [--frames N]",
    b"video.stream.presented=",
    b"video.stream.sha256_checked=1",
    b"video.stream.pixel_format=xbgr8888",
    b"video stream --manifest PATH --video-only",
    b"A90VSTR1",
    b"videostream",
)


def configure_base_for_v2874() -> None:
    v2859.CYCLE = CYCLE
    v2859.INIT_VERSION = INIT_VERSION
    v2859.INIT_BUILD = INIT_BUILD
    v2859.BUILD_TAG = BUILD_TAG
    v2859.DECISION = DECISION
    v2859.OUT_DIR = OUT_DIR
    v2859.REPORT_PATH = REPORT_PATH
    v2859.BOOT_IMAGE = BOOT_IMAGE
    v2859.INIT_BINARY = INIT_BINARY
    v2859.RAMDISK_CPIO = RAMDISK_CPIO
    v2859.HELPER_BINARY = HELPER_BINARY


def require_strings(path: Path) -> list[str]:
    data = path.read_bytes()
    missing = [marker.decode("ascii", errors="replace") for marker in REQUIRED_STRINGS if marker not in data]
    if missing:
        raise RuntimeError(f"missing V2874 boot-image markers: {missing}")
    return [marker.decode("ascii") for marker in REQUIRED_STRINGS]


def render_report(manifest: dict[str, Any],
                  helper_flags: tuple[str, ...],
                  init_extra_flags: tuple[str, ...]) -> str:
    bundled = manifest.get("audio_bundled_setcal", {}) if isinstance(manifest.get("audio_bundled_setcal"), dict) else {}
    video = manifest.get("video_command_surface", {}) if isinstance(manifest.get("video_command_surface"), dict) else {}
    marker_strings = manifest.get("v2874_marker_strings", [])
    marker_lines = [f"- `{marker}`" for marker in marker_strings] if isinstance(marker_strings, list) else []
    return "\n".join([
        "# Native Init V2874 Video Stream Reader Source Build",
        "",
        "## Summary",
        "",
        f"- Cycle: `{CYCLE}`",
        "- Track: active Video playback pipeline on the existing KMS display.",
        f"- Decision: `{manifest['decision']}`",
        "- Result: PASS",
        "- Device flash: `no` in this build unit.",
        f"- Boot image: `{manifest['boot_image']}`",
        f"- Boot SHA256: `{manifest['boot_sha256']}`",
        f"- Init: `A90 Linux init {manifest['init_version']} ({manifest['init_build']})`",
        "- Parent candidate: `v2871-video-blitbench` source plus the current audio/productization baseline builder lineage.",
        "",
        "## Included Delta",
        "",
        "- Keeps the V2871 `video blitbench` full-frame KMS copy primitive and metadata surface.",
        "- Adds strict `video stream --manifest PATH --video-only [--frames N]` command parsing.",
        "- Adds a bounded manifest parser for the V2873 `video` object and rejects absolute paths, `..`, unknown format, invalid geometry, invalid SHA-256, and excessive frame counts.",
        "- Adds the V1 `A90VSTR1` raw-stride stream reader with header and per-frame record validation.",
        "- Verifies the stream SHA-256 before playback using the existing native `a90_helper_sha256_file()` helper.",
        "- Presents frames through the existing KMS dumb-buffer path and reports `video.stream.*` metrics: frames, bytes, elapsed ns, fps_milli, mbps_milli, late frames, max late ns, geometry, stride, frame bytes, and pixel format.",
        "- Adds `prepare_video_stream_v2874.py` to generate private synthetic `A90VSTR1` fixtures for later live validation; generated payloads remain private and uncommitted.",
        "",
        "## Video Metadata",
        "",
        f"- Version: `{video.get('version')}`",
        f"- Source unit: `{video.get('source_unit')}`",
        f"- Commands: `{', '.join(video.get('commands', [])) if isinstance(video.get('commands'), list) else video.get('commands')}`",
        f"- Stream format: `{video.get('stream_format')}`",
        f"- Stream frame bound: `{video.get('stream_frame_bound')}`",
        f"- Safety boundary: `{video.get('safety_boundary')}`",
        "",
        "## Bundled Runtime Metadata",
        "",
        f"- Bundled audio artifact count: `{bundled.get('artifact_count')}`",
        f"- Replay entry count: `{bundled.get('replay_entry_count')}`",
        f"- Native manifest SHA256: `{bundled.get('native_manifest_sha256')}`",
        "- Raw SET-cal bytes remain private; this report records only counts and hashes.",
        "",
        "## Static Validation",
        "",
        "- `py_compile`: V2874 builder and V2874 synthetic stream generator.",
        "- Build: AArch64 static native-init compile, helper compile, ramdisk pack with bundled private files, boot image pack, SHA256 capture.",
        "- Marker check: generated boot image contains V2874 `video.status.next_stream`, `video.stream.*`, `A90VSTR1`, and `videostream` markers.",
        *marker_lines,
        "- `file`: native-init and helper are AArch64 statically linked executables.",
        "- Private fixture generation: synthetic `A90VSTR1` writer is available for the next live unit; no generated frame payload is committed.",
        "",
        "## Safety",
        "",
        "- No device action was performed by this builder.",
        "- This unit adds no Venus, GPU/KGSL, raw DSI, panel init, backlight, PMIC, PWM, regulator, GPIO, or GDSC path.",
        "- The stream reader only opens regular private files and writes to the already-proven KMS dumb-buffer path.",
        "- Rollback target remains `v2321-usb-clean-identity-rodata`.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `video-stream-reader-candidate`.",
        "",
    ])


def main() -> int:
    configure_base_for_v2874()
    v2859.render_report = render_report
    rc = v2859.main()

    marker_strings = require_strings(BOOT_IMAGE)
    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "video-stream-reader-candidate",
        "parent_test_artifact": "v2859-audio-changelog-latest-refresh",
        "video_command_surface": {
            "version": 3,
            "source_unit": "V2874",
            "inventory_unit": "V2864",
            "plan_unit": "V2873",
            "commands": [
                "video",
                "video status",
                "video frame",
                "video demo",
                "video anim",
                "video blitbench",
                "video stream",
            ],
            "frame_patterns": ["bars", "checker", "mono", "0xRRGGBB"],
            "animation_patterns": ["bars", "checker", "pulse"],
            "animation_bounds": {"frames_max": 240, "delay_ms_max": 1000},
            "blitbench_bound": "frames<=240",
            "stream_format": "A90VSTR1 xbgr8888-raw-stride",
            "stream_frame_bound": "frames<=600",
            "render_path": "kms-dumb-buffer",
            "pixel_format": "xbgr8888",
            "safety_boundary": "no-venus-no-kgsl-no-raw-dsi-no-power-writes",
            "live_validation": "pending",
        },
        "v2874_marker_strings": marker_strings,
        "adoption_state": "pending-live-validation",
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
    (OUT_DIR / "video-stream-reader-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "video-stream-reader-candidate",
        "boot_image": str(BOOT_IMAGE.relative_to(REPO_ROOT)),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "source_unit": "V2874",
        "plan_unit": "V2873",
        "source_report": str(REPORT_PATH.relative_to(REPO_ROOT)),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-live-validation",
        "note": "V2874 packages the A90VSTR1 raw-stride video stream reader for rollbackable live validation.",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
