from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


ROOT = Path(__file__).resolve().parents[1]
A90_AUDIO = ROOT / "workspace/public/src/native-init/a90_audio.c"
STATUS_HUD = ROOT / "workspace/public/src/native-init/v319/30_status_hud.inc.c"
MENU_APPS = ROOT / "workspace/public/src/native-init/v319/40_menu_apps.inc.c"

runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3170_badapple_nyan_av_tail_readahead.py"
)


class NativeVideoBadappleNyanAvTailReadaheadSourceV3170Tests(unittest.TestCase):
    def test_v3170_identity_and_required_markers(self) -> None:
        self.assertEqual(runner.CYCLE, "V3170")
        self.assertEqual(runner.INIT_VERSION, "0.11.13")
        self.assertEqual(runner.INIT_BUILD, "v3170-badapple-nyan-av-tail-readahead")

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"0.11.13", required)
        self.assertIn(b"v3170-badapple-nyan-av-tail-readahead", required)
        self.assertIn(b"audio.play.cap.nyan_preview_ms=%d", required)
        self.assertIn(b"nyan-preview-pcm-tail-pad", required)
        self.assertIn(b"menu.demo.nyan.audio_duration_ms=11000", required)
        self.assertIn(b"menu.demo.badapple.audio_duration_ms=232800", required)
        self.assertIn(b"video.stream.readahead.policy=sequential-window", required)
        self.assertIn(b"audio-clock-late-frame-skip", required)
        self.assertIn(b"video.status.menu_av_late_drop=audio-clock-setcrtc-pageflip", required)
        self.assertNotIn(b"video.status.menu_av_late_drop=disabled-setcrtc-default", required)

    def test_audio_cap_allows_nyan_silent_tail_without_widening_default_cap(self) -> None:
        source = A90_AUDIO.read_text(encoding="utf-8")

        self.assertIn('#define AUDIO_NYAN_PREVIEW_PCM_PATH "/cache/a90-runtime/pkg/av/v2973/audio/nyancat.s16le"', source)
        self.assertIn("#define AUDIO_NYAN_PREVIEW_PCM_DURATION_CAP_MS 12000", source)
        self.assertIn('AUDIO_NYAN_PREVIEW_PCM_EXPECTED_SHA256 "4c3774553195c04166a3a83de793253696a5bee60afe83a04219419fc28e43de"', source)
        self.assertIn("static bool audio_pcm_file_is_nyan_preview", source)
        self.assertIn("return AUDIO_NYAN_PREVIEW_PCM_DURATION_CAP_MS;", source)
        self.assertIn('return "nyan-preview-pcm-tail-pad";', source)
        self.assertIn("audio.play.cap.nyan_preview_ms=%d", source)

    def test_menu_uses_tail_padded_finite_pcm_and_audio_sync_late_drop(self) -> None:
        source = MENU_APPS.read_text(encoding="utf-8")
        badapple_start = source.index("case SCREEN_MENU_DEMO_BADAPPLE")
        nyan_start = source.index("case SCREEN_MENU_DEMO_NYAN")
        doom_start = source.index("case SCREEN_MENU_DEMO_DOOM")
        badapple = source[badapple_start:nyan_start]
        nyan = source[nyan_start:doom_start]

        self.assertIn('"--duration-ms", "232800"', badapple)
        self.assertIn("menu.demo.badapple.audio_duration_ms=232800", badapple)
        self.assertIn("menu.demo.badapple.audio_tail_pad_ms=710", badapple)
        self.assertIn("menu.demo.badapple.video_late_drop=audio-sync-setcrtc-skip", badapple)
        self.assertIn('"--duration-ms", "11000"', nyan)
        self.assertIn("menu.demo.nyan.audio_duration_ms=11000", nyan)
        self.assertIn("menu.demo.nyan.audio_tail_pad_ms=1000", nyan)
        self.assertIn("menu.demo.nyan.video_late_drop=audio-sync-setcrtc-skip", nyan)
        self.assertNotIn("video_late_drop=disabled-setcrtc-default", badapple + nyan)

    def test_video_stream_readahead_and_all_present_late_drop_are_wired(self) -> None:
        source = STATUS_HUD.read_text(encoding="utf-8")
        play_start = source.index("static int video_stream_play(")
        play_end = source.index("static const char *video_cache_preset_sha256", play_start)
        play = source[play_start:play_end]

        self.assertIn("#define VIDEO_STREAM_READAHEAD_BYTES", source)
        self.assertIn("static int video_stream_readahead_window", source)
        self.assertIn("static int video_stream_sequential_hint", source)
        self.assertIn("video.status.stream_readahead=sequential-window", source)
        self.assertIn("video.status.menu_av_late_drop=audio-clock-setcrtc-pageflip", source)
        self.assertIn("readahead_sequential_rc = video_stream_sequential_hint(fd);", play)
        self.assertIn("video.stream.readahead.policy=sequential-window", play)
        self.assertIn("drop_late_frames = audio_sync->ready;", play)
        self.assertIn("video.stream.audio_sync.drop_present_modes=%s", play)
        self.assertNotIn("drop_late_frames = audio_sync->ready && present_mode == VIDEO_STREAM_PRESENT_PAGEFLIP", play)

    def test_manifest_metadata_records_tail_and_readahead_policy(self) -> None:
        source = Path(runner.__file__).read_text(encoding="utf-8")

        self.assertIn('"badapple_audio_duration_ms": 232800', source)
        self.assertIn('"nyan_audio_duration_ms": 11000', source)
        self.assertIn('"late_drop_present_modes": ["setcrtc", "pageflip"]', source)
        self.assertIn('"stream_readahead": "sequential-window"', source)
        self.assertIn('"stream_readahead_bytes": 8 * 1024 * 1024', source)


if __name__ == "__main__":
    unittest.main()
