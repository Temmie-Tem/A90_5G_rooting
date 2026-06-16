"""Tests for the V2594 ACDB send_audio_cal_v5 pre-GET recon parser."""

from __future__ import annotations

import unittest

from _loader import load_revalidation

v2594 = load_revalidation("native_audio_acdb_send_audio_cal_preget_recon_v2594")


class AcdbSendAudioCalPregetReconV2594(unittest.TestCase):
    def test_plt_mapping_uses_relocation_order(self) -> None:
        relocs = """
Relocation section '.rel.plt' at offset 0x2428 contains 3 entries:
0001727c  00000116 R_ARM_JUMP_SLOT        00000000   first@LIBC
00017280  00002816 R_ARM_JUMP_SLOT        00000000   pthread_mutex_lock@LIBC
00017284  00002916 R_ARM_JUMP_SLOT        00000000   acdb_ioctl
"""
        plt = """
000159d0 .plt:
   159d0: 04 e0 2d e5
   159f0: 00 c6 8f e2
   159f4: 00 ca 8c e2
   159f8: 00 f0 bc e5
   15a00: 00 c6 8f e2
   15a04: 00 ca 8c e2
   15a08: 00 f0 bc e5
   15a10: 00 c6 8f e2
   15a14: 00 ca 8c e2
   15a18: 00 f0 bc e5
"""

        mapping = v2594.map_plt(relocs, plt)

        self.assertEqual(mapping[0x159F0], "first")
        self.assertEqual(mapping[0x15A00], "pthread_mutex_lock")
        self.assertEqual(mapping[0x15A10], "acdb_ioctl")

    def test_parse_calls_resolves_nearest_plt_and_local_symbol(self) -> None:
        disasm = """
    9d50: 0b f0 56 ee                   blx #48300
    9df8: 05 f0 a4 ff                   bl #24392
    9e86: 0b f0 f4 ed                   blx #48104
"""
        plt = {0x15A00: "pthread_mutex_lock", 0x15A70: "acdb_ioctl"}
        symbols = [{"addr": 0xFAB0, "size": 0x400, "name": "acdb_loader_get_mod_loading_meta_info"}]

        calls = v2594.parse_calls(disasm, plt, symbols)

        self.assertEqual(calls[0]["import_symbol"], "pthread_mutex_lock")
        self.assertEqual(calls[1]["dest"], "0xfd44")
        self.assertEqual(calls[1]["local_symbol"], "acdb_loader_get_mod_loading_meta_info")
        self.assertEqual(calls[2]["import_symbol"], "acdb_ioctl")

    def test_direct_get_geometry_is_metadata_only(self) -> None:
        self.assertEqual(v2594.FIRST_DISPATCH_CMD, 0x1122E)
        self.assertEqual(v2594.FIRST_DISPATCH_IN_LEN, 4)
        self.assertEqual(v2594.FIRST_DISPATCH_OUT_LEN, 4)
        self.assertEqual(v2594.FIRST_DISPATCH_INBUF_WORD, 0x11135)


if __name__ == "__main__":
    unittest.main()
