#!/usr/bin/env python3
"""Build V2972 native-init candidate with A90VSTR2 pal8-rle playback support."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _workspace_bootstrap import repo_root
import build_native_init_boot_v2859_audio_changelog_latest_refresh as v2859
from a90harness.evidence import workspace_private_build_path, workspace_private_input_path

REPO_ROOT = repo_root()

CYCLE = "V2972"
INIT_VERSION = "0.10.58"
INIT_BUILD = "v2972-nyan-pal8-rle-synthetic"
BUILD_TAG = INIT_BUILD
DECISION = "v2972-nyan-pal8-rle-synthetic-source-build-pass"

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
REPORT_PATH = REPO_ROOT / "docs/reports/NATIVE_INIT_V2972_NYAN_PAL8_RLE_SYNTHETIC_SOURCE_BUILD_2026-06-20.md"
BOOT_IMAGE = workspace_private_input_path("boot_images", "boot_linux_v2972_nyan_pal8_rle_synthetic.img", legacy_fallback=False)
INIT_BINARY = OUT_DIR / "init_v2972_nyan_pal8_rle_synthetic"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v2972_nyan_pal8_rle_synthetic.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v497_nyan_pal8_rle_synthetic"

REQUIRED_STRINGS = (
    b"A90 Linux init 0.10.58 (v2972-nyan-pal8-rle-synthetic)",
    b"video.status.version=8",
    b"video.status.nyan_pal8_rle=1",
    b"A90VSTR2",
    b"pal8-rle",
    b"DEMO / NYAN CAT",
    b"video.stream.error=pal8-rle-layout-unsupported",
    b"video.stream.error=stream-palette-invalid",
    b"video.stream.beat_flash.source=%s",
    b"video.stream.pixel_format=%s",
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
        raise RuntimeError(f"missing V2972 boot-image markers: {missing}")
    return [marker.decode("ascii") for marker in REQUIRED_STRINGS]


def render_report(manifest: dict[str, Any],
                  helper_flags: tuple[str, ...],
                  init_extra_flags: tuple[str, ...]) -> str:
    markers = manifest.get("v2972_marker_strings", [])
    marker_lines = [f"- `{marker}`" for marker in markers] if isinstance(markers, list) else []
    bundled = manifest.get("audio_bundled_setcal", {}) if isinstance(manifest.get("audio_bundled_setcal"), dict) else {}
    return "\n".join([
        "# Native Init V2972 Nyan pal8-rle Synthetic Source Build",
        "",
        "## Summary",
        "",
        f"- Cycle: `{CYCLE}`",
        "- Track: active Video playback pipeline / Nyan Cat compact-format enabler.",
        f"- Decision: `{manifest['decision']}`",
        "- Result: PASS",
        "- Device flash: `no` in this build unit.",
        f"- Boot image: `{manifest['boot_image']}`",
        f"- Boot SHA256: `{manifest['boot_sha256']}`",
        f"- Init: `A90 Linux init {manifest['init_version']} ({manifest['init_build']})`",
        "",
        "## Included Delta",
        "",
        "- Bumps `video.status.version` to `8` and advertises `video.status.nyan_pal8_rle=1`.",
        "- Includes the V2971 `A90VSTR2 pal8-rle` parser, palette reader, variable-size frame-record reader, and Player HUD pal8 renderer.",
        "- Keeps the V2963 Bad Apple `mono1` path available for rollback comparison.",
        "- Does not add GPU, Venus, raw DSI, backlight, PMIC, PWM, regulator, GPIO, GDSC, or telemetry write paths.",
        "",
        "## Marker Check",
        "",
        *marker_lines,
        "",
        "## Static Validation",
        "",
        "- Build: AArch64 static native-init compile, helper compile, ramdisk pack, boot image pack, SHA256 capture.",
        "- Marker check: generated boot image contains V2972 identity, status marker, `A90VSTR2`, `pal8-rle`, and Nyan Player HUD title strings.",
        "- Device validation is deferred to the V2972 live unit: flash this exact image, seed a private synthetic pal8-rle loop, play it in Player HUD, then health-check.",
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
        "- Generated streams and boot images remain private/untracked.",
        "- Rollback target remains `v2321-usb-clean-identity-rodata`.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `nyan-pal8-rle-synthetic-candidate`.",
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
        "candidate_type": "nyan-pal8-rle-synthetic-candidate",
        "parent_test_artifact": "v2971-nyan-pal8-rle-decoder-source-build",
        "nyan_pal8_rle": {
            "version": 1,
            "source_unit": "V2972",
            "stream_magic": "A90VSTR2",
            "format": "pal8-rle",
            "live_validation": "pending-v2972",
        },
        "v2972_marker_strings": marker_strings,
        "adoption_state": "pending-synthetic-live-validation",
    })
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(render_report(manifest, tuple(manifest.get("helper_flags", ())), tuple(manifest.get("init_extra_flags", ()))), encoding="utf-8")
    (OUT_DIR / "nyan-pal8-rle-synthetic-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "nyan-pal8-rle-synthetic-candidate",
        "boot_image": str(BOOT_IMAGE.relative_to(REPO_ROOT)),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "source_unit": "V2972",
        "source_report": str(REPORT_PATH.relative_to(REPO_ROOT)),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-synthetic-live-validation",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
