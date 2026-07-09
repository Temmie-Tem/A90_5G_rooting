import importlib.util
import os
import pty
import sys
import tempfile
import termios
import unittest
from pathlib import Path


SCRIPT = Path("workspace/public/src/scripts/revalidation/s22plus_o0_stock_usb_control.py")


def load_module():
    spec = importlib.util.spec_from_file_location("s22plus_o0_stock_usb_control", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class S22PlusO0StockUsbControlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_frame_roundtrip_preserves_sequence_and_payload(self):
        for seq in (0, 1, 0x12345678, 0xFFFFFFFF):
            for size in (0, 1, 31, 256, self.module.MAX_PAYLOAD):
                payload = self.module.deterministic_payload(seq, size)
                encoded = self.module.encode_frame(self.module.REQUEST, seq, payload)
                frame_type, decoded_seq, decoded_payload = self.module.decode_frame(
                    encoded, self.module.REQUEST
                )
                self.assertEqual(frame_type, self.module.REQUEST)
                self.assertEqual(decoded_seq, seq)
                self.assertEqual(decoded_payload, payload)

    def test_frame_crc_rejects_payload_corruption(self):
        encoded = bytearray(self.module.encode_frame(self.module.RESPONSE, 7, b"abcdef"))
        encoded[-1] ^= 0x80
        with self.assertRaisesRegex(ValueError, "bad crc"):
            self.module.decode_frame(bytes(encoded), self.module.RESPONSE)

    def test_frame_type_is_enforced(self):
        encoded = self.module.encode_frame(self.module.REQUEST, 3, b"payload")
        with self.assertRaisesRegex(ValueError, "unexpected frame type"):
            self.module.decode_frame(encoded, self.module.RESPONSE)

    def test_deterministic_payload_length_schedule(self):
        lengths = [len(self.module.deterministic_payload(seq, 256)) for seq in range(10)]
        self.assertEqual(lengths, [0, 1, 7, 31, 256, 0, 1, 7, 31, 256])
        self.assertEqual(
            self.module.deterministic_payload(9, 256),
            self.module.deterministic_payload(9, 256),
        )

    def test_percentile_uses_nearest_rank(self):
        values = [1.0, 2.0, 3.0, 4.0, 100.0]
        self.assertEqual(self.module.percentile(values, 0.50), 3.0)
        self.assertEqual(self.module.percentile(values, 0.95), 100.0)
        self.assertIsNone(self.module.percentile([], 0.50))

    def test_adb_parser_selects_only_device_state(self):
        text = "List of devices attached\nSERIAL1\tdevice\nSERIAL2\toffline\n\n"
        self.assertEqual(self.module.parse_adb_devices(text), ["SERIAL1"])

    def test_device_snapshot_gate_requires_known_baseline(self):
        snapshot = {
            "model": self.module.EXPECTED_MODEL,
            "device": self.module.EXPECTED_DEVICE,
            "incremental": self.module.EXPECTED_INCREMENTAL,
            "boot_completed": "1",
            "boot_recovery": "0",
            "vbstate": "orange",
            "usb_config": "mtp,conn_gadget,adb",
            "ttyGS0_char": "1",
            "udc": "a600000.dwc3",
            "boot_sha256": self.module.EXPECTED_BOOT_SHA256,
            "uid": "0",
        }
        self.assertEqual(self.module.verify_device_snapshot(snapshot), [])
        snapshot["boot_sha256"] = "0" * 64
        self.assertEqual(self.module.verify_device_snapshot(snapshot), ["boot_sha256-mismatch"])

    def test_stock_service_parser_requires_running_owner(self):
        values = self.module.parse_key_values(
            "service_state=running\nservice_pid=1867\ntty_owner_count=1\n"
        )
        self.assertEqual(values["service_state"], "running")
        self.assertEqual(values["service_pid"], "1867")
        self.assertEqual(values["tty_owner_count"], "1")

    def test_observers_are_continuous_and_do_not_request_privilege(self):
        with tempfile.TemporaryDirectory() as tmp:
            specs = self.module.observer_specs(Path(tmp))
        names = {name for name, _, _ in specs}
        self.assertIn("udev_usb", names)
        self.assertIn("kernel_journal", names)
        for _, argv, _ in specs:
            self.assertNotIn("sudo", argv)

    def test_host_tty_restores_termios(self):
        master, slave = pty.openpty()
        try:
            path = Path(os.ttyname(slave))
            before = termios.tcgetattr(slave)
            handle = self.module.HostTTY(path)
            opened = handle.open()
            self.assertNotEqual(termios.tcgetattr(opened), before)
            handle.close()
            check = os.open(path, os.O_RDWR | os.O_NOCTTY)
            try:
                self.assertEqual(termios.tcgetattr(check), before)
            finally:
                os.close(check)
        finally:
            os.close(master)
            os.close(slave)

    def test_timeline_event_uses_single_events_schema(self):
        events = []
        self.module.timeline_event(events, "o0_session_start")
        self.assertEqual(set(events[0]), {"name", "timestamp_utc"})
        self.assertEqual(events[0]["name"], "o0_session_start")
        self.assertTrue(events[0]["timestamp_utc"].endswith("Z"))

    def test_offline_contract_forbids_device_reconfiguration(self):
        result = self.module.offline_check("aarch64-linux-gnu-gcc")
        self.assertTrue(result["source_present"])
        self.assertTrue(all(result["required_tokens"].values()))
        self.assertFalse(any(result["prohibited_tokens"].values()))
        self.assertFalse(result["safety"]["flash"])
        self.assertFalse(result["safety"]["reboot"])
        self.assertFalse(result["safety"]["configfs_write"])
        self.assertFalse(result["safety"]["sysfs_write"])
        self.assertTrue(result["safety"]["stock_tty_service_stop_start_restored"])
        self.assertFalse(result["safety"]["active_gadget_change"])

    def test_static_aarch64_daemon_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.module.build_daemon(Path(tmp), "aarch64-linux-gnu-gcc")
            artifact = self.module.resolve(Path(result["path"]))
            self.assertTrue(artifact.is_file())
            self.assertIn("ARM aarch64", result["file"])
            self.assertIn("statically linked", result["file"])
            self.assertEqual(len(result["sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
