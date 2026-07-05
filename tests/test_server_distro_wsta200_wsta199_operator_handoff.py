from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _loader import load_script


runner = load_script("workspace/public/src/scripts/server-distro/run_wsta200_wsta199_operator_handoff.py")
SOURCE = Path("workspace/public/src/scripts/server-distro/run_wsta200_wsta199_operator_handoff.py")
TOKEN_LITERAL = "WSTA161-" + "EXPLICIT-ALLOW-SECCOMP-LOAD"


class ServerDistroWsta200Wsta199OperatorHandoffTests(unittest.TestCase):
    def private_tmp(self):
        runner.DEFAULT_RUN_BASE.mkdir(parents=True, exist_ok=True)
        return tempfile.TemporaryDirectory(dir=runner.DEFAULT_RUN_BASE)

    def write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def transport_gate_payload(self, gate_path: Path) -> dict:
        return {
            "schema": "a90-wsta197-seccomp-load-canary-transport-gate-v1",
            "state": "TRANSPORT_DECIDED_WSTA196_LIVE_BLOCKED_UNTIL_ADAPTER",
            "selected_transport": runner.wsta198.wsta197.SELECTED_TRANSPORT,
            "transport_gate_json": runner.rel(gate_path),
            "transport_gate_markdown": runner.rel(gate_path.with_suffix(".md")),
            "source_wsta196_result": "workspace/private/wsta196_result.json",
            "source_wsta196_source_gate": "workspace/private/wsta196_source_gate.json",
            "source_wsta149_live_transport_proof": "workspace/private/wsta149_result.json",
            "source_wsta167_seccomp_asset_source_gate": "workspace/private/wsta167_result.json",
            "canary_service": "dpublic-hud",
            "policy_service": "dpublic-hud-intent",
            "launcher_command": ["/usr/local/bin/a90-service-launch", "dpublic-hud", "/bin/true"],
            "single_service_canary": True,
            "private_token_env": runner.wsta193.PRIVATE_TOKEN_ENV,
            "token_value_included": False,
            "correct_wsta161_token_supplied": False,
            "seccomp_filter_loaded": False,
            "seccomp_enforced": False,
            "wsta196_direct_host_subprocess_execute_allowed": False,
            "ready_for_wsta198_transport_adapter": True,
            "ready_for_wsta196_live_execute": False,
            "execution_sequence": [
                "fresh-native-readonly-health",
                "start-temporary-dropbear-over-ncm",
                "post-native-readonly-health",
            ],
            "adapter_contract": {
                "runner": "workspace/public/src/scripts/server-distro/run_wsta198_seccomp_load_canary_ssh_adapter.py",
                "must_not_put_token_on_command_line": True,
                "must_redact_token_from_stdout_stderr": True,
                "must_fail_closed_without_wsta196_ack_flags": True,
                "must_fail_closed_without_private_token_env": True,
                "must_fail_closed_without_fresh_health": True,
            },
            "public_url_value_logged": False,
            "secret_values_logged": 0,
        }

    def write_wsta198_adapter(self, root: Path, *, mutate_packet=None) -> tuple[Path, Path, Path]:
        gate_path = root / "wsta197" / runner.wsta198.wsta197.TRANSPORT_JSON_NAME
        self.write_json(gate_path, self.transport_gate_payload(gate_path))
        adapter_dir = root / "wsta198"
        packet, script = runner.wsta198.build_adapter_packet(
            adapter_dir,
            gate_path,
            self.transport_gate_payload(gate_path),
        )
        if mutate_packet:
            mutate_packet(packet)
        self.write_json(adapter_dir / runner.wsta198.ADAPTER_JSON_NAME, packet)
        (adapter_dir / runner.wsta198.ADAPTER_SH_NAME).write_text(script, encoding="utf-8")
        (adapter_dir / runner.wsta198.ADAPTER_SH_NAME).chmod(0o700)
        return adapter_dir / runner.wsta198.ADAPTER_JSON_NAME, gate_path, adapter_dir / runner.wsta198.ADAPTER_SH_NAME

    def write_wsta199_status(self, root: Path, *, mutate_status=None, mutate_adapter=None) -> Path:
        adapter, _gate, _script = self.write_wsta198_adapter(root, mutate_packet=mutate_adapter)
        status_dir = root / "wsta199"
        result = runner.wsta199.run(runner.wsta199.build_arg_parser().parse_args([
            "--run-dir",
            str(status_dir),
            "--wsta198-adapter-json",
            str(adapter),
        ]))
        if mutate_status:
            mutate_status(result)
            self.write_json(status_dir / runner.wsta199.STATUS_JSON_NAME, result)
        return status_dir / runner.wsta199.STATUS_JSON_NAME

    def args(self, root: Path, status: Path) -> list[str]:
        return [
            "--run-dir",
            str(root / "wsta200"),
            "--wsta199-status-json",
            str(status),
            "--prepare-wsta200-operator-handoff",
        ]

    def test_handoff_passes_for_current_status_and_requires_token(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            status = self.write_wsta199_status(root)
            result = runner.run(runner.build_arg_parser().parse_args(self.args(root, status)))
            handoff = json.loads((root / "wsta200" / runner.HANDOFF_JSON_NAME).read_text(encoding="utf-8"))
            script = (root / "wsta200" / runner.HANDOFF_SH_NAME).read_text(encoding="utf-8")
            markdown = (root / "wsta200" / runner.HANDOFF_MD_NAME).read_text(encoding="utf-8")

        self.assertEqual(result["decision"], runner.PASS_DECISION)
        self.assertEqual(handoff["state"], "READY_OPERATOR_HANDOFF_WSTA198_TOKEN_REQUIRED_DEFAULT_OFF")
        self.assertTrue(handoff["ready_for_attended_live_handoff"])
        self.assertFalse(handoff["ready_for_immediate_live_execute"])
        self.assertFalse(handoff["correct_wsta161_token_supplied"])
        self.assertTrue(handoff["status_stable_view_match"])
        self.assertIn("run_wsta199_wsta198_adapter_status.py", script)
        self.assertIn("wsta198_seccomp_load_canary_ssh_adapter.sh", script)
        self.assertIn("WSTA200 renders an operator handoff only", markdown)
        self.assertFalse(result["safety"]["device_action"])
        self.assertFalse(result["safety"]["live_command_executed"])
        self.assertFalse(result["safety"]["seccomp_filter_loaded"])

    def test_handoff_marks_immediate_ready_when_token_env_matches_without_supplying_it(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            status = self.write_wsta199_status(root)
            with mock.patch.dict(runner.os.environ, {
                runner.wsta193.PRIVATE_TOKEN_ENV: runner.wsta161.LOAD_TOKEN
            }):
                result = runner.run(runner.build_arg_parser().parse_args(self.args(root, status)))

        handoff = result["operator_handoff"]
        self.assertEqual(result["decision"], runner.PASS_DECISION)
        self.assertEqual(handoff["state"], "READY_OPERATOR_HANDOFF_WSTA198_ATTENDED_LIVE")
        self.assertTrue(handoff["ready_for_immediate_live_execute"])
        self.assertFalse(handoff["correct_wsta161_token_supplied"])
        self.assertFalse(result["safety"]["device_action"])

    def test_default_run_blocks_without_prepare_gate(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            status = self.write_wsta199_status(root)
            args = self.args(root, status)
            args.remove("--prepare-wsta200-operator-handoff")
            result = runner.run(runner.build_arg_parser().parse_args(args))

        self.assertEqual(result["decision"], "wsta200-blocked-explicit-prepare-gate-required")
        self.assertFalse(result["safety"]["live_command_executed"])

    def test_blocks_stale_or_nonprivate_status(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)

            def mutate(payload: dict) -> None:
                payload["adapter_status"]["packet_match"] = False

            status = self.write_wsta199_status(root, mutate_status=mutate)
            result = runner.run(runner.build_arg_parser().parse_args(self.args(root, status)))
        self.assertEqual(result["decision"], "wsta200-blocked-status-invalid")
        self.assertFalse(result["status_checks"]["packet_match"])

        with self.private_tmp() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            status = self.write_wsta199_status(root)
            outside_status = Path(outside) / runner.wsta199.STATUS_JSON_NAME
            outside_status.write_text(status.read_text(encoding="utf-8"), encoding="utf-8")
            result = runner.run(runner.build_arg_parser().parse_args(self.args(root, outside_status)))
        self.assertEqual(result["decision"], "wsta200-blocked-status-nonprivate")

    def test_blocks_status_drift_against_fresh_recheck(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            status = self.write_wsta199_status(root)
            payload = json.loads(status.read_text(encoding="utf-8"))
            payload["adapter_status"]["operator_preflight_checks"].append("stale-extra")
            self.write_json(status, payload)
            result = runner.run(runner.build_arg_parser().parse_args(self.args(root, status)))

        self.assertEqual(result["decision"], "wsta200-blocked-status-drift")
        self.assertTrue(result["checks"]["wsta199_recheck_valid"])
        self.assertFalse(result["checks"]["status_stable_view_match"])

    def test_print_template_and_public_surfaces_are_redacted(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            status = self.write_wsta199_status(root)
            result = runner.run(runner.build_arg_parser().parse_args(self.args(root, status)))
            summary_text = json.dumps(runner.public_summary(result), sort_keys=True)
            handoff_text = (root / "wsta200" / runner.HANDOFF_JSON_NAME).read_text(encoding="utf-8")
            script_text = (root / "wsta200" / runner.HANDOFF_SH_NAME).read_text(encoding="utf-8")
            source_text = SOURCE.read_text(encoding="utf-8")

        with mock.patch.object(runner, "run", side_effect=AssertionError("unexpected run")):
            with mock.patch("builtins.print") as printed:
                rc = runner.main_with_args(["--print-template"])

        self.assertEqual(rc, 0)
        for text in (summary_text, handoff_text, script_text, source_text, printed.call_args.args[0]):
            self.assertNotIn(TOKEN_LITERAL, text)
            self.assertNotIn("try" + "cloudflare.com", text.lower())
            self.assertNotIn("ssid=", text.lower())
            self.assertNotIn("psk=", text.lower())
            self.assertNotIn("native_init_flash.py", text)
        self.assertIn("wsta200-wsta199-operator-handoff-pass", source_text)
        self.assertIn("READY_OPERATOR_HANDOFF_WSTA198_TOKEN_REQUIRED_DEFAULT_OFF", source_text)
        self.assertIn('"boot_flash": False', source_text)
        self.assertIn('"correct_wsta161_token_in_artifact": False', source_text)


if __name__ == "__main__":
    unittest.main()
