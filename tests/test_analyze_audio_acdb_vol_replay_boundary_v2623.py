import struct
import unittest

import analyze_audio_acdb_vol_replay_boundary_v2623 as v2623


class V2623VolReplayBoundaryTest(unittest.TestCase):
    def test_decode_audio_cal_set_topology_entry(self):
        data = bytearray(64)
        struct.pack_into("<iiii", data, 0, 32, 0, 39, 16)
        struct.pack_into("<iiii", data, 16, 0, 0, 4916, 37)
        struct.pack_into("<iiii", data, 32, 4916, 0, 0, 0)
        decoded = v2623.decode_audio_cal_entry({
            "seq": 28,
            "request": "0xc00461cb",
            "bytes_hex": data.hex(),
        })
        self.assertIsNotNone(decoded)
        self.assertEqual(decoded["request_name"], "AUDIO_SET_CALIBRATION")
        self.assertEqual(decoded["cal_type"], 39)
        self.assertEqual(decoded["cal_type_name"], "CORE_CUSTOM_TOPOLOGIES_CAL_TYPE")
        self.assertEqual(decoded["cal_size"], 4916)
        self.assertEqual(decoded["mem_handle"], 37)

    def test_decode_audio_cal_allocate_vol_entry(self):
        data = bytearray(64)
        struct.pack_into("<iiii", data, 0, 32, 0, 12, 16)
        struct.pack_into("<iiii", data, 16, 0, 1, 0, 25)
        decoded = v2623.decode_audio_cal_entry({
            "request": "0xc00461c8",
            "bytes_hex": data.hex(),
        })
        self.assertIsNotNone(decoded)
        self.assertEqual(decoded["request_name"], "AUDIO_ALLOCATE_CALIBRATION")
        self.assertEqual(decoded["cal_type"], 12)
        self.assertEqual(decoded["cal_type_name"], "ADM_AUDVOL_CAL_TYPE")
        self.assertEqual(decoded["buffer_number"], 1)
        self.assertEqual(decoded["mem_handle"], 25)

    def test_vol_ret_summary_classifies_negative_rows(self):
        rows = [
            {"cmd": "0x0001326d", "buffer": "in", "ret": "0x00000000", "out_len": "0x0000000c", "all_zero": False},
            {"cmd": "0x0001326d", "buffer": "out", "ret": "0xffffffed", "out_len": "0x00000004", "all_zero": True},
            {"cmd": "0x0001326e", "buffer": "out", "ret": "0xffffffed", "out_len": "0x00000004", "all_zero": True},
        ]
        summary = v2623.vol_ret_summary(rows)
        self.assertEqual(summary["vol_out_row_count"], 2)
        self.assertEqual(summary["vol_ret_values"], [-19])
        self.assertTrue(summary["vol_ret_all_negative_19"])
        self.assertEqual(summary["vol_nonzero_payload_count"], 0)

    def test_successful_nonzero_payloads_filters_indirect_payloads(self):
        rows = [
            {"cmd": "0x13265", "buffer": "ind-ap-common", "ret": "0", "out_len": "0x46a4", "all_zero": False, "sha256": "abc", "seq": "4"},
            {"cmd": "0x1326d", "buffer": "out", "ret": "0xffffffed", "out_len": "4", "all_zero": True, "sha256": "zero"},
            {"cmd": "0x1326e", "buffer": "ind-ap-gain", "ret": "0", "out_len": "0x10", "all_zero": True, "sha256": "zero"},
        ]
        payloads = v2623.successful_nonzero_payloads(rows)
        self.assertEqual(len(payloads), 1)
        self.assertEqual(payloads[0]["buffer"], "ind-ap-common")
        self.assertEqual(payloads[0]["out_len"], 0x46A4)


if __name__ == "__main__":
    unittest.main()
