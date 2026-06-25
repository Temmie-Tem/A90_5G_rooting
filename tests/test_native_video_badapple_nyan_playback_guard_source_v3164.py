from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


ROOT = Path(__file__).resolve().parents[1]
STATUS_HUD = ROOT / "workspace/public/src/native-init/v319/30_status_hud.inc.c"
MENU_SOURCE = ROOT / "workspace/public/src/native-init/v319/40_menu_apps.inc.c"

runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3164_badapple_nyan_playback_guard.py"
)


class NativeVideoBadappleNyanPlaybackGuardSourceV3164Tests(unittest.TestCase):
    def test_v3164_identity_and_markers(self) -> None:
        self.assertEqual(runner.CYCLE, "V3164")
        self.assertEqual(runner.INIT_VERSION, "0.11.7")
        self.assertEqual(runner.INIT_BUILD, "v3164-badapple-nyan-playback-guard")
        self.assertEqual(runner.VIDEO_PLAYER_HUD_TELEMETRY_MIN_SLACK_NS, 8000000)

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"0.11.7", required)
        self.assertIn(b"v3164-badapple-nyan-playback-guard", required)
        self.assertIn(b"video.status.player_hud_deadline_guard_ns=%llu", required)
        self.assertIn(b"video.status.stream_physical_button_exit=%d", required)
        self.assertIn(b"video.stream.physical_button_exit=%d", required)
        self.assertIn(b"video.stream.physical_exit.requested=%d", required)
        self.assertIn(b"videostream-physical-exit", required)
        self.assertIn(b"menu.demo.badapple.video_physical_exit=1", required)
        self.assertIn(b"menu.demo.nyan.video_deadline_guard=1", required)
        self.assertNotIn(b"v3163-badapple-nyan-cleanup-cadence", required)

    def test_video_stream_physical_exit_is_generic_not_doom_only(self) -> None:
        source = STATUS_HUD.read_text(encoding="utf-8")
        start = source.index("struct video_stream_physical_exit")
        end = source.index("static int video_stream_play", start)
        block = source[start:end]

        self.assertIn("A90_VIDEO_STREAM_PHYSICAL_BUTTON_EXIT", source)
        self.assertIn("video.status.stream_physical_button_exit=%d", source)
        self.assertIn("videostream-physical-exit", block)
        self.assertIn("a90_input_open(&state->input, \"videostream-physical-exit\")", block)
        self.assertIn("KEY_POWER", block)
        self.assertIn("KEY_VOLUMEUP", block)
        self.assertIn("KEY_VOLUMEDOWN", block)

        play_block = source[source.index("static int video_stream_play"):]
        self.assertIn("struct video_stream_physical_exit physical_exit", play_block)
        self.assertIn("video_stream_physical_exit_open(&physical_exit)", play_block)
        self.assertIn("video_stream_physical_exit_poll(&physical_exit)", play_block)
        self.assertIn("video_stream_physical_exit_close(&physical_exit)", play_block)
        self.assertIn("video.stream.physical_exit.last_poll_rc=%d", play_block)

    def test_player_hud_deadline_guard_defers_telemetry_reads(self) -> None:
        source = STATUS_HUD.read_text(encoding="utf-8")
        start = source.index("static int video_render_player_hud")
        end = source.index("static int video_read_frame_payload", start)
        block = source[start:end]

        self.assertIn("#define VIDEO_PLAYER_HUD_TELEMETRY_MIN_SLACK_NS 8000000ULL", source)
        self.assertIn("video_deadline_has_slack", source)
        self.assertIn("telemetry_has_slack", block)
        self.assertIn("a90_metrics_read_snapshot(&metrics)", block)
        self.assertIn("current_hud_storage_status()", block)
        self.assertIn("&&\n        telemetry_has_slack", block)
        self.assertIn("video.status.player_hud_deadline_guard_ns=%llu", source)

    def test_menu_marks_badapple_nyan_guard_without_changing_setcrtc_default(self) -> None:
        source = MENU_SOURCE.read_text(encoding="utf-8")

        self.assertIn("menu.demo.badapple.video_present=setcrtc", source)
        self.assertIn("menu.demo.nyan.video_present=setcrtc", source)
        self.assertIn("menu.demo.badapple.video_physical_exit=1", source)
        self.assertIn("menu.demo.badapple.video_deadline_guard=1", source)
        self.assertIn("menu.demo.nyan.video_physical_exit=1", source)
        self.assertIn("menu.demo.nyan.video_deadline_guard=1", source)
        self.assertNotIn('"--present", "pageflip"', source)

    def test_manifest_marks_playback_guard_validation_focus(self) -> None:
        text = Path(
            "workspace/public/src/scripts/revalidation/build_native_init_boot_v3164_badapple_nyan_playback_guard.py"
        ).read_text(encoding="utf-8")

        self.assertIn('"source_baseline": "v3163-badapple-nyan-cleanup-cadence"', text)
        self.assertIn('"physical-button-exit"', text)
        self.assertIn('"player-hud-deadline-guard"', text)
        self.assertIn('"stream_physical_button_exit": True', text)
        self.assertIn('"menu_present_mode": "setcrtc"', text)
        self.assertIn('"telemetry_deadline_guard_ns": VIDEO_PLAYER_HUD_TELEMETRY_MIN_SLACK_NS', text)

    def test_adapter_source_rewrites_to_v3164(self) -> None:
        source = runner.v3164_adapter_source()

        self.assertIn(
            "a90.doomgeneric.v3164.audio=real-sfx-pcm-stream-badapple-nyan-playback-guard",
            source,
        )
        self.assertIn("a90.doomgeneric.v3164.demo_hud=large-grouped-hw-doom-input", source)
        self.assertNotIn("v3163", source)
        self.assertNotIn("cleanup-cadence", source)


if __name__ == "__main__":
    unittest.main()
