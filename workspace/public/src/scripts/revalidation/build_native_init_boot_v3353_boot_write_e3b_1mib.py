#!/usr/bin/env python3
"""Build V3353 native-init §0.2 E3b contiguous 1MiB slack identity rung.

V3352 proved sparse confirmed-zero expansion. V3353 adds `boot-write-e3b`: one contiguous 1MiB
identity pwrite in parsed boot tail slack, requiring the target block to contain non-zero bytes.
"""

from __future__ import annotations

import json
from typing import Any

from _workspace_bootstrap import add_legacy_revalidation_path, repo_root

REPO_ROOT = repo_root()
add_legacy_revalidation_path(REPO_ROOT)

from a90harness.evidence import workspace_private_build_path, workspace_private_input_path
import build_native_init_boot_v3352_boot_write_e3a_sparse16 as previous

base = previous.base
ORIG_PREVIOUS_REWRITE_TEXT = previous._rewrite_v3352_text
ORIG_PREVIOUS_OVERLAY = previous._overlay_preserved_v3352_ramdisk
ORIG_PREVIOUS_ADAPTER_SOURCE = previous.v3352_adapter_source
ORIG_PREVIOUS_BOOT_AUDIT_MANIFEST = previous._boot_audit_manifest

CYCLE = "V3353"
INIT_VERSION = "0.11.117"
INIT_BUILD = "v3353-boot-write-e3b-1mib"
BUILD_TAG = INIT_BUILD
DECISION = "v3353-boot-write-e3b-1mib-source-build-pass"
EXPECTED_HELPER_MARKER = previous.EXPECTED_HELPER_MARKER
EXPECTED_HELPER_SHA256 = previous.EXPECTED_HELPER_SHA256

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
OBJ_DIR = OUT_DIR / "obj"
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V3353_BOOT_WRITE_E3B_1MIB_SOURCE_BUILD_2026-07-02.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images",
    "boot_linux_v3353_boot_write_e3b_1mib.img",
    legacy_fallback=False,
)
BASE_BOOT = previous.BASE_BOOT
INIT_BINARY = OUT_DIR / "init_v3353_boot_write_e3b_1mib"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v3353_boot_write_e3b_1mib.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v626_boot_write_e3b_1mib"

ENGINE_BINARY = OUT_DIR / "a90_doomgeneric_private_engine_v3353"
ENGINE_ADAPTER_SOURCE = OUT_DIR / "a90_doomgeneric_native_bridge_v3353.c"
ENGINE_ADAPTER_OBJECT = OBJ_DIR / "a90_doomgeneric_native_bridge_v3353.o"
ENGINE_RAMDISK_PATH = "bin/a90_doomgeneric_private_engine_v3353"
ENGINE_REMOTE_PATH = "/" + ENGINE_RAMDISK_PATH
ENGINE_NAME = "doomgeneric-private-link-v3353-boot-write-e3b-1mib"

FRAME_PATH = "/tmp/a90-doomgeneric-v3353-raw-fallback-frame.xbgr8888"
SHARED_FRAME_PATH = "/tmp/a90-doomgeneric-v3353-shared-frame.bin"
INPUT_STATE_PATH = "/tmp/a90-doomgeneric-v3353-input.state"
INPUT_SOCKET_PATH = "/tmp/a90-doomgeneric-v3353-input.sock"
PACE_SOCKET_PATH = "/tmp/a90-doomgeneric-v3353-pace.sock"
TICK_TELEMETRY_PATH = "/tmp/a90-doomgeneric-v3353-tick-telemetry.txt"
AUDIO_PCM_STREAM_PATH = "/cache/a90-runtime/a90-doomgeneric-v3353-sfx.pcmstream"

SFX_BACKEND_SOURCE = OUT_DIR / "a90_doomgeneric_native_sfx_v3353.c"
SDL_MIXER_STUB = OUT_DIR / "SDL_mixer.h"

SERVICE_OBJECT_FWCLASS_BRIDGE_FLAG = previous.SERVICE_OBJECT_FWCLASS_BRIDGE_FLAG

SOFTAP_COMMANDS = tuple(previous.SOFTAP_COMMANDS)


def _rewrite_v3353_text(text: str) -> str:
    text = ORIG_PREVIOUS_REWRITE_TEXT(text)
    replacements = (
        (previous.INIT_VERSION, INIT_VERSION),
        (previous.INIT_BUILD, INIT_BUILD),
        ("0.11.116", INIT_VERSION),
        ("v3352", "v3353"),
        ("V3352", "V3353"),
        ("a90-doomgeneric-v3352", "a90-doomgeneric-v3353"),
        ("a90.doomgeneric.v3352", "a90.doomgeneric.v3353"),
        ("boot_write_e3a_sparse16", "boot_write_e3b_1mib"),
        ("boot-write-e3a-sparse16", "boot-write-e3b-1mib"),
        ("BOOT_WRITE_E3A_SPARSE16", "BOOT_WRITE_E3B_1MIB"),
    )
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def _rewrite_v3353_bytes(item: bytes) -> bytes:
    return _rewrite_v3353_text(item.decode("utf-8")).encode("utf-8")


FRAME_SCALE = _rewrite_v3353_text(previous.FRAME_SCALE)
FRAME_IPC = _rewrite_v3353_text(previous.FRAME_IPC)
SFX_STREAM_MARKER = _rewrite_v3353_text(previous.SFX_STREAM_MARKER)
SOUND_MODE = _rewrite_v3353_text(previous.SOUND_MODE)


PREVIOUS_REQUIRED_STRINGS = tuple(_rewrite_v3353_bytes(item) for item in previous.REQUIRED_STRINGS)

REQUIRED_STRINGS = PREVIOUS_REQUIRED_STRINGS + (
    b"0.11.117",
    b"v3353-boot-write-e3b-1mib",
    b"A90BWE3B",
    b"boot-write-e3b <token>",
    b"BOOT-WRITE-PROBE-E3B-1MIB-SLACK",
    b"tail-slack-contiguous-1mib-nonzero-identity",
    b"nonzero_bytes=%llu nonzero_sectors=%u zero_sectors=%u",
    b"pwrite_count=1 pwrite=ok fsync=ok",
    b"readback_rc=%ld region_match=%d",
)


def _boot_audit_manifest() -> dict[str, Any]:
    manifest = ORIG_PREVIOUS_BOOT_AUDIT_MANIFEST()
    manifest["rung"] = "boot-write-probe-E3b-1MiB-nonzero-slack"
    manifest["scope"] = "0.2-write-probe-E3b-contiguous-1MiB-nonzero-tail-slack-identity"
    manifest["commands"] = ["boot-write-e3b BOOT-WRITE-PROBE-E3B-1MIB-SLACK"]
    manifest["probe_contract"] = {
        "rung": "E3b",
        "token": "BOOT-WRITE-PROBE-E3B-1MIB-SLACK",
        "cmd_flags": "CMD_DANGEROUS (menu-settle required)",
        "write_syscall": "one pwrite call of a contiguous 1MiB slack block containing non-zero bytes",
        "target": "the first 1MiB block in parsed tail slack [roundup(used_len), size-1MiB)",
        "safety_gates": "fail-closed header, target fully in slack, target contains non-zero bytes, identity on every fd, O_NOFOLLOW",
        "verify": "O_DIRECT 1MiB readback memcmp + O_DIRECT full-partition SHA before/after",
        "risk": "higher than zero-only rungs: UFS-tear residual is still tail-slack-only but not all-zero; externally recoverable boot-only",
    }
    manifest["pass_requirements"] = [
        "version-0.11.117",
        "post-flash-selftest-fail-0",
        "boot-write-e3b-token-and-menu-gated",
        "boot-write-e3b-target-fully-in-tail-slack",
        "boot-write-e3b-nonzero-bytes-positive",
        "boot-write-e3b-pwrite-count-1",
        "boot-write-e3b-region-match-all-1",
        "boot-write-e3b-full-match-1",
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
        "# Native Init V3353 §0.2 Write-Probe E3b 1MiB Source Build",
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
        "- Adds `boot-write-e3b <token>` after the V3352 sparse16 live pass. E3b writes one contiguous "
        "1MiB block in parsed tail slack, using the exact bytes read from the device.",
        "- Unlike the zero-only rungs, E3b requires the 1MiB source block to contain non-zero bytes. "
        "This proves a non-zero write buffer and TWRP-sized chunk while keeping the offset outside the "
        "parsed boot image body and at least 1MiB before the partition end.",
        "- The safety envelope remains guarded: `CMD_DANGEROUS`, no auto-menu execution, O_NOFOLLOW + "
        "identity on every fd, one fsync after the identity pwrite, O_DIRECT 1MiB readback, and "
        "O_DIRECT full-partition SHA before/after.",
        "",
        "## Validation Contract",
        "",
        "- PASS requires post-flash `selftest fail=0`, `version` 0.11.117, and after `hide`, "
        "`boot-write-e3b BOOT-WRITE-PROBE-E3B-1MIB-SLACK` emitting positive `nonzero_bytes`, "
        "`pwrite_count=1`, `region_match_all=1`, `full_match=1`, then rollback to `v2321` with "
        "`selftest fail=0`.",
        "- This is a source-build preparation only; no live V3353 write is claimed here.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `boot-write-e3b-1mib-candidate`.",
    ]) + "\n"


def v3353_adapter_source() -> str:
    return _rewrite_v3353_text(ORIG_PREVIOUS_ADAPTER_SOURCE())


def _write_candidate_manifest(manifest: dict[str, Any]) -> None:
    (OUT_DIR / "boot-write-e3b-1mib-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "boot-write-e3b-1mib-candidate",
        "boot_image": base.rel(BOOT_IMAGE),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "helper_sha256": manifest.get("helper_sha256", ""),
        "live_validation_focus": manifest["boot_audit"]["pass_requirements"],
        "source_report": base.rel(REPORT_PATH),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-boot-write-e3b-1mib-live-validation",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")


_STALE_MANIFEST_KEYS = (
    "gpu_d3", "gpu_h1", "gpu_m0", "gpu_m1", "gpu_m2", "gpu_m3", "gpu_z2", "gpu_z3",
    "softap_s2", "softap_s4",
)


def _finalize_manifest_after_overlay(
    overlay: dict[str, Any],
    *,
    base_main_completed: bool,
    base_main_error: str | None = None,
) -> None:
    manifest_path = OUT_DIR / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        manifest = {
            "helper_sha256": base.sha256_file(HELPER_BINARY),
            "helper_flags": [SERVICE_OBJECT_FWCLASS_BRIDGE_FLAG],
            "init_extra_flags": [],
        }
    manifest.update({
        "decision": DECISION,
        "cycle": CYCLE,
        "candidate_tag": INIT_BUILD,
        "candidate_type": "boot-write-e3b-1mib-candidate",
        "adoption_state": "pending-boot-write-e3b-1mib-live-validation",
        "boot_image": base.rel(BOOT_IMAGE),
        "init_version": INIT_VERSION,
        "init_build": INIT_BUILD,
        "boot_sha256": overlay["boot_sha256"],
        "ramdisk_sha256": overlay["ramdisk_sha256"],
        "ramdisk_overlay": overlay,
        "base_main_completed": base_main_completed,
        "helper_flags": list(dict.fromkeys([
            *manifest.get("helper_flags", []),
            SERVICE_OBJECT_FWCLASS_BRIDGE_FLAG,
        ])),
        "boot_audit": _boot_audit_manifest(),
    })
    if base_main_error:
        manifest["base_main_error"] = base_main_error
    else:
        manifest.pop("base_main_error", None)
    for key in _STALE_MANIFEST_KEYS:
        manifest.pop(key, None)
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
    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.pop("base_main_error", None)
    for key in _STALE_MANIFEST_KEYS:
        manifest.pop(key, None)
    manifest.update({
        "decision": DECISION,
        "cycle": CYCLE,
        "candidate_tag": INIT_BUILD,
        "candidate_type": "boot-write-e3b-1mib-candidate",
        "adoption_state": "pending-boot-write-e3b-1mib-live-validation",
        "helper_flags": list(dict.fromkeys([
            *manifest.get("helper_flags", []),
            SERVICE_OBJECT_FWCLASS_BRIDGE_FLAG,
        ])),
        "boot_audit": _boot_audit_manifest(),
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
    _write_candidate_manifest(manifest)
    return manifest


def _overlay_preserved_v3353_ramdisk() -> dict[str, Any]:
    overlay = ORIG_PREVIOUS_OVERLAY()
    overlay["mode"] = "preserve-v3335-ramdisk-overlay-v3353-init-helper-engine"
    return overlay


def _patch_v3352_module_for_v3353() -> None:
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
        "v3352_adapter_source": v3353_adapter_source,
        "_rewrite_v3352_text": _rewrite_v3353_text,
        "_rewrite_v3352_bytes": _rewrite_v3353_bytes,
        "_boot_audit_manifest": _boot_audit_manifest,
        "_write_candidate_manifest": _write_candidate_manifest,
        "_overlay_preserved_v3352_ramdisk": _overlay_preserved_v3353_ramdisk,
        "_postprocess_manifest": _postprocess_manifest,
        "_finalize_manifest_after_overlay": _finalize_manifest_after_overlay,
    }
    for name, value in replacements.items():
        setattr(previous, name, value)


def main() -> int:
    _patch_v3352_module_for_v3353()
    return previous.main()


if __name__ == "__main__":
    raise SystemExit(main())
