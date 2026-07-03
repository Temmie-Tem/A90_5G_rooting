"""Regression tests for the D-public no-exposure preflight."""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from _loader import load_script


dpublic = load_script("workspace/public/src/scripts/server-distro/prepare_dpublic_preflight.py")


class PrepareDpublicPreflightTests(unittest.TestCase):
    def test_defaults_are_private_and_operator_gated(self) -> None:
        self.assertIn("workspace/private", str(dpublic.DEFAULT_CLOUDFLARED))
        self.assertIn("workspace/private/secrets", str(dpublic.DEFAULT_TOKEN_FILE))
        self.assertIn("workspace/private/secrets", str(dpublic.DEFAULT_HOSTNAME_FILE))
        self.assertEqual(dpublic.DEFAULT_SERVICE_URL, "http://127.0.0.1:8080")
        self.assertEqual(dpublic.DPUBLIC_LIVE_OPERATOR_TOKEN, "D-PUBLIC-LIVE-PUBLISH")

    def test_live_inputs_do_not_mark_live_ready_without_private_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            payload = dpublic.live_inputs(base / "missing-token", base / "missing-hostname", "http://127.0.0.1:8080")
        self.assertFalse(payload["token_present"])
        self.assertFalse(payload["hostname_present"])
        self.assertFalse(payload["live_publish_ready"])
        self.assertTrue(payload["quick_tunnel_possible_but_live_exposure"])
        self.assertEqual(payload["live_operator_token_required"], "D-PUBLIC-LIVE-PUBLISH")

    def test_live_inputs_mark_ready_with_private_token_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            token = Path(tmp) / "token"
            hostname = Path(tmp) / "hostname"
            token.write_text("dummy-token\n", encoding="utf-8")
            payload = dpublic.live_inputs(token, hostname, "http://127.0.0.1:8080")
        self.assertTrue(payload["token_present"])
        self.assertFalse(payload["hostname_present"])
        self.assertTrue(payload["live_publish_ready"])

    def test_verify_cloudflared_is_sha_and_size_pinned(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            binary = Path(tmp) / "cloudflared-linux-arm64"
            data = b"fake-arm64-cloudflared"
            binary.write_bytes(data)
            expected_sha = hashlib.sha256(data).hexdigest()
            payload = dpublic.verify_cloudflared(binary, expected_sha, len(data))
        self.assertEqual(payload["sha256"], expected_sha)
        self.assertEqual(payload["size_bytes"], len(data))
        self.assertEqual(payload["target_device_mode_octal"], "0755")

    def test_source_keeps_public_publish_out_of_preflight(self) -> None:
        source = Path("workspace/public/src/scripts/server-distro/prepare_dpublic_preflight.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('"public_exposure_performed": False', source)
        self.assertIn('"device_write_performed": False', source)
        self.assertNotIn("cloudflared tunnel run", source)
        self.assertNotIn("cloudflared tunnel --url", source)


if __name__ == "__main__":
    unittest.main()
