#!/usr/bin/env python3
"""Build V3343 native-init SoftAP S3 mode=2 AP bring-up candidate."""

from __future__ import annotations

import json
from typing import Any

from _workspace_bootstrap import add_legacy_revalidation_path, repo_root

REPO_ROOT = repo_root()
add_legacy_revalidation_path(REPO_ROOT)

from a90harness.evidence import workspace_private_build_path, workspace_private_input_path
import build_native_init_boot_v3342_softap_s3_fwsource_iftype_probe as previous

base = previous.base
ORIG_PREVIOUS_REWRITE_TEXT = previous._rewrite_v3342_text
ORIG_PREVIOUS_SOFTAP_MANIFEST = previous._softap_manifest
ORIG_PREVIOUS_OVERLAY = previous._overlay_preserved_v3342_ramdisk
ORIG_PREVIOUS_ADAPTER_SOURCE = previous.v3342_adapter_source

CYCLE = "V3343"
INIT_VERSION = "0.11.107"
INIT_BUILD = "v3343-softap-s3-mode2-bringup"
BUILD_TAG = INIT_BUILD
DECISION = "v3343-softap-s3-mode2-bringup-source-build-pass"
EXPECTED_HELPER_MARKER = previous.EXPECTED_HELPER_MARKER
EXPECTED_HELPER_SHA256 = previous.EXPECTED_HELPER_SHA256

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
OBJ_DIR = OUT_DIR / "obj"
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V3343_SOFTAP_S3_MODE2_BRINGUP_SOURCE_BUILD_2026-06-28.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images",
    "boot_linux_v3343_softap_s3_mode2_bringup.img",
    legacy_fallback=False,
)
BASE_BOOT = previous.BASE_BOOT
INIT_BINARY = OUT_DIR / "init_v3343_softap_s3_mode2_bringup"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v3343_softap_s3_mode2_bringup.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v626_softap_s3_mode2_bringup"

ENGINE_BINARY = OUT_DIR / "a90_doomgeneric_private_engine_v3343"
ENGINE_ADAPTER_SOURCE = OUT_DIR / "a90_doomgeneric_native_bridge_v3343.c"
ENGINE_ADAPTER_OBJECT = OBJ_DIR / "a90_doomgeneric_native_bridge_v3343.o"
ENGINE_RAMDISK_PATH = "bin/a90_doomgeneric_private_engine_v3343"
ENGINE_REMOTE_PATH = "/" + ENGINE_RAMDISK_PATH
ENGINE_NAME = "doomgeneric-private-link-v3343-softap-s3-mode2-bringup"

FRAME_PATH = "/tmp/a90-doomgeneric-v3343-raw-fallback-frame.xbgr8888"
SHARED_FRAME_PATH = "/tmp/a90-doomgeneric-v3343-shared-frame.bin"
INPUT_STATE_PATH = "/tmp/a90-doomgeneric-v3343-input.state"
INPUT_SOCKET_PATH = "/tmp/a90-doomgeneric-v3343-input.sock"
PACE_SOCKET_PATH = "/tmp/a90-doomgeneric-v3343-pace.sock"
TICK_TELEMETRY_PATH = "/tmp/a90-doomgeneric-v3343-tick-telemetry.txt"
AUDIO_PCM_STREAM_PATH = "/cache/a90-runtime/a90-doomgeneric-v3343-sfx.pcmstream"

FRAME_SCALE = "1:1-demo-hud-large-groups-softap-s3-mode2-bringup"
FRAME_IPC = "shared-mmap-direct-blit-demo-hud-large-groups-softap-s3-mode2-bringup"

SFX_STREAM_MARKER = "a90.doomgeneric.v3343.audio=real-sfx-pcm-stream-softap-s3-mode2-bringup"
SOUND_MODE = "native-doom-sfx-softap-s3-mode2-bringup-v3343"

SFX_BACKEND_SOURCE = OUT_DIR / "a90_doomgeneric_native_sfx_v3343.c"
SDL_MIXER_STUB = OUT_DIR / "SDL_mixer.h"

SERVICE_OBJECT_FWCLASS_BRIDGE_FLAG = previous.SERVICE_OBJECT_FWCLASS_BRIDGE_FLAG

SOFTAP_COMMANDS = tuple(dict.fromkeys([
    *previous.SOFTAP_COMMANDS,
    "wifi softap start 6",
    "wifi softap cleanup",
]))


def _rewrite_v3343_text(text: str) -> str:
    text = ORIG_PREVIOUS_REWRITE_TEXT(text)
    replacements = (
        (previous.INIT_VERSION, INIT_VERSION),
        (previous.INIT_BUILD, INIT_BUILD),
        ("softap-s3-fwsource-iftype-probe", "softap-s3-mode2-bringup"),
        ("SOFTAP_S3_FWSOURCE_IFTYPE_PROBE", "SOFTAP_S3_MODE2_BRINGUP"),
        ("SoftAP S3 Firmware Source IfType Probe", "SoftAP S3 Mode2 Bringup"),
        ("v3342", "v3343"),
        ("V3342", "V3343"),
        ("0.11.106", INIT_VERSION),
        ("a90-doomgeneric-v3342", "a90-doomgeneric-v3343"),
        ("a90.doomgeneric.v3342", "a90.doomgeneric.v3343"),
        (
            "wifi softap [status|plan|prepare [profile]|iftype-probe [timeout_ms]|cleanup]",
            "wifi softap [status|plan|prepare [profile]|iftype-probe [timeout_ms]|start [channel]|cleanup]",
        ),
        ("scope=read-only-status-plan-no-ap-start", "scope=status-plan-start-supported-no-ap-start"),
        ("start_supported=0", "start_supported=1"),
        ("start_allowed=0", "start_allowed=%d"),
        ("softap-status-prereq-visible-start-not-implemented", "softap-status-start-supported"),
        ("softap-prepare-start-not-implemented", "softap-prepare-start-supported"),
        ("plan.s3=blocked-until-iftype-probe-pass", "plan.s3=mode2-ap-start-and-dhcp-next"),
    )
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def _rewrite_v3343_bytes(item: bytes) -> bytes:
    return _rewrite_v3343_text(item.decode("utf-8")).encode("utf-8")


REQUIRED_STRINGS = tuple(_rewrite_v3343_bytes(item) for item in previous.REQUIRED_STRINGS) + (
    b"wifi softap [status|plan|prepare [profile]|iftype-probe [timeout_ms]|start [channel]|cleanup]",
    b"scope=s3-mode2-ap-bringup-dhcp-no-server",
    b"softap-start-pass",
    b"softap-cleanup-pass",
    b"wpa_supplicant_mode2_start_attempted=1",
    b"dhcp_server_start_attempted=1",
    b"dhcp_server_alive=%d",
    b"default_route_export_attempted=0",
    b"nat_attempted=0",
    b"hostapd_start_attempted=0",
    b"dhcp_router_option_exported=0",
    b"ssid_psk_logged=0",
)


def _softap_manifest() -> dict[str, Any]:
    manifest = ORIG_PREVIOUS_SOFTAP_MANIFEST()
    manifest["rung"] = "S3-ap-bringup"
    manifest["scope"] = "softap-mode2-ap-dhcp-start-cleanup"
    manifest["commands"] = list(SOFTAP_COMMANDS)
    manifest["expected_current_decisions"] = [
        "softap-status-start-supported",
        "softap-start-pass",
        "softap-cleanup-pass",
    ]
    manifest["start_contract"] = {
        "ap_daemon": "wpa_supplicant-mode-2",
        "hostapd": "not-used",
        "dhcp": "busybox-udhcpd",
        "band": "2.4GHz",
        "allowed_channels": [1, 6, 11],
        "credentials": "private-generated-runtime-file",
        "public_secret_output": "forbidden",
        "wan_nat": "forbidden",
        "default_route_export": "forbidden",
        "server_listener": "not-yet-s4",
    }
    manifest["pass_requirements"] = [
        "version-0.11.107",
        "post-flash-selftest-fail-0",
        "wlan0-present-after-helper-window",
        "softap-start-rc-0",
        "decision-softap-start-pass",
        "wpa-supplicant-mode2-start-attempted-1",
        "dhcp-server-start-attempted-1",
        "dhcp-server-alive-1",
        "hostapd-start-attempted-0",
        "no-wan-nat-default-route-export",
        "ssid-psk-not-logged",
        "softap-cleanup-rc-0",
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
        "# Native Init V3343 SoftAP S3 Mode2 Bringup Source Build",
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
        "- Adds `wifi softap start [channel]` for the first bounded AP bring-up after the V3342 lower gate pass.",
        "- Starts a private generated WPA2 SoftAP through `wpa_supplicant mode=2` on 2.4GHz channel 1, 6, or 11; `hostapd` remains unused.",
        "- Starts BusyBox `udhcpd` for the private AP subnet without WAN/NAT/default-route export and without a server listener.",
        "- Makes `wifi softap cleanup` real: stop AP supplicant, stop `udhcpd`, delete the AP interface, and remove private runtime config.",
        "",
        "## Validation Contract",
        "",
        "- PASS requires post-flash `selftest fail=0`, `decision=softap-start-pass`, `wpa_supplicant_mode2_start_attempted=1`, `dhcp_server_start_attempted=1`, `dhcp_server_alive=1`, and `decision=softap-cleanup-pass`.",
        "- Public output remains metadata-only and must not contain SSID, PSK, BSSID, MAC, client identifiers, concrete peer addresses, DHCP leases, or transfer payloads.",
        "",
        "## Static Validation",
        "",
        "- `py_compile`: V3343 builder and focused source tests.",
        "- Unit tests: V3343 source/build contract plus retained V3341/V3342 SoftAP lower-gate contracts.",
        "- Build: AArch64 helper/native-init compile, preserved-ramdisk overlay, boot image pack, SHA256 capture.",
        "- Marker check: generated boot image contains V3343 identity, SoftAP start/cleanup decisions, mode=2, `udhcpd`, and no-route/NAT fields.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `softap-s3-mode2-bringup-candidate`.",
    ]) + "\n"


def v3343_adapter_source() -> str:
    return _rewrite_v3343_text(ORIG_PREVIOUS_ADAPTER_SOURCE())


def _write_candidate_manifest(manifest: dict[str, Any]) -> None:
    (OUT_DIR / "softap-s3-mode2-bringup-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "softap-s3-mode2-bringup-candidate",
        "boot_image": base.rel(BOOT_IMAGE),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "helper_sha256": manifest.get("helper_sha256", ""),
        "live_validation_focus": manifest["softap_s3"]["pass_requirements"],
        "source_report": base.rel(REPORT_PATH),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-softap-s3-mode2-bringup-live-validation",
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
        "candidate_type": "softap-s3-mode2-bringup-candidate",
        "adoption_state": "pending-softap-s3-mode2-bringup-live-validation",
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
        "softap_s3": _softap_manifest(),
    })
    if base_main_error:
        manifest["base_main_error"] = base_main_error
    else:
        manifest.pop("base_main_error", None)
    for key in ("gpu_d3", "gpu_h1", "gpu_m0", "gpu_m1", "gpu_m2", "gpu_m3", "gpu_z2", "gpu_z3", "softap_s2"):
        manifest.pop(key, None)
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
        "decision": DECISION,
        "cycle": CYCLE,
        "candidate_tag": INIT_BUILD,
        "candidate_type": "softap-s3-mode2-bringup-candidate",
        "adoption_state": "pending-softap-s3-mode2-bringup-live-validation",
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


def _overlay_preserved_v3343_ramdisk() -> dict[str, Any]:
    overlay = ORIG_PREVIOUS_OVERLAY()
    overlay["mode"] = "preserve-v3335-ramdisk-overlay-v3343-init-helper-engine"
    return overlay


def _patch_v3342_module_for_v3343() -> None:
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
        "v3342_adapter_source": v3343_adapter_source,
        "_rewrite_v3342_text": _rewrite_v3343_text,
        "_rewrite_v3342_bytes": _rewrite_v3343_bytes,
        "_softap_manifest": _softap_manifest,
        "_write_candidate_manifest": _write_candidate_manifest,
        "_overlay_preserved_v3342_ramdisk": _overlay_preserved_v3343_ramdisk,
        "_postprocess_manifest": _postprocess_manifest,
        "_finalize_manifest_after_overlay": _finalize_manifest_after_overlay,
    }
    for name, value in replacements.items():
        setattr(previous, name, value)


def main() -> int:
    _patch_v3342_module_for_v3343()
    return previous.main()


if __name__ == "__main__":
    raise SystemExit(main())
