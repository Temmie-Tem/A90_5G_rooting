#!/usr/bin/env python3
"""Build V2987 native-init candidate with decoded readinput events."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _workspace_bootstrap import repo_root
import build_native_init_boot_v2859_audio_changelog_latest_refresh as v2859
from a90harness.evidence import workspace_private_build_path, workspace_private_input_path

REPO_ROOT = repo_root()

CYCLE = "V2987"
INIT_VERSION = "0.10.64"
INIT_BUILD = "v2987-readinput-doom-decode"
BUILD_TAG = INIT_BUILD
DECISION = "v2987-readinput-doom-decode-source-build-pass"

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
REPORT_PATH = REPO_ROOT / "docs/reports/NATIVE_INIT_V2987_READINPUT_DOOM_DECODE_SOURCE_BUILD_2026-06-20.md"
BOOT_IMAGE = workspace_private_input_path("boot_images", "boot_linux_v2987_readinput_doom_decode.img", legacy_fallback=False)
INIT_BINARY = OUT_DIR / "init_v2987_readinput_doom_decode"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v2987_readinput_doom_decode.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v502_readinput_doom_decode"

REQUIRED_STRINGS = (
    b"A90 Linux init 0.10.64 (v2987-readinput-doom-decode)",
    b"readinput <eventX> [count] [timeout_ms]",
    b"event.decode %d: type=%s code=%s role=%s value=%d",
    b"ABS_MT_SLOT",
    b"ABS_MT_TRACKING_ID",
    b"ABS_MT_POSITION_X",
    b"ABS_MT_POSITION_Y",
    b"BTN_TOUCH",
    b"SYN_REPORT",
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
        raise RuntimeError(f"missing V2987 boot-image markers: {missing}")
    return [marker.decode("ascii") for marker in REQUIRED_STRINGS]


def render_report(manifest: dict[str, Any],
                  helper_flags: tuple[str, ...],
                  init_extra_flags: tuple[str, ...]) -> str:
    markers = manifest.get("v2987_marker_strings", [])
    marker_lines = [f"- `{marker}`" for marker in markers] if isinstance(markers, list) else []
    return "\n".join([
        "# Native Init V2987 Readinput DOOM Decode Source Build",
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
        "- Parent candidate: `v2985-doom-keyboard-caps`.",
        "",
        "## Branch Evidence",
        "",
        "- V2984 proved the touch nodes expose MT capability bits and are not runtime-PM suspended.",
        "- V2985 added DOOM keyboard fallback capability bits, and V2986 staged the exact live keyboard handoff.",
        "- A USB keyboard is not currently enumerated on v2321, so this source unit improves the shared `readinput` evidence surface without flashing.",
        "",
        "## Included Delta",
        "",
        "- Keeps the existing numeric `event N: type=0x.... code=0x.... value=...` line unchanged for host parser compatibility.",
        "- Adds a second `event.decode N: type=... code=... role=... value=...` line for each captured evdev event.",
        "- Decodes multitouch protocol-B landmarks: `ABS_MT_SLOT`, `ABS_MT_TRACKING_ID`, `ABS_MT_POSITION_X`, `ABS_MT_POSITION_Y`, `BTN_TOUCH`, and `SYN_REPORT`.",
        "- Decodes DOOM fallback keyboard roles for WASD, arrow keys, Enter/Space, Ctrl, Shift, and Esc.",
        "- Adds no input injection, evdev grabs, keymap changes, touch configuration, or sysfs writes.",
        "",
        "## Marker Check",
        "",
        *marker_lines,
        "",
        "## Static Validation",
        "",
        "- Build: AArch64 static native-init compile, helper compile, ramdisk pack, boot image pack, SHA256 capture.",
        "- Marker check: generated boot image contains the V2987 identity plus touch/keyboard decode strings.",
        "",
        "## Safety",
        "",
        "- Host-side source build only; no device action in V2987.",
        "- Runtime behavior remains read-only: `readinput` opens `/dev/input/event*` `O_RDONLY|O_NONBLOCK` and prints decoded labels for events it already reads.",
        "- No PMIC/backlight/GPIO/regulator/GDSC, Wi-Fi, audio route, video playback, or forbidden partition path is touched.",
        "- Rollback target remains `v2321-usb-clean-identity-rodata` for any later live unit.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `readinput-doom-decode-candidate`.",
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
        "candidate_type": "readinput-doom-decode-candidate",
        "parent_test_artifact": "v2985-doom-keyboard-caps",
        "readinput_decode": {
            "version": 1,
            "source_unit": CYCLE,
            "numeric_event_line_unchanged": True,
            "decoded_event_line": "event.decode N: type=... code=... role=... value=...",
            "touch_roles": ["touch_slot", "touch_tracking", "touch_x", "touch_y", "touch_contact", "frame"],
            "doom_roles": ["doom_forward", "doom_back", "doom_left", "doom_right", "doom_use", "doom_fire", "doom_menu", "doom_run"],
            "live_validation": "pending-readinput-touch-or-keyboard-sample",
        },
        "v2987_marker_strings": marker_strings,
        "adoption_state": "pending-live-readinput-sample",
    })
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(render_report(
        manifest,
        tuple(manifest.get("helper_flags", ())),
        tuple(manifest.get("init_extra_flags", ())),
    ), encoding="utf-8")
    (OUT_DIR / "readinput-doom-decode-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "readinput-doom-decode-candidate",
        "boot_image": str(BOOT_IMAGE.relative_to(REPO_ROOT)),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "source_unit": CYCLE,
        "source_report": str(REPORT_PATH.relative_to(REPO_ROOT)),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-live-readinput-sample",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
