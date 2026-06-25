from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


ROOT = Path(__file__).resolve().parents[1]
STATUS_HUD = ROOT / "workspace/public/src/native-init/v319/30_status_hud.inc.c"
MENU_APPS = ROOT / "workspace/public/src/native-init/v319/40_menu_apps.inc.c"

runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3167_badapple_nyan_stable_av.py"
)


class NativeVideoBadappleNyanStableAvSourceV3167Tests(unittest.TestCase):
    def test_v3167_identity_and_required_stable_markers(self) -> None:
        self.assertEqual(runner.CYCLE, "V3167")
        self.assertEqual(runner.INIT_VERSION, "0.11.10")
        self.assertEqual(runner.INIT_BUILD, "v3167-badapple-nyan-stable-av")
        self.assertEqual(runner.VIDEO_PLAYER_HUD_METRICS_INTERVAL_FRAMES, 900)
        self.assertEqual(runner.VIDEO_PLAYER_HUD_STORAGE_INTERVAL_FRAMES, 1800)
        self.assertEqual(runner.VIDEO_PLAYER_HUD_TEXT_INTERVAL_FRAMES, 900)
        self.assertEqual(runner.VIDEO_PLAYER_HUD_TELEMETRY_MIN_SLACK_NS, 18000000)

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"0.11.10", required)
        self.assertIn(b"v3167-badapple-nyan-stable-av", required)
        self.assertIn(b"video.status.menu_av_present=setcrtc", required)
        self.assertIn(b"video.status.menu_av_late_drop=disabled-setcrtc-default", required)
        self.assertIn(b"video.status.menu_av_pageflip_diagnostic=1", required)
        self.assertIn(b"menu.demo.badapple.video_present=setcrtc", required)
        self.assertIn(b"menu.demo.nyan.video_present=setcrtc", required)
        self.assertNotIn(b"v3166-badapple-nyan-pageflip-av", required)

    def test_badapple_and_nyan_menu_use_stable_setcrtc_default(self) -> None:
        source = MENU_APPS.read_text(encoding="utf-8")
        badapple_start = source.index("case SCREEN_MENU_DEMO_BADAPPLE")
        nyan_start = source.index("case SCREEN_MENU_DEMO_NYAN")
        doom_start = source.index("case SCREEN_MENU_DEMO_DOOM")
        badapple = source[badapple_start:nyan_start]
        nyan = source[nyan_start:doom_start]

        for block in (badapple, nyan):
            self.assertIn('"--present", "setcrtc"', block)
            self.assertNotIn('"--present", "pageflip"', block)
            self.assertIn("video_present=setcrtc", block)
            self.assertIn("video_late_drop=disabled-setcrtc-default", block)
            self.assertIn("video_pageflip_diagnostic=1", block)

    def test_badapple_and_nyan_presets_default_to_stable_setcrtc(self) -> None:
        source = STATUS_HUD.read_text(encoding="utf-8")
        helper_start = source.index("static enum video_stream_present_mode video_cache_preset_default_present")
        helper_end = source.index("static int cmd_video_cache", helper_start)
        helper = source[helper_start:helper_end]

        self.assertIn("VIDEO_CACHE_PRESET_BADAPPLE_NAME", helper)
        self.assertIn("VIDEO_CACHE_PRESET_NYAN_NAME", helper)
        self.assertIn("VIDEO_STREAM_PRESENT_SETCRTC", helper)
        self.assertNotIn("return VIDEO_STREAM_PRESENT_PAGEFLIP;", helper)

    def test_player_hud_telemetry_is_sparse(self) -> None:
        source = STATUS_HUD.read_text(encoding="utf-8")

        self.assertIn("#define VIDEO_PLAYER_HUD_METRICS_INTERVAL_FRAMES 900U", source)
        self.assertIn("#define VIDEO_PLAYER_HUD_STORAGE_INTERVAL_FRAMES 1800U", source)
        self.assertIn("#define VIDEO_PLAYER_HUD_TEXT_INTERVAL_FRAMES 900U", source)
        self.assertIn("#define VIDEO_PLAYER_HUD_TELEMETRY_MIN_SLACK_NS 18000000ULL", source)
        self.assertIn("video.status.menu_av_present=setcrtc", source)
        self.assertIn("video.status.menu_av_pageflip_diagnostic=1", source)

    def test_manifest_metadata_records_stable_policy(self) -> None:
        source = Path(runner.__file__).read_text(encoding="utf-8")

        self.assertIn('"menu_present_mode": "setcrtc"', source)
        self.assertIn('"preset_default_present_mode": "setcrtc"', source)
        self.assertIn('"pageflip_diagnostic_available": True', source)
        self.assertIn("player-hud-setcrtc-stable-cadence", source)
        self.assertIn("sparse-player-hud-telemetry", source)


if __name__ == "__main__":
    unittest.main()
