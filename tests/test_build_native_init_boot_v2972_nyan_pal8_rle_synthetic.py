import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "workspace/public/src/scripts/revalidation"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import build_native_init_boot_v2972_nyan_pal8_rle_synthetic as build_v2972


class BuildNativeInitBootV2972NyanPal8RleSynthetic(unittest.TestCase):
    def test_version_axes_are_distinct(self) -> None:
        self.assertEqual(build_v2972.CYCLE, "V2972")
        self.assertEqual(build_v2972.INIT_VERSION, "0.10.58")
        self.assertEqual(build_v2972.INIT_BUILD, "v2972-nyan-pal8-rle-synthetic")
        self.assertTrue(str(build_v2972.BOOT_IMAGE).endswith("boot_linux_v2972_nyan_pal8_rle_synthetic.img"))

    def test_required_markers_capture_nyan_decoder_surface(self) -> None:
        markers = {marker.decode("ascii") for marker in build_v2972.REQUIRED_STRINGS}
        self.assertIn("video.status.version=8", markers)
        self.assertIn("video.status.nyan_pal8_rle=1", markers)
        self.assertIn("A90VSTR2", markers)
        self.assertIn("pal8-rle", markers)
        self.assertIn("DEMO / NYAN CAT", markers)
        self.assertIn("video.stream.error=pal8-rle-layout-unsupported", markers)


if __name__ == "__main__":
    unittest.main()
