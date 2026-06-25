from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3149_doomgeneric_sfx_long_window_physical_exit.py"
)


class NativeDoomgenericSfxLongWindowPhysicalExitSourceV3149Tests(unittest.TestCase):
    def test_loop_keeps_sfx_sound_enabled_without_music(self) -> None:
        source = runner.v3149_adapter_source()
        loop_start = source.index("int a90_doomgeneric_run_wad_frame_loop(")
        loop_end = source.index("\nint main(int argc, char **argv) {", loop_start)
        loop = source[loop_start:loop_end]
        prepare_start = source.index("int a90_doomgeneric_prepare_argv(")
        prepare_end = source.index("unsigned int a90_doomgeneric_last_seq", prepare_start)
        prepare = source[prepare_start:prepare_end]

        self.assertIn(
            "a90.doomgeneric.v3149.audio=real-sfx-pcm-stream-long-window-physical-exit",
            source,
        )
        self.assertIn('argv[3] = arg_nomusic;', loop)
        self.assertIn("doomgeneric_Create(11, argv);", loop)
        self.assertNotIn("arg_nosound", loop)
        self.assertIn("-nosound", prepare)

    def test_long_window_audio_contract_is_built(self) -> None:
        self.assertEqual(runner.AUDIO_CORUN_DURATION_MS, 240000)
        self.assertEqual(runner.AUDIO_CORUN_REFRESH_MS, 0)
        self.assertEqual(runner.PHYSICAL_BUTTON_EXIT, 1)

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(runner.SOUND_MODE.encode("ascii"), required)
        self.assertIn(runner.AUDIO_PCM_STREAM_PATH.encode("ascii"), required)
        self.assertIn(b"video.demo.doom.loop.physical_button_exit=%d", required)
        self.assertIn(b"audio.play.cap.doom_sfx_stream_ms", required)

    def test_native_init_has_physical_exit_and_no_required_refresh(self) -> None:
        hud = Path("workspace/public/src/native-init/v319/30_status_hud.inc.c").read_text(
            encoding="utf-8"
        )
        v3033 = Path(
            "workspace/public/src/scripts/revalidation/build_native_init_boot_v3033_doomgeneric_visible_loop.py"
        ).read_text(encoding="utf-8")
        v3148 = Path(
            "workspace/public/src/scripts/revalidation/build_native_init_boot_v3148_doomgeneric_sfx_stream_refresh.py"
        ).read_text(encoding="utf-8")

        self.assertIn("A90_DOOMGENERIC_PHYSICAL_BUTTON_EXIT", hud)
        self.assertIn("video_demo_doom_physical_exit_poll", hud)
        self.assertIn("a90_input_open(&state->input", hud)
        self.assertIn("KEY_POWER", hud)
        self.assertIn("KEY_VOLUMEUP", hud)
        self.assertIn("KEY_VOLUMEDOWN", hud)
        self.assertIn("video_demo_doom_audio_corun_stop();", hud)
        self.assertIn("PHYSICAL_BUTTON_EXIT = 0", v3033)
        self.assertIn('numeric_define("A90_DOOMGENERIC_PHYSICAL_BUTTON_EXIT"', v3033)
        self.assertIn("PHYSICAL_BUTTON_EXIT = 0", v3148)
        self.assertIn('"PHYSICAL_BUTTON_EXIT": PHYSICAL_BUTTON_EXIT', v3148)

    def test_audio_cap_and_status_pid_stop_fallback_are_present(self) -> None:
        audio_c = Path("workspace/public/src/native-init/a90_audio.c").read_text(encoding="utf-8")

        self.assertIn("AUDIO_DOOM_SFX_STREAM_DURATION_CAP_MS", audio_c)
        self.assertIn("audio_pcm_stream_is_doom_sfx", audio_c)
        self.assertIn("doom-sfx-pcm-stream", audio_c)
        self.assertIn("audio_play_stop_status_worker", audio_c)
        self.assertIn("audio.stop.worker.status_pid", audio_c)
        self.assertIn("audio.stop.worker.status_stop_rc", audio_c)
        self.assertIn(
            "audio_play_effective_duration_cap_ms(profile, NULL, pcm_stream_path)",
            audio_c,
        )
        self.assertIn(
            "audio_play_effective_duration_cap_ms(profile, pcm_file_path, pcm_stream_path)",
            audio_c,
        )


if __name__ == "__main__":
    unittest.main()
