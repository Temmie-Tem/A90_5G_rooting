"""Tests for the V2584 ACDB pre-init store_get live runner."""

from __future__ import annotations

import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

from _loader import load_revalidation

v2584 = load_revalidation("native_audio_acdb_preinit_store_get_live_handoff_v2584")


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def args(**overrides: object) -> Namespace:
    root = Path(tempfile.mkdtemp(prefix="a90-v2584-test-"))
    defaults: dict[str, object] = {
        "dry_run": False,
        "run_live": False,
        "write_report": False,
        "report_path": root / "report.md",
        "exact_gate": None,
        "build_v2583_artifacts": False,
        "v2583_build_root": root / "build-v2583",
        "v2583_manifest_path": root / "build-v2583/manifest.json",
        "helper_path": None,
        "helper_sha256": None,
        "preload_so": None,
        "preload_sha256": None,
        "out_dir": root / "run",
        "adb": "adb",
        "serial": None,
        "from_native": True,
        "android_timeout": 240.0,
        "flash_timeout": 420.0,
        "adb_command_timeout": 90.0,
        "adb_pull_timeout": 120.0,
        "helper_timeout": 90.0,
        "android_root_recheck_attempts": 1,
        "android_root_recheck_sleep_sec": 0.0,
        "android_settle_adb_retry_attempts": 1,
        "android_settle_adb_retry_sleep_sec": 0.0,
        "readelf": "readelf",
        "file": "file",
    }
    defaults.update(overrides)
    return Namespace(**defaults)


class NativeAudioAcdbPreinitStoreGetLiveHandoffV2584(unittest.TestCase):
    def test_to_v2490_args_maps_v2583_preload_to_ioctl_slot(self) -> None:
        local = args()
        artifacts = {
            "helper": {"path": "workspace/private/builds/audio/x/bin/helper", "sha256": "a" * 64},
            "preload": {"path": "workspace/private/builds/audio/x/bin/preload.so", "sha256": "b" * 64},
        }

        base = v2584.to_v2490_args(local, artifacts)

        self.assertFalse(base.use_combined_preload)
        self.assertFalse(base.enable_acdbtap_preload)
        self.assertFalse(base.disable_ioctl_trace)
        self.assertTrue(base.fake_audio_cal_allocate)
        self.assertEqual(base.helper_sha256, "a" * 64)
        self.assertEqual(base.ioctl_trace_sha256, "b" * 64)

    def test_live_requires_exact_gate(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "exact gate"):
            v2584.require_live_gate(args(exact_gate="wrong"))
        v2584.require_live_gate(args(exact_gate=v2584.EXACT_GATE))

    def test_helper_command_uses_v2583_context_and_fake_allocate(self) -> None:
        command = v2584.run_helper_command(args())
        flat = " ".join(command)

        self.assertIn("V2583_PREINIT_STORE_GET=enabled", flat)
        self.assertIn("A90_ACDB_FAKE_ALLOCATE=1", flat)
        self.assertIn("LD_PRELOAD=/data/local/tmp/a90-acdb-ownget/liba90_ioctl_trace_v2531.so", flat)
        self.assertIn("acdb-v2583-preinit-storeget-events.jsonl", flat)
        self.assertNotIn("V2580_STORE_GET_GO", flat)

    def test_summary_accepts_nonzero_case_return_metadata(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="a90-v2584-summary-ok-"))
        write_jsonl(root / "acdb-v2583-preinit-storeget-events.jsonl", [
            {"event": "v2583_preinit_store_get", "stage": "entered_common_topology_hook", "code": 0},
            {"event": "v2583_preinit_store_get", "stage": "before_store_get_cases", "code": 0},
            {"event": "v2583_preinit_store_get", "stage": "case_return", "case": "store_selector_37", "selector": 37, "instance": 0, "ret": 0, "out_len": 64, "all_zero": False, "fnv1a32": "0x12345678"},
        ])

        summary = v2584.summarize_v2583_probe(root)

        self.assertEqual(summary["classification"], "v2584-preinit-storeget-nonzero-metadata-captured")
        self.assertTrue(summary["success"])
        self.assertEqual(summary["store_get"]["success_count"], 1)

    def test_summary_rejects_zero_case_return_metadata(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="a90-v2584-summary-zero-"))
        write_jsonl(root / "acdb-v2583-preinit-storeget-events.jsonl", [
            {"event": "v2583_preinit_store_get", "stage": "case_return", "case": "store_selector_37", "selector": 37, "instance": 0, "ret": 0, "out_len": 4916, "all_zero": True, "fnv1a32": "0x00000000"},
        ])

        summary = v2584.summarize_v2583_probe(root)

        self.assertEqual(summary["classification"], "v2584-preinit-storeget-case-returns-no-nonzero")
        self.assertFalse(summary["success"])

    def test_summary_reports_init_entered_no_hook(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="a90-v2584-summary-init-"))
        write_jsonl(root / "acdb-v2583-init-driver-events.jsonl", [
            {"event": "v2583_init_driver", "stage": "start", "code": 0},
            {"event": "v2583_init_driver", "stage": "before_init_v3", "code": 0},
        ])

        summary = v2584.summarize_v2583_probe(root)

        self.assertEqual(summary["classification"], "v2584-preinit-storeget-init-entered-no-hook")
        self.assertFalse(summary["success"])


if __name__ == "__main__":
    unittest.main()
