from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


ROOT = Path(__file__).resolve().parents[1]
AUDIO_SOURCE = ROOT / "workspace/public/src/native-init/a90_audio.c"

runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3161_audio_close_deferred.py"
)


class NativeAudioCloseDeferredSourceV3161Tests(unittest.TestCase):
    def test_v3161_identity_and_markers(self) -> None:
        self.assertEqual(runner.CYCLE, "V3161")
        self.assertEqual(runner.INIT_VERSION, "0.11.4")
        self.assertEqual(runner.INIT_BUILD, "v3161-audio-close-deferred")

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"0.11.4", required)
        self.assertIn(b"v3161-audio-close-deferred", required)
        self.assertIn(b"audio.play.execute.close.deferred=1 reason=route-reset-before-pcm-close", required)
        self.assertIn(b"audio.play.worker.close_deferred=1", required)
        self.assertIn(b"a90.doomgeneric.v3161.input_thread=background-drain-udp-unix-dgram", required)
        self.assertNotIn(b"v3160-audio-post-drain-hwfree", required)

    def test_audio_source_defers_explicit_pcm_close(self) -> None:
        source = AUDIO_SOURCE.read_text(encoding="utf-8")
        drain = source.index("audio.play.execute.drain.rc=%d errno=%d")
        drop = source.index("audio.play.execute.post_drain_drop.rc=%d errno=%d")
        hwfree = source.index("audio.play.execute.post_drain_hw_free.rc=%d errno=%d")
        deferred = source.index("audio.play.execute.close.deferred=1 reason=route-reset-before-pcm-close")
        source_close = source.index("close(source_fd);", deferred)

        self.assertLess(drain, drop)
        self.assertLess(drop, hwfree)
        self.assertLess(hwfree, deferred)
        self.assertLess(deferred, source_close)
        self.assertIn("audio.play.worker.close_deferred=1", source)
        self.assertIn("audio.play.worker.close_deferred_reason=route-reset-before-pcm-close", source)

    def test_manifest_marks_close_deferred_validation_focus(self) -> None:
        text = Path(
            "workspace/public/src/scripts/revalidation/build_native_init_boot_v3161_audio_close_deferred.py"
        ).read_text(encoding="utf-8")

        self.assertIn('"requires_live_validation": ["badapple", "nyan", "audio-worker-completion"]', text)
        self.assertIn('"source_baseline": "v3160-audio-post-drain-hwfree"', text)
        self.assertIn('"audio_close_deferred": True', text)

    def test_adapter_source_rewrites_to_v3161(self) -> None:
        source = runner.v3161_adapter_source()

        self.assertIn("a90.doomgeneric.v3161.audio=real-sfx-pcm-stream-audio-close-deferred", source)
        self.assertIn("a90.doomgeneric.v3161.demo_hud=large-grouped-hw-doom-input", source)
        self.assertNotIn("v3160", source)
        self.assertNotIn("v3154", source)


if __name__ == "__main__":
    unittest.main()
