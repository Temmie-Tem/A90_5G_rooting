from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3154_doomgeneric_physical_exit_hud_pid_adopt.py"
)


class NativeDoomgenericPhysicalExitHudPidAdoptSourceV3154Tests(unittest.TestCase):
    def test_v3154_identity_and_contract(self) -> None:
        self.assertEqual(runner.CYCLE, "V3154")
        self.assertEqual(runner.INIT_VERSION, "0.10.136")
        self.assertEqual(
            runner.INIT_BUILD,
            "v3154-doomgeneric-physical-exit-hud-pid-adopt",
        )
        self.assertEqual(runner.AUDIO_CORUN_DURATION_MS, 240000)
        self.assertEqual(runner.AUDIO_CORUN_REFRESH_MS, 0)
        self.assertEqual(runner.PHYSICAL_BUTTON_EXIT, 1)

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"v3154-doomgeneric-physical-exit-hud-pid-adopt", required)
        self.assertIn(b"physical-button-exit", required)
        self.assertIn(b"video.demo.doom.return_menu.requested=1", required)
        self.assertIn(b"video.demo.doom.return_menu.reason=physical-button-exit", required)
        self.assertIn(b"video.demo.doom.return_menu.direct_present=1", required)
        self.assertIn(b"video.demo.doom.return_menu.existing_hud_alive=%d", required)
        self.assertIn(b"video.demo.doom.return_menu.spawn_hud_rc=%d", required)
        self.assertIn(b"video.demo.doom.return_menu.live_hud_pid=%ld", required)
        self.assertIn(b"video.demo.doom.return_menu.live_hud_alive=%d", required)
        self.assertIn(b"/tmp/a90-autohud.pid", required)
        self.assertNotIn(b"video.demo.doom.return_menu.autohud_rc=%d", required)

    def test_physical_exit_restores_menu_before_audio_stop(self) -> None:
        hud = Path("workspace/public/src/native-init/v319/30_status_hud.inc.c").read_text(
            encoding="utf-8"
        )
        requested = hud.index("if (physical_exit.requested) {")
        block = hud[requested:hud.index("\n    }", requested) + 6]

        self.assertIn("video_demo_doom_restore_menu_after_exit();", block)
        self.assertIn("video_demo_doom_audio_corun_stop();", block)
        self.assertNotIn('video_demo_doom_clear_presented_frame("physical-button-exit")', block)
        self.assertLess(
            block.index("video_demo_doom_restore_menu_after_exit();"),
            block.index("video_demo_doom_audio_corun_stop();"),
        )

    def test_restore_uses_hud_pid_adopt_with_input_reader_restart(self) -> None:
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
        self.assertIn("auto_hud_current_pid();", restore_block)
        self.assertIn("auto_hud_state_init(&state);", restore_block)
        self.assertIn("auto_hud_show_menu(&state, true);", restore_block)
        self.assertIn("auto_hud_draw_current_screen(&state);", restore_block)
        self.assertIn("start_auto_hud(BOOT_HUD_REFRESH_SECONDS, false);", restore_block)
        self.assertIn("a90_controller_request_menu_show();", restore_block)
        self.assertIn("a90_controller_set_menu_active(live_hud_alive);", restore_block)
        self.assertIn('video.demo.doom.return_menu.reason=physical-button-exit', restore_block)
        self.assertIn('video.demo.doom.return_menu.direct_present=1', restore_block)
        self.assertIn('video.demo.doom.return_menu.existing_hud_alive=%d', restore_block)
        self.assertIn('video.demo.doom.return_menu.spawn_hud_rc=%d', restore_block)
        self.assertIn('video.demo.doom.return_menu.live_hud_alive=%d', restore_block)
        self.assertNotIn("return_menu.autohud_rc", restore_block)

    def test_hud_pidfile_adopts_child_started_hud_for_cleanup(self) -> None:
        hud = Path("workspace/public/src/native-init/v319/30_status_hud.inc.c").read_text(
            encoding="utf-8"
        )
        menu = Path("workspace/public/src/native-init/v319/40_menu_apps.inc.c").read_text(
            encoding="utf-8"
        )

        self.assertIn('#define AUTO_HUD_PID_PATH "/tmp/a90-autohud.pid"', hud)
        self.assertIn("static pid_t auto_hud_pidfile_read(void)", hud)
        self.assertIn("static void auto_hud_pidfile_write(pid_t pid)", hud)
        self.assertIn("static pid_t auto_hud_adopt_pidfile(void)", hud)
        self.assertIn("pid_t before = a90_service_pid(A90_SERVICE_HUD);", hud)
        self.assertIn("if (before <= 0 && current > 0)", hud)
        self.assertIn("auto_hud_pidfile_clear();", hud)
        self.assertIn("auto_hud_pidfile_write(pid);", menu)

    def test_adapter_source_rewrites_to_v3154(self) -> None:
        source = runner.v3154_adapter_source()

        self.assertIn(
            "a90.doomgeneric.v3154.audio=real-sfx-pcm-stream-long-window-physical-exit-hud-pid-adopt",
            source,
        )
        self.assertIn("a90.doomgeneric.v3154.demo_hud=large-grouped-hw-doom-input", source)
        self.assertNotIn("v3151", source)


if __name__ == "__main__":
    unittest.main()
