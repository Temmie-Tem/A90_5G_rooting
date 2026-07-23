import importlib.util
import io
import json
import re
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "workspace/public/src/scripts/revalidation"
SOURCES_PATH = (
    SCRIPT_DIR / "s22plus_fyg8_p244_e2_provider_sources.py"
)
CHECKER_PATH = SCRIPT_DIR / "s22plus_fyg8_p244_e2_static_checker.py"
PRIVATE_READY = all(
    (ROOT / path).exists()
    for path in (
        "workspace/private/work/s22plus_fyg8_kernel_rebuild_r0",
        "workspace/private/outputs/s22plus_fyg8_p242/candidate-a/boot.img",
        "workspace/private/outputs/s22plus_fyg8_p242/artifacts-a/.config",
        "workspace/private/inputs/s22plus_firmware/S906NKSS7FYG8_SKC/"
        "extracted-images/raw/vendor_boot.img",
        "workspace/private/inputs/s22plus_firmware/S906NKSS7FYG8_SKC/"
        "extracted-images/unpack-vendor-boot/dtb",
        "workspace/private/inputs/s22plus_firmware/S906NKSS7FYG8_SKC/"
        "extracted-images/unpack-vendor-boot/vendor_ramdisk00",
        "workspace/private/inputs/s22plus_kernel_source/"
        "SM-S906N_15_base_osrc/Kernel.tar.gz",
        "workspace/private/inputs/s22plus_kernel_source/"
        "S906NKSS7FYG8_osrc/S906NKSS7FYG8_kernel.tar.gz",
    )
)


def load(name: str, path: Path):
    if str(SCRIPT_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPT_DIR))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class P244ProviderSourceUnitTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = load(
            "s22plus_fyg8_p244_e2_provider_sources_public_tested",
            SOURCES_PATH,
        )
        cls.checker = load(
            "s22plus_fyg8_p244_e2_static_checker_public_tested",
            CHECKER_PATH,
        )

    def test_public_source_generation_is_exact(self):
        result = self.sources.build_result()
        self.assertEqual(result["verdict"], self.sources.VERDICT)
        self.assertEqual(result["gate_count"], 12)
        self.assertEqual(
            {
                name: row["sha256"]
                for name, row in result["generated"].items()
            },
            self.sources.GENERATED_SHA256,
        )

    def test_gate_contract_is_independent_of_generator_constants(self):
        dependency = {
            "replaces_existing_gates": ["rpmh", "gcc-waipio"],
            "provider_chain": [
                {
                    "id": "psci-domain",
                    "path": "/sys/bus/platform/drivers/"
                    "psci-cpuidle-domain/soc:psci",
                },
                {
                    "id": "apps-rsc",
                    "path": "/sys/bus/platform/drivers/rpmh/17a00000.rsc",
                },
                {
                    "id": "apps-rpmh-clock",
                    "path": "/sys/bus/platform/drivers/clk-rpmh/"
                    "17a00000.rsc:qcom,rpmhclk",
                },
                {
                    "id": "apps-rpmh-cxlvl",
                    "path": "/sys/bus/platform/drivers/qcom,rpmh-regulator/"
                    "17a00000.rsc:rpmh-regulator-cxlvl",
                },
                {
                    "id": "apps-rpmh-mxlvl",
                    "path": "/sys/bus/platform/drivers/qcom,rpmh-regulator/"
                    "17a00000.rsc:rpmh-regulator-mxlvl",
                },
                {
                    "id": "gcc-waipio",
                    "path": "/sys/bus/platform/drivers/gcc-waipio/"
                    "100000.clock-controller",
                },
            ],
        }
        base = (
            ROOT / self.sources.BASE_PATHS["plan"]
        ).read_text(encoding="ascii")
        expected = self.checker._expected_gates_from_p241(base, dependency)
        generated = self.sources.generate(ROOT)["plan"].decode("ascii")
        actual = self.checker._parse_plan_gates(generated)
        self.assertEqual(actual, expected)
        self.assertEqual(
            [row[1] for row in expected],
            [
                "hwspinlock",
                "smem",
                "cmd-db",
                "psci-domain",
                "apps-rsc",
                "apps-rpmh-clock",
                "apps-rpmh-cxlvl",
                "apps-rpmh-mxlvl",
                "gcc-waipio",
                "ssusb",
                "dwc3-core",
                "udc",
            ],
        )
        self.assertEqual(expected[-1][2], "class-device")
        runtime = self.sources.generate(ROOT)["runtime"].decode("ascii")
        self.assertEqual(
            self.checker._parse_runtime_basenames(runtime),
            tuple(
                row[3].rsplit("/", 1)[-1]
                for row in expected
                if row[2] == "driver-bind-symlink"
            ),
        )

    def test_transform_cardinality_drift_fails_closed(self):
        with self.assertRaises(self.sources.SourceError):
            self.sources.transform_plan(b"")


@unittest.skipUnless(PRIVATE_READY, "exact FYG8 private inputs are unavailable")
class P244E2ProviderImplementationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = load(
            "s22plus_fyg8_p244_e2_provider_sources_tested",
            SOURCES_PATH,
        )
        cls.checker = load(
            "s22plus_fyg8_p244_e2_static_checker_tested",
            CHECKER_PATH,
        )
        cls.result = cls.checker.build_result()

    def test_host_only_implementation_passes(self):
        self.assertEqual(self.result["verdict"], self.checker.VERDICT)
        self.assertTrue(self.result["safety"]["host_only"])
        for key, value in self.result["safety"].items():
            if key != "host_only":
                self.assertFalse(value, key)

    def test_historical_inputs_are_pinned_and_generated_outputs_are_exact(self):
        generation = self.result["generation"]
        self.assertEqual(generation["gate_count"], 12)
        self.assertEqual(generation["driver_gate_count"], 11)
        self.assertEqual(
            {
                name: row["sha256"]
                for name, row in generation["base"].items()
            },
            self.sources.BASE_SHA256,
        )
        self.assertEqual(
            {
                name: row["sha256"]
                for name, row in generation["generated"].items()
            },
            self.sources.GENERATED_SHA256,
        )

    def test_plan_is_the_same_59_modules_with_12_provider_gates(self):
        plan = self.result["plan"]
        self.assertEqual(plan["module_count"], 59)
        self.assertEqual(plan["constraint_count"], 210)
        self.assertEqual(plan["gate_count"], 12)
        self.assertTrue(plan["module_order_unchanged"])
        self.assertTrue(plan["display_module_absent"])
        self.assertEqual(
            [row["id"] for row in plan["gates"]],
            [
                "hwspinlock",
                "smem",
                "cmd-db",
                "psci-domain",
                "apps-rsc",
                "apps-rpmh-clock",
                "apps-rpmh-cxlvl",
                "apps-rpmh-mxlvl",
                "gcc-waipio",
                "ssusb",
                "dwc3-core",
                "udc",
            ],
        )
        self.assertEqual(
            plan["preserved_from_p241"],
            ["hwspinlock", "smem", "cmd-db", "ssusb", "dwc3-core", "udc"],
        )
        self.assertTrue(plan["gate_ids_unique"])
        self.assertTrue(plan["gate_paths_unique"])
        self.assertTrue(plan["last_gate_udc_class"])
        self.assertTrue(
            self.result["sources"]["basenames_derived_from_gate_paths"]
        )

    def test_profile3_sequence_and_reachable_records_expand_exactly(self):
        self.assertEqual(self.result["patch"]["sequence_count"], 80)
        self.assertEqual(self.result["patch"]["gate_stage_count"], 12)
        self.assertEqual(self.result["patch"]["terminal"], 0x8F)
        self.assertEqual(
            self.result["reachable_record_contract"][
                "reachable_slot_variants"
            ],
            323_585,
        )
        self.assertEqual(
            self.result["e1a_e1b_regression"]["reachable_slot_variants"],
            90_114,
        )

    def test_linked_runtime_is_static_reproducible_and_display_free(self):
        linked = self.result["linked_userspace"]
        self.assertTrue(linked["init"]["static_aarch64"])
        self.assertEqual(linked["init"]["undefined_symbols"], 0)
        self.assertEqual(linked["init"]["run_id_count"], 1)
        self.assertTrue(linked["two_link_reproducible"])
        self.assertTrue(linked["all_12_gate_paths_exact"])
        self.assertTrue(linked["retired_display_scope_absent"])
        self.assertEqual(linked["child"]["qemu_exit"], 23)
        self.assertTrue(linked["child"]["token_exact"])

    def test_dependency_contract_preserves_the_live_caveat(self):
        dependency = self.result["dependency_contract"]
        self.assertEqual(
            dependency["failure_classification"],
            "STATIC_MISSING_DISPLAY_CLOCK_SUPPLIER_EXPLANATION",
        )
        self.assertFalse(dependency["p242_live_root_cause_proven"])
        self.assertEqual(
            [row["id"] for row in dependency["provider_chain"]],
            [
                "psci-domain",
                "apps-rsc",
                "apps-rpmh-clock",
                "apps-rpmh-cxlvl",
                "apps-rpmh-mxlvl",
                "gcc-waipio",
            ],
        )

    def test_tools_contain_no_device_build_or_flash_action(self):
        combined = SOURCES_PATH.read_text(
            encoding="ascii"
        ) + CHECKER_PATH.read_text(encoding="ascii")
        for pattern in (
            r'["\'](?:adb|odin4|fastboot)["\']',
            r"\bfinit_module\s*\(",
            r"\breboot\s*\(",
            r'["\'][^"\']*prepare_vendor(?:\.sh)?["\']',
        ):
            self.assertIsNone(re.search(pattern, combined), pattern)

    def test_checker_timeout_is_reported_fail_closed(self):
        output = io.StringIO()
        with mock.patch.object(
            self.checker,
            "build_result",
            side_effect=subprocess.TimeoutExpired(["fixture"], 1),
        ), redirect_stdout(output):
            self.assertEqual(self.checker.main(), 1)
        result = json.loads(output.getvalue())
        self.assertEqual(result["verdict"], "FAIL_CLOSED")


if __name__ == "__main__":
    unittest.main()
