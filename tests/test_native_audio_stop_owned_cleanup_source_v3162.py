from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


ROOT = Path(__file__).resolve().parents[1]
AUDIO_SOURCE = ROOT / "workspace/public/src/native-init/a90_audio.c"

runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3162_audio_stop_owned_cleanup.py"
)


class NativeAudioStopOwnedCleanupSourceV3162Tests(unittest.TestCase):
    def test_v3162_identity_and_markers(self) -> None:
        self.assertEqual(runner.CYCLE, "V3162")
        self.assertEqual(runner.INIT_VERSION, "0.11.5")
        self.assertEqual(runner.INIT_BUILD, "v3162-audio-stop-owned-cleanup")

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"0.11.5", required)
        self.assertIn(b"v3162-audio-stop-owned-cleanup", required)
        self.assertIn(
            b"audio.play.integrated.cleanup.deferred=1 reason=pcm-complete-await-audio-stop",
            required,
        )
        self.assertIn(b"audio.play.worker.cleanup_deferred=1", required)
        self.assertIn(b"audio.play.worker.cleanup_owner=audio-stop", required)
        self.assertIn(b"audio.play.worker.exit_deferred=1", required)
        self.assertIn(b"a90.doomgeneric.v3162.input_thread=background-drain-udp-unix-dgram", required)
        self.assertNotIn(b"v3161-audio-close-deferred", required)

    def test_audio_source_marks_done_before_stop_owned_cleanup(self) -> None:
        source = AUDIO_SOURCE.read_text(encoding="utf-8")
        pcm = source.index("rc = audio_play_execute_pcm(profile,")
        deferred = source.index(
            "audio.play.integrated.cleanup.deferred=1 reason=pcm-complete-await-audio-stop"
        )
        worker_done = source.index('audio_play_async_statusf("audio.play.worker.done=1 rc=0', deferred)
        wait_loop = source.index("for (;;) {\n            pause();\n        }", worker_done)
        done_label = source.index("\ndone:", wait_loop)
        route_reset = source.index("cleanup_rc = audio_play_run_route_stage(profile, true)", done_label)

        self.assertLess(pcm, deferred)
        self.assertLess(deferred, worker_done)
        self.assertLess(worker_done, wait_loop)
        self.assertLess(wait_loop, done_label)
        self.assertLess(done_label, route_reset)
        self.assertIn("audio.play.worker.cleanup_owner=audio-stop", source)
        self.assertIn("audio.play.worker.exit_deferred=1", source)

    def test_manifest_marks_stop_owned_cleanup_validation_focus(self) -> None:
        text = Path(
            "workspace/public/src/scripts/revalidation/build_native_init_boot_v3162_audio_stop_owned_cleanup.py"
        ).read_text(encoding="utf-8")

        self.assertIn(
            '"requires_live_validation": ["badapple", "nyan", "audio-worker-completion", "audio-stop-cleanup"]',
            text,
        )
        self.assertIn('"source_baseline": "v3161-audio-close-deferred"', text)
        self.assertIn('"stop_owned_cleanup": True', text)

    def test_adapter_source_rewrites_to_v3162(self) -> None:
        source = runner.v3162_adapter_source()

        self.assertIn("a90.doomgeneric.v3162.audio=real-sfx-pcm-stream-audio-stop-owned-cleanup", source)
        self.assertIn("a90.doomgeneric.v3162.demo_hud=large-grouped-hw-doom-input", source)
        self.assertNotIn("v3161", source)
        self.assertNotIn("v3154", source)


if __name__ == "__main__":
    unittest.main()
