import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "workspace" / "public" / "src" / "scripts" / "revalidation"))

import build_native_init_boot_v3357_self_dd_f0_plan as runner  # noqa: E402


class NativeSelfDdF0PlanSourceV3357Test(unittest.TestCase):
    def test_required_strings_cover_read_only_f0_contract(self) -> None:
        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"0.11.120", required)
        self.assertIn(b"v3357-self-dd-f0-plan", required)
        self.assertIn(b"A90BWF0", required)
        self.assertIn(b"boot-flash-plan <candidate-path> <expected-sha256> <expected-version>", required)
        self.assertIn(b"read-only-source-plan would_write=0", required)
        self.assertIn(b"candidate_sha=%s expected_sha_match=%d", required)
        self.assertIn(b"target_full_sha=%s", required)
        self.assertIn(b"result=ok source-plan-only", required)

    def test_report_states_no_live_result_claimed(self) -> None:
        manifest = {
            "boot_image": "workspace/private/inputs/boot_images/boot_linux_v3357_self_dd_f0_plan.img",
            "boot_sha256": "0" * 64,
            "helper_sha256": "1" * 64,
        }
        report = runner.render_report(manifest, ("flag-a",), ("flag-b",))
        self.assertIn("Decision: `v3357-self-dd-f0-plan-source-build-pass`", report)
        self.assertIn("F0 performs no boot-partition write", report)
        self.assertIn("no live V3357 source-plan result is claimed here", report)


if __name__ == "__main__":
    unittest.main()
