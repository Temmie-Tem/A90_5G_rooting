from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _loader import load_script


runner = load_script("workspace/public/src/scripts/server-distro/run_wsta195_seccomp_load_canary_readiness.py")
SOURCE = Path("workspace/public/src/scripts/server-distro/run_wsta195_seccomp_load_canary_readiness.py")
TOKEN_LITERAL = "WSTA161-" + "EXPLICIT-ALLOW-SECCOMP-LOAD"


class ServerDistroWsta195SeccompLoadCanaryReadinessTests(unittest.TestCase):
    def private_tmp(self):
        runner.DEFAULT_RUN_BASE.mkdir(parents=True, exist_ok=True)
        return tempfile.TemporaryDirectory(dir=runner.DEFAULT_RUN_BASE)

    def write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def write_wsta194_packet(self, root: Path, *, mutate: dict | None = None) -> tuple[Path, Path, Path]:
        packet_json = root / "wsta194" / runner.wsta194.PACKET_JSON_NAME
        shell = root / "wsta194" / runner.wsta194.PACKET_SH_NAME
        markdown = root / "wsta194" / runner.wsta194.PACKET_MD_NAME
        command = [
            "python3",
            runner.wsta194.FUTURE_WSTA196_RUNNER,
            "--run-id",
            "wsta196-seccomp-load-canary-execute-live-<fresh-timestamp>",
            "--wsta194-operator-packet-json",
            runner.rel(packet_json),
            "--execute-real-seccomp-load-canary",
            "--allow-correct-wsta161-token",
            "--ack-seccomp-load-risk",
            "--ack-single-service-canary-only",
            "--ack-no-flash-no-reboot",
            "--ack-cleanup-required",
            "--print-full-json",
        ]
        packet = {
            "schema": "a90-wsta194-seccomp-load-canary-operator-packet-v1",
            "state": "READY_OPERATOR_PACKET_SINGLE_SERVICE_CANARY_DEFAULT_OFF_WSTA196_REQUIRED",
            "default_off": True,
            "ready_for_live_execution": False,
            "ready_for_wsta195_readiness": True,
            "ready_for_wsta196_design": True,
            "source_wsta193_result": "workspace/private/wsta193_result.json",
            "source_wsta193_contract": "workspace/private/wsta193_contract.json",
            "source_wsta193_shell": "workspace/private/wsta193_source.sh",
            "canary_service": "dpublic-hud",
            "policy_service": "dpublic-hud-intent",
            "canary_command": ["/bin/true"],
            "launcher_command": ["/usr/local/bin/a90-service-launch", "dpublic-hud", "/bin/true"],
            "single_service_canary": True,
            "private_token_env": runner.wsta193.PRIVATE_TOKEN_ENV,
            "token_value_included": False,
            "correct_wsta161_token_supplied": False,
            "seccomp_filter_loaded": False,
            "seccomp_enforced": False,
            "future_live_command_template": command,
            "operator_packet_shell": runner.rel(shell),
            "operator_packet_markdown": runner.rel(markdown),
            "operator_acknowledgements_required": [
                "--execute-real-seccomp-load-canary",
                "--allow-correct-wsta161-token",
                "--ack-seccomp-load-risk",
                "--ack-single-service-canary-only",
                "--ack-no-flash-no-reboot",
                "--ack-cleanup-required",
            ],
            "operator_preflight_checks": [
                "run-WSTA194-immediately-before-WSTA195-readiness",
                "confirm-token-value-remains-private",
                "confirm-single-service-canary-only",
            ],
            "abort_conditions": ["WSTA196-runner-absent"],
            "cleanup_expectations": ["post-run audit required after any future WSTA196 execution"],
            "safety_boundary": {
                "boot_flash": False,
                "native_reboot": False,
                "wifi_connect": False,
                "dhcp": False,
                "public_tunnel": False,
                "packet_filter_mutation": False,
                "userdata_touch": False,
                "switch_root": False,
                "seccomp_filter_loaded": False,
                "seccomp_enforced": False,
                "correct_wsta161_token_supplied": False,
            },
            "live_execution_requested": False,
            "public_url_value_logged": False,
            "secret_values_logged": 0,
            "json_path": runner.rel(packet_json),
        }
        if mutate:
            packet.update(mutate)
        self.write_json(packet_json, {"decision": runner.wsta194.PASS_DECISION, "operator_packet": packet})
        shell.parent.mkdir(parents=True, exist_ok=True)
        shell.write_text(
            "\n".join([
                "#!/bin/sh",
                "set -eu",
                "echo A90WSTA194_OPERATOR_PACKET_DEFAULT_OFF=1",
                "echo A90WSTA194_WSTA196_REQUIRED=1",
                "echo a90_wsta194_decision=blocked-wsta196-not-implemented",
                "exit 65",
                "",
            ]),
            encoding="utf-8",
        )
        shell.chmod(0o700)
        markdown.write_text(
            "# WSTA194 Seccomp-Load Canary Operator Packet\n\n"
            "- Default off: `true`\n\n"
            "WSTA194 does not execute the canary.\n",
            encoding="utf-8",
        )
        return packet_json, shell, markdown

    def run_with_packet(self, root: Path, packet_json: Path) -> dict:
        return runner.run(runner.build_arg_parser().parse_args([
            "--run-dir",
            str(root / "wsta195"),
            "--wsta194-operator-packet-json",
            str(packet_json),
            "--emit-wsta195-seccomp-load-canary-readiness",
        ]))

    def test_readiness_passes_without_device_contact_or_live_execution(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            packet_json, _, _ = self.write_wsta194_packet(root)
            result = self.run_with_packet(root, packet_json)
            summary = json.loads((root / "wsta195" / runner.SUMMARY_NAME).read_text(encoding="utf-8"))
            readiness = json.loads((root / "wsta195" / runner.READINESS_JSON_NAME).read_text(encoding="utf-8"))
            markdown = (root / "wsta195" / runner.READINESS_MD_NAME).read_text(encoding="utf-8")

        self.assertEqual(result["decision"], runner.PASS_DECISION)
        self.assertEqual(summary["decision"], runner.PASS_DECISION)
        self.assertTrue(result["checks"]["wsta194_payload_valid"])
        self.assertTrue(result["checks"]["wsta194_operator_packet_valid"])
        self.assertTrue(result["checks"]["shell_wrapper_valid"])
        self.assertTrue(result["checks"]["markdown_valid"])
        self.assertTrue(result["checks"]["readiness_valid"])
        self.assertEqual(readiness["state"], "READY_FOR_WSTA196_DESIGN_READONLY_NOT_EXECUTABLE")
        self.assertEqual(readiness["readiness_scope"], "host-only-packet-readiness-not-device-readiness")
        self.assertTrue(readiness["ready_for_wsta196_design"])
        self.assertFalse(readiness["ready_for_live_execution"])
        self.assertFalse(readiness["device_readiness_checked"])
        self.assertFalse(readiness["correct_wsta161_token_supplied"])
        self.assertFalse(readiness["seccomp_filter_loaded"])
        self.assertIn("does not execute the operator packet", markdown)
        self.assertFalse(result["safety"]["device_action"])
        self.assertFalse(result["safety"]["live_command_executed"])
        self.assertFalse(result["safety"]["seccomp_filter_loaded"])

    def test_default_run_is_fail_closed_without_explicit_gate(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            packet_json, _, _ = self.write_wsta194_packet(root)
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "wsta195"),
                "--wsta194-operator-packet-json",
                str(packet_json),
            ]))

        self.assertEqual(result["decision"], "wsta195-blocked-explicit-gate-required")
        self.assertFalse(result["safety"]["device_action"])
        self.assertFalse(result["safety"]["correct_wsta161_token_supplied"])
        self.assertFalse(result["safety"]["seccomp_filter_loaded"])

    def test_blocks_nonprivate_or_missing_wsta194_packet(self) -> None:
        with self.private_tmp() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            outside_packet = Path(outside) / runner.wsta194.PACKET_JSON_NAME
            self.write_json(outside_packet, {"decision": runner.wsta194.PASS_DECISION})
            result = self.run_with_packet(root, outside_packet)
        self.assertEqual(result["decision"], "wsta195-blocked-wsta194-packet-nonprivate")

        with self.private_tmp() as tmp:
            root = Path(tmp)
            result = self.run_with_packet(root, root / "missing" / runner.wsta194.PACKET_JSON_NAME)
        self.assertEqual(result["decision"], "wsta195-blocked-wsta194-packet-missing")

    def test_blocks_if_packet_drifted_toward_live_load(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            packet_json, _, _ = self.write_wsta194_packet(root, mutate={"ready_for_live_execution": True})
            result = self.run_with_packet(root, packet_json)

        self.assertEqual(result["decision"], "wsta195-blocked-wsta194-operator-packet-invalid")
        self.assertFalse(result["wsta194_operator_packet_checks"]["not_ready_for_live_execution"])

        with self.private_tmp() as tmp:
            root = Path(tmp)
            packet_json, _, _ = self.write_wsta194_packet(root, mutate={"token_value_included": True})
            result = self.run_with_packet(root, packet_json)

        self.assertEqual(result["decision"], "wsta195-blocked-wsta194-operator-packet-invalid")
        self.assertFalse(result["wsta194_operator_packet_checks"]["token_value_not_included"])

    def test_blocks_if_shell_no_longer_fails_closed(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            packet_json, shell, _ = self.write_wsta194_packet(root)
            shell.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            result = self.run_with_packet(root, packet_json)

        self.assertEqual(result["decision"], "wsta195-blocked-shell-wrapper-invalid")
        self.assertFalse(result["shell_checks"]["shell_fails_closed"])
        self.assertFalse(result["shell_checks"]["shell_wsta196_required_marker"])

    def test_blocks_nonprivate_shell_path(self) -> None:
        with self.private_tmp() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            outside_shell = Path(outside) / runner.wsta194.PACKET_SH_NAME
            outside_shell.write_text(
                "#!/bin/sh\n"
                "echo A90WSTA194_OPERATOR_PACKET_DEFAULT_OFF=1\n"
                "echo A90WSTA194_WSTA196_REQUIRED=1\n"
                "echo a90_wsta194_decision=blocked-wsta196-not-implemented\n"
                "exit 65\n",
                encoding="utf-8",
            )
            outside_shell.chmod(0o700)
            packet_json, _, _ = self.write_wsta194_packet(
                root,
                mutate={"operator_packet_shell": str(outside_shell)},
            )
            result = self.run_with_packet(root, packet_json)

        self.assertEqual(result["decision"], "wsta195-blocked-shell-wrapper-invalid")
        self.assertFalse(result["shell_checks"]["shell_path_private"])

    def test_public_surfaces_are_redacted_and_source_is_host_only(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            packet_json, _, _ = self.write_wsta194_packet(root)
            result = self.run_with_packet(root, packet_json)
            summary_text = json.dumps(runner.public_summary(result), sort_keys=True)
            template_text = json.dumps(runner.template(), sort_keys=True)
            readiness_text = (root / "wsta195" / runner.READINESS_JSON_NAME).read_text(encoding="utf-8")
            markdown = (root / "wsta195" / runner.READINESS_MD_NAME).read_text(encoding="utf-8")
            source = SOURCE.read_text(encoding="utf-8")

        for text in (summary_text, template_text, readiness_text, markdown, source):
            self.assertNotIn("try" + "cloudflare.com", text.lower())
            self.assertNotIn("ssid=", text.lower())
            self.assertNotIn("psk=", text.lower())
            self.assertNotIn("http" + "://", text.lower())
            self.assertNotIn("https" + "://", text.lower())
            self.assertNotIn(TOKEN_LITERAL, text)
        self.assertIn("wsta195-seccomp-load-canary-readiness-pass", source)
        self.assertIn("READY_FOR_WSTA196_DESIGN_READONLY_NOT_EXECUTABLE", source)
        self.assertIn('"device_action": False', source)
        self.assertIn('"seccomp_filter_loaded": False', source)
        self.assertIn('"correct_wsta161_token_supplied": False', source)
        self.assertNotIn("native_init_flash.py", source)
        self.assertNotIn("a90_bridge.py", source)

    def test_print_template_exits_without_running(self) -> None:
        with mock.patch.object(runner, "run", side_effect=AssertionError("unexpected run")):
            with mock.patch("builtins.print") as printed:
                rc = runner.main_with_args(["--print-template"])

        self.assertEqual(rc, 0)
        payload = printed.call_args.args[0]
        self.assertIn("WSTA195 host-only", payload)
        self.assertIn("--emit-wsta195-seccomp-load-canary-readiness", payload)
        self.assertNotIn(TOKEN_LITERAL, payload)


if __name__ == "__main__":
    unittest.main()
