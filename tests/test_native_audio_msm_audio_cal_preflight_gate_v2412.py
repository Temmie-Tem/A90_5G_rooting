"""Host-only tests for the V2412 msm_audio_cal preflight gate."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import unittest
from pathlib import Path

from _loader import load_revalidation

v2412 = load_revalidation("native_audio_msm_audio_cal_preflight_gate_v2412")


def args(**overrides: object) -> argparse.Namespace:
    defaults: dict[str, object] = {
        "approval": "",
        "bridge_host": "127.0.0.1",
        "bridge_port": 54321,
        "command_timeout": 90.0,
        "dmesg_timeout": 90.0,
        "dmesg_tail_lines": 160,
        "include_open_probe": True,
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


class MsmAudioCalPreflightGate(unittest.TestCase):
    def test_dry_run_payload_is_host_only_and_gate_ready(self) -> None:
        payload = v2412.dry_run_payload(args())

        self.assertTrue(payload["ok"])
        self.assertEqual(payload["decision"], "v2412-msm-audio-cal-preflight-gate-dry-run")
        self.assertEqual(payload["device_action"], "none")
        self.assertIn("AUD-5C-msm-audio-cal-preflight go:", payload["preflight"]["approval_phrase_required_for_future_live"])
        self.assertTrue(payload["preflight"]["source_report"]["exists"])
        self.assertTrue(payload["preflight"]["command_safety"]["ok"])

    def test_planned_commands_are_open_only_and_do_not_use_calibration_ioctls(self) -> None:
        commands = v2412.planned_cal_preflight_commands(args())
        safety = v2412.command_safety(commands)

        self.assertTrue(safety["ok"], safety["findings"])
        names = [command["name"] for command in commands]
        self.assertIn("msm-audio-cal-materialize-if-needed", names)
        self.assertIn("msm-audio-cal-open-only", names)
        argv_flat = " ".join(" ".join(command["argv"]) for command in commands)
        self.assertIn("/proc/misc", argv_flat)
        self.assertIn("/dev/msm_audio_cal", argv_flat)
        self.assertIn("mknod /dev/msm_audio_cal c 10", argv_flat)
        self.assertIn("exec 3<", argv_flat)
        self.assertIn("exec 3<>", argv_flat)
        self.assertNotIn("AUDIO_SET_CALIBRATION", argv_flat)
        self.assertNotIn(" ioctl", argv_flat.lower())
        self.assertNotIn("tinyplay", argv_flat)
        self.assertNotIn("tinymix", argv_flat)
        self.assertNotIn("su -c", argv_flat)

    def test_open_probe_can_be_disabled_in_plan(self) -> None:
        commands = v2412.planned_cal_preflight_commands(args(include_open_probe=False))

        self.assertNotIn("msm-audio-cal-open-only", [command["name"] for command in commands])
        self.assertTrue(v2412.command_safety(commands)["ok"])

    def test_safety_rejects_real_audio_calibration_ioctl_tokens(self) -> None:
        bad = [{
            "name": "bad-cal-write",
            "argv": ["/bin/sh", "-c", "echo AUDIO_SET_CALIBRATION ioctl"],
        }]

        safety = v2412.command_safety(bad)

        self.assertFalse(safety["ok"])
        self.assertGreaterEqual(len(safety["findings"]), 1)

    def test_magisk_policy_is_measurement_only(self) -> None:
        strategy = v2412.preflight_state(args())["magisk_strategy"]

        self.assertFalse(strategy["native_runtime_dependency"])
        self.assertFalse(strategy["v2412_uses_magisk"])
        self.assertIn("M0 transient", strategy["default"])
        self.assertIn("M1", strategy["m1_temporary_boot_module"])

    def test_wrong_live_approval_exits_before_device_action(self) -> None:
        script = Path("workspace/public/src/scripts/revalidation/native_audio_msm_audio_cal_preflight_gate_v2412.py")
        completed = subprocess.run(
            [sys.executable, str(script), "--run-live", "--approval", "wrong"],
            cwd=v2412.snd.ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("exact --approval phrase required", completed.stderr)
        self.assertIn(v2412.REQUIRED_APPROVAL_PHRASE, completed.stderr)
        self.assertEqual(completed.stdout, "")

    def test_exact_live_approval_is_source_only_placeholder(self) -> None:
        script = Path("workspace/public/src/scripts/revalidation/native_audio_msm_audio_cal_preflight_gate_v2412.py")
        completed = subprocess.run(
            [
                sys.executable,
                str(script),
                "--run-live",
                "--approval",
                v2412.REQUIRED_APPROVAL_PHRASE,
            ],
            cwd=v2412.snd.ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["decision"], "v2412-live-not-executed-source-only-gate-ready")
        self.assertEqual(payload["device_action"], "none")
        self.assertTrue(payload["approval_phrase_matched"])

    def test_cli_dry_run_outputs_json(self) -> None:
        script = Path("workspace/public/src/scripts/revalidation/native_audio_msm_audio_cal_preflight_gate_v2412.py")
        completed = subprocess.run(
            [sys.executable, str(script), "--dry-run"],
            cwd=v2412.snd.ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["decision"], "v2412-msm-audio-cal-preflight-gate-dry-run")


if __name__ == "__main__":
    unittest.main()
