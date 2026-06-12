"""Regression tests for the a90harness.module contract layer."""

import sys
import tempfile
import types
import unittest
from pathlib import Path
from types import SimpleNamespace

from _loader import load_harness

broker_stub = types.ModuleType("a90_broker")
broker_stub.PROTO = "A90B1"
broker_stub.connect_and_call = lambda *_args, **_kwargs: {}
sys.modules.setdefault("a90_broker", broker_stub)

module_contract = load_harness("module")


class ModuleContractTests(unittest.TestCase):
    def test_step_result_to_dict_includes_default_error_and_skipped(self):
        result = module_contract.StepResult("prepare", True, "ok", 1.25)

        self.assertEqual(
            result.to_dict(),
            {
                "name": "prepare",
                "ok": True,
                "detail": "ok",
                "duration_sec": 1.25,
                "error": "",
                "skipped": False,
            },
        )

    def test_module_outcome_to_dict_collects_failed_steps_only(self):
        ok_step = module_contract.StepResult("prepare", True, "ok", 0.1)
        failed_step = module_contract.StepResult(
            "run",
            False,
            "RuntimeError: boom",
            0.2,
            error="RuntimeError: boom",
        )
        outcome = module_contract.ModuleOutcome(
            name="demo",
            ok=False,
            skipped=False,
            steps=[ok_step, failed_step],
            artifacts=["runs/demo/log.txt"],
            metadata={"read_only": True},
        )

        serialized = outcome.to_dict()

        self.assertEqual(serialized["name"], "demo")
        self.assertFalse(serialized["ok"])
        self.assertEqual(serialized["artifacts"], ["runs/demo/log.txt"])
        self.assertEqual(serialized["metadata"], {"read_only": True})
        self.assertEqual(serialized["steps"], [ok_step.to_dict(), failed_step.to_dict()])
        self.assertEqual(serialized["failed_steps"], [failed_step.to_dict()])

    def test_default_test_module_metadata_and_noop_steps(self):
        test_module = module_contract.TestModule()
        ctx = SimpleNamespace()

        self.assertEqual(
            test_module.metadata(),
            {
                "description": "",
                "cycle_label": "v172",
                "read_only": True,
                "destructive": False,
                "requires_ncm": False,
                "requires_usb_rebind": False,
                "operator_confirm_required": False,
                "external_bridge_client": False,
            },
        )
        self.assertEqual(test_module.prepare(ctx).to_dict()["detail"], "no-op")
        self.assertEqual(test_module.cleanup(ctx).to_dict()["detail"], "no-op")
        self.assertEqual(test_module.verify(ctx).to_dict()["detail"], "no-op")
        with self.assertRaises(NotImplementedError):
            test_module.run(ctx)

    def test_subclass_metadata_reflects_gate_flags(self):
        class RiskyModule(module_contract.TestModule):
            description = "risky"
            cycle_label = "vrisk"
            read_only = False
            destructive = True
            requires_ncm = True
            requires_usb_rebind = True
            operator_confirm_required = True
            external_bridge_client = True

        self.assertEqual(
            RiskyModule().metadata(),
            {
                "description": "risky",
                "cycle_label": "vrisk",
                "read_only": False,
                "destructive": True,
                "requires_ncm": True,
                "requires_usb_rebind": True,
                "operator_confirm_required": True,
                "external_bridge_client": True,
            },
        )

    def test_artifacts_return_sorted_paths_relative_to_run_dir(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            run_dir = Path(tmp_dir)
            module_dir = run_dir / "module"
            (module_dir / "nested").mkdir(parents=True)
            (module_dir / "z.txt").write_text("z", encoding="utf-8")
            (module_dir / "nested" / "a.txt").write_text("a", encoding="utf-8")
            (module_dir / "nested" / "ignored-dir").mkdir()
            ctx = SimpleNamespace(
                store=SimpleNamespace(run_dir=run_dir),
                module_dir=module_dir,
            )

            self.assertEqual(
                module_contract.TestModule().artifacts(ctx),
                ["module/nested/a.txt", "module/z.txt"],
            )

    def test_artifacts_return_empty_for_missing_module_dir(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            run_dir = Path(tmp_dir)
            ctx = SimpleNamespace(
                store=SimpleNamespace(run_dir=run_dir),
                module_dir=run_dir / "missing",
            )

            self.assertEqual(module_contract.TestModule().artifacts(ctx), [])

    def test_run_step_sets_elapsed_duration_for_zero_or_negative_duration(self):
        result = module_contract.run_step(
            "run",
            lambda: module_contract.StepResult("actual", True, "ok", 0.0),
        )

        self.assertEqual(result.name, "actual")
        self.assertTrue(result.ok)
        self.assertGreater(result.duration_sec, 0)

    def test_run_step_preserves_positive_duration(self):
        result = module_contract.run_step(
            "run",
            lambda: module_contract.StepResult("actual", True, "ok", 3.5),
        )

        self.assertEqual(result.duration_sec, 3.5)

    def test_run_step_catches_exceptions_as_failed_step(self):
        def fail():
            raise ValueError("bad input")

        result = module_contract.run_step("prepare", fail)

        self.assertFalse(result.ok)
        self.assertEqual(result.name, "prepare")
        self.assertEqual(result.detail, "ValueError: bad input")
        self.assertEqual(result.error, "ValueError: bad input")
        self.assertGreaterEqual(result.duration_sec, 0)
        self.assertFalse(result.skipped)


if __name__ == "__main__":
    unittest.main()
