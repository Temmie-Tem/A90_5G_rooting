from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


ROOT = Path(__file__).resolve().parents[1]
DISPATCH = ROOT / "workspace/public/src/native-init/v319/80_shell_dispatch.inc.c"

runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3332_gpu_z3_overlay_atomic_state.py"
)


class NativeGpuZ3OverlayAtomicStateSourceV3332Tests(unittest.TestCase):
    def test_v3332_identity_and_required_markers(self) -> None:
        self.assertEqual(runner.CYCLE, "V3332")
        self.assertEqual(runner.INIT_VERSION, "0.11.100")
        self.assertEqual(runner.INIT_BUILD, "v3332-gpu-z3-overlay-atomic-state")
        self.assertEqual(
            runner.BOOT_IMAGE.name,
            "boot_linux_v3332_gpu_z3_overlay_atomic_state.img",
        )

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"0.11.100", required)
        self.assertIn(b"v3332-gpu-z3-overlay-atomic-state", required)
        self.assertIn(b"gpu.z3.scanout.kms.atomic_optional_count=", required)
        self.assertIn(b"zpos_prop=", required)
        self.assertIn(b"alpha_prop=", required)
        self.assertIn(b"rotation_prop=", required)

    def test_atomic_commit_sets_optional_overlay_state(self) -> None:
        source = DISPATCH.read_text(encoding="utf-8")

        self.assertIn('strcmp(name, "zpos") == 0', source)
        self.assertIn('strcmp(name, "alpha") == 0', source)
        self.assertIn('strcmp(name, "rotation") == 0', source)
        self.assertIn("prop_values[index++] = 1U;", source)
        self.assertIn("prop_values[index++] = 0xffffU;", source)
        self.assertIn("summary->kms_atomic_optional_count += 1", source)
        self.assertIn("gpu.z3.scanout.kms.atomic_optional_count=", source)

    def test_builder_manifest_records_optional_atomic_state(self) -> None:
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
            manifest["atomic_state_fix"],
            "set-overlay-zpos-alpha-rotation-when-properties-exist",
        )
        self.assertIn("zpos=1", report)
        self.assertIn("alpha=0xffff", report)


if __name__ == "__main__":
    unittest.main()
