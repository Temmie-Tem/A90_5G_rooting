#!/usr/bin/env python3
"""Build V2876 native-init video page-flip probe candidate.

V2876 keeps the V2874 raw-stride stream reader and adds a bounded
`video flipprobe [frames]` command that exercises DRM_IOCTL_MODE_PAGE_FLIP
plus flip-complete event waits on the existing KMS dumb-buffer display path.
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

CYCLE = "V2876"
INIT_VERSION = "0.10.24"
INIT_BUILD = "v2876-video-flipprobe"
BUILD_TAG = INIT_BUILD
DECISION = "v2876-video-flipprobe-source-build-pass"

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V2876_VIDEO_FLIPPROBE_SOURCE_BUILD_2026-06-19.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images", "boot_linux_v2876_video_flipprobe.img", legacy_fallback=False
)
INIT_BINARY = OUT_DIR / "init_v2876_video_flipprobe"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v2876_video_flipprobe.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v455_video_flipprobe"

REQUIRED_STRINGS = (
    b"video.status.next_flipprobe=video flipprobe [frames<=120]",
    b"video.flipprobe.presented=",
    b"video.flipprobe.flip_events=",
    b"video.flipprobe.path=kms-dumb-buffer-pageflip",
    b"DRM_IOCTL_MODE_PAGE_FLIP",
    b"videoflipprobe",
)


def configure_base_for_v2876() -> None:
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
        raise RuntimeError(f"missing V2876 boot-image markers: {missing}")
    return [marker.decode("ascii") for marker in REQUIRED_STRINGS]


def render_report(manifest: dict[str, Any],
                  helper_flags: tuple[str, ...],
                  init_extra_flags: tuple[str, ...]) -> str:
    bundled = manifest.get("audio_bundled_setcal", {}) if isinstance(manifest.get("audio_bundled_setcal"), dict) else {}
    video = manifest.get("video_command_surface", {}) if isinstance(manifest.get("video_command_surface"), dict) else {}
    marker_strings = manifest.get("v2876_marker_strings", [])
    marker_lines = [f"- `{marker}`" for marker in marker_strings] if isinstance(marker_strings, list) else []
    return "\n".join([
        "# Native Init V2876 Video Page-Flip Probe Source Build",
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
        "- Parent candidate: latest audio/productization builder lineage plus V2874 video stream source state.",
        "",
        "## Included Delta",
        "",
        "- Keeps the V2874 `video stream --manifest ... --video-only` raw-stride reader unchanged.",
        "- Adds `a90_kms_present_pageflip()` as a separate KMS helper that calls `DRM_IOCTL_MODE_PAGE_FLIP` with `DRM_MODE_PAGE_FLIP_EVENT` and waits for a `DRM_EVENT_FLIP_COMPLETE` event on the DRM fd.",
        "- Adds bounded `video flipprobe [frames<=120]`, which primes the CRTC with the existing SETCRTC path, then copies a synthetic full-frame source into the back buffer and presents through page-flip/event waits.",
        "- Reports `video.flipprobe.*` metrics including presented frames, flip event count, last sequence/CRTC/timestamp, fps, MB/s, geometry, stride, and `path=kms-dumb-buffer-pageflip`.",
        "- Leaves `video stream` on the proven SETCRTC present path until a separate live flipprobe validation proves page-flip support on-device.",
        "",
        "## Source / Web Grounding",
        "",
        "- Linux KMS documentation describes page flipping as replacing the scanned-out framebuffer during vertical blanking and optionally returning a completion event: `https://docs.kernel.org/gpu/drm-kms.html`.",
        "- DRM UAPI documents `DRM_EVENT_FLIP_COMPLETE` as the event returned for legacy page flips submitted with `DRM_MODE_PAGE_FLIP_EVENT`: `https://dri.freedesktop.org/docs/drm/gpu/drm-uapi.html`.",
        "- The dvdhrm double-buffered/vsync examples show the expected userspace pattern: draw into the unused buffer, issue page flip, then wait on the DRM fd before reusing buffers: `https://github.com/dvdhrm/docs/blob/master/drm-howto/modeset-vsync.c`.",
        "",
        "## Video Metadata",
        "",
        f"- Version: `{video.get('version')}`",
        f"- Source unit: `{video.get('source_unit')}`",
        f"- Commands: `{', '.join(video.get('commands', [])) if isinstance(video.get('commands'), list) else video.get('commands')}`",
        f"- Flipprobe bound: `{video.get('flipprobe_bound')}`",
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
        "- `py_compile`: V2876 builder.",
        "- Build: AArch64 static native-init compile, helper compile, ramdisk pack with bundled private files, boot image pack, SHA256 capture.",
        "- Marker check: generated boot image contains V2876 page-flip command/report markers.",
        *marker_lines,
        "- `file`: native-init and helper are AArch64 statically linked executables.",
        "- Next live unit should flash this exact image, run `video status`, `hide`, and bounded `video flipprobe`, then rollback to `v2321`.",
        "",
        "## Safety",
        "",
        "- No device action was performed by this builder.",
        "- This unit adds no Venus, GPU/KGSL, raw DSI, panel init, backlight, PMIC, PWM, regulator, GPIO, or GDSC path.",
        "- The probe uses the already-opened DRM/KMS card0 dumb-buffer path and does not alter panel power or DSI init.",
        "- Rollback target remains `v2321-usb-clean-identity-rodata`.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `video-flipprobe-candidate`.",
        "",
    ])


def main() -> int:
    configure_base_for_v2876()
    v2859.render_report = render_report
    rc = v2859.main()

    marker_strings = require_strings(BOOT_IMAGE)
    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "video-flipprobe-candidate",
        "parent_test_artifact": "v2874-video-stream-reader",
        "video_command_surface": {
            "version": 4,
            "source_unit": "V2876",
            "inventory_unit": "V2864",
            "plan_unit": "V2870",
            "commands": [
                "video",
                "video status",
                "video frame",
                "video demo",
                "video anim",
                "video blitbench",
                "video flipprobe",
                "video stream",
            ],
            "frame_patterns": ["bars", "checker", "mono", "0xRRGGBB"],
            "animation_patterns": ["bars", "checker", "pulse"],
            "animation_bounds": {"frames_max": 240, "delay_ms_max": 1000},
            "blitbench_bound": "frames<=240",
            "flipprobe_bound": "frames<=120",
            "stream_format": "A90VSTR1 xbgr8888-raw-stride",
            "stream_frame_bound": "frames<=600",
            "render_path": "kms-dumb-buffer",
            "flip_path": "kms-dumb-buffer-pageflip",
            "pixel_format": "xbgr8888",
            "safety_boundary": "no-venus-no-kgsl-no-raw-dsi-no-power-writes",
            "live_validation": "pending",
        },
        "v2876_marker_strings": marker_strings,
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
    (OUT_DIR / "video-flipprobe-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "video-flipprobe-candidate",
        "boot_image": str(BOOT_IMAGE.relative_to(REPO_ROOT)),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "source_unit": "V2876",
        "plan_unit": "V2870",
        "source_report": str(REPORT_PATH.relative_to(REPO_ROOT)),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-live-validation",
        "note": "V2876 packages bounded KMS page-flip/event probing for rollbackable live validation.",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
