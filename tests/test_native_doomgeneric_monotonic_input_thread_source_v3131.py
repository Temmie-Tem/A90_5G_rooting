from __future__ import annotations

import unittest

from _loader import load_script


runner = load_script("workspace/public/src/scripts/revalidation/build_native_init_boot_v3131_doomgeneric_monotonic_input_thread.py")


class NativeDoomgenericMonotonicInputThreadSourceV3131Tests(unittest.TestCase):
    def test_builder_contract_pins_v3131_candidate(self) -> None:
        self.assertEqual(runner.CYCLE, "V3131")
        self.assertEqual(runner.INIT_VERSION, "0.10.119")
        self.assertEqual(runner.INIT_BUILD, "v3131-doomgeneric-monotonic-input-thread")
        self.assertEqual(runner.ENGINE_RAMDISK_PATH, "bin/a90_doomgeneric_private_engine_v3131")
        self.assertEqual(runner.ENGINE_NAME, "doomgeneric-private-link-v3131-monotonic-input-thread")
        self.assertIn(runner.INPUT_THREAD_MARKER.encode("ascii"), runner.REQUIRED_STRINGS)
        self.assertIn(runner.TIME_MODEL_MARKER.encode("ascii"), runner.REQUIRED_STRINGS)

    def test_adapter_source_keeps_input_thread_and_uses_monotonic_active_time(self) -> None:
        source = runner.v3131_adapter_source()

        self.assertIn("#include <time.h>", source)
        self.assertIn("pthread_create(&ctx->thread", source)
        self.assertIn("a90_doomgeneric_drain_input_fd(ctx->input_udp_fd", source)
        self.assertIn("clock_gettime(CLOCK_MONOTONIC", source)
        self.assertIn("a90_doomgeneric_monotonic_ms", source)
        self.assertIn(runner.TIME_MODEL_MARKER, source)
        self.assertIn("monotonic_time_base_ms = a90_doomgeneric_monotonic_ms();", source)
        self.assertIn("return monotonic_time_last_ticks_ms;", source)
        self.assertNotIn("return paced_time_active ? paced_ticks_ms : fake_ticks_ms;", source)
        self.assertNotIn("/tmp/a90-doomgeneric-v3129", source)
        self.assertNotIn("a90.doomgeneric.v3129", source)

    def test_configure_v3131_module_repoints_v3129_build_chain(self) -> None:
        saved = runner.configure_v3131_module()
        try:
            self.assertEqual(runner.v3129.CYCLE, runner.CYCLE)
            self.assertEqual(runner.v3129.INIT_VERSION, runner.INIT_VERSION)
            self.assertEqual(runner.v3129.BOOT_IMAGE, runner.BOOT_IMAGE)
            self.assertIs(runner.v3129.v3129_adapter_source, runner.v3131_adapter_source)
            self.assertIs(runner.v3129.render_report, runner.render_report)
        finally:
            runner.restore_v3129_module(saved)

    def test_report_template_records_live_freeze_gate(self) -> None:
        manifest = {
            "decision": runner.DECISION,
            "boot_image": "workspace/private/inputs/boot_images/boot_linux_v3131.img",
            "boot_sha256": "boot-sha",
            "init_version": runner.INIT_VERSION,
            "init_build": runner.INIT_BUILD,
            "doomgeneric_visible_loop": {
                "runtime_wad_path": runner.RUNTIME_WAD_PATH,
                "expected_wad_sha256": runner.EXPECTED_WAD_SHA256,
                "helper_loop_command": "helper --monotonic-input-thread",
            },
        }

        report = runner.render_report(manifest, ("helper-flag",), ("init-flag",))

        self.assertIn("Native Init V3131 DOOMGENERIC Monotonic Input Thread Source Build", report)
        self.assertIn(runner.INPUT_THREAD_MARKER, report)
        self.assertIn(runner.TIME_MODEL_MARKER, report)
        self.assertIn("shared-frame sequence", report)


if __name__ == "__main__":
    unittest.main()
