from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


ROOT = Path(__file__).resolve().parents[1]
DISPATCH = ROOT / "workspace/public/src/native-init/v319/80_shell_dispatch.inc.c"

runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3334_gpu_z3_atomic_allow_modeset.py"
)


class NativeGpuZ3AtomicAllowModesetSourceV3334Tests(unittest.TestCase):
    def test_v3334_identity_and_required_markers(self) -> None:
        self.assertEqual(runner.CYCLE, "V3334")
        self.assertEqual(runner.INIT_VERSION, "0.11.102")
        self.assertEqual(runner.INIT_BUILD, "v3334-gpu-z3-atomic-allow-modeset")
        self.assertEqual(
            runner.BOOT_IMAGE.name,
            "boot_linux_v3334_gpu_z3_atomic_allow_modeset.img",
        )

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"0.11.102", required)
        self.assertIn(b"v3334-gpu-z3-atomic-allow-modeset", required)
        self.assertIn(b"gpu.z3.scanout.kms.atomic_optional_count=", required)
        self.assertIn(b"gpu.z3.scanout.kms.atomic_flags=0x", required)
        self.assertIn(b"gpu.z3.scanout.kms.plane_modifier", required)
        self.assertIn(b"idle_xbgr_linear=", required)
        self.assertIn(b"selected_linear=", required)
        self.assertIn(b"zpos_prop=", required)
        self.assertIn(b"alpha_prop=", required)
        self.assertIn(b"rotation_prop=", required)
        self.assertIn(b"pixel_blend_prop=", required)

    def test_selector_requires_linear_overlay_modifier(self) -> None:
        source = DISPATCH.read_text(encoding="utf-8")

        self.assertIn("gpu_z3_parse_in_formats_blob", source)
        self.assertIn("DRM_FORMAT_MOD_LINEAR", source)
        self.assertIn("modifiers.xbgr_linear", source)
        self.assertIn("summary->kms_plane_idle_xbgr_linear_count += 1U", source)
        self.assertIn("summary->kms_plane_selected_xbgr_linear", source)
        self.assertIn("gpu.z3.scanout.kms.plane_modifier", source)

    def test_atomic_commit_sets_pixel_blend_none(self) -> None:
        source = DISPATCH.read_text(encoding="utf-8")

        self.assertIn('strcmp(name, "zpos") == 0', source)
        self.assertIn('strcmp(name, "alpha") == 0', source)
        self.assertIn('strcmp(name, "rotation") == 0', source)
        self.assertIn('strcmp(name, "pixel blend mode") == 0', source)
        self.assertIn("prop_values[index++] = 1U;", source)
        self.assertIn("prop_values[index++] = 0xffffU;", source)
        self.assertIn("props->pixel_blend_mode", source)
        self.assertIn("summary->kms_atomic_pixel_blend_mode_prop", source)
        self.assertIn("summary->kms_atomic_optional_count += 1", source)
        self.assertIn("gpu.z3.scanout.kms.atomic_optional_count=", source)

    def test_atomic_commit_allows_modeset_and_reports_flags(self) -> None:
        source = DISPATCH.read_text(encoding="utf-8")

        self.assertIn("atomic.flags = DRM_MODE_ATOMIC_ALLOW_MODESET;", source)
        self.assertIn("summary->kms_atomic_flags = atomic.flags;", source)
        self.assertIn("gpu.z3.scanout.kms.atomic_flags=0x", source)

    def test_builder_manifest_records_atomic_allow_modeset_fix(self) -> None:
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
            manifest["atomic_allow_modeset_fix"],
            "set-drm-mode-atomic-allow-modeset-for-overlay-attach",
        )
        self.assertIn("DRM_MODE_ATOMIC_ALLOW_MODESET", report)
        self.assertIn("atomic_flags=0x", report)


if __name__ == "__main__":
    unittest.main()
