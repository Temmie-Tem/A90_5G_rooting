"""Tests for the V2845 best-effort native boot chime hook."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
AUDIO_C = REPO / "workspace/public/src/native-init/a90_audio.c"
AUDIO_H = REPO / "workspace/public/src/native-init/a90_audio.h"
CHIME_H = REPO / "workspace/public/src/native-init/a90_audio_chime.h"
MAIN_INC = REPO / "workspace/public/src/native-init/v724/90_main.inc.c"


class NativeAudioBootChimeV2845Test(unittest.TestCase):
    def test_default_autoplay_remains_compile_time_disabled(self) -> None:
        header = CHIME_H.read_text(encoding="utf-8")

        self.assertIn("#ifndef AUDIO_CHIME_BOOT_AUTOPLAY_DEFAULT", header)
        self.assertIn("#define AUDIO_CHIME_BOOT_AUTOPLAY_DEFAULT 0", header)

    def test_boot_chime_public_entrypoint_is_declared_and_gated(self) -> None:
        audio_h = AUDIO_H.read_text(encoding="utf-8")
        audio_c = AUDIO_C.read_text(encoding="utf-8")

        self.assertIn("int a90_audio_boot_chime_start_once(void);", audio_h)
        self.assertIn("int a90_audio_boot_chime_start_once(void)", audio_c)
        self.assertIn("#if AUDIO_CHIME_BOOT_AUTOPLAY_DEFAULT", audio_c)
        self.assertIn("audio.boot_chime.best_effort=1", audio_c)
        self.assertIn("audio.boot_chime.blocks_boot=0", audio_c)
        self.assertIn("audio.boot_chime.started=1", audio_c)
        self.assertIn("audio_chime_cmd(argv, argc)", audio_c)
        self.assertNotIn("waitpid(pid", audio_c[audio_c.index("int a90_audio_boot_chime_start_once"):])

    def test_pid1_calls_boot_chime_before_shell_loop(self) -> None:
        main = MAIN_INC.read_text(encoding="utf-8")
        call = "(void)a90_audio_boot_chime_start_once();"

        self.assertIn(call, main)
        self.assertLess(main.index(call), main.index('a90_logf("boot", "entering shell")'))
        self.assertLess(main.index(call), main.index("shell_loop();"))


if __name__ == "__main__":
    unittest.main()
