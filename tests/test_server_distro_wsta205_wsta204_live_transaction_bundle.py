from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _loader import load_script


runner = load_script("workspace/public/src/scripts/server-distro/run_wsta205_wsta204_live_transaction_bundle.py")
SOURCE = Path("workspace/public/src/scripts/server-distro/run_wsta205_wsta204_live_transaction_bundle.py")
TOKEN_LITERAL = "WSTA161-" + "EXPLICIT-ALLOW-SECCOMP-LOAD"


class ServerDistroWsta205Wsta204LiveTransactionBundleTests(unittest.TestCase):
    def private_tmp(self):
        runner.DEFAULT_RUN_BASE.mkdir(parents=True, exist_ok=True)
        return tempfile.TemporaryDirectory(dir=runner.DEFAULT_RUN_BASE)

    def write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def write_verifier_chain(self, root: Path) -> Path:
        from tests.test_server_distro_wsta204_wsta203_live_result_verifier import (
            ServerDistroWsta204Wsta203LiveResultVerifierTests,
        )

        fixture = ServerDistroWsta204Wsta203LiveResultVerifierTests()
        audit_path = fixture.write_audit_chain(root)
        wsta204_dir = root / "wsta204"
        runner.wsta204.run(runner.wsta204.build_arg_parser().parse_args([
            "--run-dir",
            str(wsta204_dir),
            "--source-wsta203-audit-json",
            str(audit_path),
            "--emit-wsta204-live-result-verifier",
        ]))
        return wsta204_dir / runner.wsta204.VERIFIER_JSON_NAME

    def args(self, root: Path, verifier: Path, *, emit: bool = True) -> list[str]:
        args = [
            "--run-dir",
            str(root / "wsta205"),
            "--source-wsta204-verifier-json",
            str(verifier),
        ]
        if emit:
            args.append("--emit-wsta205-live-transaction-bundle")
        return args

    def test_emits_live_transaction_bundle_but_requires_token(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            verifier_path = self.write_verifier_chain(root)
            result = runner.run(runner.build_arg_parser().parse_args(self.args(root, verifier_path)))
            bundle = json.loads((root / "wsta205" / runner.TRANSACTION_JSON_NAME).read_text(encoding="utf-8"))
            shell = root / "wsta205" / runner.TRANSACTION_SH_NAME
            shell_text = shell.read_text(encoding="utf-8")
            shell_exists = shell.exists()
            shell_executable = bool(shell.stat().st_mode & 0o100)
            markdown = (root / "wsta205" / runner.TRANSACTION_MD_NAME).read_text(encoding="utf-8")

        self.assertEqual(result["decision"], runner.PASS_DECISION)
        self.assertEqual(bundle["live_transaction_bundle"]["state"], "LIVE_TRANSACTION_BUNDLE_READY_TOKEN_REQUIRED_DEFAULT_OFF")
        self.assertTrue(bundle["live_transaction_bundle"]["ready_for_transaction_execution"])
        self.assertFalse(bundle["live_transaction_bundle"]["ready_for_immediate_live_execute"])
        self.assertFalse(bundle["live_transaction_bundle"]["private_token_env_present"])
        self.assertTrue(shell_exists)
        self.assertTrue(shell_executable)
        self.assertIn("--emit-wsta204-live-result-verifier", shell_text)
        self.assertIn("--verify-wsta204-live-result", shell_text)
        self.assertIn("wsta198_result.json", shell_text)
        self.assertTrue(result["safety"]["wsta204_recheck_executed"])
        self.assertTrue(result["safety"]["wsta205_transaction_script_generated"])
        self.assertFalse(result["safety"]["wsta205_transaction_script_executed"])
        self.assertFalse(result["safety"]["wsta200_handoff_shell_executed"])
        self.assertFalse(result["safety"]["wsta198_live_command_executed"])
        self.assertIn("WSTA205 emits the transaction script only", markdown)

    def test_emits_token_ready_state_without_supplying_it(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            verifier_path = self.write_verifier_chain(root)
            with mock.patch.dict(runner.os.environ, {
                runner.wsta193.PRIVATE_TOKEN_ENV: runner.wsta161.LOAD_TOKEN
            }):
                result = runner.run(runner.build_arg_parser().parse_args(self.args(root, verifier_path)))

        bundle = result["live_transaction_bundle"]
        self.assertEqual(result["decision"], runner.PASS_DECISION)
        self.assertEqual(bundle["state"], "LIVE_TRANSACTION_BUNDLE_READY_TOKEN_READY_DEFAULT_OFF")
        self.assertTrue(bundle["ready_for_immediate_live_execute"])
        self.assertTrue(bundle["private_token_env_present"])
        self.assertTrue(bundle["private_token_matches_wsta161"])
        self.assertFalse(result["safety"]["correct_wsta161_token_supplied"])
        self.assertFalse(result["safety"]["device_action"])

    def test_blocks_without_explicit_emit_gate(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            verifier_path = self.write_verifier_chain(root)
            result = runner.run(runner.build_arg_parser().parse_args(self.args(root, verifier_path, emit=False)))

        self.assertEqual(result["decision"], "wsta205-blocked-explicit-emit-gate-required")
        self.assertFalse(result["safety"]["wsta204_recheck_executed"])
        self.assertFalse(result["safety"]["live_command_executed"])

    def test_blocks_verifier_drift_after_recheck(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            verifier_path = self.write_verifier_chain(root)
            payload = json.loads(verifier_path.read_text(encoding="utf-8"))
            payload["live_result_verifier"]["operator_preflight_checks"].append("stale-extra")
            self.write_json(verifier_path, payload)
            result = runner.run(runner.build_arg_parser().parse_args(self.args(root, verifier_path)))

        self.assertEqual(result["decision"], "wsta205-blocked-verifier-drift")
        self.assertTrue(result["checks"]["wsta204_recheck_valid"])
        self.assertFalse(result["checks"]["verifier_stable_view_match"])
        self.assertFalse(result["safety"]["wsta200_handoff_shell_executed"])

    def test_blocks_mutated_handoff_script_before_bundle_emit(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            verifier_path = self.write_verifier_chain(root)
            payload = json.loads(verifier_path.read_text(encoding="utf-8"))
            script_path = runner.resolve_path(payload["live_result_verifier"]["handoff_command_script"])
            text = script_path.read_text(encoding="utf-8")
            script_path.write_text(text.replace("${A90_PRIVATE_WSTA161_LOAD_TOKEN:?private-token-required}", "missing-token-guard"), encoding="utf-8")
            result = runner.run(runner.build_arg_parser().parse_args(self.args(root, verifier_path)))

        self.assertEqual(result["decision"], "wsta205-blocked-verifier-invalid")
        self.assertFalse(result["verifier_checks"]["handoff_script_requires_private_token_env"])

    def test_blocks_invalid_or_nonprivate_verifier(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            verifier_path = self.write_verifier_chain(root)
            payload = json.loads(verifier_path.read_text(encoding="utf-8"))
            payload["live_result_verifier"]["audit_current"] = False
            self.write_json(verifier_path, payload)
            result = runner.run(runner.build_arg_parser().parse_args(self.args(root, verifier_path)))
        self.assertEqual(result["decision"], "wsta205-blocked-verifier-invalid")
        self.assertFalse(result["verifier_checks"]["audit_current"])

        with self.private_tmp() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            verifier_path = self.write_verifier_chain(root)
            outside_verifier = Path(outside) / runner.wsta204.VERIFIER_JSON_NAME
            outside_verifier.write_text(verifier_path.read_text(encoding="utf-8"), encoding="utf-8")
            result = runner.run(runner.build_arg_parser().parse_args(self.args(root, outside_verifier)))
        self.assertEqual(result["decision"], "wsta205-blocked-verifier-nonprivate")

    def test_print_template_and_public_surfaces_are_redacted(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            verifier_path = self.write_verifier_chain(root)
            result = runner.run(runner.build_arg_parser().parse_args(self.args(root, verifier_path)))
            summary_text = json.dumps(runner.public_summary(result), sort_keys=True)
            bundle_text = (root / "wsta205" / runner.TRANSACTION_JSON_NAME).read_text(encoding="utf-8")
            source_text = SOURCE.read_text(encoding="utf-8")

        with mock.patch.object(runner, "run", side_effect=AssertionError("unexpected run")):
            with mock.patch("builtins.print") as printed:
                rc = runner.main_with_args(["--print-template"])

        self.assertEqual(rc, 0)
        for text in (summary_text, bundle_text, source_text, printed.call_args.args[0]):
            self.assertNotIn(TOKEN_LITERAL, text)
            self.assertNotIn("try" + "cloudflare.com", text.lower())
            self.assertNotIn("ssid=", text.lower())
            self.assertNotIn("psk=", text.lower())
            self.assertNotIn("native_init_flash.py", text)
        self.assertIn("wsta205-wsta204-live-transaction-bundle-source-pass", source_text)
        self.assertIn("LIVE_TRANSACTION_BUNDLE_READY_TOKEN_REQUIRED_DEFAULT_OFF", source_text)
        self.assertIn('"boot_flash": False', source_text)
        self.assertIn('"correct_wsta161_token_in_artifact": False', source_text)


if __name__ == "__main__":
    unittest.main()
