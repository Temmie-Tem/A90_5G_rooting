from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


ROOT = Path(__file__).resolve().parents[1]
DISPATCH = ROOT / "workspace/public/src/native-init/v319/80_shell_dispatch.inc.c"

runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3325_gpu_z2_imported_scanout_target.py"
)


class NativeGpuZ2ImportedScanoutTargetSourceV3325Tests(unittest.TestCase):
    def test_v3325_identity_and_required_markers(self) -> None:
        self.assertEqual(runner.CYCLE, "V3325")
        self.assertEqual(runner.INIT_VERSION, "0.11.93")
        self.assertEqual(runner.INIT_BUILD, "v3325-gpu-z2-imported-scanout-target")
        self.assertEqual(
            runner.BOOT_IMAGE.name,
            "boot_linux_v3325_gpu_z2_imported_scanout_target.img",
        )

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"0.11.93", required)
        self.assertIn(b"v3325-gpu-z2-imported-scanout-target", required)
        self.assertIn(b"z2-imported-scanout-target-probe", required)
        self.assertIn(b"gpu.z2.import.scope=gpu-z2-imported-scanout-render-target", required)
        self.assertIn(b"gpu.z2.import.buffer=drm-msm-scanout-gem-prime-fd-kgsl-dmabuf-import", required)
        self.assertIn(b"gpu.z2.import.kms_copy_attempted=0", required)
        self.assertIn(b"gpu.z2.import.kms_present_attempted=0", required)
        self.assertIn(b"z2-imported-scanout-render-target-pass", required)

    def test_dispatch_contains_imported_scanout_target_probe(self) -> None:
        source = DISPATCH.read_text(encoding="utf-8")

        self.assertIn('strcmp(subcommand, "z2-imported-scanout-target-probe") == 0', source)
        self.assertIn("gpu_z2_imported_scanout_target_probe", source)
        self.assertIn("gpu_z2_imported_scanout_target_child", source)
        self.assertIn("DRM_IOCTL_MSM_GEM_NEW", source)
        self.assertIn("MSM_BO_SCANOUT | MSM_BO_WC", source)
        self.assertIn("DRM_IOCTL_PRIME_HANDLE_TO_FD", source)
        self.assertIn("DRM_IOCTL_MODE_ADDFB2", source)
        self.assertIn("GPU_IOCTL_KGSL_GPUOBJ_IMPORT", source)
        self.assertIn("GPU_KGSL_USER_MEM_TYPE_DMABUF", source)
        self.assertIn("gpu_2d_present_create_session_internal", source)
        self.assertIn("gpu_2d_present_render_frame_to_linear", source)
        self.assertIn("gpu_2d_present_sample_linear", source)
        self.assertIn("gpu.z2.import.kms_copy_attempted=0", source)
        self.assertIn("gpu.z2.import.kms_present_attempted=0", source)
        self.assertIn("gpu.z2.import.kgsl_submit_attempted=1", source)
        self.assertIn("gpu.z2.import.kms_adfb2_attempted=1", source)
        self.assertIn("z2-imported-scanout-render-target-pass", source)
        self.assertIn("z2-imported-scanout-target-probe [--timeout-ms N] [--materialize-devnode]", source)

    def test_builder_manifest_records_z2_validation(self) -> None:
        manifest = runner._minimal_gpu_z2_manifest()
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

        self.assertEqual(manifest["scope"], "gpu-z2-imported-scanout-render-target")
        self.assertEqual(
            manifest["command"],
            "gpu z2-imported-scanout-target-probe --timeout-ms 60000 --materialize-devnode",
        )
        self.assertEqual(manifest["expected_result"], "z2-imported-scanout-render-target-pass")
        self.assertFalse(manifest["copy_attempted"])
        self.assertFalse(manifest["kms_present_attempted"])
        self.assertTrue(manifest["kms_addfb2_attempted"])
        self.assertTrue(manifest["kgsl_submit_attempted"])
        self.assertIn("require-kms-addfb2-success", manifest["pass_requirements"])
        self.assertIn("require-kgsl-dmabuf-import-success", manifest["pass_requirements"])
        self.assertIn("require-no-kms-copy", manifest["pass_requirements"])
        self.assertIn("require-no-kms-present", manifest["pass_requirements"])
        self.assertIn("imported scanout GEM", report)
        self.assertIn("does not copy", report)
        self.assertIn("does not present/pageflip yet", report)


if __name__ == "__main__":
    unittest.main()
