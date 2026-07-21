import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / (
    "workspace/public/src/scripts/revalidation/"
    "s22plus_fyg8_p218_same_ring_discriminator.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location(
        "s22plus_fyg8_p218_same_ring_discriminator_tested", SCRIPT
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class S22PlusFyg8P218SameRingDiscriminatorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()
        cls.records = cls.module.build_records(b"canonical-candidate-contract")

    def header(self, *, idx, magic=None, boot_cnt=7):
        return self.module.retained.Header(
            boot_cnt=boot_cnt,
            magic=(
                self.module.retained.LOG_MAGIC if magic is None else magic
            ),
            idx=idx,
            prev_idx=3,
        )

    def test_record_shapes_keep_128_bit_binding(self):
        self.assertEqual(len(self.records.entry), 45)
        self.assertEqual(len(self.records.userspace), 45)
        self.assertEqual(len(self.records.unsat), 24)
        self.assertEqual(self.module.BINDING_BITS, 128)
        self.assertTrue(self.records.unsat.startswith(self.module.UNSAT_FAMILY))
        self.assertNotEqual(self.records.entry, self.records.userspace)

    def test_record_derivation_is_deterministic_and_domain_separated(self):
        repeated = self.module.build_records(b"canonical-candidate-contract")
        changed = self.module.build_records(b"another-candidate-contract")
        self.assertEqual(repeated, self.records)
        self.assertNotEqual(changed.entry, self.records.entry)
        self.assertNotEqual(changed.userspace, self.records.userspace)
        self.assertNotEqual(changed.unsat, self.records.unsat)
        self.assertEqual(len({self.records.entry, self.records.userspace,
                              self.records.unsat}), 3)

    def test_state_partition_at_exact_thresholds(self):
        expected = {
            0: "NONE",
            23: "NONE",
            24: "UNSAT",
            44: "UNSAT",
            45: "ENTRY",
        }
        for idx, state in expected.items():
            with self.subTest(idx=idx):
                plan = self.module.select_write(
                    records=self.records,
                    post_exec_hook_reached=True,
                    init_filename="/init",
                    pid=1,
                    header=self.header(idx=idx),
                    payload_size=128,
                )
                self.assertEqual(plan.state, state)

    def test_invalid_magic_path_pid_and_nonselection_never_write(self):
        cases = (
            {"magic": 0},
            {"init_filename": "/system/bin/init"},
            {"pid": 2},
            {"post_exec_hook_reached": False},
        )
        for overrides in cases:
            with self.subTest(overrides=overrides):
                plan = self.module.select_write(
                    records=self.records,
                    post_exec_hook_reached=overrides.get(
                        "post_exec_hook_reached", True
                    ),
                    init_filename=overrides.get("init_filename", "/init"),
                    pid=overrides.get("pid", 1),
                    header=self.header(idx=45, magic=overrides.get("magic")),
                    payload_size=128,
                )
                self.assertEqual(plan.state, "NONE")
                self.assertIsNone(plan.record)

    def test_header_change_around_write_fails_closed(self):
        header = self.header(idx=45)
        plan = self.module.select_write(
            records=self.records,
            post_exec_hook_reached=True,
            init_filename="/init",
            pid=1,
            header=header,
            payload_size=128,
        )
        changed = self.header(idx=46)
        with self.assertRaises(self.module.ContractError):
            self.module.apply_write(
                b"\xa5" * 128,
                plan=plan,
                header_before=header,
                header_after=changed,
            )

    def test_boundary_partition_holds_across_rotations(self):
        for idx in range(0, 128 * 4 + 1):
            with self.subTest(idx=idx):
                result = self.module.simulate(
                    self.records,
                    idx=idx,
                    payload_size=128,
                )
                expected = (
                    "ZERO_AMBIGUOUS"
                    if idx < 24
                    else "UNSAT_VALID_MAGIC_ENTRY_DID_NOT_FIT"
                    if idx < 45
                    else "ENTRY_ONLY"
                )
                self.assertEqual(result["classification"], expected)

    def test_entry_and_unsat_leave_index_unchanged(self):
        for idx in (24, 44, 45, 127, 128, 129, 511):
            with self.subTest(idx=idx):
                result = self.module.simulate(
                    self.records,
                    idx=idx,
                    payload_size=128,
                )
                self.assertEqual(result["snapshot_size"], min(idx, 128))

    def test_userspace_is_the_only_accepted_positive_state(self):
        userspace = self.module.classify_observation(
            b"clean", self.records.userspace, self.records
        )
        entry = self.module.classify_observation(
            b"clean", self.records.entry, self.records
        )
        unsat = self.module.classify_observation(
            b"clean", self.records.unsat, self.records
        )
        self.assertEqual(userspace["classification"], "USERSPACE_CALLBACK_REACHED")
        self.assertTrue(userspace["accepted"])
        self.assertEqual(entry["classification"], "ENTRY_ONLY")
        self.assertFalse(entry["accepted"])
        self.assertEqual(
            unsat["classification"],
            "UNSAT_VALID_MAGIC_ENTRY_DID_NOT_FIT",
        )
        self.assertFalse(unsat["accepted"])

    def test_zero_remains_explicitly_ambiguous(self):
        result = self.module.classify_observation(b"clean", b"ordinary", self.records)
        self.assertEqual(result["classification"], "ZERO_AMBIGUOUS")
        self.assertFalse(result["accepted"])
        self.assertIn("retained magic invalid", result["residual_zero_meanings"])
        self.assertIn(
            "candidate or post-exec hook not reached",
            result["residual_zero_meanings"],
        )

    def test_duplicate_cross_family_and_foreign_records_fail_closed(self):
        payloads = (
            self.records.entry + self.records.entry,
            self.records.entry + self.records.unsat,
            self.module.ENTRY_FAMILY + b"0" * 32 + b"]]\n",
            self.module.UNSAT_FAMILY + b"0" * 16,
        )
        for payload in payloads:
            with self.subTest(payload=payload):
                result = self.module.classify_observation(
                    b"clean", payload, self.records
                )
                self.assertEqual(
                    result["classification"], "AMBIGUOUS_INTEGRITY_FAILURE"
                )
                self.assertTrue(result["integrity_issue"])
                self.assertFalse(result["accepted"])

    def test_partial_record_at_snapshot_edge_fails_closed(self):
        result = self.module.classify_observation(
            b"clean", b"prefix" + self.records.unsat[:12], self.records
        )
        self.assertEqual(
            result["classification"], "AMBIGUOUS_INTEGRITY_FAILURE"
        )
        self.assertTrue(result["partial_at_snapshot_edge"])

    def test_dirty_baseline_is_rejected(self):
        for baseline in (
            self.records.entry,
            self.records.unsat,
            b"prefix" + self.records.entry[:12],
        ):
            with self.subTest(baseline=baseline):
                with self.assertRaises(self.module.ContractError):
                    self.module.classify_observation(
                        baseline, self.records.userspace, self.records
                    )

    def test_host_only_result_has_no_artifact_or_live_authority(self):
        result = self.module.build_result()
        self.assertEqual(result["verdict"], self.module.VERDICT)
        self.assertTrue(result["host_only"])
        self.assertFalse(result["candidate_artifact_created"])
        self.assertFalse(result["f1_authority_created"])
        self.assertEqual(
            result["acceptance"], "USERSPACE_CALLBACK_REACHED only"
        )
        self.assertTrue(result["record_contract"]["model_identity_only"])


if __name__ == "__main__":
    unittest.main()
