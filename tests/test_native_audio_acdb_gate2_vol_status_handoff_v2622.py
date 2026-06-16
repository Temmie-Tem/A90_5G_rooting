"""Tests for the V2622 ACDB Gate-2 VOL-status handoff."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _loader import load_revalidation

v2622 = load_revalidation("native_audio_acdb_gate2_vol_status_handoff_v2622")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fake_v2618_run() -> Path:
    root = Path(tempfile.mkdtemp(prefix="a90-v2622-v2618-"))
    acdbtap = root / "ownget-device-artifacts/acdbtap"
    acdbtap.mkdir(parents=True, exist_ok=True)
    rows = []
    specs = [
        ("ind-ap-common", "0x00013265", 18084, b"A"),
        ("ind-ap-stream", "0x00013269", 28, b"B"),
        ("ind-afe-common", "0x0001326f", 1560, b"C"),
    ]
    for index, (buffer, cmd, size, fill) in enumerate(specs, 1):
        raw = acdbtap / f"acdbtap-{index:08x}-cmd-{cmd[2:]}-{buffer}-len-{size:08x}.bin"
        raw.write_bytes(fill * size)
        rows.append({
            "buffer": buffer,
            "cmd": cmd,
            "seq": f"0x{index:08x}",
            "in_len": 20,
            "out_len": size,
            "ret": 0,
            "sha256": v2622.v2619.sha256_file(raw),
            "local_raw_path": str(raw),
        })
    write_json(
        root / "v2618-result.json",
        {
            "decision": "v2618-direct-matrix-perdevice-partial-no-vol-rollback-pass",
            "rolled_back": True,
            "operator_valuable": True,
            "direct_matrix_summary": {
                "classification": "v2618-direct-matrix-perdevice-partial-no-vol",
                "matrix_complete": False,
                "real_audio_set_pass_through_count": 0,
                "ordered_records": rows,
            },
        },
    )
    events = root / "ownget-device-artifacts/acdb-v2617-direct-matrix-events.jsonl"
    events.parent.mkdir(parents=True, exist_ok=True)
    events.write_text(
        json.dumps({"event": "v2617_direct_matrix", "stage": "case_return", "case": "vol-data", "cmd": "0x0001326e", "ret": -19, "step": 0}) + "\n",
        encoding="utf-8",
    )
    return root


def fake_v2621_run() -> Path:
    root = Path(tempfile.mkdtemp(prefix="a90-v2622-v2621-"))
    write_json(
        root / "v2621-result.json",
        {
            "decision": "v2621-vol-isolated-vol-sweep-no-payload-rollback-pass",
            "rolled_back": True,
            "vol_isolated_summary": {
                "classification": "v2621-vol-isolated-vol-sweep-no-payload",
                "helper_done": True,
                "vol_sweep_seen": True,
                "vol_size_case_count": 16,
                "vol_data_case_count": 16,
                "vol_size_ret_values": [-19],
                "vol_data_ret_values": [-19],
                "vol_size_ret_failed_count": 16,
                "vol_data_ret_failed_count": 16,
                "vol_request_in_buffer_count": 32,
                "vol_payload_count": 0,
                "real_audio_set_pass_through_count": 0,
                "base_summary": {"diagnostics": {"helper_rc": 0, "helper_sigsegv": False}},
            },
        },
    )
    return root


class NativeAudioAcdbGate2VolStatusHandoffV2622(unittest.TestCase):
    def test_build_manifest_combines_candidates_and_vol_negative_status(self) -> None:
        manifest = v2622.build_manifest(fake_v2618_run(), fake_v2621_run())

        self.assertTrue(manifest["ok"])
        self.assertFalse(manifest["native_replay_ready"])
        self.assertEqual(manifest["summary"]["payload_candidate_count"], 3)
        self.assertEqual(manifest["summary"]["audproc_candidate_count"], 2)
        self.assertEqual(manifest["summary"]["afe_candidate_count"], 1)
        self.assertTrue(manifest["summary"]["vol_direct_get_exhausted_for_current_tuple"])
        self.assertEqual(manifest["vol_status"]["vol_data_ret_values"], [-19])
        self.assertIn("raw_path_private", manifest["payload_candidates"][0])
        self.assertNotIn("raw_path_private", manifest["payload_candidates_redacted"][0])

    def test_vol_status_requires_complete_rollback_and_no_payload(self) -> None:
        run2618 = fake_v2618_run()
        run2621 = fake_v2621_run()
        result = json.loads((run2621 / "v2621-result.json").read_text(encoding="utf-8"))
        result["vol_isolated_summary"]["vol_payload_count"] = 1
        write_json(run2621 / "v2621-result.json", result)

        manifest = v2622.build_manifest(run2618, run2621)

        self.assertFalse(manifest["ok"])
        self.assertFalse(manifest["summary"]["vol_direct_get_exhausted_for_current_tuple"])

    def test_write_report_mentions_boundary_without_private_raw_paths(self) -> None:
        run2618 = fake_v2618_run()
        run2621 = fake_v2621_run()
        manifest = v2622.build_manifest(run2618, run2621)
        report = run2621 / "report.md"
        private_manifest = run2621 / "private.json"

        v2622.write_report(report, manifest, private_manifest)
        text = report.read_text(encoding="utf-8")

        self.assertIn("Gate-2", text)
        self.assertIn("not** a replay manifest", text)
        self.assertIn("VOL-negative", text)
        self.assertNotIn("raw_path_private", text)


if __name__ == "__main__":
    unittest.main()
