import unittest
from pathlib import Path

import analyze_audio_acdb_v2686_topology_rejection_v2687 as v2687


class V2687TopologyRejectionTests(unittest.TestCase):
    def test_module_definition_scan_finds_samsung_adaptation(self):
        defs = v2687.load_module_definitions(v2687.DEFAULT_SOURCE_ROOT)
        self.assertIn(0x10001FA0, defs)
        self.assertIn("MODULE_ID_PP_SA", defs[0x10001FA0]["names"])
        self.assertNotIn(0x10001F30, defs)

    def test_summary_classifies_v2686_asm_rejection(self):
        class Args:
            manifest = v2687.DEFAULT_MANIFEST
            v2686_dmesg = v2687.DEFAULT_V2686_DMESG
            source_root = v2687.DEFAULT_SOURCE_ROOT
            private_candidate_dir = Path("/tmp/a90-v2687-test-candidates")
            write_candidates = False

        summary = v2687.summarize(Args())
        self.assertEqual(summary["decision"], "v2687-v2686-topology-rejection-classified")
        self.assertTrue(summary["classification"]["asm_cmd_add_topologies_rejected_by_adsp"])
        cal14 = next(payload for payload in summary["payloads"] if payload["cal_type"] == 14)
        self.assertIn(0x10001F30, cal14["undefined_module_ids"])
        self.assertIn(0x10001F10, cal14["undefined_module_ids"])
        self.assertTrue(summary["classification"]["current_plus_branch_dominated"])

    def test_sanitized_candidate_removes_only_undefined_modules(self):
        defs = v2687.load_module_definitions(v2687.DEFAULT_SOURCE_ROOT)
        manifest = v2687.read_json(v2687.DEFAULT_MANIFEST)
        files_by_remote = v2687.manifest_files_by_remote(manifest)
        entry = next(item for item in manifest["replay_entries"] if item["cal_type"] == 14)
        path = v2687.entry_payload_path(entry, files_by_remote)
        self.assertIsNotNone(path)
        summary = v2687.summarize_payload(14, entry["role"], path, defs)
        candidate = v2687.write_sanitized_candidate(summary, Path("/tmp/a90-v2687-test-candidates"), defs)
        self.assertIsNotNone(candidate)
        self.assertEqual(candidate["removed_module_count"], 2)
        self.assertEqual(candidate["kept_module_count"], 9)


if __name__ == "__main__":
    unittest.main()
