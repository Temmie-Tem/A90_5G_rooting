"""Host-only tests for the V2432 read-only Android/Magisk access probe."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _loader import load_revalidation

v2432 = load_revalidation("native_audio_magisk_readonly_probe_live_handoff_v2432")


def args(**overrides: object) -> argparse.Namespace:
    values: dict[str, object] = {
        "dry_run": True,
        "run_live": False,
        "adb": "adb",
        "serial": None,
        "stimulus_apk": v2432.v2396.DEFAULT_STIMULUS_APK,
        "android_timeout": 420.0,
        "adb_command_timeout": 120.0,
        "flash_timeout": 900.0,
        "duration_ms": v2432.v2396.DEFAULT_DURATION_MS,
        "sample_rate": v2432.v2396.DEFAULT_SAMPLE_RATE,
        "amplitude": v2432.v2396.DEFAULT_AMPLITUDE,
        "active_delay_sec": 0.75,
        "post_delay_sec": 1.0,
        "from_native": True,
        "approval": None,
        "out_dir": None,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


class MagiskReadonlyProbeV2432(unittest.TestCase):
    def test_dry_run_is_read_only_and_targets_mount_master(self) -> None:
        payload = v2432.dry_run(args())

        self.assertEqual(payload["run_id"], "V2432")
        self.assertEqual(payload["decision"], "v2432-magisk-readonly-probe-live-dry-run")
        self.assertTrue(payload["host_only"])
        self.assertEqual(payload["device_action"], "none")
        self.assertEqual(payload["approval_phrase_required_for_live"], v2432.APPROVAL_PHRASE)
        self.assertTrue(payload["command_safety"]["ok"], payload["command_safety"])
        flat = json.dumps(payload["commands"], sort_keys=True)
        self.assertIn("magisk -c", flat)
        self.assertIn("magisk --path", flat)
        self.assertIn("/data/adb/modules", flat)
        self.assertIn("su -mm -c", flat)
        self.assertIn("rollback_v2321", flat)
        self.assertNotIn("--install-module", flat)
        self.assertNotIn("--remove-modules", flat)
        self.assertNotIn("mkdir", flat)
        self.assertNotIn("chmod", flat)
        self.assertNotIn("am start", flat)

    def test_probe_commands_are_check_false_safe_candidates(self) -> None:
        commands = v2432.probe_commands(args())
        self.assertEqual([item["name"] for item in commands], [
            "probe-shell-readonly",
            "probe-su-readonly",
            "probe-su-mount-master-readonly",
        ])
        self.assertEqual(commands[2]["command"][:2], ["adb", "shell"])
        self.assertIn("su -mm -c", commands[2]["command"][2])

    def test_summary_classifies_mount_master_no_denial(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir)
            stdout = out_dir / "probe-su-mount-master-readonly.stdout.txt"
            stdout.write_text(
                "A90_MAGISK_PROBE_BEGIN\n"
                "uid=0(root) gid=0(root) context=u:r:magisk:s0\n"
                "/data/adb/modules\n"
                "/data/adb/magisk\n"
                "A90_MAGISK_PROBE_END\n"
            )
            steps = [{
                "name": "probe-su-mount-master-readonly",
                "ok": True,
                "rc": 0,
                "stdout": str(stdout),
            }]
            summary = v2432.summarize_probe_outputs(out_dir, steps)

        self.assertEqual(summary["classification"], "mount-master-readonly-visible-no-denial")
        self.assertTrue(summary["root_mount_master_supported"])
        self.assertTrue(summary["data_adb_modules_visible"])

    def test_summary_rejects_malformed_su_usage_as_inconclusive(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir)
            stdout = out_dir / "probe-su-mount-master-readonly.stdout.txt"
            stderr = out_dir / "probe-su-mount-master-readonly.stderr.txt"
            stdout.write_text(
                "A90_MAGISK_PROBE_BEGIN\n"
                "uid=2000(shell) gid=2000(shell) context=u:r:shell:s0\n"
                "/data/adb/modules\n"
                "A90_MAGISK_PROBE_END\n"
            )
            stderr.write_text("su: option requires an argument -- c\n\nMagiskSU\n")
            steps = [{
                "name": "probe-su-mount-master-readonly",
                "ok": True,
                "rc": 0,
                "stdout": str(stdout),
                "stderr": str(stderr),
            }]
            summary = v2432.summarize_probe_outputs(out_dir, steps)

        self.assertEqual(summary["classification"], "su-probe-malformed")
        self.assertTrue(summary["su_usage_errors"])
        self.assertFalse(summary["root_mount_master_supported"])

    def test_wrong_live_approval_exits_before_device_action(self) -> None:
        script = Path("workspace/public/src/scripts/revalidation/native_audio_magisk_readonly_probe_live_handoff_v2432.py")
        completed = subprocess.run(
            [sys.executable, str(script), "--run-live", "--approval", "continue"],
            cwd=v2432.ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )

        self.assertNotEqual(completed.returncode, 0)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["decision"], "v2432-magisk-readonly-probe-live-refused")
        self.assertIn("exact AUD-5H", payload["reason"])
        self.assertFalse(payload["rolled_back"])

    def test_cli_dry_run_outputs_json(self) -> None:
        script = Path("workspace/public/src/scripts/revalidation/native_audio_magisk_readonly_probe_live_handoff_v2432.py")
        completed = subprocess.run(
            [sys.executable, str(script), "--dry-run"],
            cwd=v2432.ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["run_id"], "V2432")
        self.assertTrue(payload["ok"])


if __name__ == "__main__":
    unittest.main()
