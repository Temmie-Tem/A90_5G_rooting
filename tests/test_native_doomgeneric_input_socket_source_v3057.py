from __future__ import annotations

import unittest

from _loader import REPO_ROOT, load_script


runner = load_script("workspace/public/src/scripts/revalidation/build_native_init_boot_v3057_doomgeneric_input_socket.py")


class NativeDoomgenericInputSocketSourceV3057Tests(unittest.TestCase):
    def test_builder_contract_pins_v3057_input_socket_candidate(self) -> None:
        self.assertEqual(runner.CYCLE, "V3057")
        self.assertEqual(runner.INIT_VERSION, "0.10.86")
        self.assertEqual(runner.INIT_BUILD, "v3057-doomgeneric-input-socket")
        self.assertEqual(runner.ENGINE_RAMDISK_PATH, "bin/a90_doomgeneric_private_engine_v3057")
        self.assertEqual(runner.ENGINE_NAME, "doomgeneric-private-link-v3057-input-socket")
        self.assertEqual(runner.FRAME_PATH, "/tmp/a90-doomgeneric-v3057-input-socket-frame.xbgr8888")
        self.assertEqual(runner.INPUT_STATE_PATH, "/tmp/a90-doomgeneric-v3057-input.state")
        self.assertEqual(runner.INPUT_SOCKET_PATH, "/tmp/a90-doomgeneric-v3057-input.sock")
        self.assertIn(
            b"a90.doomgeneric.v3057.input=unix-dgram-state-with-file-fallback",
            runner.REQUIRED_STRINGS,
        )
        self.assertIn(b"--input-socket", runner.REQUIRED_STRINGS)
        self.assertIn(b"doompad.input_socket.rc=", runner.REQUIRED_STRINGS)

    def test_adapter_source_adds_nonblocking_unix_dgram_input_socket(self) -> None:
        source = runner.v3057_adapter_source()

        self.assertIn("a90.doomgeneric.v3057.input=unix-dgram-state-with-file-fallback", source)
        self.assertIn("struct a90_dg_input_packet", source)
        self.assertIn("a90_doomgeneric_open_input_socket", source)
        self.assertIn("a90_doomgeneric_drain_input_socket", source)
        self.assertIn("recv(fd, &packet, sizeof(packet), MSG_DONTWAIT)", source)
        self.assertIn("a90_doomgeneric_apply_input_mask(packet.seq, packet.mask)", source)
        self.assertIn("--input-socket", source)
        self.assertIn("input_socket_path = argv[12];", source)

    def test_native_bridge_and_doompad_mirror_socket_with_file_fallback(self) -> None:
        bridge_source = (REPO_ROOT / "workspace/public/src/native-init/a90_doomgeneric_bridge.c").read_text(encoding="utf-8")
        bridge_header = (REPO_ROOT / "workspace/public/src/native-init/a90_doomgeneric_bridge.h").read_text(encoding="utf-8")
        doompad_source = (REPO_ROOT / "workspace/public/src/native-init/v319/40_menu_apps.inc.c").read_text(encoding="utf-8")
        hud_source = (REPO_ROOT / "workspace/public/src/native-init/v319/30_status_hud.inc.c").read_text(encoding="utf-8")

        self.assertIn("input_socket_path", bridge_header)
        self.assertIn("a90_doomgeneric_bridge_send_input_socket", bridge_header)
        self.assertIn("A90_DOOMGENERIC_BRIDGE_INPUT_SOCKET_PATH", bridge_source)
        self.assertIn("struct a90_doomgeneric_input_packet", bridge_source)
        self.assertIn("sendto(fd,", bridge_source)
        self.assertIn('"--input-socket"', bridge_source)
        self.assertIn("doompad_mirror_result", doompad_source)
        self.assertIn("a90_doomgeneric_bridge_write_input_state(&input)", doompad_source)
        self.assertIn("a90_doomgeneric_bridge_send_input_socket(&input)", doompad_source)
        self.assertIn("doompad.input_socket.rc=%d", doompad_source)
        self.assertIn("video.demo.input.socket_path=%s", hud_source)
        self.assertIn("serial-doompad-unix-dgram-with-state-file-fallback", hud_source)

    def test_report_template_records_v3058_live_gate(self) -> None:
        manifest = {
            "decision": runner.DECISION,
            "boot_image": "workspace/private/inputs/boot_images/boot_linux_v3057.img",
            "boot_sha256": "boot-sha",
            "init_version": runner.INIT_VERSION,
            "init_build": runner.INIT_BUILD,
            "doomgeneric_visible_loop": {
                "runtime_wad_path": runner.RUNTIME_WAD_PATH,
                "expected_wad_sha256": runner.EXPECTED_WAD_SHA256,
                "input_path": "serial-doompad-to-DG_GetKey-via-unix-dgram",
                "input_socket_path": runner.INPUT_SOCKET_PATH,
                "input_state_path": runner.INPUT_STATE_PATH,
                "frame_path": runner.FRAME_PATH,
                "helper_loop_command": "helper --input-socket path",
            },
            "v3033_marker_strings": [
                "v3057-doomgeneric-input-socket",
                "a90.doomgeneric.v3057.input=unix-dgram-state-with-file-fallback",
            ],
        }

        report = runner.render_report(manifest, ("helper-flag",), ("init-flag",))

        self.assertIn("Native Init V3057 DOOMGENERIC Input Socket Source Build", report)
        self.assertIn("Unix datagram input socket", report)
        self.assertIn("Run ID: `V3058`", report)
        self.assertIn("doompad.input_socket.sent=1", report)


if __name__ == "__main__":
    unittest.main()
