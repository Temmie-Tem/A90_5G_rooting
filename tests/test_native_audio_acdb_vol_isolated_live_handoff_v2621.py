"""Tests for the V2621 ACDB VOL-isolated live wrapper."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from _loader import load_revalidation

v2621 = load_revalidation("native_audio_acdb_vol_isolated_live_handoff_v2621")


def args(**overrides: object) -> argparse.Namespace:
    root = Path(tempfile.mkdtemp(prefix="a90-v2621-test-"))
    defaults: dict[str, object] = {
        "dry_run": True,
        "run_live": False,
        "write_report": False,
        "report_path": root / "report.md",
        "build_v2620_artifacts": False,
        "v2620_build_root": v2621.v2620.DEFAULT_BUILD_ROOT,
        "v2620_manifest_path": v2621.v2620.DEFAULT_MANIFEST,
        "helper_path": None,
        "helper_sha256": None,
        "preload_path": None,
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
        "android_root_recheck_attempts": v2621.v2490.v2396.DEFAULT_ANDROID_ROOT_RECHECK_ATTEMPTS,
        "android_root_recheck_sleep_sec": v2621.v2490.v2396.DEFAULT_ANDROID_ROOT_RECHECK_SLEEP_SEC,
        "android_settle_adb_retry_attempts": v2621.v2490.DEFAULT_SETTLE_ADB_RETRY_ATTEMPTS,
        "android_settle_adb_retry_sleep_sec": v2621.v2490.DEFAULT_SETTLE_ADB_RETRY_SLEEP_SEC,
        "readelf": "readelf",
        "file": "file",
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


class NativeAudioAcdbVolIsolatedLiveHandoffV2621(unittest.TestCase):
    def test_read_v2620_manifest_checks_vol_contract(self) -> None:
        manifest = v2621.read_v2620_manifest(v2621.v2620.DEFAULT_MANIFEST)

        self.assertTrue(manifest["ok"], manifest)
        self.assertTrue(manifest["vol_isolated_contract_ok"], manifest)
        self.assertTrue(manifest["armed_contract_ok"], manifest)

    def test_summarize_vol_isolated_capture_counts_indirect_gain_payload(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="a90-v2621-summary-"))
        acdbtap = root / "acdbtap"
        acdbtap.mkdir(parents=True, exist_ok=True)
        raw_gain = acdbtap / "acdbtap-00000007-cmd-0001326e-len-00000020-ind-ap-gain.bin"
        raw_gain.write_bytes(b"G" * 32)
        raw_size = acdbtap / "acdbtap-00000006-cmd-0001326d-len-00000004-out.bin"
        raw_size.write_bytes((32).to_bytes(4, "little"))
        write_jsonl(
            acdbtap / "acdbtap-events.jsonl",
            [
                {
                    "event": "acdb_ioctl",
                    "seq": 6,
                    "cmd": "0x0001326d",
                    "in_len": 12,
                    "out_len": 4,
                    "ret": 0,
                    "buffer": "out",
                    "raw_path": str(raw_size),
                    "sha256": hashlib.sha256(raw_size.read_bytes()).hexdigest(),
                },
                {
                    "event": "acdb_ioctl",
                    "seq": 7,
                    "cmd": "0x0001326e",
                    "in_len": 20,
                    "out_len": 32,
                    "ret": 0,
                    "buffer": "ind-ap-gain",
                    "raw_path": str(raw_gain),
                    "sha256": hashlib.sha256(raw_gain.read_bytes()).hexdigest(),
                },
            ],
        )
        helper_rows = [
            {"event": "v2620_vol_isolated", "stage": "before_safe_prelude", "code": 0},
            {"event": "v2620_vol_isolated", "stage": "before_vol_sweep", "code": 0},
            {"event": "v2620_vol_isolated", "stage": "case_return", "case": "vol-size", "cmd": "0x0001326d", "step": 0, "ret": 0, "out_word": "0x00000020"},
            {"event": "v2620_vol_isolated", "stage": "case_return", "case": "vol-data", "cmd": "0x0001326e", "step": 0, "ret": 0, "out_word": "0x00000020"},
            {"event": "v2620_vol_isolated", "stage": "done", "code": 0},
        ]
        write_jsonl(root / "acdb-v2620-vol-isolated-events.jsonl", helper_rows)

        summary = v2621.summarize_vol_isolated_capture(root)

        self.assertEqual(summary["classification"], "v2621-vol-isolated-vol-captured")
        self.assertTrue(summary["operator_valuable"])
        self.assertTrue(summary["success"])
        self.assertEqual(summary["vol_size_case_count"], 1)
        self.assertEqual(summary["vol_data_case_count"], 1)
        self.assertEqual(summary["vol_payload_count"], 1)

    def test_dry_run_uses_v2490_engine_with_v2620_artifacts(self) -> None:
        payload = v2621.dry_run_payload(args())

        self.assertTrue(payload["ok"], payload.get("live_blockers"))
        self.assertTrue(payload["capture_contract"]["manual_arm_after_init"])
        self.assertFalse(payload["capture_contract"]["auto_arm_on_initialize"])
        self.assertFalse(payload["capture_contract"]["exit_on_first_4916"])
        self.assertTrue(payload["v2620_artifacts"]["ok"])
        self.assertTrue(payload["v2490_engine"]["live_ready"])


if __name__ == "__main__":
    unittest.main()
