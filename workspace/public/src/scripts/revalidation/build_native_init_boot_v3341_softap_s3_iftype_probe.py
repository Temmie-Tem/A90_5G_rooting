#!/usr/bin/env python3
"""Build V3341 native-init SoftAP S3 AP-iftype probe candidate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _workspace_bootstrap import add_legacy_revalidation_path, repo_root

REPO_ROOT = repo_root()
add_legacy_revalidation_path(REPO_ROOT)

from a90harness.evidence import workspace_private_build_path, workspace_private_input_path
import build_native_init_boot_v2237_supplicant_terminate_poll as wifi_route
import build_native_init_boot_v3339_softap_s2_status_plan as previous

base = previous.base
ORIG_PREVIOUS_OVERLAY = previous._overlay_preserved_v3339_ramdisk
ORIG_PREVIOUS_ADAPTER_SOURCE = previous.v3339_adapter_source

CYCLE = "V3341"
INIT_VERSION = "0.11.105"
INIT_BUILD = "v3341-softap-s3-iftype-probe"
BUILD_TAG = INIT_BUILD
DECISION = "v3341-softap-s3-iftype-probe-source-build-pass"

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
OBJ_DIR = OUT_DIR / "obj"
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V3341_SOFTAP_S3_IFTYPE_PROBE_SOURCE_BUILD_2026-06-28.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images",
    "boot_linux_v3341_softap_s3_iftype_probe.img",
    legacy_fallback=False,
)
BASE_BOOT = previous.BASE_BOOT
INIT_BINARY = OUT_DIR / "init_v3341_softap_s3_iftype_probe"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v3341_softap_s3_iftype_probe.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v624_softap_s3_iftype_probe"

ENGINE_BINARY = OUT_DIR / "a90_doomgeneric_private_engine_v3341"
ENGINE_ADAPTER_SOURCE = OUT_DIR / "a90_doomgeneric_native_bridge_v3341.c"
ENGINE_ADAPTER_OBJECT = OBJ_DIR / "a90_doomgeneric_native_bridge_v3341.o"
ENGINE_RAMDISK_PATH = "bin/a90_doomgeneric_private_engine_v3341"
ENGINE_REMOTE_PATH = "/" + ENGINE_RAMDISK_PATH
ENGINE_NAME = "doomgeneric-private-link-v3341-softap-s3-iftype-probe"

FRAME_PATH = "/tmp/a90-doomgeneric-v3341-raw-fallback-frame.xbgr8888"
SHARED_FRAME_PATH = "/tmp/a90-doomgeneric-v3341-shared-frame.bin"
INPUT_STATE_PATH = "/tmp/a90-doomgeneric-v3341-input.state"
INPUT_SOCKET_PATH = "/tmp/a90-doomgeneric-v3341-input.sock"
PACE_SOCKET_PATH = "/tmp/a90-doomgeneric-v3341-pace.sock"
TICK_TELEMETRY_PATH = "/tmp/a90-doomgeneric-v3341-tick-telemetry.txt"
AUDIO_PCM_STREAM_PATH = "/cache/a90-runtime/a90-doomgeneric-v3341-sfx.pcmstream"

FRAME_SCALE = "1:1-demo-hud-large-groups-softap-s3-iftype-probe"
FRAME_IPC = "shared-mmap-direct-blit-demo-hud-large-groups-softap-s3-iftype-probe"

SFX_STREAM_MARKER = "a90.doomgeneric.v3341.audio=real-sfx-pcm-stream-softap-s3-iftype-probe"
SOUND_MODE = "native-doom-sfx-softap-s3-iftype-probe-v3341"

SFX_BACKEND_SOURCE = OUT_DIR / "a90_doomgeneric_native_sfx_v3341.c"
SDL_MIXER_STUB = OUT_DIR / "SDL_mixer.h"

SERVICE_OBJECT_FWCLASS_BRIDGE_FLAG = wifi_route.SERVICE_OBJECT_FWCLASS_BRIDGE_FLAG

SOFTAP_COMMANDS = (
    "wifi softap status",
    "wifi softap plan",
    "wifi softap prepare",
    "wifi softap iftype-probe",
)


def _rewrite_v3341_text(text: str) -> str:
    replacements = (
        (previous.INIT_VERSION, INIT_VERSION),
        (previous.INIT_BUILD, INIT_BUILD),
        (previous.ENGINE_NAME, ENGINE_NAME),
        (previous.ENGINE_REMOTE_PATH, ENGINE_REMOTE_PATH),
        (previous.SOUND_MODE, SOUND_MODE),
        (previous.SFX_STREAM_MARKER, SFX_STREAM_MARKER),
        (previous.AUDIO_PCM_STREAM_PATH, AUDIO_PCM_STREAM_PATH),
        ("a90-native-wifi-softap-v1", "a90-native-wifi-softap-v2"),
        (
            "wifi softap [status|plan|prepare [profile]|cleanup]",
            "wifi softap [status|plan|prepare [profile]|iftype-probe [timeout_ms]|cleanup]",
        ),
        ("a90-doomgeneric-v3335", "a90-doomgeneric-v3341"),
        ("a90.doomgeneric.v3335", "a90.doomgeneric.v3341"),
        ("a90-doomgeneric-v3339", "a90-doomgeneric-v3341"),
        ("a90.doomgeneric.v3339", "a90.doomgeneric.v3341"),
        ("v3335", "v3341"),
        ("V3335", "V3341"),
        ("v3339", "v3341"),
        ("V3339", "V3341"),
        ("gpu-z3-primary-setcrtc", "softap-s3-iftype-probe"),
        ("softap-s2-status-plan", "softap-s3-iftype-probe"),
    )
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def _rewrite_v3341_bytes(item: bytes) -> bytes:
    return _rewrite_v3341_text(item.decode("utf-8")).encode("utf-8")


REQUIRED_STRINGS = tuple(_rewrite_v3341_bytes(item) for item in previous.REQUIRED_STRINGS) + (
    b"a90-native-wifi-softap-v2",
    b"wifi softap [status|plan|prepare [profile]|iftype-probe [timeout_ms]|cleanup]",
    b"scope=s3-ap-iftype-add-delete-probe-no-ap-start",
    b"softap-iftype-probe-pass",
    b"softap-iftype-probe-wlan0-timeout",
    b"softap-iftype-probe-add-failed",
    b"softap-iftype-probe-cleanup-failed",
    b"ap_iftype_add_attempted=1",
    b"ap_iftype_iface_created=%d",
    b"ap_iftype_cleanup_ok=%d",
    b"sta_supplicant.stoppable=%d",
    b"wpa_supplicant_mode2_start_attempted=0",
)


def _softap_manifest() -> dict[str, Any]:
    return {
        "rung": "S3-lower-gate",
        "scope": "softap-iftype-add-delete-probe-no-ap-start",
        "commands": list(SOFTAP_COMMANDS),
        "helper_route": {
            "source": "v2237-supplicant-terminate-poll",
            "fwclass_bridge_flag": SERVICE_OBJECT_FWCLASS_BRIDGE_FLAG,
            "watch_sec": 180,
            "supervisor_timeout_sec": 215,
        },
        "expected_current_decisions": [
            "softap-status-blocked-wlan-gate",
            "softap-prepare-blocked-wlan-gate",
            "softap-iftype-probe-pass",
        ],
        "hard_no_start_fields": [
            "config_write_attempted=0",
            "wpa_supplicant_mode2_start_attempted=0",
            "dhcp_server_start_attempted=0",
            "listener_start_attempted=0",
            "address_assign_attempted=0",
            "server_exposure_attempted=0",
            "ssid_psk_logged=0",
        ],
        "pass_requirements": [
            "version-0.11.105",
            "post-flash-selftest-fail-0",
            "wlan0-present-after-helper-window",
            "wifi-softap-iftype-probe-rc-0",
            "ap-iftype-add-rc-0",
            "ap-iftype-cleanup-ok-1",
            "sta-supplicant-stoppable-1",
            "no-mode2-ap-start",
            "no-dhcp-server-listener-address-route-nat",
        ],
    }


def render_report(
    manifest: dict[str, Any],
    helper_flags: tuple[str, ...],
    init_extra_flags: tuple[str, ...],
) -> str:
    boot_image = manifest.get("boot_image", base.rel(BOOT_IMAGE))
    boot_sha = manifest.get("boot_sha256", "")
    return "\n".join([
        "# Native Init V3341 SoftAP S3 IfType Probe Source Build",
        "",
        f"- Cycle: `{CYCLE}`",
        f"- Decision: `{DECISION}`",
        f"- Init: `A90 Linux init {INIT_VERSION} ({INIT_BUILD})`",
        f"- Boot image: `{boot_image}`",
        f"- Boot SHA256: `{boot_sha}`",
        f"- Base boot: `{base.rel(BASE_BOOT)}`",
        "",
        "## Change",
        "",
        "- Adds `wifi softap iftype-probe [timeout_ms]` as the S3 lower-gate proof command.",
        "- The probe waits for `wlan0`, stops a stale station `wpa_supplicant` if present, creates a temporary AP-type nl80211 interface, and deletes it before returning.",
        "- Carries forward the V2237 post-FW_READY firmware_class bridge helper route so the current SoftAP baseline can surface `wlan0` before the probe.",
        "- Keeps AP service below start: no generated SSID/PSK config, no `wpa_supplicant mode=2`, no `udhcpd`, no listener, no AP address, no route/NAT.",
        "",
        "## Validation Contract",
        "",
        "- Commands: `wifi softap status`, `wifi softap plan`, `wifi softap prepare`, `wifi softap iftype-probe`.",
        "- PASS requires post-flash `selftest fail=0`, helper-window `wlan0_present=1`, `decision=softap-iftype-probe-pass`, `ap_iftype_add_rc=0`, `ap_iftype_iface_created=1`, and `ap_iftype_cleanup_ok=1`.",
        "- Public output remains metadata-only and must not contain SSID, PSK, BSSID, MAC, client identifiers, concrete peer addresses, DHCP leases, or transfer payloads.",
        "",
        "## Static Validation",
        "",
        "- `py_compile`: V3341 builder and focused source tests.",
        "- Unit tests: V3341 iftype-probe source/build contract plus retained V3338/V3339 SoftAP contract updates.",
        "- Build: AArch64 helper/native-init compile, preserved-ramdisk overlay, boot image pack, SHA256 capture.",
        "- Marker check: generated boot image contains V3341 identity, SoftAP v2, iftype-probe decision markers, and no-start fields.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `softap-s3-iftype-probe-candidate`.",
    ]) + "\n"


def v3341_adapter_source() -> str:
    return _rewrite_v3341_text(ORIG_PREVIOUS_ADAPTER_SOURCE())


def _write_candidate_manifest(manifest: dict[str, Any]) -> None:
    (OUT_DIR / "softap-s3-iftype-probe-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "softap-s3-iftype-probe-candidate",
        "boot_image": base.rel(BOOT_IMAGE),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "live_validation_focus": manifest["softap_s3"]["pass_requirements"],
        "source_report": base.rel(REPORT_PATH),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-softap-s3-iftype-probe-live-validation",
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
            "decision": DECISION,
            "cycle": CYCLE,
            "candidate_tag": INIT_BUILD,
            "candidate_type": "softap-s3-iftype-probe-candidate",
            "adoption_state": "pending-softap-s3-iftype-probe-live-validation",
            "boot_image": base.rel(BOOT_IMAGE),
            "init_version": INIT_VERSION,
            "init_build": INIT_BUILD,
            "helper_sha256": base.sha256_file(HELPER_BINARY),
            "helper_flags": [SERVICE_OBJECT_FWCLASS_BRIDGE_FLAG],
            "init_extra_flags": [],
        }
    manifest["decision"] = DECISION
    manifest["cycle"] = CYCLE
    manifest["candidate_tag"] = INIT_BUILD
    manifest["candidate_type"] = "softap-s3-iftype-probe-candidate"
    manifest["adoption_state"] = "pending-softap-s3-iftype-probe-live-validation"
    manifest["boot_image"] = base.rel(BOOT_IMAGE)
    manifest["init_version"] = INIT_VERSION
    manifest["init_build"] = INIT_BUILD
    manifest["boot_sha256"] = overlay["boot_sha256"]
    manifest["ramdisk_sha256"] = overlay["ramdisk_sha256"]
    manifest["ramdisk_overlay"] = overlay
    manifest["base_main_completed"] = base_main_completed
    manifest["helper_flags"] = list(dict.fromkeys([
        *manifest.get("helper_flags", []),
        SERVICE_OBJECT_FWCLASS_BRIDGE_FLAG,
    ]))
    if base_main_error:
        manifest["base_main_error"] = base_main_error
    else:
        manifest.pop("base_main_error", None)
    for key in ("gpu_d3", "gpu_h1", "gpu_m0", "gpu_m1", "gpu_m2", "gpu_m3", "gpu_z2", "gpu_z3", "softap_s2"):
        manifest.pop(key, None)
    manifest["softap_s3"] = _softap_manifest()
    manifest["softap_s3"]["ramdisk_overlay"] = overlay
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
        "candidate_tag": INIT_BUILD,
        "candidate_type": "softap-s3-iftype-probe-candidate",
        "adoption_state": "pending-softap-s3-iftype-probe-live-validation",
        "helper_flags": list(dict.fromkeys([
            *manifest.get("helper_flags", []),
            SERVICE_OBJECT_FWCLASS_BRIDGE_FLAG,
        ])),
        "softap_s3": _softap_manifest(),
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


def _overlay_preserved_v3341_ramdisk() -> dict[str, Any]:
    overlay = ORIG_PREVIOUS_OVERLAY()
    overlay["mode"] = "preserve-v3335-ramdisk-overlay-v3341-init-helper-engine"
    return overlay


def _apply_v3341_overrides() -> dict[str, Any]:
    helper_flags = wifi_route.configure_helper_flags()
    previous._apply_v3339_overrides()
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
        "AUDIO_CORUN_MODE": SOUND_MODE,
        "SFX_BACKEND_SOURCE": SFX_BACKEND_SOURCE,
        "SDL_MIXER_STUB": SDL_MIXER_STUB,
        "SFX_BACKEND_SOURCE_TEXT": _rewrite_v3341_text(base.SFX_BACKEND_SOURCE_TEXT),
        "REQUIRED_STRINGS": REQUIRED_STRINGS,
        "render_report": render_report,
        "v3210_adapter_source": v3341_adapter_source,
        "_overlay_preserved_v3208_ramdisk": _overlay_preserved_v3341_ramdisk,
        "_postprocess_manifest": _postprocess_manifest,
        "_finalize_manifest_after_overlay": _finalize_manifest_after_overlay,
    }
    for name, value in replacements.items():
        setattr(base, name, value)
        if hasattr(previous, name):
            setattr(previous, name, value)
    previous.REQUIRED_STRINGS = REQUIRED_STRINGS
    previous._rewrite_v3339_text = _rewrite_v3341_text
    previous._softap_manifest = _softap_manifest
    previous._write_candidate_manifest = _write_candidate_manifest
    previous.render_report = render_report
    previous.v3339_adapter_source = v3341_adapter_source
    previous._overlay_preserved_v3339_ramdisk = _overlay_preserved_v3341_ramdisk
    previous._postprocess_manifest = _postprocess_manifest
    previous._finalize_manifest_after_overlay = _finalize_manifest_after_overlay
    return {"helper_flags": helper_flags}


def main() -> int:
    _apply_v3341_overrides()
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
