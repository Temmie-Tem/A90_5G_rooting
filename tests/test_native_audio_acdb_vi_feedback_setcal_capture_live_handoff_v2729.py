"""Tests for the V2729 vi-feedback ACDB SET capture live wrapper."""

from __future__ import annotations

import argparse
import json
import tempfile
import unittest
from pathlib import Path

from _loader import load_revalidation

v2729 = load_revalidation("native_audio_acdb_vi_feedback_setcal_capture_live_handoff_v2729")


def args(**overrides: object) -> argparse.Namespace:
    root = Path(tempfile.mkdtemp(prefix="a90-v2729-test-"))
    defaults: dict[str, object] = {
        "dry_run": True,
        "run_live": False,
        "write_report": False,
        "report_path": root / "report.md",
        "build_v2728_artifacts": False,
        "v2728_build_root": v2729.v2728.DEFAULT_BUILD_ROOT,
        "v2728_manifest_path": v2729.v2728.DEFAULT_MANIFEST,
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
        "android_root_recheck_attempts": v2729.v2490.v2396.DEFAULT_ANDROID_ROOT_RECHECK_ATTEMPTS,
        "android_root_recheck_sleep_sec": v2729.v2490.v2396.DEFAULT_ANDROID_ROOT_RECHECK_SLEEP_SEC,
        "android_settle_adb_retry_attempts": v2729.v2490.DEFAULT_SETTLE_ADB_RETRY_ATTEMPTS,
        "android_settle_adb_retry_sleep_sec": v2729.v2490.DEFAULT_SETTLE_ADB_RETRY_SLEEP_SEC,
        "readelf": "readelf",
        "file": "file",
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def setcal_event(seq: int, cal_type: int, cal_size: int, mem_handle: int, dmabuf_status: str) -> dict[str, object]:
    return {
        "event": "setcal_capture",
        "pid": 4198,
        "tid": 4198,
        "sequence": seq,
        "fd": 31,
        "request": "0xc00461cb",
        "header_valid": True,
        "data_size": 48,
        "version": 0,
        "cal_type": cal_type,
        "cal_type_size": 32,
        "cal_hdr_version": 3,
        "buffer_number": 0,
        "cal_size": cal_size,
        "mem_handle": mem_handle,
        "set_arg": {
            "path": f"/data/local/tmp/a90-acdb-ownget/setcal-arg-{seq:04d}.bin",
            "len": 48,
            "dump_rc": 0,
            "sha256": f"{cal_type:064x}",
            "all_zero": False,
        },
        "dmabuf": {
            "status": dmabuf_status,
            "path": f"/data/local/tmp/a90-acdb-ownget/setcal-dmabuf-{seq:04d}.bin",
            "len": cal_size if dmabuf_status == "dumped" else 0,
            "dump_rc": 0 if dmabuf_status == "dumped" else -1,
            "mmap_errno": 0 if dmabuf_status == "dumped" else 5,
            "sha256": f"{seq:064x}" if dmabuf_status == "dumped" else "0" * 64,
            "all_zero": False,
        },
    }


class NativeAudioAcdbViFeedbackSetcalCaptureLiveHandoffV2729(unittest.TestCase):
    def test_read_v2728_manifest_checks_vi_feedback_contract(self) -> None:
        manifest = v2729.read_v2728_manifest(v2729.v2728.DEFAULT_MANIFEST)

        self.assertTrue(manifest["ok"], manifest)
        self.assertTrue(manifest["setcal_contract_ok"], manifest)
        self.assertEqual(manifest["capture_contract"]["vi_feedback_call"]["acdb_id"], 102)

    def test_summarize_success_when_cal17_captured(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="a90-v2729-success-"))
        write_jsonl(
            root / "setcal-events.jsonl",
            [
                setcal_event(1, 11, 4096, 10, "dumped"),
                setcal_event(2, 17, 1560, 11, "dumped"),
            ],
        )

        summary = v2729.summarize_setcal_capture(root)

        self.assertEqual(summary["classification"], "v2729-vi-feedback-cal17-captured")
        self.assertTrue(summary["success"])
        self.assertEqual(summary["target_record_count"], 1)
        self.assertEqual(summary["target_dmabuf_dumped_count"], 1)
        self.assertEqual(summary["supplemental_cal_types_seen"], [11])

    def test_summarize_partial_when_records_lack_cal17(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="a90-v2729-nocal17-"))
        write_jsonl(root / "setcal-events.jsonl", [setcal_event(1, 11, 4096, 10, "dumped")])

        summary = v2729.summarize_setcal_capture(root)

        self.assertEqual(summary["classification"], "v2729-setcal-records-no-cal17")
        self.assertFalse(summary["success"])
        self.assertTrue(summary["partial_success"])
        self.assertTrue(summary["operator_valuable"])

    def test_summarize_boundary_violation_on_real_set_passthrough(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="a90-v2729-boundary-"))
        write_jsonl(root / "setcal-events.jsonl", [setcal_event(1, 17, 1560, 11, "dumped")])
        write_jsonl(
            root / "ioctl-trace-events.jsonl",
            [
                {
                    "event": "ioctl_trace",
                    "name": "AUDIO_SET_CALIBRATION",
                    "intercept": "passed-through",
                    "ret": 0,
                }
            ],
        )

        summary = v2729.summarize_setcal_capture(root)

        self.assertEqual(summary["classification"], "v2729-boundary-violation-real-audio-set-passthrough")
        self.assertFalse(summary["success"])
        self.assertEqual(summary["real_audio_set_pass_through_count"], 1)

    def test_dry_run_uses_v2490_engine_with_v2728_artifacts(self) -> None:
        payload = v2729.dry_run_payload(args())

        self.assertTrue(payload["ok"], payload.get("live_blockers"))
        self.assertEqual(
            payload["capture_contract"]["send_path"],
            "init_v3 -> a90_arm_capture -> send_audio_cal_v5(102,1,0x11132,8000,0,8000,1)",
        )
        self.assertEqual(
            payload["capture_contract"]["set_intercept"],
            "AUDIO_SET_CALIBRATION always fake-successed; never reaches Android kernel SET",
        )
        self.assertTrue(payload["v2728_artifacts"]["ok"])
        self.assertTrue(payload["v2490_engine"]["live_ready"])


if __name__ == "__main__":
    unittest.main()
