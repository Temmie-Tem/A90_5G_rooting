#!/usr/bin/env python3
"""Build V2847 native-init audio stop-execute candidate.

V2847 keeps the V2845 bundled SET-cal boot-chime package and adds the native
`audio stop --execute` cleanup surface. The stop executor is intentionally
bounded to core route reset plus explicit no-active-session markers; it does not
invent an out-of-band PCM handle or ACDB session.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _workspace_bootstrap import repo_root
import build_native_init_boot_v2845_audio_boot_chime as v2845
from a90harness.evidence import workspace_private_build_path, workspace_private_input_path

REPO_ROOT = repo_root()

CYCLE = "V2847"
INIT_VERSION = "0.10.14"
INIT_BUILD = "v2847-audio-stop-execute"
BUILD_TAG = INIT_BUILD
DECISION = "v2847-audio-stop-execute-source-build-pass"

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V2847_AUDIO_STOP_EXECUTE_SOURCE_BUILD_2026-06-19.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images", "boot_linux_v2847_audio_stop_execute.img", legacy_fallback=False
)
INIT_BINARY = OUT_DIR / "init_v2847_audio_stop_execute"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v2847_audio_stop_execute.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v454_audio_stop_execute"


def configure_base_for_v2847() -> None:
    v2845.CYCLE = CYCLE
    v2845.INIT_VERSION = INIT_VERSION
    v2845.INIT_BUILD = INIT_BUILD
    v2845.BUILD_TAG = BUILD_TAG
    v2845.DECISION = DECISION
    v2845.OUT_DIR = OUT_DIR
    v2845.REPORT_PATH = REPORT_PATH
    v2845.BOOT_IMAGE = BOOT_IMAGE
    v2845.INIT_BINARY = INIT_BINARY
    v2845.RAMDISK_CPIO = RAMDISK_CPIO
    v2845.HELPER_BINARY = HELPER_BINARY


def render_report(manifest: dict[str, Any],
                  helper_flags: tuple[str, ...],
                  init_extra_flags: tuple[str, ...]) -> str:
    bundled = manifest.get("audio_bundled_setcal", {}) if isinstance(manifest.get("audio_bundled_setcal"), dict) else {}
    boot_chime = manifest.get("audio_boot_chime", {}) if isinstance(manifest.get("audio_boot_chime"), dict) else {}
    stop_execute = manifest.get("audio_stop_execute", {}) if isinstance(manifest.get("audio_stop_execute"), dict) else {}
    return "\n".join([
        "# Native Init V2847 Audio Stop Execute Source Build",
        "",
        "## Summary",
        "",
        f"- Cycle: `{CYCLE}`",
        "- Track: post-promotion audio productization / cleanup command surface.",
        f"- Decision: `{manifest['decision']}`",
        "- Result: PASS",
        "- Device flash: `no` in this build unit.",
        f"- Boot image: `{manifest['boot_image']}`",
        f"- Boot SHA256: `{manifest['boot_sha256']}`",
        f"- Init: `A90 Linux init {manifest['init_version']} ({manifest['init_build']})`",
        "- Parent candidate: `v2845-audio-boot-chime`",
        "",
        "## Included Delta",
        "",
        "- Keeps the bundled SET-cal manifest/payload package under `/a90/audio` from V2843/V2845.",
        "- Keeps the compile-time best-effort boot chime hook enabled for candidate continuity.",
        "- Promotes `audio stop --execute` from a refusal to a bounded cleanup command.",
        "- Stop execute reuses the existing `audio route <profile> --reset --layer core` writer.",
        "- Stop execute explicitly avoids fake PCM-handle stop and avoids ACDB deallocate without an active session.",
        "",
        "## Stop Execute Contract",
        "",
        f"- Execute supported: `{int(bool(stop_execute.get('execute_supported')))}`",
        f"- Route reset layer: `{stop_execute.get('route_reset_layer')}`",
        f"- Playback stop mode: `{stop_execute.get('playback_stop_mode')}`",
        f"- SET-cal deallocate mode: `{stop_execute.get('setcal_deallocate_mode')}`",
        f"- Live validation state: `{stop_execute.get('live_validation')}`",
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
        "- `unittest`: stop-execute source contract and build wrapper tests.",
        "- Build: AArch64 static native-init compile, helper compile, ramdisk pack with bundled private files, boot image pack, SHA256 capture.",
        "- Next live unit should flash this exact image, run `audio stop internal-speaker-safe --execute`, verify route-reset markers, and rollback to `v2321`.",
        "",
        "## Safety",
        "",
        "- No device action was performed by this builder.",
        "- Stop execute is bounded to the already-validated core route reset path.",
        "- No blind smart-amp boost, SP-bypass, or ACDB deallocate without a live session is introduced.",
        "- Private raw payloads are not committed; they are only copied into the private generated boot image.",
        "- Rollback target remains `v2321-usb-clean-identity-rodata`.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `audio-productization-stop-execute-candidate`.",
        "",
    ])


def main() -> int:
    configure_base_for_v2847()
    v2845.render_report = render_report
    rc = v2845.main()

    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "audio-productization-stop-execute-candidate",
        "parent_test_artifact": "v2845-audio-boot-chime",
        "audio_stop_execute": {
            "execute_supported": True,
            "route_reset_layer": "core",
            "route_reset_command": "audio route internal-speaker-safe --reset --layer core",
            "playback_stop_mode": "no-active-pcm-handle",
            "setcal_deallocate_mode": "no-active-setcal-session",
            "live_validation": "pending",
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
    (OUT_DIR / "audio-stop-execute-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "audio-productization-stop-execute-candidate",
        "boot_image": str(BOOT_IMAGE.relative_to(REPO_ROOT)),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "stop_execute_supported": True,
        "stop_execute_route_reset_layer": "core",
        "boot_chime_enabled": True,
        "bundled_prefix": v2845.v2843.BUNDLED_PREFIX,
        "bundled_remote_manifest": v2845.v2843.BUNDLED_REMOTE_MANIFEST,
        "source_report": str(REPORT_PATH.relative_to(REPO_ROOT)),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-live-validation",
        "note": "V2847 adds bounded audio stop execute cleanup on top of V2845; live validation is a separate unit.",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
