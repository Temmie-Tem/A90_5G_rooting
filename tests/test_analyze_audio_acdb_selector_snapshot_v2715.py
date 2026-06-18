import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import analyze_audio_acdb_selector_snapshot_v2715 as v2715


def make_v2714_result(path: Path) -> None:
    rows = []
    targets = {
        24: ("0x1001025d", 35, 1180, v2715.EXPECTED_SHAS[24], "ind-lower-afe-custom-topology"),
        10: ("0x10004000", 36, 16076, v2715.EXPECTED_SHAS[10], "ind-lower-adm-custom-topology"),
        14: ("0x10005000", 37, 2356, v2715.EXPECTED_SHAS[14], "ind-lower-asm-custom-topology"),
    }
    for cal_type, (_, handle, size, sha, _) in targets.items():
        rows.append({
            "cal_type": cal_type,
            "node_words": ["0xf6b76d45", "0x00000000", f"0xf738c5{handle:02x}"] + ["0x00000000"] * 13,
            "block_words": ["0x00001000", "0x00000001", f"0xf6c2{handle:02x}00", f"0x{handle:08x}"] + ["0x00000000"] * 28,
        })
    target_rows = []
    for cal_type, (_, _, size, sha, buffer) in targets.items():
        target_rows.append({"target_cal_type": cal_type, "out_len": size, "sha256": sha, "buffer": buffer})
    path.write_text(json.dumps({
        "success": True,
        "rolled_back": True,
        "selector_snapshot_summary": {"selector_rows": rows, "target_rows": target_rows},
    }), encoding="utf-8")


class TestV2715SelectorSnapshot(unittest.TestCase):
    def make_args(self, root: Path, *, v2712_ok: bool = True, v2708_ok: bool = True):
        result = root / "v2714.json"
        make_v2714_result(result)
        v2711 = root / "v2711.md"
        v2711.write_text("v2711-setarg-geometry-exhausted-selector-payload-frontier\n", encoding="utf-8")
        v2712 = root / "v2712.md"
        v2712.write_text("v2712-existing-payload-corpus-exhausted-need-new-selector-model\n" if v2712_ok else "open\n", encoding="utf-8")
        v2708 = root / "v2708.md"
        v2708.write_text(
            "| 1 | 24 | 1180 | `AUDIO_SET_CALIBRATION ok` |\n"
            "| 2 | 10 | 16076 | `AUDIO_SET_CALIBRATION ok` |\n"
            "| 3 | 14 | 2356 | `AUDIO_SET_CALIBRATION ok` |\n"
            "send_asm_custom_topology: DSP returned error[ADSP_EBADPARAM]\n" if v2708_ok else "no replay\n",
            encoding="utf-8",
        )
        return SimpleNamespace(v2714_result=result, v2711_report=v2711, v2712_report=v2712, v2708_report=v2708)

    def test_confirms_no_replay_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            summary = v2715.build_summary(self.make_args(Path(temp)))
        self.assertEqual(summary["classification"]["decision"], "v2715-selector-snapshot-confirms-lower-hidden-stale-path-no-replay")
        self.assertTrue(summary["classification"]["selector_block_shape_is_lower_hidden_family"])
        self.assertTrue(summary["classification"]["native_replay_should_remain_parked"])
        self.assertFalse(summary["classification"]["any_selector_word_contains_selected_topology"])

    def test_missing_prior_frontier_keeps_open(self):
        with tempfile.TemporaryDirectory() as temp:
            summary = v2715.build_summary(self.make_args(Path(temp), v2712_ok=False))
        self.assertEqual(summary["classification"]["decision"], "v2715-selector-snapshot-frontier-open")

    def test_selected_word_in_snapshot_breaks_lower_hidden_classification(self):
        with tempfile.TemporaryDirectory() as temp:
            args = self.make_args(Path(temp))
            payload = json.loads(args.v2714_result.read_text(encoding="utf-8"))
            payload["selector_snapshot_summary"]["selector_rows"][1]["node_words"][4] = "0x10004000"
            args.v2714_result.write_text(json.dumps(payload), encoding="utf-8")
            summary = v2715.build_summary(args)
        self.assertFalse(summary["classification"]["selector_block_shape_is_lower_hidden_family"])
        self.assertEqual(summary["classification"]["decision"], "v2715-selector-snapshot-frontier-open")


if __name__ == "__main__":
    unittest.main()
