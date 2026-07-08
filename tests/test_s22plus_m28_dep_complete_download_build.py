import importlib.util
import json
import sys
import unittest
from pathlib import Path


SCRIPT = Path("workspace/public/src/scripts/revalidation/build_s22plus_m28_dep_complete_download.py")
SOURCE = Path("workspace/public/src/native-init/s22plus_init_m28_dep_complete_download.c")
OUTPUT_MANIFEST = Path("workspace/private/outputs/s22plus_native_init/m28_dep_complete_download_v0_1/manifest.json")


def load_module():
    script_dir = str(SCRIPT.parent.resolve())
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location("build_s22plus_m28_dep_complete_download", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class S22PlusM28DepCompleteDownloadBuildTest(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_variant_constants(self):
        self.assertEqual(self.module.MARKER, "S22_NATIVE_INIT_M28_DEP_COMPLETE_DOWNLOAD")
        self.assertEqual(self.module.M28_MODULES_RAMDISK, "s22plus_m28_dep_complete.modules")
        self.assertEqual(self.module.DEFAULT_VARIANTS, ("S24", "F43"))
        self.assertEqual(
            self.module.REINCLUDED_HARD_SUPPLIERS,
            ("sec_debug.ko", "minidump.ko", "abc.ko"),
        )
        self.assertIn("qcom_wdt_core.ko", self.module.M28_EXCLUDED_MODULES)
        self.assertIn("phy-msm-ssusb-qmp.ko", self.module.M28_EXCLUDED_MODULES)
        self.assertNotIn("sec_debug.ko", self.module.M28_EXCLUDED_MODULES)
        self.assertNotIn("minidump.ko", self.module.M28_EXCLUDED_MODULES)
        self.assertNotIn("abc.ko", self.module.M28_EXCLUDED_MODULES)

    def test_variant_targets(self):
        modules = self.module.EXPECTED_M25_HS_ONLY_SUBSET
        self.assertEqual(self.module.variant_targets("S24"), modules[:24])
        self.assertEqual(self.module.variant_targets("F43"), modules)
        with self.assertRaises(SystemExit):
            self.module.variant_targets("P08")

    def test_source_is_download_beacon_not_acm_park(self):
        text = SOURCE.read_text(encoding="utf-8")
        self.assertIn("S22_NATIVE_INIT_M28_DEP_COMPLETE_DOWNLOAD", text)
        self.assertIn("modules_dep_complete=/s22plus_m28_dep_complete.modules", text)
        self.assertIn("module_list=dep_complete_hs_only", text)
        self.assertIn("observation=dep-complete-download", text)
        self.assertIn("reboot_request=download", text)
        self.assertIn("sys_reboot(", text)
        self.assertNotIn("/config", text)
        self.assertNotIn("ttyGS0", text)
        self.assertNotIn("ss_acm.0", text)

    def test_dependency_complete_order_rejects_excluded_hard_dep(self):
        dep_map = {
            "root.ko": ["qcom_wdt_core.ko"],
            "qcom_wdt_core.ko": [],
        }
        with self.assertRaises(SystemExit):
            self.module.dependency_complete_order(
                targets=["root.ko"],
                dep_map=dep_map,
                recovery_basenames=["qcom_wdt_core.ko", "root.ko"],
            )

    def test_dependency_complete_order_toposorts_suppliers_first(self):
        dep_map = {
            "clk-rpmh.ko": ["minidump.ko", "sec_debug.ko"],
            "minidump.ko": ["smem.ko"],
            "sec_debug.ko": [],
            "smem.ko": [],
        }
        closure = self.module.dependency_complete_order(
            targets=["clk-rpmh.ko"],
            dep_map=dep_map,
            recovery_basenames=["clk-rpmh.ko", "minidump.ko", "sec_debug.ko", "smem.ko"],
        )
        self.assertEqual(closure["modules"], ["smem.ko", "minidump.ko", "sec_debug.ko", "clk-rpmh.ko"])
        self.assertEqual(closure["reincluded_hard_suppliers"], ["sec_debug.ko", "minidump.ko"])

    @unittest.skipUnless(OUTPUT_MANIFEST.exists(), "private M28 manifest missing")
    def test_current_output_manifest_is_dep_complete_matrix(self):
        data = json.loads(OUTPUT_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(
            data["purpose"],
            "M28 dependency-complete HS-only download-beacon matrix; stop blind P01..P08 bisection",
        )
        self.assertEqual(data["safety"]["host_only_build"], True)
        self.assertEqual(data["safety"]["live_flash_authorized"], False)
        self.assertEqual(data["safety"]["device_action"], False)
        self.assertEqual(data["policy"]["reincluded_hard_suppliers"], ["sec_debug.ko", "minidump.ko", "abc.ko"])
        self.assertEqual(data["policy"]["watchdog_excluded"], ["qcom_wdt_core.ko", "gh_virt_wdt.ko"])
        expected = [
            (
                "S24",
                26,
                ["sec_debug.ko", "minidump.ko"],
                "8c605e2c69aad74f80191bdbc1843b002539d22d49bcffa86bb85bbcb343e5e4",
                "c684f6a21bcc9aa50b066b447f4356958fe6d7bfed93edf0ac1b7dcaae8ce75f",
                "a1459931001bfd6e17593dd329fc682f00ab61f4841b6543791f5349dd012cd0",
                "5c04a2023b2b56ef98746da6f7168121b62d7859cee81c756b80d1a382c1964e",
            ),
            (
                "F43",
                43,
                ["sec_debug.ko", "minidump.ko", "abc.ko"],
                "430050d648d85dd6c3fea459a6cd627a58fd234afe1b485820ccc1f2eb65f87b",
                "003ea5760d9e33402750afd7a52b6b95727e4b4cff3f4d3cf66c559eabbb38d1",
                "6453b8f2dd685757148056ba8767c2820b0547123f4e5e5e423c4adb0c70496c",
                "68de58cd3f05fd77af00984027948ad5ab953ae128dc4133d336e0a521cd588f",
            ),
        ]
        seen = [
            (
                entry["label"],
                entry["module_count"],
                entry["reincluded_hard_suppliers"],
                entry["modules_sha256"],
                entry["ap_tar_md5_sha256"],
                entry["boot_img_sha256"],
                entry["init_sha256"],
            )
            for entry in data["variants"]
        ]
        self.assertEqual(seen, expected)
        for label, _count, _suppliers, _modules_sha, _ap_sha, _boot_sha, _init_sha in expected:
            ap = OUTPUT_MANIFEST.parent / label / "odin4" / "AP.tar.md5"
            self.assertEqual(self.module.tar_members(ap), ["boot.img.lz4"])
            variant_manifest = json.loads((OUTPUT_MANIFEST.parent / label / "manifest.json").read_text(encoding="utf-8"))
            modules = variant_manifest["closure"]["modules"]
            self.assertFalse(set(modules) & set(self.module.M28_EXCLUDED_MODULES))
            self.assertEqual(len(modules), len(set(modules)))


if __name__ == "__main__":
    unittest.main()
