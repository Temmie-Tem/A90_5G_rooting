#!/usr/bin/env python3
"""Build V2989 native-init candidate with DOOM input state sampling."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _workspace_bootstrap import repo_root
import build_native_init_boot_v2859_audio_changelog_latest_refresh as v2859
from a90harness.evidence import workspace_private_build_path, workspace_private_input_path

REPO_ROOT = repo_root()

CYCLE = "V2989"
INIT_VERSION = "0.10.65"
INIT_BUILD = "v2989-doominput-state"
BUILD_TAG = INIT_BUILD
DECISION = "v2989-doominput-state-source-build-pass"

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
REPORT_PATH = REPO_ROOT / "docs/reports/NATIVE_INIT_V2989_DOOMINPUT_STATE_SOURCE_BUILD_2026-06-20.md"
BOOT_IMAGE = workspace_private_input_path("boot_images", "boot_linux_v2989_doominput_state.img", legacy_fallback=False)
INIT_BINARY = OUT_DIR / "init_v2989_doominput_state"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v2989_doominput_state.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v503_doominput_state"

REQUIRED_STRINGS = (
    b"A90 Linux init 0.10.65 (v2989-doominput-state)",
    b"doominput <eventX> [count] [timeout_ms]",
    b"doominput.event %d: type=%s code=%s role=%s value=%d",
    b"doominput.state %d: forward=%d back=%d left=%d right=%d fire=%d use=%d menu=%d run=%d touch=%d",
    b"has_x=%d has_y=%d tracking=%d slot=%d pressure=%d has_pressure=%d active=%d frame=%u",
    b"doom_forward",
    b"doom_back",
    b"doom_left",
    b"doom_right",
    b"doom_use",
    b"doom_fire",
    b"doom_menu",
    b"doom_run",
    b"touch_x",
    b"touch_y",
    b"touch_tracking",
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
        raise RuntimeError(f"missing V2989 boot-image markers: {missing}")
    return [marker.decode("ascii") for marker in REQUIRED_STRINGS]


def render_report(manifest: dict[str, Any],
                  helper_flags: tuple[str, ...],
                  init_extra_flags: tuple[str, ...]) -> str:
    markers = manifest.get("v2989_marker_strings", [])
    marker_lines = [f"- `{marker}`" for marker in markers] if isinstance(markers, list) else []
    return "\n".join([
        "# Native Init V2989 DOOM Input State Source Build",
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
        "- Parent candidate: `v2987-readinput-doom-decode`.",
        "",
        "## Branch Evidence",
        "",
        "- V2984 proved `event6` and `event8` expose touch/MT capability bits and are not sysfs runtime-PM suspended.",
        "- V2988 proved the V2987 decoded `readinput` candidate boots cleanly, but the bounded touch sample still produced `0` decoded events before rollback.",
        "- Repeating the same no-event live sample without fresh operator input or a USB keyboard would be low-information; this source unit prepares the DOOM state surface for the next successful event sample.",
        "",
        "## Included Delta",
        "",
        "- Adds `doominput <eventX> [count] [timeout_ms]` as a read-only evdev sampler.",
        "- Reuses the V2987 decoded event names and prints `doominput.event` plus `doominput.state` for every captured event.",
        "- Tracks DOOM keyboard roles: forward/back/left/right, fire, use, menu, and run.",
        "- Tracks touch state without inventing controls: contact, x/y, slot, tracking id, pressure, active, and SYN frame count.",
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
        "- Marker check: generated boot image contains the V2989 identity, `doominput` command surface, state markers, and retained V2987 decode role strings.",
        "",
        "## Safety",
        "",
        "- Host-side source build only; no device action in V2989.",
        "- Runtime behavior remains read-only: `doominput` opens `/dev/input/event*` `O_RDONLY|O_NONBLOCK`, polls, reads, and prints state.",
        "- Rollback target remains `v2321-usb-clean-identity-rodata` for any later live unit.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `doominput-state-candidate`.",
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
        "candidate_type": "doominput-state-candidate",
        "parent_test_artifact": "v2987-readinput-doom-decode",
        "doominput_state": {
            "version": 1,
            "source_unit": CYCLE,
            "command": "doominput <eventX> [count] [timeout_ms]",
            "event_line": "doominput.event N: type=... code=... role=... value=...",
            "state_line": "doominput.state N: forward=... back=... touch=... active=...",
            "keyboard_roles": ["forward", "back", "left", "right", "fire", "use", "menu", "run"],
            "touch_fields": ["touch", "x", "y", "has_x", "has_y", "tracking", "slot", "pressure", "frame"],
            "live_validation": "pending-doominput-touch-or-keyboard-sample",
        },
        "v2989_marker_strings": marker_strings,
        "adoption_state": "pending-doominput-live-sample",
    })
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(render_report(
        manifest,
        tuple(manifest.get("helper_flags", ())),
        tuple(manifest.get("init_extra_flags", ())),
    ), encoding="utf-8")
    (OUT_DIR / "doominput-state-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "doominput-state-candidate",
        "boot_image": str(BOOT_IMAGE.relative_to(REPO_ROOT)),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "source_unit": CYCLE,
        "source_report": str(REPORT_PATH.relative_to(REPO_ROOT)),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-doominput-live-sample",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
