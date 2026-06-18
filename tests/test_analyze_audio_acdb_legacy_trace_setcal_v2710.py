import json
import tempfile
import unittest
from pathlib import Path

import analyze_audio_acdb_legacy_trace_setcal_v2710 as v2710


def header_hex(cal_type: int, cal_size: int = 0, mem_handle: int = -1, data_size: int = 32) -> str:
    import struct

    return struct.pack("<8i", data_size, 0, cal_type, 16, 0, 0, cal_size, mem_handle).hex()


class TestV2710LegacyTraceSetcal(unittest.TestCase):
    def write_jsonl(self, path: Path, rows: list[dict]):
        path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

    def test_decode_cal_header(self):
        decoded = v2710.decode_cal_header(header_hex(39, cal_size=4916, mem_handle=37))
        self.assertEqual(decoded["cal_type"], 39)
        self.assertEqual(decoded["cal_size"], 4916)
        self.assertEqual(decoded["mem_handle"], 37)

    def test_parse_trace_file_pairs_exit_ret(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "v2466-test.jsonl"
            self.write_jsonl(
                path,
                [
                    {
                        "event": "ioctl_entry",
                        "seq": 1,
                        "tid": 100,
                        "fd_pid": 90,
                        "abi": "aarch32",
                        "request": "0xc00461cb",
                        "fd_target": "/dev/msm_audio_cal",
                        "bytes_hex": header_hex(39, 4916, 37),
                    },
                    {"event": "ioctl_exit", "seq": 1, "request": "0xc00461cb", "ret": 0},
                ],
            )
            parsed = v2710.parse_trace_file(path)
        self.assertEqual(parsed["entry_count"], 1)
        self.assertEqual(parsed["entries"][0]["request_name"], "AUDIO_SET_CALIBRATION")
        self.assertEqual(parsed["entries"][0]["cal_type"], 39)
        self.assertEqual(parsed["entries"][0]["ret"], 0)

    def test_classifies_absent_target_setcal(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "v2461-test.jsonl"
            rows = []
            seq = 1
            for cal_type, handle in [(10, 21), (14, 26), (24, 31), (39, 37)]:
                rows.append(
                    {
                        "event": "ioctl_entry",
                        "seq": seq,
                        "tid": 1,
                        "fd_pid": 1,
                        "abi": "aarch32",
                        "request": "0xc00461c8",
                        "fd_target": "/dev/msm_audio_cal",
                        "bytes_hex": header_hex(cal_type, 0, handle),
                    }
                )
                rows.append({"event": "ioctl_exit", "seq": seq, "request": "0xc00461c8", "ret": 0})
                seq += 1
            rows.append(
                {
                    "event": "ioctl_entry",
                    "seq": seq,
                    "tid": 1,
                    "fd_pid": 1,
                    "abi": "aarch32",
                    "request": "0xc00461cb",
                    "fd_target": "/dev/msm_audio_cal",
                    "bytes_hex": header_hex(39, 4916, 37),
                }
            )
            rows.append({"event": "ioctl_exit", "seq": seq, "request": "0xc00461cb", "ret": 0})
            self.write_jsonl(path, rows)

            aggregate = v2710.aggregate([v2710.parse_trace_file(path)])

        classification = aggregate["classification"]
        self.assertEqual(classification["decision"], "v2710-legacy-real-hal-traces-have-no-subsystem-topology-setcal")
        self.assertFalse(classification["legacy_traces_have_target_setcal"])
        self.assertTrue(classification["legacy_traces_have_target_allocations"])
        self.assertTrue(classification["legacy_traces_have_core_topology_setcal_39"])

    def test_classifies_candidate_when_target_set_exists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "v2466-test.jsonl"
            self.write_jsonl(
                path,
                [
                    {
                        "event": "ioctl_entry",
                        "seq": 1,
                        "tid": 1,
                        "fd_pid": 1,
                        "abi": "aarch32",
                        "request": "0xc00461cb",
                        "fd_target": "/dev/msm_audio_cal",
                        "bytes_hex": header_hex(10, 16076, 21),
                    },
                    {"event": "ioctl_exit", "seq": 1, "request": "0xc00461cb", "ret": 0},
                ],
            )
            aggregate = v2710.aggregate([v2710.parse_trace_file(path)])

        self.assertEqual(aggregate["classification"]["decision"], "v2710-legacy-traces-contain-target-setcal-candidate")
        self.assertTrue(aggregate["classification"]["legacy_traces_have_target_setcal"])


if __name__ == "__main__":
    unittest.main()
