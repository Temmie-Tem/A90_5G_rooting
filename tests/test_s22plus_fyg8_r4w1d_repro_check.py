import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / (
    "workspace/public/src/scripts/revalidation/"
    "s22plus_fyg8_r4w1d_repro_check.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location(
        "s22plus_fyg8_r4w1d_repro_tested", SCRIPT
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class S22PlusFyg8R4W1DReproCheckTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_image_gate_requires_compact_proof(self):
        with tempfile.TemporaryDirectory() as name:
            image = Path(name) / "Image"
            data = bytearray(8192)
            header = self.module.static_audit.ARM64_IMAGE_HEADER
            data[: len(header)] = header
            proof = self.module.contract.PROOF.encode("ascii")
            data[4096 : 4096 + len(proof)] = proof
            image.write_bytes(data)
            with mock.patch.object(
                self.module.r4w1d_build.engine, "STOCK_IMAGE_SIZE", len(data)
            ), mock.patch.object(
                self.module.r4w1d_build.engine,
                "FIXED_KERNEL_SLOT_CAPACITY",
                (len(data) + 4095) & ~4095,
            ):
                result = self.module.check_image(image)
            self.assertTrue(result["verified"])
            self.assertEqual(result["marker_count"], 1)

    def test_source_restoration_gate_requires_current_controls_and_runtime(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            builds = []
            links = [
                {
                    "relative_path": f"path-{index}",
                    "expected_target": f"/archive/target-{index}",
                    "actual_target": f"/archive/target-{index}",
                    "restored_target": f"/archive/target-{index}",
                    "verified": True,
                }
                for index in range(self.module.EXPECTED_SOURCE_SYMLINK_COUNT)
            ]
            for index in range(2):
                path = root / f"build-{index}.json"
                payload = {
                    "work_tree": str(root / f"source-{index}"),
                    "provenance": {"source_overlay": {"verified": True}},
                }
                if index == 1:
                    payload["source_symlink_control_runtime"] = {
                        "verified": True,
                        "restored": True,
                        "absolute_symlink_count": len(links),
                        "mutation_count": 3,
                        "members_sha256": "a" * 64,
                        "links": links,
                    }
                path.write_text(__import__("json").dumps(payload), encoding="ascii")
                builds.append(path)
            with mock.patch.object(
                self.module.r4w1d_build,
                "inspect_source_symlink_control",
                return_value={
                    "verified": True,
                    "absolute_symlink_count": len(links),
                    "members_sha256": "a" * 64,
                    "links": links,
                },
            ):
                result = self.module.source_restoration_gate(tuple(builds))
            self.assertTrue(result["verified"])
            self.assertEqual(result["recorded_successful_runtime_count"], 1)
            self.assertFalse(result["final_hardening_full_build_claimed"])

    def test_source_restoration_gate_rejects_count_only_identity_match(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            builds = []
            for index in range(2):
                path = root / f"build-{index}.json"
                path.write_text(
                    __import__("json").dumps(
                        {
                            "work_tree": str(root / f"source-{index}"),
                            "provenance": {
                                "source_overlay": {"verified": True}
                            },
                            "source_symlink_control_runtime": {
                                "verified": True,
                                "restored": True,
                                "absolute_symlink_count": 5,
                                "mutation_count": 3,
                                "members_sha256": "a" * 64,
                                "links": [
                                    {
                                        "relative_path": f"runtime-{row}",
                                        "expected_target": f"/runtime/{row}",
                                        "restored_target": f"/runtime/{row}",
                                        "verified": True,
                                    }
                                    for row in range(5)
                                ],
                            },
                        }
                    ),
                    encoding="ascii",
                )
                builds.append(path)
            with mock.patch.object(
                self.module.r4w1d_build,
                "inspect_source_symlink_control",
                return_value={
                    "verified": True,
                    "absolute_symlink_count": 5,
                    "members_sha256": "b" * 64,
                    "links": [
                        {
                            "relative_path": f"current-{row}",
                            "expected_target": f"/current/{row}",
                            "actual_target": f"/current/{row}",
                            "verified": True,
                        }
                        for row in range(5)
                    ],
                },
            ):
                result = self.module.source_restoration_gate(tuple(builds))
            self.assertFalse(result["verified"])
            self.assertEqual(result["recorded_successful_runtime_count"], 0)
            self.assertFalse(
                result["builds"][0]["recorded_runtime_identity_match"]
            )

    def test_contract_binding_restores_base_engine_globals(self):
        previous = self.module.engine.SCHEMA
        with self.module._bind_engine_contract():
            self.assertEqual(self.module.engine.SCHEMA, self.module.SCHEMA)
            self.assertEqual(
                self.module.engine.WITNESS_CONFIG, self.module.contract.CONFIG
            )
        self.assertEqual(self.module.engine.SCHEMA, previous)


if __name__ == "__main__":
    unittest.main()
