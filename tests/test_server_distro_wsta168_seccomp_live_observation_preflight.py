from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _loader import load_script


runner = load_script("workspace/public/src/scripts/server-distro/run_wsta168_seccomp_live_observation_preflight.py")


class ServerDistroWsta168SeccompLiveObservationPreflightTests(unittest.TestCase):
    def private_tmp(self):
        runner.DEFAULT_RUN_BASE.mkdir(parents=True, exist_ok=True)
        return tempfile.TemporaryDirectory(dir=runner.DEFAULT_RUN_BASE)

    def write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def wsta167_no_live_proof(self) -> dict:
        return {
            "decision": "wsta167-blocked-seccomp-live-observation-required",
            "checks": {
                "contract_valid": True,
                "local_inputs_present": True,
                "explicit_live_gate": False,
            },
            "contract_checks": {
                "schema_ok": True,
                "source_only_state": True,
                "scenario_count_three": True,
                "expected_returncode_65": True,
                "correct_token_false": True,
                "load_expected_false": True,
                "enforcement_expected_false": True,
                "correct_token_literal_absent": True,
                "script_has_remote_done": True,
                "script_has_wrong_token_placeholder": True,
                "script_no_external_network_inputs": True,
                "secret_values_logged_zero": True,
            },
            "safety": {
                "device_action": False,
                "seccomp_filter_loaded": False,
                "seccomp_enforced": False,
                "correct_wsta161_token_supplied": False,
            },
        }

    def test_preflight_emits_ready_command_without_executing(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            proof_path = root / "inputs" / "wsta167_result.json"
            self.write_json(proof_path, self.wsta167_no_live_proof())
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "wsta168"),
                "--wsta167-proof-json",
                str(proof_path),
                "--emit-seccomp-live-preflight",
            ]))
            command_json = json.loads((root / "wsta168" / runner.COMMAND_JSON_NAME).read_text(encoding="utf-8"))
            command_sh = (root / "wsta168" / runner.COMMAND_SH_NAME).read_text(encoding="utf-8")

        self.assertEqual(result["decision"], runner.PASS_DECISION)
        self.assertEqual(command_json["state"], "READY_TO_RUN_NOT_EXECUTED")
        self.assertFalse(command_json["executed"])
        for flag in command_json["required_ack_flags"]:
            self.assertIn(flag, command_json["command"])
            self.assertIn(flag, command_sh)
        self.assertIn("run_wsta167_seccomp_live_observation.py", " ".join(command_json["command"]))
        self.assertNotIn("WSTA161-EXPLICIT-ALLOW-SECCOMP-LOAD", command_sh)
        self.assertFalse(result["safety"]["device_action"])
        self.assertFalse(result["safety"]["live_command_executed"])

    def test_gate_blocks_without_explicit_flag_or_private_proof(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            proof_path = root / "inputs" / "wsta167_result.json"
            self.write_json(proof_path, self.wsta167_no_live_proof())
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "wsta168"),
                "--wsta167-proof-json",
                str(proof_path),
            ]))
        self.assertEqual(result["decision"], "wsta168-blocked-explicit-gate-required")

        with self.private_tmp() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            proof_path = Path(outside) / "wsta167_result.json"
            self.write_json(proof_path, self.wsta167_no_live_proof())
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "wsta168"),
                "--wsta167-proof-json",
                str(proof_path),
                "--emit-seccomp-live-preflight",
            ]))
        self.assertEqual(result["decision"], "wsta168-blocked-wsta167-proof-nonprivate")

    def test_bad_wsta167_proof_blocks_preflight(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            proof = self.wsta167_no_live_proof()
            proof["safety"]["correct_wsta161_token_supplied"] = True
            proof_path = root / "inputs" / "wsta167_result.json"
            self.write_json(proof_path, proof)
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "wsta168"),
                "--wsta167-proof-json",
                str(proof_path),
                "--emit-seccomp-live-preflight",
            ]))
        self.assertEqual(result["decision"], "wsta168-blocked-preflight-invalid")
        self.assertFalse(result["proof_checks"]["correct_token_false"])


if __name__ == "__main__":
    unittest.main()
