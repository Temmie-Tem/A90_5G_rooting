import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(
    "workspace/public/src/scripts/revalidation/"
    "build_s22plus_v3429_phase_observer.py"
)
SOURCE = Path(
    "workspace/public/src/native-init/s22plus_init_v3429_phase_observer.c"
)
DEFAULT_MANIFEST = Path(
    "workspace/private/outputs/s22plus_native_init/"
    "v3429_phase_observer_v0_1/manifest.json"
)


def load_module():
    script_dir = str(SCRIPT.parent.resolve())
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location(
        "build_s22plus_v3429_phase_observer", SCRIPT
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class S22PlusV3429PhaseObserverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()
        cls.root = cls.module.repo_root()
        cls.source = cls.root / SOURCE
        cls.run_id = "0123456789abcdef0123456789abcdef"
        cls.source_sha = cls.module.sha256_file(cls.source)
        cls.base_sha = cls.module.EXPECTED_BASE_BOOT_SHA256
        cls.expectation = cls.module.make_expectation(
            cls.run_id, cls.source_sha, cls.base_sha
        )
        cls.record = cls.module.marker_record(
            cls.expectation, cls.source_sha, cls.base_sha
        )

    def test_source_contract_is_narrow_and_parks(self):
        contract = self.module.verify_source_contract(self.source)
        self.assertEqual(contract["module_load_call_count"], 1)
        self.assertEqual(contract["precheck_emit_call_count"], 1)
        self.assertEqual(contract["final_emit_call_count"], 1)
        self.assertTrue(contract["all_paths_park"])

    def test_contexts_bind_phase_and_source(self):
        self.assertNotEqual(
            self.expectation.precheck_context_sha256,
            self.expectation.final_context_sha256,
        )
        changed = self.module.make_expectation(
            self.run_id, "f" * 64, self.base_sha
        )
        self.assertNotEqual(
            self.expectation.precheck_context_sha256,
            changed.precheck_context_sha256,
        )

    def test_expected_frames_roundtrip_through_v3426_classifier(self):
        precheck = self.module.observer.encode_marker(
            self.expectation, self.module.observer.PHASE_PRECHECK
        )
        final = self.module.observer.encode_marker(
            self.expectation, self.module.observer.PHASE_FINAL
        )
        baseline = self.module.observer.classify_marker_snapshot(
            "baseline", b"foreign-data", self.expectation
        )
        precheck_result = self.module.observer.classify_marker_snapshot(
            "precheck", precheck, self.expectation
        )
        final_result = self.module.observer.classify_marker_snapshot(
            "final", precheck + b"\n" + final, self.expectation
        )
        self.assertTrue(baseline["pass"])
        self.assertTrue(precheck_result["pass"])
        self.assertTrue(final_result["pass"])

    def test_generated_header_pins_exact_frames_and_guard_byte(self):
        header = self.module.render_generated_header(self.record)
        self.assertIn(self.record["precheck_frame"], header)
        self.assertIn(self.record["final_frame"], header)
        self.assertIn(
            f"#define V3429_RING_MAX_BYTES {self.module.RING_MAX_BYTES}U",
            header,
        )
        source = self.source.read_text(encoding="ascii")
        self.assertIn("V3429_RING_MAX_BYTES + 1U", source)
        self.assertIn("if (amount != 0)", source)

    def test_runtime_source_uses_length_bounded_ordered_counts(self):
        source = self.source.read_text(encoding="ascii")
        self.assertNotIn("strstr", source)
        self.assertIn("cursor + pattern_size <= buffer_size", source)
        self.assertIn("counts.first_precheck >= counts.first_final", source)
        self.assertIn("counts.raw_run_count != expected_raw", source)
        self.assertIn(
            '"S22_V3429_PHASE_OBSERVER_FAIL " V3429_RAW_RUN_TOKEN',
            source,
        )
        self.assertIn("char output[128]", source)
        self.assertIn("char too_small[64]", source)
        self.assertIn("short_size == 0U", source)
        self.assertIn("V3429_FAILURE_SELFTEST_ONLY", source)

    def test_compile_and_qemu_sha_selftest(self):
        with tempfile.TemporaryDirectory() as temp:
            build_dir = Path(temp)
            generated = build_dir / "generated"
            generated.mkdir()
            (generated / "s22plus_v3429_phase_observer.generated.h").write_text(
                self.module.render_generated_header(self.record), encoding="ascii"
            )
            output = build_dir / "init"
            info = self.module.compile_init(
                self.source, generated, output, build_dir, self.record
            )
            self.assertTrue(info["sha256_known_vector_qemu"])
            self.assertTrue(info["failure_full_run_token_qemu"])
            self.assertTrue(info["no_interp"])
            self.assertEqual(info["undefined_symbols"], [])
            self.assertLess(info["size"], 131072)

    @unittest.skipUnless(DEFAULT_MANIFEST.is_file(), "V3429 manifest unavailable")
    def test_built_manifest_is_host_only_and_exact(self):
        manifest = json.loads(DEFAULT_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema"], self.module.SCHEMA)
        self.assertEqual(manifest["tar_members"], ["boot.img.lz4"])
        self.assertEqual(
            manifest["contracts"]["observer_sha256"],
            self.module.observer.CONTRACT_SHA256,
        )
        self.assertEqual(
            manifest["contracts"]["transition_sha256"],
            self.module.transition.TRANSITION_SHA256,
        )
        self.assertEqual(manifest["hashes"]["source"], self.source_sha)
        self.assertEqual(
            manifest["expected_markers"]["source_sha256"], self.source_sha
        )
        self.assertEqual(manifest["init"]["sha256"], manifest["hashes"]["init"])
        self.assertTrue(manifest["init"]["failure_full_run_token_qemu"])
        self.assertFalse(manifest["safety"]["live_flash_authorized"])
        self.assertTrue(manifest["safety"]["pid1_never_exits"])
        self.assertFalse(manifest["safety"]["candidate_transition"])


if __name__ == "__main__":
    unittest.main()
