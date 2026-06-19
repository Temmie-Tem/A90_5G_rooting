"""Tests for the V2828 audio route-map safety label polish."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
AUDIO_APP_C = REPO / "workspace/public/src/native-init/a90_app_audio.c"


class NativeAudioRouteMapSafetyLabelsV2828Test(unittest.TestCase):
    def test_route_map_separates_boost_block_and_unverified_sp(self) -> None:
        source = AUDIO_APP_C.read_text(encoding="utf-8")

        for marker in [
            '"BOOST WRITE BLOCKED %d  SP UNVERIFIED"',
            '"LEFT %s route=%d obs=%d boost=%d"',
            '"RIGHT %s route=%d obs=%d boost=%d"',
            '"VI SPKR_VI_1/SPKR_VI_2 OBSERVED ONLY"',
            'a90_audio_observer_count_for_prefix(profile, "SpkrLeft")',
            'a90_audio_observer_count_for_prefix(profile, "SpkrRight")',
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, source)

    def test_route_map_screen_remains_display_only(self) -> None:
        source = AUDIO_APP_C.read_text(encoding="utf-8")

        for forbidden in [
            "open(",
            "ioctl(",
            "audio_route_write",
            "audio_setcal",
            "audio_play",
            "SNDRV_CTL_IOCTL_ELEM_WRITE",
            "tinymix",
            "tinyplay",
        ]:
            with self.subTest(marker=forbidden):
                self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
