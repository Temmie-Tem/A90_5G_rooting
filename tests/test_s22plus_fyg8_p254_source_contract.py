import copy
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "workspace/public/src/scripts/revalidation"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import s22plus_fyg8_p234_candidate_intent as intent  # noqa: E402
import device_action_f1_evidence_v2 as evidence  # noqa: E402
import s22plus_fyg8_p252_source_contract as p252  # noqa: E402
import s22plus_fyg8_p254_e1_decoder as decoder  # noqa: E402
import s22plus_fyg8_p254_source_contract as p254  # noqa: E402
import s22plus_fyg8_source_contracts as contracts  # noqa: E402


class S22PlusFyg8P254SourceContractTest(unittest.TestCase):
    RUN_ID_HEX = "54" * 16

    @classmethod
    def setUpClass(cls):
        cls.reachable = p254.validate_reachable_records(
            bytes.fromhex(cls.RUN_ID_HEX)
        )

    def test_contract_preserves_runtime_and_binds_both_proof_adapters(self):
        self.assertEqual(p254.generate(ROOT), p252.generate(ROOT))
        data, receipts = p254.source_receipts(ROOT)
        self.assertEqual(set(data), p254.SOURCE_KEYS)
        self.assertIn("linked_validator_adapter", data)
        self.assertIn("stock_closure_adapter", data)
        self.assertIn("linked_adapter_dispatch", data)
        self.assertIn("candidate_repro_enforcement", data)
        self.assertEqual(
            receipts["linked_validator_adapter"],
            p254.receipt(data["linked_validator_adapter"]),
        )
        selected = contracts.select(p254.CONTRACT_ID, "E2")
        self.assertIs(selected.module, p254)
        self.assertIs(selected.decoder, decoder)

    def test_adapter_receipt_mutation_changes_derived_run_id(self):
        _data, receipts = p254.source_receipts(ROOT)
        preimage = intent.identity_preimage(
            bytes.fromhex("54" * 16),
            receipts,
            "E2",
            p254.CONTRACT_ID,
        )
        original = intent.derive_run_id(preimage)
        for key in (
            "linked_validator_adapter",
            "stock_closure_adapter",
            "linked_adapter_dispatch",
            "candidate_repro_enforcement",
        ):
            with self.subTest(key=key):
                changed_receipts = copy.deepcopy(receipts)
                changed_receipts[key]["sha256"] = "00" * 32
                changed = intent.identity_preimage(
                    bytes.fromhex("54" * 16),
                    changed_receipts,
                    "E2",
                    p254.CONTRACT_ID,
                )
                self.assertNotEqual(intent.derive_run_id(changed), original)

    def test_implementation_rejects_legacy_global_mutation_tokens(self):
        data = p254.source_bytes(ROOT)
        self.assertNotIn(
            b"legacy.EXPECTED_ELF_ENTRYPOINTS =",
            data["stock_closure_adapter"],
        )
        self.assertNotIn(
            b"_ENTRYPOINT_LOCK",
            data["stock_closure_adapter"],
        )

    def test_reachable_records_use_p254_decoder_identity(self):
        result = self.reachable
        self.assertTrue(result["verified"])
        self.assertEqual(result["decoder_policy_id"], decoder.POLICY_ID)

    def test_process_v2_accepts_exact_p254_reachable_contract_shape(self):
        expected = self.reachable
        with mock.patch.object(
            p254,
            "validate_reachable_records",
            return_value=copy.deepcopy(expected),
        ):
            self.assertEqual(
                evidence._validate_reachable_record_contract(
                    expected,
                    "E2",
                    p254.CONTRACT_ID,
                    self.RUN_ID_HEX,
                ),
                expected,
            )
        self.assertEqual(expected["classifier_detail_count"], 17)

    def test_process_v2_rejects_p254_reachable_contract_drift(self):
        expected = self.reachable
        mutations = []
        missing = copy.deepcopy(expected)
        missing.pop("classifier_detail_count")
        mutations.append(missing)
        changed = copy.deepcopy(expected)
        changed["classifier_detail_count"] += 1
        mutations.append(changed)
        type_alias = copy.deepcopy(expected)
        type_alias["classifier_detail_count"] = True
        mutations.append(type_alias)
        for value in mutations:
            with self.subTest(value=value):
                with mock.patch.object(
                    p254,
                    "validate_reachable_records",
                    return_value=copy.deepcopy(expected),
                ):
                    with self.assertRaises(evidence.EvidenceError):
                        evidence._validate_reachable_record_contract(
                            value,
                            "E2",
                            p254.CONTRACT_ID,
                            self.RUN_ID_HEX,
                        )

    def test_process_v2_legacy_reachable_contract_shape_is_unchanged(self):
        expected = evidence._expected_reachable_record_contract(
            "E1A", None, self.RUN_ID_HEX
        )
        self.assertNotIn("classifier_detail_count", expected)
        self.assertEqual(
            set(expected),
            {
                "reachable_slot_variants",
                "profiles",
                "checked_run_ids",
                "adjacent_slot_combinations_verified",
                "zero_crc_count",
                "family_collision_count",
                "decoder_policy_id",
                "verified",
            },
        )
        self.assertEqual(
            evidence._validate_reachable_record_contract(
                expected, "E1A", None, self.RUN_ID_HEX
            ),
            expected,
        )


if __name__ == "__main__":
    unittest.main()
