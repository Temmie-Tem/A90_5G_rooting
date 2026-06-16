"""Host-only tests for V2558 ACDB replay manifest reconciliation."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

from _loader import load_revalidation

v2558 = load_revalidation("analyze_audio_acdb_replay_manifest_v2558")


def make_args(root: Path, **overrides: object) -> Namespace:
    defaults: dict[str, object] = {
        "v2557_result_path": root / "v2557-result.json",
        "stable_payload_path": root / "stable.bin",
        "v2552_report_path": root / "v2552.md",
        "v2557_report_path": root / "v2557.md",
        "libacdbloader_path": root / "libacdbloader.so",
        "expected_topology_sha256": "",
        "manifest_path": root / "manifest.json",
        "readelf": "readelf",
    }
    defaults.update(overrides)
    return Namespace(**defaults)


def write_payload(path: Path) -> str:
    data = (b"A90_TOPOLOGY_REAL_TEST" * 256)[: v2558.EXPECTED_TOPOLOGY_LEN]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def write_result(path: Path, raw_path: Path, digest: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "decision": "v2555-full-manifest-captured-rollback-pass",
        "full_manifest_summary": {
            "classification": "v2555-full-manifest-captured",
            "topology_success_count": 1,
            "per_device_success_count": 1,
            "base_summary": {
                "acdbtap_rows": [
                    {"seq": "0x0", "cmd": "0x131de", "out_len": "0x10", "ret": "0x0", "all_zero": False, "sha256": "1" * 64, "raw_path": "/data/local/tmp/a90-acdb-tap/a.bin"},
                    {"seq": "0x3", "cmd": "0x13296", "out_len": "0x1334", "ret": "0x0", "all_zero": False, "sha256": digest, "raw_path": f"/data/local/tmp/a90-acdb-tap/{raw_path.name}"},
                ]
            },
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


class AnalyzeAcdbReplayManifestV2558(unittest.TestCase):
    def test_v2557_capture_state_validates_raw_4916(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="a90-v2558-test-"))
        result = root / "v2557-result.json"
        raw = root / "ownget-device-artifacts/acdbtap/acdbtap-00000003-cmd-00013296-len-00001334.bin"
        digest = write_payload(raw)
        write_result(result, raw, digest)

        state = v2558.v2557_capture_state(result, expected_sha256=digest)

        self.assertTrue(state["ok"], state)
        self.assertEqual(state["target_4916_count"], 1)
        self.assertEqual(state["raw_validation"][0]["raw"]["sha256"], digest)

    def test_manifest_keeps_full_cal_replay_blocked(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="a90-v2558-test-"))
        args = make_args(root)
        raw = root / "ownget-device-artifacts/acdbtap/acdbtap-00000003-cmd-00013296-len-00001334.bin"
        digest = write_payload(raw)
        write_payload(args.stable_payload_path)
        args.expected_topology_sha256 = digest
        write_result(args.v2557_result_path, raw, digest)
        args.v2552_report_path.write_text("AUDIO_SET_CALIBRATION ok cal_type=39\nA90_PCM_PROBE_WRITE_ERROR\ntopology-only calibration\n", encoding="utf-8")
        args.v2557_report_path.write_text("The `out_len==4916` record passes\nreal `AUDIO_SET_CALIBRATION` pass-through: `0`\n", encoding="utf-8")
        log_dir = args.v2557_result_path.parent / "ownget-device-artifacts"
        log_dir.mkdir(parents=True, exist_ok=True)
        (log_dir / "logcat-acdb-loader.txt").write_text(
            "ACDB -> send_common_custom_topology\n"
            "ACDB -> acdb_loader_send_common_custom_topology: Common custom topology in use\n",
            encoding="utf-8",
        )
        (log_dir / "logcat-avc-acdb-filter.txt").write_text(
            "Fatal signal 11 (SIGSEGV)\n",
            encoding="utf-8",
        )

        payload = v2558.manifest(args)

        self.assertTrue(payload["ok"], payload)
        self.assertTrue(payload["topology_payload_ready"])
        self.assertFalse(payload["full_calibration_replay_ready"])
        self.assertFalse(payload["replay_boundary"]["safe_to_repeat_topology_only_live"])
        self.assertFalse(payload["replay_boundary"]["safe_to_run_full_cal_replay_live"])
        self.assertTrue(payload["v2557_logcat_boundary"]["checks"]["fatal_sigsegv_after_topology"])
        self.assertEqual(len(payload["v2557_logcat_boundary"]["existing_paths"]), 2)
        self.assertGreaterEqual(len(payload["required_per_device_cal_types_not_pinned"]), 4)

    def test_payload_state_rejects_zero_buffer(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="a90-v2558-test-"))
        zero = root / "zero.bin"
        zero.write_bytes(b"\x00" * v2558.EXPECTED_TOPOLOGY_LEN)
        digest = hashlib.sha256(zero.read_bytes()).hexdigest()

        state = v2558.payload_state(zero, expected_sha256=digest)

        self.assertFalse(state["ok"], state)
        self.assertFalse(state["checks"]["nonzero_ok"])
        self.assertFalse(state["checks"]["zero_hash_rejected"])


if __name__ == "__main__":
    unittest.main()
