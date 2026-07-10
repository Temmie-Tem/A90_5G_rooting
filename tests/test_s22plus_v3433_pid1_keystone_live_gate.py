import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(
    "workspace/public/src/scripts/revalidation/"
    "s22plus_v3433_pid1_keystone_live_gate.py"
)


def load_module():
    script_dir = str(SCRIPT.parent.resolve())
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location(
        "s22plus_v3433_pid1_keystone_live_gate", SCRIPT
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class S22PlusV3433Pid1KeystoneLiveGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()
        cls.root = cls.module.keystone.repo_root()

    def test_candidate_artifact_and_marker_roundtrip(self):
        expectation, marker = self.module.load_candidate(self.root)
        self.assertEqual(expectation.run_id, self.module.EXPECTED_RUN_ID)
        self.assertEqual(marker["run_id"], self.module.EXPECTED_RUN_ID)
        self.assertEqual(
            marker["keystone_contract_sha256"],
            self.module.keystone.CONTRACT_SHA256,
        )
        self.assertEqual(
            self.module.tar_members(self.root / self.module.CANDIDATE_AP),
            ["boot.img.lz4"],
        )

    def test_offline_plan_is_not_live_authorization(self):
        plan = self.module.offline_plan(self.root)
        self.assertEqual(plan["schema"], self.module.SCHEMA)
        self.assertTrue(plan["candidate_flash"])
        self.assertTrue(plan["manual_transition"])
        self.assertFalse(plan["live_authorized_by_plan"])
        self.assertEqual(
            plan["candidate_ap_sha256"],
            self.module.EXPECTED_CANDIDATE_AP_SHA256,
        )

    def test_active_exception_preserves_exact_pins(self):
        segment = self.module.active_exception_segment(
            (self.root / "AGENTS.md").read_text(encoding="utf-8")
        )
        self.module.verify_agents_exception(self.root)
        self.assertNotIn("Consumed/retired", segment)
        for marker in self.module.policy_markers(self.root):
            self.assertIn(marker, " ".join(segment.split()))

    def test_consumed_exception_is_rejected_for_new_live(self):
        heading = self.module.ACTIVE_EXCEPTION_HEADING
        segment = heading + "\n   Consumed/retired " + " ".join(
            self.module.policy_markers(self.root)
        )
        with self.assertRaisesRegex(self.module.LiveGateError, "already consumed"):
            self.module.validate_exception_segment(
                segment,
                self.module.policy_markers(self.root),
                allow_consumed=False,
            )
        self.module.validate_exception_segment(
            segment,
            self.module.policy_markers(self.root),
            allow_consumed=True,
        )

    def test_bad_live_ack_stops_before_policy_or_device(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(
                self.module.LiveGateError, "live acknowledgement token mismatch"
            ):
                self.module.live_run(
                    self.root,
                    Path(temp),
                    "wrong-token",
                    self.module.MAX_MANUAL_WAIT_SEC,
                )

    def test_file_pin_detects_post_verification_change(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "artifact"
            path.write_bytes(b"before")
            pin = self.module.file_pin(path)
            path.write_bytes(b"after-longer")
            with self.assertRaisesRegex(
                self.module.LiveGateError, "pinned file changed"
            ):
                self.module.require_unchanged(pin)

    def test_run_directory_uses_v3433_prefix(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run_dir = self.module.allocate_run_dir(root, None)
            self.assertTrue(run_dir.name.startswith("s22plus_v3433_pid1_keystone_"))

    def test_timeline_uses_canonical_eight_phase_names(self):
        self.assertEqual(
            self.module.control.TIMELINE_REQUIRED_NAMES,
            (
                "live_session_start",
                "candidate_flash_start",
                "candidate_flash_done",
                "candidate_boot_ready",
                "rollback_flash_start",
                "rollback_flash_done",
                "rollback_boot_ready",
                "live_session_end",
            ),
        )

    def test_exact_marker_double_read_is_positive(self):
        expectation, marker = self.module.load_candidate(self.root)
        payload = marker["frame"].encode("ascii")
        result = self.module.classify_first_boot_capture(
            payload,
            payload,
            expectation,
            first_eof=True,
            second_eof=True,
        )
        self.assertEqual(
            result["verdict"], "PASS_PID1_EXECUTION_AND_OBSERVER_LOAD"
        )

    def test_absent_marker_is_no_proof(self):
        expectation, _ = self.module.load_candidate(self.root)
        payload = b"retained kernel text"
        result = self.module.classify_first_boot_capture(
            payload,
            payload,
            expectation,
            first_eof=True,
            second_eof=True,
        )
        self.assertEqual(
            result["verdict"],
            "NO_PROOF_PID1_VS_OBSERVER_UNRESOLVED_STOP",
        )

    def test_duplicate_marker_is_fail_stop(self):
        expectation, marker = self.module.load_candidate(self.root)
        payload = marker["frame"].encode("ascii") * 2
        result = self.module.classify_first_boot_capture(
            payload,
            payload,
            expectation,
            first_eof=True,
            second_eof=True,
        )
        self.assertEqual(result["verdict"], "FAIL_STOP")

    def test_capture_integrity_failures_are_unavailable(self):
        expectation, _ = self.module.load_candidate(self.root)
        non_eof = self.module.classify_first_boot_capture(
            b"a",
            b"a",
            expectation,
            first_eof=False,
            second_eof=True,
        )
        mismatch = self.module.classify_first_boot_capture(
            b"a",
            b"b",
            expectation,
            first_eof=True,
            second_eof=True,
        )
        self.assertEqual(non_eof["verdict"], "UNAVAILABLE_STOP_NON_EOF_CAPTURE")
        self.assertEqual(
            mismatch["verdict"], "UNAVAILABLE_STOP_DOUBLE_READ_MISMATCH"
        )

    def test_preflight_requires_exact_osrelease_and_two_negative_controls(self):
        source = (self.root / SCRIPT).read_text(encoding="utf-8")
        self.assertIn("keystone.EXPECTED_LIVE_OSRELEASE", source)
        self.assertIn('control.read_root_bytes(serial, "cat /proc/ap_klog")', source)
        self.assertIn(
            'control.read_root_bytes(serial, "cat /proc/last_kmsg")', source
        )
        self.assertIn(
            'keystone.classify_snapshot(\n        "baseline", baseline_ap', source
        )
        self.assertIn(
            'keystone.classify_snapshot(\n        "baseline", baseline_last', source
        )

    def test_source_contract_is_boot_only_and_attended(self):
        source = (self.root / SCRIPT).read_text(encoding="utf-8")
        self.assertIn('reboot", "download"', source)
        self.assertIn("MANUAL_ACTION_REQUIRED enter Samsung RDX/Download", source)
        self.assertIn("first_boot_capture", source)
        self.assertIn("candidate AP must contain exactly boot.img.lz4", source)
        self.assertIn("sha256sum /dev/block/by-name/boot", source)
        self.assertNotIn("emit_marker(", source)
        self.assertNotIn("dd if=", source)
        self.assertNotIn("dd of=", source)
        self.assertNotIn("/sys/module/", source)
        self.assertNotIn("usb_gadget", source)


if __name__ == "__main__":
    unittest.main()
