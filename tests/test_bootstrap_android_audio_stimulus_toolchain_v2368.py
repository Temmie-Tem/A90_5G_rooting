import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "workspace/public/src/scripts/revalidation/bootstrap_android_audio_stimulus_toolchain_v2368.py"


def load_module():
    spec = importlib.util.spec_from_file_location("bootstrap_v2368", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class BootstrapAndroidAudioStimulusToolchainV2368Test(unittest.TestCase):
    def test_private_paths_and_pinned_packages(self):
        module = load_module()
        self.assertEqual(module.RUN_ID, "V2368")
        self.assertTrue(str(module.ANDROID_SDK).endswith("workspace/private/inputs/android-sdk-v2368"))
        self.assertTrue(str(module.JDK_BASE).endswith("workspace/private/inputs/toolchains/temurin17-v2368"))
        self.assertEqual(module.SDK_PACKAGES, ("platforms;android-31", "build-tools;35.0.0"))
        self.assertIn("dl.google.com/android/repository/commandlinetools-linux-", module.CMDLINE_TOOLS_URL)
        self.assertIn("adoptium/temurin17-binaries", module.JDK_URL)

    def test_archive_name_ignores_query(self):
        module = load_module()
        self.assertEqual(module.archive_name("https://example.invalid/a/b.zip?x=1"), "b.zip")

    def test_status_shape_without_private_toolchain(self):
        module = load_module()
        state = module.status()
        self.assertEqual(state["run_id"], "V2368")
        self.assertIn("ready", state)
        self.assertIn("android_jar_exists", state)
        self.assertIn("d8_exists", state)


if __name__ == "__main__":
    unittest.main()
