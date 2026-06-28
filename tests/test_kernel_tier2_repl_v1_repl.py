from __future__ import annotations

import hashlib
import struct
import unittest

from _loader import load_script


runner = load_script(
    "workspace/public/src/scripts/revalidation/build_kernel_tier2_repl_v1_repl.py"
)


class KernelTier2ReplV1ReplTests(unittest.TestCase):
    def test_repl_injection_contract(self) -> None:
        payload = runner.build_repl_injection(
            runner.ENTRY_OFF,
            runner.NEXT_MAGIC_OFF,
            runner.stage_c.PRINTK_EXPECTED_ENTRY_OFF,
        )

        words = [
            struct.unpack_from("<I", payload, index)[0]
            for index in range(0, runner.CODE_WORD_COUNT * 4, 4)
        ]
        self.assertEqual(len(payload), runner.NEXT_MAGIC_OFF - runner.ENTRY_OFF)
        self.assertEqual(len(payload), runner.EXPECTED_PATCH_LEN)

        self.assertEqual(words[0], runner.stage_c.U32_EOR_PROLOGUE)
        self.assertEqual(words[1], 0xA9BE47F0)  # stp x16,x17,[sp,#-32]!
        self.assertEqual(words[2], 0xF9000BE3)  # str x3,[sp,#16]
        self.assertEqual(words[3], 0x580005A7)  # ldr x7, magic_literal
        self.assertEqual(words[7], 0x39402044)  # ldrb w4,[x2,#8]
        self.assertEqual(words[10], 0x36080064)  # tbz w4,#1,low_ops
        self.assertEqual(words[15], 0x10000001)  # adr x1,.
        self.assertEqual(words[19], runner.encode_cmp_x_imm(6, runner.PEEK_MAX_LEN))
        self.assertEqual(words[27], runner.encode_b_cond_index(27, 30, 0x1))
        self.assertEqual(words[39], runner.encode_blr(9))
        self.assertEqual(words[44], 0xF9400BE0)  # ldr x0,[sp,#16]
        self.assertEqual(words[45], 0xA8C247F0)  # ldp x16,x17,[sp],#32
        self.assertEqual(words[46], runner.stage_c.U32_EOR_EPILOGUE)
        self.assertEqual(words[47], runner.stage_c.U32_RET)
        self.assertEqual(
            runner.stage_c.decode_bl_target(
                runner.stage_c.kernel_vaddr(runner.ENTRY_OFF + 43 * 4),
                words[43],
            ),
            runner.PRINTK_ENTRY_VADDR,
        )
        self.assertEqual(
            struct.unpack_from("<Q", payload, runner.MAGIC_LITERAL_WORD_INDEX * 4)[0],
            runner.REPL_MAGIC,
        )
        self.assertIn(runner.FORMAT, payload)

    def test_private_v2321_image_signatures_when_available(self) -> None:
        if not runner.BASE_BOOT.exists():
            self.skipTest("private v2321 boot image unavailable")

        image = runner.BASE_BOOT.read_bytes()
        self.assertEqual(hashlib.sha256(image).hexdigest(), runner.BASE_BOOT_SHA256)
        layout = runner.stage_c.parse_boot_layout(image)
        kernel = image[layout.kernel_off : layout.kernel_off + layout.kernel_size]

        runner._assert_force_no_nap_store_fingerprint(kernel)
        self.assertEqual(
            runner.stage_c.locate_printk_variadic_wrapper(kernel),
            (
                runner.stage_c.PRINTK_EXPECTED_ENTRY_OFF - 4,
                runner.stage_c.PRINTK_EXPECTED_ENTRY_OFF,
                runner.stage_c.PRINTK_EXPECTED_VA_HELPER_OFF,
                runner.stage_c.PRINTK_EXPECTED_EMIT_CORE_OFF,
            ),
        )


if __name__ == "__main__":
    unittest.main()
