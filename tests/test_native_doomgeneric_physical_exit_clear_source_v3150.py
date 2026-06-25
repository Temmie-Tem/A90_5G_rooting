from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3150_doomgeneric_physical_exit_clear.py"
)


class NativeDoomgenericPhysicalExitClearSourceV3150Tests(unittest.TestCase):
    def test_v3150_identity_and_contract(self) -> None:
        self.assertEqual(runner.CYCLE, "V3150")
        self.assertEqual(runner.INIT_VERSION, "0.10.132")
        self.assertEqual(runner.INIT_BUILD, "v3150-doomgeneric-physical-exit-clear")
        self.assertEqual(runner.AUDIO_CORUN_DURATION_MS, 240000)
        self.assertEqual(runner.AUDIO_CORUN_REFRESH_MS, 0)
        self.assertEqual(runner.PHYSICAL_BUTTON_EXIT, 1)

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"v3150-doomgeneric-physical-exit-clear", required)
        self.assertIn(b"physical-button-exit", required)
        self.assertIn(b"video.demo.doom.clear.reason=%s", required)

    def test_physical_exit_clears_display_before_audio_stop(self) -> None:
        hud = Path("workspace/public/src/native-init/v319/30_status_hud.inc.c").read_text(
            encoding="utf-8"
        )
        requested = hud.index("if (physical_exit.requested) {")
        block = hud[requested:hud.index("\n    }", requested) + 6]

        self.assertIn('video_demo_doom_clear_presented_frame("physical-button-exit")', block)
        self.assertIn("video_demo_doom_audio_corun_stop();", block)
        self.assertLess(
            block.index('video_demo_doom_clear_presented_frame("physical-button-exit")'),
            block.index("video_demo_doom_audio_corun_stop();"),
        )

    def test_adapter_source_rewrites_to_v3150(self) -> None:
        source = runner.v3150_adapter_source()

        self.assertIn(
            "a90.doomgeneric.v3150.audio=real-sfx-pcm-stream-long-window-physical-exit-clear",
            source,
        )
        self.assertIn("a90.doomgeneric.v3150.demo_hud=large-grouped-hw-doom-input", source)
        self.assertNotIn("v3149", source)


if __name__ == "__main__":
    unittest.main()
