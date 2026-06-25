from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


ROOT = Path(__file__).resolve().parents[1]
STATUS_HUD = ROOT / "workspace/public/src/native-init/v319/30_status_hud.inc.c"

runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3157_video_epic_promotion.py"
)


class NativeVideoEpicPromotionSourceV3157Tests(unittest.TestCase):
    def test_v3157_identity_and_promotion_contract(self) -> None:
        self.assertEqual(runner.CYCLE, "V3157")
        self.assertEqual(runner.INIT_VERSION, "0.11.0")
        self.assertEqual(runner.INIT_BUILD, "v3157-video-epic-promotion")
        self.assertEqual(runner.VIDEO_PLAYER_HUD_TEXT_INTERVAL_FRAMES, 15)
        self.assertEqual(runner.VIDEO_PLAYER_HUD_FULL_REPAINT_INTERVAL_FRAMES, 300)

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"0.11.0", required)
        self.assertIn(b"v3157-video-epic-promotion", required)
        self.assertIn(b"video.status.player_hud_text_interval_frames=%u", required)
        self.assertIn(b"video.status.player_hud_full_repaint_interval_frames=%u", required)
        self.assertIn(b"video.status.stream_timing_probe=1", required)
        self.assertIn(b"video.stream.timing.render.avg_us", required)
        self.assertIn(b"video.demo.doom.return_menu.reason=physical-button-exit", required)
        self.assertIn(b"a90.doomgeneric.v3157.input_thread=background-drain-udp-unix-dgram", required)
        self.assertIn(b"USB-NCM UDP EVDEV keyboard", required)
        self.assertNotIn(b"v3156-video-player-hud-cadence", required)

    def test_source_keeps_video_player_hud_cadence_fix(self) -> None:
        source = STATUS_HUD.read_text(encoding="utf-8")

        self.assertIn("#define VIDEO_PLAYER_HUD_TEXT_INTERVAL_FRAMES 15U", source)
        self.assertIn("#define VIDEO_PLAYER_HUD_FULL_REPAINT_INTERVAL_FRAMES 300U", source)
        self.assertIn("frame_index % VIDEO_PLAYER_HUD_FULL_REPAINT_INTERVAL_FRAMES", source)
        self.assertIn("frame_index - text_frame >= VIDEO_PLAYER_HUD_TEXT_INTERVAL_FRAMES", source)
        self.assertIn("video.stream.timing.render.avg_us", source)

    def test_manifest_postprocess_marks_three_demo_promotion(self) -> None:
        text = Path(
            "workspace/public/src/scripts/revalidation/build_native_init_boot_v3157_video_epic_promotion.py"
        ).read_text(encoding="utf-8")

        self.assertIn('"requires_live_validation": ["badapple", "nyan", "doom"]', text)
        self.assertIn('"bundled_demos": ["badapple", "nyan", "doom"]', text)
        self.assertIn('"source_baseline": "v3156-video-player-hud-cadence"', text)
        self.assertIn('"adoption_state": "pending-video-0.11.0-promotion-live-validation"', text)

    def test_adapter_source_rewrites_to_v3157(self) -> None:
        source = runner.v3157_adapter_source()

        self.assertIn("a90.doomgeneric.v3157.audio=real-sfx-pcm-stream-video-epic-promotion", source)
        self.assertIn("a90.doomgeneric.v3157.demo_hud=large-grouped-hw-doom-input", source)
        self.assertNotIn("v3156", source)
        self.assertNotIn("v3154", source)


if __name__ == "__main__":
    unittest.main()
