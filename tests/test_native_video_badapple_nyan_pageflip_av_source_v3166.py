from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


ROOT = Path(__file__).resolve().parents[1]
STATUS_HUD = ROOT / "workspace/public/src/native-init/v319/30_status_hud.inc.c"
MENU_APPS = ROOT / "workspace/public/src/native-init/v319/40_menu_apps.inc.c"

runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3166_badapple_nyan_pageflip_av.py"
)


class NativeVideoBadappleNyanPageflipAvSourceV3166Tests(unittest.TestCase):
    def test_v3166_identity_and_required_pageflip_markers(self) -> None:
        self.assertEqual(runner.CYCLE, "V3166")
        self.assertEqual(runner.INIT_VERSION, "0.11.9")
        self.assertEqual(runner.INIT_BUILD, "v3166-badapple-nyan-pageflip-av")

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"0.11.9", required)
        self.assertIn(b"v3166-badapple-nyan-pageflip-av", required)
        self.assertIn(b"video.status.menu_av_present=pageflip", required)
        self.assertIn(b"video.status.menu_av_late_drop=audio-synced-pageflip", required)
        self.assertIn(b"menu.demo.badapple.video_present=pageflip", required)
        self.assertIn(b"menu.demo.nyan.video_present=pageflip", required)
        self.assertNotIn(b"v3165-badapple-nyan-smooth-av", required)

    def test_badapple_and_nyan_menu_use_pageflip(self) -> None:
        source = MENU_APPS.read_text(encoding="utf-8")
        badapple_start = source.index("case SCREEN_MENU_DEMO_BADAPPLE")
        nyan_start = source.index("case SCREEN_MENU_DEMO_NYAN")
        doom_start = source.index("case SCREEN_MENU_DEMO_DOOM")
        badapple = source[badapple_start:nyan_start]
        nyan = source[nyan_start:doom_start]

        for block in (badapple, nyan):
            self.assertIn('"--present", "pageflip"', block)
            self.assertNotIn('"--present", "setcrtc"', block)
            self.assertIn("video_present=pageflip", block)
            self.assertIn("video_late_drop=audio-synced-pageflip", block)

    def test_badapple_and_nyan_presets_default_to_pageflip(self) -> None:
        source = STATUS_HUD.read_text(encoding="utf-8")
        helper_start = source.index("static enum video_stream_present_mode video_cache_preset_default_present")
        helper_end = source.index("static int cmd_video_cache", helper_start)
        helper = source[helper_start:helper_end]
        cache_start = source.index("static int cmd_video_cache")
        cache_end = source.index("static int handle_video", cache_start)
        cache = source[cache_start:cache_end]

        self.assertIn("VIDEO_CACHE_PRESET_BADAPPLE_NAME", helper)
        self.assertIn("VIDEO_CACHE_PRESET_NYAN_NAME", helper)
        self.assertIn("VIDEO_STREAM_PRESENT_PAGEFLIP", helper)
        self.assertIn("VIDEO_STREAM_PRESENT_SETCRTC", helper)
        self.assertIn("present_mode = video_cache_preset_default_present(preset_name);", cache)

    def test_video_status_exposes_pageflip_av_policy(self) -> None:
        source = STATUS_HUD.read_text(encoding="utf-8")

        self.assertIn("video.status.menu_av_present=pageflip", source)
        self.assertIn("video.status.menu_av_late_drop=audio-synced-pageflip", source)
        self.assertIn("drop_late_frames = audio_sync->ready && present_mode == VIDEO_STREAM_PRESENT_PAGEFLIP;", source)

    def test_manifest_metadata_records_pageflip_policy(self) -> None:
        source = Path(runner.__file__).read_text(encoding="utf-8")

        self.assertIn('"menu_present_mode": "pageflip"', source)
        self.assertIn('"preset_default_present_mode": "pageflip"', source)
        self.assertIn("player-hud-pageflip-cadence", source)
        self.assertIn("audio-synced-late-frame-drop", source)


if __name__ == "__main__":
    unittest.main()
