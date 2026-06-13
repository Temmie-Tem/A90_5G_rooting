from __future__ import annotations

import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from _loader import load_script


if "native_wifi_qcacld_fwclass_clean_recapture_handoff_v2144" not in sys.modules:
    v2144_stub = types.ModuleType("native_wifi_qcacld_fwclass_clean_recapture_handoff_v2144")
    v2144_stub.collect_test_evidence = lambda *_args, **_kwargs: None
    sys.modules["native_wifi_qcacld_fwclass_clean_recapture_handoff_v2144"] = v2144_stub

v725 = load_script("workspace/public/src/scripts/revalidation/a90_v725_fasttransport_baseline_validation.py")


class FakeStore:
    def __init__(self, root: Path) -> None:
        self.run_dir = root
        self.logs: dict[str, str] = {}

    def write_log(self, category: str, name: str, text: str) -> Path:
        path = self.run_dir / category / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        self.logs[f"{category}/{name}"] = text
        return path


class CommandAndStatusHelpers(unittest.TestCase):
    def test_run_command_serializes_command_and_records_timeout_result(self) -> None:
        completed = SimpleNamespace(returncode=7, stdout="out", stderr="err")
        with mock.patch.object(v725.ncm, "now_iso", side_effect=["start", "end"]), \
                mock.patch.object(v725.subprocess, "run", return_value=completed) as run:
            result = v725.run_command(["tool", 123], timeout=2.5)

        run.assert_called_once()
        self.assertEqual(result["command"], ["tool", "123"])
        self.assertEqual(result["started"], "start")
        self.assertEqual(result["ended"], "end")
        self.assertFalse(result["timeout"])
        self.assertEqual(result["rc"], 7)
        self.assertFalse(result["ok"])
        self.assertEqual(result["stdout"], "out")
        self.assertEqual(result["stderr"], "err")

        timeout = subprocess.TimeoutExpired(["slow"], 9, output="partial", stderr="late")
        with mock.patch.object(v725.ncm, "now_iso", side_effect=["s", "e"]), \
                mock.patch.object(v725.subprocess, "run", side_effect=timeout):
            failed = v725.run_command(["slow"], timeout=9)
        self.assertTrue(failed["timeout"])
        self.assertIsNone(failed["rc"])
        self.assertFalse(failed["ok"])
        self.assertEqual(failed["stdout"], "partial")
        self.assertEqual(failed["stderr"], "late")

    def test_status_summary_extracts_required_readiness_flags_and_relevant_lines(self) -> None:
        text = "\n".join([
            "init: A90 Linux init 0.9.244 (v725-fasttransport)",
            "selftest: pass=12 fail=0",
            "exposure: tcpctl=stopped",
            "netservice: ncm=present other=ok",
            "irrelevant secret line",
        ])
        summary = v725.status_summary(text)
        self.assertTrue(summary["version_ok"])
        self.assertTrue(summary["selftest_fail0"])
        self.assertTrue(summary["ncm_present"])
        self.assertTrue(summary["tcpctl_stopped"])
        self.assertIn("init:", summary["raw"])
        self.assertIn("netservice:", summary["raw"])
        self.assertNotIn("irrelevant", summary["raw"])

        missing = v725.status_summary("selftest: fail=1\n")
        self.assertFalse(missing["version_ok"])
        self.assertFalse(missing["selftest_fail0"])
        self.assertFalse(missing["ncm_present"])
        self.assertFalse(missing["tcpctl_stopped"])

    def test_candidate_brief_keeps_public_ncm_identity_fields_only(self) -> None:
        brief = v725.candidate_brief([
            {
                "ifname": "enx0",
                "ifindex": 3,
                "address": "56:6c:b8:d2:17:e9",
                "driver": "cdc_ncm",
                "usb_vendor": "04e8",
                "usb_product": "6861",
                "usb_serial": "redacted",
                "interface_number": "02",
                "link_local": "fe80::1",
                "sysfs_path": "/sys/devices/usb",
                "cdc_ncm": True,
                "private_extra": "drop",
            }
        ])
        self.assertEqual(brief, [{
            "ifname": "enx0",
            "ifindex": 3,
            "address": "56:6c:b8:d2:17:e9",
            "driver": "cdc_ncm",
            "usb_vendor": "04e8",
            "usb_product": "6861",
            "usb_serial": "redacted",
            "interface_number": "02",
            "link_local": "fe80::1",
            "sysfs_path": "/sys/devices/usb",
            "cdc_ncm": True,
        }])


class StepAndSubprocessHelpers(unittest.TestCase):
    def test_write_step_persists_stdout_stderr_and_appends_compact_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = FakeStore(Path(tmp))
            steps: list[dict[str, object]] = []
            v725.write_step(store, steps, "probe", {
                "command": ["cmd"],
                "started": "s",
                "ended": "e",
                "timeout": False,
                "rc": 0,
                "ok": True,
                "stdout": "hello",
                "stderr": "warn",
            })

            self.assertEqual(store.logs["host/probe.stdout.txt"], "hello")
            self.assertEqual(store.logs["host/probe.stderr.txt"], "warn")
            self.assertEqual(steps, [{
                "name": "probe",
                "command": ["cmd"],
                "started": "s",
                "ended": "e",
                "timeout": False,
                "rc": 0,
                "ok": True,
                "stdout_file": "host/probe.stdout.txt",
                "stderr_file": "host/probe.stderr.txt",
            }])

    def test_run_json_subprocess_parses_json_suffix_or_reports_parse_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = FakeStore(Path(tmp))
            steps: list[dict[str, object]] = []
            with mock.patch.object(
                v725,
                "run_command",
                return_value={
                    "command": ["cmd"],
                    "started": "s",
                    "ended": "e",
                    "timeout": False,
                    "rc": 0,
                    "ok": True,
                    "stdout": "prefix\n{\"ok\": true, \"value\": 3}",
                    "stderr": "",
                },
            ):
                parsed = v725.run_json_subprocess(store, steps, "json", ["cmd"], timeout=1.0)
            self.assertEqual(parsed["value"], 3)
            self.assertTrue(parsed["_step_ok"])

            with mock.patch.object(
                v725,
                "run_command",
                return_value={
                    "command": ["cmd"],
                    "started": "s",
                    "ended": "e",
                    "timeout": False,
                    "rc": 0,
                    "ok": False,
                    "stdout": "not-json",
                    "stderr": "",
                },
            ):
                failed = v725.run_json_subprocess(store, steps, "bad", ["cmd"], timeout=1.0)
            self.assertFalse(failed["ok"])
            self.assertTrue(failed["parse_error"])
            self.assertFalse(failed["_step_ok"])

    def test_run_transport_smoke_builds_upload_command_and_passes_extra_args(self) -> None:
        with mock.patch.object(v725, "run_json_subprocess", return_value={"ok": True}) as run_json:
            result = v725.run_transport_smoke(
                mock.Mock(),
                [],
                label="lab",
                sizes_mib="1,32",
                extra_args=["--force-nm-repair"],
                timeout=99,
            )

        self.assertEqual(result, {"ok": True})
        command = run_json.call_args.args[3]
        self.assertEqual(command[:5], [
            "python3",
            "workspace/public/src/scripts/revalidation/a90_ncm_transport_smoke.py",
            "--label",
            "lab",
            "--sizes-mib",
        ])
        self.assertIn("--upload", command)
        self.assertIn("--force-nm-repair", command)
        self.assertEqual(run_json.call_args.kwargs["timeout"], 99)


class BaselineDecisionHelpers(unittest.TestCase):
    def test_run_idempotent_netservice_requires_same_sysfs_and_fast_duration(self) -> None:
        before = [{"sysfs_path": "/sys/a", "ifname": "enx0"}]
        after = [{"sysfs_path": "/sys/a", "ifname": "enx0"}]
        steps: list[dict[str, object]] = []
        with mock.patch.object(v725, "a90_candidates", side_effect=[before, after]), \
                mock.patch.object(v725, "candidate_brief", side_effect=lambda value: value), \
                mock.patch.object(
                    v725,
                    "a90ctl_step",
                    side_effect=[
                        {"ok": True, "stdout": "duration_ms=10\n"},
                        {"ok": True, "stdout": "duration_ms=999\n"},
                    ],
                ), \
                mock.patch.object(v725.ncm, "write_compact_step") as compact:
            result = v725.run_idempotent_netservice(mock.Mock(), steps, count=2)

        self.assertTrue(result["ok"])
        self.assertTrue(result["same_sysfs_path"])
        self.assertEqual(result["durations_ms"], [10, 999])
        compact.assert_called_once()
        self.assertEqual(compact.call_args.args[2], "netservice-idempotent-result")

        with mock.patch.object(v725, "a90_candidates", side_effect=[before, [{"sysfs_path": "/sys/b"}]]), \
                mock.patch.object(v725, "candidate_brief", side_effect=lambda value: value), \
                mock.patch.object(v725, "a90ctl_step", return_value={"ok": True, "stdout": "duration_ms=1001\n"}), \
                mock.patch.object(v725.ncm, "write_compact_step"):
            failed = v725.run_idempotent_netservice(mock.Mock(), [], count=1)
        self.assertFalse(failed["ok"])
        self.assertFalse(failed["same_sysfs_path"])
        self.assertEqual(failed["durations_ms"], [1001])

    def test_run_nm_repair_probe_skips_without_candidate_or_runs_disconnect_smoke(self) -> None:
        with mock.patch.object(v725, "a90_candidates", return_value=[]), \
                mock.patch.object(v725.ncm, "write_compact_step") as compact:
            skipped = v725.run_nm_repair_probe(mock.Mock(), [])
        self.assertFalse(skipped["ok"])
        self.assertEqual(skipped["reason"], "no-a90-ncm-candidate-before-disconnect")
        compact.assert_called_once()

        with mock.patch.object(v725, "a90_candidates", return_value=[{"ifname": "enx0"}]), \
                mock.patch.object(v725, "run_command", return_value={"ok": True, "stdout": "", "stderr": ""}) as run_cmd, \
                mock.patch.object(v725, "write_step") as write_step, \
                mock.patch.object(v725.time, "sleep"), \
                mock.patch.object(v725, "run_transport_smoke", return_value={"ok": True}) as smoke:
            result = v725.run_nm_repair_probe(mock.Mock(), [])

        self.assertTrue(result["ok"])
        self.assertEqual(result["ifname"], "enx0")
        self.assertTrue(result["disconnect_ok"])
        run_cmd.assert_called_once_with(["nmcli", "device", "disconnect", "enx0"], timeout=20)
        write_step.assert_called_once()
        smoke.assert_called_once()

    def test_wait_for_status_returns_ready_summary_or_timeout_result(self) -> None:
        ready_stdout = "\n".join([
            "init: A90 Linux init 0.9.244 (v725-fasttransport)",
            "selftest: fail=0",
            "netservice: ncm=present tcpctl=stopped",
        ])
        with mock.patch.object(v725.time, "monotonic", side_effect=[0.0, 0.1, 0.4]), \
                mock.patch.object(
                    v725.transport,
                    "run_serial_command_recovered",
                    return_value={"ok": True, "stdout": ready_stdout},
                ) as run_serial, \
                mock.patch.object(v725.transport, "write_step") as write_step:
            result = v725.wait_for_status(mock.Mock(), [], timeout_sec=5.0)

        self.assertTrue(result["ok"])
        self.assertEqual(result["attempts"], 1)
        self.assertEqual(result["elapsed_sec"], 0.4)
        self.assertTrue(result["status"]["version_ok"])
        run_serial.assert_called_once()
        write_step.assert_called_once()

        with mock.patch.object(v725.time, "monotonic", side_effect=[0.0, 6.0]):
            timeout = v725.wait_for_status(mock.Mock(), [], timeout_sec=5.0)
        self.assertFalse(timeout["ok"])
        self.assertEqual(timeout["attempts"], 0)
        self.assertEqual(timeout["elapsed_sec"], 5.0)


if __name__ == "__main__":
    unittest.main()
