from __future__ import annotations

import importlib
import json
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from _loader import load_harness


broker_stub = types.ModuleType("a90_broker")
broker_stub.PROTO = "A90B1"
broker_stub.connect_and_call = lambda *_args, **_kwargs: {}
sys.modules.setdefault("a90_broker", broker_stub)

load_harness("module")
kselftest = importlib.import_module("a90harness.modules.kselftest_feasibility")


class FakeStore:
    def __init__(self, run_dir: Path) -> None:
        self.run_dir = run_dir
        self.text: dict[str, str] = {}

    def write_text(self, rel: str, text: str) -> Path:
        self.text[rel] = text
        path = self.run_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path


def build_ctx(tmp: str, *, timeout: float = 10.0):
    root = Path(tmp)
    store = FakeStore(root)
    module_dir = root / "modules" / kselftest.KselftestFeasibilityModule.name
    module_dir.mkdir(parents=True, exist_ok=True)
    return SimpleNamespace(
        repo_root=Path("/repo"),
        store=store,
        module_dir=module_dir,
        host="127.0.0.1",
        port=54321,
        timeout=timeout,
        expect_version="A90 Linux init 0.9.268",
    )


def completed(returncode: int, stdout: str) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(["cmd"], returncode, stdout=stdout)


def write_report(ctx, payload: dict[str, object]) -> Path:
    path = ctx.module_dir / "kselftest-feasibility-report.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def passing_payload() -> dict[str, object]:
    return {
        "pass": True,
        "version_matches": True,
        "mutation_performed": False,
        "failed_mandatory_count": 0,
        "classification": {
            "safe_candidates": ["timers/nsleep-lat"],
            "blocked": ["net/fib_tests"],
        },
    }


class RunPhase(unittest.TestCase):
    def test_run_builds_read_only_feasibility_command_and_records_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ctx = build_ctx(tmp, timeout=9.0)
            module = kselftest.KselftestFeasibilityModule()

            with mock.patch.object(kselftest.subprocess, "run", return_value=completed(0, "feasible")) as run:
                result = module.run(ctx)

        self.assertTrue(result.ok)
        self.assertEqual(result.detail, "rc=0")
        command = run.call_args.args[0]
        self.assertEqual(command[:2], [
            sys.executable,
            "/repo/workspace/public/src/scripts/revalidation/kselftest_feasibility.py",
        ])
        self.assertEqual(command[command.index("--host") + 1], "127.0.0.1")
        self.assertEqual(command[command.index("--port") + 1], "54321")
        self.assertEqual(command[command.index("--timeout-scale") + 1], "1")
        self.assertEqual(command[command.index("--expect-version") + 1], "A90 Linux init 0.9.268")
        self.assertEqual(command[command.index("--bundle-dir") + 1], str(ctx.module_dir))
        self.assertEqual(run.call_args.kwargs["timeout"], 120.0)
        self.assertIn("feasible", ctx.store.text["modules/kselftest-feasibility/wrapper-output.txt"])

    def test_run_scales_timeout_and_reports_nonzero_rc(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ctx = build_ctx(tmp, timeout=15.0)
            module = kselftest.KselftestFeasibilityModule()

            with mock.patch.object(kselftest.subprocess, "run", return_value=completed(9, "failed")) as run:
                result = module.run(ctx)

        self.assertFalse(result.ok)
        self.assertEqual(result.detail, "rc=9")
        self.assertEqual(run.call_args.kwargs["timeout"], 180.0)


class VerifyPhase(unittest.TestCase):
    def test_verify_fails_when_report_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ctx = build_ctx(tmp)
            result = kselftest.KselftestFeasibilityModule().verify(ctx)

        self.assertFalse(result.ok)
        self.assertIn("missing", result.detail)

    def test_verify_accepts_report_only_when_all_safety_checks_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ctx = build_ctx(tmp)
            write_report(ctx, passing_payload())

            result = kselftest.KselftestFeasibilityModule().verify(ctx)

        self.assertTrue(result.ok)
        self.assertIn("pass=True", result.detail)
        self.assertIn("version_matches=True", result.detail)
        self.assertIn("no_mutation=True", result.detail)
        self.assertIn("failed_mandatory_count=True", result.detail)
        self.assertIn("safe_candidates=True", result.detail)
        self.assertIn("blocked=True", result.detail)

    def test_verify_rejects_mutation_or_missing_classification_dimensions(self) -> None:
        cases = [
            ("mutation_performed", True, "no_mutation=False"),
            ("safe_candidates", [], "safe_candidates=False"),
            ("blocked", [], "blocked=False"),
        ]
        for key, value, detail in cases:
            with self.subTest(key=key):
                with tempfile.TemporaryDirectory() as tmp:
                    ctx = build_ctx(tmp)
                    payload = passing_payload()
                    if key in {"safe_candidates", "blocked"}:
                        classification = dict(payload["classification"])  # type: ignore[index]
                        classification[key] = value
                        payload["classification"] = classification
                    else:
                        payload[key] = value
                    write_report(ctx, payload)

                    result = kselftest.KselftestFeasibilityModule().verify(ctx)

                self.assertFalse(result.ok)
                self.assertIn(detail, result.detail)


if __name__ == "__main__":
    unittest.main()
