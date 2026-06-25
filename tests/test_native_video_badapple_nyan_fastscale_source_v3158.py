from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


ROOT = Path(__file__).resolve().parents[1]
STATUS_HUD = ROOT / "workspace/public/src/native-init/v319/30_status_hud.inc.c"

runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3158_badapple_nyan_fastscale.py"
)


class NativeVideoBadappleNyanFastscaleSourceV3158Tests(unittest.TestCase):
    def test_v3158_identity_and_fastscale_contract(self) -> None:
        self.assertEqual(runner.CYCLE, "V3158")
        self.assertEqual(runner.INIT_VERSION, "0.11.1")
        self.assertEqual(runner.INIT_BUILD, "v3158-badapple-nyan-fastscale")
        self.assertEqual(runner.VIDEO_PLAYER_HUD_TEXT_INTERVAL_FRAMES, 15)
        self.assertEqual(runner.VIDEO_PLAYER_HUD_FULL_REPAINT_INTERVAL_FRAMES, 300)

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"0.11.1", required)
        self.assertIn(b"v3158-badapple-nyan-fastscale", required)
        self.assertIn(b"video.status.player_hud_fastscale=1", required)
        self.assertIn(b"video.status.player_hud_text_interval_frames=%u", required)
        self.assertIn(b"video.status.player_hud_full_repaint_interval_frames=%u", required)
        self.assertIn(b"video.status.stream_timing_probe=1", required)
        self.assertIn(b"video.stream.timing.render.avg_us", required)
        self.assertIn(b"a90.doomgeneric.v3158.input_thread=background-drain-udp-unix-dgram", required)
        self.assertNotIn(b"v3157-video-epic-promotion", required)

    def test_source_adds_player_hud_fastscale_paths(self) -> None:
        source = STATUS_HUD.read_text(encoding="utf-8")

        self.assertIn('a90_console_printf("video.status.player_hud_fastscale=1\\r\\n");', source)
        self.assertIn("video_expand_mono1_frame_scaled2", source)
        self.assertIn("video_expand_pal8_indices_scaled2", source)
        self.assertIn("video_expand_pal8_rle_scaled2", source)
        self.assertIn("mode == VIDEO_STREAM_PAL8_RLE_MODE", source)
        self.assertIn("return video_expand_pal8_rle_scaled2", source)
        self.assertIn("return video_expand_mono1_frame_scaled2", source)

    def test_source_bounds_repaint_and_progress_updates(self) -> None:
        source = STATUS_HUD.read_text(encoding="utf-8")

        self.assertIn("previous_progress_fill", source)
        self.assertIn("progress_fill - previous_progress_fill", source)
        self.assertIn("previous_progress_fill - progress_fill", source)
        self.assertIn("video_region_right", source)
        self.assertIn("video_region_w = fb->width - video_region_x", source)
        self.assertNotIn("a90_draw_rect(fb, 0, 0, fb->width, fb->height, 0x05070C);", source)

    def test_manifest_marks_badapple_nyan_validation_focus(self) -> None:
        text = Path(
            "workspace/public/src/scripts/revalidation/build_native_init_boot_v3158_badapple_nyan_fastscale.py"
        ).read_text(encoding="utf-8")

        self.assertIn('"requires_live_validation": ["badapple", "nyan"]', text)
        self.assertIn('"live_validation_focus": ["badapple", "nyan"]', text)
        self.assertIn('"bundled_demos": ["badapple", "nyan", "doom"]', text)
        self.assertIn('"source_baseline": "v3157-video-epic-promotion"', text)
        self.assertIn('"adoption_state": "pending-badapple-nyan-fastscale-live-validation"', text)

    def test_adapter_source_rewrites_to_v3158(self) -> None:
        source = runner.v3158_adapter_source()

        self.assertIn("a90.doomgeneric.v3158.audio=real-sfx-pcm-stream-badapple-nyan-fastscale", source)
        self.assertIn("a90.doomgeneric.v3158.demo_hud=large-grouped-hw-doom-input", source)
        self.assertNotIn("v3157", source)
        self.assertNotIn("v3154", source)


if __name__ == "__main__":
    unittest.main()
