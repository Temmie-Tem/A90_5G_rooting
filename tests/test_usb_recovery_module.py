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
usb_recovery = importlib.import_module("a90harness.modules.usb_recovery")


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


def build_ctx(tmp: str, *, profile: str = "smoke", timeout: float = 10.0):
    root = Path(tmp)
    store = FakeStore(root)
    module_dir = root / "modules" / usb_recovery.UsbRecoveryModule.name
    module_dir.mkdir(parents=True, exist_ok=True)
    return SimpleNamespace(
        repo_root=Path("/repo"),
        store=store,
        module_dir=module_dir,
        profile=profile,
        host="127.0.0.1",
        port=54321,
        timeout=timeout,
    )


def completed(returncode: int, stdout: str) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(["cmd"], returncode, stdout=stdout)


def write_report(ctx, run_id: str, payload: dict[str, object]) -> Path:
    path = ctx.module_dir / run_id / "usb-recovery-report.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def report_payload(
    *,
    passed: bool = True,
    final_version: bool = True,
    final_selftest: bool = True,
    max_recovery_sec: float = 3.25,
) -> dict[str, object]:
    return {
        "pass": passed,
        "max_recovery_sec": max_recovery_sec,
        "checks": [
            {"name": "final version", "ok": final_version},
            {"name": "final selftest", "ok": final_selftest},
        ],
    }


class MetadataAndRunPhase(unittest.TestCase):
    def test_metadata_declares_usb_rebind_and_operator_confirmation_gate(self) -> None:
        module = usb_recovery.UsbRecoveryModule()

        self.assertEqual(module.name, "usb-recovery")
        self.assertFalse(module.read_only)
        self.assertTrue(module.requires_usb_rebind)
        self.assertTrue(module.operator_confirm_required)
        self.assertEqual(module.cycle_label, "v174")

    def test_run_smoke_builds_one_cycle_usb_recovery_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ctx = build_ctx(tmp, profile="smoke", timeout=5.0)
            module = usb_recovery.UsbRecoveryModule()
            module._run_id = "testrun"

            with mock.patch.object(usb_recovery.subprocess, "run", return_value=completed(0, "usb ok")) as run:
                result = module.run(ctx)

        self.assertTrue(result.ok)
        self.assertEqual(result.detail, "rc=0 cycles=1")
        command = run.call_args.args[0]
        self.assertEqual(command[:2], [
            sys.executable,
            "/repo/workspace/public/src/scripts/revalidation/usb_recovery_validate.py",
        ])
        self.assertEqual(command[command.index("--host") + 1], "127.0.0.1")
        self.assertEqual(command[command.index("--port") + 1], "54321")
        self.assertEqual(command[command.index("--timeout") + 1], "12.0")
        self.assertEqual(command[command.index("--recovery-timeout") + 1], "45")
        self.assertEqual(command[command.index("--cycles") + 1], "1")
        self.assertEqual(command[command.index("--run-id") + 1], "testrun")
        self.assertEqual(command[command.index("--out-dir") + 1], str(ctx.module_dir))
        self.assertEqual(run.call_args.kwargs["timeout"], 300)
        self.assertIn("usb ok", ctx.store.text["modules/usb-recovery/wrapper-output.txt"])

    def test_run_quick_profile_uses_two_cycles_and_reports_nonzero_rc(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ctx = build_ctx(tmp, profile="quick", timeout=44.0)
            module = usb_recovery.UsbRecoveryModule()
            module._run_id = "testrun"

            with mock.patch.object(usb_recovery.subprocess, "run", return_value=completed(5, "failed")) as run:
                result = module.run(ctx)

        self.assertFalse(result.ok)
        self.assertEqual(result.detail, "rc=5 cycles=2")
        command = run.call_args.args[0]
        self.assertEqual(command[command.index("--timeout") + 1], "44.0")
        self.assertEqual(command[command.index("--cycles") + 1], "2")


class VerifyPhase(unittest.TestCase):
    def test_verify_fails_when_report_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ctx = build_ctx(tmp)
            module = usb_recovery.UsbRecoveryModule()
            module._run_id = "testrun"

            result = module.verify(ctx)

        self.assertFalse(result.ok)
        self.assertIn("missing", result.detail)

    def test_verify_accepts_passing_report_with_final_version_and_selftest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ctx = build_ctx(tmp)
            module = usb_recovery.UsbRecoveryModule()
            module._run_id = "testrun"
            write_report(ctx, "testrun", report_payload())

            result = module.verify(ctx)

        self.assertTrue(result.ok)
        self.assertEqual(result.detail, "pass=True max_recovery=3.25")

    def test_verify_rejects_failed_report_or_missing_final_health_checks(self) -> None:
        cases = [
            report_payload(passed=False),
            report_payload(final_version=False),
            report_payload(final_selftest=False),
            {"pass": True, "max_recovery_sec": 7.0, "checks": []},
        ]
        for payload in cases:
            with self.subTest(payload=payload):
                with tempfile.TemporaryDirectory() as tmp:
                    ctx = build_ctx(tmp)
                    module = usb_recovery.UsbRecoveryModule()
                    module._run_id = "testrun"
                    write_report(ctx, "testrun", payload)

                    result = module.verify(ctx)

                self.assertFalse(result.ok)
                self.assertIn("pass=", result.detail)
                self.assertIn("max_recovery=", result.detail)


if __name__ == "__main__":
    unittest.main()
