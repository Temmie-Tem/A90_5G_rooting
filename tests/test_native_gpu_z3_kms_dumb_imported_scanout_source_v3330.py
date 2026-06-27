from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


ROOT = Path(__file__).resolve().parents[1]
DISPATCH = ROOT / "workspace/public/src/native-init/v319/80_shell_dispatch.inc.c"

runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3330_gpu_z3_kms_dumb_imported_scanout.py"
)


class NativeGpuZ3KmsDumbImportedScanoutSourceV3330Tests(unittest.TestCase):
    def test_v3330_identity_and_required_markers(self) -> None:
        self.assertEqual(runner.CYCLE, "V3330")
        self.assertEqual(runner.INIT_VERSION, "0.11.98")
        self.assertEqual(runner.INIT_BUILD, "v3330-gpu-z3-kms-dumb-imported-scanout")
        self.assertEqual(
            runner.BOOT_IMAGE.name,
            "boot_linux_v3330_gpu_z3_kms_dumb_imported_scanout.img",
        )

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"0.11.98", required)
        self.assertIn(b"v3330-gpu-z3-kms-dumb-imported-scanout", required)
        self.assertIn(
            b"kms-dumb-scanout-gem-prime-fd-kgsl-dmabuf-import",
            required,
        )
        self.assertIn(b"gpu.z3.scanout.drm.dumb_create_rc=", required)
        self.assertIn(b"gpu.z3.scanout.drm.dumb_map_offset_rc=", required)

    def test_z3_uses_kms_dumb_buffer_before_kgsl_import(self) -> None:
        source = DISPATCH.read_text(encoding="utf-8")

        self.assertIn("DRM_IOCTL_MODE_CREATE_DUMB", source)
        self.assertIn("DRM_IOCTL_MODE_MAP_DUMB", source)
        self.assertIn("DRM_IOCTL_MODE_DESTROY_DUMB", source)
        self.assertIn("GPU_Z3_BUFFER_KIND_KMS_DUMB", source)
        self.assertIn("use_kms_dumb_target = present_external", source)
        self.assertIn("gpu_z3_kms_dumb_imported_target_summary_passed", source)
        self.assertIn("DRM_IOCTL_PRIME_HANDLE_TO_FD", source)
        self.assertIn("DRM_IOCTL_MODE_ATOMIC", source)

    def test_builder_manifest_records_dumb_scanout_fix(self) -> None:
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
            manifest["scanout_target_fix"],
            "kms-dumb-fb-prime-imported-into-kgsl",
        )
        self.assertIn("KMS-native dumb framebuffer", report)
        self.assertIn("PRIME", report)


if __name__ == "__main__":
    unittest.main()
