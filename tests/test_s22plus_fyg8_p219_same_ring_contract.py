import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "workspace/public/src/scripts/revalidation"
SCRIPT = SCRIPTS / "s22plus_fyg8_p219_same_ring_contract.py"


def load_module():
    sys.path.insert(0, str(SCRIPTS))
    try:
        spec = importlib.util.spec_from_file_location(
            "s22plus_fyg8_p219_same_ring_contract_tested", SCRIPT
        )
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(SCRIPTS))


class S22PlusFyg8P219SameRingContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def compiled_blob(self):
        return (
            b"prefix"
            + self.module.ENTRY_PROOF
            + b"middle"
            + self.module.USERSPACE_PROOF
            + b"middle"
            + self.module.UNSAT_PROOF
            + b"suffix"
        )

    def test_candidate_contract_and_record_bytes_are_fixed(self):
        result = self.module.check_record_derivation()
        self.assertEqual(
            result["contract_sha256"],
            "a01800f437cf129e693f32b7199ea6a613dd2366fff82ca45083f2098fd13bae",
        )
        self.assertEqual(result["contract_id"], "a01800f437cf129e693f32b7199ea6a6")
        self.assertEqual(len(self.module.ENTRY_PROOF), 45)
        self.assertEqual(len(self.module.USERSPACE_PROOF), 45)
        self.assertEqual(len(self.module.UNSAT_PROOF), 24)
        self.assertEqual(result["binding_bits"], 128)

    def test_patch_applies_to_exact_base_with_required_guard_order(self):
        source = ROOT / self.module.DEFAULT_SOURCE
        if not source.is_dir():
            self.skipTest("private FYG8 source is not present")
        result = self.module.run(source, ROOT / self.module.DEFAULT_PATCH)
        self.assertEqual(result["verdict"], self.module.VERDICT)
        self.assertTrue(result["source"]["target_layout_guard"])
        self.assertTrue(result["source"]["pre_post_header_checks"])
        self.assertTrue(result["source"]["source_semantics"])

    def test_compiled_record_cardinality_contract(self):
        result = self.module.classify_compiled_blob(
            self.compiled_blob(), "synthetic-compiled-output"
        )
        self.assertEqual(result["entry_count"], 1)
        self.assertEqual(result["userspace_count"], 1)
        self.assertEqual(result["unsat_count"], 1)
        self.assertEqual(result["long_family_count"], 2)
        self.assertEqual(result["unsat_family_count"], 1)

    def test_fixed_decoder_matches_the_reviewed_design_model(self):
        payloads = (
            b"ordinary",
            self.module.ENTRY_PROOF,
            self.module.USERSPACE_PROOF,
            self.module.UNSAT_PROOF,
            self.module.ENTRY_PROOF * 2,
            self.module.design.ENTRY_FAMILY + b"0" * 32 + b"]]\n",
            b"prefix" + self.module.UNSAT_PROOF[:12],
        )
        for payload in payloads:
            with self.subTest(payload=payload.hex()):
                expected = self.module.design.classify_observation(
                    b"", payload, self.module.RECORDS
                )
                actual = self.module.decoder.classify_observation(payload)
                self.assertEqual(actual, expected)

    def test_compiled_record_cardinality_rejects_missing_duplicate_and_old_e0(self):
        invalid = (
            self.compiled_blob().replace(self.module.UNSAT_PROOF, b""),
            self.compiled_blob() + self.module.ENTRY_PROOF,
            self.compiled_blob() + self.module.OLD_E0_ENTRY_PROOF,
        )
        for blob in invalid:
            with self.subTest(blob_size=len(blob)):
                with self.assertRaises(self.module.CheckError):
                    self.module.classify_compiled_blob(blob, "invalid")

    def test_extracted_artifact_closure_is_exact(self):
        blob = self.compiled_blob()
        result = self.module.verify_extracted_artifact_closure(
            image=blob,
            vmlinux=blob,
            boot_image=b"synthetic boot image",
            extracted_boot_kernel=blob,
            ap_members=[{"name": "boot.img.lz4", "type": "regular"}],
        )
        self.assertTrue(result["boot_kernel"]["equals_image"])
        self.assertTrue(result["boot_only_ap"])

        with self.assertRaisesRegex(self.module.CheckError, "boot-extracted"):
            self.module.verify_extracted_artifact_closure(
                image=blob,
                vmlinux=blob,
                boot_image=b"synthetic boot image",
                extracted_boot_kernel=blob + b"changed",
                ap_members=[{"name": "boot.img.lz4", "type": "regular"}],
            )
        with self.assertRaisesRegex(self.module.CheckError, "one-member"):
            self.module.verify_extracted_artifact_closure(
                image=blob,
                vmlinux=blob,
                boot_image=b"synthetic boot image",
                extracted_boot_kernel=blob,
                ap_members=[
                    {"name": "boot.img.lz4", "type": "regular"},
                    {"name": "vendor_boot.img.lz4", "type": "regular"},
                ],
            )

    def test_host_only_result_creates_no_candidate_or_authority(self):
        source = ROOT / self.module.DEFAULT_SOURCE
        if not source.is_dir():
            self.skipTest("private FYG8 source is not present")
        result = self.module.run(source, ROOT / self.module.DEFAULT_PATCH)
        self.assertTrue(result["safety"]["host_only"])
        self.assertFalse(result["safety"]["kernel_build"])
        self.assertFalse(result["safety"]["image_created"])
        self.assertFalse(result["safety"]["manifest_created"])
        self.assertFalse(result["safety"]["live_authorized"])
        self.assertFalse(
            result["artifact_checker"]["candidate_artifacts_verified"]
        )


if __name__ == "__main__":
    unittest.main()
