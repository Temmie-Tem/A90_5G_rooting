from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3151_doomgeneric_physical_exit_menu_return.py"
)


class NativeDoomgenericPhysicalExitMenuReturnSourceV3151Tests(unittest.TestCase):
    def test_v3151_identity_and_contract(self) -> None:
        self.assertEqual(runner.CYCLE, "V3151")
        self.assertEqual(runner.INIT_VERSION, "0.10.133")
        self.assertEqual(runner.INIT_BUILD, "v3151-doomgeneric-physical-exit-menu-return")
        self.assertEqual(runner.AUDIO_CORUN_DURATION_MS, 240000)
        self.assertEqual(runner.AUDIO_CORUN_REFRESH_MS, 0)
        self.assertEqual(runner.PHYSICAL_BUTTON_EXIT, 1)

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"v3151-doomgeneric-physical-exit-menu-return", required)
        self.assertIn(b"physical-button-exit", required)
        self.assertIn(b"video.demo.doom.return_menu.requested=1", required)
        self.assertIn(b"video.demo.doom.return_menu.autohud_rc=%d", required)
        self.assertIn(b"video.demo.doom.return_menu.active=%d", required)

    def test_physical_exit_restores_menu_after_clear_and_audio_stop(self) -> None:
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

        menu = Path("workspace/public/src/native-init/v319/40_menu_apps.inc.c").read_text(
            encoding="utf-8"
        )
        joined = hud + menu
        self.assertIn("static int video_demo_doom_restore_menu_after_exit(void)", joined)
        self.assertIn("a90_controller_request_menu_show();", joined)
        self.assertIn("a90_controller_set_menu_active", joined)
        self.assertIn('video.demo.doom.return_menu.requested=1', joined)

    def test_adapter_source_rewrites_to_v3151(self) -> None:
        source = runner.v3151_adapter_source()

        self.assertIn(
            "a90.doomgeneric.v3151.audio=real-sfx-pcm-stream-long-window-physical-exit-menu-return",
            source,
        )
        self.assertIn("a90.doomgeneric.v3151.demo_hud=large-grouped-hw-doom-input", source)
        self.assertNotIn("v3150", source)


if __name__ == "__main__":
    unittest.main()
