from __future__ import annotations

import unittest

from _loader import load_script


runner = load_script("workspace/public/src/scripts/revalidation/analyze_doom_suspect_priority_audit_v3128.py")


class AnalyzeDoomSuspectPriorityAuditV3128Tests(unittest.TestCase):
    def test_collect_evidence_extracts_current_live_metrics(self) -> None:
        evidence = runner.collect_evidence()

        self.assertEqual(evidence["v3124"]["read_avg_us"], 2)
        self.assertEqual(evidence["v3127"]["read_avg_us"], 3)
        self.assertEqual(evidence["v3127"]["draw_avg_us"], 4277)
        self.assertEqual(evidence["v3127"]["flip_avg_us"], 16639)
        self.assertEqual(evidence["v3127"]["flip_max_us"], 16666)
        self.assertEqual(evidence["v3127"]["seq_missed"], 0)
        self.assertEqual(evidence["v3127"]["seq_max_gap"], 1)
        self.assertEqual(evidence["v3127"]["dump_repeated"], 0)
        self.assertEqual(evidence["v3127"]["dump_max_same_run"], 1)
        self.assertTrue(evidence["v3127"]["output_gametic_bounded"])
        self.assertTrue(evidence["kms"]["static_kms_state"])
        self.assertTrue(evidence["kms"]["pageflip_api"])
        self.assertTrue(evidence["kms"]["framebuffer_api"])
        self.assertFalse(evidence["kms"]["shared_buffer_export_api"])

    def test_build_audit_closes_ranked_suspects_and_defers_direct_kms(self) -> None:
        audit = runner.build_audit(runner.collect_evidence())

        self.assertEqual(audit["run_id"], "V3128")
        self.assertEqual(audit["decision"], "v3128-doom-suspect-priority-audit-complete")
        self.assertEqual(audit["remaining_required_work"], [])
        statuses = {item["rank"]: item["status"] for item in audit["suspects"]}
        self.assertEqual(statuses, {1: "closed", 2: "closed", 3: "closed", 4: "closed", 5: "explained"})
        self.assertEqual(audit["direct_kms"]["status"], "defer")
        self.assertEqual(audit["direct_kms"]["expected_best_case_saved_us"], 3)
        self.assertFalse(audit["direct_kms"]["direct_kms_saves_meaningful_time"])

    def test_render_report_records_decision_and_no_flash_scope(self) -> None:
        audit = runner.build_audit(runner.collect_evidence())
        report = runner.render_report(audit)

        self.assertIn("Native Init V3128 DOOM Suspect Priority Audit", report)
        self.assertIn("Device flash: `no`", report)
        self.assertIn("Direct KMS Buffer Path", report)
        self.assertIn("Expected best-case saved time: `3 us`", report)
        self.assertIn("Do not implement helper-direct-KMS in this pass", report)
        self.assertIn("Further visual quality work should be framed explicitly as a DOOM semantics/interpolation feature", report)


if __name__ == "__main__":
    unittest.main()
