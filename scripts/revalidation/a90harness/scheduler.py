"""Mixed-soak scheduler primitives for A90 host-side validation."""

from __future__ import annotations

import random
import threading
import time
from dataclasses import asdict, dataclass
from typing import Any

from a90harness.device import DeviceClient
from a90harness.evidence import EvidenceStore
from a90harness.gate import GateOptions, evaluate_gate
from a90harness.module import TestModule
from a90harness.observer import ObserverSummary, run_observer
from a90harness.runner import ModuleRunner


@dataclass
class ScheduleEntry:
    seq: int
    phase: str
    workload: str
    profile: str
    start_sec: float
    end_sec: float
    resource_locks: list[str]
    seed: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class WorkloadEvent:
    type: str
    seq: int
    phase: str
    workload: str
    status: str
    ok: bool
    skipped: bool
    scheduled_start_sec: float
    scheduled_end_sec: float
    actual_start_sec: float
    actual_end_sec: float
    resource_locks: list[str]
    detail: str
    gate: dict[str, Any]
    module: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MixedSoakResult:
    ok: bool
    seed: int
    profile: str
    duration_sec: float
    workload_count: int
    pass_count: int
    skip_count: int
    blocked_count: int
    fail_count: int
    observer: ObserverSummary | None
    schedule_path: str
    events_path: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["observer"] = self.observer.to_dict() if self.observer is not None else None
        return payload


def locks_for_module(module: TestModule) -> list[str]:
    locks = ["serial"]
    if module.requires_ncm:
        locks.append("ncm")
    if module.requires_usb_rebind:
        locks.append("usb")
    if module.name == "storage-io":
        locks.append("storage")
    return locks


def default_workloads(profile: str, modules: dict[str, type[TestModule]]) -> list[str]:
    preferred = ["cpu-mem-thermal", "ncm-tcp-preflight", "storage-io"]
    if profile in {"idle", "observer-only"}:
        return []
    return [name for name in preferred if name in modules]


def build_schedule(
    *,
    modules: dict[str, type[TestModule]],
    workloads: list[str],
    profile: str,
    duration_sec: float,
    seed: int,
) -> list[ScheduleEntry]:
    if duration_sec <= 0:
        raise ValueError("duration_sec must be positive")

    selected = workloads or default_workloads(profile, modules)
    for name in selected:
        if name not in modules:
            raise ValueError(f"unknown workload: {name}")

    if not selected:
        return []

    rng = random.Random(seed)
    ordered = selected[:]
    rng.shuffle(ordered)
    spacing = max(1.0, duration_sec / max(len(ordered), 1))
    schedule: list[ScheduleEntry] = []
    for index, name in enumerate(ordered):
        module = modules[name]()
        start_sec = min(duration_sec, index * spacing)
        end_sec = min(duration_sec, start_sec + spacing)
        schedule.append(
            ScheduleEntry(
                seq=index,
                phase="main",
                workload=name,
                profile=profile,
                start_sec=round(start_sec, 3),
                end_sec=round(end_sec, 3),
                resource_locks=locks_for_module(module),
                seed=seed,
            )
        )
    return schedule


def schedule_document(schedule: list[ScheduleEntry],
                      *,
                      seed: int,
                      profile: str,
                      duration_sec: float,
                      observer_interval_sec: float) -> dict[str, Any]:
    return {
        "schema": "a90-mixed-soak-schedule-v179",
        "seed": seed,
        "profile": profile,
        "duration_sec": duration_sec,
        "observer_interval_sec": observer_interval_sec,
        "workload_count": len(schedule),
        "schedule": [entry.to_dict() for entry in schedule],
    }


def run_mixed_soak_schedule(
    *,
    repo_root: Any,
    store: EvidenceStore,
    client: DeviceClient,
    modules: dict[str, type[TestModule]],
    schedule: list[ScheduleEntry],
    gate_options: GateOptions,
    expect_version: str,
    host: str,
    port: int,
    timeout: float,
    duration_sec: float,
    observer_interval_sec: float,
    workload_profile: str,
) -> MixedSoakResult:
    started = time.monotonic()
    observer_summary: ObserverSummary | None = None
    observer_error: list[BaseException] = []

    def observer_worker() -> None:
        nonlocal observer_summary
        try:
            observer_summary = run_observer(
                client,
                store,
                duration_sec=duration_sec,
                interval_sec=observer_interval_sec,
            )
        except BaseException as exc:  # noqa: BLE001 - preserve thread failure in final result
            observer_error.append(exc)

    observer_thread = threading.Thread(target=observer_worker, name="a90-mixed-soak-observer")
    observer_thread.start()

    runner = ModuleRunner(
        repo_root=repo_root,
        store=store,
        client=client,
        expect_version=expect_version,
        host=host,
        port=port,
        timeout=timeout,
    )

    events: list[WorkloadEvent] = []
    for entry in schedule:
        target = started + entry.start_sec
        now = time.monotonic()
        if target > now:
            time.sleep(target - now)

        event_start = time.monotonic()
        module = modules[entry.workload]()
        gate = evaluate_gate(module, gate_options)
        if not gate.allowed:
            event = WorkloadEvent(
                type="workload_event",
                seq=entry.seq,
                phase=entry.phase,
                workload=entry.workload,
                status="blocked",
                ok=True,
                skipped=True,
                scheduled_start_sec=entry.start_sec,
                scheduled_end_sec=entry.end_sec,
                actual_start_sec=event_start - started,
                actual_end_sec=time.monotonic() - started,
                resource_locks=entry.resource_locks,
                detail="; ".join(gate.reasons),
                gate=gate.to_dict(),
                module=None,
            )
        else:
            outcome, _ = runner.run(
                module,
                profile=workload_profile,
                observer_duration_sec=0.0,
                observer_interval_sec=observer_interval_sec,
            )
            skipped = outcome.skipped
            event = WorkloadEvent(
                type="workload_event",
                seq=entry.seq,
                phase=entry.phase,
                workload=entry.workload,
                status="pass" if outcome.ok else "fail",
                ok=outcome.ok,
                skipped=skipped,
                scheduled_start_sec=entry.start_sec,
                scheduled_end_sec=entry.end_sec,
                actual_start_sec=event_start - started,
                actual_end_sec=time.monotonic() - started,
                resource_locks=entry.resource_locks,
                detail=", ".join(f"{step.name}={step.ok}" for step in outcome.steps),
                gate=gate.to_dict(),
                module=outcome.to_dict(),
            )
        store.append_jsonl("workload-events.jsonl", event.to_dict())
        events.append(event)

    observer_thread.join()
    if observer_error:
        store.write_text("observer-thread-error.txt", f"{type(observer_error[0]).__name__}: {observer_error[0]}\n")

    pass_count = sum(1 for event in events if event.status == "pass")
    skip_count = sum(1 for event in events if event.skipped)
    blocked_count = sum(1 for event in events if event.status == "blocked")
    fail_count = sum(1 for event in events if not event.ok)
    ok = fail_count == 0 and not observer_error and (observer_summary is None or observer_summary.ok)
    result = MixedSoakResult(
        ok=ok,
        seed=schedule[0].seed if schedule else 0,
        profile=workload_profile,
        duration_sec=time.monotonic() - started,
        workload_count=len(events),
        pass_count=pass_count,
        skip_count=skip_count,
        blocked_count=blocked_count,
        fail_count=fail_count,
        observer=observer_summary,
        schedule_path=str(store.path("schedule.json")),
        events_path=str(store.path("workload-events.jsonl")),
    )
    store.write_json("mixed-soak-result.json", result.to_dict())
    return result
