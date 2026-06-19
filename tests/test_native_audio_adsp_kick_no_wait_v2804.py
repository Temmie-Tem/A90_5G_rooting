"""Tests for the V2804 no-wait ADSP kick before audio play worker."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
AUDIO_C = REPO / "workspace/public/src/native-init/a90_audio.c"
BUILDER = REPO / "workspace/public/src/scripts/revalidation/build_native_init_boot_v2804_audio_adsp_kick_no_wait.py"


class NativeAudioAdspKickNoWaitV2804(unittest.TestCase):
    def test_play_execute_kicks_adsp_without_waiting_before_worker(self) -> None:
        text = AUDIO_C.read_text(encoding="utf-8")

        self.assertIn("audio_play_kick_adsp_stage_no_wait", text)
        self.assertIn("audio.play.execute.foreground_prime_adsp.wait=0", text)
        self.assertIn("prime_rc = audio_play_kick_adsp_stage_no_wait(profile);", text)
        self.assertIn("audio.play.worker.adsp_prebooted=%d", text)
        self.assertIn("audio.play.integrated.adsp_prebooted=%d", text)
        self.assertIn("audio.play.integrated.adsp.boot_skipped=1 reason=foreground_prime_no_wait", text)
        self.assertLess(
            text.index("prime_rc = audio_play_kick_adsp_stage_no_wait(profile);"),
            text.index('a90_console_printf("audio.play.execute.async_worker=1\\r\\n");'),
        )
        self.assertLess(
            text.index('a90_console_printf("audio.play.execute.async_worker=1\\r\\n");'),
            text.index("return audio_play_start_worker(profile, mode, amplitude_milli, duration_ms, manifest_path, true);"),
        )

    def test_integrated_worker_does_not_rewrite_adsp_after_preboot(self) -> None:
        text = AUDIO_C.read_text(encoding="utf-8")

        self.assertIn("audio_play_run_adsp_stage(profile, !adsp_prebooted)", text)
        self.assertIn("audio.play.integrated.adsp.boot_allowed=%d", text)
        self.assertIn("audio.play.integrated.adsp.boot_skipped=1 reason=foreground_prime_no_wait", text)
        self.assertIn(
            'audio_wait_for_audio_condition("sound_control", 70000, 250, audio_condition_sound_control_ready, profile)',
            text,
        )

    def test_builder_uses_v2804_artifact_identity(self) -> None:
        text = BUILDER.read_text(encoding="utf-8")

        self.assertIn('CYCLE = "V2804"', text)
        self.assertIn('INIT_VERSION = "0.9.314"', text)
        self.assertIn('INIT_BUILD = "v2804-audio-adsp-kick-no-wait"', text)
        self.assertIn('boot_linux_v2804_audio_adsp_kick_no_wait.img', text)
        self.assertIn("foreground_adsp_kick_no_wait_compiled", text)
        self.assertIn("v2803_blocker", text)


if __name__ == "__main__":
    unittest.main()
