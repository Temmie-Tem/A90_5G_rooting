"""Static checks for V3021 Bad Apple + Nyan demo checkpoint source build."""

from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


REPO = Path(__file__).resolve().parents[1]
STATUS_HUD = REPO / "workspace/public/src/native-init/v319/30_status_hud.inc.c"
MENU_APPS = REPO / "workspace/public/src/native-init/v319/40_menu_apps.inc.c"

runner = load_script("workspace/public/src/scripts/revalidation/build_native_init_boot_v3021_demo_checkpoint_badapple_nyan.py")


class NativeDemoCheckpointBadAppleNyanSourceV3021Tests(unittest.TestCase):
    def test_build_identity_and_marker_contract(self) -> None:
        self.assertEqual(runner.CYCLE, "V3021")
        self.assertEqual(runner.INIT_VERSION, "0.10.72")
        self.assertEqual(runner.INIT_BUILD, "v3021-demo-checkpoint-badapple-nyan")
        self.assertTrue(str(runner.BOOT_IMAGE).endswith("boot_linux_v3021_demo_checkpoint_badapple_nyan.img"))

        markers = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"A90 Linux init 0.10.72 (v3021-demo-checkpoint-badapple-nyan)", markers)
        self.assertIn(b"video.status.player_hud_incremental_panel=1", markers)
        self.assertIn(b"video.status.nyan_pal8_rle=1", markers)
        self.assertIn(b"badapple-480x360-full-v2903", markers)
        self.assertIn(b"menu.demo.badapple.action=play-av-fullsong", markers)
        self.assertIn(b"nyancat-v2973-pal8-rle-preview", markers)
        self.assertIn(b"menu.demo.nyan.action=play-av-preview", markers)
        self.assertIn(b"A90VSTR2", markers)
        self.assertIn(b"pal8-rle", markers)
        self.assertIn(b"video.demo.input=serial-doompad-consumed", markers)
        self.assertIn(b"video.demo.engine=doompad-loop-not-doomgeneric", markers)

    def test_current_video_status_exposes_all_demo_presets(self) -> None:
        text = STATUS_HUD.read_text(encoding="utf-8")

        self.assertIn('a90_console_printf("video.status.version=9\\r\\n");', text)
        self.assertIn('a90_console_printf("video.status.player_hud_incremental_panel=1\\r\\n");', text)
        self.assertIn('a90_console_printf("video.status.nyan_pal8_rle=1\\r\\n");', text)
        self.assertIn("VIDEO_CACHE_PRESET_BADAPPLE_NAME", text)
        self.assertIn("VIDEO_CACHE_PRESET_NYAN_NAME", text)
        self.assertIn("VIDEO_STREAM_VERSION_A90VSTR2", text)
        self.assertIn('strcmp(manifest->format, "pal8-rle")', text)
        self.assertIn("video_badapple_beat_flash_active", text)
        self.assertIn("video_demo_doom_status", text)

    def test_menu_launches_badapple_and_nyan_as_bounded_player_hud_demos(self) -> None:
        text = MENU_APPS.read_text(encoding="utf-8")

        self.assertIn('a90_console_printf("menu.demo.badapple.action=play-av-fullsong\\r\\n");', text)
        self.assertIn('a90_console_printf("menu.demo.badapple.frames=6962\\r\\n");', text)
        self.assertIn('a90_console_printf("menu.demo.badapple.audio_amplitude_milli=150\\r\\n");', text)
        self.assertIn('a90_console_printf("menu.demo.badapple.video_present=setcrtc\\r\\n");', text)
        self.assertIn('a90_console_printf("menu.demo.badapple.restore=menu\\r\\n");', text)
        self.assertIn('a90_console_printf("menu.demo.nyan.action=play-av-preview\\r\\n");', text)
        self.assertIn('a90_console_printf("menu.demo.nyan.frames=300\\r\\n");', text)
        self.assertIn('a90_console_printf("menu.demo.nyan.audio_amplitude_milli=150\\r\\n");', text)
        self.assertIn('a90_console_printf("menu.demo.nyan.video_present=setcrtc\\r\\n");', text)
        self.assertIn('a90_console_printf("menu.demo.nyan.restore=menu\\r\\n");', text)
        self.assertIn('auto_hud_show_menu(state, false);', text)
        self.assertNotIn("SpkrLeft BOOST", text)
        self.assertNotIn("backlight", text.lower())
        self.assertNotIn("regulator", text.lower())

    def test_render_report_describes_checkpoint_without_claiming_minor_release(self) -> None:
        manifest = {
            "decision": runner.DECISION,
            "boot_image": "workspace/private/inputs/boot_images/boot_linux_v3021_demo_checkpoint_badapple_nyan.img",
            "boot_sha256": "abc123",
            "init_version": runner.INIT_VERSION,
            "init_build": runner.INIT_BUILD,
            "v3021_marker_strings": [
                "menu.demo.badapple.action=play-av-fullsong",
                "menu.demo.nyan.action=play-av-preview",
                "video.demo.input=serial-doompad-consumed",
            ],
        }

        report = runner.render_report(manifest, ("helper",), ("init",))

        self.assertIn("Native Init V3021 Demo Checkpoint Bad Apple + Nyan Source Build", report)
        self.assertIn("kept demo checkpoint", report)
        self.assertIn("0.10.72", report)
        self.assertIn("not a 0.11.0 video-epic closeout", report)
        self.assertIn("Bad Apple", report)
        self.assertIn("Nyan", report)
        self.assertIn("does not claim WAD-backed `doomgeneric`", report)
        self.assertIn("pending-badapple-nyan-same-image-live-validation", report)


if __name__ == "__main__":
    unittest.main()
