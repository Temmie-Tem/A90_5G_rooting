#!/usr/bin/env python3
"""Build V2845 native-init audio boot-chime candidate.

V2845 keeps the V2843 bundled SET-cal ramdisk package and enables the
compile-time best-effort boot chime hook. This is source/build only; live boot
audibility and rollback validation remain a separate V-iteration.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _workspace_bootstrap import repo_root
import build_native_init_boot_v2843_audio_bundled_setcal as v2843
from a90harness.evidence import workspace_private_build_path, workspace_private_input_path

REPO_ROOT = repo_root()

CYCLE = "V2845"
INIT_VERSION = "0.10.13"
INIT_BUILD = "v2845-audio-boot-chime"
BUILD_TAG = INIT_BUILD
DECISION = "v2845-audio-boot-chime-source-build-pass"

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V2845_AUDIO_BOOT_CHIME_SOURCE_BUILD_2026-06-19.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images", "boot_linux_v2845_audio_boot_chime.img", legacy_fallback=False
)
INIT_BINARY = OUT_DIR / "init_v2845_audio_boot_chime"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v2845_audio_boot_chime.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v454_audio_boot_chime"
BOOT_CHIME_FLAG = "-DAUDIO_CHIME_BOOT_AUTOPLAY_DEFAULT=1"

_original_patch_ramdisk_and_flags = v2843.patch_ramdisk_and_flags


def configure_v2843_module_for_v2845() -> None:
    v2843.CYCLE = CYCLE
    v2843.INIT_VERSION = INIT_VERSION
    v2843.INIT_BUILD = INIT_BUILD
    v2843.BUILD_TAG = BUILD_TAG
    v2843.DECISION = DECISION
    v2843.OUT_DIR = OUT_DIR
    v2843.REPORT_PATH = REPORT_PATH
    v2843.BOOT_IMAGE = BOOT_IMAGE
    v2843.INIT_BINARY = INIT_BINARY
    v2843.RAMDISK_CPIO = RAMDISK_CPIO
    v2843.HELPER_BINARY = HELPER_BINARY


def patch_ramdisk_and_flags_with_boot_chime(ramdisk_files: dict[str, Path]) -> None:
    _original_patch_ramdisk_and_flags(ramdisk_files)
    base = v2843.v2807.v2799.v2789.v2334.base_module().base
    flags = tuple(base.EXTRA_INIT_FLAGS)
    if BOOT_CHIME_FLAG not in flags:
        base.EXTRA_INIT_FLAGS = (*flags, BOOT_CHIME_FLAG)


def render_report(manifest: dict[str, object],
                  helper_flags: tuple[str, ...],
                  init_extra_flags: tuple[str, ...]) -> str:
    bundled = manifest.get("audio_bundled_setcal", {}) if isinstance(manifest.get("audio_bundled_setcal"), dict) else {}
    boot_chime = manifest.get("audio_boot_chime", {}) if isinstance(manifest.get("audio_boot_chime"), dict) else {}
    return "\n".join([
        "# Native Init V2845 Audio Boot Chime Source Build",
        "",
        "## Summary",
        "",
        f"- Cycle: `{CYCLE}`",
        "- Track: post-promotion audio productization / best-effort boot chime.",
        f"- Decision: `{manifest['decision']}`",
        "- Result: PASS",
        "- Device flash: `no` in this build unit.",
        f"- Boot image: `{manifest['boot_image']}`",
        f"- Boot SHA256: `{manifest['boot_sha256']}`",
        f"- Init: `A90 Linux init {manifest['init_version']} ({manifest['init_build']})`",
        f"- Parent candidate: `{boot_chime.get('parent_candidate', 'v2843-audio-bundled-setcal')}`",
        "",
        "## Included Delta",
        "",
        "- Keeps the bundled SET-cal manifest/payload package under `/a90/audio` from V2843.",
        "- Enables `AUDIO_CHIME_BOOT_AUTOPLAY_DEFAULT=1` for this build only.",
        "- PID1 starts the chime through a best-effort child before entering the shell; failures are logged and do not block boot.",
        "- The child delegates to the existing bounded `audio chime --execute` path with amplitude `80` milli and duration `1200` ms.",
        "",
        "## Bundled Runtime Metadata",
        "",
        f"- Bundled artifact count: `{bundled.get('artifact_count')}`",
        f"- Replay entry count: `{bundled.get('replay_entry_count')}`",
        f"- Native manifest SHA256: `{bundled.get('native_manifest_sha256')}`",
        f"- Boot chime enabled: `{int(bool(boot_chime.get('enabled')))}`",
        f"- Boot chime best-effort: `{int(bool(boot_chime.get('best_effort')))}`",
        f"- Boot chime blocks boot: `{int(bool(boot_chime.get('blocks_boot')))}`",
        "- Raw SET-cal bytes remain private; this report records only counts and hashes.",
        "",
        "## Validation",
        "",
        "- `py_compile`: builder and focused tests.",
        "- `unittest`: boot-chime source/build contract tests.",
        "- Build: AArch64 static native-init compile, helper compile, ramdisk pack with bundled private files, boot image pack, SHA256 capture.",
        "- Next live unit should flash this exact image and verify boot health, chime worker markers, and rollback to `v2321`.",
        "",
        "## Safety",
        "",
        "- No device action was performed by this builder.",
        "- The boot hook is compile-time gated and best-effort; it does not wait for playback and does not block PID1 shell readiness.",
        "- No forbidden partitions are touched by the build.",
        "- Private raw payloads are not committed; they are only copied into the private generated boot image.",
        "- Rollback target remains `v2321-usb-clean-identity-rodata`.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `audio-productization-boot-chime-candidate`.",
        "",
    ])


def main() -> int:
    configure_v2843_module_for_v2845()
    v2843.patch_ramdisk_and_flags = patch_ramdisk_and_flags_with_boot_chime
    v2843.render_report = render_report
    rc = v2843.main()

    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "audio-productization-boot-chime-candidate",
        "parent_test_artifact": "v2843-audio-bundled-setcal",
        "audio_boot_chime": {
            "enabled": True,
            "best_effort": True,
            "blocks_boot": False,
            "compile_flag": BOOT_CHIME_FLAG,
            "parent_candidate": "v2843-audio-bundled-setcal",
            "manual_chime_validated_by": "V2844",
            "default_amplitude_milli": 80,
            "default_duration_ms": 1200,
        },
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
    (OUT_DIR / "audio-boot-chime-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "audio-productization-boot-chime-candidate",
        "boot_image": str(BOOT_IMAGE.relative_to(REPO_ROOT)),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "boot_chime_enabled": True,
        "boot_chime_best_effort": True,
        "boot_chime_blocks_boot": False,
        "bundled_prefix": v2843.BUNDLED_PREFIX,
        "bundled_remote_manifest": v2843.BUNDLED_REMOTE_MANIFEST,
        "source_report": str(REPORT_PATH.relative_to(REPO_ROOT)),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-live-validation",
        "note": "V2845 enables best-effort boot chime on top of the V2843 bundled SET-cal candidate; live boot validation is a separate unit.",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
