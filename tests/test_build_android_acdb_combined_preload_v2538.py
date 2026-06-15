"""Host-only tests for the V2538 combined ACDB preload build."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

from _loader import load_revalidation

v2538 = load_revalidation("build_android_acdb_combined_preload_v2538")


def args(**overrides: object) -> Namespace:
    root = Path(tempfile.mkdtemp(prefix="a90-v2538-test-"))
    defaults: dict[str, object] = {
        "build": False,
        "build_root": root / "build",
        "manifest_path": root / "build/manifest.json",
        "clang": None,
        "lld": v2538.TOOLCHAIN_ROOT / "bin/ld.lld",
        "readelf": str(v2538.TOOLCHAIN_ROOT / "bin/llvm-readelf"),
        "file": "file",
    }
    defaults.update(overrides)
    return Namespace(**defaults)


class BuildAndroidAcdbCombinedPreloadV2538(unittest.TestCase):
    def test_source_state_combines_acdbtap_and_ioctl_trace_boundaries(self) -> None:
        state = v2538.source_state()

        self.assertTrue(state["required_ok"], state["required"])
        self.assertTrue(state["prohibited_ok"], state["prohibited"])
        self.assertTrue(state["required"]["tap_exports_acdb_ioctl"])
        self.assertTrue(state["required"]["ioctl_exports_ioctl"])
        self.assertTrue(state["required"]["ioctl_fake_allocate_mode"])
        self.assertTrue(state["required"]["tap_target_len_4916"])

    def test_dry_run_is_host_only_and_single_preload_boundary(self) -> None:
        payload = v2538.manifest(args())

        self.assertTrue(payload["ok"])
        self.assertTrue(payload["host_only"])
        self.assertEqual(payload["device_action"], "none")
        self.assertEqual(payload["android_action"], "none")
        self.assertTrue(payload["boundaries"]["single_preload_library"])
        self.assertTrue(payload["boundaries"]["exports_acdb_ioctl_and_ioctl"])
        self.assertTrue(payload["boundaries"]["does_not_issue_extra_ioctl"])
        self.assertIn("two-LD_PRELOAD", payload["v2537_delta"])

    @unittest.skipUnless(
        (v2538.TOOLCHAIN_ROOT / "bin/clang").exists() and (v2538.TOOLCHAIN_ROOT / "bin/ld.lld").exists(),
        "private Android clang/lld unavailable",
    )
    def test_build_outputs_single_arm32_shared_object_with_both_exports(self) -> None:
        payload = v2538.manifest(args(build=True))
        binary = payload["build"]["binary"]

        self.assertTrue(payload["ok"], payload)
        self.assertIn("ELF 32-bit LSB shared object, ARM", binary["file"]["stdout"])
        self.assertTrue(binary["symbols"]["exports_acdb_ioctl"])
        self.assertTrue(binary["symbols"]["exports_ioctl"])
        self.assertTrue(binary["symbols"]["undefined_dlsym"])
        self.assertTrue(binary["symbols"]["undefined_errno"])
        self.assertEqual(binary["mode"], "0o600")
        self.assertEqual(len(binary["sha256"]), 64)

    def test_cli_writes_manifest(self) -> None:
        local_args = args()
        completed = subprocess.run(
            [
                sys.executable,
                "workspace/public/src/scripts/revalidation/build_android_acdb_combined_preload_v2538.py",
                "--build-root",
                str(local_args.build_root),
                "--manifest-path",
                str(local_args.manifest_path),
            ],
            cwd=v2538.ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["ok"])
        self.assertTrue(local_args.manifest_path.exists())


if __name__ == "__main__":
    unittest.main()
