import json
import tempfile
import unittest
from pathlib import Path

from workspace.public.src.scripts.revalidation import analyze_audio_acdb_core_topology_bridge_v2683 as v2683
from workspace.public.src.scripts.revalidation import analyze_audio_acdb_selected_topology_selector_v2695 as v2695


class TestAnalyzeAudioAcdbSelectedTopologySelectorV2695(unittest.TestCase):
    def test_relaxed_json_accepts_unquoted_hex(self):
        row = v2695.parse_relaxed_json_line('{"value":0xf1bd8410,"code":0}')
        self.assertEqual(row["value"], "0xf1bd8410")
        self.assertEqual(v2695.intish(row["value"]), 0xF1BD8410)

    def test_parse_tap_records_classifies_unmapped_signed_ret(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: self.remove_tree(root))
        artifacts = root / "ownget-device-artifacts"
        tap = artifacts / "acdbtap"
        tap.mkdir(parents=True)
        rows = [
            {"event": "acdb_ioctl_call", "seq": "0x00000002", "cmd": "0x00011394", "in_len": "0x8", "in_word0": "0x1000", "in_word1": "0xf14f5000", "phase": "enter"},
            {"event": "ptrtarget_status", "seq": "0x00000002", "cmd": "0x00011394", "status": "ptrtarget_unmapped", "map_start": "0x0", "map_end": "0x0"},
            {"seq": "0x00000002", "cmd": "0x00011394", "buffer": "out", "ret": "0xfffffff4", "out_len": "0x4", "all_zero": True},
        ]
        (tap / "acdbtap-events.jsonl").write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

        records = v2695.parse_tap_records(artifacts)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].cal_type, 10)
        self.assertEqual(records[0].ret, -12)
        self.assertTrue(records[0].word1_page_aligned)
        self.assertTrue(records[0].word1_unmapped)

    def test_analyze_classifies_v2695_frontier(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: self.remove_tree(root))
        run = root / "run"
        artifacts = run / "ownget-device-artifacts"
        tap = artifacts / "acdbtap"
        tap.mkdir(parents=True)
        lower = []
        for cal, cmd, word1, code, value in (
            (24, 0x130DA, 0xF14F6000, 0, 0x49C),
            (10, 0x11394, 0xF14F5000, -12, 0),
            (14, 0x12E01, 0xF14BB000, 0, 0x934),
        ):
            lower.extend([
                f'{{"event":"v2672_lower_hidden","stage":"create_cal_node_return","code":0,"cal_type":{cal},"value":0x1}}',
                f'{{"event":"v2672_lower_hidden","stage":"allocate_cal_block_return","code":0,"cal_type":{cal},"value":0x2}}',
                json.dumps({"event": "v2692_lower_block_snapshot", "cal_type": cal, "node": "0x1", "block": "0x2", "get_arg0": "0x00001000", "get_arg1": f"0x{word1:08x}", "mem_handle": cal, "word4": "0x1", "word16": "0x0", "word20": "0x0"}),
                f'{{"event":"v2672_lower_hidden","stage":"acdb_ioctl_get_return","code":{code},"cal_type":{cal},"value":0x{value:08x}}}',
            ])
        (artifacts / "acdb-v2674-lower-hidden-inhook-events.jsonl").write_text("\n".join(lower), encoding="utf-8")
        tap_rows = []
        for seq, cal, cmd, word1, ret, zero in (
            (1, 24, 0x130DA, 0xF14F6000, 0, False),
            (2, 10, 0x11394, 0xF14F5000, 0xFFFFFFF4, True),
            (3, 14, 0x12E01, 0xF14BB000, 0, False),
        ):
            tap_rows.extend([
                {"event": "acdb_ioctl_call", "seq": f"0x{seq:08x}", "cmd": f"0x{cmd:08x}", "in_word0": "0x00001000", "in_word1": f"0x{word1:08x}", "phase": "enter"},
                {"event": "ptrtarget_status", "seq": f"0x{seq:08x}", "cmd": f"0x{cmd:08x}", "status": "ptrtarget_unmapped", "map_start": "0x0", "map_end": "0x0"},
                {"seq": f"0x{seq:08x}", "cmd": f"0x{cmd:08x}", "buffer": "out", "ret": f"0x{ret:08x}", "out_len": "0x4", "all_zero": zero},
            ])
        (tap / "acdbtap-events.jsonl").write_text("\n".join(json.dumps(row) for row in tap_rows), encoding="utf-8")
        # cal24 contains selected AFE topology; cal14 deliberately omits selected ASM 0x10005000.
        cal24 = v2683.fixed_payload_from_core([v2683.CoreRecord(0, 0, 0, 0x1001025D, 0, ((0x1025F, 0x10000),))])
        cal14 = v2683.fixed_payload_from_core([v2683.CoreRecord(0, 0, 0, 0x10000018, 0, ((0x10719, 0x10000),))])
        (artifacts / "setcal-dmabuf-p-test-cal00000018-len0000049c.bin").write_bytes(cal24)
        (artifacts / "setcal-dmabuf-p-test-cal0000000e-len00000934.bin").write_bytes(cal14)
        setcal = [
            {"event": "setcal_capture", "sequence": 1, "cal_type": 24, "cal_size": len(cal24), "mem_handle": 35, "set_arg": {"sha256": "arg24"}, "dmabuf": {"status": "dumped", "path": "/data/local/tmp/a90-acdb-ownget/setcal-dmabuf-p-test-cal00000018-len0000049c.bin", "sha256": "pay24", "all_zero": False}},
            {"event": "setcal_capture", "sequence": 2, "cal_type": 14, "cal_size": len(cal14), "mem_handle": 37, "set_arg": {"sha256": "arg14"}, "dmabuf": {"status": "dumped", "path": "/data/local/tmp/a90-acdb-ownget/setcal-dmabuf-p-test-cal0000000e-len00000934.bin", "sha256": "pay14", "all_zero": False}},
        ]
        (artifacts / "setcal-events.jsonl").write_text("\n".join(json.dumps(row) for row in setcal), encoding="utf-8")

        summary = v2695.analyze(run, legacy_trace_dirs=())

        self.assertEqual(summary["decision"], "v2695-selector-audit-pivots-away-from-lower-ptrtarget")
        self.assertTrue(summary["all_word1_unmapped"])
        self.assertTrue(summary["afe_selected_topology_present_in_cal24"])
        self.assertFalse(summary["asm_selected_topology_present_in_cal14"])
        self.assertFalse(summary["adm_set_captured"])

    def remove_tree(self, path: Path):
        import shutil

        shutil.rmtree(path, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
