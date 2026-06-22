from __future__ import annotations

import unittest

from _loader import load_script


runner = load_script("workspace/public/src/scripts/revalidation/build_native_init_boot_v3063_doomgeneric_frame_ms28.py")


class NativeDoomgenericFrameMs28SourceV3063Tests(unittest.TestCase):
    def test_builder_contract_pins_v3063_frame_ms28_candidate(self) -> None:
        self.assertEqual(runner.CYCLE, "V3063")
        self.assertEqual(runner.INIT_VERSION, "0.10.89")
        self.assertEqual(runner.INIT_BUILD, "v3063-doomgeneric-frame-ms28")
        self.assertEqual(runner.ENGINE_RAMDISK_PATH, "bin/a90_doomgeneric_private_engine_v3063")
        self.assertEqual(runner.ENGINE_NAME, "doomgeneric-private-link-v3063-frame-ms28")
        self.assertEqual(
            runner.FRAME_PATH,
            "/tmp/a90-doomgeneric-v3063-frame-ms28-frame.xbgr8888",
        )
        self.assertEqual(runner.INPUT_STATE_PATH, "/tmp/a90-doomgeneric-v3063-input.state")
        self.assertEqual(runner.INPUT_SOCKET_PATH, "/tmp/a90-doomgeneric-v3063-input.sock")
        self.assertEqual(runner.INPUT_UDP_PORT, 30570)
        self.assertEqual(runner.BASELINE_LOOP_FRAME_MS, 33)
        self.assertEqual(runner.LOOP_FRAME_MS, 28)
        self.assertEqual(runner.PRESENTER_POLL_MS, 4)
        self.assertEqual(runner.NATIVE_DASHBOARD_LARGE_FRAME, 1)
        self.assertIn(b"v3063-doomgeneric-frame-ms28", runner.REQUIRED_STRINGS)
        self.assertIn(b"video.demo.doom.loop.frame_ms=", runner.REQUIRED_STRINGS)
        self.assertIn(b"video.demo.doom.presenter.pacing=helper-frame-mtime", runner.REQUIRED_STRINGS)
        self.assertIn(b"video.demo.input.udp_port=", runner.REQUIRED_STRINGS)

    def test_v3063_mutates_v3061_build_surface_without_changing_input_or_dashboard(self) -> None:
        runner.apply_v3063_globals()

        self.assertEqual(runner.v3061.CYCLE, runner.CYCLE)
        self.assertEqual(runner.v3061.INIT_VERSION, runner.INIT_VERSION)
        self.assertEqual(runner.v3061.INIT_BUILD, runner.INIT_BUILD)
        self.assertEqual(runner.v3061.LOOP_FRAME_MS, 28)
        self.assertEqual(runner.v3061.PRESENTER_POLL_MS, 4)
        self.assertEqual(runner.v3061.INPUT_UDP_PORT, 30570)
        self.assertEqual(runner.v3061.NATIVE_DASHBOARD_LARGE_FRAME, 1)
        self.assertEqual(runner.v3061.FRAME_PATH, runner.FRAME_PATH)
        self.assertIs(runner.v3061.render_report, runner.render_report)

    def test_report_template_records_v3064_live_gate(self) -> None:
        manifest = {
            "decision": runner.DECISION,
            "boot_image": "workspace/private/inputs/boot_images/boot_linux_v3063.img",
            "boot_sha256": "boot-sha",
            "init_version": runner.INIT_VERSION,
            "init_build": runner.INIT_BUILD,
            "doomgeneric_visible_loop": {
                "runtime_wad_path": runner.RUNTIME_WAD_PATH,
                "expected_wad_sha256": runner.EXPECTED_WAD_SHA256,
                "input_path": "udp-ncm-to-DG_GetKey-with-serial-doompad-fallback",
                "input_udp_port": runner.INPUT_UDP_PORT,
                "input_socket_path": runner.INPUT_SOCKET_PATH,
                "input_state_path": runner.INPUT_STATE_PATH,
                "frame_path": runner.FRAME_PATH,
                "helper_loop_command": "helper --frame-ms 28 --input-udp 30570",
                "loop_frame_ms": runner.LOOP_FRAME_MS,
                "presenter_poll_ms": runner.PRESENTER_POLL_MS,
                "presenter_pacing": "helper-frame-mtime",
            },
            "v3033_marker_strings": [
                "v3063-doomgeneric-frame-ms28",
                "video.demo.doom.loop.frame_ms=",
            ],
        }

        report = runner.render_report(manifest, ("helper-flag",), ("init-flag",))

        self.assertIn("Native Init V3063 DOOMGENERIC Frame MS28 Source Build", report)
        self.assertIn("Baseline helper frame ms: `33`", report)
        self.assertIn("Candidate helper frame ms: `28`", report)
        self.assertIn("Dashboard large frame: `1`", report)
        self.assertIn("Run ID: `V3064`", report)
        self.assertIn("native_init_flash.py", report)


if __name__ == "__main__":
    unittest.main()
