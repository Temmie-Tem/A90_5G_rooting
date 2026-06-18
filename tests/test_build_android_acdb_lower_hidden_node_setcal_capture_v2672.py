import unittest

import build_android_acdb_lower_hidden_node_setcal_capture_v2672 as v2672


class V2672BuildContractTest(unittest.TestCase):
    def test_source_contract(self):
        state = v2672.source_state()
        self.assertTrue(state["required_ok"], state["required"])
        self.assertTrue(state["prohibited_ok"], state["prohibited"])
        self.assertEqual(state["v2672_contract"]["targets"][24], "0x000130da")
        self.assertEqual(state["v2672_contract"]["targets"][10], "0x00011394")
        self.assertEqual(state["v2672_contract"]["targets"][14], "0x00012e01")

    def test_make_payload_without_private_build(self):
        args = v2672.parse_args([])
        payload = v2672.make_payload(args)
        self.assertTrue(payload["ok"], payload)
        self.assertTrue(payload["host_only_build"])
        self.assertTrue(payload["measurement_boundary"]["no_live_default"])
        self.assertIn("create_cal_node", payload["capture_contract"]["hidden_offsets"])
        self.assertEqual(payload["capture_contract"]["target_cal_types"], [24, 10, 14])

    def test_patched_constants_restore(self):
        old_helper = v2672.v2659.HELPER_SOURCE_REL
        old_preinit = v2672.v2659.PREINIT_SOURCE_REL
        with v2672.patched_v2659_constants():
            self.assertEqual(v2672.v2659.HELPER_SOURCE_REL, v2672.HELPER_SOURCE_REL)
            self.assertEqual(v2672.v2659.PREINIT_SOURCE_REL, v2672.PREINIT_SOURCE_REL)
        self.assertEqual(v2672.v2659.HELPER_SOURCE_REL, old_helper)
        self.assertEqual(v2672.v2659.PREINIT_SOURCE_REL, old_preinit)


if __name__ == "__main__":
    unittest.main()
