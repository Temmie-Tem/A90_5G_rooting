import importlib.util
import json
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


SCRIPT = Path(
    "workspace/public/src/scripts/revalidation/s22plus_fyg8_r4w1c_connected_gate.py"
)


def load_module():
    script_dir = str(SCRIPT.parent.resolve())
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location("r4w1c_connected_gate_tested", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class S22PlusFyg8R4W1CConnectedGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def build_evidence_fixture(self, root: Path):
        module = self.module
        run_dir = root / module.RUN_ROOT / "connected-fixture"
        run_dir.mkdir(parents=True)
        empty_runner = lambda _argv, _timeout: SimpleNamespace(
            returncode=0, stdout="", stderr=""
        )
        phase_payload = {
            "mode": "connected-read-only",
            "no_odin_endpoint": True,
            "initial_snapshot_sequence": 0,
            "final_snapshot_sequence": 1,
            "android_serial": "serial",
            "boot_id": "12345678-1234-1234-1234-123456789abc",
        }
        with module.odin_core.transaction_session(run_dir) as lease:
            first = module.odin_core.wait_for_no_live_endpoint(
                Path("odin4"),
                run_dir,
                timeout_sec=1,
                lease=lease,
                runner=empty_runner,
                device_identity=lambda _path: None,
                device_inventory=lambda: {},
            )
            module.odin_core.wait_for_no_live_endpoint(
                Path("odin4"),
                run_dir,
                timeout_sec=1,
                sequence_start=first.next_sequence,
                lease=lease,
                runner=empty_runner,
                device_identity=lambda _path: None,
                device_inventory=lambda: {},
            )
            module.odin_core.create_phase_receipt(
                run_dir,
                "prepared",
                phase_payload,
                lease=lease,
            )
        android = {
            "model": "SM-S906N",
            "device": "g0q",
            "bootloader": "S906NKSS7FYG8",
            "incremental": "S906NKSS7FYG8",
            "boot_completed": "1",
            "bootanim": "stopped",
            "verified_boot_state": "orange",
            "root": "uid=0(root)",
            "boot_sha256": module.EXPECTED_MAGISK_BOOT_SHA256,
            "dtbo_sha256": module.EXPECTED_DTBO_SHA256,
            "recovery_sha256": module.EXPECTED_RECOVERY_SHA256,
            "vendor_boot_sha256": module.EXPECTED_VENDOR_BOOT_SHA256,
        }

        def observer(name, count):
            payload = b"clean-" + name.encode("ascii")
            digest = module.core.sha256_bytes(payload)
            reads = []
            for index in range(count):
                suffix = f"_{index + 1}" if count > 1 else ""
                path = run_dir / f"baseline_{name}{suffix}.bin"
                path.write_bytes(payload)
                path.with_suffix(path.suffix + ".stderr").write_bytes(b"")
                reads.append(
                    {
                        "path": str(path),
                        "bytes": len(payload),
                        "sha256": digest,
                        "returncode": 0,
                        "stderr_bytes": 0,
                        "read_to_eof": True,
                        "elapsed_sec": 0.1,
                    }
                )
            return {
                "reads": reads,
                "read_count": count,
                "byte_identical": True,
                "read_to_eof": True,
                "stderr_bytes": 0,
                "bytes": len(payload),
                "sha256": digest,
                "marker": module.classify_marker(payload),
            }

        baseline = {
            "target": module.TARGET,
            "android": android,
            "final_android": android,
            "android_serial": "serial",
            "boot_id": "12345678-1234-1234-1234-123456789abc",
            "sec_log_buf_live": True,
            "bind": module.EXPECTED_BIND,
            "pstore_console_absent": {
                path: True for path in module.PSTORE_PATHS
            },
            "observers": {
                "ap_klog": observer("ap_klog", 1),
                "last_kmsg": observer("last_kmsg", 2),
            },
            "no_odin_endpoint": True,
            "odin_evidence": module.collect_odin_evidence(
                root,
                run_dir,
                expected_phase_payload=phase_payload,
            ),
            "device_writes": False,
        }
        preflight_path = run_dir / "connected_preflight.json"
        module.core.durable_write_json(preflight_path, baseline)
        timeline_path = run_dir / "timeline.json"
        events = []
        for name in module.core.TIMELINE_NAMES:
            module.core.append_event(timeline_path, events, name)
        draft = root / module.POLICY_DRAFT
        draft.parent.mkdir(parents=True, exist_ok=True)
        draft.write_text("test policy draft\n", encoding="ascii")
        clause = "test connected active clause"
        runtime_pins = {
            "helper_sha256": "a" * 64,
            "test_sha256": "b" * 64,
            "policy_draft_sha256": module.core.sha256_file(draft),
            "policy_clause_sha256": module.core.sha256_bytes(clause.encode("utf-8")),
        }
        result = {
            "schema": module.SCHEMA,
            "mode": "connected-read-only-dry-run",
            "target": module.TARGET,
            "artifacts": {},
            "baseline": baseline,
            "runtime_pins": runtime_pins,
            "evidence": {
                "timeline": {
                    "path": str(timeline_path.relative_to(root)),
                    **module.core.hash_stable_file(timeline_path),
                },
                "preflight": {
                    "path": str(preflight_path.relative_to(root)),
                    **module.core.hash_stable_file(preflight_path),
                },
            },
            "timeline_semantics": {},
            "device_contact": True,
            "device_writes": False,
            "reboot": False,
            "download_transition": False,
            "odin_transfer": False,
            "flash": False,
            "verdict": module.VERDICT,
        }
        return run_dir, result, clause

    def test_exact_artifact_and_transport_pins(self):
        module = self.module
        self.assertEqual(
            module.EXPECTED_CANDIDATE_BOOT_SHA256,
            "1d394028714c48cfc0fd220acade9ead9a49ea21a81c59b2b87f88e61de704b0",
        )
        self.assertEqual(
            module.EXPECTED_CANDIDATE_AP_SHA256,
            "85514e79e3400de30b7146606a9e86c3655fc7a8766daba5f054ae1bd54fd42f",
        )
        self.assertEqual(
            module.EXPECTED_ODIN_CORE_SHA256,
            "ab418aac5ce4c854f433e2132bd9536a610991384ec82c50dc0ba063f1888a9b",
        )
        self.assertEqual(module.DEFAULT_REPRO.name, "reproduction-h")

    def test_parser_exposes_no_live_or_recovery_mode(self):
        parser = self.module.build_parser()
        options = {action.dest for action in parser._actions}
        self.assertIn("offline_check", options)
        self.assertIn("connected_read_only_dry_run", options)
        self.assertNotIn("live", options)
        self.assertNotIn("rollback_from_download", options)

    def test_marker_baseline_rejects_exact_and_foreign_family(self):
        module = self.module
        clean = module.classify_marker(b"ordinary retained log")
        self.assertTrue(clean["baseline_absent"])
        exact = module.classify_marker(module.MARKER)
        self.assertFalse(exact["baseline_absent"])
        foreign = module.classify_marker(b"[[S22R4W1B|id=foreign]]")
        self.assertTrue(foreign["integrity_issue"])

    def test_policy_activation_requires_exact_single_sentinel_and_pins(self):
        module = self.module
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            draft = root / module.POLICY_DRAFT
            draft.parent.mkdir(parents=True)
            draft.write_text("draft\n", encoding="ascii")
            draft_sha = module.core.sha256_file(draft)
            (root / "AGENTS.md").write_text("unrelated\n", encoding="ascii")
            with mock.patch.object(module, "policy_required_values", return_value=("pin-a",)):
                self.assertFalse(module.policy_active(root))
                (root / "AGENTS.md").write_text(
                    f"{module.POLICY_CLAUSE_BEGIN}\n{module.ACTIVE_SENTINEL}\n"
                    f"pin-a\n{draft_sha}\n{module.POLICY_CLAUSE_END}\n",
                    encoding="ascii",
                )
                self.assertTrue(module.policy_active(root))
                (root / "AGENTS.md").write_text(
                    f"{module.POLICY_CLAUSE_BEGIN}\n{module.ACTIVE_SENTINEL}\n"
                    f"{module.ACTIVE_SENTINEL}\npin-a\n{draft_sha}\n"
                    f"{module.POLICY_CLAUSE_END}\n",
                    encoding="ascii",
                )
                self.assertFalse(module.policy_active(root))

    def test_policy_identity_detects_mid_run_clause_replacement(self):
        module = self.module
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            draft = root / module.POLICY_DRAFT
            draft.parent.mkdir(parents=True)
            draft.write_text(
                f"DRAFT_INACTIVE\n{module.ACTIVE_SENTINEL}\n",
                encoding="ascii",
            )
            with mock.patch.object(
                module, "policy_required_values", return_value=()
            ), mock.patch.object(
                module, "helper_sha256", return_value="a" * 64
            ), mock.patch.object(
                module, "test_sha256", return_value="b" * 64
            ), mock.patch.object(
                module, "policy_clause", side_effect=["clause-a", "clause-b"]
            ):
                before = module.verify_policy_draft(root)
                after = module.verify_policy_draft(root)
            self.assertNotEqual(
                before["policy_clause_sha256"],
                after["policy_clause_sha256"],
            )

    def test_connected_dry_run_fails_before_contact_without_policy_or_ack(self):
        module = self.module
        args = module.build_parser().parse_args(["--connected-read-only-dry-run"])
        with mock.patch.object(module, "policy_active", return_value=False), mock.patch.object(
            module, "connected_preflight"
        ) as preflight:
            with self.assertRaises(module.GateError):
                module.connected_dry_run(Path("/tmp/root"), args, {}, {})
            preflight.assert_not_called()

        args.ack = "wrong"
        with mock.patch.object(module, "policy_active", return_value=True), mock.patch.object(
            module, "connected_preflight"
        ) as preflight:
            with self.assertRaises(module.GateError):
                module.connected_dry_run(Path("/tmp/root"), args, {}, {})
            preflight.assert_not_called()

    def test_connected_preflight_requires_proven_odin_absence_before_adb(self):
        module = self.module
        absence = module.odin_core.AbsenceResult(absent=False, next_sequence=1, timed_out=True)
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            with mock.patch.object(
                module.odin_core, "wait_for_no_live_endpoint", return_value=absence
            ), mock.patch.object(module, "current_android_exact") as android:
                with self.assertRaises(module.GateError):
                    module.connected_preflight(
                        run_dir,
                        run_dir,
                        Path("/odin"),
                        odin_absence_wait_sec=1.0,
                        lease=object(),
                    )
                android.assert_not_called()

    def test_connected_preflight_uses_new_odin_core_and_is_read_only(self):
        module = self.module
        absence = module.odin_core.AbsenceResult(
            absent=True, next_sequence=1, timed_out=False
        )
        final_absence = module.odin_core.AbsenceResult(
            absent=True, next_sequence=2, timed_out=False
        )
        snapshot0 = {
            "sequence": 0,
            "live_devices": [],
            "live_device_identities": [],
            "stale_devices": [],
        }
        snapshot1 = {**snapshot0, "sequence": 1}
        android = {
            "model": "SM-S906N",
            "device": "g0q",
            "bootloader": "S906NKSS7FYG8",
            "incremental": "S906NKSS7FYG8",
            "boot_completed": "1",
            "bootanim": "stopped",
            "verified_boot_state": "orange",
            "root": "uid=0(root)",
            "boot_sha256": module.EXPECTED_MAGISK_BOOT_SHA256,
            "dtbo_sha256": module.EXPECTED_DTBO_SHA256,
            "recovery_sha256": module.EXPECTED_RECOVERY_SHA256,
            "vendor_boot_sha256": module.EXPECTED_VENDOR_BOOT_SHA256,
        }
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            with mock.patch.object(
                module.odin_core,
                "wait_for_no_live_endpoint",
                side_effect=[absence, final_absence],
            ), mock.patch.object(
                module.odin_core,
                "list_snapshot_receipts",
                side_effect=[[snapshot0], [snapshot0, snapshot1]],
            ), mock.patch.object(
                module.odin_core, "create_phase_receipt"
            ), mock.patch.object(
                module, "collect_odin_evidence", return_value={"clean": True}
            ), mock.patch.object(
                module,
                "current_android_exact",
                side_effect=[("serial", android), ("serial", android)],
            ), mock.patch.object(
                module,
                "remote_text",
                side_effect=[
                    "12345678-1234-1234-1234-123456789abc",
                    (
                        f"osrelease={module.transport.EXPECTED_RELEASE}\n"
                        "sec_log_buf 1 0 - Live 0x0\nbind_ok=1\n"
                        "/proc/ap_klog:10:400\n/proc/last_kmsg:10:400"
                    ),
                    "12345678-1234-1234-1234-123456789abc",
                ],
            ), mock.patch.object(
                module,
                "pstore_console_absent",
                return_value={path: True for path in module.PSTORE_PATHS},
            ), mock.patch.object(
                module, "capture_observers", return_value={"ap_klog": {}, "last_kmsg": {}}
            ):
                baseline = module.connected_preflight(
                    run_dir,
                    run_dir,
                    Path("/odin"),
                    odin_absence_wait_sec=1.0,
                    lease=object(),
                )
            self.assertTrue(baseline["no_odin_endpoint"])
            self.assertFalse(baseline["device_writes"])
            self.assertEqual(baseline["odin_evidence"], {"clean": True})

    def test_connected_preflight_rejects_stale_only_initial_snapshot(self):
        module = self.module
        absence = module.odin_core.AbsenceResult(
            absent=True, next_sequence=1, timed_out=False
        )
        stale = {
            "sequence": 0,
            "live_devices": [],
            "live_device_identities": [],
            "stale_devices": ["/dev/bus/usb/002/007"],
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with mock.patch.object(
                module.odin_core, "wait_for_no_live_endpoint", return_value=absence
            ), mock.patch.object(
                module.odin_core, "list_snapshot_receipts", return_value=[stale]
            ), mock.patch.object(module, "current_android_exact") as android:
                with self.assertRaises(module.GateError):
                    module.connected_preflight(
                        root,
                        root,
                        Path("/odin"),
                        odin_absence_wait_sec=1.0,
                        lease=object(),
                    )
                android.assert_not_called()

    def test_validate_connected_result_rejects_write_or_missing_observer(self):
        module = self.module
        result = {
            "schema": module.SCHEMA,
            "mode": "connected-read-only-dry-run",
            "target": module.TARGET,
            "artifacts": {},
            "baseline": {},
            "device_contact": True,
            "device_writes": True,
            "reboot": False,
            "download_transition": False,
            "odin_transfer": False,
            "flash": False,
            "verdict": module.VERDICT,
        }
        with self.assertRaises(module.GateError):
            module.validate_connected_result(result, {})

    def test_result_rejects_invalid_nested_observer_receipt(self):
        module = self.module
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir, result, clause = self.build_evidence_fixture(root)
            result["baseline"]["observers"]["last_kmsg"]["reads"][0].update(
                {
                    "path": "/outside/run.bin",
                    "returncode": 99,
                    "stderr_bytes": 4,
                    "read_to_eof": False,
                }
            )
            with mock.patch.object(
                module, "helper_sha256", return_value="a" * 64
            ), mock.patch.object(
                module, "test_sha256", return_value="b" * 64
            ), mock.patch.object(module, "policy_clause", return_value=clause):
                with self.assertRaises(module.GateError):
                    module.validate_connected_result(
                        result,
                        {},
                        root=root,
                        result_path=run_dir / "result.json",
                    )

    def test_result_reopens_raw_timeline_and_odin_evidence(self):
        module = self.module
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir, result, clause = self.build_evidence_fixture(root)
            result_path = run_dir / "result.json"
            patches = (
                mock.patch.object(module, "helper_sha256", return_value="a" * 64),
                mock.patch.object(module, "test_sha256", return_value="b" * 64),
                mock.patch.object(module, "policy_clause", return_value=clause),
            )
            with patches[0], patches[1], patches[2]:
                reopened = module.validate_connected_result(
                    result, {}, root=root, result_path=result_path
                )
                self.assertIn(run_dir / "timeline.json", reopened)
                self.assertIn(
                    run_dir / "receipts/phase-prepared.json",
                    reopened,
                )
                self.assertIn(run_dir / "transaction.jsonl", reopened)
                raw = run_dir / "baseline_last_kmsg_2.bin"
                raw.write_bytes(raw.read_bytes() + b"tamper")
                with self.assertRaises(module.GateError):
                    module.validate_connected_result(
                        result, {}, root=root, result_path=result_path
                    )

    def test_collect_odin_evidence_rejects_schema_valid_wrong_phase_payload(self):
        module = self.module
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir, result, _clause = self.build_evidence_fixture(root)
            phase = run_dir / "receipts/phase-prepared.json"
            value = json.loads(phase.read_text(encoding="utf-8"))
            value["payload"]["boot_id"] = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
            phase.chmod(0o600)
            phase.write_text(
                json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n",
                encoding="utf-8",
            )
            phase.chmod(0o400)
            with self.assertRaises(module.GateError):
                module.collect_odin_evidence(
                    root,
                    run_dir,
                    expected_phase_payload=module.expected_phase_payload(
                        result["baseline"]
                    ),
                )

    def test_result_rejects_timeline_tamper(self):
        module = self.module
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir, result, clause = self.build_evidence_fixture(root)
            timeline = run_dir / "timeline.json"
            timeline.write_text('{"events": []}\n', encoding="ascii")
            with mock.patch.object(
                module, "helper_sha256", return_value="a" * 64
            ), mock.patch.object(
                module, "test_sha256", return_value="b" * 64
            ), mock.patch.object(module, "policy_clause", return_value=clause):
                with self.assertRaises(module.GateError):
                    module.validate_connected_result(
                        result,
                        {},
                        root=root,
                        result_path=run_dir / "result.json",
                    )

    def test_connected_pass_reopens_complete_evidence(self):
        module = self.module
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir, result, clause = self.build_evidence_fixture(root)
            result_path = run_dir / "result.json"
            module.core.durable_write_json(result_path, result)
            result_identity = module.core.hash_stable_file(result_path)
            pass_record = {
                "schema": module.PASS_SCHEMA,
                "target": module.TARGET,
                "created_at_utc": "2026-07-20T00:00:00.000000Z",
                "helper_sha256": "a" * 64,
                "test_sha256": "b" * 64,
                "live_core_sha256": module.EXPECTED_LIVE_CORE_SHA256,
                "odin_core_sha256": module.EXPECTED_ODIN_CORE_SHA256,
                "policy_draft_sha256": module.core.sha256_file(
                    root / module.POLICY_DRAFT
                ),
                "policy_clause_sha256": module.core.sha256_bytes(
                    clause.encode("utf-8")
                ),
                "result_path": str(result_path.relative_to(root)),
                "result_size": result_identity["size"],
                "result_sha256": result_identity["sha256"],
                "verdict": module.VERDICT,
                "device_writes": False,
            }
            module.core.durable_create_json(root / module.PASS_STATE, pass_record)
            with mock.patch.object(
                module, "helper_sha256", return_value="a" * 64
            ), mock.patch.object(
                module, "test_sha256", return_value="b" * 64
            ), mock.patch.object(module, "policy_clause", return_value=clause):
                self.assertEqual(
                    module.validate_connected_pass(root, expected_artifacts={}),
                    pass_record,
                )
                receipt = run_dir / "receipts/odin-snapshot-000001.json"
                receipt.chmod(0o600)
                receipt.write_text("{}\n", encoding="ascii")
                receipt.chmod(0o400)
                with self.assertRaises(
                    (module.GateError, module.odin_core.OdinTransitionError)
                ):
                    module.validate_connected_pass(root, expected_artifacts={})

    def test_connected_pass_rejects_symlinked_result_path(self):
        module = self.module
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir, result, clause = self.build_evidence_fixture(root)
            other_dir = root / module.RUN_ROOT / "other-run"
            other_dir.mkdir()
            actual_result = other_dir / "result.json"
            module.core.durable_write_json(actual_result, result)
            claimed_result = run_dir / "result.json"
            claimed_result.symlink_to(actual_result)
            identity = module.core.hash_stable_file(actual_result)
            pass_record = {
                "schema": module.PASS_SCHEMA,
                "target": module.TARGET,
                "created_at_utc": "2026-07-20T00:00:00.000000Z",
                "helper_sha256": "a" * 64,
                "test_sha256": "b" * 64,
                "live_core_sha256": module.EXPECTED_LIVE_CORE_SHA256,
                "odin_core_sha256": module.EXPECTED_ODIN_CORE_SHA256,
                "policy_draft_sha256": module.core.sha256_file(
                    root / module.POLICY_DRAFT
                ),
                "policy_clause_sha256": module.core.sha256_bytes(
                    clause.encode("utf-8")
                ),
                "result_path": str(claimed_result.relative_to(root)),
                "result_size": identity["size"],
                "result_sha256": identity["sha256"],
                "verdict": module.VERDICT,
                "device_writes": False,
            }
            module.core.durable_create_json(root / module.PASS_STATE, pass_record)
            with mock.patch.object(
                module, "helper_sha256", return_value="a" * 64
            ), mock.patch.object(
                module, "test_sha256", return_value="b" * 64
            ), mock.patch.object(module, "policy_clause", return_value=clause):
                with self.assertRaises(module.GateError):
                    module.validate_connected_pass(root, expected_artifacts={})

    def test_connected_pass_rejects_symlinked_parent_run_directory(self):
        module = self.module
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            actual_run, result, clause = self.build_evidence_fixture(root)
            actual_result = actual_run / "result.json"
            module.core.durable_write_json(actual_result, result)
            claimed_run = root / module.RUN_ROOT / "claimed-run"
            claimed_run.symlink_to(actual_run, target_is_directory=True)
            claimed_result = claimed_run / "result.json"
            identity = module.core.hash_stable_file(actual_result)
            pass_record = {
                "schema": module.PASS_SCHEMA,
                "target": module.TARGET,
                "created_at_utc": "2026-07-20T00:00:00.000000Z",
                "helper_sha256": "a" * 64,
                "test_sha256": "b" * 64,
                "live_core_sha256": module.EXPECTED_LIVE_CORE_SHA256,
                "odin_core_sha256": module.EXPECTED_ODIN_CORE_SHA256,
                "policy_draft_sha256": module.core.sha256_file(
                    root / module.POLICY_DRAFT
                ),
                "policy_clause_sha256": module.core.sha256_bytes(
                    clause.encode("utf-8")
                ),
                "result_path": str(claimed_result.relative_to(root)),
                "result_size": identity["size"],
                "result_sha256": identity["sha256"],
                "verdict": module.VERDICT,
                "device_writes": False,
            }
            module.core.durable_create_json(root / module.PASS_STATE, pass_record)
            with mock.patch.object(
                module, "helper_sha256", return_value="a" * 64
            ), mock.patch.object(
                module, "test_sha256", return_value="b" * 64
            ), mock.patch.object(module, "policy_clause", return_value=clause):
                with self.assertRaises(module.GateError):
                    module.validate_connected_pass(root, expected_artifacts={})

    def test_connected_pass_rejects_symlinked_parent_state_directory(self):
        module = self.module
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir, result, clause = self.build_evidence_fixture(root)
            result_path = run_dir / "result.json"
            module.core.durable_write_json(result_path, result)
            identity = module.core.hash_stable_file(result_path)
            actual_state = root / "redirected-state"
            actual_state.mkdir()
            state_parent = (root / module.PASS_STATE).parent
            state_parent.symlink_to(actual_state, target_is_directory=True)
            pass_record = {
                "schema": module.PASS_SCHEMA,
                "target": module.TARGET,
                "created_at_utc": "2026-07-20T00:00:00.000000Z",
                "helper_sha256": "a" * 64,
                "test_sha256": "b" * 64,
                "live_core_sha256": module.EXPECTED_LIVE_CORE_SHA256,
                "odin_core_sha256": module.EXPECTED_ODIN_CORE_SHA256,
                "policy_draft_sha256": module.core.sha256_file(
                    root / module.POLICY_DRAFT
                ),
                "policy_clause_sha256": module.core.sha256_bytes(
                    clause.encode("utf-8")
                ),
                "result_path": str(result_path.relative_to(root)),
                "result_size": identity["size"],
                "result_sha256": identity["sha256"],
                "verdict": module.VERDICT,
                "device_writes": False,
            }
            module.core.durable_create_json(root / module.PASS_STATE, pass_record)
            with mock.patch.object(
                module, "helper_sha256", return_value="a" * 64
            ), mock.patch.object(
                module, "test_sha256", return_value="b" * 64
            ), mock.patch.object(module, "policy_clause", return_value=clause):
                with self.assertRaises(module.GateError):
                    module.validate_connected_pass(root, expected_artifacts={})

    def test_connected_wrapper_holds_transaction_lease_through_locked_close(self):
        module = self.module
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args = module.build_parser().parse_args(
                ["--connected-read-only-dry-run", "--ack", module.ACK_TOKEN]
            )
            policy = {"active": True, "policy_clause_sha256": "c" * 64}
            active = {"value": False}

            @contextmanager
            def session(_run_dir):
                active["value"] = True
                try:
                    yield object()
                finally:
                    active["value"] = False

            def locked(*_args):
                self.assertTrue(active["value"])
                return 0

            run_dir = root / module.RUN_ROOT / "lease-fixture"
            run_dir.mkdir(parents=True)
            (root / module.PASS_STATE).parent.mkdir(parents=True)
            with mock.patch.object(
                module, "verify_policy_draft", return_value=policy
            ), mock.patch.object(
                module, "policy_active", return_value=True
            ), mock.patch.object(
                module.core, "allocate_run_dir", return_value=run_dir
            ), mock.patch.object(
                module.odin_core, "transaction_session", side_effect=session
            ), mock.patch.object(
                module, "_connected_dry_run_locked", side_effect=locked
            ):
                self.assertEqual(module.connected_dry_run(root, args, {}, policy), 0)
            self.assertFalse(active["value"])
    def test_pass_state_creation_is_exclusive(self):
        module = self.module
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / module.PASS_STATE
            module.core.durable_create_json(path, {"schema": module.PASS_SCHEMA})
            with self.assertRaises(module.core.LiveCoreError):
                module.core.durable_create_json(path, {"schema": module.PASS_SCHEMA})
            self.assertEqual(json.loads(path.read_text())["schema"], module.PASS_SCHEMA)


if __name__ == "__main__":
    unittest.main()
