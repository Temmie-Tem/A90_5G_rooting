from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


runner = load_script("workspace/public/src/scripts/revalidation/build_native_init_boot_v3104_doomgeneric_paced_tic.py")
REPO_ROOT = Path(__file__).resolve().parents[1]


class NativeDoomgenericPacedTicSourceV3104Tests(unittest.TestCase):
    def test_builder_contract_pins_v3104_candidate(self) -> None:
        self.assertEqual(runner.CYCLE, "V3104")
        self.assertEqual(runner.INIT_VERSION, "0.10.108")
        self.assertEqual(runner.INIT_BUILD, "v3104-doomgeneric-paced-tic")
        self.assertEqual(runner.ENGINE_RAMDISK_PATH, "bin/a90_doomgeneric_private_engine_v3104")
        self.assertEqual(runner.ENGINE_NAME, "doomgeneric-private-link-v3104-paced-tic")
        self.assertEqual(runner.FRAME_PATH, "/tmp/a90-doomgeneric-v3104-raw-fallback-frame.xbgr8888")
        self.assertEqual(runner.SHARED_FRAME_PATH, "/tmp/a90-doomgeneric-v3104-shared-frame.bin")
        self.assertEqual(runner.INPUT_STATE_PATH, "/tmp/a90-doomgeneric-v3104-input.state")
        self.assertEqual(runner.INPUT_SOCKET_PATH, "/tmp/a90-doomgeneric-v3104-input.sock")
        self.assertEqual(runner.PACE_SOCKET_PATH, "/tmp/a90-doomgeneric-v3104-pace.sock")
        self.assertEqual(runner.TICK_TELEMETRY_PATH, "/tmp/a90-doomgeneric-v3104-tick-telemetry.txt")
        self.assertEqual(runner.TICK_QUANTUM_US, 28571)
        self.assertIn(runner.PACED_TIME_MARKER.encode("ascii"), runner.REQUIRED_STRINGS)
        self.assertIn(b"paced_time_model=presenter-token-doom-tic-quantum", runner.REQUIRED_STRINGS)
        self.assertIn(b"paced_time.quantum_us=%u", runner.REQUIRED_STRINGS)
        self.assertIn(b"paced_time.advance_calls=%u", runner.REQUIRED_STRINGS)

    def test_v3104_adapter_uses_presenter_token_paced_time(self) -> None:
        source = runner.v3104_adapter_source()

        self.assertIn(runner.PACED_TIME_MARKER, source)
        self.assertIn("a90_doomgeneric_v3104_paced_time_policy", source)
        self.assertIn("#define A90_DG_PACED_TICK_QUANTUM_US 28571U", source)
        self.assertIn("static void a90_doomgeneric_advance_paced_time(void)", source)
        self.assertIn("paced_ticks_ms += step_ms;", source)
        self.assertIn("return paced_time_active ? paced_ticks_ms : fake_ticks_ms;", source)
        self.assertIn(
            "doomgeneric_Create(12, argv);\n"
            "    paced_ticks_ms = fake_ticks_ms;\n"
            "    paced_tick_remainder_us = 0;\n"
            "    paced_time_active = 1;\n"
            "    for (index = 0; frames == 0 || index < frames; ++index) {\n"
            "        int rc;",
            source,
        )
        self.assertIn("a90_doomgeneric_advance_paced_time();\n            doomgeneric_Tick();", source)
        self.assertEqual(source.count("a90_doomgeneric_advance_paced_time();"), 1)
        self.assertIn("paced_time_model=presenter-token-doom-tic-quantum", source)
        self.assertIn("fake_time_model=DG_SleepMs-request-telemetry-only", source)
        self.assertNotIn("/tmp/a90-doomgeneric-v3100", source)
        self.assertNotIn("gametic_present_only=changed-gametic-only", source)

    def test_v3104_apply_globals_keeps_60hz_presenter_flags(self) -> None:
        v3033 = runner.v3033_module()
        saved_adapter = runner.V3059.v3059_adapter_source
        saved_v3081_adapter = runner.v3100.v3098.v3096.v3086.v3084.v3083.v3081.v3081_adapter_source
        saved_gametic = getattr(v3033, "GAMETIC_PRESENT_ONLY", None)
        saved_interval = getattr(v3033, "TICK_PACE_INTERVAL_US", None)
        saved_shared = getattr(v3033, "SHARED_FRAME_PATH", None)
        saved_pace = getattr(v3033, "PACE_SOCKET_PATH", None)
        large_frame_modules = [
            runner.v3100.v3098.v3096.v3086,
            runner.v3100.v3098.v3096.v3086.v3084,
            runner.v3100.v3098.v3096.v3086.v3084.v3083,
            runner.v3100.v3098.v3096.v3086.v3084.v3083.v3081,
            runner.v3100.v3098.v3096.v3086.v3084.v3083.v3081.v3079,
            runner.v3100.v3098.v3096.v3086.v3084.v3083.v3081.v3079.v3077,
            runner.v3100.v3098.v3096.v3086.v3084.v3083.v3081.v3079.v3077.v3074,
            runner.v3100.v3098.v3096.v3086.v3084.v3083.v3081.v3079.v3077.v3074.v3071,
            v3033,
        ]
        saved_large = [getattr(module, "NATIVE_DASHBOARD_LARGE_FRAME", None) for module in large_frame_modules]
        try:
            runner.apply_v3104_globals()

            self.assertEqual(runner.v3100.v3098.v3096.v3086.CYCLE, runner.CYCLE)
            self.assertEqual(runner.v3100.v3098.v3096.v3086.INIT_VERSION, runner.INIT_VERSION)
            self.assertEqual(v3033.SHARED_FRAME_PATH, runner.SHARED_FRAME_PATH)
            self.assertEqual(v3033.PACE_SOCKET_PATH, runner.PACE_SOCKET_PATH)
            self.assertEqual(v3033.GAMETIC_PRESENT_ONLY, 0)
            self.assertEqual(v3033.TICK_PACE_INTERVAL_US, 0)
            self.assertIs(runner.V3059.v3059_adapter_source, runner.v3104_adapter_source)
        finally:
            runner.V3059.v3059_adapter_source = saved_adapter
            runner.v3100.v3098.v3096.v3086.v3084.v3083.v3081.v3081_adapter_source = saved_v3081_adapter
            if saved_gametic is not None:
                v3033.GAMETIC_PRESENT_ONLY = saved_gametic
            if saved_interval is not None:
                v3033.TICK_PACE_INTERVAL_US = saved_interval
            if saved_shared is not None:
                v3033.SHARED_FRAME_PATH = saved_shared
            if saved_pace is not None:
                v3033.PACE_SOCKET_PATH = saved_pace
            for module, value in zip(large_frame_modules, saved_large):
                if value is not None:
                    module.NATIVE_DASHBOARD_LARGE_FRAME = value

    def test_report_template_records_v3105_live_gate(self) -> None:
        manifest = {
            "decision": runner.DECISION,
            "boot_image": "workspace/private/inputs/boot_images/boot_linux_v3104.img",
            "boot_sha256": "boot-sha",
            "init_version": runner.INIT_VERSION,
            "init_build": runner.INIT_BUILD,
            "doomgeneric_visible_loop": {
                "runtime_wad_path": runner.RUNTIME_WAD_PATH,
                "expected_wad_sha256": runner.EXPECTED_WAD_SHA256,
                "helper_loop_command": "helper --paced-tic",
            },
            "v3033_marker_strings": [
                runner.INIT_BUILD,
                runner.PACED_TIME_MARKER,
                runner.TICK_TELEMETRY_MARKER,
            ],
        }

        report = runner.render_report(manifest, ("helper-flag",), ("init-flag",))

        self.assertIn("Native Init V3104 DOOMGENERIC Paced Tic Source Build", report)
        self.assertIn(f"Paced-time marker: `{runner.PACED_TIME_MARKER}`", report)
        self.assertIn("presenter-token-doom-tic-quantum", report)
        self.assertIn("non-original-speed candidate", report)
        self.assertIn("Run ID: `V3105`", report)
        self.assertIn("native_init_flash.py", report)


if __name__ == "__main__":
    unittest.main()
