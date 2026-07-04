#!/usr/bin/env python3
"""Build V3396 native-init boot image with the WSTA persistent-state screen."""

from __future__ import annotations

import json
from typing import Any

from _workspace_bootstrap import add_legacy_revalidation_path, repo_root

REPO_ROOT = repo_root()
add_legacy_revalidation_path(REPO_ROOT)

from a90harness.evidence import workspace_private_build_path, workspace_private_input_path
import build_native_init_boot_v3395_wsta_screenapp_live as previous

base = previous.base
ORIG_V3395_REQUIRED_STRINGS = previous.REQUIRED_STRINGS
ORIG_V3395_BOOT_AUDIT_MANIFEST = previous._boot_audit_manifest
ORIG_V3395_NORMALIZE_MANIFEST = previous._normalize_manifest_for_v3395
ORIG_V3395_REWRITE_TEXT = previous._rewrite_v3395_text

CYCLE = "V3396"
INIT_VERSION = "0.11.152"
INIT_BUILD = "v3396-wsta-persistent-state-screen"
BUILD_TAG = INIT_BUILD
DECISION = "v3396-wsta-persistent-state-screen-source-build"
EXPECTED_HELPER_MARKER = previous.EXPECTED_HELPER_MARKER
EXPECTED_HELPER_SHA256 = previous.EXPECTED_HELPER_SHA256

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
OBJ_DIR = OUT_DIR / "obj"
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V3396_WSTA_PERSISTENT_STATE_SCREEN_SOURCE_BUILD_2026-07-04.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images",
    "boot_linux_v3396_wsta_persistent_state_screen.img",
    legacy_fallback=False,
)
BASE_BOOT = previous.BOOT_IMAGE
INIT_BINARY = OUT_DIR / "init_v3396_wsta_persistent_state_screen"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v3396_wsta_persistent_state_screen.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v638_wsta_persistent_state_screen"

ENGINE_BINARY = OUT_DIR / "a90_doomgeneric_private_engine_v3396"
ENGINE_ADAPTER_SOURCE = OUT_DIR / "a90_doomgeneric_native_bridge_v3396.c"
ENGINE_ADAPTER_OBJECT = OBJ_DIR / "a90_doomgeneric_native_bridge_v3396.o"
ENGINE_RAMDISK_PATH = "bin/a90_doomgeneric_private_engine_v3396"
ENGINE_REMOTE_PATH = "/" + ENGINE_RAMDISK_PATH
ENGINE_NAME = "doomgeneric-private-link-v3396-wsta-persistent-state-screen"

FRAME_PATH = "/tmp/a90-doomgeneric-v3396-raw-fallback-frame.xbgr8888"
SHARED_FRAME_PATH = "/tmp/a90-doomgeneric-v3396-shared-frame.bin"
INPUT_STATE_PATH = "/tmp/a90-doomgeneric-v3396-input.state"
INPUT_SOCKET_PATH = "/tmp/a90-doomgeneric-v3396-input.sock"
PACE_SOCKET_PATH = "/tmp/a90-doomgeneric-v3396-pace.sock"
TICK_TELEMETRY_PATH = "/tmp/a90-doomgeneric-v3396-tick-telemetry.txt"
AUDIO_PCM_STREAM_PATH = "/cache/a90-runtime/a90-doomgeneric-v3396-sfx.pcmstream"

SFX_BACKEND_SOURCE = OUT_DIR / "a90_doomgeneric_native_sfx_v3396.c"
SDL_MIXER_STUB = OUT_DIR / "SDL_mixer.h"

SERVICE_OBJECT_FWCLASS_BRIDGE_FLAG = previous.SERVICE_OBJECT_FWCLASS_BRIDGE_FLAG
SOFTAP_COMMANDS = tuple(previous.SOFTAP_COMMANDS)


def _rewrite_v3396_text(text: str) -> str:
    text = ORIG_V3395_REWRITE_TEXT(text)
    replacements = (
        ("v3395-wsta-screenapp-live", INIT_BUILD),
        ("0.11.151", INIT_VERSION),
        ("V3395", CYCLE),
        ("v3395", "v3396"),
        ("a90-doomgeneric-v3395", "a90-doomgeneric-v3396"),
        ("a90.doomgeneric.v3395", "a90.doomgeneric.v3396"),
    )
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def _rewrite_v3396_bytes(item: bytes) -> bytes:
    return _rewrite_v3396_text(item.decode("utf-8")).encode("utf-8")


FRAME_SCALE = _rewrite_v3396_text(previous.FRAME_SCALE)
FRAME_IPC = _rewrite_v3396_text(previous.FRAME_IPC)
SFX_STREAM_MARKER = _rewrite_v3396_text(previous.SFX_STREAM_MARKER)
SOUND_MODE = _rewrite_v3396_text(previous.SOUND_MODE)

STALE_WSTA_REQUIRED_STRINGS = (
    b"FLOW WSTA45 -> WSTA43 -> WSTA42",
    b"PUBLISH: HOST RUNBOOK ONLY",
    b"NATIVE MENU: DISPLAY-ONLY NO CONNECT",
    b"AGGREGATE: WSTA48 REDACTED RESULT",
)

PREVIOUS_REQUIRED_STRINGS = tuple(
    _rewrite_v3396_bytes(marker)
    for marker in ORIG_V3395_REQUIRED_STRINGS
    if marker not in STALE_WSTA_REQUIRED_STRINGS
)

REQUIRED_STRINGS = PREVIOUS_REQUIRED_STRINGS + (
    b"0.11.152",
    b"v3396-wsta-persistent-state-screen",
    b"screenapp.title=WSTA D-PUBLIC",
    b"WSTA D-PUBLIC",
    b"WSTA PUBLISH",
    b"STATE: PUBLIC_OFF LEASE-GATED",
    b"PROOF: WSTA55 START / WSTA58 RENEW",
    b"URL: REDACTED PRIVATE-RUN ONLY",
    b"NATIVE: DISPLAY-ONLY NO CONNECT",
)

OBSOLETE_RAMDISK_ENGINES = tuple(dict.fromkeys([
    *previous.OBSOLETE_RAMDISK_ENGINES,
    "a90_doomgeneric_private_engine_v3395",
]))


def _boot_audit_manifest() -> dict[str, Any]:
    manifest = ORIG_V3395_BOOT_AUDIT_MANIFEST()
    manifest["rung"] = "wsta-persistent-state-screen"
    manifest["scope"] = "native-wsta-redacted-persistent-state-screen"
    manifest["wsta_operator_screenapp"] = {
        "surface": "NETWORK menu + screenapp wsta/dpublic",
        "mode": "read-only-display",
        "state": "PUBLIC_OFF",
        "lease_policy": "host-private-lease-gated",
        "proofs": "WSTA55 short start + WSTA58 renew/manual-stop",
        "public_url_display": "redacted-private-run-only",
        "native_public_action": "none",
        "redacted_result_source": "WSTA48",
    }
    manifest["wifi_uplink_service_boundary"]["obsolete_ramdisk_engines"] = [
        "bin/" + name for name in OBSOLETE_RAMDISK_ENGINES
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
        "# Native Init V3396 WSTA Persistent State Screen Source Build",
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
        "- Carries forward V3395 WSTA screenapp live validation.",
        "- Replaces the generic publish-only wording with a redacted persistent-state screen.",
        "- Shows `PUBLIC_OFF`, host-private lease gating, WSTA55/WSTA58 proof lineage, and private-run-only URL redaction.",
        "- Does not add Wi-Fi connect, DHCP, public tunnel, native reboot, or flash behavior to the WSTA screen.",
        "",
        "## Validation",
        "",
        "- Build: AArch64 helper/native-init compile, required-string audit, preserved-ramdisk overlay, boot image pack, and SHA256 capture.",
        "- Static source checks: `tests.test_native_wsta_operator_screenapp_source`.",
        "- Builder regression: `tests.test_build_native_init_boot_v3396_wsta_persistent_state_screen`.",
        "- No association, DHCP, ping, public exposure, userdata, switch-root, or live display action was performed in this source build.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `wsta-persistent-state-screen`.",
    ]) + "\n"


def _write_candidate_manifest(manifest: dict[str, Any]) -> None:
    (OUT_DIR / "wsta-persistent-state-screen.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "wsta-persistent-state-screen",
        "boot_image": base.rel(BOOT_IMAGE),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "helper_sha256": manifest.get("helper_sha256", ""),
        "source_report": base.rel(REPORT_PATH),
        "base_boot": base.rel(BASE_BOOT),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "wsta_operator_screenapp": manifest["boot_audit"]["wsta_operator_screenapp"],
        "wifi_wpa_failure_detail": manifest["boot_audit"]["wifi_uplink_service_boundary"]["wpa_failure_detail"],
        "wifi_ctrl_socket_uniqueness": manifest["boot_audit"]["wifi_uplink_service_boundary"]["ctrl_socket_uniqueness"],
        "wifi_tmp_ctrl_dir": manifest["boot_audit"]["wifi_uplink_service_boundary"]["tmp_ctrl_dir"],
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _normalize_manifest_for_v3396(manifest: dict[str, Any]) -> dict[str, Any]:
    manifest = ORIG_V3395_NORMALIZE_MANIFEST(manifest)
    manifest.update({
        "decision": DECISION,
        "cycle": CYCLE,
        "candidate_tag": INIT_BUILD,
        "candidate_type": "wsta-persistent-state-screen",
        "adoption_state": "source-built-live-gated",
        "boot_image": base.rel(BOOT_IMAGE),
        "init_version": INIT_VERSION,
        "init_build": INIT_BUILD,
        "boot_audit": _boot_audit_manifest(),
    })
    return manifest


def _patch_v3395_module_for_v3396() -> None:
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
        "OBSOLETE_RAMDISK_ENGINES": OBSOLETE_RAMDISK_ENGINES,
        "SOFTAP_COMMANDS": SOFTAP_COMMANDS,
        "render_report": render_report,
        "_rewrite_v3395_text": _rewrite_v3396_text,
        "_rewrite_v3395_bytes": _rewrite_v3396_bytes,
        "_boot_audit_manifest": _boot_audit_manifest,
        "_write_candidate_manifest": _write_candidate_manifest,
        "_normalize_manifest_for_v3395": _normalize_manifest_for_v3396,
    }
    for name, value in replacements.items():
        setattr(previous, name, value)


def main() -> int:
    _patch_v3395_module_for_v3396()
    return previous.main()


if __name__ == "__main__":
    raise SystemExit(main())
