"""Host-only tests for the V2552 ACDB topology replay ION live handoff."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

from _loader import load_revalidation

v2552 = load_revalidation("native_audio_acdb_topology_replay_live_handoff_v2552")


def args(**overrides: object) -> Namespace:
    root = Path(tempfile.mkdtemp(prefix="a90-v2552-test-"))
    defaults: dict[str, object] = {
        "dry_run": True,
        "run_live": False,
        "approval": "",
        "manifest_path": root / "manifest.json",
        "helper": v2552.planmod.DEFAULT_HELPER,
        "payload": v2552.planmod.v2549.STABLE_PAYLOAD,
        "hold_sec": 10,
        "replay_start_timeout": 45.0,
        "tinyalsa_manifest": v2552.speaker.inv.MANIFEST,
        "pcm_probe_manifest": v2552.speaker.pcm_probe.DEFAULT_MANIFEST,
        "evidence_dir": v2552.speaker.recipe.DEFAULT_EVIDENCE_DIR,
        "bridge_host": "127.0.0.1",
        "bridge_port": 54321,
        "device_ip": "192.168.7.2",
        "host_ip": "192.168.7.1",
        "host_prefix": 24,
        "tcp_port": 2325,
        "command_timeout": 60.0,
        "tcp_timeout": 30.0,
        "device_toolbox": v2552.speaker.DEFAULT_DEVICE_TOOLBOX,
        "device_busybox": v2552.speaker.DEFAULT_DEVICE_BUSYBOX,
        "flash_timeout": 900.0,
        "card_timeout": 70.0,
        "poll_interval": 2.0,
        "menu_settle_sec": 1.0,
        "transfer_port": 18240,
        "transfer_delay": 1.0,
        "transfer_timeout": 120.0,
        "repair_host_ncm": True,
        "ncm_setup_timeout": 120.0,
        "ncm_interface_timeout": 20.0,
        "ncm_setup_sudo": "sudo -n",
        "inventory_transport": "auto",
        "card": 0,
        "route_transport": "serial",
        "mixer_timeout": 45.0,
        "playback_timeout": 25.0,
        "duration_ms": v2552.speaker.DEFAULT_DURATION_MS,
        "amplitude": v2552.speaker.DEFAULT_AMPLITUDE,
    }
    defaults.update(overrides)
    return Namespace(**defaults)


class AcdbTopologyReplayLiveHandoffV2552(unittest.TestCase):
    def test_dry_run_payload_is_ready_and_live_not_run(self) -> None:
        payload = v2552.dry_run_payload(args())
        payload["v2550_plan"] = v2552.planmod.plan(args())

        self.assertTrue(payload["ok"], payload.get("safety"))
        self.assertEqual(payload["decision"], "v2552-acdb-topology-replay-ion-live-handoff-dry-run")
        self.assertEqual(payload["run_id"], "V2552")
        self.assertTrue(payload["live_runner_implemented"])
        self.assertFalse(payload["native_calibration_ioctls_run"])
        self.assertFalse(payload["playback_run"])
        self.assertEqual(payload["inputs"]["route_apply_count"], 13)
        self.assertEqual(payload["inputs"]["route_reset_count"], 12)

    def test_v2550_plan_rewrites_all_runtime_tool_paths_to_v2550_dir(self) -> None:
        payload = v2552.planmod.plan(args())

        self.assertEqual(payload["app_type_command"]["argv"][0], v2552.planmod.REMOTE_TINYMIX)
        self.assertTrue(all(cmd["argv"][0] == v2552.planmod.REMOTE_TINYMIX for cmd in payload["route_apply_commands"]))
        self.assertTrue(all(cmd["argv"][0] == v2552.planmod.REMOTE_TINYMIX for cmd in payload["route_reset_commands"]))
        self.assertEqual(payload["playback_command"]["argv"][0], v2552.planmod.REMOTE_PCM_PROBE)

    def test_cleanup_script_waits_for_deallocate_without_removing_runtime_dir(self) -> None:
        script = v2552.cleanup_script(25)

        self.assertIn("AUDIO_DEALLOCATE_CALIBRATION", script)
        self.assertIn("A90_ACDB_REPLAY_DEALLOCATE_MISSING", script)
        self.assertNotIn(f"rm -rf {v2552.planmod.REMOTE_DIR}", script)
        self.assertNotIn("SECONDS", script)

    def test_runtime_cleanup_script_removes_runtime_dir_after_reset(self) -> None:
        script = v2552.runtime_cleanup_script()

        self.assertIn(f"rm -rf {v2552.planmod.REMOTE_DIR}", script)
        self.assertIn("A90_ACDB_REPLAY_RUNTIME_CLEANUP_DONE", script)

    def test_verify_live_approval_requires_exact_phrase(self) -> None:
        with self.assertRaises(SystemExit):
            v2552.verify_live_approval(args(approval="proceed"))
        v2552.verify_live_approval(args(approval=v2552.APPROVAL_PHRASE))


    def test_selftest_content_retry_helper_is_defined(self) -> None:
        self.assertTrue(callable(v2552.run_selftest_fail0_observation))

    def test_cli_dry_run_outputs_json_and_writes_manifest(self) -> None:
        local_args = args()
        script = Path("workspace/public/src/scripts/revalidation/native_audio_acdb_topology_replay_live_handoff_v2552.py")
        completed = subprocess.run(
            [sys.executable, str(script), "--dry-run", "--manifest-path", str(local_args.manifest_path)],
            cwd=v2552.snd.ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["decision"], "v2552-acdb-topology-replay-ion-live-handoff-dry-run")
        self.assertTrue(payload["ok"])
        self.assertTrue(local_args.manifest_path.exists())


if __name__ == "__main__":
    unittest.main()
