import unittest

import analyze_audio_libaudcal_topology_data_handlers_v2702 as v2702


class LibaudcalTopologyDataHandlersV2702Test(unittest.TestCase):
    def test_branch_target_uses_thumb_pc_bias_for_blx_operand(self) -> None:
        ins = v2702.Instruction(addr=0x17098, mnemonic="blx", operands="#62052 <x>", text="")

        self.assertEqual(v2702.branch_target(ins), 0x26300)

    def test_parse_relplt_maps_jump_slots_to_plt_entries(self) -> None:
        rel = """
00027f3c  00000016 R_ARM_JUMP_SLOT 00000000  first_func
00027f40  00000016 R_ARM_JUMP_SLOT 00000000  second_func
"""

        symbols = v2702.parse_relplt(rel)

        self.assertEqual(symbols[0].plt_addr, 0x25C90)
        self.assertEqual(symbols[1].plt_addr, 0x25CA0)
        self.assertEqual(symbols[1].name, "second_func")

    def test_resolve_plt_symbol_accepts_branch_inside_plt_slot(self) -> None:
        symbols = [
            v2702.PltSymbol(index=0, plt_addr=0x25C90, got_addr=0x27F3C, name="first"),
            v2702.PltSymbol(index=1, plt_addr=0x25CA0, got_addr=0x27F40, name="second"),
        ]

        resolved = v2702.resolve_plt_symbol(symbols, 0x25CA2)

        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.name, "second")

    def test_find_table_id_combines_latest_movw_movt_r1_before_call(self) -> None:
        instructions = v2702.parse_instructions(
            "\n".join(
                [
                    "   1707e: 40 f6 47 11                   \tmovw\tr1, #11847",
                    "   17082: c0 f2 01 01                   \tmovt\tr1, #1",
                    "   17098: ff f7 00 e8                   \tblx\t#62052",
                ]
            )
        )

        self.assertEqual(v2702.find_table_id(instructions, 0x17098), 0x12E47)

    def test_analyze_handler_detects_buffer_size_gate(self) -> None:
        disasm = "\n".join(
            [
                "   1707e: 40 f6 47 11                   \tmovw\tr1, #11847",
                "   17082: c0 f2 01 01                   \tmovt\tr1, #1",
                "   17098: ff f7 00 e8                   \tblx\t#62052",
                "   170ac: 11 f0 e0 30                   \tmvn\tr0, #17",
                "   170c0: 28 68                         \tldr\tr0, [r5]",
                "   170c2: 03 9a                         \tldr\tr2, [sp, #12]",
                "   170d6: 0b f0 e0 30                   \tmvn\tr0, #11",
                "   170e4: 68 68                         \tldr\tr0, [r5, #4]",
                "   170e6: ff f7 28 e8                   \tblx\t#61992",
                "   170ec: 20 60                         \tstr\tr0, [r4]",
            ]
        )
        symbols = [
            v2702.PltSymbol(index=index, plt_addr=0x25C90 + index * 0x10, got_addr=0, name=f"slot_{index}")
            for index in range(0x69)
        ]
        symbols[0x67] = v2702.PltSymbol(index=0x67, plt_addr=0x26300, got_addr=0, name="acdbdata_ioctl")
        symbols[0x68] = v2702.PltSymbol(index=0x68, plt_addr=0x26310, got_addr=0, name="__aeabi_memcpy")

        handler = v2702.analyze_handler(v2702.HANDLERS[0], disasm, symbols)

        self.assertEqual(handler.table_id, 0x12E47)
        self.assertEqual(handler.lookup_plt_symbol, "acdbdata_ioctl")
        self.assertEqual(handler.copy_plt_symbol, "__aeabi_memcpy")
        self.assertTrue(handler.has_buffer_size_gate)
        self.assertEqual(handler.insufficient_buffer_return_addr, 0x170D6)

    def test_classification_relabels_cal10_minus_12_as_buffer_too_small(self) -> None:
        handlers = [
            v2702.TopologyHandler(
                cal_type=10,
                role="ADM_CUST_TOPOLOGY",
                cmd=0x11394,
                symbol="AcdbCmdGetAudioCOPPTopologyData",
                symbol_addr=0x17050,
                table_id=0x12E47,
                lookup_call_addr=0,
                lookup_call_target=0,
                lookup_plt_addr=0x26300,
                lookup_plt_symbol="acdbdata_ioctl",
                copy_call_addr=0,
                copy_call_target=0,
                copy_plt_addr=0x26310,
                copy_plt_symbol="__aeabi_memcpy",
                word0_length_load_addr=1,
                required_size_load_addr=2,
                insufficient_buffer_return_addr=3,
                word1_destination_load_addr=4,
                return_size_store_addr=5,
                fail_lookup_return_addr=6,
                observed_v2700_ret=-12,
                observed_v2700_state="absent-ret-minus-12",
                has_buffer_size_gate=True,
                interpretation="",
            ),
            v2702.TopologyHandler(
                cal_type=14,
                role="ASM_CUST_TOPOLOGY",
                cmd=0x12E01,
                symbol="AcdbCmdGetAudioPOPPTopologyData",
                symbol_addr=0x171A4,
                table_id=0x12E48,
                lookup_call_addr=0,
                lookup_call_target=0,
                lookup_plt_addr=0x26300,
                lookup_plt_symbol="acdbdata_ioctl",
                copy_call_addr=0,
                copy_call_target=0,
                copy_plt_addr=0x26310,
                copy_plt_symbol="__aeabi_memcpy",
                word0_length_load_addr=1,
                required_size_load_addr=2,
                insufficient_buffer_return_addr=3,
                word1_destination_load_addr=4,
                return_size_store_addr=5,
                fail_lookup_return_addr=6,
                observed_v2700_ret=0,
                observed_v2700_state="stale-selected-absent",
                has_buffer_size_gate=True,
                interpretation="",
            ),
            v2702.TopologyHandler(
                cal_type=24,
                role="AFE_CUST_TOPOLOGY",
                cmd=0x130DA,
                symbol="AcdbCmdGetAfeTopologyData",
                symbol_addr=0x17734,
                table_id=0x130DE,
                lookup_call_addr=0,
                lookup_call_target=0,
                lookup_plt_addr=0x26300,
                lookup_plt_symbol="acdbdata_ioctl",
                copy_call_addr=0,
                copy_call_target=0,
                copy_plt_addr=0x26310,
                copy_plt_symbol="__aeabi_memcpy",
                word0_length_load_addr=1,
                required_size_load_addr=2,
                insufficient_buffer_return_addr=3,
                word1_destination_load_addr=4,
                return_size_store_addr=5,
                fail_lookup_return_addr=6,
                observed_v2700_ret=0,
                observed_v2700_state="aligned-selected-present",
                has_buffer_size_gate=True,
                interpretation="",
            ),
        ]

        classification = v2702.classify_handlers(handlers)

        self.assertEqual(classification["decision"], "v2702-libaudcal-ret-minus-12-is-buffer-too-small")
        self.assertTrue(classification["cal10_ret_minus_12_reclassified"])
        self.assertEqual(classification["recommended_next"], "v2703-ownprocess-large-buffer-topology-get-plan")


if __name__ == "__main__":
    unittest.main()
