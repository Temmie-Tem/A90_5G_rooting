from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from _loader import load_script


runner = load_script("workspace/public/src/scripts/revalidation/native_doomgeneric_port_probe_v3020.py")


class NativeDoomgenericPortProbeV3020Tests(unittest.TestCase):
    def test_collect_state_reads_pinned_private_source(self) -> None:
        state = runner.collect_state(build=False)
        source = state["source"]

        self.assertEqual(state["run_id"], "V3020")
        self.assertEqual(state["decision"], "v3020-doomgeneric-private-source-build-probe-pass")
        self.assertTrue(source["source_exists"])
        self.assertEqual(source["git_head"], runner.PINNED_COMMIT)
        self.assertTrue(source["git_head_matches_pin"])
        self.assertTrue(source["git_status_clean"])
        self.assertGreater(source["source_file_count"], 100)
        self.assertEqual(state["public_wads"]["count"], 0)
        self.assertFalse(state["asset_policy"]["commit_wad"])
        self.assertFalse(state["asset_policy"]["embed_wad_in_boot_image"])
        self.assertTrue(state["safe_to_continue_host_only"])

    def test_adapter_source_maps_doompad_edges_to_doomgeneric_keys(self) -> None:
        source = runner.ADAPTER_SOURCE_TEXT

        self.assertIn("void a90_doomgeneric_feed_snapshot", source)
        self.assertIn("queue_edge(snapshot->forward, &last_forward, KEY_UPARROW)", source)
        self.assertIn("queue_edge(snapshot->fire, &last_fire, KEY_FIRE)", source)
        self.assertIn("queue_edge(snapshot->run, &last_run, KEY_RSHIFT)", source)
        self.assertIn("int DG_GetKey(int *pressed, unsigned char *key)", source)
        self.assertIn("void DG_DrawFrame(void)", source)
        self.assertNotIn("EVIOCGRAB", source)
        self.assertNotIn("/dev/input", source)
        self.assertNotIn("native_init_flash.py", source)
        self.assertNotIn("O_WRONLY", source)

    def test_compile_probe_builds_aarch64_static_binary(self) -> None:
        build = runner.compile_probe()

        self.assertTrue(build["aarch64_static_elf"])
        self.assertIn("ARM aarch64", build["file_output"])
        self.assertIn("statically linked", build["file_output"])
        self.assertTrue(build["adapter_source_sha256"])
        self.assertTrue(build["probe_binary_sha256"])

    def test_render_report_records_private_boundaries_and_validation(self) -> None:
        state = runner.collect_state(build=False)
        state["build"] = {
            "aarch64_static_elf": True,
            "adapter_source": "workspace/private/builds/native-init/v3020-doomgeneric-port-probe/a90.c",
            "adapter_source_sha256": "adapter-sha",
            "adapter_object": "workspace/private/builds/native-init/v3020-doomgeneric-port-probe/a90.o",
            "adapter_object_sha256": "adapter-object-sha",
            "doomgeneric_object": "workspace/private/builds/native-init/v3020-doomgeneric-port-probe/doomgeneric.o",
            "doomgeneric_object_sha256": "doomgeneric-object-sha",
            "probe_binary": "workspace/private/builds/native-init/v3020-doomgeneric-port-probe/a90",
            "probe_binary_sha256": "probe-sha",
            "file_output": "ELF 64-bit LSB executable, ARM aarch64, statically linked",
        }
        report = runner.render_report(state)

        self.assertIn("Native Init V3020 DOOMGENERIC Port Probe", report)
        self.assertIn("v3020-doomgeneric-private-source-build-probe-pass", report)
        self.assertIn("https://github.com/ozkl/doomgeneric", report)
        self.assertIn("AArch64 probe linked: `1`", report)
        self.assertIn("WAD/IWAD data must not be committed", report)
        self.assertIn("Host-only source/build probe", report)
        self.assertIn("Safe next unit: `1`", report)

    def test_count_files_is_case_insensitive_and_omits_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "doom1.WAD").write_bytes(b"wad")
            (root / "note.txt").write_text("ignore", encoding="utf-8")

            result = runner.count_files(root, ".wad")

        self.assertEqual(result["count"], 1)
        self.assertEqual(result["total_bytes"], 3)
        self.assertNotIn("files", result)
        self.assertNotIn("doom1.WAD", str(result))


if __name__ == "__main__":
    unittest.main()
