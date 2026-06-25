from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


ROOT = Path(__file__).resolve().parents[1]
STATUS_HUD = ROOT / "workspace/public/src/native-init/v319/30_status_hud.inc.c"

runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3165_badapple_nyan_smooth_av.py"
)


class NativeVideoBadappleNyanSmoothAvSourceV3165Tests(unittest.TestCase):
    def test_v3165_identity_and_markers(self) -> None:
        self.assertEqual(runner.CYCLE, "V3165")
        self.assertEqual(runner.INIT_VERSION, "0.11.8")
        self.assertEqual(runner.INIT_BUILD, "v3165-badapple-nyan-smooth-av")
        self.assertEqual(runner.VIDEO_PLAYER_HUD_METRICS_INTERVAL_FRAMES, 120)
        self.assertEqual(runner.VIDEO_PLAYER_HUD_STORAGE_INTERVAL_FRAMES, 900)
        self.assertEqual(runner.VIDEO_PLAYER_HUD_TEXT_INTERVAL_FRAMES, 120)
        self.assertEqual(runner.VIDEO_PLAYER_HUD_TELEMETRY_MIN_SLACK_NS, 12000000)

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"0.11.8", required)
        self.assertIn(b"v3165-badapple-nyan-smooth-av", required)
        self.assertIn(b"video.status.player_hud_text_slack_guard=%d", required)
        self.assertIn(b"video.status.stream_audio_tail_guard=1", required)
        self.assertIn(b"video.stream.audio_sync.tail_guard=1", required)
        self.assertNotIn(b"v3164-badapple-nyan-playback-guard", required)

    def test_player_hud_work_is_lower_cadence_and_slack_guarded(self) -> None:
        source = STATUS_HUD.read_text(encoding="utf-8")
        render_start = source.index("static int video_render_player_hud")
        render_end = source.index("static int video_read_frame_payload", render_start)
        block = source[render_start:render_end]

        self.assertIn("#define VIDEO_PLAYER_HUD_METRICS_INTERVAL_FRAMES 120U", source)
        self.assertIn("#define VIDEO_PLAYER_HUD_STORAGE_INTERVAL_FRAMES 900U", source)
        self.assertIn("#define VIDEO_PLAYER_HUD_TEXT_INTERVAL_FRAMES 120U", source)
        self.assertIn("#define VIDEO_PLAYER_HUD_TELEMETRY_MIN_SLACK_NS 12000000ULL", source)
        self.assertIn("#define VIDEO_PLAYER_HUD_TEXT_SLACK_GUARD 1", source)
        self.assertIn("video.status.player_hud_text_slack_guard=%d", source)
        self.assertIn("(!VIDEO_PLAYER_HUD_TEXT_SLACK_GUARD || telemetry_has_slack)", block)
        self.assertIn("frame_index - text_frame >= VIDEO_PLAYER_HUD_TEXT_INTERVAL_FRAMES", block)

    def test_video_stream_polls_physical_exit_once_per_frame(self) -> None:
        source = STATUS_HUD.read_text(encoding="utf-8")
        play_start = source.index("static int video_stream_play")
        play_end = source.index("static const char *video_cache_preset_sha256", play_start)
        block = source[play_start:play_end]
        loop_start = block.index("for (frame_index = 0; frame_index < limit_frames; ++frame_index)")
        first_record_read = block.index("if (manifest->stream_version == VIDEO_STREAM_VERSION_A90VSTR2)", loop_start)

        self.assertNotIn("video_stream_physical_exit_poll(&physical_exit)", block[loop_start:first_record_read])
        self.assertEqual(block.count("video_stream_physical_exit_poll(&physical_exit)"), 1)

    def test_video_stream_waits_through_final_audio_synced_frame_interval(self) -> None:
        source = STATUS_HUD.read_text(encoding="utf-8")
        play_start = source.index("static int video_stream_play")
        play_end = source.index("static const char *video_cache_preset_sha256", play_start)
        block = source[play_start:play_end]

        self.assertIn("audio_tail_wait_attempted", block)
        self.assertIn("stream_end_ns = started_ns + ((uint64_t)limit_frames * interval_ns)", block)
        self.assertIn("!physical_exit.requested", block)
        self.assertIn("video.stream.audio_sync.tail_guard=1", block)
        self.assertIn("video.stream.audio_sync.tail_wait_attempted=%d", block)
        self.assertIn("video.stream.audio_sync.tail_wait_ns=%llu", block)

    def test_adapter_source_rewrites_to_v3165(self) -> None:
        source = runner.v3165_adapter_source()

        self.assertIn("a90.doomgeneric.v3165.audio=real-sfx-pcm-stream-badapple-nyan-smooth-av", source)
        self.assertIn("a90.doomgeneric.v3165.demo_hud=large-grouped-hw-doom-input", source)
        self.assertNotIn("v3164", source)
        self.assertNotIn("playback-guard", source)


if __name__ == "__main__":
    unittest.main()
