from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


ROOT = Path(__file__).resolve().parents[1]
STATUS_HUD = ROOT / "workspace/public/src/native-init/v319/30_status_hud.inc.c"

runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3156_video_player_hud_cadence.py"
)


class NativeVideoPlayerHudCadenceSourceV3156Tests(unittest.TestCase):
    def test_v3156_identity_and_contract(self) -> None:
        self.assertEqual(runner.CYCLE, "V3156")
        self.assertEqual(runner.INIT_VERSION, "0.10.138")
        self.assertEqual(runner.INIT_BUILD, "v3156-video-player-hud-cadence")
        self.assertEqual(runner.VIDEO_PLAYER_HUD_TEXT_INTERVAL_FRAMES, 15)
        self.assertEqual(runner.VIDEO_PLAYER_HUD_FULL_REPAINT_INTERVAL_FRAMES, 300)

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"v3156-video-player-hud-cadence", required)
        self.assertIn(b"video.status.player_hud_text_interval_frames=%u", required)
        self.assertIn(b"video.status.player_hud_full_repaint_interval_frames=%u", required)
        self.assertIn(b"video.status.stream_timing_probe=1", required)
        self.assertIn(b"video.stream.timing.render.avg_us", required)
        self.assertIn(b"video.stream.timing.present.max_us", required)
        self.assertNotIn(b"v3155-doomgeneric-sfx-best-effort-video-cadence", required)

    def test_player_hud_redraw_cadence_is_throttled(self) -> None:
        source = STATUS_HUD.read_text(encoding="utf-8")

        self.assertIn("#define VIDEO_PLAYER_HUD_TEXT_INTERVAL_FRAMES 15U", source)
        self.assertIn("#define VIDEO_PLAYER_HUD_FULL_REPAINT_INTERVAL_FRAMES 300U", source)
        self.assertIn("video.status.player_hud_text_interval_frames=%u", source)
        self.assertIn("video.status.player_hud_full_repaint_interval_frames=%u", source)
        self.assertIn("frame_index % VIDEO_PLAYER_HUD_FULL_REPAINT_INTERVAL_FRAMES", source)
        self.assertIn("frame_index - text_frame >= VIDEO_PLAYER_HUD_TEXT_INTERVAL_FRAMES", source)
        self.assertIn("if (text_repaint) {", source)
        self.assertIn("if (border_repaint) {", source)
        self.assertNotIn("frame_index % 60U", source)

    def test_stream_timing_metrics_are_emitted(self) -> None:
        source = STATUS_HUD.read_text(encoding="utf-8")

        self.assertIn("struct video_stage_timing", source)
        self.assertIn("video_stage_timing_add(&read_timing", source)
        self.assertIn("video_stage_timing_add(&render_timing", source)
        self.assertIn("video_stage_timing_add(&wait_timing", source)
        self.assertIn("video_stage_timing_add(&present_timing", source)
        self.assertIn("video_stage_timing_add(&total_timing", source)
        self.assertIn("video.stream.timing.read.avg_us", source)
        self.assertIn("video.stream.timing.render.avg_us", source)
        self.assertIn("video.stream.timing.wait.max_us", source)
        self.assertIn("video.stream.timing.total.max_us", source)

    def test_adapter_source_rewrites_to_v3156(self) -> None:
        source = runner.v3156_adapter_source()

        self.assertIn(
            "a90.doomgeneric.v3156.audio=real-sfx-pcm-stream-best-effort-video-player-hud-cadence",
            source,
        )
        self.assertIn("a90.doomgeneric.v3156.demo_hud=large-grouped-hw-doom-input", source)
        self.assertNotIn("v3155", source)
        self.assertNotIn("v3154", source)


if __name__ == "__main__":
    unittest.main()
