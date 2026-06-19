#!/usr/bin/env python3
"""Build V2908 native-init candidate with trusted video SD-cache playback."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _workspace_bootstrap import repo_root
import build_native_init_boot_v2859_audio_changelog_latest_refresh as v2859
from a90harness.evidence import workspace_private_build_path, workspace_private_input_path

REPO_ROOT = repo_root()

CYCLE = "V2908"
INIT_VERSION = "0.10.35"
INIT_BUILD = "v2908-video-cache-trust-play"
BUILD_TAG = INIT_BUILD
DECISION = "v2908-video-cache-trust-play-source-build-pass"

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
REPORT_PATH = REPO_ROOT / "docs/reports/NATIVE_INIT_V2908_VIDEO_CACHE_TRUST_PLAY_SOURCE_BUILD_2026-06-20.md"
BOOT_IMAGE = workspace_private_input_path("boot_images", "boot_linux_v2908_video_cache_trust_play.img", legacy_fallback=False)
INIT_BINARY = OUT_DIR / "init_v2908_video_cache_trust_play"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v2908_video_cache_trust_play.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v463_video_cache_trust_play"

REQUIRED_STRINGS = (
    b"A90 Linux init 0.10.35 (v2908-video-cache-trust-play)",
    b"video.status.next_cache=video cache [status|verify|play] SHA256 [--trust-cache] [--present pageflip]",
    b"video.cache.version=1",
    b"/mnt/sdext/a90/runtime/video/cache",
    b"sha256-",
    b"video.cache.stream_size_match=",
    b"video.cache.verify.sha256_match=",
    b"video.cache.play.trust_cache=1",
    b"video.cache.verify.actual_sha256=trust-cache-not-checked",
    b"video.cache.verify.sha256_checked=0",
    b"video.cache.play.requested_present=",
    b"video cache [status|verify|play] SHA256 [--trust-cache]",
    b"kms-dumb-buffer-pageflip",
    b"mono1",
    b"video.stream.frames_total=",
    b"video.stream.dropped_frames=",
)


def configure_base() -> None:
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
        raise RuntimeError(f"missing V2908 boot-image markers: {missing}")
    return [marker.decode("ascii") for marker in REQUIRED_STRINGS]


def render_report(manifest: dict[str, Any], helper_flags: tuple[str, ...], init_extra_flags: tuple[str, ...]) -> str:
    bundled = manifest.get("audio_bundled_setcal", {}) if isinstance(manifest.get("audio_bundled_setcal"), dict) else {}
    markers = manifest.get("v2908_marker_strings", [])
    marker_lines = [f"- `{marker}`" for marker in markers] if isinstance(markers, list) else []
    return "\n".join([
        "# Native Init V2908 Trusted Video SD Cache Playback Source Build",
        "",
        "## Summary",
        "",
        f"- Cycle: `{CYCLE}`",
        "- Track: active Video playback pipeline on existing KMS display.",
        f"- Decision: `{manifest['decision']}`",
        "- Result: PASS",
        "- Device flash: `no` in this build unit.",
        f"- Boot image: `{manifest['boot_image']}`",
        f"- Boot SHA256: `{manifest['boot_sha256']}`",
        f"- Init: `A90 Linux init {manifest['init_version']} ({manifest['init_build']})`",
        "- Parent code unit: V2907 added explicit `video cache play SHA256 --trust-cache` support over the existing `A90VSTR1` stream player.",
        "",
        "## Included Delta",
        "",
        "- Builds the V2907 trusted cache playback command surface into a flashable test image.",
        "- Keeps large video assets on the SD SHA-addressed cache; the boot image carries only player and verification code.",
        "- `video cache status` reports manifest and stream-size state without hashing the multi-GB stream.",
        "- Default `video cache play` still requires a full SHA-256 stream match; `--trust-cache` skips the full re-hash only after manifest and exact stream-size checks.",
        "- Playback still reuses the existing KMS dumb-buffer stream path; no Venus, GPU, raw DSI, backlight, PMIC, PWM, regulator, GPIO, or GDSC path is added.",
        "",
        "## Marker Check",
        "",
        *marker_lines,
        "",
        "## Validation",
        "",
        "- `py_compile`: V2908 builder.",
        "- Build: AArch64 static native-init compile, helper compile, ramdisk pack, boot image pack, SHA256 capture.",
        "- Marker check: generated boot image contains the V2908 init identity, video cache command markers, SD cache path, and retained video stream/pageflip markers.",
        "- Device validation is deferred to V2909: flash this exact image, run `video cache verify` once, then run a bounded `video cache play --trust-cache` A/V-sync slice against the V2900 SD cache SHA, then rollback to `v2321`.",
        "",
        "## Bundled Runtime Metadata",
        "",
        f"- Bundled audio artifact count: `{bundled.get('artifact_count')}`",
        f"- Replay entry count: `{bundled.get('replay_entry_count')}`",
        f"- Native manifest SHA256: `{bundled.get('native_manifest_sha256')}`",
        "",
        "## Safety",
        "",
        "- No device action was performed by this builder.",
        "- This unit changes the command surface only; generated frames, raw streams, and boot images remain private/untracked.",
        "- Rollback target remains `v2321-usb-clean-identity-rodata`.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `video-cache-trust-play-candidate`.",
        "",
    ])


def main() -> int:
    configure_base()
    v2859.render_report = render_report
    rc = v2859.main()
    marker_strings = require_strings(BOOT_IMAGE)
    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "video-cache-trust-play-candidate",
        "parent_test_artifact": "v2907-video-cache-trust-play-host-only",
        "video_cache_trust_play": {
            "version": 1,
            "source_unit": "V2908",
            "parent_unit": "V2907",
            "cache_root": "/mnt/sdext/a90/runtime/video/cache",
            "commands": [
                "video cache status SHA256",
                "video cache verify SHA256",
                "video cache play SHA256 [--trust-cache] [--frames N] [--present setcrtc|pageflip]",
            ],
            "stream_format": "A90VSTR1",
            "large_asset_policy": "pre-rendered streams stay in the SHA-addressed SD-card cache, not inside the boot image",
            "live_validation": "pending",
        },
        "v2908_marker_strings": marker_strings,
        "adoption_state": "pending-live-validation",
        "trust_cache_contract": "requires a prior video cache verify in the validation plan; runtime path emits sha256_checked=0",
    })
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(render_report(manifest, tuple(manifest.get("helper_flags", ())), tuple(manifest.get("init_extra_flags", ()))), encoding="utf-8")
    (OUT_DIR / "video-cache-trust-play-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "video-cache-trust-play-candidate",
        "boot_image": str(BOOT_IMAGE.relative_to(REPO_ROOT)),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "source_unit": "V2908",
        "source_report": str(REPORT_PATH.relative_to(REPO_ROOT)),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-live-validation",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
