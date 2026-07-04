from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _loader import load_script


wsta53 = load_script("workspace/public/src/scripts/server-distro/run_wsta53_persistent_exposure_plan.py")
runner = load_script("workspace/public/src/scripts/server-distro/run_wsta54_private_lease_artifact.py")
SOURCE = Path("workspace/public/src/scripts/server-distro/run_wsta54_private_lease_artifact.py")


class ServerDistroWsta54PrivateLeaseArtifactTests(unittest.TestCase):
    def private_tmp(self):
        runner.DEFAULT_RUN_BASE.mkdir(parents=True, exist_ok=True)
        return tempfile.TemporaryDirectory(dir=runner.DEFAULT_RUN_BASE)

    def valid_wsta53_result_path(self, root: Path) -> Path:
        args = wsta53.build_arg_parser().parse_args([
            "--run-dir",
            str(root / "wsta53"),
            "--ttl-sec",
            "1800",
            "--ack-credentialed-wifi",
            "--ack-public-exposure",
            "--native-confirm-token-source",
            "private",
            "--public-confirm-token-source",
            "private",
        ])
        result = wsta53.run(args)
        self.assertEqual(result["decision"], wsta53.PASS_DECISION)
        return root / "wsta53" / "wsta53_result.json"

    def valid_args(self, root: Path):
        return runner.build_arg_parser().parse_args([
            "--run-dir",
            str(root / "wsta54"),
            "--wsta53-result-json",
            str(self.valid_wsta53_result_path(root)),
        ])

    def test_default_run_is_fail_closed_and_device_inert(self) -> None:
        with self.private_tmp() as tmp:
            result = runner.run(runner.build_arg_parser().parse_args(["--run-dir", str(Path(tmp) / "run")]))

        self.assertEqual(result["decision"], "wsta54-blocked-wsta53-result-required")
        for key in (
            "device_action",
            "boot_flash",
            "native_reboot",
            "wifi_connect",
            "dhcp",
            "public_tunnel",
            "public_smoke",
            "userdata_touch",
            "switch_root",
        ):
            self.assertFalse(result["safety"][key])

    def test_valid_wsta53_result_generates_private_lease_and_redacted_marker(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            result = runner.run(self.valid_args(root))
            lease_path = runner.REPO_ROOT / result["private_lease_artifact"]
            marker_path = runner.REPO_ROOT / result["redacted_marker"]
            self.assertTrue(lease_path.is_file())
            self.assertTrue(marker_path.is_file())
            lease = json.loads(lease_path.read_text(encoding="utf-8"))
            marker = json.loads(marker_path.read_text(encoding="utf-8"))

        self.assertEqual(result["decision"], runner.PASS_DECISION)
        self.assertEqual(lease["schema"], runner.PRIVATE_LEASE_SCHEMA)
        self.assertEqual(lease["state"], "ARMED_PRIVATE_LEASE")
        self.assertEqual(lease["ttl_sec"], 1800)
        self.assertTrue(lease["lease_id"].startswith("wsta54-"))
        self.assertFalse(lease["wsta54_live_allowed"])
        self.assertTrue(lease["wsta55_explicit_live_gate_required"])
        self.assertEqual(lease["confirm_token_sources"], {"native": "private", "public": "private"})
        self.assertEqual(marker["schema"], runner.REDACTED_MARKER_SCHEMA)
        self.assertTrue(marker["lease_id_present"])
        self.assertTrue(marker["lease_id_value_redacted"])
        self.assertNotIn(lease["lease_id"], json.dumps(result, sort_keys=True))
        self.assertEqual(result["safety"]["secret_values_logged"], 0)
        self.assertFalse(result["safety"]["public_url_value_logged"])

    def test_rejects_blocked_wsta53_result(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            blocked = wsta53.run(wsta53.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "wsta53-blocked"),
            ]))
            self.assertNotEqual(blocked["decision"], wsta53.PASS_DECISION)
            args = runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "wsta54"),
                "--wsta53-result-json",
                str(root / "wsta53-blocked" / "wsta53_result.json"),
            ])
            result = runner.run(args)

        self.assertEqual(result["decision"], "wsta54-blocked-wsta53-not-pass")
        self.assertNotIn("private_lease_artifact", result)

    def test_rejects_nonprivate_run_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = runner.run(runner.build_arg_parser().parse_args(["--run-dir", str(Path(tmp) / "run")]))

        self.assertEqual(result["decision"], "wsta54-blocked-nonprivate-run-dir")

    def test_rejects_wsta53_result_with_forbidden_nested_field(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            source = self.valid_wsta53_result_path(root)
            payload = json.loads(source.read_text(encoding="utf-8"))
            payload["nested"] = {"raw_public_url": "redacted-placeholder"}
            source.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            result = runner.run(runner.build_arg_parser().parse_args([
                "--run-dir",
                str(root / "wsta54"),
                "--wsta53-result-json",
                str(source),
            ]))

        self.assertEqual(result["decision"], "wsta54-blocked-wsta53-redaction-finding")
        self.assertIn("forbidden-field:nested.raw_public_url", result["gate_detail"]["findings"])

    def test_public_summary_and_template_are_redacted(self) -> None:
        with self.private_tmp() as tmp:
            result = runner.run(self.valid_args(Path(tmp)))
            summary_text = repr(runner.public_summary(result)).lower()
            template_text = repr(runner.template()).lower()

        for text in (summary_text, template_text):
            self.assertNotIn("trycloudflare.com", text)
            self.assertNotIn("ssid=", text)
            self.assertNotIn("psk=", text)
            self.assertNotIn("http://", text)
            self.assertNotIn("https://", text)
            self.assertNotIn("native-confirm-token", text)
            self.assertNotIn("public-confirm-token", text)
        self.assertIn("workspace/private", template_text)

    def test_print_template_exits_without_running(self) -> None:
        with mock.patch.object(runner, "run", side_effect=AssertionError("unexpected run")):
            with mock.patch("builtins.print") as printed:
                rc = runner.main_with_args(["--print-template"])

        self.assertEqual(rc, 0)
        payload = printed.call_args.args[0]
        self.assertIn(runner.PRIVATE_LEASE_SCHEMA, payload)
        self.assertIn("workspace/private", payload)

    def test_source_does_not_import_or_call_live_control_surfaces(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")

        self.assertNotIn("subprocess", source)
        self.assertNotIn("native_init_flash.py", source)
        self.assertNotIn("a90ctl", source)
        self.assertNotIn("cloudflared tunnel", source)
        self.assertNotIn("run_wsta42", source)
        self.assertNotIn("run_wsta43", source)
        self.assertNotIn("run_wsta45", source)
        self.assertIn('"public_tunnel": False', source)
        self.assertIn('"boot_flash": False', source)
        self.assertIn('"native_reboot": False', source)


if __name__ == "__main__":
    unittest.main()
