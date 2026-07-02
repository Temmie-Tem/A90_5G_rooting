#!/usr/bin/env python3
"""Build V3355 native-init §0.2 E5 full-partition identity rung."""

from __future__ import annotations

import json
from typing import Any

from _workspace_bootstrap import add_legacy_revalidation_path, repo_root

REPO_ROOT = repo_root()
add_legacy_revalidation_path(REPO_ROOT)

from a90harness.evidence import workspace_private_build_path, workspace_private_input_path
import build_native_init_boot_v3354_boot_write_e4_header as previous

base = previous.base
ORIG_PREVIOUS_REWRITE_TEXT = previous._rewrite_v3354_text
ORIG_PREVIOUS_ADAPTER_SOURCE = previous.v3354_adapter_source
ORIG_PREVIOUS_BOOT_AUDIT_MANIFEST = previous._boot_audit_manifest
ORIG_PREVIOUS_OVERLAY = previous._overlay_preserved_v3354_ramdisk
ORIG_PREVIOUS_FINALIZE = previous._finalize_manifest_after_overlay
ORIG_PREVIOUS_POSTPROCESS = previous._postprocess_manifest

CYCLE = "V3355"
INIT_VERSION = "0.11.119"
INIT_BUILD = "v3355-boot-write-e5-full"
BUILD_TAG = INIT_BUILD
DECISION = "v3355-boot-write-e5-full-source-build-pass"
EXPECTED_HELPER_MARKER = previous.EXPECTED_HELPER_MARKER
EXPECTED_HELPER_SHA256 = previous.EXPECTED_HELPER_SHA256

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
OBJ_DIR = OUT_DIR / "obj"
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V3355_BOOT_WRITE_E5_FULL_SOURCE_BUILD_2026-07-02.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images",
    "boot_linux_v3355_boot_write_e5_full.img",
    legacy_fallback=False,
)
BASE_BOOT = previous.BASE_BOOT
INIT_BINARY = OUT_DIR / "init_v3355_boot_write_e5_full"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v3355_boot_write_e5_full.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v626_boot_write_e5_full"

ENGINE_BINARY = OUT_DIR / "a90_doomgeneric_private_engine_v3355"
ENGINE_ADAPTER_SOURCE = OUT_DIR / "a90_doomgeneric_native_bridge_v3355.c"
ENGINE_ADAPTER_OBJECT = OBJ_DIR / "a90_doomgeneric_native_bridge_v3355.o"
ENGINE_RAMDISK_PATH = "bin/a90_doomgeneric_private_engine_v3355"
ENGINE_REMOTE_PATH = "/" + ENGINE_RAMDISK_PATH
ENGINE_NAME = "doomgeneric-private-link-v3355-boot-write-e5-full"

FRAME_PATH = "/tmp/a90-doomgeneric-v3355-raw-fallback-frame.xbgr8888"
SHARED_FRAME_PATH = "/tmp/a90-doomgeneric-v3355-shared-frame.bin"
INPUT_STATE_PATH = "/tmp/a90-doomgeneric-v3355-input.state"
INPUT_SOCKET_PATH = "/tmp/a90-doomgeneric-v3355-input.sock"
PACE_SOCKET_PATH = "/tmp/a90-doomgeneric-v3355-pace.sock"
TICK_TELEMETRY_PATH = "/tmp/a90-doomgeneric-v3355-tick-telemetry.txt"
AUDIO_PCM_STREAM_PATH = "/cache/a90-runtime/a90-doomgeneric-v3355-sfx.pcmstream"

SFX_BACKEND_SOURCE = OUT_DIR / "a90_doomgeneric_native_sfx_v3355.c"
SDL_MIXER_STUB = OUT_DIR / "SDL_mixer.h"

SERVICE_OBJECT_FWCLASS_BRIDGE_FLAG = previous.SERVICE_OBJECT_FWCLASS_BRIDGE_FLAG
SOFTAP_COMMANDS = tuple(previous.SOFTAP_COMMANDS)


def _rewrite_v3355_text(text: str) -> str:
    text = ORIG_PREVIOUS_REWRITE_TEXT(text)
    replacements = (
        (previous.INIT_VERSION, INIT_VERSION),
        (previous.INIT_BUILD, INIT_BUILD),
        ("0.11.118", INIT_VERSION),
        ("v3354", "v3355"),
        ("V3354", "V3355"),
        ("a90-doomgeneric-v3354", "a90-doomgeneric-v3355"),
        ("a90.doomgeneric.v3354", "a90.doomgeneric.v3355"),
        ("boot_write_e4_header", "boot_write_e5_full"),
        ("boot-write-e4-header", "boot-write-e5-full"),
        ("BOOT_WRITE_E4_HEADER", "BOOT_WRITE_E5_FULL"),
    )
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def _rewrite_v3355_bytes(item: bytes) -> bytes:
    return _rewrite_v3355_text(item.decode("utf-8")).encode("utf-8")


FRAME_SCALE = _rewrite_v3355_text(previous.FRAME_SCALE)
FRAME_IPC = _rewrite_v3355_text(previous.FRAME_IPC)
SFX_STREAM_MARKER = _rewrite_v3355_text(previous.SFX_STREAM_MARKER)
SOUND_MODE = _rewrite_v3355_text(previous.SOUND_MODE)

PREVIOUS_REQUIRED_STRINGS = tuple(_rewrite_v3355_bytes(item) for item in previous.REQUIRED_STRINGS)

REQUIRED_STRINGS = PREVIOUS_REQUIRED_STRINGS + (
    b"0.11.119",
    b"v3355-boot-write-e5-full",
    b"A90BWE5",
    b"boot-write-e5 <token>",
    b"BOOT-WRITE-PROBE-E5-FULL-IDENTITY",
    b"full-partition-64mib-identity-stream",
    b"source_sha=%s source_match_before=%d",
    b"target_off=0 len=%llu chunk_len=%u expected_chunks=%u",
    b"pwrite_count=%u pwrite=ok fsync=ok",
    b"region_match_all=%d",
)


def _boot_audit_manifest() -> dict[str, Any]:
    manifest = ORIG_PREVIOUS_BOOT_AUDIT_MANIFEST()
    manifest["rung"] = "boot-write-probe-E5-full-partition-identity"
    manifest["scope"] = "0.2-write-probe-E5-full-64MiB-boot-partition-identity"
    manifest["commands"] = ["boot-write-e5 BOOT-WRITE-PROBE-E5-FULL-IDENTITY"]
    manifest["probe_contract"] = {
        "rung": "E5",
        "token": "BOOT-WRITE-PROBE-E5-FULL-IDENTITY",
        "cmd_flags": "CMD_DANGEROUS (menu-settle required)",
        "write_syscall": "64 pwrite calls of 1MiB chunks, covering the full 64MiB boot partition",
        "target": "entire boot partition, offset 0..64MiB",
        "safety_gates": "fail-closed Android magic/header parse, source SHA equals O_DIRECT pre-SHA, identity on every fd, O_NOFOLLOW",
        "verify": "O_DIRECT full-partition SHA before/after plus region_match_all=full_match",
        "risk": "highest identity rung: UFS-tear residual can corrupt any boot LBA; externally recoverable boot-only",
    }
    manifest["pass_requirements"] = [
        "version-0.11.119",
        "post-flash-selftest-fail-0",
        "boot-write-e5-token-and-menu-gated",
        "boot-write-e5-target-offset-0-len-67108864",
        "boot-write-e5-source-match-before-1",
        "boot-write-e5-pwrite-count-64",
        "boot-write-e5-region-match-all-1",
        "boot-write-e5-full-match-1",
        "rollback-v2321-selftest-fail-0",
    ]
    return manifest


def render_report(
    manifest: dict[str, Any],
    helper_flags: tuple[str, ...],
    init_extra_flags: tuple[str, ...],
) -> str:
    boot_image = manifest.get("boot_image", base.rel(BOOT_IMAGE))
    boot_sha = manifest.get("boot_sha256", "")
    helper_sha = manifest.get("helper_sha256", "")
    return "\n".join([
        "# Native Init V3355 §0.2 Write-Probe E5 Full Source Build",
        "",
        f"- Cycle: `{CYCLE}`",
        f"- Decision: `{DECISION}`",
        f"- Init: `A90 Linux init {INIT_VERSION} ({INIT_BUILD})`",
        f"- Boot image: `{boot_image}`",
        f"- Boot SHA256: `{boot_sha}`",
        f"- Helper SHA256: `{helper_sha}`",
        f"- Base boot: `{base.rel(BASE_BOOT)}`",
        "",
        "## Change",
        "",
        "- Adds `boot-write-e5 <token>` after the V3354 E4 live pass. E5 streams the entire 64MiB "
        "boot partition back to itself in 1MiB identity chunks.",
        "- Before any write, the command verifies Android boot magic/header parse, computes an "
        "O_DIRECT full-partition SHA, computes a normal-read source SHA, and requires those SHAs to "
        "match. It then performs 64 identity `pwrite` calls, fsyncs once, and compares the O_DIRECT "
        "full-partition SHA after the write.",
        "- This is the highest-consequence identity rung. It still changes no bytes on completion, "
        "but an interrupted write can corrupt any boot LBA; rollback/recovery remains external and "
        "boot-only.",
        "",
        "## Validation Contract",
        "",
        "- PASS requires post-flash `selftest fail=0`, `version` 0.11.119, and after `hide`, "
        "`boot-write-e5 BOOT-WRITE-PROBE-E5-FULL-IDENTITY` emitting `target_off=0`, "
        "`len=67108864`, `expected_chunks=64`, `source_match_before=1`, `pwrite_count=64`, "
        "`region_match_all=1`, `full_match=1`, then rollback to `v2321` with `selftest fail=0`.",
        "- This is a source-build preparation only; no live V3355 write is claimed here.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `boot-write-e5-full-candidate`.",
    ]) + "\n"


def v3355_adapter_source() -> str:
    return _rewrite_v3355_text(ORIG_PREVIOUS_ADAPTER_SOURCE())


def _write_candidate_manifest(manifest: dict[str, Any]) -> None:
    (OUT_DIR / "boot-write-e5-full-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "boot-write-e5-full-candidate",
        "boot_image": base.rel(BOOT_IMAGE),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "helper_sha256": manifest.get("helper_sha256", ""),
        "live_validation_focus": manifest["boot_audit"]["pass_requirements"],
        "source_report": base.rel(REPORT_PATH),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-boot-write-e5-full-live-validation",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _normalize_manifest_for_v3355(manifest: dict[str, Any]) -> dict[str, Any]:
    manifest.update({
        "decision": DECISION,
        "cycle": CYCLE,
        "candidate_tag": INIT_BUILD,
        "candidate_type": "boot-write-e5-full-candidate",
        "adoption_state": "pending-boot-write-e5-full-live-validation",
        "boot_image": base.rel(BOOT_IMAGE),
        "init_version": INIT_VERSION,
        "init_build": INIT_BUILD,
        "boot_audit": _boot_audit_manifest(),
    })
    manifest["helper_flags"] = list(dict.fromkeys([
        *manifest.get("helper_flags", []),
        SERVICE_OBJECT_FWCLASS_BRIDGE_FLAG,
    ]))
    for key in previous.previous._STALE_MANIFEST_KEYS:
        manifest.pop(key, None)
    return manifest


def _finalize_manifest_after_overlay(
    overlay: dict[str, Any],
    *,
    base_main_completed: bool,
    base_main_error: str | None = None,
) -> None:
    ORIG_PREVIOUS_FINALIZE(
        overlay,
        base_main_completed=base_main_completed,
        base_main_error=base_main_error,
    )
    manifest_path = OUT_DIR / "manifest.json"
    manifest = _normalize_manifest_for_v3355(json.loads(manifest_path.read_text(encoding="utf-8")))
    if base_main_error:
        manifest["base_main_error"] = base_main_error
    else:
        manifest.pop("base_main_error", None)
    manifest["boot_audit"]["ramdisk_overlay"] = overlay
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
    manifest = _normalize_manifest_for_v3355(ORIG_PREVIOUS_POSTPROCESS())
    manifest_path = OUT_DIR / "manifest.json"
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


def _overlay_preserved_v3355_ramdisk() -> dict[str, Any]:
    overlay = ORIG_PREVIOUS_OVERLAY()
    overlay["mode"] = "preserve-v3335-ramdisk-overlay-v3355-init-helper-engine"
    return overlay


def _patch_v3354_module_for_v3355() -> None:
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
        "SFX_BACKEND_SOURCE": SFX_BACKEND_SOURCE,
        "SDL_MIXER_STUB": SDL_MIXER_STUB,
        "REQUIRED_STRINGS": REQUIRED_STRINGS,
        "SOFTAP_COMMANDS": SOFTAP_COMMANDS,
        "render_report": render_report,
        "v3354_adapter_source": v3355_adapter_source,
        "_rewrite_v3354_text": _rewrite_v3355_text,
        "_rewrite_v3354_bytes": _rewrite_v3355_bytes,
        "_boot_audit_manifest": _boot_audit_manifest,
        "_write_candidate_manifest": _write_candidate_manifest,
        "_overlay_preserved_v3354_ramdisk": _overlay_preserved_v3355_ramdisk,
        "_postprocess_manifest": _postprocess_manifest,
        "_finalize_manifest_after_overlay": _finalize_manifest_after_overlay,
    }
    for name, value in replacements.items():
        setattr(previous, name, value)


def main() -> int:
    _patch_v3354_module_for_v3355()
    return previous.main()


if __name__ == "__main__":
    raise SystemExit(main())
