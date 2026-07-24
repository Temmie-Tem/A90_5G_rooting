import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "workspace/public/src/scripts/revalidation"
CHECKER_PATH = (
    SCRIPT_DIR / "s22plus_fyg8_p251_ssusb_dependency_audit.py"
)
PRIVATE_READY = all(
    (ROOT / path).is_file()
    for path in (
        "workspace/private/outputs/s22plus_fyg8_p249/candidate-a/boot.img",
        "workspace/private/outputs/s22plus_fyg8_p249/artifacts-a/.config",
        "workspace/private/outputs/s22plus_fyg8_p249/intent/"
        "materialized-sources/s22plus_fyg8_p244_e2_plan.h",
        "workspace/private/outputs/s22plus_fyg8_p249/intent/"
        "materialized-sources/s22plus_fyg8_p248_e2_runtime.c",
        "workspace/private/runs/device-action-f1-live-v2/"
        "p249-20260724-2/live-result.json",
        "workspace/private/inputs/s22plus_firmware/S906NKSS7FYG8_SKC/"
        "extracted-images/raw/vendor_boot.img",
        "workspace/private/inputs/s22plus_firmware/S906NKSS7FYG8_SKC/"
        "extracted-images/unpack-vendor-boot/dtb",
        "workspace/private/inputs/s22plus_firmware/S906NKSS7FYG8_SKC/"
        "extracted-images/ramdisk-list/vendor/extract/lib/modules/dwc3-msm.ko",
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


@unittest.skipUnless(PRIVATE_READY, "exact FYG8 private inputs are unavailable")
class P251SsusbDependencyAuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load(
            "s22plus_fyg8_p251_ssusb_dependency_audit_tested",
            CHECKER_PATH,
        )
        cls.result = cls.module.build_result()

    def test_host_only_audit_passes(self):
        self.assertEqual(self.result["verdict"], self.module.VERDICT)
        self.assertTrue(self.result["safety"]["host_only"])
        for key, value in self.result["safety"].items():
            if key != "host_only":
                self.assertFalse(value, key)

    def test_live_frontier_is_gcc_then_ssusb_timeout(self):
        live = self.result["live_frontier"]
        self.assertEqual(live["previous_gate"]["id"], "gcc-waipio")
        self.assertEqual(live["previous_gate"]["stage"], "0x83")
        self.assertEqual(live["previous_gate"]["outcome"], "success")
        self.assertEqual(live["active_gate"]["id"], "ssusb")
        self.assertEqual(live["active_gate"]["stage"], "0x84")
        self.assertEqual(live["active_gate"]["detail"], 110)
        self.assertTrue(live["rollback_verified"])

    def test_timeout_is_global_not_dedicated_to_ssusb(self):
        runtime = self.result["plan_runtime"]
        self.assertEqual(runtime["module_count"], 59)
        self.assertTrue(runtime["all_modules_checked_before_gate_deadline"])
        self.assertEqual(runtime["deadline_scope"], "all-12-gates-shared")
        self.assertEqual(
            runtime["ssusb_observation_window_sec"],
            {"lower_bound": 0, "upper_bound": 20, "exact": None},
        )
        self.assertFalse(runtime["per_gate_timestamps_retained"])

    def test_exact_dtb_and_stock_supplier_sets_are_closed(self):
        tree = self.result["vendor_dtb"]
        self.assertEqual(tree["blob_count"], 4)
        self.assertEqual(
            set(tree["common_topology"]["interconnect"]),
            self.module.EXPECTED_DIRECT_DT_PROVIDERS["interconnect"],
        )
        self.assertEqual(
            set(self.result["stock_control"]["supplier_links"]),
            self.module.EXPECTED_STOCK_SUPPLIERS,
        )
        self.assertTrue(
            all(not row["redriver_phandle"] for row in tree["variants"])
        )

    def test_reasoning_keeps_root_cause_open_and_rules_out_growth(self):
        hypotheses = {
            row["id"]: row for row in self.result["hypotheses"]
        }
        self.assertEqual(hypotheses["H1"]["status"], "OPEN_HIGH_PRIORITY")
        self.assertEqual(hypotheses["H4"]["status"], "OPEN_CONFOUND")
        self.assertEqual(
            hypotheses["H5"]["status"], "RULED_OUT_FOR_P250_FRONTIER"
        )
        self.assertEqual(hypotheses["H6"]["status"], "RULED_OUT")
        conclusion = self.result["conclusion"]
        self.assertFalse(conclusion["exact_root_cause_identified"])
        self.assertFalse(
            conclusion["another_unchanged_live_candidate_justified"]
        )

    def test_bounded_discriminator_has_no_module_growth(self):
        discriminator = self.result["bounded_discriminator"]
        self.assertEqual(
            discriminator["action"],
            "classify-ssusb-timeout-without-module-growth",
        )
        self.assertEqual(discriminator["frontier_stage"], "0x84")
        self.assertEqual(discriminator["add_modules"], [])
        self.assertEqual(len(discriminator["provider_checks"]), 7)
        self.assertEqual(len(discriminator["phy_checks"]), 2)
        self.assertEqual(
            discriminator["bounded_timing_correction"][
                "maximum_added_runtime_sec"
            ],
            5,
        )
        self.assertEqual(
            discriminator["structured_detail_partition"][
                "ssusb_classifier"
            ],
            "0xa00..0xaff",
        )
        self.assertIn(
            "reserved and rejected",
            discriminator["current_contract_state"],
        )
        self.assertIn(
            "descriptor SoT",
            discriminator["required_contract_change"],
        )

    def test_checker_contains_no_device_or_build_action(self):
        source = CHECKER_PATH.read_text(encoding="ascii")
        for token in (
            "adb ",
            "odin4 ",
            "fastboot ",
            "subprocess.",
            "finit_module(",
            "reboot(",
        ):
            self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
