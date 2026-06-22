from __future__ import annotations

import unittest

from _loader import REPO_ROOT, load_script


runner = load_script("workspace/public/src/scripts/revalidation/build_native_init_boot_v3074_doomgeneric_minimal_dashboard.py")


class NativeDoomgenericMinimalDashboardSourceV3074Tests(unittest.TestCase):
    def test_builder_contract_pins_v3074_minimal_dashboard_candidate(self) -> None:
        self.assertEqual(runner.CYCLE, "V3074")
        self.assertEqual(runner.INIT_VERSION, "0.10.94")
        self.assertEqual(runner.INIT_BUILD, "v3074-doomgeneric-minimal-dashboard")
        self.assertEqual(runner.ENGINE_RAMDISK_PATH, "bin/a90_doomgeneric_private_engine_v3074")
        self.assertEqual(runner.ENGINE_NAME, "doomgeneric-private-link-v3074-minimal-dashboard")
        self.assertEqual(
            runner.FRAME_PATH,
            "/tmp/a90-doomgeneric-v3074-minimal-dashboard-frame.xbgr8888",
        )
        self.assertEqual(runner.INPUT_STATE_PATH, "/tmp/a90-doomgeneric-v3074-input.state")
        self.assertEqual(runner.INPUT_SOCKET_PATH, "/tmp/a90-doomgeneric-v3074-input.sock")
        self.assertEqual(runner.INPUT_UDP_PORT, 30570)
        self.assertEqual(runner.LOOP_FRAME_MS, 28)
        self.assertEqual(runner.PRESENTER_POLL_MS, 4)
        self.assertEqual(runner.NATIVE_DASHBOARD, 1)
        self.assertEqual(runner.NATIVE_DASHBOARD_MINIMAL, 1)
        self.assertEqual(runner.BASELINE_NATIVE_DASHBOARD_MINIMAL, 0)
        self.assertEqual(runner.NATIVE_DASHBOARD_LARGE_FRAME, 0)
        self.assertEqual(runner.REUSE_FRAME_BUFFER, 1)
        self.assertEqual(runner.FRAME_TIMING_PROBE, 1)
        self.assertIn(b"v3074-doomgeneric-minimal-dashboard", runner.REQUIRED_STRINGS)
        self.assertIn(b"video.demo.doom.dashboard.profile=minimal-fastdraw", runner.REQUIRED_STRINGS)
        self.assertIn(b"video.demo.doom.dashboard.layout=top-frame-minimal-input", runner.REQUIRED_STRINGS)
        self.assertIn(b"video.demo.doom.dashboard.metrics_pacing=disabled-minimal", runner.REQUIRED_STRINGS)
        self.assertIn(b"video.demo.doom.loop.timing=frame-ipc-kms-stage-us", runner.REQUIRED_STRINGS)

    def test_native_dashboard_has_minimal_fastdraw_path(self) -> None:
        hud_source = (REPO_ROOT / "workspace/public/src/native-init/v319/30_status_hud.inc.c").read_text(encoding="utf-8")

        self.assertIn("A90_DOOMGENERIC_NATIVE_DASHBOARD_MINIMAL", hud_source)
        self.assertIn("video_demo_doom_draw_minimal_dashboard", hud_source)
        self.assertIn("video.demo.doom.dashboard.profile=minimal-fastdraw", hud_source)
        self.assertIn("video.demo.doom.dashboard.redraw=doom-frame-plus-compact-status", hud_source)
        self.assertIn("video.demo.doom.dashboard.metrics_pacing=disabled-minimal", hud_source)
        self.assertIn("return video_demo_doom_draw_minimal_dashboard(fb,", hud_source)

    def test_base_builder_exposes_minimal_dashboard_compile_flag(self) -> None:
        base_source = (
            REPO_ROOT
            / "workspace/public/src/scripts/revalidation/build_native_init_boot_v3033_doomgeneric_visible_loop.py"
        ).read_text(encoding="utf-8")

        self.assertIn("NATIVE_DASHBOARD_MINIMAL = 0", base_source)
        self.assertIn("A90_DOOMGENERIC_NATIVE_DASHBOARD_MINIMAL", base_source)

    def test_v3074_mutates_v3071_build_surface_without_changing_input_or_timing(self) -> None:
        runner.apply_v3074_globals()
        v3033 = runner.v3033_module()

        self.assertEqual(runner.v3071.CYCLE, runner.CYCLE)
        self.assertEqual(runner.v3071.INIT_VERSION, runner.INIT_VERSION)
        self.assertEqual(runner.v3071.INIT_BUILD, runner.INIT_BUILD)
        self.assertEqual(runner.v3071.LOOP_FRAME_MS, 28)
        self.assertEqual(runner.v3071.PRESENTER_POLL_MS, 4)
        self.assertEqual(runner.v3071.INPUT_UDP_PORT, 30570)
        self.assertEqual(runner.v3071.NATIVE_DASHBOARD, 1)
        self.assertEqual(runner.v3071.NATIVE_DASHBOARD_LARGE_FRAME, 0)
        self.assertEqual(runner.v3071.FRAME_TIMING_PROBE, 1)
        self.assertEqual(runner.v3071.FRAME_PATH, runner.FRAME_PATH)
        self.assertEqual(v3033.REUSE_FRAME_BUFFER, 1)
        self.assertEqual(v3033.FRAME_TIMING_PROBE, 1)
        self.assertEqual(v3033.NATIVE_DASHBOARD_MINIMAL, 1)
        self.assertIs(runner.v3071.render_report, runner.render_report)

    def test_report_template_records_v3075_live_gate(self) -> None:
        manifest = {
            "decision": runner.DECISION,
            "boot_image": "workspace/private/inputs/boot_images/boot_linux_v3074.img",
            "boot_sha256": "boot-sha",
            "init_version": runner.INIT_VERSION,
            "init_build": runner.INIT_BUILD,
            "doomgeneric_visible_loop": {
                "runtime_wad_path": runner.RUNTIME_WAD_PATH,
                "expected_wad_sha256": runner.EXPECTED_WAD_SHA256,
                "frame_path": runner.FRAME_PATH,
                "helper_loop_command": "helper --frame-ms 28 --input-udp 30570",
                "loop_frame_ms": runner.LOOP_FRAME_MS,
                "presenter_poll_ms": runner.PRESENTER_POLL_MS,
            },
            "v3033_marker_strings": [
                "v3074-doomgeneric-minimal-dashboard",
                "video.demo.doom.dashboard.profile=minimal-fastdraw",
            ],
        }

        report = runner.render_report(manifest, ("helper-flag",), ("init-flag",))

        self.assertIn("Native Init V3074 DOOMGENERIC Minimal Dashboard Source Build", report)
        self.assertIn("Baseline minimal dashboard: `0`", report)
        self.assertIn("Candidate minimal dashboard: `1`", report)
        self.assertIn("Dashboard profile marker: `minimal-fastdraw`", report)
        self.assertIn("Run ID: `V3075`", report)
        self.assertIn("native_init_flash.py", report)


if __name__ == "__main__":
    unittest.main()
