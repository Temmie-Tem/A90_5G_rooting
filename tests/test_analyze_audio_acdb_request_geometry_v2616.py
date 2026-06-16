"""Tests for V2616 ACDB request geometry analyzer."""

from __future__ import annotations

import json
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _loader import load_revalidation

v2616 = load_revalidation("analyze_audio_acdb_request_geometry_v2616")


def write_words(path: Path, words: list[int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"".join(struct.pack("<I", word & 0xFFFFFFFF) for word in words))


def row(seq: int, cmd: str, buffer: str, words: list[int], *, ret: int = 0, raw_name: str | None = None) -> dict[str, object]:
    raw_name = raw_name or f"acdbtap-{seq:08x}-{cmd}-{buffer}.bin"
    return {
        "seq": f"0x{seq:08x}",
        "cmd": cmd,
        "buffer": buffer,
        "in_len": f"0x{len(words) * 4:08x}",
        "out_len": f"0x{len(words) * 4:08x}",
        "ret": f"0x{ret & 0xFFFFFFFF:08x}",
        "all_zero": all(word == 0 for word in words),
        "sha256": "test-sha",
        "raw_path": f"/data/local/tmp/a90-acdb-tap/{raw_name}",
    }


def write_pair(rows: list[dict[str, object]], run: Path, seq: int, cmd: str, in_words: list[int], out_words: list[int], *, ret: int = 0) -> None:
    acdbtap = run / "ownget-device-artifacts/acdbtap"
    in_name = f"acdbtap-{seq:08x}-{cmd}-in.bin"
    out_name = f"acdbtap-{seq:08x}-{cmd}-out.bin"
    write_words(acdbtap / in_name, in_words)
    write_words(acdbtap / out_name, out_words)
    rows.append(row(seq, cmd, "in", in_words, ret=0, raw_name=in_name))
    rows.append(row(seq, cmd, "out", out_words, ret=ret, raw_name=out_name))


def write_v2614_like_run(root: Path) -> Path:
    run = root / "run"
    rows: list[dict[str, object]] = []
    pairs = [
        (1, "0x0001122e", [0x11135], [0x10005000], 0),
        (2, "0x0001122d", [0xF, 0x11135], [0x10004000], 0),
        (3, "0x00013267", [0xF, 0xBB80, 0x11135], [0x46A4], 0),
        (4, "0x00013265", [0xF, 0xBB80, 0x11135, 0x46A4, 0xF0001000], [0x46A4], 0),
        (5, "0x0001326d", [0xF, 0x11135, 0], [0], -19),
        (6, "0x0001326e", [0xF, 0x11135, 0, 0x1000, 0xF0002000], [0], -19),
        (7, "0x00013268", [0x11135], [0x1C], 0),
        (8, "0x00013269", [0x11135, 0x1000, 0xF0003000], [0x1C], 0),
        (9, "0x000130d8", [0xF], [0x1001025D], 0),
        (10, "0x00013271", [0xF, 0xBB80], [0x618], 0),
        (11, "0x0001326f", [0xF, 0xBB80, 0x1000, 0xF0004000], [0x618], 0),
        (12, "0x00012eeb", [0xF, 1, 0xCC, 0xFFC1A3C4], [0x1C], 0),
    ]
    for seq, cmd, in_words, out_words, ret in pairs:
        write_pair(rows, run, seq, cmd, in_words, out_words, ret=ret)
    rows.extend(
        [
            {
                "seq": "0x00000004",
                "cmd": "0x00013265",
                "buffer": "ind-ap-common",
                "out_len": "0x000046a4",
                "ret": "0x00000000",
                "all_zero": False,
                "sha256": "ind-ap-common-sha",
            },
            {
                "seq": "0x00000008",
                "cmd": "0x00013269",
                "buffer": "ind-ap-stream",
                "out_len": "0x0000001c",
                "ret": "0x00000000",
                "all_zero": False,
                "sha256": "ind-ap-stream-sha",
            },
            {
                "seq": "0x0000000b",
                "cmd": "0x0001326f",
                "buffer": "ind-afe-common",
                "out_len": "0x00000618",
                "ret": "0x00000000",
                "all_zero": False,
                "sha256": "ind-afe-common-sha",
            },
        ]
    )
    result = {
        "ok": True,
        "rolled_back": True,
        "decision": "v2490-acdbtap-full-outbuf-set-no-4916-before-helper-exit-before-rollback-rollback-pass",
        "ownget_summary": {"acdbtap_rows": rows},
    }
    (run / "result.json").parent.mkdir(parents=True, exist_ok=True)
    (run / "result.json").write_text(json.dumps(result), encoding="utf-8")
    return run


class AnalyzeAudioAcdbRequestGeometryV2616(unittest.TestCase):
    def test_analyze_run_pins_order_and_vol_minus_19(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="a90-v2616-test-"))
        run = write_v2614_like_run(root)

        payload = v2616.analyze_run(run)

        self.assertTrue(payload["ok"], payload)
        self.assertEqual(payload["decision"], "v2616-request-geometry-pinned")
        self.assertTrue(payload["checks"]["vol_size_ret_minus_19"])
        self.assertTrue(payload["checks"]["vol_data_ret_minus_19"])
        self.assertEqual(payload["successful_indirect_commands"], ["0x00013265", "0x00013269", "0x0001326f"])
        gain = [call for call in payload["calls"] if call["cmd"] == "0x0001326e"][0]
        self.assertEqual(gain["fields"]["gain_step"], "0x00000000")
        self.assertEqual(gain["ret_signed"], -19)

    def test_report_says_replay_remains_blocked(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="a90-v2616-test-"))
        run = write_v2614_like_run(root)
        payload = v2616.analyze_run(run)
        text = "\n".join(v2616.report_lines(payload))

        self.assertIn("Native replay remains blocked", text)
        self.assertIn("0x1326d", text)
        self.assertIn("0x1001025d", text)

    def test_cli_writes_json_and_report(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="a90-v2616-test-"))
        run = write_v2614_like_run(root)
        json_path = root / "request-geometry.json"
        report_path = root / "report.md"
        completed = subprocess.run(
            [
                sys.executable,
                "workspace/public/src/scripts/revalidation/analyze_audio_acdb_request_geometry_v2616.py",
                "--run-dir",
                str(run),
                "--json-path",
                str(json_path),
                "--write-report",
                "--report-path",
                str(report_path),
            ],
            cwd=v2616.ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["ok"])
        self.assertTrue(json_path.exists())
        self.assertTrue(report_path.exists())
        self.assertIn("V2616", report_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
