from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


runner = load_script("workspace/public/src/scripts/revalidation/build_native_init_boot_v3148_doomgeneric_sfx_stream_refresh.py")


class NativeDoomgenericSfxStreamRefreshSourceV3148Tests(unittest.TestCase):
    def test_loop_only_enables_sfx_sound(self) -> None:
        source = runner.v3148_adapter_source()
        loop_start = source.index("int a90_doomgeneric_run_wad_frame_loop(")
        loop_end = source.index("\nint main(int argc, char **argv) {", loop_start)
        loop = source[loop_start:loop_end]
        prepare_start = source.index("int a90_doomgeneric_prepare_argv(")
        prepare_end = source.index("unsigned int a90_doomgeneric_last_seq", prepare_start)
        prepare = source[prepare_start:prepare_end]

        self.assertIn("a90.doomgeneric.v3148.audio=real-sfx-pcm-stream-refresh-music-disabled", source)
        self.assertIn('argv[3] = arg_nomusic;', loop)
        self.assertIn("doomgeneric_Create(11, argv);", loop)
        self.assertNotIn("arg_nosound", loop)
        self.assertIn("-nosound", prepare)

    def test_audio_refresh_contract_is_built(self) -> None:
        self.assertEqual(runner.AUDIO_CORUN_DURATION_MS, 10000)
        self.assertEqual(runner.AUDIO_CORUN_REFRESH_MS, 13000)

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(runner.SOUND_MODE.encode("ascii"), required)
        self.assertIn(runner.AUDIO_PCM_STREAM_PATH.encode("ascii"), required)
        self.assertIn(b"--pcm-stream", required)

    def test_native_init_refreshes_bounded_audio_worker_quietly(self) -> None:
        audio_h = Path("workspace/public/src/native-init/a90_audio.h").read_text(encoding="utf-8")
        audio_c = Path("workspace/public/src/native-init/a90_audio.c").read_text(encoding="utf-8")
        hud = Path("workspace/public/src/native-init/v319/30_status_hud.inc.c").read_text(encoding="utf-8")
        v3033 = Path("workspace/public/src/scripts/revalidation/build_native_init_boot_v3033_doomgeneric_visible_loop.py").read_text(encoding="utf-8")

        self.assertIn("a90_audio_start_pcm_stream_worker_quiet", audio_h)
        self.assertIn("static int audio_play_start_worker_ex", audio_c)
        self.assertIn("bool quiet_parent", audio_c)
        self.assertIn("if (!quiet_parent)", audio_c)
        self.assertIn("AUDIO_PCM_GAIN_MILLI_DEFAULT", audio_c)
        self.assertIn("A90_DOOMGENERIC_AUDIO_CORUN_REFRESH_MS", hud)
        self.assertIn("video_demo_doom_audio_corun_refresh_quiet", hud)
        self.assertIn("background_child && continuous", hud)
        self.assertIn("a90_audio_start_pcm_stream_worker_quiet", hud)
        self.assertIn("numeric_define(\"A90_DOOMGENERIC_AUDIO_CORUN_REFRESH_MS\"", v3033)


if __name__ == "__main__":
    unittest.main()
