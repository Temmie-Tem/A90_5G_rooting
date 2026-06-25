from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


ROOT = Path(__file__).resolve().parents[1]
AUDIO_SOURCE = ROOT / "workspace/public/src/native-init/a90_audio.c"
STATUS_HUD = ROOT / "workspace/public/src/native-init/v319/30_status_hud.inc.c"

runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3159_audio_post_drain_drop.py"
)


class NativeAudioPostDrainDropSourceV3159Tests(unittest.TestCase):
    def test_v3159_identity_and_markers(self) -> None:
        self.assertEqual(runner.CYCLE, "V3159")
        self.assertEqual(runner.INIT_VERSION, "0.11.2")
        self.assertEqual(runner.INIT_BUILD, "v3159-audio-post-drain-drop")

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"0.11.2", required)
        self.assertIn(b"v3159-audio-post-drain-drop", required)
        self.assertIn(b"video.status.player_hud_fastscale=1", required)
        self.assertIn(b"audio.play.execute.post_drain_drop.rc=%d errno=%d", required)
        self.assertIn(b"audio.play.worker.post_drain_drop_rc=%d", required)
        self.assertIn(b"a90.doomgeneric.v3159.input_thread=background-drain-udp-unix-dgram", required)
        self.assertNotIn(b"v3158-badapple-nyan-fastscale", required)

    def test_audio_source_drops_pcm_after_drain_before_close(self) -> None:
        source = AUDIO_SOURCE.read_text(encoding="utf-8")
        drain = source.index("audio.play.execute.drain.rc=%d errno=%d")
        drop = source.index("audio.play.execute.post_drain_drop.rc=%d errno=%d")
        close = source.index("close(fd);", drop)

        self.assertLess(drain, drop)
        self.assertLess(drop, close)
        self.assertIn("post_drain_drop_rc = ioctl(fd, SNDRV_PCM_IOCTL_DROP);", source)
        self.assertIn("audio.play.worker.post_drain_drop_rc=%d", source)
        self.assertIn("audio.play.worker.post_drain_drop_errno=%d", source)

    def test_video_fastscale_is_preserved(self) -> None:
        source = STATUS_HUD.read_text(encoding="utf-8")

        self.assertIn('a90_console_printf("video.status.player_hud_fastscale=1\\r\\n");', source)
        self.assertIn("video_expand_mono1_frame_scaled2", source)
        self.assertIn("video_expand_pal8_rle_scaled2", source)
        self.assertIn("previous_progress_fill", source)

    def test_manifest_marks_audio_worker_validation_focus(self) -> None:
        text = Path(
            "workspace/public/src/scripts/revalidation/build_native_init_boot_v3159_audio_post_drain_drop.py"
        ).read_text(encoding="utf-8")

        self.assertIn('"requires_live_validation": ["badapple", "nyan", "audio-worker-completion"]', text)
        self.assertIn('"live_validation_focus": ["badapple", "nyan", "audio-worker-completion"]', text)
        self.assertIn('"source_baseline": "v3158-badapple-nyan-fastscale"', text)
        self.assertIn('"audio_post_drain_drop": True', text)

    def test_adapter_source_rewrites_to_v3159(self) -> None:
        source = runner.v3159_adapter_source()

        self.assertIn("a90.doomgeneric.v3159.audio=real-sfx-pcm-stream-audio-post-drain-drop", source)
        self.assertIn("a90.doomgeneric.v3159.demo_hud=large-grouped-hw-doom-input", source)
        self.assertNotIn("v3158", source)
        self.assertNotIn("v3154", source)


if __name__ == "__main__":
    unittest.main()
