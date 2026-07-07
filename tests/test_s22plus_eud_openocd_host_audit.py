import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path("workspace/public/src/scripts/revalidation/s22plus_eud_openocd_host_audit.py")


def load_module():
    spec = importlib.util.spec_from_file_location("s22plus_eud_openocd_host_audit", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def readiness(openocd_present=True, eud_cfg=True, qcom_cfg=True, sm8450_cfg=True, host_eud=True, phase_b=None):
    return {
        "openocd": {
            "openocd_present": openocd_present,
            "eud_cfg_present": eud_cfg,
            "qcom_cfg_present": qcom_cfg,
            "sm8450_cfg_present": sm8450_cfg,
        },
        "host": {"host_eud_usb_hint": host_eud},
        "phase_b": phase_b,
    }


class S22PlusEudOpenocdHostAuditTest(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_classify_blocks_without_openocd_first(self):
        result = self.module.classify(
            readiness(openocd_present=False, eud_cfg=False, qcom_cfg=False, sm8450_cfg=False, host_eud=False)
        )
        self.assertEqual(result["result"], "blocked_no_openocd")
        self.assertIn("openocd-not-installed", result["reasons"])

    def test_classify_requires_eud_and_qualcomm_scripts(self):
        result = self.module.classify(readiness(eud_cfg=False, qcom_cfg=False, sm8450_cfg=True, host_eud=True))
        self.assertEqual(result["result"], "blocked_missing_openocd_eud_scripts")
        self.assertIn("missing-interface-eud-cfg", result["reasons"])
        self.assertIn("missing-qualcomm-target-cfg", result["reasons"])

    def test_classify_requires_sm8450_target_before_usb_wait(self):
        result = self.module.classify(readiness(sm8450_cfg=False, host_eud=False))
        self.assertEqual(result["result"], "blocked_missing_sm8450_target")
        self.assertIn("missing-sm8450-target-cfg", result["reasons"])

    def test_classify_waits_for_eud_enumeration_after_phase_b_negative(self):
        phase_b = {
            "restored_enable_0": True,
            "host_eud_or_new_tty_hint": False,
        }
        result = self.module.classify(readiness(host_eud=False, phase_b=phase_b))
        self.assertEqual(result["result"], "waiting_for_eud_enumeration_or_hardware")
        self.assertIn("phase-b-no-host-eud-or-new-tty", result["reasons"])
        self.assertIn("no-current-host-eud-usb", result["reasons"])

    def test_classify_ready_when_all_host_requirements_present(self):
        result = self.module.classify(readiness())
        self.assertEqual(result["result"], "host_openocd_eud_ready_to_probe")
        self.assertEqual(result["reasons"], [])


if __name__ == "__main__":
    unittest.main()
