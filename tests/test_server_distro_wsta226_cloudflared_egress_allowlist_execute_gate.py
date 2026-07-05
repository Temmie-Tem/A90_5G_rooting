from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _loader import load_script


runner = load_script(
    "workspace/public/src/scripts/server-distro/run_wsta226_cloudflared_egress_allowlist_execute_gate.py"
)
SOURCE = Path("workspace/public/src/scripts/server-distro/run_wsta226_cloudflared_egress_allowlist_execute_gate.py")


class ServerDistroWsta226CloudflaredEgressAllowlistExecuteGateTests(unittest.TestCase):
    def private_tmp(self):
        runner.DEFAULT_RUN_BASE.mkdir(parents=True, exist_ok=True)
        return tempfile.TemporaryDirectory(dir=runner.DEFAULT_RUN_BASE)

    def write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def wsta223_result(self) -> dict:
        plan = {
            "schema": runner.wsta223.PLAN_SCHEMA,
            "state": runner.wsta223.PLAN_STATE,
            "service": runner.wsta223.wsta221.SERVICE,
            "hardening_lever": runner.wsta223.wsta221.HARDENING_LEVER,
            "activation": "attended-explicit-live-gate-after-default-drop",
            "default_public_off": True,
            "live_execution_requested": False,
            "packet_filter_mutation_by_wsta223": False,
            "required_helper_ops": list(runner.wsta223.HELPER_REQUIRED_OPS),
            "required_operator_acknowledgements": list(runner.wsta223.OPERATOR_ACKS),
            "required_live_phases": [
                {"name": "preflight"},
                {"name": "derive-redacted-egress-route"},
                {"name": "apply-after-default-drop"},
                {"name": "prove-service-and-nonwidening"},
                {"name": "restore-and-public-off"},
            ],
            "candidate_rule_shape": {
                "entry_chain": "OUTPUT",
                "dedicated_chain": "A90_CLOUDFLARED_EGRESS",
                "owner_match": {
                    "uid_owner": runner.wsta223.wsta221.SERVICE_UID,
                    "user": runner.wsta223.wsta221.SERVICE_USER,
                },
                "allow_dns": "route-resolved-live-preflight-required",
                "allow_tls": "route-resolved-live-preflight-required",
                "global_output_default": "unchanged-until-live-proof",
            },
            "blocked_until_source_exists": True,
            "public_url_value_logged": False,
            "secret_values_logged": 0,
        }
        return {
            "decision": runner.wsta223.PASS_DECISION,
            "run_dir": "workspace/private/runs/server-distro/wsta223-test",
            "live_gate_plan": plan,
            "checks": {"plan_ready": True},
            "safety": {
                "device_action": False,
                "packet_filter_mutation": False,
                "public_url_value_logged": False,
                "secret_values_logged": 0,
            },
        }

    def route_artifact(self) -> dict:
        return {
            "schema": runner.ROUTE_SCHEMA,
            "state": runner.ROUTE_STATE,
            "dns4": ["dns-route-redacted"],
            "tls4": ["tls-route-redacted"],
            "route_values_private": True,
            "route_values_logged": False,
            "public_url_value_logged": False,
            "secret_values_logged": 0,
        }

    def valid_args(self, root: Path, *extra: str):
        plan_path = root / "inputs" / "wsta223_result.json"
        self.write_json(plan_path, self.wsta223_result())
        return runner.build_arg_parser().parse_args([
            "--run-dir",
            str(root / "wsta226"),
            "--wsta223-result-json",
            str(plan_path),
            "--prepare-attended-egress-gate",
            "--ack-credentialed-wifi",
            "--ack-public-exposure",
            *extra,
        ])

    def fake_wsta88_preflight(self) -> dict:
        return {
            "decision": runner.wsta88.PREFLIGHT_DECISION,
            "run_dir": "workspace/private/runs/server-distro/example/wsta88",
            "checks": {
                "wsta80_preflight_pass": True,
                "packet_filter_hardening_ready": True,
                "public_url_value_logged": False,
                "secret_values_logged": 0,
            },
            "safety": {"public_url_value_logged": False, "secret_values_logged": 0},
        }

    def fake_wsta88_live(self) -> dict:
        payload = self.fake_wsta88_preflight()
        payload["decision"] = runner.wsta88.PASS_DECISION
        payload["checks"]["wsta80_live_pass"] = True
        payload["checks"]["cloudflared_egress_allowlist_enabled"] = True
        payload["checks"]["cloudflared_egress_dns4_count"] = 1
        payload["checks"]["cloudflared_egress_tls4_count"] = 1
        return payload

    def test_default_run_is_fail_closed_and_device_inert(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            with mock.patch.object(runner.wsta88, "run", side_effect=AssertionError("unexpected WSTA88")):
                result = runner.run(runner.build_arg_parser().parse_args([
                    "--run-dir",
                    str(root / "wsta226"),
                ]))

        self.assertEqual(result["decision"], "wsta226-blocked-prepare-attended-egress-gate-required")
        for key in ("device_action", "boot_flash", "native_reboot", "userdata_touch", "switch_root"):
            self.assertFalse(result["safety"][key])

    def test_prepare_gate_validates_plan_and_delegates_wsta88_preflight_only(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            with mock.patch.object(runner.wsta88, "run", return_value=self.fake_wsta88_preflight()) as delegated:
                result = runner.run(self.valid_args(root))
            saved = json.loads((root / "wsta226" / runner.RESULT_NAME).read_text(encoding="utf-8"))
            gate = json.loads((root / "wsta226" / runner.GATE_NAME).read_text(encoding="utf-8"))
            markdown = (root / "wsta226" / runner.MARKDOWN_NAME).read_text(encoding="utf-8")

        self.assertEqual(result["decision"], runner.PASS_DECISION)
        self.assertEqual(saved["decision"], runner.PASS_DECISION)
        self.assertEqual(gate["state"], "READY_FOR_ATTENDED_WSTA88_EGRESS_ALLOWLIST_LIVE_GATE")
        self.assertFalse(result["checks"]["live_execution_requested"])
        self.assertTrue(result["checks"]["wsta88_preflight_pass"])
        self.assertEqual(delegated.call_count, 1)
        call_args = delegated.call_args.args[0]
        self.assertTrue(call_args.prepare_to_execute)
        self.assertFalse(call_args.execute_wsta58_from_status)
        self.assertIn("WSTA226 Cloudflared Egress Execute Gate", markdown)

    def test_live_gate_blocks_without_route_artifact(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            args = self.valid_args(
                root,
                "--execute-live-egress-allowlist",
                "--allow-operator-live",
                "--allow-native-reboot",
                "--allow-public-live",
                "--ack-packet-filter-mutation",
                "--force-packet-filter-restore-proof",
                "--force-cloudflared-egress-allowlist-proof",
                "--force-control-plane-proof",
                "--force-public-off-proof",
                "--force-ttl-expiry-proof",
                "--force-manual-stop-proof",
                "--native-confirm-token",
                runner.wsta88.wsta80.wsta58.wsta55.wsta45.wsta25.NATIVE_CONFIRM_TOKEN,
                "--public-confirm-token",
                runner.wsta88.wsta80.wsta58.wsta55.wsta45.PUBLIC_CONFIRM_TOKEN,
            )
            with mock.patch.object(runner.wsta88, "run", side_effect=AssertionError("unexpected WSTA88")):
                result = runner.run(args)

        self.assertEqual(result["decision"], "wsta226-blocked-route-artifact-required")
        self.assertFalse(result["checks"]["explicit_live_gate"])

    def test_live_gate_delegates_to_wsta88_with_redacted_route_values(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            route_path = root / "inputs" / "cloudflared_egress_route.json"
            self.write_json(route_path, self.route_artifact())
            with mock.patch.object(runner.wsta88, "run", return_value=self.fake_wsta88_live()) as delegated:
                result = runner.run(self.valid_args(
                    root,
                    "--route-artifact-json",
                    str(route_path),
                    "--execute-live-egress-allowlist",
                    "--allow-operator-live",
                    "--allow-native-reboot",
                    "--allow-public-live",
                    "--ack-packet-filter-mutation",
                    "--force-packet-filter-restore-proof",
                    "--force-cloudflared-egress-allowlist-proof",
                    "--force-control-plane-proof",
                    "--force-public-off-proof",
                    "--force-ttl-expiry-proof",
                    "--force-manual-stop-proof",
                    "--native-confirm-token",
                    runner.wsta88.wsta80.wsta58.wsta55.wsta45.wsta25.NATIVE_CONFIRM_TOKEN,
                    "--public-confirm-token",
                    runner.wsta88.wsta80.wsta58.wsta55.wsta45.PUBLIC_CONFIRM_TOKEN,
                ))

        self.assertEqual(result["decision"], runner.LIVE_PASS_DECISION)
        self.assertEqual(delegated.call_count, 1)
        call_args = delegated.call_args.args[0]
        self.assertTrue(call_args.execute_wsta58_from_status)
        self.assertTrue(call_args.enable_cloudflared_egress_allowlist)
        self.assertTrue(call_args.force_cloudflared_egress_allowlist_proof)
        self.assertEqual(call_args.cloudflared_egress_dns4, ["dns-route-redacted"])
        self.assertEqual(call_args.cloudflared_egress_tls4, ["tls-route-redacted"])
        public_text = json.dumps(runner.public_summary(result), sort_keys=True)
        self.assertIn('"dns4_count": 1', public_text)
        self.assertNotIn("dns-route-redacted", public_text)
        self.assertNotIn("tls-route-redacted", public_text)

    def test_invalid_plan_or_route_artifact_fail_closed(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            args = self.valid_args(root)
            bad_plan_path = root / "inputs" / "bad_wsta223_result.json"
            bad_plan = self.wsta223_result()
            bad_plan["live_gate_plan"]["required_helper_ops"].remove("restore")
            self.write_json(bad_plan_path, bad_plan)
            args.wsta223_result_json = bad_plan_path
            with mock.patch.object(runner.wsta88, "run", side_effect=AssertionError("unexpected WSTA88")):
                result = runner.run(args)

        self.assertEqual(result["decision"], "wsta226-blocked-wsta223-plan-incomplete")

        with self.private_tmp() as tmp:
            root = Path(tmp)
            route_path = root / "inputs" / "bad_route.json"
            route = self.route_artifact()
            route["tls4"] = []
            self.write_json(route_path, route)
            args = self.valid_args(root, "--route-artifact-json", str(route_path))
            with mock.patch.object(runner.wsta88, "run", side_effect=AssertionError("unexpected WSTA88")):
                result = runner.run(args)

        self.assertEqual(result["decision"], "wsta226-blocked-route-artifact-invalid")

    def test_source_keeps_flash_and_public_value_surfaces_out(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")

        self.assertIn("--prepare-attended-egress-gate", source)
        self.assertIn("--execute-live-egress-allowlist", source)
        self.assertIn("--force-cloudflared-egress-allowlist-proof", source)
        self.assertIn("--force-control-plane-proof", source)
        self.assertIn("--force-public-off-proof", source)
        self.assertIn("wsta88.run", source)
        self.assertIn('"boot_flash": False', source)
        self.assertIn('"route_values_logged": False', source)
        self.assertIn('"public_url_value_logged": False', source)
        self.assertNotIn("native_init_flash.py", source)
        self.assertNotIn("try" + "cloudflare.com", source)
        self.assertNotIn("ssid" + "=", source.lower())
        self.assertNotIn("psk" + "=", source.lower())


if __name__ == "__main__":
    unittest.main()
