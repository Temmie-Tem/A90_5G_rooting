"""Tests for the V2619 ACDB Gate-2 handoff manifest."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _loader import load_revalidation

v2619 = load_revalidation("native_audio_acdb_gate2_handoff_v2619")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fake_run() -> Path:
    root = Path(tempfile.mkdtemp(prefix="a90-v2619-run-"))
    acdbtap = root / "ownget-device-artifacts/acdbtap"
    payload = acdbtap / "acdbtap-00000004-cmd-00013265-ind-ap-common-len-00000008.bin"
    payload.parent.mkdir(parents=True, exist_ok=True)
    payload.write_bytes(b"ABCDEFGH")
    size = acdbtap / "acdbtap-00000004-cmd-00013265-len-00000004.bin"
    size.write_bytes((8).to_bytes(4, "little"))
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
                "ordered_records": [
                    {
                        "buffer": "ind-ap-common",
                        "cmd": "0x00013265",
                        "seq": "0x00000004",
                        "in_len": "0x00000014",
                        "out_len": 8,
                        "ret": 0,
                        "sha256": v2619.sha256_file(payload),
                        "local_raw_path": str(payload),
                    },
                    {
                        "buffer": "out",
                        "cmd": "0x00013265",
                        "seq": "0x00000004",
                        "out_len": 4,
                        "ret": 0,
                        "sha256": v2619.sha256_file(size),
                        "local_raw_path": str(size),
                    },
                ],
            },
        },
    )
    events = root / "ownget-device-artifacts/acdb-v2617-direct-matrix-events.jsonl"
    events.parent.mkdir(parents=True, exist_ok=True)
    events.write_text(
        json.dumps({
            "event": "v2617_direct_matrix",
            "stage": "case_return",
            "case": "audproc-common-data",
            "cmd": "0x00013265",
            "ret": 0,
            "out_word": "0x00000008",
            "step": 0,
        }) + "\n",
        encoding="utf-8",
    )
    return root


class NativeAudioAcdbGate2HandoffV2619(unittest.TestCase):
    def test_build_manifest_keeps_private_raw_paths_out_of_redacted_rows(self) -> None:
        run = fake_run()
        manifest = v2619.build_manifest(run)

        self.assertTrue(manifest["ok"])
        self.assertFalse(manifest["native_replay_ready"])
        self.assertEqual(manifest["summary"]["payload_candidate_count"], 1)
        self.assertEqual(manifest["summary"]["audproc_candidate_count"], 1)
        self.assertEqual(manifest["summary"]["vol_candidate_count"], 0)
        self.assertIn("raw_path_private", manifest["payload_candidates"][0])
        self.assertNotIn("raw_path_private", manifest["payload_candidates_redacted"][0])

    def test_zero_payload_is_not_verified(self) -> None:
        run = fake_run()
        raw = run / "ownget-device-artifacts/acdbtap/acdbtap-00000004-cmd-00013265-ind-ap-common-len-00000008.bin"
        raw.write_bytes(b"\x00" * 8)
        result = json.loads((run / "v2618-result.json").read_text(encoding="utf-8"))
        result["direct_matrix_summary"]["ordered_records"][0]["sha256"] = v2619.sha256_file(raw)
        write_json(run / "v2618-result.json", result)

        manifest = v2619.build_manifest(run)

        self.assertFalse(manifest["ok"])
        self.assertEqual(manifest["summary"]["payload_verified_count"], 0)
        self.assertFalse(manifest["payload_candidates"][0]["nonzero"])

    def test_write_report_mentions_gate_boundary(self) -> None:
        run = fake_run()
        manifest = v2619.build_manifest(run)
        report = run / "report.md"
        private_manifest = run / "private.json"

        v2619.write_report(report, manifest, private_manifest)
        text = report.read_text(encoding="utf-8")

        self.assertIn("Gate-2", text)
        self.assertIn("not** a replay manifest", text)
        self.assertIn("AUDPROC_COMMON_CANDIDATE", text)


if __name__ == "__main__":
    unittest.main()
