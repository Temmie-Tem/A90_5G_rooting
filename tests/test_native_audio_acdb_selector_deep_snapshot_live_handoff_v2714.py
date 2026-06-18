"""Tests for the V2714 selector deep-snapshot live wrapper."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from _loader import load_revalidation

v2714 = load_revalidation("native_audio_acdb_selector_deep_snapshot_live_handoff_v2714")


def args(**overrides: object) -> argparse.Namespace:
    root = Path(tempfile.mkdtemp(prefix="a90-v2714-test-"))
    defaults: dict[str, object] = {
        "dry_run": True,
        "run_live": False,
        "write_report": False,
        "report_path": root / "report.md",
        "build_v2713_artifacts": False,
        "v2713_build_root": v2714.v2713.DEFAULT_BUILD_ROOT,
        "v2713_manifest_path": v2714.v2713.DEFAULT_MANIFEST,
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
        "android_root_recheck_attempts": v2714.v2490.v2396.DEFAULT_ANDROID_ROOT_RECHECK_ATTEMPTS,
        "android_root_recheck_sleep_sec": v2714.v2490.v2396.DEFAULT_ANDROID_ROOT_RECHECK_SLEEP_SEC,
        "android_settle_adb_retry_attempts": v2714.v2490.DEFAULT_SETTLE_ADB_RETRY_ATTEMPTS,
        "android_settle_adb_retry_sleep_sec": v2714.v2490.DEFAULT_SETTLE_ADB_RETRY_SLEEP_SEC,
        "readelf": "readelf",
        "file": "file",
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def acdbtap_row(seq: int, cal_type: int, data: bytes, ret: int = 0) -> dict[str, object]:
    target = v2714.TARGETS[cal_type]
    raw_name = f"acdbtap-{seq:04d}.bin"
    return {
        "seq": seq,
        "cmd": f"0x{target['cmd']:08x}",
        "in_len": "0x00000008",
        "out_len": f"0x{len(data):08x}",
        "ret": ret,
        "buffer": target["buffer"],
        "sha256": hashlib.sha256(data).hexdigest(),
        "raw_path": f"/data/local/tmp/a90-acdb-ownget/acdbtap/{raw_name}",
        "raw_written": True,
        "all_zero": data == bytes(len(data)),
        "is_target_4916": False,
        "is_size_query_4": False,
    }


class NativeAudioAcdbSelectorDeepSnapshotLiveHandoffV2714(unittest.TestCase):
    def test_read_v2713_manifest_checks_large_buffer_contract(self) -> None:
        manifest = v2714.read_v2713_manifest(v2714.v2713.DEFAULT_MANIFEST)

        self.assertTrue(manifest["ok"], manifest)
        self.assertTrue(manifest["selector_snapshot_contract_ok"], manifest)
        self.assertEqual(manifest["capture_contract"]["large_get_bytes"], 65536)

    def test_dry_run_ready_uses_v2713_artifacts(self) -> None:
        payload = v2714.dry_run_payload(args())

        self.assertTrue(payload["ok"], payload.get("live_blockers"))
        self.assertTrue(payload["live_ready"])
        self.assertIn("selector-deep-snapshot", payload["decision"])
        self.assertEqual(payload["capture_contract"]["target_cal_types"], [10, 14, 24])
        self.assertTrue(payload["v2713_artifacts"]["manifest"]["selector_snapshot_contract_ok"])

    def test_summarize_selector_snapshot_capture_success(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="a90-v2714-full-"))
        acdbtap = root / "acdbtap"
        rows = []
        for index, cal_type in enumerate([24, 10, 14], 1):
            data = bytes([index]) * (256 + index)
            (acdbtap / f"acdbtap-{index:04d}.bin").parent.mkdir(parents=True, exist_ok=True)
            (acdbtap / f"acdbtap-{index:04d}.bin").write_bytes(data)
            rows.append(acdbtap_row(index, cal_type, data))
        write_jsonl(acdbtap / "acdbtap-events.jsonl", rows)
        write_jsonl(
            root / "acdb-v2713-selector-deep-snapshot-events.jsonl",
            [
                {"event": "v2672_lower_hidden", "stage": "v2703_large_get_return", "code": 0, "cal_type": 10, "value": 2048},
                {"event": "v2713_selector_deep_snapshot", "cal_type": 24, "node_words": ["0x00000001"] * 16, "block_words": ["0x00000002"] * 32},
                {"event": "v2713_selector_deep_snapshot", "cal_type": 10, "node_words": ["0x00000003"] * 16, "block_words": ["0x00000004"] * 32},
                {"event": "v2713_selector_deep_snapshot", "cal_type": 14, "node_words": ["0x00000005"] * 16, "block_words": ["0x00000006"] * 32},
            ],
        )

        summary = v2714.summarize_selector_snapshot_capture(root)

        self.assertEqual(summary["classification"], "v2714-selector-deep-snapshot-lower-custom-topology-captured")
        self.assertTrue(summary["success"])
        self.assertEqual(summary["captured_cal_types"], [10, 14, 24])
        self.assertEqual(summary["missing_cal_types"], [])
        self.assertEqual(summary["target_seen_count"], 3)
        self.assertEqual(summary["snapshot_cal_types"], [10, 14, 24])
        self.assertEqual(summary["missing_snapshot_cal_types"], [])

    def test_summarize_selector_snapshot_capture_partial_when_one_zero(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="a90-v2714-partial-"))
        acdbtap = root / "acdbtap"
        rows = []
        for index, cal_type in enumerate([24, 10, 14], 1):
            data = bytes(64) if cal_type == 14 else bytes([index]) * 64
            (acdbtap / f"acdbtap-{index:04d}.bin").parent.mkdir(parents=True, exist_ok=True)
            (acdbtap / f"acdbtap-{index:04d}.bin").write_bytes(data)
            rows.append(acdbtap_row(index, cal_type, data))
        write_jsonl(acdbtap / "acdbtap-events.jsonl", rows)

        summary = v2714.summarize_selector_snapshot_capture(root)

        self.assertEqual(summary["classification"], "v2714-selector-deep-snapshot-lower-custom-topology-partial")
        self.assertFalse(summary["success"])
        self.assertTrue(summary["partial_success"])
        self.assertEqual(summary["captured_cal_types"], [10, 24])
        self.assertEqual(summary["missing_cal_types"], [14])

    def test_report_writer_includes_target_metadata_table(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="a90-v2714-report-"))
        payload = v2714.dry_run_payload(args(report_path=root / "report.md"))
        payload["selector_snapshot_summary"] = {
            "classification": "unit-test",
            "target_rows": [{
                "target_cal_type": 10,
                "seq": 1,
                "cmd": 0x11394,
                "ret": 0,
                "out_len": 123,
                "buffer": "ind-lower-adm-custom-topology",
                "sha256": "a" * 64,
                "raw_status": {"exists": True, "size_ok": True, "sha_ok": True, "nonzero": True},
            }],
        }

        v2714.write_report(root / "report.md", payload)

        text = (root / "report.md").read_text(encoding="utf-8")
        self.assertIn("Selector Deep Snapshots", text)
        self.assertIn("Target Rows", text)
        self.assertIn("ind-lower-adm-custom-topology", text)
        self.assertIn("0x00011394", text)


if __name__ == "__main__":
    unittest.main()
