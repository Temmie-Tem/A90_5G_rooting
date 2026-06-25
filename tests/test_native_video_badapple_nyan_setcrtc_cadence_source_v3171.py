from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


ROOT = Path(__file__).resolve().parents[1]
STATUS_HUD = ROOT / "workspace/public/src/native-init/v319/30_status_hud.inc.c"
MENU_APPS = ROOT / "workspace/public/src/native-init/v319/40_menu_apps.inc.c"

runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3171_badapple_nyan_setcrtc_cadence.py"
)


class NativeVideoBadappleNyanSetcrtcCadenceSourceV3171Tests(unittest.TestCase):
    def test_v3171_identity_and_required_markers(self) -> None:
        self.assertEqual(runner.CYCLE, "V3171")
        self.assertEqual(runner.INIT_VERSION, "0.11.14")
        self.assertEqual(runner.INIT_BUILD, "v3171-badapple-nyan-setcrtc-cadence")

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"0.11.14", required)
        self.assertIn(b"v3171-badapple-nyan-setcrtc-cadence", required)
        self.assertIn(b"video.status.menu_av_late_drop=pageflip-only-setcrtc-cadence", required)
        self.assertIn(b"menu.demo.badapple.video_late_drop=setcrtc-cadence-no-drop", required)
        self.assertIn(b"menu.demo.nyan.video_late_drop=setcrtc-cadence-no-drop", required)
        self.assertNotIn(b"video.status.menu_av_late_drop=audio-clock-setcrtc-pageflip", required)
        self.assertNotIn(b"menu.demo.badapple.video_late_drop=audio-sync-setcrtc-skip", required)
        self.assertNotIn(b"menu.demo.nyan.video_late_drop=audio-sync-setcrtc-skip", required)

    def test_setcrtc_menu_keeps_stable_cadence_without_late_drop(self) -> None:
        source = MENU_APPS.read_text(encoding="utf-8")
        badapple_start = source.index("case SCREEN_MENU_DEMO_BADAPPLE")
        nyan_start = source.index("case SCREEN_MENU_DEMO_NYAN")
        doom_start = source.index("case SCREEN_MENU_DEMO_DOOM")
        badapple = source[badapple_start:nyan_start]
        nyan = source[nyan_start:doom_start]

        self.assertIn('"--present", "setcrtc"', badapple)
        self.assertIn('"--present", "setcrtc"', nyan)
        self.assertIn("menu.demo.badapple.video_late_drop=setcrtc-cadence-no-drop", badapple)
        self.assertIn("menu.demo.nyan.video_late_drop=setcrtc-cadence-no-drop", nyan)
        self.assertNotIn("video_late_drop=audio-sync-setcrtc-skip", badapple + nyan)

    def test_late_drop_is_pageflip_only_in_player_loop(self) -> None:
        source = STATUS_HUD.read_text(encoding="utf-8")
        play_start = source.index("static int video_stream_play(")
        play_end = source.index("static const char *video_cache_preset_sha256", play_start)
        play = source[play_start:play_end]

        self.assertIn("video.status.menu_av_late_drop=pageflip-only-setcrtc-cadence", source)
        self.assertIn(
            "drop_late_frames = audio_sync->ready && present_mode == VIDEO_STREAM_PRESENT_PAGEFLIP;",
            play,
        )
        self.assertIn('drop_late_frames ? "pageflip" : "none"', play)
        self.assertNotIn("drop_late_frames = audio_sync->ready;", play)
        self.assertNotIn('"setcrtc,pageflip"', play)

    def test_manifest_metadata_records_setcrtc_cadence_policy(self) -> None:
        source = Path(runner.__file__).read_text(encoding="utf-8")

        self.assertIn('"setcrtc_drop_policy": "disabled-stable-cadence"', source)
        self.assertIn('"late_drop_present_modes": ["pageflip"]', source)
        self.assertIn('"setcrtc-stable-cadence"', source)
        self.assertIn('"pageflip-late-drop-diagnostic"', source)
        self.assertNotIn('"late_drop_present_modes": ["setcrtc", "pageflip"]', source)


if __name__ == "__main__":
    unittest.main()
