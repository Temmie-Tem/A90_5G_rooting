from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3152_doomgeneric_physical_exit_direct_menu_present.py"
)


class NativeDoomgenericPhysicalExitDirectMenuPresentSourceV3152Tests(unittest.TestCase):
    def test_v3152_identity_and_contract(self) -> None:
        self.assertEqual(runner.CYCLE, "V3152")
        self.assertEqual(runner.INIT_VERSION, "0.10.134")
        self.assertEqual(
            runner.INIT_BUILD,
            "v3152-doomgeneric-physical-exit-direct-menu-present",
        )
        self.assertEqual(runner.AUDIO_CORUN_DURATION_MS, 240000)
        self.assertEqual(runner.AUDIO_CORUN_REFRESH_MS, 0)
        self.assertEqual(runner.PHYSICAL_BUTTON_EXIT, 1)

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"v3152-doomgeneric-physical-exit-direct-menu-present", required)
        self.assertIn(b"physical-button-exit", required)
        self.assertIn(b"video.demo.doom.return_menu.requested=1", required)
        self.assertIn(b"video.demo.doom.return_menu.direct_present=1", required)
        self.assertIn(b"video.demo.doom.return_menu.existing_hud_alive=%d", required)
        self.assertNotIn(b"video.demo.doom.return_menu.autohud_rc=%d", required)

    def test_physical_exit_calls_restore_after_clear_and_audio_stop(self) -> None:
        hud = Path("workspace/public/src/native-init/v319/30_status_hud.inc.c").read_text(
            encoding="utf-8"
        )
        requested = hud.index("if (physical_exit.requested) {")
        block = hud[requested:hud.index("\n    }", requested) + 6]

        self.assertIn('video_demo_doom_clear_presented_frame("physical-button-exit")', block)
        self.assertIn("video_demo_doom_audio_corun_stop();", block)
        self.assertIn("video_demo_doom_restore_menu_after_exit();", block)
        self.assertLess(
            block.index('video_demo_doom_clear_presented_frame("physical-button-exit")'),
            block.index("video_demo_doom_audio_corun_stop();"),
        )
        self.assertLess(
            block.index("video_demo_doom_audio_corun_stop();"),
            block.index("video_demo_doom_restore_menu_after_exit();"),
        )

    def test_restore_uses_direct_menu_present_without_child_hud_start(self) -> None:
        hud = Path("workspace/public/src/native-init/v319/30_status_hud.inc.c").read_text(
            encoding="utf-8"
        )
        menu = Path("workspace/public/src/native-init/v319/40_menu_apps.inc.c").read_text(
            encoding="utf-8"
        )
        restore = menu.index("static int video_demo_doom_restore_menu_after_exit(void)")
        restore_block = menu[restore:menu.index("\n}", restore) + 2]

        self.assertNotIn(
            "static int video_demo_doom_restore_menu_after_exit(void) {",
            hud,
        )
        self.assertIn("auto_hud_state_init(&state);", restore_block)
        self.assertIn("auto_hud_show_menu(&state, true);", restore_block)
        self.assertIn("auto_hud_draw_current_screen(&state);", restore_block)
        self.assertIn("a90_controller_request_menu_show();", restore_block)
        self.assertIn("a90_controller_set_menu_active(hud_alive);", restore_block)
        self.assertIn('video.demo.doom.return_menu.direct_present=1', restore_block)
        self.assertIn('video.demo.doom.return_menu.existing_hud_alive=%d', restore_block)
        self.assertNotIn("start_auto_hud(", restore_block)
        self.assertNotIn("return_menu.autohud_rc", restore_block)

    def test_adapter_source_rewrites_to_v3152(self) -> None:
        source = runner.v3152_adapter_source()

        self.assertIn(
            "a90.doomgeneric.v3152.audio=real-sfx-pcm-stream-long-window-physical-exit-direct-menu-present",
            source,
        )
        self.assertIn("a90.doomgeneric.v3152.demo_hud=large-grouped-hw-doom-input", source)
        self.assertNotIn("v3151", source)


if __name__ == "__main__":
    unittest.main()
