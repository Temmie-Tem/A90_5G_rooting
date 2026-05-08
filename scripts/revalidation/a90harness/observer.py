"""Read-only observer for A90 native-init host-side validation."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from typing import Any

from a90harness.device import DeviceClient
from a90harness.evidence import EvidenceStore


DEFAULT_OBSERVER_COMMANDS: tuple[tuple[str, list[str], float], ...] = (
    ("version", ["version"], 20.0),
    ("status", ["status"], 20.0),
    ("selftest-verbose", ["selftest", "verbose"], 20.0),
    ("bootstatus", ["bootstatus"], 20.0),
    ("longsoak-status", ["longsoak", "status", "verbose"], 20.0),
    ("storage", ["storage"], 20.0),
    ("netservice-status", ["netservice", "status"], 20.0),
)


@dataclass
class ObserverSample:
    type: str
    seq: int
    cycle: int
    host_ts: float
    name: str
    command: list[str]
    ok: bool
    rc: int | None
    status: str
    duration_sec: float
    error: str
    text_excerpt: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ObserverSummary:
    ok: bool
    cycles: int
    samples: int
    failures: int
    duration_sec: float
    jsonl: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def text_excerpt(text: str, limit: int = 8192) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n[truncated]\n"


def observe_cycle(client: DeviceClient,
                  store: EvidenceStore,
                  cycle: int,
                  seq_start: int,
                  *,
                  jsonl_name: str = "observer.jsonl") -> list[ObserverSample]:
    samples: list[ObserverSample] = []
    seq = seq_start
    for name, command, timeout in DEFAULT_OBSERVER_COMMANDS:
        record, text = client.run(name, command, timeout=timeout)
        sample = ObserverSample(
            type="observer_sample",
            seq=seq,
            cycle=cycle,
            host_ts=time.time(),
            name=name,
            command=command,
            ok=record.ok,
            rc=record.rc,
            status=record.status,
            duration_sec=record.duration_sec,
            error=record.error,
            text_excerpt=text_excerpt(text),
        )
        samples.append(sample)
        store.append_jsonl(jsonl_name, sample.to_dict())
        seq += 1
    return samples


def run_observer(client: DeviceClient,
                 store: EvidenceStore,
                 *,
                 duration_sec: float,
                 interval_sec: float,
                 jsonl_name: str = "observer.jsonl") -> ObserverSummary:
    started = time.monotonic()
    deadline = started + duration_sec
    all_samples: list[ObserverSample] = []
    cycle = 0
    seq = 0

    while True:
        cycle += 1
        cycle_samples = observe_cycle(client, store, cycle, seq, jsonl_name=jsonl_name)
        all_samples.extend(cycle_samples)
        seq += len(cycle_samples)
        now = time.monotonic()
        if now >= deadline:
            break
        time.sleep(max(0.0, min(interval_sec, deadline - now)))

    failures = sum(1 for sample in all_samples if not sample.ok)
    summary = ObserverSummary(
        ok=failures == 0,
        cycles=cycle,
        samples=len(all_samples),
        failures=failures,
        duration_sec=time.monotonic() - started,
        jsonl=str(store.path(jsonl_name)),
    )
    store.write_json("observer-summary.json", summary.to_dict())
    return summary

