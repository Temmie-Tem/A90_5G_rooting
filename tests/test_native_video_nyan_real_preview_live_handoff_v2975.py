"""Static checks for V2975 Nyan real preview live handoff."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "workspace/public/src/scripts/revalidation/native_video_nyan_real_preview_live_handoff_v2975.py"


class TestNativeVideoNyanRealPreviewLiveHandoffV2975(unittest.TestCase):
    def setUp(self) -> None:
        self.text = RUNNER.read_text(encoding="utf-8")

    def test_runner_targets_v2974_candidate_and_v2321_rollback(self) -> None:
        self.assertIn('RUN_ID = "V2975"', self.text)
        self.assertIn('CANDIDATE_VERSION = "0.10.59"', self.text)
        self.assertIn('CANDIDATE_TAG = "v2974-nyan-real-preset"', self.text)
        self.assertIn("boot_linux_v2974_nyan_real_preset.img", self.text)
        self.assertIn("video_live.ROLLBACK_IMAGE", self.text)
        self.assertIn("rollback v2321", self.text)

    def test_runner_uses_real_nyan_assets_and_low_amplitude_audio(self) -> None:
        self.assertIn("v2973-nyancat-pal8-rle-preview", self.text)
        self.assertIn("nyancat-v2973-pal8-rle-preview", self.text)
        self.assertIn("9a8d91956218acf674b7d99d421467effec442fdde1dbbea8635b8f47085c573", self.text)
        self.assertIn("4c3774553195c04166a3a83de793253696a5bee60afe83a04219419fc28e43de", self.text)
        self.assertIn("AUDIO_AMPLITUDE_MILLI = 150", self.text)
        self.assertIn("AUDIO_PCM_GAIN_MILLI = 780", self.text)
        self.assertIn("--pcm-file", self.text)
        self.assertIn("pcm_file_validated", self.text)
        self.assertIn("execute_plan_waveform_file", self.text)

    def test_runner_validates_setcrtc_player_hud_path(self) -> None:
        self.assertIn('PRESENT_MODE = "setcrtc"', self.text)
        self.assertIn('LAYOUT = "player-hud"', self.text)
        self.assertIn("video.stream.path=kms-dumb-buffer", self.text)
        self.assertIn("video.stream.pixel_format={NYAN_FORMAT}", self.text)
        self.assertIn("video.stream.audio_sync.drop_policy=none", self.text)
        self.assertIn("video.cache.play.requested_present={PRESENT_MODE}", self.text)
        self.assertIn("video.cache.play.requested_layout={LAYOUT}", self.text)

    def test_runner_keeps_private_media_untracked_and_forbidden_paths_out(self) -> None:
        forbidden = (
            "/efs",
            "/sec_efs",
            "pmic",
            "GDSC write",
            "raw DSI write",
            "fastboot flash",
        )
        for token in forbidden:
            self.assertNotIn(token, self.text)
        self.assertIn("private Nyan raw stream/audio remain untracked", self.text)


if __name__ == "__main__":
    unittest.main()
