"""Tests for the V2788 audio speaker descriptor API live validation runner."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RUNNER = REPO / "workspace/public/src/scripts/revalidation/native_audio_speaker_descriptor_api_device_validation_handoff_v2788.py"


def runner_text() -> str:
    return RUNNER.read_text(encoding="utf-8")


class NativeAudioSpeakerDescriptorApiDeviceValidationV2788(unittest.TestCase):
    def test_runner_targets_v2787_image_and_v2321_rollback(self) -> None:
        text = runner_text()

        self.assertIn("v2787-audio-speaker-descriptor-api/manifest.json", text)
        self.assertIn("boot_linux_v2787_audio_speaker_descriptor_api.img", text)
        self.assertIn('CANDIDATE_VERSION = "0.9.301"', text)
        self.assertIn("boot_linux_v2321_usb_clean_identity_rodata.img", text)
        self.assertIn("ROLLBACK_SHA256", text)
        self.assertIn("native_init_flash.py", text)
        self.assertIn("v2788-audio-speaker-descriptor-api-device-pass", text)

    def test_runner_checks_descriptor_markers(self) -> None:
        text = runner_text()

        for marker in [
            "audio.speaker_map.version=1",
            "audio.speaker_map.profile=",
            "audio.speaker_map.read_only=1",
            "audio.speaker_map.route_write_attempted=0",
            "audio.speaker_map.playback_attempted=0",
            "audio.speaker_map.speaker.count=6",
            "audio.speaker_map.speaker.0.role=stream-route",
            "audio.speaker_map.speaker.1.role=feedback",
            "audio.speaker_map.speaker.2.role=feedback",
            "audio.speaker_map.speaker.3.role=feedback-format",
            "audio.speaker_map.speaker.4.role=endpoint",
            "audio.speaker_map.speaker.5.role=endpoint",
            "audio.speaker_map.speaker.4.hardware=left WSA881x speaker endpoint",
            "audio.speaker_map.speaker.5.hardware=right WSA881x speaker endpoint",
            "audio.speaker_map.speaker.4.safety=boost-write-blocked",
            "audio.speaker_map.speaker.5.safety=boost-write-blocked",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_runner_is_read_only_audio_observability(self) -> None:
        text = runner_text()

        self.assertIn('["audio", "status"]', text)
        self.assertIn('["audio", "profiles"]', text)
        self.assertIn('["audio", "profile", PROFILE]', text)
        self.assertIn('["audio", "speaker-map", PROFILE]', text)
        self.assertNotIn('["audio", "adsp-boot-once"', text)
        self.assertNotIn('["audio", "snd-materialize-once"', text)
        self.assertNotIn('["audio", "route", PROFILE, "--apply"', text)
        self.assertNotIn('["audio", "route", PROFILE, "--reset"', text)
        self.assertNotIn('["audio", "setcal"', text)
        self.assertNotIn('["audio", "play"', text)
        self.assertIn("No ADSP boot", text)
        self.assertIn("No forbidden partitions are touched", text)

    def test_runner_requires_decision_and_rollback_for_success(self) -> None:
        text = runner_text()

        self.assertIn('result.get("decision") == "v2788-audio-speaker-descriptor-api-device-pass"', text)
        self.assertIn('result.get("rollback_version_ok")', text)
        self.assertIn('result.get("rollback_selftest_fail0")', text)

    def test_runner_has_recovery_mode_rollback_fallback(self) -> None:
        text = runner_text()

        self.assertIn("def adb_recovery_present", text)
        self.assertIn('["adb", "devices"]', text)
        self.assertIn("def rollback_v2321", text)
        self.assertIn('"rollback-v2321-recovery-fallback"', text)
        self.assertIn("rollback_recovery_fallback_used", text)


if __name__ == "__main__":
    unittest.main()
