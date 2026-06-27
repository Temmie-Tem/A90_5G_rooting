from __future__ import annotations

import re
import unittest
from pathlib import Path

from _loader import load_script


ROOT = Path(__file__).resolve().parents[1]
DISPATCH = ROOT / "workspace/public/src/native-init/v319/80_shell_dispatch.inc.c"

runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3327_gpu_z3_imported_scanout_plane_present.py"
)


class NativeGpuZ3ImportedScanoutPlanePresentSourceV3327Tests(unittest.TestCase):
    def test_v3327_identity_and_required_markers(self) -> None:
        self.assertEqual(runner.CYCLE, "V3327")
        self.assertEqual(runner.INIT_VERSION, "0.11.95")
        self.assertEqual(runner.INIT_BUILD, "v3327-gpu-z3-imported-scanout-plane-present")
        self.assertEqual(
            runner.BOOT_IMAGE.name,
            "boot_linux_v3327_gpu_z3_imported_scanout_plane_present.img",
        )

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"0.11.95", required)
        self.assertIn(b"v3327-gpu-z3-imported-scanout-plane-present", required)
        self.assertIn(b"z3-imported-scanout-plane-probe", required)
        self.assertIn(b"gpu.z3.scanout.kms_copy_attempted=0", required)
        self.assertIn(b"gpu.z3.scanout.kms_present_attempted=1", required)
        self.assertIn(b"z3-imported-scanout-plane-present-pass", required)

    def test_z3_command_and_plane_present_contract(self) -> None:
        source = DISPATCH.read_text(encoding="utf-8")

        self.assertIn("z3-imported-scanout-plane-probe", source)
        self.assertIn("gpu.z3.scanout.present_mode=legacy-overlay-plane-setplane", source)
        self.assertIn("gpu.z3.scanout.kms_copy_attempted=0", source)
        self.assertIn("gpu.z3.scanout.kms_present_attempted=1", source)
        self.assertIn("gpu.z3.scanout.primary_pageflip_attempted=0", source)
        self.assertIn("DRM_IOCTL_MODE_SETPLANE", source)
        self.assertIn("gpu_z3_select_idle_xbgr_plane", source)
        self.assertIn("gpu_z3_present_imported_fb_on_plane", source)
        self.assertIn("gpu_z3_disable_present_plane", source)

    def test_z3_pass_gate_requires_import_render_and_plane_present(self) -> None:
        source = DISPATCH.read_text(encoding="utf-8")
        match = re.search(
            r"static bool gpu_z3_imported_scanout_present_summary_passed\(.*?^}\n",
            source,
            flags=re.DOTALL | re.MULTILINE,
        )
        self.assertIsNotNone(match)
        predicate = match.group(0)

        self.assertIn("gpu_z2_imported_target_summary_passed(summary)", predicate)
        self.assertIn("summary->kms_begin_rc == 0", predicate)
        self.assertIn("summary->kms_base_present_rc == 0", predicate)
        self.assertIn("summary->kms_info_initialized == 1", predicate)
        self.assertIn("summary->kms_plane_select_rc == 0", predicate)
        self.assertIn("summary->kms_present_rc == 0", predicate)
        self.assertIn("summary->hold_ms > 0U", predicate)
        self.assertIn("summary->kms_disable_plane_rc == 0", predicate)

    def test_builder_manifest_records_z3_contract(self) -> None:
        manifest = runner._minimal_gpu_z3_manifest()
        report = runner.render_report(
            {
                "decision": runner.DECISION,
                "boot_image": str(runner.BOOT_IMAGE),
                "boot_sha256": "0" * 64,
                "init_version": runner.INIT_VERSION,
                "init_build": runner.INIT_BUILD,
            },
            (),
            (),
        )

        self.assertEqual(manifest["expected_result"], "z3-imported-scanout-plane-present-pass")
        self.assertEqual(manifest["present_mode"], "legacy-overlay-plane-setplane")
        self.assertIn("kms-copy-attempted-0", manifest["pass_requirements"])
        self.assertIn("KMS plane selection", report)
        self.assertIn("CPU copy", report)


if __name__ == "__main__":
    unittest.main()
