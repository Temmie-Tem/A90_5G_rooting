from __future__ import annotations

import unittest

from _loader import load_script


recon = load_script(
    "workspace/public/src/scripts/revalidation/native_gpu_compute_c0_reference_v3299.py"
)


class NativeGpuComputeC0ReferenceV3299Tests(unittest.TestCase):
    def test_c0_reference_recon_passes_against_staged_sources(self) -> None:
        result = recon.run_recon()

        self.assertEqual(result["cycle"], "V3299")
        self.assertEqual(result["scope"], "gpu-compute-c0-reference-envelope-recon")
        self.assertTrue(result["passed"])
        self.assertTrue(result["checks"]["c0_reference_recon_passed"])
        self.assertEqual(result["offset_mismatches"], {})
        self.assertEqual(result["pm4_mismatches"], {})

    def test_compute_register_offsets_match_a640_reference(self) -> None:
        result = recon.run_recon()
        offsets = result["actual_reg_offsets"]

        self.assertEqual(offsets["SP_CS_CONST_CONFIG"], 0xB987)
        self.assertEqual(offsets["SP_CS_CONFIG"], 0xA9BB)
        self.assertEqual(offsets["SP_CS_INSTR_SIZE"], 0xA9BC)
        self.assertEqual(offsets["SP_CS_CNTL_0"], 0xA9B0)
        self.assertEqual(offsets["SP_CS_CNTL_1"], 0xA9B1)
        self.assertEqual(offsets["HLSQ_CS_CTRL_REG1"], 0xB9D0)
        self.assertEqual(offsets["SP_CS_WGE_CNTL"], 0xB998)
        self.assertEqual(offsets["SP_CS_BASE"], 0xA9B4)
        self.assertEqual(offsets["SP_CS_UAV_BASE"], 0xA9F2)
        self.assertEqual(offsets["SP_CS_USIZE"], 0xAA00)
        self.assertEqual(
            [offsets[f"SP_CS_NDRANGE_{idx}"] for idx in range(7)],
            [0xB990, 0xB991, 0xB992, 0xB993, 0xB994, 0xB995, 0xB996],
        )
        self.assertEqual(
            [
                offsets["SP_CS_KERNEL_GROUP_X"],
                offsets["SP_CS_KERNEL_GROUP_Y"],
                offsets["SP_CS_KERNEL_GROUP_Z"],
            ],
            [0xB999, 0xB99A, 0xB99B],
        )

    def test_pm4_opcodes_and_state_enums_are_source_verified(self) -> None:
        result = recon.run_recon()
        values = result["actual_pm4_values"]

        self.assertEqual(values["CP_EXEC_CS"], 0x33)
        self.assertEqual(values["CP_SET_MARKER"], 0x65)
        self.assertEqual(values["RM6_COMPUTE"], 0x08)
        self.assertEqual(values["SB6_CS_SHADER"], 0x0D)
        self.assertEqual(values["ST6_SHADER"], 0)
        self.assertEqual(values["ST6_CONSTANTS"], 1)
        self.assertEqual(values["ST6_UAV"], 3)
        self.assertEqual(values["SS6_DIRECT"], 0)
        self.assertEqual(values["SS6_INDIRECT"], 2)

    def test_ordered_envelope_preserves_mesa_compute_dispatch_sequence(self) -> None:
        result = recon.run_recon()

        self.assertEqual(
            [stage["stage"] for stage in result["ordered_envelope"]],
            [
                "cs_restore",
                "cs_program_emit_regs",
                "cs_shader_preload",
                "cs_const_emit",
                "cs_uav_emit",
                "compute_marker",
                "ndrange",
                "dispatch",
                "idle_and_readback",
            ],
        )
        marker = result["ordered_envelope"][5]
        self.assertEqual(marker["packet"], "CP_SET_MARKER")
        self.assertEqual(marker["mode"], "RM6_COMPUTE")
        dispatch = result["ordered_envelope"][7]
        self.assertEqual(dispatch["packet"], "CP_EXEC_CS")
        self.assertEqual(dispatch["ngroups"], [1, 1, 1])

    def test_c1_kernel_contract_is_fixed_before_live_dispatch(self) -> None:
        result = recon.run_recon()
        kernel = result["kernel_contract"]

        self.assertTrue(kernel["valid"])
        self.assertEqual(kernel["localsize"], [32, 1, 1])
        self.assertEqual(kernel["buf_words"], 32)
        self.assertEqual(kernel["invocationid_reg"], "r0.x")
        self.assertEqual(kernel["wgid_reg"], "r48.x")
        self.assertEqual(kernel["numwg_reg"], "c2.x")
        self.assertTrue(kernel["moves_invocation_id_to_store_offset"])
        self.assertTrue(kernel["stores_invocation_id_to_uav"])
        self.assertEqual(kernel["expected_readback_words"], 32)
        self.assertEqual(kernel["expected_readback"], list(range(32)))

    def test_byte_materialization_is_an_explicit_c1_gate(self) -> None:
        result = recon.run_recon()

        self.assertTrue(result["checks"]["ir3_disasm_available"])
        self.assertFalse(result["checks"]["mesa_build_has_full_nir"])
        self.assertFalse(result["checks"]["mesa_computerator_executable_available"])
        self.assertFalse(result["checks"]["kernel_bytes_verified"])
        self.assertFalse(result["checks"]["ready_for_c1_live"])
        self.assertIn("verify the generated words with ir3-disasm", result["next_required_before_c1_live"][1])

    def test_mesa_build_state_explains_assembler_gate(self) -> None:
        result = recon.run_recon()
        build = result["tools"]["mesa_build"]

        self.assertTrue(build["build_ninja_present"])
        self.assertTrue(build["computerator_target_present"])
        self.assertFalse(build["computerator_executable_present"])
        self.assertTrue(build["libnir_is_stub_only"])
        self.assertEqual(build["libnir_member_count"], 1)
        self.assertTrue(
            any("full NIR symbols" in blocker for blocker in build["blockers"])
        )


if __name__ == "__main__":
    unittest.main()
