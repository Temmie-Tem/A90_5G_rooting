"""Tests for the V2817 read-only audio selftest status entry."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SELFTEST_C = REPO / "workspace/public/src/native-init/a90_selftest.c"
PROFILE_H = REPO / "workspace/public/src/native-init/a90_audio_profile.h"
AUDIO_C = REPO / "workspace/public/src/native-init/a90_audio.c"


class NativeAudioSelftestStatusV2817(unittest.TestCase):
    def test_promotion_constants_are_shared_from_profile_header(self) -> None:
        header = PROFILE_H.read_text(encoding="utf-8")
        audio = AUDIO_C.read_text(encoding="utf-8")

        self.assertIn('#define AUDIO_CORE_PROMOTION_RUN "V2815"', header)
        self.assertIn('#define AUDIO_CORE_PROMOTION_VERSION "0.10.0"', header)
        self.assertIn('#define AUDIO_CORE_PROMOTION_TAG "v2812-audio-core-promotion-candidate"', header)
        self.assertIn('#define AUDIO_CORE_VALIDATION_RUN "V2814"', header)
        self.assertIn('AUDIO_CORE_PROMOTION_VERSION', audio)
        self.assertNotIn('#define AUDIO_CORE_PROMOTION_VERSION "0.10.0"', audio)

    def test_selftest_has_read_only_audio_entry(self) -> None:
        text = SELFTEST_C.read_text(encoding="utf-8")

        for marker in [
            '#include "a90_audio_profile.h"',
            '#include "a90_audio_route.h"',
            'static void selftest_audio(void)',
            'a90_audio_find_profile(AUDIO_DEFAULT_PROFILE_ID)',
            'a90_audio_route_control_count()',
            'a90_audio_speaker_map_count()',
            'a90_audio_route_has_smart_amp_boost()',
            'a90_audio_route_layer_write_allowed(AUDIO_ROUTE_LAYER_BLOCKED)',
            'AUDIO_CORE_PROMOTION_VERSION',
            'selftest_record_elapsed("audio"',
            'sp=unverified',
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_selftest_audio_runs_before_longsoak_and_usb(self) -> None:
        text = SELFTEST_C.read_text(encoding="utf-8")
        run_block = text[text.index('static int selftest_run'):]

        self.assertLess(run_block.index('selftest_service();'), run_block.index('selftest_audio();'))
        self.assertLess(run_block.index('selftest_audio();'), run_block.index('selftest_longsoak();'))
        self.assertLess(run_block.index('selftest_audio();'), run_block.index('selftest_usb();'))

    def test_selftest_audio_does_not_touch_runtime_audio_devices(self) -> None:
        text = SELFTEST_C.read_text(encoding="utf-8")
        block = text[text.index('static void selftest_audio'):text.index('static void selftest_longsoak')]

        forbidden = [
            'open(',
            'ioctl(',
            'audio_route_write',
            'audio_setcal',
            'audio_play',
            'SNDRV_CTL_IOCTL_ELEM_WRITE',
        ]
        for marker in forbidden:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, block)


if __name__ == "__main__":
    unittest.main()
