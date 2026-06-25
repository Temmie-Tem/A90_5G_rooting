from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3155_doomgeneric_sfx_best_effort_video_cadence.py"
)


class NativeDoomgenericSfxBestEffortVideoCadenceSourceV3155Tests(unittest.TestCase):
    def test_v3155_identity_and_contract(self) -> None:
        self.assertEqual(runner.CYCLE, "V3155")
        self.assertEqual(runner.INIT_VERSION, "0.10.137")
        self.assertEqual(
            runner.INIT_BUILD,
            "v3155-doomgeneric-sfx-best-effort-video-cadence",
        )
        self.assertEqual(runner.AUDIO_CORUN_DURATION_MS, 240000)
        self.assertEqual(runner.AUDIO_CORUN_REFRESH_MS, 0)
        self.assertEqual(runner.PHYSICAL_BUTTON_EXIT, 1)

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"v3155-doomgeneric-sfx-best-effort-video-cadence", required)
        self.assertIn(b"best-effort-video-cadence", required)
        self.assertIn(b"physical-button-exit", required)
        self.assertIn(b"video.demo.doom.return_menu.reason=physical-button-exit", required)
        self.assertIn(b"video.demo.doom.return_menu.direct_present=1", required)
        self.assertIn(b"/tmp/a90-autohud.pid", required)
        self.assertNotIn(b"v3154-doomgeneric-physical-exit-hud-pid-adopt", required)

    def test_sfx_backend_is_best_effort_nonblocking(self) -> None:
        source = runner.SFX_BACKEND_SOURCE_TEXT

        self.assertIn(
            '#define A90_SFX_STREAM_PATH "/cache/a90-runtime/a90-doomgeneric-v3155-sfx.pcmstream"',
            source,
        )
        self.assertIn("static int write_best_effort", source)
        self.assertIn("errno == EAGAIN", source)
        self.assertIn("return true;", source)
        self.assertIn("stream_fd = open_stream_once();", source)
        self.assertIn("int write_rc = write_best_effort", source)
        self.assertNotIn("flags & ~O_NONBLOCK", source)
        self.assertNotIn("for (attempt = 0; attempt < 500; ++attempt)", source)
        self.assertNotIn("write_full", source)

    def test_physical_exit_menu_recovery_is_preserved(self) -> None:
        hud = Path("workspace/public/src/native-init/v319/30_status_hud.inc.c").read_text(
            encoding="utf-8"
        )
        menu = Path("workspace/public/src/native-init/v319/40_menu_apps.inc.c").read_text(
            encoding="utf-8"
        )
        requested = hud.index("if (physical_exit.requested) {")
        block = hud[requested:hud.index("\n    }", requested) + 6]
        restore = menu.index("static int video_demo_doom_restore_menu_after_exit(void)")
        restore_block = menu[restore:menu.index("\n}", restore) + 2]

        self.assertIn("video_demo_doom_restore_menu_after_exit();", block)
        self.assertIn("video_demo_doom_audio_corun_stop();", block)
        self.assertLess(
            block.index("video_demo_doom_restore_menu_after_exit();"),
            block.index("video_demo_doom_audio_corun_stop();"),
        )
        self.assertIn("auto_hud_current_pid();", restore_block)
        self.assertIn("start_auto_hud(BOOT_HUD_REFRESH_SECONDS, false);", restore_block)
        self.assertIn("auto_hud_pidfile_write(pid);", menu)

    def test_adapter_source_rewrites_to_v3155(self) -> None:
        source = runner.v3155_adapter_source()

        self.assertIn(
            "a90.doomgeneric.v3155.audio=real-sfx-pcm-stream-best-effort-video-cadence",
            source,
        )
        self.assertIn("a90.doomgeneric.v3155.demo_hud=large-grouped-hw-doom-input", source)
        self.assertNotIn("v3154", source)


if __name__ == "__main__":
    unittest.main()
