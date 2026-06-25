from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


runner = load_script("workspace/public/src/scripts/revalidation/build_native_init_boot_v3145_doomgeneric_sfx_stream_write_retry.py")


class NativeDoomgenericSfxStreamWriteRetrySourceV3145Tests(unittest.TestCase):
    def test_loop_only_enables_sfx_sound(self) -> None:
        source = runner.v3145_adapter_source()
        loop_start = source.index("int a90_doomgeneric_run_wad_frame_loop(")
        loop_end = source.index("\nint main(int argc, char **argv) {", loop_start)
        loop = source[loop_start:loop_end]
        prepare_start = source.index("int a90_doomgeneric_prepare_argv(")
        prepare_end = source.index("unsigned int a90_doomgeneric_last_seq", prepare_start)
        prepare = source[prepare_start:prepare_end]

        self.assertIn("a90.doomgeneric.v3145.audio=real-sfx-pcm-stream-write-retry-music-disabled", source)
        self.assertIn('argv[3] = arg_nomusic;', loop)
        self.assertIn("doomgeneric_Create(11, argv);", loop)
        self.assertNotIn("arg_nosound", loop)
        self.assertIn("-nosound", prepare)

    def test_generated_sfx_backend_uses_fifo_not_alsa(self) -> None:
        backend = runner.SFX_BACKEND_SOURCE_TEXT

        self.assertIn("sound_module_t DG_sound_module", backend)
        self.assertIn("music_module_t DG_music_module", backend)
        self.assertIn(runner.AUDIO_PCM_STREAM_PATH, backend)
        self.assertIn("open(A90_SFX_STREAM_PATH, O_WRONLY | O_NONBLOCK | O_CLOEXEC)", backend)
        self.assertNotIn("SNDRV_", backend)
        self.assertNotIn("/dev/snd", backend)

    def test_required_strings_include_stream_contract(self) -> None:
        required = b"\n".join(runner.REQUIRED_STRINGS)

        self.assertIn(runner.SOUND_MODE.encode("ascii"), required)
        self.assertIn(runner.AUDIO_PCM_STREAM_PATH.encode("ascii"), required)
        self.assertIn(b"--pcm-stream", required)
        self.assertIn(b"audio.play.pcm_stream_supported=1", required)

    def test_native_audio_stream_is_nonblocking_and_xrun_recoverable(self) -> None:
        source = Path("workspace/public/src/native-init/a90_audio.c").read_text(encoding="utf-8")
        hud = Path("workspace/public/src/native-init/v319/30_status_hud.inc.c").read_text(encoding="utf-8")

        self.assertIn("O_RDONLY | O_NONBLOCK | O_CLOEXEC", source)
        self.assertIn("errno == EAGAIN || errno == EWOULDBLOCK", source)
        self.assertIn("audio.play.execute.write.xrun_recover", source)
        self.assertIn("audio.play.execute.write.eagain_retry", source)
        self.assertIn("usleep(1000)", source)
        self.assertIn('ensure_dir("/cache/a90-runtime", 0700)', hud)


if __name__ == "__main__":
    unittest.main()
