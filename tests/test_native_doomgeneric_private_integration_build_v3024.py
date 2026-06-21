from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from _loader import load_script


runner = load_script("workspace/public/src/scripts/revalidation/native_doomgeneric_engine_integration_build_v3024.py")


class NativeDoomgenericPrivateIntegrationBuildV3024Tests(unittest.TestCase):
    def test_collect_state_reads_private_source_contract_without_build(self) -> None:
        state = runner.collect_state(build=False)
        source = state["source"]

        self.assertEqual(state["run_id"], "V3024")
        self.assertEqual(state["decision"], "v3024-doomgeneric-private-full-engine-link-pass")
        self.assertTrue(source["source_exists"])
        self.assertEqual(source["git_head"], runner.PINNED_COMMIT)
        self.assertTrue(source["git_head_matches_pin"])
        self.assertTrue(source["git_status_clean"])
        self.assertGreaterEqual(source["engine_source_count"], 70)
        self.assertEqual(source["engine_sources_missing"], [])
        self.assertEqual(source["excluded_platform_backend"], "doomgeneric_soso.c")
        self.assertEqual(state["public_wads"]["count"], 0)
        self.assertFalse(state["runtime_policy"]["wad_committed"])
        self.assertFalse(state["runtime_policy"]["wad_embedded_in_boot"])
        self.assertTrue(state["safe_to_continue_host_only"])

    def test_parse_soso_sources_excludes_platform_backend(self) -> None:
        sources = runner.parse_soso_sources()

        self.assertIn("doomgeneric.c", sources)
        self.assertIn("d_main.c", sources)
        self.assertIn("i_video.c", sources)
        self.assertNotIn("doomgeneric_soso.c", sources)
        self.assertNotIn("doomgeneric_sdl.c", sources)
        self.assertGreaterEqual(len(sources), 70)

    def test_adapter_source_defines_runtime_private_wad_and_serial_doompad_bridge(self) -> None:
        source = runner.ADAPTER_SOURCE_TEXT

        self.assertIn("a90.doomgeneric.v3024.private_source_integration=1", source)
        self.assertIn("/cache/a90-runtime/pkg/doom/v3024/DOOM1.WAD", source)
        self.assertIn("a90_doomgeneric_feed_snapshot", source)
        self.assertIn("queue_edge(snapshot->forward, &last_forward, KEY_UPARROW)", source)
        self.assertIn("queue_edge(snapshot->fire, &last_fire, KEY_FIRE)", source)
        self.assertIn("DG_GetKey", source)
        self.assertIn("-nosound", source)
        self.assertIn("-nomusic", source)
        self.assertNotIn("/dev/input", source)
        self.assertNotIn("uinput", source)
        self.assertNotIn("native_init_flash.py", source)
        self.assertNotIn("O_WRONLY", source)

    def test_render_report_records_v3025_next_unit(self) -> None:
        state = runner.collect_state(build=False)
        state["build"] = {
            "third_party_source_compile_count": 78,
            "engine_object_count": 79,
            "aarch64_static_elf": True,
            "marker_check_pass": True,
            "adapter_source": "workspace/private/builds/native-init/v3024/a90.c",
            "adapter_source_sha256": "adapter-sha",
            "engine_binary": "workspace/private/builds/native-init/v3024/doom",
            "engine_binary_sha256": "engine-sha",
            "engine_binary_bytes": 123,
            "engine_object_total_bytes": 456,
            "compile_stdout_nonempty_count": 0,
            "file_output": "ELF 64-bit LSB executable, ARM aarch64, statically linked",
            "size_output": "text data bss dec hex filename",
        }
        state["sizes"] = runner.collect_sizes(state["build"])
        report = runner.render_report(state)

        self.assertIn("Native Init V3024 DOOMGENERIC Private Integration Build", report)
        self.assertIn("v3024-doomgeneric-private-full-engine-link-pass", report)
        self.assertIn("AArch64 static engine linked: `1`", report)
        self.assertIn("Public WAD files committed/present: `0`", report)
        self.assertIn("Boot-image delta: `not-produced`", report)
        self.assertIn("Run ID: `V3025`", report)

    def test_count_files_reports_counts_without_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "DOOM1.WAD").write_bytes(b"wad")
            (root / "ignore.txt").write_text("ignore", encoding="utf-8")

            result = runner.count_files(root, ".wad")

        self.assertEqual(result["count"], 1)
        self.assertEqual(result["total_bytes"], len(b"wad"))
        self.assertNotIn("DOOM1.WAD", str(result))
        self.assertNotIn("files", result)


if __name__ == "__main__":
    unittest.main()
