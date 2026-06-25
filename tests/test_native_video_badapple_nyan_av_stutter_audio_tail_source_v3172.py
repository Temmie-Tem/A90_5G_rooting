from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


ROOT = Path(__file__).resolve().parents[1]
STATUS_HUD = ROOT / "workspace/public/src/native-init/v319/30_status_hud.inc.c"
MENU_APPS = ROOT / "workspace/public/src/native-init/v319/40_menu_apps.inc.c"

runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3172_badapple_nyan_av_stutter_audio_tail.py"
)


class NativeVideoBadappleNyanAvStutterAudioTailSourceV3172Tests(unittest.TestCase):
    def test_v3172_identity_and_required_markers(self) -> None:
        self.assertEqual(runner.CYCLE, "V3172")
        self.assertEqual(runner.INIT_VERSION, "0.11.15")
        self.assertEqual(runner.INIT_BUILD, "v3172-badapple-nyan-av-stutter-audio-tail")

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"0.11.15", required)
        self.assertIn(b"v3172-badapple-nyan-av-stutter-audio-tail", required)
        self.assertIn(b"video.status.stream_readahead=%s", required)
        self.assertIn(b"sequential-only-window-off", required)
        self.assertIn(b"video.status.stream_readahead.window_enabled=%d", required)
        self.assertIn(b"video.status.menu_av_tail_wait=audio-expected-duration", required)
        self.assertIn(b"video.stream.readahead.deadline_skips=%u", required)
        self.assertIn(b"video.stream.audio_sync.tail_wait_target=%s", required)
        self.assertIn(b"menu.demo.badapple.audio_tail_wait=expected-duration", required)
        self.assertIn(b"menu.demo.nyan.audio_tail_wait=expected-duration", required)
        self.assertNotIn(b"video.status.stream_readahead=sequential-window", required)
        self.assertNotIn(b"video.stream.readahead.policy=sequential-window", required)

    def test_periodic_window_readahead_is_disabled_and_guarded_if_reenabled(self) -> None:
        source = STATUS_HUD.read_text(encoding="utf-8")
        play_start = source.index("static int video_stream_play(")
        play_end = source.index("static const char *video_cache_preset_sha256", play_start)
        play = source[play_start:play_end]

        self.assertIn("#define VIDEO_STREAM_READAHEAD_WINDOW_ENABLED 0", source)
        self.assertIn("#define VIDEO_STREAM_READAHEAD_DEADLINE_GUARD_NS 25000000ULL", source)
        self.assertIn("video.status.stream_readahead=%s", source)
        self.assertIn('"sequential-only-window-off"', source)
        self.assertIn("video.stream.readahead.window_enabled=%d", play)
        self.assertIn("video.stream.readahead.deadline_guard_ns=%llu", play)
        self.assertIn("#if VIDEO_STREAM_READAHEAD_WINDOW_ENABLED", play)
        self.assertIn("deadline_ns - now_ns >= VIDEO_STREAM_READAHEAD_DEADLINE_GUARD_NS", play)
        self.assertIn("++readahead_deadline_skips;", play)
        self.assertIn("video.stream.readahead.deadline_skips=%u", play)

    def test_full_demo_tail_wait_targets_audio_expected_duration(self) -> None:
        source = STATUS_HUD.read_text(encoding="utf-8")
        play_start = source.index("static int video_stream_play(")
        play_end = source.index("static const char *video_cache_preset_sha256", play_start)
        play = source[play_start:play_end]

        self.assertIn('const char *audio_tail_wait_target = "none";', play)
        self.assertIn('audio_tail_wait_target = "video";', play)
        self.assertIn("limit_frames == manifest->frame_count", play)
        self.assertIn("audio_sync->listen_begin_ns + audio_sync->expected_duration_ns", play)
        self.assertIn('audio_tail_wait_target = "audio";', play)
        self.assertIn("video.stream.audio_sync.tail_wait_target=%s", play)

    def test_badapple_and_nyan_menu_advertise_expected_duration_tail_wait(self) -> None:
        source = MENU_APPS.read_text(encoding="utf-8")
        badapple_start = source.index("case SCREEN_MENU_DEMO_BADAPPLE")
        nyan_start = source.index("case SCREEN_MENU_DEMO_NYAN")
        doom_start = source.index("case SCREEN_MENU_DEMO_DOOM")
        badapple = source[badapple_start:nyan_start]
        nyan = source[nyan_start:doom_start]

        self.assertIn("menu.demo.badapple.audio_tail_wait=expected-duration", badapple)
        self.assertIn("menu.demo.nyan.audio_tail_wait=expected-duration", nyan)
        self.assertIn('"--present", "setcrtc"', badapple)
        self.assertIn('"--present", "setcrtc"', nyan)
        self.assertIn("menu.demo.badapple.video_late_drop=setcrtc-cadence-no-drop", badapple)
        self.assertIn("menu.demo.nyan.video_late_drop=setcrtc-cadence-no-drop", nyan)

    def test_manifest_metadata_records_new_readahead_and_tail_policy(self) -> None:
        source = Path(runner.__file__).read_text(encoding="utf-8")

        self.assertIn('"source_baseline": "v3171-badapple-nyan-setcrtc-cadence"', source)
        self.assertIn('"stream_readahead": "sequential-only-window-off"', source)
        self.assertIn('"window_readahead_default_enabled": False', source)
        self.assertIn('"window_readahead_deadline_guard_ns": 25000000', source)
        self.assertIn('"audio_tail_wait": "expected-duration-for-full-demo"', source)
        self.assertIn("periodic-stutter-check", source)
        self.assertIn("audio-tail-clean-menu-return", source)


if __name__ == "__main__":
    unittest.main()
