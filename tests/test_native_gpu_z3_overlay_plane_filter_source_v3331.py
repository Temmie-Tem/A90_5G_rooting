from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


ROOT = Path(__file__).resolve().parents[1]
DISPATCH = ROOT / "workspace/public/src/native-init/v319/80_shell_dispatch.inc.c"

runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3331_gpu_z3_overlay_plane_filter.py"
)


class NativeGpuZ3OverlayPlaneFilterSourceV3331Tests(unittest.TestCase):
    def test_v3331_identity_and_required_markers(self) -> None:
        self.assertEqual(runner.CYCLE, "V3331")
        self.assertEqual(runner.INIT_VERSION, "0.11.99")
        self.assertEqual(runner.INIT_BUILD, "v3331-gpu-z3-overlay-plane-filter")
        self.assertEqual(
            runner.BOOT_IMAGE.name,
            "boot_linux_v3331_gpu_z3_overlay_plane_filter.img",
        )

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"0.11.99", required)
        self.assertIn(b"v3331-gpu-z3-overlay-plane-filter", required)
        self.assertIn(b"overlay=", required)
        self.assertIn(b"selected_type=", required)

    def test_plane_selection_filters_overlay_type(self) -> None:
        source = DISPATCH.read_text(encoding="utf-8")

        self.assertIn("GPU_Z3_DRM_PLANE_TYPE_OVERLAY", source)
        self.assertIn("GPU_Z3_DRM_PLANE_TYPE_CURSOR", source)
        self.assertIn("gpu_z3_fetch_plane_type", source)
        self.assertIn('strcmp(prop.name, "type") == 0', source)
        self.assertIn("overlay = plane_type == GPU_Z3_DRM_PLANE_TYPE_OVERLAY", source)
        self.assertIn("idle && xbgr && overlay", source)
        self.assertIn("summary->kms_plane_selected_type = plane_type", source)

    def test_builder_manifest_records_overlay_filter(self) -> None:
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
            manifest["plane_select_fix"],
            "filter-plane-type-overlay-and-report-selected-type",
        )
        self.assertIn("DRM_PLANE_TYPE_OVERLAY", report)
        self.assertIn("selected type", report)


if __name__ == "__main__":
    unittest.main()
