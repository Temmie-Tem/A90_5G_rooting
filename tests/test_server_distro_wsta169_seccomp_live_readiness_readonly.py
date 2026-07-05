from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _loader import load_script


runner = load_script(
    "workspace/public/src/scripts/server-distro/run_wsta169_seccomp_live_readiness_readonly.py"
)


class ServerDistroWsta169SeccompLiveReadinessReadonlyTests(unittest.TestCase):
    def private_tmp(self):
        runner.DEFAULT_RUN_BASE.mkdir(parents=True, exist_ok=True)
        return tempfile.TemporaryDirectory(dir=runner.DEFAULT_RUN_BASE)

    def write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def write_wsta168_command(self, root: Path, *, correct_token: bool = False) -> tuple[Path, Path]:
        command = [
            "python3",
            "workspace/public/src/scripts/server-distro/run_wsta167_seccomp_live_observation.py",
            "--run-id",
            "wsta168-seccomp-live-observation-execute",
            "--run-dir",
            str(root / "wsta167-live-run"),
            "--execute-seccomp-live-observation",
            "--allow-seccomp-live-observation",
            "--ack-no-correct-wsta161-token",
            "--ack-no-seccomp-load",
            "--ack-cleanup-required",
        ]
        payload = {
            "schema": "a90-wsta168-seccomp-live-observation-command-v1",
            "state": "READY_TO_RUN_NOT_EXECUTED",
            "command": command,
            "required_ack_flags": [
                "--execute-seccomp-live-observation",
                "--allow-seccomp-live-observation",
                "--ack-no-correct-wsta161-token",
                "--ack-no-seccomp-load",
                "--ack-cleanup-required",
            ],
            "expected_outcome": {
                "decision": "wsta167-seccomp-live-observation-pass",
                "seccomp_filter_loaded": False,
                "seccomp_enforced": False,
                "correct_wsta161_token_supplied": False,
                "scenario_returncode": 65,
            },
            "executed": False,
            "secret_values_logged": 0,
        }
        command_json = root / "wsta168_live_command.json"
        command_sh = root / "wsta168_live_command.sh"
        self.write_json(command_json, payload)
        script = "#!/bin/sh\nexec " + " ".join(command) + "\n"
        if correct_token:
            script += "WSTA161-EXPLICIT-ALLOW-SECCOMP-LOAD\n"
        command_sh.write_text(script, encoding="utf-8")
        return command_json, command_sh

    def healthy_fake_run_host(self, calls: list[list[str]]):
        def fake_run_host(command: list[str], *, timeout: float) -> dict:
            del timeout
            calls.append(command)
            text = " ".join(str(item) for item in command)
            if "a90_bridge.py" in text:
                return {
                    "command": command,
                    "returncode": 0,
                    "stdout": json.dumps({
                        "bridge_process": "running",
                        "port_listening": True,
                        "bridge_probe": "connected-no-immediate-error",
                        "selected_device": "/dev/serial/by-id/usb-A90-LNX_REDACTED-if00",
                        "selected_realpath": "/dev/ttyACM-test",
                    }),
                    "stderr": "",
                }
            if command[-1] == "version":
                return {
                    "command": command,
                    "returncode": 0,
                    "stdout": "A90 Linux init 0.11.158 (v3402-dpublic-hud-presenter-restart-policy)\n",
                    "stderr": "",
                }
            if command[-1] == "status":
                return {
                    "command": command,
                    "returncode": 0,
                    "stdout": (
                        "selftest: pass=12 warn=1 fail=0\n"
                        "transport.ncm=ready\n"
                        "storage: sd present=yes mounted=yes\n"
                        "runtime: backend=sd\n"
                    ),
                    "stderr": "",
                }
            if command[-1] == "selftest":
                return {
                    "command": command,
                    "returncode": 0,
                    "stdout": "selftest: pass=12 warn=1 fail=0\n",
                    "stderr": "",
                }
            raise AssertionError(f"unexpected command: {command}")

        return fake_run_host

    def run_with_artifacts(self, root: Path, command_json: Path, command_sh: Path) -> dict:
        return runner.run(runner.build_arg_parser().parse_args([
            "--run-dir",
            str(root / "wsta169"),
            "--wsta168-command-json",
            str(command_json),
            "--wsta168-command-sh",
            str(command_sh),
            "--emit-seccomp-live-readiness-readonly",
        ]))

    def test_readiness_passes_with_healthy_status_without_executing_live_command(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            command_json, command_sh = self.write_wsta168_command(root)
            calls: list[list[str]] = []
            old_run_host = runner.run_host
            runner.run_host = self.healthy_fake_run_host(calls)
            try:
                result = self.run_with_artifacts(root, command_json, command_sh)
            finally:
                runner.run_host = old_run_host

            summary = json.loads((root / "wsta169" / runner.SUMMARY_NAME).read_text(encoding="utf-8"))

        self.assertEqual(result["decision"], runner.PASS_DECISION)
        self.assertEqual(summary["decision"], runner.PASS_DECISION)
        self.assertEqual(len(calls), 4)
        self.assertTrue(result["checks"]["command_ready"])
        self.assertTrue(result["checks"]["bridge_ready"])
        self.assertTrue(result["checks"]["status_ok"])
        self.assertTrue(result["checks"]["selftest_fail_zero"])
        self.assertFalse(result["safety"]["live_command_executed"])
        self.assertFalse(result["safety"]["seccomp_filter_loaded"])
        self.assertTrue(all("run_wsta167_seccomp_live_observation.py" not in " ".join(call) for call in calls))

    def test_gate_and_private_artifact_checks_block_before_host_commands(self) -> None:
        def fail_run_host(command: list[str], *, timeout: float) -> dict:
            raise AssertionError(f"host command should not run: {command} {timeout}")

        old_run_host = runner.run_host
        runner.run_host = fail_run_host
        try:
            with self.private_tmp() as tmp:
                root = Path(tmp)
                command_json, command_sh = self.write_wsta168_command(root)
                result = runner.run(runner.build_arg_parser().parse_args([
                    "--run-dir",
                    str(root / "wsta169"),
                    "--wsta168-command-json",
                    str(command_json),
                    "--wsta168-command-sh",
                    str(command_sh),
                ]))
            self.assertEqual(result["decision"], "wsta169-blocked-explicit-gate-required")

            with self.private_tmp() as tmp, tempfile.TemporaryDirectory() as outside:
                root = Path(tmp)
                outside_root = Path(outside)
                command_json, command_sh = self.write_wsta168_command(outside_root)
                result = self.run_with_artifacts(root, command_json, command_sh)
            self.assertEqual(result["decision"], "wsta169-blocked-command-json-nonprivate")
        finally:
            runner.run_host = old_run_host

    def test_bad_command_artifact_blocks_even_when_device_is_ready(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            command_json, command_sh = self.write_wsta168_command(root, correct_token=True)
            calls: list[list[str]] = []
            old_run_host = runner.run_host
            runner.run_host = self.healthy_fake_run_host(calls)
            try:
                result = self.run_with_artifacts(root, command_json, command_sh)
            finally:
                runner.run_host = old_run_host

        self.assertEqual(result["decision"], "wsta169-blocked-readiness-invalid")
        self.assertFalse(result["command_checks"]["correct_token_absent"])
        self.assertEqual(len(calls), 4)

    def test_device_readiness_failure_blocks(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            command_json, command_sh = self.write_wsta168_command(root)
            calls: list[list[str]] = []

            def degraded_run_host(command: list[str], *, timeout: float) -> dict:
                record = self.healthy_fake_run_host(calls)(command, timeout=timeout)
                if command[-1] == "status":
                    record["stdout"] = "selftest: pass=11 warn=1 fail=1\nruntime: backend=sd\n"
                return record

            old_run_host = runner.run_host
            runner.run_host = degraded_run_host
            try:
                result = self.run_with_artifacts(root, command_json, command_sh)
            finally:
                runner.run_host = old_run_host

        self.assertEqual(result["decision"], "wsta169-blocked-readiness-invalid")
        self.assertFalse(result["checks"]["status_ok"])


if __name__ == "__main__":
    unittest.main()
