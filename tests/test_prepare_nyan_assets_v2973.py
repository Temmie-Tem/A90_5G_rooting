import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "workspace/public/src/scripts/revalidation/prepare_nyan_assets_v2973.py"


class PrepareNyanAssetsV2973(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = SOURCE.read_text(encoding="utf-8")

    def test_defaults_match_player_hud_real_nyan_geometry(self) -> None:
        self.assertIn('RUN_ID = "V2973"', self.text)
        self.assertIn('DEFAULT_SOURCE = ROOT / "workspace/private/demo-assets/video/nyancat-src.mp4"', self.text)
        self.assertIn('parser.add_argument("--width", type=int, default=540)', self.text)
        self.assertIn('parser.add_argument("--height", type=int, default=360)', self.text)
        self.assertIn('parser.add_argument("--max-frames", type=int, default=300)', self.text)

    def test_video_uses_global_palette_before_pal8_rle_encode(self) -> None:
        self.assertIn("palettegen=max_colors={max_colors}:reserve_transparent=0", self.text)
        self.assertIn("paletteuse=dither=none,format=rgb24", self.text)
        self.assertIn("prepare_nyan_pal8_rle_v2970 as pal8_encoder", self.text)
        self.assertIn('input_format="ppm"', self.text)

    def test_cache_compatible_stream_path_is_rewritten(self) -> None:
        self.assertIn('stream_dir / "frames.a90vstr2"', self.text)
        self.assertIn('stream_dir / "frames.a90vstr"', self.text)
        self.assertIn('manifest["video"]["path"] = "frames.a90vstr"', self.text)
        self.assertIn('f"{stream_sha}  frames.a90vstr\\n"', self.text)

    def test_audio_is_bounded_and_s16le(self) -> None:
        self.assertIn("MAX_AUDIO_VOLUME = 0.2", self.text)
        self.assertIn('parser.add_argument("--audio-volume", type=float, default=0.12)', self.text)
        self.assertIn('"-f",', self.text)
        self.assertIn('"s16le"', self.text)
        self.assertIn("--audio-volume must be within 0.0..", self.text)

    def test_report_validation_fields_are_explicit(self) -> None:
        self.assertIn('"py_compile": bool(args.validation_py_compile)', self.text)
        self.assertIn('"unit_tests": bool(args.validation_unit_tests)', self.text)
        self.assertIn('payload["validation"]["host_asset_run"] = True', self.text)
        self.assertIn('parser.add_argument("--validation-py-compile", action="store_true")', self.text)
        self.assertIn('parser.add_argument("--validation-unit-tests", action="store_true")', self.text)


if __name__ == "__main__":
    unittest.main()
