"""Regression tests for the shared a90_transport helpers."""

import os
import unittest
from unittest import mock

from _loader import load_revalidation

transport = load_revalidation("a90_transport")
a90ctl = transport.a90ctl


def command_result(stdout="", stderr="", *, ok=False, rc=1):
    return {
        "command": ["cmdv1", "status"],
        "started": "start",
        "ended": "end",
        "elapsed_sec": 0.1,
        "timeout": False,
        "rc": rc,
        "ok": ok,
        "stdout": stdout,
        "stderr": stderr,
    }


class PhaseAndCommandHelpers(unittest.TestCase):
    def test_phase_records_success_and_failure_with_contract(self):
        success = {}
        with transport.phase(success, "unit"):
            success["inside"] = True

        self.assertEqual(success["phase_timer_contract"], transport.PHASE_TIMER_CONTRACT)
        self.assertEqual(success["phase_timers"][0]["name"], "unit")
        self.assertTrue(success["phase_timers"][0]["ok"])
        self.assertIn("elapsed_sec", success["phase_timers"][0])

        failed = {}
        with self.assertRaises(RuntimeError):
            with transport.phase(failed, "boom"):
                raise RuntimeError("x")
        self.assertFalse(failed["phase_timers"][0]["ok"])
        self.assertEqual(failed["phase_timers"][0]["error_type"], "RuntimeError")

    def test_add_total_phase_and_residual_state_stamp_contracts(self):
        manifest = {}
        with mock.patch.object(transport, "elapsed_sec", return_value=1.234):
            transport.add_total_phase(manifest, "total", 10.0, ok=True)
        transport.set_residual_state(manifest, {"cleanup_required": False})

        self.assertEqual(manifest["phase_timer_contract"], transport.PHASE_TIMER_CONTRACT)
        self.assertEqual(manifest["phase_timers"], [{"name": "total", "elapsed_sec": 1.234, "ok": True}])
        self.assertEqual(manifest["residual_state_contract"], transport.RESIDUAL_STATE_CONTRACT)
        self.assertEqual(manifest["residual_state"], {"cleanup_required": False})

    def test_parse_json_stdout_accepts_only_dict_payloads(self):
        self.assertEqual(transport.parse_json_stdout({"stdout": '{"ok": true}'}), {"ok": True})
        self.assertEqual(transport.parse_json_stdout({"stdout": '[1, 2]'}), {})
        self.assertEqual(transport.parse_json_stdout({"stdout": 'not json'}), {})

    def test_bridge_command_includes_contract_args_and_extra_flags(self):
        command = transport.bridge_command(
            "status",
            host="::1",
            port=1234,
            device="/dev/ttyX",
            device_glob="/dev/serial/*",
            no_client_probe=False,
            extra=["--verbose"],
        )

        self.assertEqual(command[:3], ["python3", transport.BRIDGE_SCRIPT_REL, "status"])
        self.assertIn("::1", command)
        self.assertIn(1234, command)
        self.assertIn("/dev/ttyX", command)
        self.assertIn("/dev/serial/*", command)
        self.assertIn("--json", command)
        self.assertNotIn("--no-client-probe", command)
        self.assertEqual(command[-1], "--verbose")

    def test_protocol_result_to_command_result_preserves_protocol_metadata(self):
        proto = a90ctl.ProtocolResult(
            begin={"cmd": "status"},
            end={"rc": "0", "status": "ok"},
            text="payload",
        )

        result = transport.protocol_result_to_command_result(["status"], "start", 0.2, proto)

        self.assertEqual(result["command"], ["cmdv1", "status"])
        self.assertTrue(result["ok"])
        self.assertEqual(result["rc"], 0)
        self.assertEqual(result["stdout"], "payload")
        self.assertEqual(result["protocol"], {"begin": {"cmd": "status"}, "end": {"rc": "0", "status": "ok"}, "status": "ok"})


class SerialRecoveryHelpers(unittest.TestCase):
    def test_serial_need_detectors_and_retry_policy(self):
        self.assertTrue(transport.serial_needs_hide_on_busy(command_result(stderr="device [busy]")))
        self.assertTrue(transport.serial_needs_hide_on_protocol_noise(command_result(stderr="A90P1 END marker not found")))
        self.assertTrue(transport.serial_needs_bridge_ensure_on_missing(command_result(stderr=a90ctl.BRIDGE_SERIAL_MISSING_TEXT)))
        self.assertTrue(transport.serial_command_can_recover(["status"], retry_unsafe=False))
        with mock.patch.object(a90ctl, "command_allows_retry", return_value=False):
            self.assertFalse(transport.serial_command_can_recover(["wifi", "connect"], retry_unsafe=False))
            self.assertTrue(transport.serial_command_can_recover(["wifi", "connect"], retry_unsafe=True))

    def test_recovered_serial_busy_hides_but_skips_unsafe_retry(self):
        busy = command_result(stderr="[busy]", ok=False)
        hide = command_result(stdout="hidden", ok=True, rc=0)
        with mock.patch.object(a90ctl, "command_allows_retry", return_value=False), \
             mock.patch.object(transport, "run_serial_command", side_effect=[busy, hide]) as run_serial:
            result = transport.run_serial_command_recovered(["wifi", "connect"], retry_unsafe=False)

        self.assertIs(result, busy)
        self.assertEqual(result["serial_recovery"]["reason"], "busy")
        self.assertEqual(result["serial_recovery"]["actions"], ["hide"])
        self.assertEqual(result["serial_recovery"]["skip_reason"], "unsafe-retry-not-allowed")
        self.assertEqual(run_serial.call_count, 2)

    def test_recovered_serial_protocol_noise_restarts_bridge_and_retries(self):
        noise = command_result(stderr="A90P1 command mismatch", ok=False)
        retried = command_result(stdout="ok", ok=True, rc=0)
        with mock.patch.object(transport, "run_serial_command", side_effect=[noise, retried]), \
             mock.patch.object(transport, "restart_bridge", return_value=command_result(stdout="restarted", ok=True, rc=0)) as restart:
            result = transport.run_serial_command_recovered(["status"], retry_unsafe=False)

        self.assertIs(result, retried)
        self.assertTrue(result["serial_recovery"]["recovered"])
        self.assertEqual(result["serial_recovery"]["actions"], ["bridge-restart", "retry-command"])
        restart.assert_called_once()


class NcmAndSelectionHelpers(unittest.TestCase):
    def test_parse_key_values_skips_bracket_lines_and_uses_last_value(self):
        parsed = transport.parse_key_values("[info]\ntransport.contract=1\ntransport.tcpctl=stale\ntransport.tcpctl=ready\nno equals\n")

        self.assertEqual(parsed, {"transport.contract": "1", "transport.tcpctl": "ready"})

    def test_summarize_host_ncm_classifies_ready_present_and_absent(self):
        snapshot = [{"ifname": "ncm0"}]
        with mock.patch.object(transport.ncm, "host_netdev_snapshot", return_value=snapshot), \
             mock.patch.object(transport.ncm, "host_ncm_candidates", side_effect=[[{"ifname": "ncm0", "ll": "fe80::1"}], [{"ifname": "ncm0"}]]):
            ready = transport.summarize_host_ncm()
        with mock.patch.object(transport.ncm, "host_netdev_snapshot", return_value=snapshot), \
             mock.patch.object(transport.ncm, "host_ncm_candidates", side_effect=[[], [{"ifname": "ncm0"}]]):
            present = transport.summarize_host_ncm()
        with mock.patch.object(transport.ncm, "host_netdev_snapshot", return_value=[]), \
             mock.patch.object(transport.ncm, "host_ncm_candidates", side_effect=[[], []]):
            absent = transport.summarize_host_ncm()

        self.assertEqual(ready["state"], "ready")
        self.assertEqual(present["state"], "present-no-link-local")
        self.assertEqual(absent["state"], "not-ready")

    def test_auto_repair_env_and_compact_repair_redact_large_payload(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertTrue(transport.auto_repair_enabled(default=True))
            self.assertFalse(transport.auto_repair_enabled(default=False))
        with mock.patch.dict(os.environ, {transport.NCM_AUTO_REPAIR_ENV: "off"}):
            self.assertFalse(transport.auto_repair_enabled(default=True))
        with mock.patch.dict(os.environ, {transport.NCM_AUTO_REPAIR_ENV: "yes"}):
            self.assertTrue(transport.auto_repair_enabled(default=False))

        compact = transport.compact_ncm_repair({
            "ok": True,
            "reason": "fixed",
            "trigger_reason": "missing-link-local",
            "profile": "a90",
            "ifname": "ncm0",
            "host_link_local": "fe80::1",
            "commands": [
                {"command": ["nmcli", "up"], "rc": 0, "ok": True, "stdout": "large"},
                "ignored",
            ],
            "snapshot": ["large"],
        })

        self.assertEqual(compact["commands"], [{"command": ["nmcli", "up"], "rc": 0, "ok": True}])
        self.assertNotIn("snapshot", compact)
        self.assertIsNone(transport.compact_ncm_repair(None))

    def test_maybe_repair_host_ncm_runs_only_for_present_without_linklocal(self):
        not_ready = {"state": "not-ready"}
        skipped, repair = transport.maybe_repair_host_ncm(None, None, not_ready, enabled=True)
        self.assertIs(skipped, not_ready)
        self.assertIsNone(repair)

        before = {"state": "present-no-link-local", "snapshot": [{"ifname": "ncm0"}]}
        after = {"state": "ready", "ready_candidates": [], "present_candidates": [], "snapshot": []}
        repair_payload = {"ok": True, "commands": []}
        with mock.patch.object(transport.ncm, "host_linklocal_repair_nmcli", return_value=repair_payload) as repair_fn, \
             mock.patch.object(transport, "summarize_host_ncm", return_value=after):
            repaired, repair = transport.maybe_repair_host_ncm(None, None, before, enabled=True)

        self.assertIs(repaired, after)
        self.assertIs(repair, repair_payload)
        repair_fn.assert_called_once()

    def test_select_transport_prefers_tcpctl_then_ncm_then_serial(self):
        bridge = {"ok": True, "json": {"bridge_process": "running", "wrapper_contract": 2}}
        version = command_result(stdout="version", ok=True, rc=0)
        tcp_status = command_result(stdout="transport.contract=1\ntransport.tcpctl=ready\n", ok=True, rc=0)
        ncm_status = command_result(stdout="transport.contract=1\ntransport.tcpctl=not-ready\n", ok=True, rc=0)
        dead_status = command_result(stdout="", ok=False, rc=1)
        ready_ncm = {"state": "ready", "ready_candidates": [{"ifname": "ncm0"}], "present_candidates": [{"ifname": "ncm0"}]}
        absent_ncm = {"state": "not-ready", "ready_candidates": [], "present_candidates": []}

        with mock.patch.object(transport, "ensure_bridge", return_value=bridge), \
             mock.patch.object(transport, "run_serial_command_recovered", side_effect=[version, tcp_status]), \
             mock.patch.object(transport, "summarize_host_ncm", return_value=ready_ncm), \
             mock.patch.object(transport, "maybe_repair_host_ncm", side_effect=lambda _store, _steps, host_ncm, enabled: (host_ncm, None)):
            tcp = transport.select_transport(auto_repair_ncm=False)
        with mock.patch.object(transport, "ensure_bridge", return_value=bridge), \
             mock.patch.object(transport, "run_serial_command_recovered", side_effect=[version, ncm_status]), \
             mock.patch.object(transport, "summarize_host_ncm", return_value=ready_ncm), \
             mock.patch.object(transport, "maybe_repair_host_ncm", side_effect=lambda _store, _steps, host_ncm, enabled: (host_ncm, None)):
            ncm_selected = transport.select_transport(auto_repair_ncm=False)
        with mock.patch.object(transport, "ensure_bridge", return_value=bridge), \
             mock.patch.object(transport, "run_serial_command_recovered", side_effect=[version, dead_status]), \
             mock.patch.object(transport, "summarize_host_ncm", return_value=absent_ncm), \
             mock.patch.object(transport, "maybe_repair_host_ncm", side_effect=lambda _store, _steps, host_ncm, enabled: (host_ncm, None)):
            serial = transport.select_transport(auto_repair_ncm=False)

        self.assertEqual(tcp["selected"], "tcpctl")
        self.assertEqual(tcp["transport_contract"], 1)
        self.assertEqual(ncm_selected["selected"], "ncm")
        self.assertIsNone(ncm_selected["fallback_reason"])
        self.assertEqual(serial["selected"], "serial")
        self.assertEqual(serial["fallback_reason"], "device-status-not-ready")
        self.assertFalse(serial["status_ok"])


if __name__ == "__main__":
    unittest.main()
