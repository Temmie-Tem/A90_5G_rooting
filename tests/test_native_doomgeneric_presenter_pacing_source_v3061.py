from __future__ import annotations

import unittest

from _loader import REPO_ROOT, load_script


runner = load_script("workspace/public/src/scripts/revalidation/build_native_init_boot_v3061_doomgeneric_presenter_pacing.py")


class NativeDoomgenericPresenterPacingSourceV3061Tests(unittest.TestCase):
    def test_builder_contract_pins_v3061_presenter_pacing_candidate(self) -> None:
        self.assertEqual(runner.CYCLE, "V3061")
        self.assertEqual(runner.INIT_VERSION, "0.10.88")
        self.assertEqual(runner.INIT_BUILD, "v3061-doomgeneric-presenter-pacing")
        self.assertEqual(runner.ENGINE_RAMDISK_PATH, "bin/a90_doomgeneric_private_engine_v3061")
        self.assertEqual(runner.ENGINE_NAME, "doomgeneric-private-link-v3061-presenter-pacing")
        self.assertEqual(
            runner.FRAME_PATH,
            "/tmp/a90-doomgeneric-v3061-presenter-pacing-frame.xbgr8888",
        )
        self.assertEqual(runner.INPUT_STATE_PATH, "/tmp/a90-doomgeneric-v3061-input.state")
        self.assertEqual(runner.INPUT_SOCKET_PATH, "/tmp/a90-doomgeneric-v3061-input.sock")
        self.assertEqual(runner.INPUT_UDP_PORT, 30570)
        self.assertEqual(runner.LOOP_FRAME_MS, 33)
        self.assertEqual(runner.PRESENTER_POLL_MS, 4)
        self.assertIn(b"video.demo.doom.presenter.pacing=helper-frame-mtime", runner.REQUIRED_STRINGS)
        self.assertIn(b"video.demo.doom.presenter.poll_ms=", runner.REQUIRED_STRINGS)
        self.assertIn(b"video.demo.doom.loop.presenter.pacing=helper-frame-mtime", runner.REQUIRED_STRINGS)
        self.assertIn(b"video.demo.doom.loop.presenter.poll_ms=", runner.REQUIRED_STRINGS)

    def test_native_bridge_exposes_frame_metadata_for_presenter_sync(self) -> None:
        header = (REPO_ROOT / "workspace/public/src/native-init/a90_doomgeneric_bridge.h").read_text(encoding="utf-8")
        source = (REPO_ROOT / "workspace/public/src/native-init/a90_doomgeneric_bridge.c").read_text(encoding="utf-8")

        self.assertIn("uint64_t frame_id;", header)
        self.assertIn("uint64_t mtime_ns;", header)
        self.assertIn("render->mtime_ns", source)
        self.assertIn("st.st_mtim.tv_sec", source)
        self.assertIn("st.st_mtim.tv_nsec", source)
        self.assertIn("render->frame_id = render->mtime_ns", source)

    def test_native_presenter_polls_for_new_helper_frames_only(self) -> None:
        hud_source = (REPO_ROOT / "workspace/public/src/native-init/v319/30_status_hud.inc.c").read_text(encoding="utf-8")

        self.assertIn("VIDEO_DEMO_DOOMGENERIC_PRESENTER_POLL_MS", hud_source)
        self.assertIn("video.demo.doom.presenter.pacing=helper-frame-mtime", hud_source)
        self.assertIn("video.demo.doom.loop.presenter.pacing=helper-frame-mtime", hud_source)
        self.assertIn("uint64_t last_presented_frame_id = 0ULL;", hud_source)
        self.assertIn("render.frame_id != last_presented_frame_id", hud_source)
        self.assertIn("last_presented_frame_id = render.frame_id", hud_source)
        self.assertIn(
            "usleep((useconds_t)VIDEO_DEMO_DOOMGENERIC_PRESENTER_POLL_MS * 1000U)",
            hud_source,
        )

    def test_base_builder_exports_presenter_poll_compile_define(self) -> None:
        base_builder = (
            REPO_ROOT
            / "workspace/public/src/scripts/revalidation/build_native_init_boot_v3033_doomgeneric_visible_loop.py"
        ).read_text(encoding="utf-8")

        self.assertIn("PRESENTER_POLL_MS = 4", base_builder)
        self.assertIn(
            'numeric_define("VIDEO_DEMO_DOOMGENERIC_PRESENTER_POLL_MS", PRESENTER_POLL_MS)',
            base_builder,
        )

    def test_report_template_records_v3062_live_gate(self) -> None:
        manifest = {
            "decision": runner.DECISION,
            "boot_image": "workspace/private/inputs/boot_images/boot_linux_v3061.img",
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
                "helper_loop_command": "helper --frame-ms 33 --input-udp 30570",
                "loop_frame_ms": runner.LOOP_FRAME_MS,
                "presenter_poll_ms": runner.PRESENTER_POLL_MS,
                "presenter_pacing": "helper-frame-mtime",
            },
            "v3033_marker_strings": [
                "v3061-doomgeneric-presenter-pacing",
                "video.demo.doom.presenter.pacing=helper-frame-mtime",
            ],
        }

        report = runner.render_report(manifest, ("helper-flag",), ("init-flag",))

        self.assertIn("Native Init V3061 DOOMGENERIC Presenter Pacing Source Build", report)
        self.assertIn("frame_id", report)
        self.assertIn("Presenter poll ms: `4`", report)
        self.assertIn("Run ID: `V3062`", report)
        self.assertIn("native_init_flash.py", report)


if __name__ == "__main__":
    unittest.main()
