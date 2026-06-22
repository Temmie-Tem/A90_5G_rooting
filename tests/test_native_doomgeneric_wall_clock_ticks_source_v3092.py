from __future__ import annotations

import unittest

from _loader import load_script


runner = load_script("workspace/public/src/scripts/revalidation/build_native_init_boot_v3092_doomgeneric_wall_clock_ticks.py")


class NativeDoomgenericWallClockTicksSourceV3092Tests(unittest.TestCase):
    def test_builder_contract_pins_v3092_wall_clock_tick_candidate(self) -> None:
        self.assertEqual(runner.CYCLE, "V3092")
        self.assertEqual(runner.INIT_VERSION, "0.10.102")
        self.assertEqual(runner.INIT_BUILD, "v3092-doomgeneric-wall-clock-ticks")
        self.assertEqual(runner.ENGINE_RAMDISK_PATH, "bin/a90_doomgeneric_private_engine_v3092")
        self.assertEqual(runner.ENGINE_NAME, "doomgeneric-private-link-v3092-wall-clock-ticks")
        self.assertEqual(runner.FRAME_PATH, "/tmp/a90-doomgeneric-v3092-raw-fallback-frame.xbgr8888")
        self.assertEqual(runner.SHARED_FRAME_PATH, "/tmp/a90-doomgeneric-v3092-shared-frame.bin")
        self.assertEqual(runner.INPUT_STATE_PATH, "/tmp/a90-doomgeneric-v3092-input.state")
        self.assertEqual(runner.INPUT_SOCKET_PATH, "/tmp/a90-doomgeneric-v3092-input.sock")
        self.assertEqual(runner.PACE_SOCKET_PATH, "/tmp/a90-doomgeneric-v3092-pace.sock")
        self.assertEqual(runner.TICK_TELEMETRY_PATH, "/tmp/a90-doomgeneric-v3092-tick-telemetry.txt")
        self.assertEqual(runner.PAGEFLIP_MIN_SUBMIT_INTERVAL_MS, 0)
        self.assertIn(runner.TICK_TELEMETRY_MARKER.encode("ascii"), runner.REQUIRED_STRINGS)
        self.assertIn(runner.WALL_CLOCK_MARKER.encode("ascii"), runner.REQUIRED_STRINGS)
        self.assertIn(runner.TICK_TELEMETRY_PATH.encode("ascii"), runner.REQUIRED_STRINGS)
        self.assertIn(b"a90.doomgeneric.v3081.frame_ipc=shared-mmap-seq", runner.REQUIRED_STRINGS)
        self.assertIn(b"a90.doomgeneric.v3059.input=udp-ncm-state-with-unix-dgram-fallback", runner.REQUIRED_STRINGS)

    def test_v3092_adapter_uses_wall_clock_ticks_and_records_telemetry(self) -> None:
        saved_adapter = runner.V3059.v3059_adapter_source
        saved_v3081_adapter = runner.v3086.v3084.v3083.v3081.v3081_adapter_source
        try:
            runner.apply_v3092_globals()

            source = runner.v3092_adapter_source()
        finally:
            runner.V3059.v3059_adapter_source = saved_adapter
            runner.v3086.v3084.v3083.v3081.v3081_adapter_source = saved_v3081_adapter

        self.assertIn("#include <time.h>", source)
        self.assertIn("extern int I_GetTime(void);", source)
        self.assertIn("extern int gametic;", source)
        self.assertIn("a90_doomgeneric_v3092_tick_telemetry_policy", source)
        self.assertIn("a90_doomgeneric_v3092_wall_clock_policy", source)
        self.assertIn(runner.TICK_TELEMETRY_MARKER, source)
        self.assertIn(runner.WALL_CLOCK_MARKER, source)
        self.assertIn("a90_doomgeneric_monotonic_ms", source)
        self.assertIn("clock_gettime(CLOCK_MONOTONIC, &ts)", source)
        self.assertIn("usleep((useconds_t)ms * 1000U);", source)
        self.assertIn("tick_telemetry_last_ticks_ms = now - wall_clock_base_ms;", source)
        self.assertIn("return tick_telemetry_last_ticks_ms;", source)
        self.assertIn(f'#define A90_DG_TICK_TELEMETRY_PATH "{runner.TICK_TELEMETRY_PATH}"', source)
        self.assertIn("static int a90_doomgeneric_write_tick_telemetry", source)
        self.assertIn("++tick_telemetry_sleep_calls;", source)
        self.assertIn("tick_telemetry_sleep_ms_total += ms;", source)
        self.assertIn("++tick_telemetry_getticks_calls;", source)
        self.assertIn('fprintf(fp, "ticks_ms=%u\\n", observed_ticks)', source)
        self.assertIn('fprintf(fp, "time_model=clock-monotonic-elapsed\\n")', source)
        self.assertIn('fprintf(fp, "sleep_policy=usleep-requested-ms\\n")', source)
        self.assertIn('fprintf(fp, "i_get_time=%d\\n", i_time)', source)
        self.assertIn('fprintf(fp, "gametic=%d\\n", observed_gametic)', source)
        self.assertIn("a90_doomgeneric_write_tick_telemetry(", source)
        self.assertIn("A90_DG_TICK_TELEMETRY_PATH, frames, index, final_rc", source)
        self.assertIn("a90_doomgeneric_open_input_udp(input_udp_port)", source)
        self.assertIn("a90_doomgeneric_open_pace_socket(pace_socket_path)", source)
        self.assertIn("a90_doomgeneric_write_shared_frame(&shared_frame)", source)

    def test_v3092_mutates_build_surface_and_custom_adapter(self) -> None:
        v3033 = runner.v3033_module()
        saved_paths = {
            "shared": getattr(v3033, "SHARED_FRAME_PATH", None),
            "pace": getattr(v3033, "PACE_SOCKET_PATH", None),
        }
        saved_adapter = runner.V3059.v3059_adapter_source
        saved_v3081_adapter = runner.v3086.v3084.v3083.v3081.v3081_adapter_source
        try:
            runner.apply_v3092_globals()

            self.assertEqual(runner.v3086.CYCLE, runner.CYCLE)
            self.assertEqual(runner.v3086.INIT_VERSION, runner.INIT_VERSION)
            self.assertEqual(runner.v3086.INIT_BUILD, runner.INIT_BUILD)
            self.assertEqual(runner.v3086.v3084.CYCLE, runner.CYCLE)
            self.assertEqual(v3033.SHARED_FRAME_PATH, runner.SHARED_FRAME_PATH)
            self.assertEqual(v3033.PACE_SOCKET_PATH, runner.PACE_SOCKET_PATH)
            self.assertIs(runner.V3059.v3059_adapter_source, runner.v3092_adapter_source)
        finally:
            runner.V3059.v3059_adapter_source = saved_adapter
            runner.v3086.v3084.v3083.v3081.v3081_adapter_source = saved_v3081_adapter
            if saved_paths["shared"] is not None:
                v3033.SHARED_FRAME_PATH = saved_paths["shared"]
            if saved_paths["pace"] is not None:
                v3033.PACE_SOCKET_PATH = saved_paths["pace"]

    def test_report_template_records_v3093_live_gate_and_wall_clock_contract(self) -> None:
        manifest = {
            "decision": runner.DECISION,
            "boot_image": "workspace/private/inputs/boot_images/boot_linux_v3092.img",
            "boot_sha256": "boot-sha",
            "init_version": runner.INIT_VERSION,
            "init_build": runner.INIT_BUILD,
            "doomgeneric_visible_loop": {
                "runtime_wad_path": runner.RUNTIME_WAD_PATH,
                "expected_wad_sha256": runner.EXPECTED_WAD_SHA256,
                "helper_loop_command": "helper --pace-socket /tmp/a90-doomgeneric-v3092-pace.sock",
            },
            "v3033_marker_strings": [
                "v3092-doomgeneric-wall-clock-ticks",
                runner.TICK_TELEMETRY_MARKER,
                runner.WALL_CLOCK_MARKER,
            ],
        }

        report = runner.render_report(manifest, ("helper-flag",), ("init-flag",))

        self.assertIn("Native Init V3092 DOOMGENERIC Wall-Clock Ticks Source Build", report)
        self.assertIn(f"Telemetry path: `{runner.TICK_TELEMETRY_PATH}`", report)
        self.assertIn(f"Wall-clock marker: `{runner.WALL_CLOCK_MARKER}`", report)
        self.assertIn("clock-monotonic-elapsed", report)
        self.assertIn("ticks_ms", report)
        self.assertIn("Run ID: `V3093`", report)
        self.assertIn("native_init_flash.py", report)


if __name__ == "__main__":
    unittest.main()
