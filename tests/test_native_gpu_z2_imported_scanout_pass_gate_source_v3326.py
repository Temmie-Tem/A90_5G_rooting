from __future__ import annotations

import re
import unittest
from pathlib import Path

from _loader import load_script


ROOT = Path(__file__).resolve().parents[1]
DISPATCH = ROOT / "workspace/public/src/native-init/v319/80_shell_dispatch.inc.c"

runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3326_gpu_z2_imported_scanout_pass_gate.py"
)


class NativeGpuZ2ImportedScanoutPassGateSourceV3326Tests(unittest.TestCase):
    def test_v3326_identity_and_required_markers(self) -> None:
        self.assertEqual(runner.CYCLE, "V3326")
        self.assertEqual(runner.INIT_VERSION, "0.11.94")
        self.assertEqual(runner.INIT_BUILD, "v3326-gpu-z2-imported-scanout-pass-gate")
        self.assertEqual(
            runner.BOOT_IMAGE.name,
            "boot_linux_v3326_gpu_z2_imported_scanout_pass_gate.img",
        )

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"0.11.94", required)
        self.assertIn(b"v3326-gpu-z2-imported-scanout-pass-gate", required)
        self.assertIn(b"z2-imported-scanout-target-probe", required)
        self.assertIn(b"gpu.z2.import.kms_copy_attempted=0", required)
        self.assertIn(b"z2-imported-scanout-render-target-pass", required)

    def test_pass_gate_no_longer_self_references_result_rc(self) -> None:
        source = DISPATCH.read_text(encoding="utf-8")
        match = re.search(
            r"static bool gpu_z2_imported_target_summary_passed\(.*?^}\n",
            source,
            flags=re.DOTALL | re.MULTILINE,
        )
        self.assertIsNotNone(match)
        predicate = match.group(0)

        self.assertNotIn("summary->result_rc == 0", predicate)
        self.assertIn("summary->drm_addfb2_rc == 0", predicate)
        self.assertIn("summary->kgsl_import_rc == 0", predicate)
        self.assertIn("summary->render_rc == 0", predicate)
        self.assertIn("summary->changed_count > 0ULL", predicate)
        self.assertIn("summary->semantic_sample_match_count == GPU_D1_CHECKER_SAMPLE_COUNT", predicate)
        self.assertIn("summary->semantic_output_other_count == 0U", predicate)

    def test_builder_manifest_records_pass_gate_fix(self) -> None:
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

        self.assertEqual(manifest["expected_result"], "z2-imported-scanout-render-target-pass")
        self.assertEqual(
            manifest["pass_gate_fix"],
            "remove-result_rc-self-reference-before-final-result-assignment",
        )
        self.assertIn("V3325 live telemetry", report)
        self.assertIn("result_rc", report)
        self.assertIn("self-reference", report)


if __name__ == "__main__":
    unittest.main()
