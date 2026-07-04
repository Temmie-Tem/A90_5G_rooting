"""Regression tests for V3396 WSTA persistent-state screen source build."""

from __future__ import annotations

import unittest

from _loader import load_revalidation


builder = load_revalidation("build_native_init_boot_v3396_wsta_persistent_state_screen")


class BuildNativeInitBootV3396WstaPersistentStateScreenTests(unittest.TestCase):
    def test_builder_identity_and_required_markers(self) -> None:
        self.assertEqual(builder.CYCLE, "V3396")
        self.assertEqual(builder.INIT_VERSION, "0.11.152")
        self.assertEqual(builder.INIT_BUILD, "v3396-wsta-persistent-state-screen")

        required = b"\n".join(builder.REQUIRED_STRINGS)
        for marker in (
            b"v3396-wsta-persistent-state-screen",
            b"0.11.152",
            b"screenapp.title=WSTA D-PUBLIC",
            b"WSTA D-PUBLIC",
            b"WSTA PUBLISH",
            b"STATE: PUBLIC_OFF LEASE-GATED",
            b"PROOF: WSTA55 START / WSTA58 RENEW",
            b"URL: REDACTED PRIVATE-RUN ONLY",
            b"NATIVE: DISPLAY-ONLY NO CONNECT",
        ):
            self.assertIn(marker, required)

    def test_rewrite_updates_v3395_identity(self) -> None:
        text = builder._rewrite_v3396_text(
            "V3395 0.11.151 v3395-wsta-screenapp-live "
            "a90-doomgeneric-v3395"
        )
        self.assertIn("V3396", text)
        self.assertIn("0.11.152", text)
        self.assertIn("v3396-wsta-persistent-state-screen", text)
        self.assertIn("a90-doomgeneric-v3396", text)
        self.assertNotIn("v3395", text)
        self.assertNotIn("wsta-screenapp-live", text)

    def test_manifest_records_wsta_persistent_state_contract(self) -> None:
        manifest = builder._boot_audit_manifest()
        self.assertEqual(manifest["rung"], "wsta-persistent-state-screen")
        self.assertEqual(manifest["scope"], "native-wsta-redacted-persistent-state-screen")

        screenapp = manifest["wsta_operator_screenapp"]
        self.assertEqual(screenapp["surface"], "NETWORK menu + screenapp wsta/dpublic")
        self.assertEqual(screenapp["mode"], "read-only-display")
        self.assertEqual(screenapp["state"], "PUBLIC_OFF")
        self.assertEqual(screenapp["lease_policy"], "host-private-lease-gated")
        self.assertEqual(screenapp["public_url_display"], "redacted-private-run-only")
        self.assertEqual(screenapp["native_public_action"], "none")
        self.assertEqual(screenapp["redacted_result_source"], "WSTA48")


if __name__ == "__main__":
    unittest.main()
