#!/usr/bin/env python3
"""Build V3357 native-init self-dd F0 read-only source-plan rung."""

from __future__ import annotations

import json
from typing import Any

from _workspace_bootstrap import add_legacy_revalidation_path, repo_root

REPO_ROOT = repo_root()
add_legacy_revalidation_path(REPO_ROOT)

from a90harness.evidence import workspace_private_build_path, workspace_private_input_path
import build_native_init_boot_v3355_boot_write_e5_full as previous

base = previous.base
ORIG_PREVIOUS_REWRITE_TEXT = previous._rewrite_v3355_text
ORIG_PREVIOUS_ADAPTER_SOURCE = previous.v3355_adapter_source
ORIG_PREVIOUS_BOOT_AUDIT_MANIFEST = previous._boot_audit_manifest
ORIG_PREVIOUS_OVERLAY = previous._overlay_preserved_v3355_ramdisk
ORIG_PREVIOUS_FINALIZE = previous._finalize_manifest_after_overlay
ORIG_PREVIOUS_POSTPROCESS = previous._postprocess_manifest

CYCLE = "V3357"
INIT_VERSION = "0.11.120"
INIT_BUILD = "v3357-self-dd-f0-plan"
BUILD_TAG = INIT_BUILD
DECISION = "v3357-self-dd-f0-plan-source-build-pass"
EXPECTED_HELPER_MARKER = previous.EXPECTED_HELPER_MARKER
EXPECTED_HELPER_SHA256 = previous.EXPECTED_HELPER_SHA256

_STALE_MANIFEST_KEYS = tuple(
    getattr(previous, "_STALE_MANIFEST_KEYS", None)
    or getattr(previous.previous, "_STALE_MANIFEST_KEYS", None)
    or getattr(previous.previous.previous, "_STALE_MANIFEST_KEYS", ())
)

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
OBJ_DIR = OUT_DIR / "obj"
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V3357_SELF_DD_F0_PLAN_SOURCE_BUILD_2026-07-02.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images",
    "boot_linux_v3357_self_dd_f0_plan.img",
    legacy_fallback=False,
)
BASE_BOOT = previous.BASE_BOOT
INIT_BINARY = OUT_DIR / "init_v3357_self_dd_f0_plan"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v3357_self_dd_f0_plan.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v626_self_dd_f0_plan"

ENGINE_BINARY = OUT_DIR / "a90_doomgeneric_private_engine_v3357"
ENGINE_ADAPTER_SOURCE = OUT_DIR / "a90_doomgeneric_native_bridge_v3357.c"
ENGINE_ADAPTER_OBJECT = OBJ_DIR / "a90_doomgeneric_native_bridge_v3357.o"
ENGINE_RAMDISK_PATH = "bin/a90_doomgeneric_private_engine_v3357"
ENGINE_REMOTE_PATH = "/" + ENGINE_RAMDISK_PATH
ENGINE_NAME = "doomgeneric-private-link-v3357-self-dd-f0-plan"

FRAME_PATH = "/tmp/a90-doomgeneric-v3357-raw-fallback-frame.xbgr8888"
SHARED_FRAME_PATH = "/tmp/a90-doomgeneric-v3357-shared-frame.bin"
INPUT_STATE_PATH = "/tmp/a90-doomgeneric-v3357-input.state"
INPUT_SOCKET_PATH = "/tmp/a90-doomgeneric-v3357-input.sock"
PACE_SOCKET_PATH = "/tmp/a90-doomgeneric-v3357-pace.sock"
TICK_TELEMETRY_PATH = "/tmp/a90-doomgeneric-v3357-tick-telemetry.txt"
AUDIO_PCM_STREAM_PATH = "/cache/a90-runtime/a90-doomgeneric-v3357-sfx.pcmstream"

SFX_BACKEND_SOURCE = OUT_DIR / "a90_doomgeneric_native_sfx_v3357.c"
SDL_MIXER_STUB = OUT_DIR / "SDL_mixer.h"

SERVICE_OBJECT_FWCLASS_BRIDGE_FLAG = previous.SERVICE_OBJECT_FWCLASS_BRIDGE_FLAG
SOFTAP_COMMANDS = tuple(previous.SOFTAP_COMMANDS)


def _rewrite_v3357_text(text: str) -> str:
    text = ORIG_PREVIOUS_REWRITE_TEXT(text)
    replacements = (
        (previous.INIT_VERSION, INIT_VERSION),
        (previous.INIT_BUILD, INIT_BUILD),
        ("0.11.119", INIT_VERSION),
        ("v3355", "v3357"),
        ("V3355", "V3357"),
        ("a90-doomgeneric-v3355", "a90-doomgeneric-v3357"),
        ("a90.doomgeneric.v3355", "a90.doomgeneric.v3357"),
        ("boot_write_e5_full", "self_dd_f0_plan"),
        ("boot-write-e5-full", "self-dd-f0-plan"),
        ("BOOT_WRITE_E5_FULL", "SELF_DD_F0_PLAN"),
    )
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def _rewrite_v3357_bytes(item: bytes) -> bytes:
    return _rewrite_v3357_text(item.decode("utf-8")).encode("utf-8")


FRAME_SCALE = _rewrite_v3357_text(previous.FRAME_SCALE)
FRAME_IPC = _rewrite_v3357_text(previous.FRAME_IPC)
SFX_STREAM_MARKER = _rewrite_v3357_text(previous.SFX_STREAM_MARKER)
SOUND_MODE = _rewrite_v3357_text(previous.SOUND_MODE)

PREVIOUS_REQUIRED_STRINGS = tuple(_rewrite_v3357_bytes(item) for item in previous.REQUIRED_STRINGS)

REQUIRED_STRINGS = PREVIOUS_REQUIRED_STRINGS + (
    b"0.11.120",
    b"v3357-self-dd-f0-plan",
    b"A90BWF0",
    b"boot-flash-plan <candidate-path> <expected-sha256> <expected-version>",
    b"read-only-source-plan would_write=0",
    b"candidate_sha=%s expected_sha_match=%d",
    b"expected_version=%s version_marker_found=%d",
    b"target_full_sha=%s",
    b"changed_chunks=%u changed_bytes=%llu chunk_len=%u",
    b"result=ok source-plan-only",
)


def _boot_audit_manifest() -> dict[str, Any]:
    manifest = ORIG_PREVIOUS_BOOT_AUDIT_MANIFEST()
    manifest["rung"] = "self-dd-F0-read-only-source-plan"
    manifest["scope"] = "post-E5-content-changing-source-plan-read-only"
    manifest["commands"] = [
        "boot-flash-plan <candidate-path> <expected-sha256> <expected-version>",
    ]
    manifest["probe_contract"] = {
        "rung": "F0",
        "cmd_flags": "CMD_NONE (read-only, no boot-partition write)",
        "write_syscall": "none from F0 command",
        "target": "guarded current boot partition plus staged candidate image under approved staging root",
        "safety_gates": "boot fd identity, O_NOFOLLOW candidate open, candidate SHA/version/header/size checks",
        "verify": "before_full_sha plus target_full_sha computed by overlaying candidate bytes onto current 64MiB boot snapshot",
        "risk": "read-only planning; candidate flash still uses checked native_init_flash.py",
    }
    manifest["pass_requirements"] = [
        "version-0.11.120",
        "post-flash-selftest-fail-0",
        "boot-flash-plan-read-only-would-write-0",
        "candidate-sha-match-1",
        "version-marker-found-1",
        "candidate-header-ok",
        "target-full-sha-present",
        "changed-summary-present",
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
        "# Native Init V3357 Self-dd F0 Source-Plan Source Build",
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
        "- Adds `boot-flash-plan <candidate-path> <expected-sha256> <expected-version>` as the "
        "read-only F0 rung after the V3355 E5 full-partition identity pass.",
        "- The command resolves and guards the current boot partition, computes an O_DIRECT "
        "`before_full_sha`, validates a staged candidate image under approved staging roots, checks "
        "the expected SHA/version/header/size, and computes the `target_full_sha` that a later "
        "content-changing rung would write.",
        "- F0 performs no boot-partition write and emits `would_write=0`; F1 remains blocked until "
        "F0 passes live and the policy gate for content-changing self-write is deliberately resolved.",
        "",
        "## Validation Contract",
        "",
        "- PASS requires post-flash `selftest fail=0`, `version` 0.11.120, a staged candidate image, "
        "and `boot-flash-plan` emitting `candidate_sha` with `expected_sha_match=1`, "
        "`version_marker_found=1`, `candidate_header=ok`, `target_full_sha=...`, "
        "`changed_chunks=...`, `would_write=0`, and `result=ok source-plan-only`, then rollback to "
        "`v2321` with `selftest fail=0`.",
        "- This is a source-build preparation only; no live V3357 source-plan result is claimed here.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `self-dd-f0-plan-candidate`.",
    ]) + "\n"


def v3357_adapter_source() -> str:
    return _rewrite_v3357_text(ORIG_PREVIOUS_ADAPTER_SOURCE())


def _write_candidate_manifest(manifest: dict[str, Any]) -> None:
    (OUT_DIR / "self-dd-f0-plan-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "self-dd-f0-plan-candidate",
        "boot_image": base.rel(BOOT_IMAGE),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "helper_sha256": manifest.get("helper_sha256", ""),
        "live_validation_focus": manifest["boot_audit"]["pass_requirements"],
        "source_report": base.rel(REPORT_PATH),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-self-dd-f0-live-validation",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _normalize_manifest_for_v3357(manifest: dict[str, Any]) -> dict[str, Any]:
    manifest.update({
        "decision": DECISION,
        "cycle": CYCLE,
        "candidate_tag": INIT_BUILD,
        "candidate_type": "self-dd-f0-plan-candidate",
        "adoption_state": "pending-self-dd-f0-live-validation",
        "boot_image": base.rel(BOOT_IMAGE),
        "init_version": INIT_VERSION,
        "init_build": INIT_BUILD,
        "boot_audit": _boot_audit_manifest(),
    })
    manifest["helper_flags"] = list(dict.fromkeys([
        *manifest.get("helper_flags", []),
        SERVICE_OBJECT_FWCLASS_BRIDGE_FLAG,
    ]))
    for key in _STALE_MANIFEST_KEYS:
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
    manifest = _normalize_manifest_for_v3357(json.loads(manifest_path.read_text(encoding="utf-8")))
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
    manifest = _normalize_manifest_for_v3357(ORIG_PREVIOUS_POSTPROCESS())
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


def _overlay_preserved_v3357_ramdisk() -> dict[str, Any]:
    overlay = ORIG_PREVIOUS_OVERLAY()
    overlay["mode"] = "preserve-v3335-ramdisk-overlay-v3357-init-helper-engine"
    return overlay


def _patch_v3355_module_for_v3357() -> None:
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
        "v3355_adapter_source": v3357_adapter_source,
        "_rewrite_v3355_text": _rewrite_v3357_text,
        "_rewrite_v3355_bytes": _rewrite_v3357_bytes,
        "_boot_audit_manifest": _boot_audit_manifest,
        "_write_candidate_manifest": _write_candidate_manifest,
        "_overlay_preserved_v3355_ramdisk": _overlay_preserved_v3357_ramdisk,
        "_postprocess_manifest": _postprocess_manifest,
        "_finalize_manifest_after_overlay": _finalize_manifest_after_overlay,
    }
    for name, value in replacements.items():
        setattr(previous, name, value)


def main() -> int:
    _patch_v3355_module_for_v3357()
    return previous.main()


if __name__ == "__main__":
    raise SystemExit(main())
