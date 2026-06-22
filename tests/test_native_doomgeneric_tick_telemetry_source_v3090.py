from __future__ import annotations

import unittest

from _loader import load_script


runner = load_script("workspace/public/src/scripts/revalidation/build_native_init_boot_v3090_doomgeneric_tick_telemetry.py")


class NativeDoomgenericTickTelemetrySourceV3090Tests(unittest.TestCase):
    def test_builder_contract_pins_v3090_tick_telemetry_candidate(self) -> None:
        self.assertEqual(runner.CYCLE, "V3090")
        self.assertEqual(runner.INIT_VERSION, "0.10.101")
        self.assertEqual(runner.INIT_BUILD, "v3090-doomgeneric-tick-telemetry")
        self.assertEqual(runner.ENGINE_RAMDISK_PATH, "bin/a90_doomgeneric_private_engine_v3090")
        self.assertEqual(runner.ENGINE_NAME, "doomgeneric-private-link-v3090-tick-telemetry")
        self.assertEqual(runner.FRAME_PATH, "/tmp/a90-doomgeneric-v3090-raw-fallback-frame.xbgr8888")
        self.assertEqual(runner.SHARED_FRAME_PATH, "/tmp/a90-doomgeneric-v3090-shared-frame.bin")
        self.assertEqual(runner.INPUT_STATE_PATH, "/tmp/a90-doomgeneric-v3090-input.state")
        self.assertEqual(runner.INPUT_SOCKET_PATH, "/tmp/a90-doomgeneric-v3090-input.sock")
        self.assertEqual(runner.PACE_SOCKET_PATH, "/tmp/a90-doomgeneric-v3090-pace.sock")
        self.assertEqual(runner.TICK_TELEMETRY_PATH, "/tmp/a90-doomgeneric-v3090-tick-telemetry.txt")
        self.assertEqual(runner.PAGEFLIP_MIN_SUBMIT_INTERVAL_MS, 0)
        self.assertIn(runner.TICK_TELEMETRY_MARKER.encode("ascii"), runner.REQUIRED_STRINGS)
        self.assertIn(runner.TICK_TELEMETRY_PATH.encode("ascii"), runner.REQUIRED_STRINGS)
        self.assertIn(b"a90.doomgeneric.v3081.frame_ipc=shared-mmap-seq", runner.REQUIRED_STRINGS)
        self.assertIn(b"a90.doomgeneric.v3059.input=udp-ncm-state-with-unix-dgram-fallback", runner.REQUIRED_STRINGS)

    def test_v3090_adapter_records_fake_time_and_game_tic_telemetry(self) -> None:
        saved_adapter = runner.V3059.v3059_adapter_source
        saved_v3081_adapter = runner.v3086.v3084.v3083.v3081.v3081_adapter_source
        try:
            runner.apply_v3090_globals()

            source = runner.v3090_adapter_source()
        finally:
            runner.V3059.v3059_adapter_source = saved_adapter
            runner.v3086.v3084.v3083.v3081.v3081_adapter_source = saved_v3081_adapter

        self.assertIn("extern int I_GetTime(void);", source)
        self.assertIn("extern int gametic;", source)
        self.assertIn("a90_doomgeneric_v3090_tick_telemetry_policy", source)
        self.assertIn(runner.TICK_TELEMETRY_MARKER, source)
        self.assertIn(f'#define A90_DG_TICK_TELEMETRY_PATH "{runner.TICK_TELEMETRY_PATH}"', source)
        self.assertIn("static int a90_doomgeneric_write_tick_telemetry", source)
        self.assertIn("++tick_telemetry_sleep_calls;", source)
        self.assertIn("tick_telemetry_sleep_ms_total += ms;", source)
        self.assertIn("++tick_telemetry_getticks_calls;", source)
        self.assertIn('fprintf(fp, "i_get_time=%d\\n", i_time)', source)
        self.assertIn('fprintf(fp, "gametic=%d\\n", observed_gametic)', source)
        self.assertIn("a90_doomgeneric_write_tick_telemetry(", source)
        self.assertIn("A90_DG_TICK_TELEMETRY_PATH, frames, index, final_rc", source)
        self.assertIn("a90_doomgeneric_open_input_udp(input_udp_port)", source)
        self.assertIn("a90_doomgeneric_open_pace_socket(pace_socket_path)", source)
        self.assertIn("a90_doomgeneric_write_shared_frame(&shared_frame)", source)

    def test_v3090_mutates_build_surface_and_custom_adapter(self) -> None:
        v3033 = runner.v3033_module()
        saved_paths = {
            "shared": getattr(v3033, "SHARED_FRAME_PATH", None),
            "pace": getattr(v3033, "PACE_SOCKET_PATH", None),
        }
        saved_adapter = runner.V3059.v3059_adapter_source
        saved_v3081_adapter = runner.v3086.v3084.v3083.v3081.v3081_adapter_source
        try:
            runner.apply_v3090_globals()

            self.assertEqual(runner.v3086.CYCLE, runner.CYCLE)
            self.assertEqual(runner.v3086.INIT_VERSION, runner.INIT_VERSION)
            self.assertEqual(runner.v3086.INIT_BUILD, runner.INIT_BUILD)
            self.assertEqual(runner.v3086.v3084.CYCLE, runner.CYCLE)
            self.assertEqual(v3033.SHARED_FRAME_PATH, runner.SHARED_FRAME_PATH)
            self.assertEqual(v3033.PACE_SOCKET_PATH, runner.PACE_SOCKET_PATH)
            self.assertIs(runner.V3059.v3059_adapter_source, runner.v3090_adapter_source)
        finally:
            runner.V3059.v3059_adapter_source = saved_adapter
            runner.v3086.v3084.v3083.v3081.v3081_adapter_source = saved_v3081_adapter
            if saved_paths["shared"] is not None:
                v3033.SHARED_FRAME_PATH = saved_paths["shared"]
            if saved_paths["pace"] is not None:
                v3033.PACE_SOCKET_PATH = saved_paths["pace"]

    def test_report_template_records_v3091_live_gate_and_telemetry_path(self) -> None:
        manifest = {
            "decision": runner.DECISION,
            "boot_image": "workspace/private/inputs/boot_images/boot_linux_v3090.img",
            "boot_sha256": "boot-sha",
            "init_version": runner.INIT_VERSION,
            "init_build": runner.INIT_BUILD,
            "doomgeneric_visible_loop": {
                "runtime_wad_path": runner.RUNTIME_WAD_PATH,
                "expected_wad_sha256": runner.EXPECTED_WAD_SHA256,
                "helper_loop_command": "helper --pace-socket /tmp/a90-doomgeneric-v3090-pace.sock",
            },
            "v3033_marker_strings": [
                "v3090-doomgeneric-tick-telemetry",
                runner.TICK_TELEMETRY_MARKER,
            ],
        }

        report = runner.render_report(manifest, ("helper-flag",), ("init-flag",))

        self.assertIn("Native Init V3090 DOOMGENERIC Tick Telemetry Source Build", report)
        self.assertIn(f"Telemetry path: `{runner.TICK_TELEMETRY_PATH}`", report)
        self.assertIn("fake_ticks_ms", report)
        self.assertIn("Run ID: `V3091`", report)
        self.assertIn("native_init_flash.py", report)


if __name__ == "__main__":
    unittest.main()
