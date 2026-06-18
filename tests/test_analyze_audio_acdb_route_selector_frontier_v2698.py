import unittest

import analyze_audio_acdb_route_selector_frontier_v2698 as v2698


class TestAnalyzeAudioAcdbRouteSelectorFrontierV2698(unittest.TestCase):
    def test_scan_word_constants_counts_little_endian_hits(self):
        data = (
            b"\x00\x40\x00\x10"
            b"xxxx"
            b"\x00\x50\x00\x10"
            b"\x00\x40\x00\x10"
        )
        hits = {hit.name: hit for hit in v2698.scan_word_constants(data, v2698.CONSTANTS)}
        self.assertEqual(hits["selected_adm_0x10004000"].count, 2)
        self.assertEqual(hits["selected_adm_0x10004000"].offsets, (0, 12))
        self.assertEqual(hits["selected_asm_0x10005000"].count, 1)
        self.assertEqual(hits["selected_afe_0x1001025d"].count, 0)

    def test_parse_readelf_symbols_filters_interesting_names(self):
        text = """
           Num:    Value  Size Type    Bind   Vis      Ndx Name
            13: 00000000     0 FUNC    GLOBAL DEFAULT  UND acdb_ioctl
           141: 00008cf1  2620 FUNC    GLOBAL DEFAULT   14 acdb_loader_send_common_custom_topology
           999: 00000001     4 OBJECT  GLOBAL DEFAULT   23 unrelated_symbol
        """
        hits = v2698.parse_readelf_symbols(text, "lib.so", v2698.SYMBOLS_OF_INTEREST)
        by_name = {hit.name: hit for hit in hits}
        self.assertFalse(by_name["acdb_ioctl"].defined)
        self.assertTrue(by_name["acdb_loader_send_common_custom_topology"].defined)
        self.assertEqual(by_name["acdb_loader_send_common_custom_topology"].size, 2620)
        self.assertNotIn("unrelated_symbol", by_name)

    def test_report_value_and_contains(self):
        text = "- decision: `v2695-selector-audit-pivots-away-from-lower-ptrtarget`\nASM selected absent\n"
        self.assertEqual(
            v2698.report_value(text, "decision"),
            "v2695-selector-audit-pivots-away-from-lower-ptrtarget",
        )
        self.assertTrue(v2698.report_contains(text, "asm SELECTED"))

    def test_classify_frontier_closes_prior_branches(self):
        lib_summary = {
            "constants": [
                {"name": "selected_asm_0x10005000", "count": 0},
                {"name": "speaker_app_0x11135", "count": 0},
                {"name": "avcs_custom_topo_cmd_0x13296", "count": 1},
            ]
        }
        hal_summary = {
            "constants": [
                {"name": "selected_asm_0x10005000", "count": 0},
                {"name": "speaker_app_0x11135", "count": 0},
            ]
        }
        markers = {
            "v2695_decision": "v2695-selector-audit-pivots-away-from-lower-ptrtarget",
            "v2695_asm_selected_absent": True,
            "v2697_decision": "v2697-firmware-acdbdata-staged-selected-records-absent",
            "v2697_db_absent": True,
            "v2689_synthetic_failed": True,
            "v2694_set_geometry_not_blocker": True,
            "spec_cross_process_closed": True,
        }
        result = v2698.classify_frontier(lib_summary, hal_summary, markers)
        self.assertEqual(result["decision"], "v2698-route-selector-frontier-needs-new-selector-model")
        self.assertEqual(result["recommended_next"], "loader-selector-re-or-new-real-hal-set-capture")
        self.assertTrue(result["park_native_replay"])
        self.assertTrue(all(result["closed_branches"].values()))

    def test_classify_frontier_flags_unclosed_branch(self):
        result = v2698.classify_frontier({"constants": []}, {"constants": []}, {})
        self.assertEqual(result["decision"], "v2698-route-selector-frontier-has-unclosed-prior-branch")
        self.assertTrue(result["park_native_replay"])


if __name__ == "__main__":
    unittest.main()
