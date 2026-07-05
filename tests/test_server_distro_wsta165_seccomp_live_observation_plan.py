from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _loader import load_script


runner = load_script("workspace/public/src/scripts/server-distro/run_wsta165_seccomp_live_observation_plan.py")


class ServerDistroWsta165SeccompLiveObservationPlanTests(unittest.TestCase):
    def private_tmp(self):
        runner.DEFAULT_RUN_BASE.mkdir(parents=True, exist_ok=True)
        return tempfile.TemporaryDirectory(dir=runner.DEFAULT_RUN_BASE)

    def write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def wsta164_pass_proof(self) -> dict:
        proof_checks = {
            "no_gate_no_load_attempt": True,
            "missing_token_no_load_attempt": True,
            "wrong_token_no_load_attempt": True,
            "no_gate_blocks_load_gate": True,
            "missing_token_blocks_before_helper": True,
            "wrong_token_blocks_token": True,
        }
        return {
            "decision": runner.wsta164.PASS_DECISION,
            "checks": {
                "launcher_has_wsta164_load_gate": True,
                "launcher_forwards_load_env": True,
                "launcher_does_not_hardcode_wsta161_token": True,
            },
            "proof": {
                "correct_wsta161_token_supplied": False,
                "filter_load_enabled": False,
                "seccomp_enforced": False,
            },
            "proof_checks": proof_checks,
        }

    def test_plan_consumes_wsta164_pass_and_emits_no_load_observation_plan(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            proof_path = root / "inputs" / "wsta164_result.json"
            self.write_json(proof_path, self.wsta164_pass_proof())
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "wsta165"),
                "--wsta164-proof-json",
                str(proof_path),
                "--emit-seccomp-live-observation-plan",
            ]))
            plan_path = root / "wsta165" / runner.PLAN_NAME
            plan = json.loads(plan_path.read_text(encoding="utf-8"))

        self.assertEqual(result["decision"], runner.PASS_DECISION)
        self.assertTrue(result["proof_checks"]["wsta164_decision_pass"])
        self.assertTrue(result["plan_checks"]["three_scenarios"])
        self.assertFalse(result["plan"]["correct_wsta161_token_supplied"])
        self.assertFalse(result["plan"]["seccomp_filter_load_expected"])
        self.assertFalse(result["plan"]["seccomp_enforcement_expected"])
        self.assertEqual([item["name"] for item in plan["scenarios"]], [
            "no-load-env-gate",
            "load-env-gate-missing-token",
            "load-env-gate-wrong-token",
        ])
        serialized = json.dumps(plan, sort_keys=True)
        self.assertIn("intentionally-wrong-token", serialized)
        self.assertIn("A90WSTA161_SECCOMP_LOAD_ATTEMPT=1", serialized)
        self.assertNotIn("WSTA161-EXPLICIT-ALLOW-SECCOMP-LOAD", serialized)

    def test_gate_blocks_without_explicit_flag_or_private_wsta164_proof(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            proof_path = root / "inputs" / "wsta164_result.json"
            self.write_json(proof_path, self.wsta164_pass_proof())
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "wsta165"),
                "--wsta164-proof-json",
                str(proof_path),
            ]))
        self.assertEqual(result["decision"], "wsta165-blocked-explicit-gate-required")

        with self.private_tmp() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            proof_path = Path(outside) / "wsta164_result.json"
            self.write_json(proof_path, self.wsta164_pass_proof())
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "wsta165"),
                "--wsta164-proof-json",
                str(proof_path),
                "--emit-seccomp-live-observation-plan",
            ]))
        self.assertEqual(result["decision"], "wsta165-blocked-wsta164-proof-nonprivate")

    def test_non_pass_wsta164_proof_blocks_plan(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            proof = self.wsta164_pass_proof()
            proof["proof"]["correct_wsta161_token_supplied"] = True
            proof_path = root / "inputs" / "wsta164_result.json"
            self.write_json(proof_path, proof)
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "wsta165"),
                "--wsta164-proof-json",
                str(proof_path),
                "--emit-seccomp-live-observation-plan",
            ]))
        self.assertEqual(result["decision"], "wsta165-blocked-plan-invalid")
        self.assertFalse(result["proof_checks"]["wsta164_correct_token_not_supplied"])


if __name__ == "__main__":
    unittest.main()
