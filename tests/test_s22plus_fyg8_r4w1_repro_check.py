import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / (
    "workspace/public/src/scripts/revalidation/"
    "s22plus_fyg8_r4w1_repro_check.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("s22plus_fyg8_r4w1_repro_tested", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class S22PlusFyg8R4W1ReproCheckTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_normalized_config_ignores_only_whitelist_path(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            a = root / "a"
            b = root / "b"
            common = "CONFIG_S22PLUS_FYG8_RETAINED_WITNESS=y\n"
            a.write_text(
                common + 'CONFIG_UNUSED_KSYMS_WHITELIST="/a/list"\n',
                encoding="ascii",
            )
            b.write_text(
                common + 'CONFIG_UNUSED_KSYMS_WHITELIST="/b/list"\n',
                encoding="ascii",
            )
            self.assertEqual(
                self.module.normalized_config(a), self.module.normalized_config(b)
            )

    def test_normalized_config_preserves_security_delta(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            a = root / "a"
            b = root / "b"
            a.write_text("CONFIG_RKP=y\n", encoding="ascii")
            b.write_text("# CONFIG_RKP is not set\n", encoding="ascii")
            self.assertNotEqual(
                self.module.normalized_config(a), self.module.normalized_config(b)
            )

    def test_image_gate_requires_exact_marker_and_size(self):
        with tempfile.TemporaryDirectory() as name:
            image = Path(name) / "Image"
            image.write_bytes(
                self.module.MARKER
                + bytes(self.module.IMAGE_SIZE - len(self.module.MARKER))
            )
            result = self.module.check_image(image)
            self.assertTrue(result["verified"])
            image.write_bytes(image.read_bytes().replace(self.module.MARKER, b"X", 1))
            self.assertFalse(self.module.check_image(image)["verified"])


if __name__ == "__main__":
    unittest.main()
