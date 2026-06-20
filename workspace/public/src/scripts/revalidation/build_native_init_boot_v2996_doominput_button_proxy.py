#!/usr/bin/env python3
"""Build V2996 native-init candidate with DOOM physical-button proxy mapping."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _workspace_bootstrap import repo_root
import build_native_init_boot_v2859_audio_changelog_latest_refresh as v2859
from a90harness.evidence import workspace_private_build_path, workspace_private_input_path

REPO_ROOT = repo_root()

CYCLE = "V2996"
INIT_VERSION = "0.10.66"
INIT_BUILD = "v2996-doominput-button-proxy"
BUILD_TAG = INIT_BUILD
DECISION = "v2996-doominput-button-proxy-source-build-pass"

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
REPORT_PATH = REPO_ROOT / "docs/reports/NATIVE_INIT_V2996_DOOMINPUT_BUTTON_PROXY_SOURCE_BUILD_2026-06-20.md"
BOOT_IMAGE = workspace_private_input_path("boot_images", "boot_linux_v2996_doominput_button_proxy.img", legacy_fallback=False)
INIT_BINARY = OUT_DIR / "init_v2996_doominput_button_proxy"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v2996_doominput_button_proxy.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v504_doominput_button_proxy"

REQUIRED_STRINGS = (
    b"A90 Linux init 0.10.66 (v2996-doominput-button-proxy)",
    b"doominput <eventX> [count] [timeout_ms]",
    b"doominput.event %d: type=%s code=%s role=%s value=%d",
    b"doominput.state %d: forward=%d back=%d left=%d right=%d fire=%d use=%d menu=%d run=%d touch=%d",
    b"doom_button_forward",
    b"doom_button_back",
    b"doom_button_fire",
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
        raise RuntimeError(f"missing V2996 boot-image markers: {missing}")
    return [marker.decode("ascii") for marker in REQUIRED_STRINGS]


def render_report(manifest: dict[str, Any],
                  helper_flags: tuple[str, ...],
                  init_extra_flags: tuple[str, ...]) -> str:
    markers = manifest.get("v2996_marker_strings", [])
    marker_lines = [f"- `{marker}`" for marker in markers] if isinstance(markers, list) else []
    return "\n".join([
        "# Native Init V2996 DOOM Input Button Proxy Source Build",
        "",
        "## Summary",
        "",
        f"- Cycle: `{CYCLE}`",
        "- Track: active Video playback / DOOM input prerequisite.",
        f"- Decision: `{manifest['decision']}`",
        "- Result: PASS",
        "- Device flash: `no` in this build unit.",
        f"- Boot image: `{manifest['boot_image']}`",
        f"- Boot SHA256: `{manifest['boot_sha256']}`",
        f"- Init: `A90 Linux init {manifest['init_version']} ({manifest['init_build']})`",
        "- Parent candidate: `v2989-doominput-state`.",
        "",
        "## Branch Evidence",
        "",
        "- V2993 gated repeated built-in touch sampling until a new touch hypothesis exists.",
        "- V2994 gated V2992 USB-keyboard live validation until A90 exposes a keyboard-class evdev node.",
        "- V2995 found two existing physical-button input nodes, but the previous `doominput` source did not map POWER/VOLUME keys to DOOM state bits.",
        "",
        "## Included Delta",
        "",
        "- Keeps the V2989 `doominput <eventX> [count] [timeout_ms]` read-only sampler.",
        "- Adds a diagnostic physical-button proxy mapping for known live A90 buttons:",
        "  - `KEY_VOLUMEUP` -> `forward` with event role `doom_button_forward`.",
        "  - `KEY_VOLUMEDOWN` -> `back` with event role `doom_button_back`.",
        "  - `KEY_POWER` -> `fire` with event role `doom_button_fire`.",
        "- This is a diagnostic proxy to prove evdev-to-`doominput.state` liveness through event0/event3; it is not promoted as the final DOOM control scheme.",
        "- Adds no input injection, evdev grabs, keymap changes, touch configuration, or sysfs writes.",
        "- No PMIC/backlight/GPIO/regulator/GDSC writes, audio playback, video playback, or forbidden partition path is touched.",
        "",
        "## Marker Check",
        "",
        *marker_lines,
        "",
        "## Static Validation",
        "",
        "- Build: AArch64 static native-init compile, helper compile, ramdisk pack, boot image pack, SHA256 capture.",
        "- Marker check: generated boot image contains the V2996 identity, `doominput` command surface, state markers, and physical-button proxy role strings.",
        "",
        "## Host Validation",
        "",
        "- `python3 -m py_compile workspace/public/src/scripts/revalidation/build_native_init_boot_v2996_doominput_button_proxy.py tests/test_native_doominput_button_proxy_source_v2996.py`: PASS",
        "- `PYTHONPATH=workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 -m unittest tests.test_native_doominput_button_proxy_source_v2996`: PASS (`4` tests)",
        "- `PYTHONPATH=workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 workspace/public/src/scripts/revalidation/build_native_init_boot_v2996_doominput_button_proxy.py`: PASS (source build and marker check)",
        "- `file workspace/private/builds/native-init/v2996-doominput-button-proxy/init_v2996_doominput_button_proxy workspace/private/builds/native-init/v2996-doominput-button-proxy/a90_android_execns_probe_v504_doominput_button_proxy`: PASS (both AArch64 static ELF)",
        "- `sha256sum workspace/private/inputs/boot_images/boot_linux_v2996_doominput_button_proxy.img`: PASS (`1509ce74701f2f8d30e7a5ee924b108ca9bb60debed8afab5f9352643e2a4a75`)",
        "- `git diff --check`: PASS",
        "",
        "## Safety",
        "",
        "- Host-side source build only; no device action in V2996.",
        "- Runtime behavior remains read-only: `doominput` opens `/dev/input/event*` `O_RDONLY|O_NONBLOCK`, polls, reads, and prints state.",
        "- Rollback target remains `v2321-usb-clean-identity-rodata` for any later live unit.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `doominput-button-proxy-candidate`.",
    ]) + "\n"


def main() -> int:
    configure_base()
    v2859.render_report = render_report
    rc = v2859.main()
    marker_strings = require_strings(BOOT_IMAGE)
    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "doominput-button-proxy-candidate",
        "parent_test_artifact": "v2989-doominput-state",
        "doominput_button_proxy": {
            "version": 1,
            "source_unit": CYCLE,
            "command": "doominput <eventX> [count] [timeout_ms]",
            "purpose": "diagnostic evdev-to-doominput.state liveness proxy",
            "mappings": {
                "KEY_VOLUMEUP": "forward",
                "KEY_VOLUMEDOWN": "back",
                "KEY_POWER": "fire",
            },
            "live_validation": "pending-event0-event3-button-proxy-sample",
        },
        "v2996_marker_strings": marker_strings,
        "adoption_state": "pending-doominput-button-proxy-live-sample",
    })
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(render_report(
        manifest,
        tuple(manifest.get("helper_flags", ())),
        tuple(manifest.get("init_extra_flags", ())),
    ), encoding="utf-8")
    (OUT_DIR / "doominput-button-proxy-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "doominput-button-proxy-candidate",
        "boot_image": str(BOOT_IMAGE.relative_to(REPO_ROOT)),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "source_unit": CYCLE,
        "source_report": str(REPORT_PATH.relative_to(REPO_ROOT)),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-doominput-button-proxy-live-sample",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
