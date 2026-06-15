from __future__ import annotations

import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

import native_audio_acdbtap_live_planner_v2476 as v2476


class V2476AcdbTapPlannerTests(unittest.TestCase):
    def test_command_plan_mentions_preload_and_restore(self) -> None:
        plan = v2476.live_command_plan(Namespace(adb="adb", serial=None))
        flat = str(plan)
        self.assertIn("LD_PRELOAD", flat)
        self.assertIn(v2476.REMOTE_LIB, flat)
        self.assertIn(f"chmod 755 {v2476.REMOTE_STAGE_DIR}", flat)
        self.assertIn(f"chmod 777 {v2476.REMOTE_STAGE_DIR}/incoming", flat)
        self.assertIn(f"chmod 700 {v2476.REMOTE_STAGE_DIR}/lib", flat)
        self.assertIn("ctl.stop", flat)
        self.assertIn("ctl.start", flat)
        self.assertIn("rollback_v2321", flat)

    def test_command_safety_rejects_native_calibration_and_silent_permissive(self) -> None:
        bad = {"commands": ["AUDIO_SET_CALIBRATION", "setenforce 0"]}
        safety = v2476.command_safety(bad)
        names = {item["name"] for item in safety["findings"]}
        self.assertIn("native_cal_set_symbol", names)
        self.assertIn("silent_permissive", names)

    def test_file_state_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.bin"
            path.write_bytes(b"abc")
            state = v2476.file_state(path, expected_sha256="ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")
            self.assertTrue(state["ok"])
            self.assertTrue(state["sha256_ok"])

    def test_stage_private_inputs_copies_when_sources_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_root = v2476.ROOT
            old_dump = v2476.V2324_VENDOR_DUMP
            root = Path(tmp)
            dump = root / "workspace/private/runs/audio/v2324-aud0-inventory/vendor_dump"
            (dump / "lib").mkdir(parents=True)
            (dump / "etc/acdbdata").mkdir(parents=True)
            (dump / "lib/libaudcal.so").write_bytes(b"lib")
            (dump / "etc/acdbdata/test.acdb").write_bytes(b"acdb")
            try:
                v2476.ROOT = root
                v2476.V2324_VENDOR_DUMP = dump
                result = v2476.stage_private_inputs(root / "workspace/private/inputs/audio/acdb-cross-validation/v2476")
            finally:
                v2476.ROOT = old_root
                v2476.V2324_VENDOR_DUMP = old_dump
            self.assertTrue(result["ok"])
            self.assertGreaterEqual(result["copied_count"], 2)


if __name__ == "__main__":
    unittest.main()
