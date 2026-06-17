"""Tests for the V2628 ACDB AFE topology Gate-2 analyzer."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from _loader import load_revalidation


v2628 = load_revalidation("analyze_audio_acdb_afe_topology_gate2_v2628")


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def make_run(indirect_word: int = 1, direct_word: int = 4) -> Path:
    run_dir = Path(tempfile.mkdtemp(prefix="a90-v2628-run-"))
    artifact_dir = run_dir / "ownget-device-artifacts"
    acdbtap = artifact_dir / "acdbtap"
    acdbtap.mkdir(parents=True, exist_ok=True)
    result = {
        "decision": "v2627-afe-topology-candidate-captured-rollback-pass",
        "rolled_back": True,
        "afe_topology_summary": {
            "helper_event_path": str(artifact_dir / "acdb-v2626-afe-topology-probe-events.jsonl"),
        },
    }
    (run_dir / "v2627-result.json").write_text(json.dumps(result, sort_keys=True), encoding="utf-8")
    helper_rows: list[dict[str, object]] = [
        {
            "event": "v2626_afe_topology_probe",
            "stage": "case_return",
            "case": "afe-topology-id",
            "cmd": "0x000130d8",
            "ret": 0,
            "step": 0,
            "out_word": "0x1001025d",
        }
    ]
    for step in (4, 256, 4096):
        helper_rows.append(
            {
                "event": "v2626_afe_topology_probe",
                "stage": "case_return",
                "case": f"afe-topology-cap{step}",
                "cmd": "0x00013262",
                "ret": 0,
                "step": step,
                "out_word": "0x00000004",
            }
        )
    write_jsonl(artifact_dir / "acdb-v2626-afe-topology-probe-events.jsonl", helper_rows)

    events: list[dict[str, object]] = []
    for seq, capacity in enumerate((4, 256, 4096), start=2):
        indirect = acdbtap / f"acdbtap-{seq:08x}-cmd-00013262-ind-afe-topology-len-00000004.bin"
        direct = acdbtap / f"acdbtap-{seq:08x}-cmd-00013262-len-00000004.bin"
        indirect.write_bytes(indirect_word.to_bytes(4, "little"))
        direct.write_bytes(direct_word.to_bytes(4, "little"))
        events.extend(
            [
                {
                    "cmd": "0x00013262",
                    "seq": f"0x{seq:08x}",
                    "ret": "0x00000000",
                    "buffer": "ind-afe-topology",
                    "out_len": "0x00000004",
                    "in_len": "0x00000008",
                    "raw_path": str(indirect),
                    "sha256": hashlib.sha256(indirect.read_bytes()).hexdigest(),
                    "capacity": capacity,
                },
                {
                    "cmd": "0x00013262",
                    "seq": f"0x{seq:08x}",
                    "ret": "0x00000000",
                    "buffer": "out",
                    "out_len": "0x00000004",
                    "in_len": "0x00000008",
                    "raw_path": str(direct),
                    "sha256": hashlib.sha256(direct.read_bytes()).hexdigest(),
                    "capacity": capacity,
                },
            ]
        )
    write_jsonl(acdbtap / "acdbtap-events.jsonl", events)
    return run_dir


class AnalyzeAudioAcdbAfeTopologyGate2V2628(unittest.TestCase):
    def test_four_byte_one_count_rejects_native_replay(self) -> None:
        run_dir = make_run()
        payload = v2628.make_payload(
            argparse.Namespace(v2627_run=run_dir, include_prior_scan=False)
        )

        self.assertEqual(payload["decision"], "v2628-afe-topology-gate2-reject-replay-payload")
        self.assertTrue(payload["operator_valuable"])
        self.assertFalse(payload["replay_ready"])
        self.assertTrue(payload["native_replay_blocked"])
        self.assertEqual(payload["topology_id_words"], ["0x1001025d"])
        self.assertEqual(payload["direct_13262_words"], ["0x00000004"])
        self.assertEqual(payload["indirect_13262_words"], ["0x00000001"])

    def test_unexpected_indirect_word_requires_operator_review(self) -> None:
        run_dir = make_run(indirect_word=0x1001025D)
        payload = v2628.make_payload(
            argparse.Namespace(v2627_run=run_dir, include_prior_scan=False)
        )

        self.assertEqual(payload["decision"], "v2628-afe-topology-gate2-requires-operator-review")
        self.assertTrue(payload["operator_valuable"])
        self.assertFalse(payload["replay_ready"])
        self.assertEqual(payload["indirect_13262_words"], ["0x1001025d"])

    def test_report_contains_replay_blocking_decision(self) -> None:
        run_dir = make_run()
        payload = v2628.make_payload(
            argparse.Namespace(v2627_run=run_dir, include_prior_scan=False)
        )
        report = run_dir / "report.md"

        v2628.write_report(report, payload)

        text = report.read_text(encoding="utf-8")
        self.assertIn("v2628-afe-topology-gate2-reject-replay-payload", text)
        self.assertIn("native_replay_blocked: `True`", text)
        self.assertIn("0x1001025d", text)


if __name__ == "__main__":
    unittest.main()
