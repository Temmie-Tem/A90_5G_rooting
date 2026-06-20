#!/usr/bin/env python3
"""Build V3000 native-init candidate with a status-only DOOM demo surface."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _workspace_bootstrap import repo_root
import build_native_init_boot_v2859_audio_changelog_latest_refresh as v2859
from a90harness.evidence import workspace_private_build_path, workspace_private_input_path

REPO_ROOT = repo_root()

CYCLE = "V3000"
INIT_VERSION = "0.10.68"
INIT_BUILD = "v3000-doom-status-stub"
BUILD_TAG = INIT_BUILD
DECISION = "v3000-doom-status-stub-source-build-pass"

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
REPORT_PATH = REPO_ROOT / "docs/reports/NATIVE_INIT_V3000_DOOM_STATUS_STUB_SOURCE_BUILD_2026-06-20.md"
BOOT_IMAGE = workspace_private_input_path("boot_images", "boot_linux_v3000_doom_status_stub.img", legacy_fallback=False)
INIT_BINARY = OUT_DIR / "init_v3000_doom_status_stub"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v3000_doom_status_stub.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v506_doom_status_stub"

REQUIRED_STRINGS = (
    b"A90 Linux init 0.10.68 (v3000-doom-status-stub)",
    b"video.status.doom_stub=1",
    b"video.status.doom_input=not-proven",
    b"video.demo.status=blocked-input-prerequisite",
    b"video.demo.input.button_mux=v2999-doominput-mux-live",
    b"video.demo.input.next=doominputmux event3,event0 24 45000",
    b"menu.demo.doom.action=status-only",
    b"menu.demo.doom.input.live_handoff=v2999-doominput-mux-live",
    b"menu.demo.doom.input.command=doominputmux event3,event0 24 45000",
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
        raise RuntimeError(f"missing V3000 boot-image markers: {missing}")
    return [marker.decode("ascii") for marker in REQUIRED_STRINGS]


def render_report(manifest: dict[str, Any],
                  helper_flags: tuple[str, ...],
                  init_extra_flags: tuple[str, ...]) -> str:
    markers = manifest.get("v3000_marker_strings", [])
    marker_lines = [f"- `{marker}`" for marker in markers] if isinstance(markers, list) else []
    return "\n".join([
        "# Native Init V3000 DOOM Status Stub Source Build",
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
        "- Parent live handoff: `v2999-doominput-mux-live`.",
        "",
        "## Branch Evidence",
        "",
        "- Bad Apple and Nyan Cat already cover the KMS/audio demo surface.",
        "- DOOM remains blocked on input liveness: touch events are not proven, and the current live handoff is the V2999 `doominputmux event3,event0` operator-button sample.",
        "- The device menu should expose that status without claiming that DOOM is playable.",
        "",
        "## Included Delta",
        "",
        "- Adds a `DOOM` entry under the DEMO menu with the subtitle `INPUT PREREQ STATUS`.",
        "- Extends `video status` and `video demo doom status` to report the DOOM blocker and exact V2999 live handoff command.",
        "- Routes `SCREEN_MENU_DEMO_DOOM` to `video demo doom status` only.",
        "- Records the current DOOM input state as `not-proven` rather than silently falling through to a playback path.",
        "- `video demo doom verify` and `video demo doom play` remain blocked with `-EAGAIN` until input is proven.",
        "- Adds no DOOM WAD, no gameplay loop, no input injection, no video/audio playback, and no sysfs writes.",
        "- No PMIC/backlight/GPIO/regulator/GDSC writes, Wi-Fi, or forbidden partition path is touched.",
        "",
        "## Marker Check",
        "",
        *marker_lines,
        "",
        "## Static Validation",
        "",
        "- Build: AArch64 static native-init compile, helper compile, ramdisk pack, boot image pack, SHA256 capture.",
        "- Marker check: generated boot image contains the V3000 identity, status-only DOOM menu strings, and V2999 live handoff pointers.",
        "",
        "## Host Validation",
        "",
        "- `python3 -m py_compile workspace/public/src/scripts/revalidation/build_native_init_boot_v3000_doom_status_stub.py tests/test_native_doom_status_stub_source_v3000.py`: PASS",
        "- `PYTHONPATH=workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 -m unittest tests.test_native_doom_status_stub_source_v3000`: PASS",
        "- `PYTHONPATH=workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 workspace/public/src/scripts/revalidation/build_native_init_boot_v3000_doom_status_stub.py`: PASS (source build and marker check)",
        "- `file workspace/private/builds/native-init/v3000-doom-status-stub/init_v3000_doom_status_stub workspace/private/builds/native-init/v3000-doom-status-stub/a90_android_execns_probe_v506_doom_status_stub`: PASS (both AArch64 static ELF)",
        f"- `sha256sum workspace/private/inputs/boot_images/boot_linux_v3000_doom_status_stub.img`: PASS (`{manifest['boot_sha256']}`)",
        "- `git diff --check`: PASS",
        "",
        "## Safety",
        "",
        "- Host-side source build only; no device action in V3000.",
        "- The new DOOM surface is status-only and does not start playback or sample input.",
        "- Rollback target remains `v2321-usb-clean-identity-rodata` for any later live unit.",
        "",
        "## Next",
        "",
        "- Run the V2999 live handoff only when an operator can press VOLUMEUP/VOLUMEDOWN/POWER during the single bounded mux window.",
        "- If that proves button liveness, the next DOOM branch can map a minimal menu-driven control path; if it times out, keep the blocker visible and pursue the USB-keyboard fallback explicitly.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `doom-status-stub-candidate`.",
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
        "candidate_type": "doom-status-stub-candidate",
        "parent_live_handoff": "v2999-doominput-mux-live",
        "doom_status_stub": {
            "version": 1,
            "source_unit": CYCLE,
            "menu_action": "SCREEN_MENU_DEMO_DOOM",
            "menu_command": "video demo doom status",
            "status": "blocked-input-prerequisite",
            "input_state": "not-proven",
            "next_live_handoff": "doominputmux event3,event0 24 45000",
            "verify_play_rc": "-EAGAIN",
        },
        "v3000_marker_strings": marker_strings,
        "adoption_state": "status-only-until-doom-input-proven",
    })
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(render_report(
        manifest,
        tuple(manifest.get("helper_flags", ())),
        tuple(manifest.get("init_extra_flags", ())),
    ), encoding="utf-8")
    (OUT_DIR / "doom-status-stub-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "doom-status-stub-candidate",
        "boot_image": str(BOOT_IMAGE.relative_to(REPO_ROOT)),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "source_unit": CYCLE,
        "source_report": str(REPORT_PATH.relative_to(REPO_ROOT)),
        "parent_live_handoff": "v2999-doominput-mux-live",
        "adoption_state": "status-only-until-doom-input-proven",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
