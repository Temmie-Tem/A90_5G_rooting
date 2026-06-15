"""Host-only tests for the V2413 msm_audio_cal live preflight runner."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import unittest
from pathlib import Path

from _loader import load_revalidation

v2413 = load_revalidation("native_audio_msm_audio_cal_preflight_live_handoff_v2413")


def args(**overrides: object) -> argparse.Namespace:
    defaults: dict[str, object] = {
        "approval": "",
        "bridge_host": "127.0.0.1",
        "bridge_port": 54321,
        "command_timeout": 90.0,
        "dmesg_timeout": 90.0,
        "dmesg_tail_lines": 160,
        "flash_timeout": 420.0,
        "card_timeout": 90.0,
        "poll_interval": 3.0,
        "menu_settle_sec": 1.5,
        "include_open_probe": True,
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


class MsmAudioCalPreflightLiveHandoff(unittest.TestCase):
    def test_dry_run_is_gate_ready_and_device_action_free(self) -> None:
        payload = v2413.dry_run_payload(args())

        self.assertTrue(payload["ok"])
        self.assertEqual(payload["decision"], "v2413-msm-audio-cal-preflight-live-runner-dry-run")
        self.assertEqual(payload["device_action"], "none")
        self.assertTrue(payload["preflight"]["preflight_ok"])
        self.assertTrue(payload["preflight"]["command_safety"]["ok"])
        self.assertIn("rollback to V2321", payload["live_sequence"][-1])

    def test_live_commands_are_open_only_and_cleanup_created_node(self) -> None:
        commands = v2413.live_shell_commands(args())
        safety = v2413.command_safety(commands)
        flattened = "\n".join(" ".join(command["native_command"]) for command in commands)

        self.assertTrue(safety["ok"], safety["findings"])
        names = [command["name"] for command in commands]
        self.assertIn("msm-audio-cal-materialize-if-needed", names)
        self.assertIn("msm-audio-cal-open-only", names)
        self.assertIn("msm-audio-cal-cleanup", names)
        self.assertIn("mknod /dev/msm_audio_cal c 10", flattened)
        self.assertIn("exec 3< \"$node\"", flattened)
        self.assertIn("A90_MSM_AUDIO_CAL_CLEANUP_REMOVED", flattened)
        self.assertNotIn("AUDIO_SET_CALIBRATION", flattened)
        self.assertNotIn(" ioctl", flattened.lower())
        self.assertNotIn("tinymix", flattened)
        self.assertNotIn("tinyplay", flattened)
        self.assertNotIn("magisk", flattened.lower())

    def test_open_probe_disabled_blocks_open_only_unit(self) -> None:
        commands = v2413.live_shell_commands(args(include_open_probe=False))
        safety = v2413.command_safety(commands)

        self.assertNotIn("msm-audio-cal-open-only", [command["name"] for command in commands])
        self.assertFalse(safety["ok"])
        self.assertIn("expected O_RDONLY open-only probe missing", str(safety["findings"]))

    def test_classification_reads_success_markers(self) -> None:
        text = """
A90_MSM_AUDIO_CAL_MISC minor=57
A90_MSM_AUDIO_CAL_MATERIALIZE_OK minor=57 created=1
A90_MSM_AUDIO_CAL_OPEN_OK mode=O_RDONLY
A90_MSM_AUDIO_CAL_CLEANUP_REMOVED created_minor=57
"""
        classification = v2413.classify_msm_audio_cal_text(text)

        self.assertTrue(classification["misc_registered"])
        self.assertTrue(classification["materialized"])
        self.assertTrue(classification["materialized_created"])
        self.assertTrue(classification["opened"])
        self.assertEqual(classification["opened_mode"], "O_RDONLY")
        self.assertTrue(classification["cleanup_removed_created_node"])

    def test_wrong_live_approval_exits_before_device_action(self) -> None:
        script = Path("workspace/public/src/scripts/revalidation/native_audio_msm_audio_cal_preflight_live_handoff_v2413.py")
        completed = subprocess.run(
            [sys.executable, str(script), "--run-live", "--approval", "wrong"],
            cwd=v2413.snd.ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(completed.stdout, "")
        self.assertIn("exact --approval phrase required", completed.stderr)
        self.assertIn(v2413.APPROVAL_PHRASE, completed.stderr)

    def test_cli_dry_run_outputs_json(self) -> None:
        script = Path("workspace/public/src/scripts/revalidation/native_audio_msm_audio_cal_preflight_live_handoff_v2413.py")
        completed = subprocess.run(
            [sys.executable, str(script), "--dry-run"],
            cwd=v2413.snd.ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["decision"], "v2413-msm-audio-cal-preflight-live-runner-dry-run")


if __name__ == "__main__":
    unittest.main()
