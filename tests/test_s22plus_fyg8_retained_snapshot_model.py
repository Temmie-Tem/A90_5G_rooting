import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / (
    "workspace/public/src/scripts/revalidation/"
    "s22plus_fyg8_retained_snapshot_model.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location(
        "s22plus_fyg8_retained_snapshot_model_tested", SCRIPT
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class S22PlusFyg8RetainedSnapshotModelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def header(self, *, magic=None, idx=0, boot_cnt=1, prev_idx=2):
        return self.module.Header(
            boot_cnt=boot_cnt,
            magic=self.module.LOG_MAGIC if magic is None else magic,
            idx=idx,
            prev_idx=prev_idx,
        )

    def test_invalid_magic_resets_index_and_yields_empty_snapshot(self):
        snapshot = self.module.stock_snapshot(
            b"01234567", self.header(magic=0, idx=12, boot_cnt=9, prev_idx=7)
        )
        self.assertEqual(snapshot.branch, "invalid_magic_reset_empty")
        self.assertEqual(snapshot.data, b"")
        self.assertEqual(snapshot.prepared_header.boot_cnt, 9)
        self.assertEqual(snapshot.prepared_header.magic, self.module.LOG_MAGIC)
        self.assertEqual(snapshot.prepared_header.idx, 0)
        self.assertEqual(snapshot.prepared_header.prev_idx, 0)

    def test_unsaturated_snapshot_is_exact_prefix(self):
        payload = b"abcdefgh"
        snapshot = self.module.stock_snapshot(payload, self.header(idx=3))
        self.assertEqual(snapshot.branch, "prefix")
        self.assertEqual(snapshot.data, b"abc")

    def test_equal_payload_size_uses_prefix_branch_and_returns_full_payload(self):
        payload = b"abcdefgh"
        snapshot = self.module.stock_snapshot(payload, self.header(idx=len(payload)))
        self.assertEqual(snapshot.branch, "prefix")
        self.assertEqual(snapshot.data, payload)

    def test_greater_than_payload_size_rotates_full_payload(self):
        payload = b"abcdefgh"
        snapshot = self.module.stock_snapshot(payload, self.header(idx=11))
        self.assertEqual(snapshot.branch, "rotated_full")
        self.assertEqual(snapshot.data, b"defghabc")

    def test_boot_count_and_previous_index_do_not_change_snapshot(self):
        payload = b"abcdefgh"
        first = self.module.stock_snapshot(
            payload, self.header(idx=11, boot_cnt=0, prev_idx=0)
        )
        second = self.module.stock_snapshot(
            payload,
            self.header(idx=11, boot_cnt=0xFFFFFFFF, prev_idx=0xDEADBEEF),
        )
        self.assertEqual(first.data, second.data)
        self.assertEqual(first.branch, second.branch)

    def test_full_proof_is_invisible_below_proof_length(self):
        proof = b"PROOF"
        for idx in (0, len(proof) - 1):
            with self.subTest(idx=idx):
                result = self.module.analyze_visibility(
                    idx=idx, proof=proof, payload_size=32
                )
                self.assertFalse(result["proof_visible"])
                self.assertFalse(result["minimal_full_proof_visibility_gate"])

    def test_full_proof_becomes_visible_at_proof_length(self):
        proof = b"PROOF"
        result = self.module.analyze_visibility(
            idx=len(proof), proof=proof, payload_size=32
        )
        self.assertTrue(result["proof_visible"])
        self.assertEqual(result["proof_offset"], 0)
        self.assertFalse(result["legacy_full_saturation_gate"])

    def test_unsaturated_prefix_keeps_precursor_at_exported_end(self):
        proof = b"PROOF"
        result = self.module.analyze_visibility(idx=31, proof=proof, payload_size=32)
        self.assertTrue(result["proof_visible"])
        self.assertEqual(result["proof_offset"], 31 - len(proof))
        self.assertEqual(result["snapshot_size"], 31)

    def test_exact_payload_boundary_is_visible_without_rotation(self):
        proof = b"PROOF"
        result = self.module.analyze_visibility(idx=32, proof=proof, payload_size=32)
        self.assertTrue(result["proof_visible"])
        self.assertEqual(result["source_branch"], "prefix")
        self.assertEqual(result["proof_offset"], 32 - len(proof))

    def test_rotated_snapshot_contains_proof_for_cursor_below_proof_size(self):
        proof = b"PROOF"
        result = self.module.analyze_visibility(idx=33, proof=proof, payload_size=32)
        self.assertTrue(result["proof_visible"])
        self.assertEqual(result["source_branch"], "rotated_full")
        self.assertEqual(result["proof_count"], 1)

    def test_rotated_snapshot_contains_proof_for_cursor_at_or_above_proof_size(self):
        proof = b"PROOF"
        for idx in (32 + len(proof), 64, self.module.UINT32_MAX):
            with self.subTest(idx=idx):
                result = self.module.analyze_visibility(
                    idx=idx, proof=proof, payload_size=32
                )
                self.assertTrue(result["proof_visible"])
                self.assertEqual(result["proof_count"], 1)

    def test_visibility_threshold_holds_across_multiple_rotations(self):
        proof = b"PROOF"
        for idx in range(0, 32 * 4 + 1):
            with self.subTest(idx=idx):
                result = self.module.analyze_visibility(
                    idx=idx, proof=proof, payload_size=32
                )
                self.assertEqual(result["proof_visible"], idx >= len(proof))

    def test_source_audit_passes_for_pinned_fyg8_sources(self):
        if not (
            self.module.DEFAULT_MAIN_SOURCE.is_file()
            and self.module.DEFAULT_LAST_KMSG_SOURCE.is_file()
        ):
            self.skipTest("private FYG8 source tree is unavailable")
        result = self.module.audit_sources(
            self.module.DEFAULT_MAIN_SOURCE,
            self.module.DEFAULT_LAST_KMSG_SOURCE,
        )
        self.assertEqual(
            result["strict_rotation_condition"], "idx > payload_size"
        )
        self.assertEqual(result["snapshot_ignores"], ["boot_cnt", "prev_idx"])
        self.assertTrue(result["proc_open_restores_optional_compressed_snapshot"])

    def test_rejects_non_u32_indices(self):
        for idx in (-1, self.module.UINT32_MAX + 1):
            with self.subTest(idx=idx), self.assertRaises(self.module.ModelError):
                self.module.precursor_position(idx, 32, 5)


if __name__ == "__main__":
    unittest.main()
