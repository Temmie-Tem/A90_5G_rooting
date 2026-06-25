from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


ROOT = Path(__file__).resolve().parents[1]
STATUS_HUD = ROOT / "workspace/public/src/native-init/v319/30_status_hud.inc.c"
MENU_SOURCE = ROOT / "workspace/public/src/native-init/v319/40_menu_apps.inc.c"
AUDIO_SOURCE = ROOT / "workspace/public/src/native-init/a90_audio.c"

runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3163_badapple_nyan_cleanup_cadence.py"
)


class NativeVideoBadappleNyanCleanupCadenceSourceV3163Tests(unittest.TestCase):
    def test_v3163_identity_and_markers(self) -> None:
        self.assertEqual(runner.CYCLE, "V3163")
        self.assertEqual(runner.INIT_VERSION, "0.11.6")
        self.assertEqual(runner.INIT_BUILD, "v3163-badapple-nyan-cleanup-cadence")
        self.assertEqual(runner.VIDEO_PLAYER_HUD_METRICS_INTERVAL_FRAMES, 60)
        self.assertEqual(runner.VIDEO_PLAYER_HUD_STORAGE_INTERVAL_FRAMES, 180)
        self.assertEqual(runner.VIDEO_PLAYER_HUD_TEXT_INTERVAL_FRAMES, 30)
        self.assertEqual(runner.VIDEO_PLAYER_HUD_FULL_REPAINT_INTERVAL_FRAMES, 0)

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"0.11.6", required)
        self.assertIn(b"v3163-badapple-nyan-cleanup-cadence", required)
        self.assertIn(b"video.status.player_hud_metrics_interval_frames=%u", required)
        self.assertIn(b"video.status.player_hud_storage_interval_frames=%u", required)
        self.assertIn(b"video.status.player_hud_full_repaint_interval_frames=%u", required)
        self.assertIn(b"menu.demo.badapple.audio_pre_stop_best_effort=1", required)
        self.assertIn(b"menu.demo.badapple.audio_post_stop_required=1", required)
        self.assertIn(b"menu.demo.nyan.audio_pre_stop_best_effort=1", required)
        self.assertIn(b"menu.demo.nyan.audio_post_stop_required=1", required)
        self.assertIn(b"audio.play.worker.cleanup_deferred=", required)
        self.assertIn(b"audio.play.worker.exit_deferred=", required)
        self.assertIn(b"audio.play.worker.done=1", required)
        self.assertIn(b"a90.doomgeneric.v3163.input_thread=background-drain-udp-unix-dgram", required)
        self.assertNotIn(b"v3162-audio-stop-owned-cleanup", required)

    def test_player_hud_cadence_reduces_periodic_work(self) -> None:
        source = STATUS_HUD.read_text(encoding="utf-8")

        self.assertIn("#define VIDEO_PLAYER_HUD_METRICS_INTERVAL_FRAMES 60U", source)
        self.assertIn("#define VIDEO_PLAYER_HUD_STORAGE_INTERVAL_FRAMES 180U", source)
        self.assertIn("#define VIDEO_PLAYER_HUD_TEXT_INTERVAL_FRAMES 30U", source)
        self.assertIn("#define VIDEO_PLAYER_HUD_FULL_REPAINT_INTERVAL_FRAMES 0U", source)
        self.assertIn("video.status.player_hud_metrics_interval_frames=%u", source)
        self.assertIn("video.status.player_hud_storage_interval_frames=%u", source)
        self.assertIn("VIDEO_PLAYER_HUD_FULL_REPAINT_INTERVAL_FRAMES > 0U", source)
        self.assertIn('strstr(status, "audio.play.worker.done=1")', source)

    def test_menu_stops_demo_audio_around_badapple_and_nyan(self) -> None:
        source = MENU_SOURCE.read_text(encoding="utf-8")

        self.assertIn("static int auto_hud_stop_demo_audio", source)
        self.assertIn('auto_hud_stop_demo_audio("badapple", "pre")', source)
        self.assertIn('auto_hud_stop_demo_audio("badapple", "post")', source)
        self.assertIn('auto_hud_stop_demo_audio("nyan", "pre")', source)
        self.assertIn('auto_hud_stop_demo_audio("nyan", "post")', source)
        self.assertIn("menu.demo.badapple.audio_pre_stop_best_effort=1", source)
        self.assertIn("menu.demo.badapple.audio_post_stop_required=1", source)
        self.assertIn("menu.demo.nyan.audio_pre_stop_best_effort=1", source)
        self.assertIn("menu.demo.nyan.audio_post_stop_required=1", source)

    def test_audio_stop_kills_deferred_completed_status_worker(self) -> None:
        source = AUDIO_SOURCE.read_text(encoding="utf-8")
        start = source.index("static int audio_play_stop_status_worker")
        end = source.index("static int audio_play_cmd", start)
        block = source[start:end]

        self.assertIn("cleanup_deferred_value", block)
        self.assertIn("exit_deferred_value", block)
        self.assertIn('"audio.play.worker.cleanup_deferred="', block)
        self.assertIn('"audio.play.worker.exit_deferred="', block)
        self.assertIn("done_value != 0 &&\n        !cleanup_deferred &&\n        !exit_deferred", block)

    def test_manifest_marks_badapple_nyan_cleanup_validation_focus(self) -> None:
        text = Path(
            "workspace/public/src/scripts/revalidation/build_native_init_boot_v3163_badapple_nyan_cleanup_cadence.py"
        ).read_text(encoding="utf-8")

        self.assertIn(
            '"requires_live_validation": ["badapple", "nyan", "player-hud-cadence", "audio-cleanup"]',
            text,
        )
        self.assertIn('"source_baseline": "v3162-audio-stop-owned-cleanup"', text)
        self.assertIn('"periodic_full_repaint_disabled": True', text)
        self.assertIn('"sync_rejects_completed_audio_status": True', text)
        self.assertIn('"affected_demos": ["badapple", "nyan"]', text)

    def test_adapter_source_rewrites_to_v3163(self) -> None:
        source = runner.v3163_adapter_source()

        self.assertIn(
            "a90.doomgeneric.v3163.audio=real-sfx-pcm-stream-badapple-nyan-cleanup-cadence",
            source,
        )
        self.assertIn("a90.doomgeneric.v3163.demo_hud=large-grouped-hw-doom-input", source)
        self.assertNotIn("v3162", source)
        self.assertNotIn("v3154", source)


if __name__ == "__main__":
    unittest.main()
