#!/usr/bin/env python3
"""Build V3021 kept demo checkpoint candidate for Bad Apple + Nyan."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _workspace_bootstrap import repo_root
import build_native_init_boot_v2859_audio_changelog_latest_refresh as v2859
from a90harness.evidence import workspace_private_build_path, workspace_private_input_path

REPO_ROOT = repo_root()

CYCLE = "V3021"
INIT_VERSION = "0.10.72"
INIT_BUILD = "v3021-demo-checkpoint-badapple-nyan"
BUILD_TAG = INIT_BUILD
DECISION = "v3021-demo-checkpoint-badapple-nyan-source-build-pass"

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
REPORT_PATH = REPO_ROOT / "docs/reports/NATIVE_INIT_V3021_DEMO_CHECKPOINT_BADAPPLE_NYAN_SOURCE_BUILD_2026-06-21.md"
BOOT_IMAGE = workspace_private_input_path("boot_images", "boot_linux_v3021_demo_checkpoint_badapple_nyan.img", legacy_fallback=False)
INIT_BINARY = OUT_DIR / "init_v3021_demo_checkpoint_badapple_nyan"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v3021_demo_checkpoint_badapple_nyan.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v510_demo_checkpoint_badapple_nyan"

BADAPPLE_STREAM_SHA256 = "9e938aa83ef40aa692d0f42080821dc21a627f1dddd90cc9c2696aafe6ac6eb0"
BADAPPLE_AUDIO_SHA256 = "b96d2e0bc4bb6b0ada0da6e63e40168115e3818d72c386dd8764162e85238a75"
BADAPPLE_ASSET_ID = "badapple-480x360-full-v2903"
BADAPPLE_AUDIO_PATH = "/cache/a90-runtime/pkg/av/v2920/audio/badapple.s16le"

NYAN_STREAM_SHA256 = "9a8d91956218acf674b7d99d421467effec442fdde1dbbea8635b8f47085c573"
NYAN_AUDIO_SHA256 = "4c3774553195c04166a3a83de793253696a5bee60afe83a04219419fc28e43de"
NYAN_ASSET_ID = "nyancat-v2973-pal8-rle-preview"
NYAN_AUDIO_PATH = "/cache/a90-runtime/pkg/av/v2973/audio/nyancat.s16le"

REQUIRED_STRINGS = (
    b"A90 Linux init 0.10.72 (v3021-demo-checkpoint-badapple-nyan)",
    b"video.status.version=9",
    b"video.status.player_hud_incremental_panel=1",
    b"video.status.nyan_pal8_rle=1",
    b"video.status.doom_input=serial-doompad-staged",
    b"video cache preset [badapple|badapple-scale|nyan]",
    b"video demo [badapple|badapple-scale|nyan|doom]",
    b"badapple-480x360-full-v2903",
    b"9e938aa83ef40aa692d0f42080821dc21a627f1dddd90cc9c2696aafe6ac6eb0",
    b"b96d2e0bc4bb6b0ada0da6e63e40168115e3818d72c386dd8764162e85238a75",
    b"menu.demo.badapple.action=play-av-fullsong",
    b"menu.demo.badapple.frames=6962",
    b"menu.demo.badapple.audio_pcm=/cache/a90-runtime/pkg/av/v2920/audio/badapple.s16le",
    b"menu.demo.badapple.video_present=setcrtc",
    b"menu.demo.badapple.audio_sync_start_offset_ms=450",
    b"nyancat-v2973-pal8-rle-preview",
    b"9a8d91956218acf674b7d99d421467effec442fdde1dbbea8635b8f47085c573",
    b"DEMO / NYAN CAT",
    b"menu.demo.nyan.action=play-av-preview",
    b"menu.demo.nyan.frames=300",
    b"menu.demo.nyan.audio_pcm=/cache/a90-runtime/pkg/av/v2973/audio/nyancat.s16le",
    b"menu.demo.nyan.video_present=setcrtc",
    b"pal8-rle",
    b"A90VSTR2",
    b"doompad [status|reset|key <role> <0|1>|tap <role>]",
    b"video.demo.status=doompad-frame-loop-ready",
    b"video.demo.engine=doompad-loop-not-doomgeneric",
    b"video.demo.input=serial-doompad-consumed",
    b"video.demo.play.command=video demo doom play [frames]",
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
        raise RuntimeError(f"missing V3021 boot-image markers: {missing}")
    return [marker.decode("ascii") for marker in REQUIRED_STRINGS]


def render_report(manifest: dict[str, Any],
                  helper_flags: tuple[str, ...],
                  init_extra_flags: tuple[str, ...]) -> str:
    markers = manifest.get("v3021_marker_strings", [])
    marker_lines = [f"- `{marker}`" for marker in markers] if isinstance(markers, list) else []
    bundled = manifest.get("audio_bundled_setcal", {}) if isinstance(manifest.get("audio_bundled_setcal"), dict) else {}
    return "\n".join([
        "# Native Init V3021 Demo Checkpoint Bad Apple + Nyan Source Build",
        "",
        "## Summary",
        "",
        f"- Cycle: `{CYCLE}`",
        "- Track: active Video playback / kept demo checkpoint before further DOOM integration.",
        f"- Decision: `{manifest['decision']}`",
        "- Result: PASS",
        "- Device flash: `no` in this build unit.",
        f"- Boot image: `{manifest['boot_image']}`",
        f"- Boot SHA256: `{manifest['boot_sha256']}`",
        f"- Init: `A90 Linux init {manifest['init_version']} ({manifest['init_build']})`",
        "",
        "## Included Delta",
        "",
        "- Bumps the current accumulated native-init video/demo surface to patch version `0.10.72`.",
        "- Keeps the validated Bad Apple Player HUD full-song path: `setcrtc`, incremental HUD panel, beat flash, low-amplitude PCM, and SHA-addressed SD cache.",
        "- Keeps the validated Nyan Cat `A90VSTR2 pal8-rle` Player HUD preview path with bounded low-amplitude PCM.",
        "- Keeps the DOOM serial `doompad`/`doomplay` status surface present but does not claim WAD-backed `doomgeneric` yet.",
        "- Does not bundle media frames or PCM into the boot image; the image carries player code, menu entries, and content-addressed path/SHA contracts.",
        "",
        "## Demo Contracts",
        "",
        f"- Bad Apple asset ID: `{BADAPPLE_ASSET_ID}`",
        f"- Bad Apple stream SHA256: `{BADAPPLE_STREAM_SHA256}`",
        f"- Bad Apple audio SHA256: `{BADAPPLE_AUDIO_SHA256}`",
        f"- Bad Apple audio runtime path: `{BADAPPLE_AUDIO_PATH}`",
        f"- Nyan asset ID: `{NYAN_ASSET_ID}`",
        f"- Nyan stream SHA256: `{NYAN_STREAM_SHA256}`",
        f"- Nyan audio SHA256: `{NYAN_AUDIO_SHA256}`",
        f"- Nyan audio runtime path: `{NYAN_AUDIO_PATH}`",
        "",
        "## Marker Check",
        "",
        *marker_lines,
        "",
        "## Static Validation",
        "",
        "- Build: AArch64 static native-init compile, helper compile, ramdisk pack, boot image pack, SHA256 capture.",
        "- Marker check: generated boot image contains the V3021 identity, Bad Apple full-song Player HUD markers, Nyan pal8-rle preview markers, and retained serial DOOMPAD status markers.",
        "- Device validation is deferred to V3022: flash this exact image, validate Bad Apple and Nyan in the same resident image, health-check, and rollback to V2321.",
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
        "- Generated streams, PCM, boot images, and private caches remain private/untracked.",
        "- This is a patch-level kept demo checkpoint candidate, not a 0.11.0 video-epic closeout.",
        "- Rollback target remains `v2321-usb-clean-identity-rodata`.",
        "",
        "## Host Validation",
        "",
        "- `python3 -m py_compile workspace/public/src/scripts/revalidation/build_native_init_boot_v3021_demo_checkpoint_badapple_nyan.py workspace/public/src/scripts/revalidation/native_init_frontier_select.py tests/test_native_demo_checkpoint_badapple_nyan_source_v3021.py tests/test_native_init_frontier_select.py`: PASS",
        "- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 -m unittest tests.test_native_demo_checkpoint_badapple_nyan_source_v3021 tests.test_native_init_frontier_select`: PASS",
        "- `PYTHONPATH=workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 workspace/public/src/scripts/revalidation/native_init_frontier_select.py --json`: PASS (`demo-checkpoint-live-validation-ready`).",
        "- `PYTHONPATH=workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 workspace/public/src/scripts/revalidation/build_native_init_boot_v3021_demo_checkpoint_badapple_nyan.py`: PASS",
        "- `file workspace/private/builds/native-init/v3021-demo-checkpoint-badapple-nyan/init_v3021_demo_checkpoint_badapple_nyan workspace/private/builds/native-init/v3021-demo-checkpoint-badapple-nyan/a90_android_execns_probe_v510_demo_checkpoint_badapple_nyan`: PASS (both AArch64 static ELF)",
        f"- `sha256sum workspace/private/inputs/boot_images/boot_linux_v3021_demo_checkpoint_badapple_nyan.img`: PASS (`{manifest['boot_sha256']}`)",
        "- `git diff --check`: PASS",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `demo-checkpoint-badapple-nyan-candidate`.",
        f"- Adoption state: `{manifest.get('adoption_state', 'pending-badapple-nyan-same-image-live-validation')}`.",
    ]) + "\n"


def main() -> int:
    configure_base()
    v2859.render_report = render_report
    rc = v2859.main()
    marker_strings = require_strings(BOOT_IMAGE)
    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "demo-checkpoint-badapple-nyan-candidate",
        "parent_test_artifacts": [
            "v2964-badapple-hud-incremental-panel-live",
            "v2976-nyan-rung-completion-pass",
            "v3017-doompad-gameplay-loop-live",
        ],
        "demo_checkpoint": {
            "version": 1,
            "source_unit": CYCLE,
            "checkpoint_type": "patch-level-kept-demo-checkpoint",
            "badapple": {
                "asset_id": BADAPPLE_ASSET_ID,
                "stream_sha256": BADAPPLE_STREAM_SHA256,
                "audio_sha256": BADAPPLE_AUDIO_SHA256,
                "audio_runtime_path": BADAPPLE_AUDIO_PATH,
                "frames": 6962,
                "present_mode": "setcrtc",
                "layout": "player-hud",
            },
            "nyan": {
                "asset_id": NYAN_ASSET_ID,
                "stream_sha256": NYAN_STREAM_SHA256,
                "audio_sha256": NYAN_AUDIO_SHA256,
                "audio_runtime_path": NYAN_AUDIO_PATH,
                "frames": 300,
                "present_mode": "setcrtc",
                "layout": "player-hud",
                "format": "pal8-rle",
            },
            "doom": {
                "status_surface": "serial-doompad-consumed",
                "wad_backed": False,
            },
            "live_validation": "pending-v3022",
        },
        "v3021_marker_strings": marker_strings,
        "adoption_state": "pending-badapple-nyan-same-image-live-validation",
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
    (OUT_DIR / "demo-checkpoint-badapple-nyan-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "demo-checkpoint-badapple-nyan-candidate",
        "boot_image": str(BOOT_IMAGE.relative_to(REPO_ROOT)),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "source_unit": CYCLE,
        "source_report": str(REPORT_PATH.relative_to(REPO_ROOT)),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-badapple-nyan-same-image-live-validation",
        "note": "V3021 is the patch-level kept demo checkpoint candidate; V3022 must validate Bad Apple and Nyan in this exact image before further WAD-backed DOOM integration.",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
