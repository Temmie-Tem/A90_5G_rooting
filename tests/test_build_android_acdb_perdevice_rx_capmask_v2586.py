"""Host-only tests for the V2586 ACDB RX cap-mask build unit."""

from __future__ import annotations

import unittest

from _loader import load_revalidation

v2586 = load_revalidation("build_android_acdb_perdevice_rx_capmask_v2586")


class AcdbPerdeviceRxCapmaskBuildV2586(unittest.TestCase):
    def test_source_state_preserves_v2572_shape_and_allows_capmask_override(self) -> None:
        state = v2586.source_state()
        required = state["required"]

        self.assertTrue(state["required_ok"], state)
        self.assertTrue(state["prohibited_ok"], state)
        self.assertTrue(required["preinit_skips_real_common_topology_by_default"])
        self.assertTrue(required["preinit_calls_send_audio_cal_v5"])
        self.assertTrue(required["preinit_rx_path_default_zero"])
        self.assertTrue(required["preinit_rx_path_compile_override_guard"])
        self.assertEqual(state["v2586_delta"]["send_audio_cal_v5_arg2"], 1)
        self.assertEqual(state["v2586_delta"]["compile_override"], "-DA90_SPEAKER_RX_PATH=1")

    def test_payload_contract_documents_arg2_one_and_boundaries(self) -> None:
        class Args:
            build = False
            build_root = v2586.DEFAULT_BUILD_ROOT
            readelf = "readelf"
            file = "file"
            clang = v2586.v2572.TOOLCHAIN_ROOT / "bin/clang"
            lld = v2586.v2572.TOOLCHAIN_ROOT / "bin/ld.lld"

        payload = v2586.make_payload(Args())
        contract = payload["capture_contract"]
        boundary = payload["measurement_boundary"]

        self.assertIn("send_audio_cal_v5(15, 1, 0x11135", contract["per_device_call"])
        self.assertIn("arg2", contract["delta_from_v2572"])
        self.assertTrue(boundary["no_live_default"])
        self.assertTrue(boundary["no_native_replay"])
        self.assertTrue(boundary["no_speaker_write"])
        self.assertEqual(boundary["fake_audio_cal_env"], "A90_ACDB_FAKE_ALLOCATE=1")


if __name__ == "__main__":
    unittest.main()
