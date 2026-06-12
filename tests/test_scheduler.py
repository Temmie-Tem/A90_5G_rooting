"""Regression tests for a90harness.scheduler mixed-soak primitives."""

from __future__ import annotations

import sys
import tempfile
import types
import unittest
from contextlib import contextmanager
from pathlib import Path

from _loader import load_harness

broker_stub = types.ModuleType("a90_broker")
broker_stub.PROTO = "A90B1"
broker_stub.connect_and_call = lambda *_args, **_kwargs: {}
sys.modules.setdefault("a90_broker", broker_stub)

scheduler = load_harness("scheduler")
module_contract = load_harness("module")
gate_contract = load_harness("gate")
observer_contract = load_harness("observer")


class PlainModule(module_contract.TestModule):
    name = "plain"


class NcmUsbExternalModule(module_contract.TestModule):
    name = "external"
    requires_ncm = True
    requires_usb_rebind = True
    external_bridge_client = True


class StorageModule(module_contract.TestModule):
    name = "storage-io"


class CpuMemoryProfiles(module_contract.TestModule):
    name = "cpu-memory-profiles"


class CpuMemThermal(module_contract.TestModule):
    name = "cpu-mem-thermal"


class NcmTcpPreflight(module_contract.TestModule):
    name = "ncm-tcp-preflight"


class FakeStore:
    def __init__(self, run_dir: Path):
        self.run_dir = run_dir
        self.jsonl_writes: list[tuple[str, dict]] = []
        self.json_writes: list[tuple[str, dict]] = []
        self.text_writes: list[tuple[str, str]] = []

    def path(self, name: str) -> Path:
        return self.run_dir / name

    def append_jsonl(self, name: str, payload: dict) -> None:
        self.jsonl_writes.append((name, payload))

    def write_json(self, name: str, payload: dict) -> None:
        self.json_writes.append((name, payload))

    def write_text(self, name: str, text: str) -> None:
        self.text_writes.append((name, text))


class FakeClient:
    def __init__(self):
        self.exclusive_entries = 0

    @contextmanager
    def exclusive(self):
        self.exclusive_entries += 1
        yield


class FakeRunner:
    calls: list[tuple[str, str, float, float]] = []
    outcomes: list[module_contract.ModuleOutcome] = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def run(self, module, *, profile, observer_duration_sec, observer_interval_sec):
        self.calls.append((module.name, profile, observer_duration_sec, observer_interval_sec))
        if self.outcomes:
            return self.outcomes.pop(0), None
        outcome = module_contract.ModuleOutcome(
            name=module.name,
            ok=True,
            skipped=False,
            steps=[module_contract.StepResult("run", True, "ok", 0.1)],
            artifacts=[],
            metadata={"module": module.name},
        )
        return outcome, None


class SchedulerTests(unittest.TestCase):
    def test_locks_for_module_combines_serial_resource_flags_and_storage_special_case(self):
        self.assertEqual(scheduler.locks_for_module(PlainModule()), ["serial"])
        self.assertEqual(
            scheduler.locks_for_module(NcmUsbExternalModule()),
            ["serial", "ncm", "usb", "external-bridge"],
        )
        self.assertEqual(scheduler.locks_for_module(StorageModule()), ["serial", "storage"])

    def test_default_workloads_respects_profile_and_cpu_fallback(self):
        modules = {
            "cpu-memory-profiles": CpuMemoryProfiles,
            "ncm-tcp-preflight": NcmTcpPreflight,
            "storage-io": StorageModule,
        }
        self.assertEqual(
            scheduler.default_workloads("smoke", modules),
            ["cpu-memory-profiles", "ncm-tcp-preflight", "storage-io"],
        )
        self.assertEqual(scheduler.default_workloads("idle", modules), [])

        fallback_modules = {
            "cpu-mem-thermal": CpuMemThermal,
            "storage-io": StorageModule,
        }
        self.assertEqual(
            scheduler.default_workloads("full", fallback_modules),
            ["cpu-mem-thermal", "storage-io"],
        )

    def test_build_schedule_validates_inputs_and_produces_seeded_entries(self):
        modules = {"plain": PlainModule, "storage-io": StorageModule, "external": NcmUsbExternalModule}

        with self.assertRaisesRegex(ValueError, "duration_sec must be positive"):
            scheduler.build_schedule(modules=modules, workloads=["plain"], profile="smoke", duration_sec=0, seed=1)
        with self.assertRaisesRegex(ValueError, "unknown workload"):
            scheduler.build_schedule(modules=modules, workloads=["missing"], profile="smoke", duration_sec=10, seed=1)

        schedule = scheduler.build_schedule(
            modules=modules,
            workloads=["plain", "storage-io", "external"],
            profile="smoke",
            duration_sec=9.0,
            seed=1234,
        )

        self.assertEqual([entry.seq for entry in schedule], [0, 1, 2])
        self.assertEqual([entry.phase for entry in schedule], ["main", "main", "main"])
        self.assertEqual([entry.start_sec for entry in schedule], [0.0, 3.0, 6.0])
        self.assertEqual([entry.end_sec for entry in schedule], [3.0, 6.0, 9.0])
        self.assertEqual({entry.seed for entry in schedule}, {1234})
        self.assertEqual({entry.profile for entry in schedule}, {"smoke"})
        self.assertEqual(
            {entry.workload: entry.resource_locks for entry in schedule},
            {
                "plain": ["serial"],
                "storage-io": ["serial", "storage"],
                "external": ["serial", "ncm", "usb", "external-bridge"],
            },
        )

    def test_build_schedule_uses_default_workloads_and_allows_observer_only_empty(self):
        modules = {"cpu-memory-profiles": CpuMemoryProfiles, "storage-io": StorageModule}
        schedule = scheduler.build_schedule(modules=modules, workloads=[], profile="smoke", duration_sec=5, seed=4)
        self.assertEqual({entry.workload for entry in schedule}, {"cpu-memory-profiles", "storage-io"})
        self.assertEqual(
            scheduler.build_schedule(modules=modules, workloads=[], profile="observer-only", duration_sec=5, seed=4),
            [],
        )

    def test_schedule_document_serializes_schema_and_entries(self):
        entry = scheduler.ScheduleEntry(
            seq=0,
            phase="main",
            workload="plain",
            profile="smoke",
            start_sec=0.0,
            end_sec=1.0,
            resource_locks=["serial"],
            seed=9,
        )

        document = scheduler.schedule_document(
            [entry],
            seed=9,
            profile="smoke",
            duration_sec=1.0,
            observer_interval_sec=0.25,
        )

        self.assertEqual(document["schema"], "a90-mixed-soak-schedule-v179")
        self.assertEqual(document["workload_count"], 1)
        self.assertEqual(document["schedule"], [entry.to_dict()])

    def test_workload_event_and_mixed_soak_result_to_dict(self):
        event = scheduler.WorkloadEvent(
            type="workload_event",
            seq=1,
            phase="main",
            workload="plain",
            status="pass",
            ok=True,
            skipped=False,
            scheduled_start_sec=0.0,
            scheduled_end_sec=1.0,
            actual_start_sec=0.1,
            actual_end_sec=0.2,
            resource_locks=["serial"],
            detail="run=True",
            gate={"allowed": True},
            module={"name": "plain"},
        )
        self.assertEqual(event.to_dict()["workload"], "plain")

        observer = observer_contract.ObserverSummary(
            ok=True,
            cycles=2,
            samples=3,
            failures=0,
            duration_sec=0.5,
            jsonl="observer.jsonl",
        )
        result = scheduler.MixedSoakResult(
            ok=True,
            seed=7,
            profile="smoke",
            duration_sec=1.0,
            workload_count=1,
            pass_count=1,
            skip_count=0,
            blocked_count=0,
            fail_count=0,
            observer=observer,
            schedule_path="schedule.json",
            events_path="events.jsonl",
            classification_path="classification.json",
            classification_summary={"count": 0},
            interrupted=False,
            stop_reason="complete",
        )
        payload = result.to_dict()
        self.assertEqual(payload["observer"], observer.to_dict())
        self.assertEqual(payload["stop_reason"], "complete")

    def test_run_mixed_soak_schedule_records_allowed_workload_and_observer_summary(self):
        original_runner = scheduler.ModuleRunner
        original_observer = scheduler.run_observer
        original_classify = scheduler.classify_mixed_soak
        original_load_samples = scheduler.load_observer_samples
        FakeRunner.calls = []
        FakeRunner.outcomes = [
            module_contract.ModuleOutcome(
                name="plain",
                ok=True,
                skipped=False,
                steps=[module_contract.StepResult("run", True, "ok", 0.1)],
                artifacts=["artifact.txt"],
                metadata={"m": "plain"},
            )
        ]

        def fake_observer(client, store, *, duration_sec, interval_sec, stop_event):
            self.assertFalse(stop_event.is_set())
            return observer_contract.ObserverSummary(True, 1, 1, 0, 0.01, "observer.jsonl")

        try:
            scheduler.ModuleRunner = FakeRunner
            scheduler.run_observer = fake_observer
            scheduler.load_observer_samples = lambda path: [{"sample": str(path)}]
            scheduler.classify_mixed_soak = lambda events, samples: {
                "classifications": [],
                "summary": {"count": 0, "events": len(events), "samples": len(samples)},
            }
            with tempfile.TemporaryDirectory() as tmp:
                store = FakeStore(Path(tmp))
                client = FakeClient()
                schedule = [
                    scheduler.ScheduleEntry(0, "main", "plain", "smoke", 0.0, 0.0, ["serial"], 77)
                ]

                result = scheduler.run_mixed_soak_schedule(
                    repo_root=Path("/repo"),
                    store=store,
                    client=client,
                    modules={"plain": PlainModule},
                    schedule=schedule,
                    gate_options=gate_contract.GateOptions(),
                    expect_version="A90 test",
                    host="127.0.0.1",
                    port=54321,
                    timeout=1.0,
                    duration_sec=0.001,
                    observer_interval_sec=0.1,
                    workload_profile="smoke",
                )
        finally:
            scheduler.ModuleRunner = original_runner
            scheduler.run_observer = original_observer
            scheduler.classify_mixed_soak = original_classify
            scheduler.load_observer_samples = original_load_samples

        self.assertTrue(result.ok)
        self.assertEqual(result.seed, 77)
        self.assertEqual(result.pass_count, 1)
        self.assertEqual(result.skip_count, 0)
        self.assertEqual(result.classification_summary, {"count": 0, "events": 1, "samples": 1})
        self.assertEqual(FakeRunner.calls, [("plain", "smoke", 0.0, 0.1)])
        self.assertEqual(store.jsonl_writes[0][0], "workload-events.jsonl")
        self.assertEqual(store.jsonl_writes[0][1]["status"], "pass")
        self.assertEqual(store.json_writes[-1][0], "mixed-soak-result.json")
        self.assertEqual(client.exclusive_entries, 0)

    def test_run_mixed_soak_schedule_blocks_disallowed_workload_without_runner(self):
        original_runner = scheduler.ModuleRunner
        original_observer = scheduler.run_observer
        original_gate = scheduler.evaluate_gate
        original_classify = scheduler.classify_mixed_soak
        original_load_samples = scheduler.load_observer_samples
        FakeRunner.calls = []

        try:
            scheduler.ModuleRunner = FakeRunner
            scheduler.run_observer = lambda *args, **kwargs: observer_contract.ObserverSummary(
                True, 1, 1, 0, 0.01, "observer.jsonl"
            )
            scheduler.evaluate_gate = lambda module, options: gate_contract.GateResult(
                allowed=False,
                reasons=["requires flag"],
                required_flags=["--flag"],
                metadata={"name": module.name},
            )
            scheduler.load_observer_samples = lambda path: []
            scheduler.classify_mixed_soak = lambda events, samples: {
                "classifications": [],
                "summary": {"count": 0},
            }
            with tempfile.TemporaryDirectory() as tmp:
                store = FakeStore(Path(tmp))
                schedule = [
                    scheduler.ScheduleEntry(0, "main", "plain", "smoke", 0.0, 0.0, ["serial"], 55)
                ]
                result = scheduler.run_mixed_soak_schedule(
                    repo_root=Path("/repo"),
                    store=store,
                    client=FakeClient(),
                    modules={"plain": PlainModule},
                    schedule=schedule,
                    gate_options=gate_contract.GateOptions(),
                    expect_version="A90 test",
                    host="127.0.0.1",
                    port=54321,
                    timeout=1.0,
                    duration_sec=0.001,
                    observer_interval_sec=0.1,
                    workload_profile="smoke",
                )
        finally:
            scheduler.ModuleRunner = original_runner
            scheduler.run_observer = original_observer
            scheduler.evaluate_gate = original_gate
            scheduler.classify_mixed_soak = original_classify
            scheduler.load_observer_samples = original_load_samples

        self.assertTrue(result.ok)
        self.assertEqual(result.blocked_count, 1)
        self.assertEqual(result.skip_count, 1)
        self.assertEqual(FakeRunner.calls, [])
        event = store.jsonl_writes[0][1]
        self.assertEqual(event["status"], "blocked")
        self.assertEqual(event["detail"], "requires flag")
        self.assertIsNone(event["module"])

    def test_run_mixed_soak_schedule_uses_client_exclusive_for_external_bridge_modules(self):
        original_runner = scheduler.ModuleRunner
        original_observer = scheduler.run_observer
        original_classify = scheduler.classify_mixed_soak
        original_load_samples = scheduler.load_observer_samples
        FakeRunner.calls = []
        FakeRunner.outcomes = []

        try:
            scheduler.ModuleRunner = FakeRunner
            scheduler.run_observer = lambda *args, **kwargs: observer_contract.ObserverSummary(
                True, 1, 1, 0, 0.01, "observer.jsonl"
            )
            scheduler.load_observer_samples = lambda path: []
            scheduler.classify_mixed_soak = lambda events, samples: {
                "classifications": [],
                "summary": {"count": 0},
            }
            with tempfile.TemporaryDirectory() as tmp:
                store = FakeStore(Path(tmp))
                client = FakeClient()
                schedule = [
                    scheduler.ScheduleEntry(0, "main", "external", "smoke", 0.0, 0.0, ["serial"], 9)
                ]
                result = scheduler.run_mixed_soak_schedule(
                    repo_root=Path("/repo"),
                    store=store,
                    client=client,
                    modules={"external": NcmUsbExternalModule},
                    schedule=schedule,
                    gate_options=gate_contract.GateOptions(allow_ncm=True, allow_usb_rebind=True),
                    expect_version="A90 test",
                    host="127.0.0.1",
                    port=54321,
                    timeout=1.0,
                    duration_sec=0.001,
                    observer_interval_sec=0.1,
                    workload_profile="smoke",
                )
        finally:
            scheduler.ModuleRunner = original_runner
            scheduler.run_observer = original_observer
            scheduler.classify_mixed_soak = original_classify
            scheduler.load_observer_samples = original_load_samples

        self.assertTrue(result.ok)
        self.assertEqual(client.exclusive_entries, 1)
        self.assertEqual(FakeRunner.calls, [("external", "smoke", 0.0, 0.1)])


if __name__ == "__main__":
    unittest.main()
