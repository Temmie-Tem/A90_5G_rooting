import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "workspace/public/src/scripts/revalidation"
SCRIPT = SCRIPTS / "s22plus_fyg8_p230_same_ring_multiboot_decoder.py"


def load_module():
    sys.path.insert(0, str(SCRIPTS))
    try:
        spec = importlib.util.spec_from_file_location(
            "s22plus_fyg8_p230_same_ring_multiboot_decoder_tested", SCRIPT
        )
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(SCRIPTS))


class P230SameRingMultibootDecoderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()
        cls.base = cls.module.base

    def test_zero_remains_ambiguous(self):
        result = self.module.classify_observation(b"ordinary retained bytes")
        self.assertEqual(result["classification"], "ZERO_AMBIGUOUS")
        self.assertFalse(result["accepted"])
        self.assertEqual(result["minimum_candidate_boots"], 0)

    def test_one_or_more_userspace_records_are_positive(self):
        for count in (1, 2, 5):
            with self.subTest(count=count):
                result = self.module.classify_observation(
                    b"prefix" + self.base.USERSPACE_PROOF * count + b"suffix"
                )
                self.assertEqual(
                    result["classification"],
                    "USERSPACE_CALLBACK_REACHED_ONE_OR_MORE_BOOTS",
                )
                self.assertTrue(result["accepted"])
                self.assertFalse(result["integrity_issue"])
                self.assertEqual(result["userspace_count"], count)
                self.assertEqual(result["minimum_candidate_boots"], count)

    def test_repeated_diagnostic_states_are_not_accepted(self):
        cases = (
            (self.base.ENTRY_PROOF, "ENTRY_ONLY_ONE_OR_MORE_BOOTS"),
            (self.base.UNSAT_PROOF, "UNSAT_VALID_MAGIC_ONE_OR_MORE_BOOTS"),
        )
        for record, classification in cases:
            with self.subTest(classification=classification):
                result = self.module.classify_observation(record * 2)
                self.assertEqual(result["classification"], classification)
                self.assertFalse(result["accepted"])
                self.assertFalse(result["integrity_issue"])
                self.assertEqual(result["minimum_candidate_boots"], 2)

    def test_mixed_foreign_and_partial_records_fail_closed(self):
        payloads = (
            self.base.USERSPACE_PROOF + self.base.ENTRY_PROOF,
            self.base.USERSPACE_PROOF + self.base.UNSAT_PROOF,
            self.base.ENTRY_FAMILY + b"0" * 32 + b"]]\n",
            self.base.UNSAT_FAMILY + b"\x00" * 16,
            self.base.USERSPACE_PROOF[-12:] + b"suffix",
            b"prefix" + self.base.USERSPACE_PROOF[:20],
        )
        for payload in payloads:
            with self.subTest(payload=payload.hex()):
                result = self.module.classify_observation(payload)
                self.assertEqual(
                    result["classification"], "AMBIGUOUS_INTEGRITY_FAILURE"
                )
                self.assertTrue(result["integrity_issue"])
                self.assertFalse(result["accepted"])
                self.assertEqual(result["minimum_candidate_boots"], 0)

    def test_non_bytes_are_rejected(self):
        with self.assertRaises(self.module.DecodeError):
            self.module.classify_observation("not bytes")

    def test_execution_closure_receipts_both_decoders(self):
        sys.path.insert(0, str(SCRIPTS))
        try:
            import device_action_f1_evidence_v2 as evidence
            import device_action_f1_v2 as core

            receipts = core.execution_critical_source_receipts(
                {"kind": evidence.SAME_RING_MULTIBOOT_KIND}
            )
        finally:
            sys.path.remove(str(SCRIPTS))
        required = {
            "runner",
            "typed_evidence",
            "checkpoint_decoder",
            "regular_path_transport",
            "same_ring_multiboot_decoder",
            "same_ring_record_decoder",
            "same_ring_static_checker",
            "same_ring_design_model",
            "same_ring_base_checker",
        }
        self.assertEqual(set(receipts), required)
        for receipt in receipts.values():
            self.assertGreater(receipt["size"], 0)
            self.assertRegex(receipt["sha256"], r"^[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
