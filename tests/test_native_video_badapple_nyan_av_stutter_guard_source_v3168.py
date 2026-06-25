from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


ROOT = Path(__file__).resolve().parents[1]
STATUS_HUD = ROOT / "workspace/public/src/native-init/v319/30_status_hud.inc.c"
MENU_APPS = ROOT / "workspace/public/src/native-init/v319/40_menu_apps.inc.c"

runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3168_badapple_nyan_av_stutter_guard.py"
)


class NativeVideoBadappleNyanAvStutterGuardSourceV3168Tests(unittest.TestCase):
    def test_v3168_identity_and_required_stutter_guard_markers(self) -> None:
        self.assertEqual(runner.CYCLE, "V3168")
        self.assertEqual(runner.INIT_VERSION, "0.11.11")
        self.assertEqual(runner.INIT_BUILD, "v3168-badapple-nyan-av-stutter-guard")
        self.assertEqual(runner.VIDEO_PLAYER_HUD_LIVE_TELEMETRY, 0)
        self.assertEqual(runner.VIDEO_PLAYER_HUD_DYNAMIC_TEXT, 0)
        self.assertEqual(runner.VIDEO_PLAYER_HUD_METRICS_INTERVAL_FRAMES, 900)
        self.assertEqual(runner.VIDEO_PLAYER_HUD_STORAGE_INTERVAL_FRAMES, 1800)
        self.assertEqual(runner.VIDEO_PLAYER_HUD_TEXT_INTERVAL_FRAMES, 900)
        self.assertEqual(runner.VIDEO_PLAYER_HUD_TELEMETRY_MIN_SLACK_NS, 18000000)

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"0.11.11", required)
        self.assertIn(b"v3168-badapple-nyan-av-stutter-guard", required)
        self.assertIn(b"video.status.player_hud_live_telemetry=%d", required)
        self.assertIn(b"video.status.player_hud_dynamic_text=%d", required)
        self.assertIn(b"LIVE TELEMETRY OFF DURING PLAYBACK", required)
        self.assertIn(b"video.status.menu_av_present=setcrtc", required)
        self.assertIn(b"menu.demo.badapple.video_present=setcrtc", required)
        self.assertIn(b"menu.demo.nyan.video_present=setcrtc", required)
        self.assertNotIn(b"v3167-badapple-nyan-stable-av", required)

    def test_badapple_and_nyan_menu_keep_stable_setcrtc_default(self) -> None:
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

    def test_player_hud_live_telemetry_is_compile_time_disabled_by_default(self) -> None:
        source = STATUS_HUD.read_text(encoding="utf-8")

        self.assertIn("#define VIDEO_PLAYER_HUD_LIVE_TELEMETRY 0", source)
        self.assertIn("#define VIDEO_PLAYER_HUD_DYNAMIC_TEXT VIDEO_PLAYER_HUD_LIVE_TELEMETRY", source)
        self.assertIn("video.status.player_hud_live_telemetry=%d", source)
        self.assertIn("video.status.player_hud_dynamic_text=%d", source)
        self.assertIn("LIVE TELEMETRY OFF DURING PLAYBACK", source)

    def test_player_hud_frame_loop_guards_metrics_storage_and_dynamic_text(self) -> None:
        source = STATUS_HUD.read_text(encoding="utf-8")
        start = source.index("static int video_render_player_hud(")
        end = source.index("static int video_read_frame_payload", start)
        render = source[start:end]

        self.assertIn("#if !VIDEO_PLAYER_HUD_LIVE_TELEMETRY", render)
        self.assertIn("video_player_hud_set_static_telemetry(&metrics, &storage);", render)
        self.assertIn("#if VIDEO_PLAYER_HUD_LIVE_TELEMETRY", render)
        self.assertIn("a90_metrics_read_snapshot(&metrics);", render)
        self.assertIn("storage = current_hud_storage_status();", render)
        self.assertIn("#if VIDEO_PLAYER_HUD_DYNAMIC_TEXT", render)
        self.assertIn("text_repaint = full_repaint;", render)
        self.assertIn("full_repaint = render_session_frames < 2U;", render)
        self.assertNotIn("(frame_index % 60U) == 0U", render)

    def test_manifest_metadata_records_static_telemetry_policy(self) -> None:
        source = Path(runner.__file__).read_text(encoding="utf-8")

        self.assertIn('"menu_present_mode": "setcrtc"', source)
        self.assertIn('"preset_default_present_mode": "setcrtc"', source)
        self.assertIn('"live_telemetry": bool(VIDEO_PLAYER_HUD_LIVE_TELEMETRY)', source)
        self.assertIn('"dynamic_text": bool(VIDEO_PLAYER_HUD_DYNAMIC_TEXT)', source)
        self.assertIn("player-hud-static-telemetry", source)
        self.assertIn("player-hud-static-text", source)


if __name__ == "__main__":
    unittest.main()
