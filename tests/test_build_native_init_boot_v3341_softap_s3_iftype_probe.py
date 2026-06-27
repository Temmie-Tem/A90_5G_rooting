from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


ROOT = Path(__file__).resolve().parents[1]
WIFI_C = ROOT / "workspace/public/src/native-init/a90_wifi.c"

runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3341_softap_s3_iftype_probe.py"
)


class BuildNativeInitBootV3341SoftapS3IftypeProbeTests(unittest.TestCase):
    def test_v3341_identity(self) -> None:
        self.assertEqual(runner.CYCLE, "V3341")
        self.assertEqual(runner.INIT_VERSION, "0.11.105")
        self.assertEqual(runner.INIT_BUILD, "v3341-softap-s3-iftype-probe")
        self.assertEqual(
            runner.BOOT_IMAGE.name,
            "boot_linux_v3341_softap_s3_iftype_probe.img",
        )
        self.assertEqual(runner.BASE_BOOT.name, "boot_linux_v3335_gpu_z3_primary_setcrtc.img")

    def test_required_strings_include_iftype_probe_markers(self) -> None:
        required = b"\n".join(runner.REQUIRED_STRINGS)

        self.assertIn(b"0.11.105", required)
        self.assertIn(b"v3341-softap-s3-iftype-probe", required)
        self.assertIn(b"a90-native-wifi-softap-v2", required)
        self.assertIn(b"wifi softap [status|plan|prepare [profile]|iftype-probe [timeout_ms]|cleanup]", required)
        self.assertIn(b"softap-iftype-probe-pass", required)
        self.assertIn(b"softap-iftype-probe-add-failed", required)
        self.assertIn(b"ap_iftype_add_attempted=1", required)
        self.assertIn(b"sta_supplicant.stoppable=%d", required)
        self.assertIn(b"wpa_supplicant_mode2_start_attempted=0", required)

    def test_softap_manifest_is_s3_lower_gate_contract(self) -> None:
        manifest = runner._softap_manifest()

        self.assertEqual(manifest["rung"], "S3-lower-gate")
        self.assertEqual(manifest["scope"], "softap-iftype-add-delete-probe-no-ap-start")
        self.assertIn("wifi softap iftype-probe", manifest["commands"])
        self.assertIn("softap-iftype-probe-pass", manifest["expected_current_decisions"])
        self.assertIn("ap-iftype-cleanup-ok-1", manifest["pass_requirements"])
        self.assertIn("no-mode2-ap-start", manifest["pass_requirements"])
        self.assertEqual(
            manifest["helper_route"]["fwclass_bridge_flag"],
            runner.SERVICE_OBJECT_FWCLASS_BRIDGE_FLAG,
        )

    def test_report_describes_no_ap_start(self) -> None:
        report = runner.render_report(
            {
                "boot_image": str(runner.BOOT_IMAGE),
                "boot_sha256": "0" * 64,
            },
            (runner.SERVICE_OBJECT_FWCLASS_BRIDGE_FLAG,),
            (),
        )

        self.assertIn("V3341", report)
        self.assertIn("0.11.105", report)
        self.assertIn("wifi softap iftype-probe", report)
        self.assertIn("wpa_supplicant mode=2", report)
        self.assertIn("no `udhcpd`", report)
        self.assertIn("metadata-only", report)

    def test_current_source_contains_iftype_probe(self) -> None:
        source = WIFI_C.read_text(encoding="utf-8")

        self.assertIn("wifi_softap_iftype_probe", source)
        self.assertIn("NL80211_CMD_NEW_INTERFACE", source)
        self.assertIn("NL80211_CMD_DEL_INTERFACE", source)
        self.assertIn("softap-iftype-probe-pass", source)


if __name__ == "__main__":
    unittest.main()
