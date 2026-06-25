from __future__ import annotations

import unittest

from _loader import load_script


runner = load_script("workspace/public/src/scripts/revalidation/build_native_init_boot_v3129_doomgeneric_input_thread_direct_blit.py")


class NativeDoomgenericInputThreadSourceV3129Tests(unittest.TestCase):
    def test_builder_contract_pins_v3129_candidate(self) -> None:
        self.assertEqual(runner.CYCLE, "V3129")
        self.assertEqual(runner.INIT_VERSION, "0.10.118")
        self.assertEqual(runner.INIT_BUILD, "v3129-doomgeneric-input-thread-direct-blit")
        self.assertEqual(runner.ENGINE_RAMDISK_PATH, "bin/a90_doomgeneric_private_engine_v3129")
        self.assertEqual(runner.ENGINE_NAME, "doomgeneric-private-link-v3129-input-thread-direct-blit")
        self.assertIn(runner.INPUT_THREAD_MARKER.encode("ascii"), runner.REQUIRED_STRINGS)

    def test_adapter_source_adds_background_input_thread_and_queue_lock(self) -> None:
        source = runner.v3129_adapter_source()

        self.assertIn("#include <pthread.h>", source)
        self.assertIn(runner.INPUT_THREAD_MARKER, source)
        self.assertIn("a90_doomgeneric_v3129_input_thread_policy", source)
        self.assertIn("static pthread_mutex_t a90_dg_key_lock", source)
        self.assertIn("pthread_mutex_lock(&a90_dg_key_lock);", source)
        self.assertIn("pthread_create(&ctx->thread", source)
        self.assertIn("a90_doomgeneric_input_thread_main", source)
        self.assertIn("a90_doomgeneric_drain_input_fd(ctx->input_udp_fd", source)
        self.assertIn("a90_doomgeneric_input_thread_start(&input_thread)", source)
        self.assertIn("a90_doomgeneric_input_thread_stop(&input_thread)", source)
        self.assertIn("loop_rc == 0 && (frames == 0 || index < frames)", source)
        self.assertNotIn("/tmp/a90-doomgeneric-v3126", source)
        self.assertNotIn("a90.doomgeneric.v3126", source)

    def test_configure_v3129_module_repoints_v3126_build_chain(self) -> None:
        saved_adapter = runner.v3126.v3126_adapter_source
        saved_report = runner.v3126.render_report
        try:
            runner.configure_v3129_module()

            self.assertEqual(runner.v3126.CYCLE, runner.CYCLE)
            self.assertEqual(runner.v3126.INIT_VERSION, runner.INIT_VERSION)
            self.assertEqual(runner.v3126.BOOT_IMAGE, runner.BOOT_IMAGE)
            self.assertIs(runner.v3126.v3126_adapter_source, runner.v3129_adapter_source)
            self.assertIs(runner.v3126.render_report, runner.render_report)
        finally:
            runner.v3126.v3126_adapter_source = saved_adapter
            runner.v3126.render_report = saved_report

    def test_report_template_records_input_thread_live_gate(self) -> None:
        manifest = {
            "decision": runner.DECISION,
            "boot_image": "workspace/private/inputs/boot_images/boot_linux_v3129.img",
            "boot_sha256": "boot-sha",
            "init_version": runner.INIT_VERSION,
            "init_build": runner.INIT_BUILD,
            "doomgeneric_visible_loop": {
                "runtime_wad_path": runner.RUNTIME_WAD_PATH,
                "expected_wad_sha256": runner.EXPECTED_WAD_SHA256,
                "helper_loop_command": "helper --input-thread",
            },
        }

        report = runner.render_report(manifest, ("helper-flag",), ("init-flag",))

        self.assertIn("Native Init V3129 DOOMGENERIC Input Thread Direct Blit Source Build", report)
        self.assertIn(runner.INPUT_THREAD_MARKER, report)
        self.assertIn("rx_queue", report)
        self.assertIn("native_init_flash.py", report)


if __name__ == "__main__":
    unittest.main()
