#!/usr/bin/env python3
"""Build V3344 native-init SoftAP S4 transfer server candidate."""

from __future__ import annotations

import json
from typing import Any

from _workspace_bootstrap import add_legacy_revalidation_path, repo_root

REPO_ROOT = repo_root()
add_legacy_revalidation_path(REPO_ROOT)

from a90harness.evidence import workspace_private_build_path, workspace_private_input_path
import build_native_init_boot_v3343_softap_s3_mode2_bringup as previous

base = previous.base
ORIG_PREVIOUS_REWRITE_TEXT = previous._rewrite_v3343_text
ORIG_PREVIOUS_SOFTAP_MANIFEST = previous._softap_manifest
ORIG_PREVIOUS_OVERLAY = previous._overlay_preserved_v3343_ramdisk
ORIG_PREVIOUS_ADAPTER_SOURCE = previous.v3343_adapter_source

CYCLE = "V3344"
INIT_VERSION = "0.11.108"
INIT_BUILD = "v3344-softap-s4-transfer-server"
BUILD_TAG = INIT_BUILD
DECISION = "v3344-softap-s4-transfer-server-source-build-pass"
EXPECTED_HELPER_MARKER = previous.EXPECTED_HELPER_MARKER
EXPECTED_HELPER_SHA256 = previous.EXPECTED_HELPER_SHA256

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
OBJ_DIR = OUT_DIR / "obj"
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V3344_SOFTAP_S4_TRANSFER_SERVER_SOURCE_BUILD_2026-06-28.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images",
    "boot_linux_v3344_softap_s4_transfer_server.img",
    legacy_fallback=False,
)
BASE_BOOT = previous.BASE_BOOT
INIT_BINARY = OUT_DIR / "init_v3344_softap_s4_transfer_server"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v3344_softap_s4_transfer_server.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v626_softap_s4_transfer_server"

ENGINE_BINARY = OUT_DIR / "a90_doomgeneric_private_engine_v3344"
ENGINE_ADAPTER_SOURCE = OUT_DIR / "a90_doomgeneric_native_bridge_v3344.c"
ENGINE_ADAPTER_OBJECT = OBJ_DIR / "a90_doomgeneric_native_bridge_v3344.o"
ENGINE_RAMDISK_PATH = "bin/a90_doomgeneric_private_engine_v3344"
ENGINE_REMOTE_PATH = "/" + ENGINE_RAMDISK_PATH
ENGINE_NAME = "doomgeneric-private-link-v3344-softap-s4-transfer-server"

FRAME_PATH = "/tmp/a90-doomgeneric-v3344-raw-fallback-frame.xbgr8888"
SHARED_FRAME_PATH = "/tmp/a90-doomgeneric-v3344-shared-frame.bin"
INPUT_STATE_PATH = "/tmp/a90-doomgeneric-v3344-input.state"
INPUT_SOCKET_PATH = "/tmp/a90-doomgeneric-v3344-input.sock"
PACE_SOCKET_PATH = "/tmp/a90-doomgeneric-v3344-pace.sock"
TICK_TELEMETRY_PATH = "/tmp/a90-doomgeneric-v3344-tick-telemetry.txt"
AUDIO_PCM_STREAM_PATH = "/cache/a90-runtime/a90-doomgeneric-v3344-sfx.pcmstream"

FRAME_SCALE = "1:1-demo-hud-large-groups-softap-s4-transfer-server"
FRAME_IPC = "shared-mmap-direct-blit-demo-hud-large-groups-softap-s4-transfer-server"

SFX_STREAM_MARKER = "a90.doomgeneric.v3344.audio=real-sfx-pcm-stream-softap-s4-transfer-server"
SOUND_MODE = "native-doom-sfx-softap-s4-transfer-server-v3344"

SFX_BACKEND_SOURCE = OUT_DIR / "a90_doomgeneric_native_sfx_v3344.c"
SDL_MIXER_STUB = OUT_DIR / "SDL_mixer.h"

SERVICE_OBJECT_FWCLASS_BRIDGE_FLAG = previous.SERVICE_OBJECT_FWCLASS_BRIDGE_FLAG

SOFTAP_COMMANDS = tuple(dict.fromkeys([
    *previous.SOFTAP_COMMANDS,
    "wifi softap transfer-start 6",
    "wifi softap transfer-status",
    "wifi softap cleanup",
]))


def _rewrite_v3344_text(text: str) -> str:
    text = ORIG_PREVIOUS_REWRITE_TEXT(text)
    replacements = (
        (previous.INIT_VERSION, INIT_VERSION),
        (previous.INIT_BUILD, INIT_BUILD),
        ("softap-s3-mode2-bringup", "softap-s4-transfer-server"),
        ("SOFTAP_S3_MODE2_BRINGUP", "SOFTAP_S4_TRANSFER_SERVER"),
        ("SoftAP S3 Mode2 Bringup", "SoftAP S4 Transfer Server"),
        ("v3343", "v3344"),
        ("V3343", "V3344"),
        ("0.11.107", INIT_VERSION),
        ("a90-doomgeneric-v3343", "a90-doomgeneric-v3344"),
        ("a90.doomgeneric.v3343", "a90.doomgeneric.v3344"),
        (
            "wifi softap [status|plan|prepare [profile]|iftype-probe [timeout_ms]|start [channel]|cleanup]",
            "wifi softap [status|plan|prepare [profile]|iftype-probe [timeout_ms]|start [channel]|transfer-start [channel]|transfer-status|cleanup]",
        ),
    )
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def _rewrite_v3344_bytes(item: bytes) -> bytes:
    return _rewrite_v3344_text(item.decode("utf-8")).encode("utf-8")


REQUIRED_STRINGS = tuple(_rewrite_v3344_bytes(item) for item in previous.REQUIRED_STRINGS) + (
    b"0.11.108",
    b"v3344-softap-s4-transfer-server",
    b"wifi softap [status|plan|prepare [profile]|iftype-probe [timeout_ms]|start [channel]|transfer-start [channel]|transfer-status|cleanup]",
    b"scope=s4-local-transfer-server-private-ap",
    b"a90-native-wifi-softap-transfer-v1",
    b"server_bind_private_ap_only=1",
    b"softap-transfer-start-pass",
    b"softap-transfer-status-pass",
    b"httpd_start_attempted=1",
    b"upload_receiver_start_attempted=1",
    b"download_payload_sha256=%s",
    b"upload_result.sha256=%s",
    b"transfer_runtime_removed=1",
    b"final_httpd_count=%d",
    b"wan_nat_attempted=0",
    b"default_route_export_attempted=0",
    b"ssid_psk_logged=0",
    b"client_identity_logged=0",
    b"peer_address_logged=0",
)


def _softap_manifest() -> dict[str, Any]:
    manifest = ORIG_PREVIOUS_SOFTAP_MANIFEST()
    manifest["rung"] = "S4-transfer-server"
    manifest["scope"] = "softap-private-ap-http-download-raw-upload-sha-cleanup"
    manifest["commands"] = list(SOFTAP_COMMANDS)
    manifest["expected_current_decisions"] = [
        "softap-status-start-supported",
        "softap-transfer-start-pass",
        "softap-transfer-status-pass",
        "softap-cleanup-pass",
    ]
    manifest["transfer_contract"] = {
        "ap_daemon": "wpa_supplicant-mode-2",
        "dhcp": "busybox-udhcpd",
        "http_download": "busybox-httpd-private-ap-bind",
        "raw_upload": "native-bounded-single-connection-private-ap-bind",
        "payload": "deterministic-bounded-download-file",
        "upload_limit_bytes": 1024 * 1024,
        "public_secret_output": "forbidden",
        "client_identity_output": "forbidden",
        "peer_address_output": "forbidden",
        "wan_nat": "forbidden",
        "default_route_export": "forbidden",
    }
    manifest["pass_requirements"] = [
        "version-0.11.108",
        "post-flash-selftest-fail-0",
        "softap-transfer-start-rc-0",
        "decision-softap-transfer-start-pass",
        "httpd-alive-1",
        "upload-receiver-alive-1",
        "client-joined-private-ap",
        "http-download-sha256-match",
        "raw-upload-sha256-match",
        "decision-softap-transfer-status-pass",
        "softap-cleanup-rc-0",
        "post-cleanup-selftest-fail-0",
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
        "# Native Init V3344 SoftAP S4 Transfer Server Source Build",
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
        "- Adds `wifi softap transfer-start [channel]` for the S4 private transfer proof on top of the V3343 AP/DHCP bring-up.",
        "- Starts BusyBox `httpd` bound only to the private AP address and serves a bounded deterministic download payload with a printed SHA256.",
        "- Starts a native single-connection raw upload receiver bound only to the private AP address, writes a bounded upload file, and reports upload SHA256 through `wifi softap transfer-status`.",
        "- Extends `wifi softap cleanup` to stop HTTP/upload workers and remove transfer runtime files before tearing down AP/DHCP.",
        "",
        "## Validation Contract",
        "",
        "- PASS requires post-flash `selftest fail=0`, `decision=softap-transfer-start-pass`, a client joined to the private AP, HTTP download SHA match, raw upload SHA match, `decision=softap-cleanup-pass`, and post-cleanup `selftest fail=0`.",
        "- Public output remains metadata-only and must not contain SSID, PSK, BSSID, MAC, client identifiers, concrete peer addresses, DHCP leases, or transfer payload bytes.",
        "",
        "## Static Validation",
        "",
        "- `py_compile`: V3344 builder and focused source tests.",
        "- Unit tests: V3344 source/build contract plus retained V3341-V3343 SoftAP contracts.",
        "- Build: AArch64 helper/native-init compile, preserved-ramdisk overlay, boot image pack, SHA256 capture.",
        "- Marker check: generated boot image contains V3344 identity, transfer-start/status decisions, private AP bind marker, SHA fields, and cleanup markers.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `softap-s4-transfer-server-candidate`.",
    ]) + "\n"


def v3344_adapter_source() -> str:
    return _rewrite_v3344_text(ORIG_PREVIOUS_ADAPTER_SOURCE())


def _write_candidate_manifest(manifest: dict[str, Any]) -> None:
    (OUT_DIR / "softap-s4-transfer-server-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "softap-s4-transfer-server-candidate",
        "boot_image": base.rel(BOOT_IMAGE),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "helper_sha256": manifest.get("helper_sha256", ""),
        "live_validation_focus": manifest["softap_s4"]["pass_requirements"],
        "source_report": base.rel(REPORT_PATH),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-softap-s4-transfer-server-live-validation",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
        "candidate_type": "softap-s4-transfer-server-candidate",
        "adoption_state": "pending-softap-s4-transfer-server-live-validation",
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
        "softap_s4": _softap_manifest(),
    })
    if base_main_error:
        manifest["base_main_error"] = base_main_error
    else:
        manifest.pop("base_main_error", None)
    for key in ("gpu_d3", "gpu_h1", "gpu_m0", "gpu_m1", "gpu_m2", "gpu_m3", "gpu_z2", "gpu_z3", "softap_s2"):
        manifest.pop(key, None)
    manifest["softap_s4"]["ramdisk_overlay"] = overlay
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
    for key in ("gpu_d3", "gpu_h1", "gpu_m0", "gpu_m1", "gpu_m2", "gpu_m3", "gpu_z2", "gpu_z3", "softap_s2"):
        manifest.pop(key, None)
    manifest.update({
        "decision": DECISION,
        "cycle": CYCLE,
        "candidate_tag": INIT_BUILD,
        "candidate_type": "softap-s4-transfer-server-candidate",
        "adoption_state": "pending-softap-s4-transfer-server-live-validation",
        "helper_flags": list(dict.fromkeys([
            *manifest.get("helper_flags", []),
            SERVICE_OBJECT_FWCLASS_BRIDGE_FLAG,
        ])),
        "softap_s4": _softap_manifest(),
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


def _overlay_preserved_v3344_ramdisk() -> dict[str, Any]:
    overlay = ORIG_PREVIOUS_OVERLAY()
    overlay["mode"] = "preserve-v3335-ramdisk-overlay-v3344-init-helper-engine"
    return overlay


def _patch_v3343_module_for_v3344() -> None:
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
        "v3343_adapter_source": v3344_adapter_source,
        "_rewrite_v3343_text": _rewrite_v3344_text,
        "_rewrite_v3343_bytes": _rewrite_v3344_bytes,
        "_softap_manifest": _softap_manifest,
        "_write_candidate_manifest": _write_candidate_manifest,
        "_overlay_preserved_v3343_ramdisk": _overlay_preserved_v3344_ramdisk,
        "_postprocess_manifest": _postprocess_manifest,
        "_finalize_manifest_after_overlay": _finalize_manifest_after_overlay,
    }
    for name, value in replacements.items():
        setattr(previous, name, value)


def main() -> int:
    _patch_v3343_module_for_v3344()
    return previous.main()


if __name__ == "__main__":
    raise SystemExit(main())
