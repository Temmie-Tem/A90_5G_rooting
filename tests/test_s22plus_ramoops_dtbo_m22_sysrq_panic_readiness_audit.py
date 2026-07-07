import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path("workspace/public/src/scripts/revalidation/s22plus_ramoops_dtbo_m22_sysrq_panic_readiness_audit.py")
DRAFT = Path("docs/operations/S22PLUS_RAMOOPS_DTBO_M22_SYSRQ_PANIC_AGENTS_EXCEPTION_DRAFT_2026-07-08.md")
AGENTS = Path("AGENTS.md")


def load_module():
    script_dir = str(SCRIPT.parent.resolve())
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location("s22plus_ramoops_dtbo_m22_sysrq_panic_readiness_audit", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class S22PlusRamoopsDtboM22SysrqPanicReadinessAuditTest(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_draft_has_required_markers(self):
        markers = self.module.required_markers()
        status = self.module.marker_status(DRAFT, markers)
        self.assertEqual(status["missing"], [])
        self.assertTrue(status["complete"])

    def test_agents_policy_is_inactive_by_default(self):
        markers = self.module.required_markers()
        status = self.module.marker_status(AGENTS, markers)
        self.assertFalse(status["complete"])
        self.assertIn(self.module.gate.LIVE_ACK_TOKEN, status["missing"])
        self.assertIn(self.module.gate.ROLLBACK_BOOT_ACK_TOKEN, status["missing"])

    def test_required_markers_cover_intentional_crash_and_cleanup(self):
        markers = self.module.required_markers()
        self.assertIn("intentional kernel crash", markers)
        self.assertIn("sysrq-trigger-c", markers)
        self.assertIn("restore stock DTBO", markers)
        self.assertIn("no vendor_boot", markers)


if __name__ == "__main__":
    unittest.main()
