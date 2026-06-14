"""Host-only tests for the V2399 Android ACDB capture analyzer."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _loader import load_revalidation


v2399 = load_revalidation("analyze_audio_acdb_android_measurement_v2399")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def make_run(
    root: Path,
    *,
    result_ok: bool = True,
    rolled_back: bool = True,
    stimulus_ok: bool = True,
    calibration: bool = True,
    app_type: bool = True,
    hal: bool = True,
    nested_artifacts: bool = True,
) -> Path:
    run_dir = root / "v2397-android-acdb-measurement-test"
    artifact_dir = run_dir / "device-artifacts"
    if nested_artifacts:
        artifact_dir = artifact_dir / "a90-audio-acdb-v2396"
    artifact_dir.mkdir(parents=True)
    write(
        run_dir / "result.json",
        json.dumps({
            "run_id": "V2397",
            "build_tag": "v2397-audio-acdb-android-magisk-live",
            "decision": "v2397-android-acdb-measurement-captured-rollback-pass",
            "ok": result_ok,
            "rolled_back": rolled_back,
            "approval_ok": True,
        }),
    )
    logcat = "\n".join([
        "A90_AUDIO_STIMULUS_BEGIN",
        "AudioFlinger AudioTrack active speaker",
        "audio_hw_primary: platform_send_audio_calibration app_type=69941" if app_type else "audio_hw_primary active",
        "ACDB acdb_loader_send_audio_cal_v5 /dev/msm_audio_cal" if calibration else "audio framework active",
        "A90_AUDIO_STIMULUS_END" if stimulus_ok else "A90_AUDIO_STIMULUS_ERROR",
        "A90_AUDIO_STIMULUS_FINISH" if stimulus_ok else "",
    ])
    write(run_dir / "stimulus-logcat.stdout.txt", logcat)

    for phase in ("baseline", "active", "post"):
        write(artifact_dir / f"{phase}-meta.txt", f"phase={phase}\n")
        write(artifact_dir / f"{phase}-getprop-audio.txt", "[vendor.audio.test]: [1]\n")
        write(artifact_dir / f"{phase}-ps.txt", "audio 123 android.hardware.audio.service\n")
        write(artifact_dir / f"{phase}-audio-hal-pids.txt", "123\n")
        maps = ""
        if hal:
            maps = "/vendor/lib/hw/audio.primary.msmnile.so\n/vendor/lib/libacdbloader.so\n/vendor/lib/libtinyalsa.so\n"
        write(artifact_dir / f"{phase}-audio-hal-123-maps.txt", maps)
        write(artifact_dir / f"{phase}-audio-hal-123-fd.txt", "/dev/msm_audio_cal\n/dev/snd/controlC0\n")
        write(artifact_dir / f"{phase}-devnodes.txt", "crw------- /dev/msm_audio_cal\ndrwxr-xr-x /dev/snd\n")
        write(artifact_dir / f"{phase}-proc-asound.txt", " 0 [tavil]: sm8150-tavil-snd-card\n")
        app_line = "3345 INT 4 Audio Stream 0 App Type Cfg  69941 15 48000 2\n" if app_type else ""
        write(artifact_dir / f"{phase}-tinymix-all-values.txt", app_line + "453 BOOL 2 SLIMBUS_0_RX Audio Mixer MultiMedia1  On Off\n")
        dmesg = ""
        if calibration:
            dmesg = "send_afe_cal_type cal_block found\nq6asm_send_cal ok\nadm_open returned ADSP_EOK\n"
        write(artifact_dir / f"{phase}-dmesg-tail.txt", dmesg)
    return run_dir


class AnalyzeAudioAcdbAndroidMeasurement(unittest.TestCase):
    def test_positive_capture_is_bounded_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = make_run(Path(temp))
            payload = v2399.analyze_run(run_dir)

        self.assertEqual(payload["decision"], "bounded-native-acdb-candidate")
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["stimulus"]["ok"])
        self.assertGreater(payload["marker_counts"]["calibration"]["ACDB"], 0)
        self.assertGreater(payload["marker_counts"]["calibration"]["send_afe_cal"], 0)
        self.assertTrue(payload["app_type_lines"]["active"])
        self.assertIn("bounded native ACDB", payload["next_action"])

    def test_missing_artifacts_are_capture_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp) / "v2397-android-acdb-measurement-empty"
            run_dir.mkdir()
            payload = v2399.analyze_run(run_dir)

        self.assertEqual(payload["decision"], "capture-incomplete")
        self.assertFalse(payload["ok"])
        self.assertIn("result.json", payload["missing_requirements"])
        self.assertIn("stimulus-logcat.stdout.txt", payload["missing_requirements"])

    def test_complete_capture_without_calibration_is_negative(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = make_run(Path(temp), calibration=False, app_type=False, hal=False)
            payload = v2399.analyze_run(run_dir)

        self.assertEqual(payload["decision"], "negative-no-calibration")
        self.assertTrue(payload["ok"])
        self.assertIn("no App Type or calibration sequence markers", " ".join(payload["reasons"]))

    def test_hal_markers_without_bounded_sequence_are_opaque(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = make_run(Path(temp), calibration=False, app_type=True, hal=True)
            payload = v2399.analyze_run(run_dir)

        self.assertEqual(payload["decision"], "hal-dependent-or-opaque")
        self.assertTrue(payload["ok"])
        self.assertGreater(payload["marker_counts"]["hal"]["audio_primary"], 0)
        self.assertIn("HAL", " ".join(payload["reasons"]))

    def test_cli_outputs_json_for_positive_capture(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = make_run(Path(temp))
            completed = subprocess.run(
                [
                    sys.executable,
                    "workspace/public/src/scripts/revalidation/analyze_audio_acdb_android_measurement_v2399.py",
                    "--run-dir",
                    str(run_dir),
                ],
                cwd=v2399.ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["run_id"], "V2399")
        self.assertEqual(payload["decision"], "bounded-native-acdb-candidate")
        self.assertEqual(payload["device_action"], "none")


if __name__ == "__main__":
    unittest.main()
