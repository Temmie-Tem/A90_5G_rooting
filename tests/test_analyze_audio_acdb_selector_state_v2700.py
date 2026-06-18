import unittest

import analyze_audio_acdb_selector_state_v2700 as v2700


def _synthetic_disasm() -> str:
    return "\n".join(
        [
            "    90ea:\tmovs\tr0, #24",
            "    90ec:\tbl\t#27732",
            "    910a:\tbl\t#27310",
            "    9110:\tstr\tr0, [sp, #68]",
            "    9112:\tstr\tr0, [sp, #56]",
            "    9154:\tmovw\tr0, #12506",
            "    9158:\tmovt\tr0, #1",
            "    924a:\tmovs\tr0, #10",
            "    924c:\tbl\t#27380",
            "    926c:\tbl\t#26956",
            "    9270:\tstr\tr0, [sp, #68]",
            "    9272:\tstr\tr0, [sp, #56]",
            "    92ba:\tmovw\tr0, #5012",
            "    92be:\tmovt\tr0, #1",
            "    93f6:\tmovs\tr0, #14",
            "    93f8:\tbl\t#26952",
            "    9416:\tbl\t#26530",
            "    941a:\tstr\tr0, [sp, #68]",
            "    941c:\tstr\tr0, [sp, #56]",
            "    945e:\tmovw\tr0, #11777",
            "    9462:\tmovt\tr0, #1",
        ]
    )


class AcdbSelectorStateV2700Test(unittest.TestCase):
    def test_parse_instructions_extracts_thumb_objdump_rows(self) -> None:
        instructions = v2700.parse_instructions("    924c:\tbl\t#27380\n")

        self.assertEqual(len(instructions), 1)
        self.assertEqual(instructions[0].addr, 0x924C)
        self.assertEqual(instructions[0].mnemonic, "bl")
        self.assertEqual(instructions[0].operands, "#27380")

    def test_branch_target_uses_thumb_pc_bias(self) -> None:
        instruction = v2700.Instruction(addr=0x924C, mnemonic="bl", operands="#27380", text="")

        self.assertEqual(v2700.branch_target(instruction), 0xFD44)

    def test_selector_shapes_share_loader_helpers_and_observed_words(self) -> None:
        shapes = v2700.analyze_selector_shapes(_synthetic_disasm())

        self.assertEqual([shape.cal_type for shape in shapes], [24, 10, 14])
        self.assertEqual({shape.node_fetch_call for shape in shapes}, {0xFD44})
        self.assertEqual({shape.prepare_call for shape in shapes}, {0xFBBC})
        self.assertEqual({shape.in_buf_words for shape in shapes}, {"{sp+56, sp+60} = {node_payload[+0], node_payload[+8]}"})
        self.assertEqual(shapes[0].observed_word1, 0xF14F6000)
        self.assertEqual(shapes[1].observed_ret, -12)
        self.assertEqual(shapes[2].latest_payload_state, "stale-selected-absent")

    def test_classification_pivots_past_loader_request_shape(self) -> None:
        shapes = v2700.analyze_selector_shapes(_synthetic_disasm())

        classification = v2700.classify_shapes(shapes)

        self.assertEqual(classification["decision"], "v2700-selector-state-localized-past-loader-request-shape")
        self.assertTrue(classification["identical_loader_request_shape"])
        self.assertEqual(classification["recommended_next"], "v2701-libaudcal-command-handler-re")


if __name__ == "__main__":
    unittest.main()
