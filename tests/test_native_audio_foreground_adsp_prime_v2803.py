"""Tests for the V2803 foreground ADSP prime before audio play worker."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
AUDIO_C = REPO / "workspace/public/src/native-init/a90_audio.c"
BUILDER = REPO / "workspace/public/src/scripts/revalidation/build_native_init_boot_v2803_audio_foreground_adsp_prime.py"


class NativeAudioForegroundAdspPrimeV2803(unittest.TestCase):
    def test_audio_play_execute_primes_adsp_before_worker(self) -> None:
        text = AUDIO_C.read_text(encoding="utf-8")

        self.assertIn("audio.play.execute.plan.foreground_prime_adsp=1", text)
        self.assertIn("audio.play.execute.foreground_prime_adsp=1", text)
        self.assertIn("prime_rc = audio_play_run_adsp_stage(profile);", text)
        self.assertIn("audio.play.execute.foreground_prime_adsp.rc=%d", text)
        self.assertIn("audio.play.execute.foreground_prime_adsp.failed=1", text)
        self.assertLess(
            text.index("prime_rc = audio_play_run_adsp_stage(profile);"),
            text.index('a90_console_printf("audio.play.execute.async_worker=1\\r\\n");'),
        )
        self.assertLess(
            text.index('a90_console_printf("audio.play.execute.async_worker=1\\r\\n");'),
            text.index("return audio_play_start_worker(profile, mode, amplitude_milli, duration_ms, manifest_path);"),
        )

    def test_worker_stage_remains_idempotent_after_foreground_prime(self) -> None:
        text = AUDIO_C.read_text(encoding="utf-8")

        self.assertIn("audio.play.integrated.adsp.already_ready=1", text)
        self.assertIn("rc = audio_adsp_boot_once(adsp_argv, 3);", text)
        self.assertIn("if (rc == -EALREADY)", text)
        self.assertIn(
            'audio_wait_for_audio_condition("sound_control", 70000, 250, audio_condition_sound_control_ready, profile)',
            text,
        )

    def test_builder_uses_v2803_artifact_identity(self) -> None:
        text = BUILDER.read_text(encoding="utf-8")

        self.assertIn('CYCLE = "V2803"', text)
        self.assertIn('INIT_VERSION = "0.9.313"', text)
        self.assertIn('INIT_BUILD = "v2803-audio-foreground-adsp-prime"', text)
        self.assertIn('boot_linux_v2803_audio_foreground_adsp_prime.img', text)
        self.assertIn("foreground_adsp_prime_compiled", text)
        self.assertIn("v2802_blocker", text)


if __name__ == "__main__":
    unittest.main()
