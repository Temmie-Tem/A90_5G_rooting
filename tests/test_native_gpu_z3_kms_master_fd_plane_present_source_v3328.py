from __future__ import annotations

import re
import unittest
from pathlib import Path

from _loader import load_script


ROOT = Path(__file__).resolve().parents[1]
DISPATCH = ROOT / "workspace/public/src/native-init/v319/80_shell_dispatch.inc.c"
KMS_C = ROOT / "workspace/public/src/native-init/a90_kms.c"
KMS_H = ROOT / "workspace/public/src/native-init/a90_kms.h"

runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3328_gpu_z3_kms_master_fd_plane_present.py"
)


class NativeGpuZ3KmsMasterFdPlanePresentSourceV3328Tests(unittest.TestCase):
    def test_v3328_identity_and_required_markers(self) -> None:
        self.assertEqual(runner.CYCLE, "V3328")
        self.assertEqual(runner.INIT_VERSION, "0.11.96")
        self.assertEqual(runner.INIT_BUILD, "v3328-gpu-z3-kms-master-fd-plane-present")
        self.assertEqual(
            runner.BOOT_IMAGE.name,
            "boot_linux_v3328_gpu_z3_kms_master_fd_plane_present.img",
        )

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"0.11.96", required)
        self.assertIn(b"v3328-gpu-z3-kms-master-fd-plane-present", required)
        self.assertIn(b"z3-imported-scanout-plane-probe", required)
        self.assertIn(b"gpu.z3.scanout.kms_copy_attempted=0", required)

    def test_kms_master_fd_is_exported_and_used_for_z3(self) -> None:
        dispatch = DISPATCH.read_text(encoding="utf-8")
        kms_c = KMS_C.read_text(encoding="utf-8")
        kms_h = KMS_H.read_text(encoding="utf-8")

        self.assertIn("int a90_kms_drm_fd(void);", kms_h)
        self.assertIn("int a90_kms_drm_fd(void)", kms_c)
        self.assertIn("return kms_state.fd;", kms_c)
        self.assertIn("drm_fd = a90_kms_drm_fd();", dispatch)
        self.assertIn("drm_fd_owned = false;", dispatch)
        self.assertIn("DRM_IOCTL_MODE_SETPLANE", dispatch)

    def test_z3_pass_gate_still_requires_plane_present(self) -> None:
        source = DISPATCH.read_text(encoding="utf-8")
        match = re.search(
            r"static bool gpu_z3_imported_scanout_present_summary_passed\(.*?^}\n",
            source,
            flags=re.DOTALL | re.MULTILINE,
        )
        self.assertIsNotNone(match)
        predicate = match.group(0)

        self.assertIn("gpu_z2_imported_target_summary_passed(summary)", predicate)
        self.assertIn("summary->kms_plane_select_rc == 0", predicate)
        self.assertIn("summary->kms_present_rc == 0", predicate)
        self.assertIn("summary->kms_disable_plane_rc == 0", predicate)

    def test_builder_manifest_records_eacces_fix(self) -> None:
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

        self.assertEqual(
            manifest["fd_fix"],
            "reuse-a90-kms-master-fd-for-drm-gem-addfb2-and-setplane",
        )
        self.assertIn("EACCES", report)
        self.assertIn("KMS master fd", report)


if __name__ == "__main__":
    unittest.main()
