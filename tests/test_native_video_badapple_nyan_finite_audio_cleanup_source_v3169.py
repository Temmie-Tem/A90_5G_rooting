from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


ROOT = Path(__file__).resolve().parents[1]
A90_AUDIO = ROOT / "workspace/public/src/native-init/a90_audio.c"
MENU_APPS = ROOT / "workspace/public/src/native-init/v319/40_menu_apps.inc.c"

runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3169_badapple_nyan_finite_audio_cleanup.py"
)


class NativeVideoBadappleNyanFiniteAudioCleanupSourceV3169Tests(unittest.TestCase):
    def test_v3169_identity_and_required_finite_cleanup_markers(self) -> None:
        self.assertEqual(runner.CYCLE, "V3169")
        self.assertEqual(runner.INIT_VERSION, "0.11.12")
        self.assertEqual(runner.INIT_BUILD, "v3169-badapple-nyan-finite-audio-cleanup")
        self.assertEqual(runner.VIDEO_PLAYER_HUD_LIVE_TELEMETRY, 0)
        self.assertEqual(runner.VIDEO_PLAYER_HUD_DYNAMIC_TEXT, 0)

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"0.11.12", required)
        self.assertIn(b"v3169-badapple-nyan-finite-audio-cleanup", required)
        self.assertIn(b"audio.play.execute.close.deferred=0 reason=finite-pcm-worker-owned", required)
        self.assertIn(b"audio.play.worker.close_deferred=0", required)
        self.assertIn(b"audio.play.integrated.cleanup.deferred=0 reason=finite-pcm-worker-owned", required)
        self.assertIn(b"audio.play.worker.cleanup_owner=worker", required)
        self.assertIn(b"menu.demo.badapple.audio_cleanup=worker-owned-finite-pcm", required)
        self.assertIn(b"menu.demo.nyan.audio_cleanup=worker-owned-finite-pcm", required)
        self.assertNotIn(b"menu.demo.badapple.audio_post_stop_required=1", required)
        self.assertNotIn(b"menu.demo.nyan.audio_post_stop_required=1", required)

    def test_finite_pcm_closes_pcm_fd_while_stream_cleanup_stays_deferred(self) -> None:
        source = A90_AUDIO.read_text(encoding="utf-8")
        start = source.index("static int audio_play_execute_pcm(")
        end = source.index("static void audio_play_print_execute_plan", start)
        block = source[start:end]

        close_deferred = block.index(
            "audio.play.execute.close.deferred=1 reason=route-reset-before-pcm-close"
        )
        stream_branch = block.rindex("if (use_pcm_stream) {", 0, close_deferred)
        finite_branch = block.index("} else {", close_deferred)
        self.assertIn("audio.play.execute.close.deferred=1 reason=route-reset-before-pcm-close",
                      block[stream_branch:finite_branch])
        self.assertIn("audio.play.worker.close_deferred=1", block[stream_branch:finite_branch])
        self.assertIn("pcm_fd_close_rc = close(fd);", block[finite_branch:])
        self.assertIn("audio.play.execute.close.deferred=0 reason=finite-pcm-worker-owned",
                      block[finite_branch:])
        self.assertIn("audio.play.worker.close_deferred=0", block[finite_branch:])

    def test_integrated_cleanup_is_deferred_only_for_pcm_streams(self) -> None:
        source = A90_AUDIO.read_text(encoding="utf-8")
        start = source.index("static int audio_play_execute_integrated(")
        end = source.index("static int audio_play_cmd(", start)
        block = source[start:end]

        self.assertIn("const bool stop_owned_cleanup = pcm_stream_path != NULL && pcm_stream_path[0] != '\\0';",
                      block)
        stream_branch = block.index("if (stop_owned_cleanup) {")
        finite_branch = block.index("} else {", stream_branch)
        self.assertIn("audio.play.integrated.cleanup.deferred=1 reason=pcm-complete-await-audio-stop",
                      block[stream_branch:finite_branch])
        self.assertIn("audio.play.worker.cleanup_owner=audio-stop", block[stream_branch:finite_branch])
        self.assertIn("pause();", block[stream_branch:finite_branch])
        self.assertIn("audio.play.integrated.cleanup.deferred=0 reason=finite-pcm-worker-owned",
                      block[finite_branch:])
        self.assertIn("audio.play.worker.cleanup_owner=worker", block[finite_branch:])
        self.assertIn("audio.play.worker.exit_deferred=0", block[finite_branch:])

    def test_badapple_and_nyan_menu_no_longer_force_post_video_audio_stop(self) -> None:
        source = MENU_APPS.read_text(encoding="utf-8")
        badapple_start = source.index("case SCREEN_MENU_DEMO_BADAPPLE")
        nyan_start = source.index("case SCREEN_MENU_DEMO_NYAN")
        doom_start = source.index("case SCREEN_MENU_DEMO_DOOM")
        badapple = source[badapple_start:nyan_start]
        nyan = source[nyan_start:doom_start]

        for block, demo_name in ((badapple, "badapple"), (nyan, "nyan")):
            self.assertIn(f'menu.demo.{demo_name}.audio_cleanup=worker-owned-finite-pcm', block)
            self.assertIn("audio_pre_stop_best_effort=1", block)
            self.assertNotIn("audio_post_stop_required=1", block)
            self.assertNotIn('auto_hud_stop_demo_audio("badapple", "post")', block)
            self.assertNotIn('auto_hud_stop_demo_audio("nyan", "post")', block)
            self.assertIn('"--present", "setcrtc"', block)

    def test_manifest_metadata_records_cleanup_owner_split(self) -> None:
        source = Path(runner.__file__).read_text(encoding="utf-8")

        self.assertIn('"finite_pcm_cleanup_owner": "worker"', source)
        self.assertIn('"stream_pcm_cleanup_owner": "audio-stop"', source)
        self.assertIn('"badapple_nyan_post_stop_required": False', source)
        self.assertIn("badapple-fullsong-av", source)
        self.assertIn("nyan-preview-av", source)


if __name__ == "__main__":
    unittest.main()
