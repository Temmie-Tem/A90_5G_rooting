import argparse
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "workspace/public/src/scripts/revalidation"
SCRIPT = SCRIPT_DIR / "s22plus_o3f_freestanding_acm_live_gate.py"
MANIFEST = ROOT / "workspace/private/outputs/s22plus_native_init/o3f_freestanding_acm_v0_1/manifest.json"


def load_module():
    sys.path.insert(0, str(SCRIPT_DIR))
    try:
        spec = importlib.util.spec_from_file_location("s22plus_o3f_freestanding_acm_live_gate_tested", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(SCRIPT_DIR))


class S22PlusO3FFreestandingAcmLiveGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    @unittest.skipUnless(MANIFEST.is_file(), "O3F build manifest unavailable")
    def test_real_manifest_matches_exact_live_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = self.module.verify_manifest(MANIFEST, Path(tmp) / "gate.log")
        self.assertEqual(data["hashes"]["ap_tar_md5"], self.module.EXPECTED_AP_SHA256)
        self.assertEqual(data["hashes"]["o3f_init"], self.module.EXPECTED_INIT_SHA256)
        self.assertEqual(data["plan"]["module_count"], 59)
        self.assertEqual(data["ramdisk"]["added_entries"], [])
        self.assertFalse(data["safety"]["live_flash_authorized"])
        self.assertFalse(data["safety"]["daemon_exec"])

    def test_status_contract_accepts_only_complete_o3f_bundle(self):
        values = {
            "marker": self.module.EXPECTED_MARKER,
            "version": "0.2",
            "phase": "control-ready",
            "result": "ready",
            "rc": "0",
            "plan_count": "59",
            "module_attempted": "59",
            "module_loaded": "58",
            "module_eexist": "1",
            "module_failed": "0",
            "proc_registration_rc": "0",
            "proc_eof": "1",
            "proc_found": "59",
            "gate_mask": "0xff",
            "gate_count": "8",
            "configfs_rc": "0",
            "ssusb_mode_write_rc": "0",
            "ssusb_mode_readback_ok": "1",
            "udc_bind_rc": "0",
            "udc_readback_ok": "1",
            "ttyGS0_ready": "1",
            "gadget_function": "acm.usb0",
            "udc": "a600000.dwc3",
            "protocol_result": "pass",
            "protocol_handled": "128",
            "protocol_invalid": "0",
            "protocol_crc_errors": "0",
            "protocol_seq_errors": "0",
        }
        self.assertEqual(self.module.status_reasons(values), [])
        values["version"] = "0.1"
        self.assertIn("version-mismatch:'0.1'", self.module.status_reasons(values))

    def test_agents_exception_is_o3f_exact_and_consumption_aware(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = root / "gate.log"
            segment = self.module.ACTIVE_EXCEPTION_HEADING + "\n" + "\n".join(
                self.module.policy_markers()
            )
            (root / "AGENTS.md").write_text(segment + "\n", encoding="utf-8")
            self.module.verify_agents_exception(root, log)
            (root / "AGENTS.md").write_text(segment + "\nConsumed/retired\n", encoding="utf-8")
            with self.assertRaisesRegex(SystemExit, "absent or consumed"):
                self.module.verify_agents_exception(root, log)

    def test_live_requires_independent_o3f_tokens(self):
        good = argparse.Namespace(
            ack=self.module.LIVE_ACK_TOKEN,
            rollback_ack=self.module.ROLLBACK_ACK_TOKEN,
        )
        self.module.validate_live_tokens(good)
        bad = argparse.Namespace(ack="wrong", rollback_ack=self.module.ROLLBACK_ACK_TOKEN)
        with self.assertRaisesRegex(SystemExit, "--live requires --ack"):
            self.module.validate_live_tokens(bad)

    def test_base_runner_is_rebound_to_o3f_contract(self):
        self.module.configure_base()
        delegated = self.module.base
        self.assertEqual(delegated.EXPECTED_AP_SHA256, self.module.EXPECTED_AP_SHA256)
        self.assertEqual(delegated.EXPECTED_USB_SERIAL, "S22O3FACM01")
        self.assertEqual(delegated.EXPECTED_MARKER, self.module.EXPECTED_MARKER)
        self.assertIs(delegated.verify_manifest, self.module.verify_manifest)
        self.assertIs(delegated.verify_artifacts, self.module.verify_artifacts)
        self.assertIs(delegated.status_reasons, self.module.status_reasons)
        self.assertEqual(delegated.REQUIRED_TIMELINE_PHASES, self.module.REQUIRED_TIMELINE_PHASES)

    def test_source_keeps_attended_rollback_and_single_events_timeline(self):
        base_text = (SCRIPT_DIR / "s22plus_o3_minimal_acm_live_gate.py").read_text(encoding="ascii")
        for phase in self.module.REQUIRED_TIMELINE_PHASES:
            self.assertIn(f'"{phase}"', base_text)
        self.assertIn("manual-rollback-wait", base_text)
        self.assertIn("perform_rollback(", base_text)
        self.assertIn("verify_partition_hash(", base_text)
        wrapper_text = SCRIPT.read_text(encoding="ascii")
        self.assertIn(self.module.EXPECTED_AP_SHA256, wrapper_text)
        self.assertNotIn("EXPECTED_CONTROL_SHA256", wrapper_text)


if __name__ == "__main__":
    unittest.main()
