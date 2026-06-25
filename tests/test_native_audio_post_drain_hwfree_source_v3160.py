from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


ROOT = Path(__file__).resolve().parents[1]
AUDIO_SOURCE = ROOT / "workspace/public/src/native-init/a90_audio.c"

runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3160_audio_post_drain_hwfree.py"
)


class NativeAudioPostDrainHwfreeSourceV3160Tests(unittest.TestCase):
    def test_v3160_identity_and_markers(self) -> None:
        self.assertEqual(runner.CYCLE, "V3160")
        self.assertEqual(runner.INIT_VERSION, "0.11.3")
        self.assertEqual(runner.INIT_BUILD, "v3160-audio-post-drain-hwfree")

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"0.11.3", required)
        self.assertIn(b"v3160-audio-post-drain-hwfree", required)
        self.assertIn(b"audio.play.execute.post_drain_drop.rc=%d errno=%d", required)
        self.assertIn(b"audio.play.execute.post_drain_hw_free.rc=%d errno=%d", required)
        self.assertIn(b"audio.play.worker.post_drain_hw_free_rc=%d", required)
        self.assertIn(b"a90.doomgeneric.v3160.input_thread=background-drain-udp-unix-dgram", required)
        self.assertNotIn(b"v3159-audio-post-drain-drop", required)

    def test_audio_source_frees_pcm_hw_before_close(self) -> None:
        source = AUDIO_SOURCE.read_text(encoding="utf-8")
        drain = source.index("audio.play.execute.drain.rc=%d errno=%d")
        drop = source.index("audio.play.execute.post_drain_drop.rc=%d errno=%d")
        hwfree = source.index("audio.play.execute.post_drain_hw_free.rc=%d errno=%d")
        close = source.index("close(fd);", hwfree)

        self.assertLess(drain, drop)
        self.assertLess(drop, hwfree)
        self.assertLess(hwfree, close)
        self.assertIn("post_drain_drop_rc = ioctl(fd, SNDRV_PCM_IOCTL_DROP);", source)
        self.assertIn("post_drain_hw_free_rc = ioctl(fd, SNDRV_PCM_IOCTL_HW_FREE);", source)
        self.assertIn("audio.play.worker.post_drain_hw_free_rc=%d", source)
        self.assertIn("audio.play.worker.post_drain_hw_free_errno=%d", source)

    def test_manifest_marks_hwfree_validation_focus(self) -> None:
        text = Path(
            "workspace/public/src/scripts/revalidation/build_native_init_boot_v3160_audio_post_drain_hwfree.py"
        ).read_text(encoding="utf-8")

        self.assertIn('"requires_live_validation": ["badapple", "nyan", "audio-worker-completion"]', text)
        self.assertIn('"live_validation_focus": ["badapple", "nyan", "audio-worker-completion"]', text)
        self.assertIn('"source_baseline": "v3159-audio-post-drain-drop"', text)
        self.assertIn('"audio_post_drain_hw_free": True', text)

    def test_adapter_source_rewrites_to_v3160(self) -> None:
        source = runner.v3160_adapter_source()

        self.assertIn("a90.doomgeneric.v3160.audio=real-sfx-pcm-stream-audio-post-drain-hwfree", source)
        self.assertIn("a90.doomgeneric.v3160.demo_hud=large-grouped-hw-doom-input", source)
        self.assertNotIn("v3159", source)
        self.assertNotIn("v3154", source)


if __name__ == "__main__":
    unittest.main()
