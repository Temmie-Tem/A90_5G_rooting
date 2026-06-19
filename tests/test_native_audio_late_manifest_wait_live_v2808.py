from pathlib import Path
import argparse
import importlib
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "workspace/public/src/scripts/revalidation"
SCRIPT = SCRIPT_DIR / "native_audio_late_manifest_wait_live_handoff_v2808.py"


class NativeAudioLateManifestWaitLiveV2808Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sys.path.insert(0, str(SCRIPT_DIR))
        cls.module = importlib.import_module("native_audio_late_manifest_wait_live_handoff_v2808")

    def test_runner_uses_v2807_candidate_and_default_runtime_manifest(self) -> None:
        module = self.module
        self.assertEqual(module.CYCLE, "V2808")
        self.assertEqual(module.CANDIDATE_VERSION, "0.9.315")
        self.assertEqual(module.CANDIDATE_TAG, "v2807-audio-late-manifest-wait")
        self.assertEqual(
            module.DEFAULT_REMOTE_MANIFEST,
            "/cache/a90-runtime/pkg/manifests/audio-setcal-internal-speaker-safe.manifest",
        )
        self.assertEqual(
            module.DEFAULT_REMOTE_ROOT,
            "/cache/a90-runtime/pkg/audio/setcal/internal-speaker-safe",
        )

    def test_play_command_starts_before_manifest_exists(self) -> None:
        command = self.module.play_command(
            argparse.Namespace(play_mode="listen", duration_ms=8000, amplitude_milli=150)
        )
        self.assertEqual(command[:3], ["audio", "play", "internal-speaker-safe"])
        self.assertIn("--execute", command)
        self.assertNotIn("--manifest", command)

    def test_deploy_plan_paths_remap_from_legacy_cache_to_default_runtime(self) -> None:
        module = self.module
        self.assertEqual(
            module.remap_remote_path("/cache/a90-acdb-setcal-replay-v2725/cal-39.arg.bin"),
            "/cache/a90-runtime/pkg/audio/setcal/internal-speaker-safe/cal-39.arg.bin",
        )
        plan = {
            "files": [{"remote_path": "/cache/a90-acdb-setcal-replay-v2725/a.bin"}],
            "replay_entries": [
                {
                    "arg_remote": "/cache/a90-acdb-setcal-replay-v2725/arg.bin",
                    "payload_remote": "/cache/a90-acdb-setcal-replay-v2725/payload.bin",
                }
            ],
        }
        remapped = module.remap_deploy_plan_to_default_runtime(plan)
        self.assertEqual(remapped["remote_dir"], module.DEFAULT_REMOTE_ROOT)
        self.assertEqual(remapped["remote_native_manifest"], module.DEFAULT_REMOTE_MANIFEST)
        self.assertEqual(
            remapped["files"][0]["remote_path"],
            "/cache/a90-runtime/pkg/audio/setcal/internal-speaker-safe/a.bin",
        )
        self.assertEqual(
            remapped["replay_entries"][0]["arg_remote"],
            "/cache/a90-runtime/pkg/audio/setcal/internal-speaker-safe/arg.bin",
        )
        self.assertEqual(
            remapped["replay_entries"][0]["payload_remote"],
            "/cache/a90-runtime/pkg/audio/setcal/internal-speaker-safe/payload.bin",
        )

    def test_runner_requires_manifest_wait_markers_for_pass(self) -> None:
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("manifest_wait_started", text)
        self.assertIn("manifest_ready", text)
        self.assertIn("audio.play.worker.manifest_wait_started=1", text)
        self.assertIn("audio.play.worker.manifest_ready=1", text)


if __name__ == "__main__":
    unittest.main()
