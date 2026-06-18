"""Tests for V2661 legacy ACDB custom SETCAL reparse."""

from __future__ import annotations

import json
import struct
import tempfile
import unittest
from pathlib import Path

from _loader import load_revalidation

v2661 = load_revalidation("analyze_audio_acdb_legacy_custom_setcal_v2661")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def cal_bytes(cal_type: int, request: int, cal_size: int = 0, mem_handle: int = 21) -> dict:
    data = bytearray(64)
    struct.pack_into("<IIII", data, 0, 32, 0, cal_type, 16)
    struct.pack_into("<IIII", data, 16, 0, 0, cal_size, mem_handle & 0xFFFFFFFF)
    return {
        "event": "ioctl_entry",
        "request": f"0x{request:08x}",
        "bytes_hex": data.hex(),
        "seq": cal_type,
        "fd_target": "/dev/msm_audio_cal",
    }


class AnalyzeLegacyCustomSetcalV2661(unittest.TestCase):
    def test_decodes_bytes_hex_set_record(self) -> None:
        event = cal_bytes(10, v2661.AUDIO_SET_CALIBRATION, cal_size=1234, mem_handle=-1)
        decoded = v2661.record_from_event(Path("x.jsonl"), event)

        self.assertIsNotNone(decoded)
        assert decoded is not None
        self.assertEqual(decoded["request_name"], "AUDIO_SET_CALIBRATION")
        self.assertEqual(decoded["cal_type"], 10)
        self.assertEqual(decoded["cal_size"], 1234)
        self.assertEqual(decoded["mem_handle"], -1)

    def test_decodes_v2660_arg_snapshot_allocate(self) -> None:
        event = {
            "event": "ioctl_trace",
            "request": "0xc00461c8",
            "name": "AUDIO_ALLOCATE_CALIBRATION",
            "arg_snapshot": {
                "available": True,
                "data_size": 32,
                "version": 0,
                "cal_type": 14,
                "cal_type_size": 16,
                "type_version": 0,
                "buffer_number": 0,
                "cal_size": 0,
                "mem_handle": 26,
                "sample_len": 32,
            },
        }

        decoded = v2661.record_from_event(Path("ioctl-trace-events.jsonl"), event)

        self.assertIsNotNone(decoded)
        assert decoded is not None
        self.assertEqual(decoded["request_name"], "AUDIO_ALLOCATE_CALIBRATION")
        self.assertEqual(decoded["cal_type"], 14)

    def test_existing_trace_without_target_set_keeps_next_action_lower_function(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="a90-v2661-test-"))
        run = root / "v2461"
        write_jsonl(
            run / "device-artifacts/msm.jsonl",
            [
                cal_bytes(10, v2661.AUDIO_ALLOCATE_CALIBRATION),
                cal_bytes(14, v2661.AUDIO_ALLOCATE_CALIBRATION),
                cal_bytes(24, v2661.AUDIO_ALLOCATE_CALIBRATION),
                cal_bytes(39, v2661.AUDIO_SET_CALIBRATION, cal_size=4916, mem_handle=37),
            ],
        )

        summary = v2661.build_summary([run])

        self.assertEqual(summary["decision"], "v2661-existing-traces-no-custom-setcal-host-only")
        self.assertEqual(summary["target_allocate_cal_types"], [10, 14, 24])
        self.assertEqual(summary["target_set_cal_types"], [])
        self.assertIn("lower-function", summary["operator_value"]["next_action"])

    def test_target_set_success_is_detected(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="a90-v2661-test-"))
        run = root / "future"
        write_jsonl(
            run / "device-artifacts/msm.jsonl",
            [
                cal_bytes(10, v2661.AUDIO_SET_CALIBRATION),
                cal_bytes(14, v2661.AUDIO_SET_CALIBRATION),
                cal_bytes(24, v2661.AUDIO_SET_CALIBRATION),
            ],
        )

        summary = v2661.build_summary([run])

        self.assertEqual(summary["decision"], "v2661-legacy-custom-setcal-found-host-only")
        self.assertEqual(summary["missing_target_set_cal_types"], [])
        self.assertTrue(summary["operator_value"]["custom_sets_already_available"])

    def test_report_is_public_metadata_only(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="a90-v2661-test-"))
        run = root / "v2461"
        write_jsonl(run / "x.jsonl", [cal_bytes(39, v2661.AUDIO_SET_CALIBRATION)])
        summary = v2661.build_summary([run])

        report = v2661.render_report(summary)

        self.assertIn("metadata only", report.lower())
        self.assertNotIn("bytes_hex", report)
        self.assertNotIn("0000000000000000", report)


if __name__ == "__main__":
    unittest.main()
