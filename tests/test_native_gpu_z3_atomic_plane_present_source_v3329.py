from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


ROOT = Path(__file__).resolve().parents[1]
DISPATCH = ROOT / "workspace/public/src/native-init/v319/80_shell_dispatch.inc.c"

runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3329_gpu_z3_atomic_plane_present.py"
)


class NativeGpuZ3AtomicPlanePresentSourceV3329Tests(unittest.TestCase):
    def test_v3329_identity_and_required_markers(self) -> None:
        self.assertEqual(runner.CYCLE, "V3329")
        self.assertEqual(runner.INIT_VERSION, "0.11.97")
        self.assertEqual(runner.INIT_BUILD, "v3329-gpu-z3-atomic-plane-present")
        self.assertEqual(
            runner.BOOT_IMAGE.name,
            "boot_linux_v3329_gpu_z3_atomic_plane_present.img",
        )

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"0.11.97", required)
        self.assertIn(b"v3329-gpu-z3-atomic-plane-present", required)
        self.assertIn(b"gpu.z3.scanout.kms.atomic_props_rc=", required)
        self.assertIn(b"gpu.z3.scanout.kms.atomic_commit_rc=", required)

    def test_atomic_commit_helpers_are_present(self) -> None:
        source = DISPATCH.read_text(encoding="utf-8")

        self.assertIn("struct gpu_z3_atomic_plane_props", source)
        self.assertIn("gpu_z3_fetch_atomic_plane_props", source)
        self.assertIn("gpu_z3_atomic_commit_imported_fb_on_plane", source)
        self.assertIn("DRM_IOCTL_MODE_ATOMIC", source)
        self.assertIn("DRM_IOCTL_MODE_SETPLANE", source)
        self.assertIn("summary->kms_atomic_commit_rc = rc", source)

    def test_builder_manifest_records_atomic_fix(self) -> None:
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
            manifest["plane_present_fix"],
            "atomic-plane-commit-first-with-legacy-setplane-fallback",
        )
        self.assertIn("DRM_IOCTL_MODE_ATOMIC", report)
        self.assertIn("SETPLANE", report)


if __name__ == "__main__":
    unittest.main()
