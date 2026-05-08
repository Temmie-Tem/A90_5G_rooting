# F043. Unlimited observer retains samples until memory exhaustion

## Metadata

| field | value |
|---|---|
| finding_id | `3c3afb170d488191be694bee3b3010f1` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/3c3afb170d488191be694bee3b3010f1 |
| severity | `low` |
| status | `new` |
| detected_at | `2026-05-08T18:17:34.463425Z` |
| committed_at | `2026-05-09 03:02:34 +0900` |
| commit_hash | `c7e28272c3325613f01457aa27ec33445a7cd11f` |
| relevant_paths | `scripts/revalidation/native_test_supervisor.py` <br> `scripts/revalidation/a90harness/observer.py` |
| source_csv | `docs/security/codex-security-findings-2026-05-08T18-39-05.112Z.csv` |

## CSV Description

This commit adds `--duration-sec unlimited`, represented as `duration_sec=None`, and makes `--max-cycles` optional. In that mode `run_observer()` sets no deadline and continues until `max_cycles` is reached or the user interrupts it. However, each cycle appends all collected samples to `all_samples` even though samples are already streamed to `observer.jsonl`. For a real long-running or unlimited observation, memory usage grows without bound and can eventually crash the host-side supervisor or degrade the operator workstation. The repeated failure counting over `all_samples` also becomes increasingly expensive. This is a reliability/availability bug rather than a direct security boundary bypass in the stated lab threat model.

## Local Initial Assessment

- Valid reliability finding for unattended long-run mode.
- Directly affects v178-v184 because 8h/24h/unlimited observation must not grow host memory linearly.
- Not a root compromise, but it can invalidate long-run evidence by crashing the host supervisor.

## Local Remediation

- Planned Batch B fix.
- Keep `observer.jsonl` as the full record and replace in-memory `all_samples` with streaming counters.
- Track only counts and a bounded recent failure excerpt list in memory.

## Codex Cloud Detail

Unlimited observer retains samples until memory exhaustion
Link: https://chatgpt.com/codex/cloud/security/findings/3c3afb170d488191be694bee3b3010f1?sev=&repo=https%3A%2F%2Fgithub.com%2FTemmie-Tem%2FA90_5G_rooting
Criticality: low
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: c7e2827
Author: shs02140@gmail.com
Created: 2026. 5. 9. 오전 3:17:34
Assignee: Unassigned
Signals: 없음

# Summary
Introduced: v176 makes unbounded observation an explicit supported mode without changing the observer accounting from full sample retention to bounded counters or requiring a positive `--max-cycles` for unlimited runs.
This commit adds `--duration-sec unlimited`, represented as `duration_sec=None`, and makes `--max-cycles` optional. In that mode `run_observer()` sets no deadline and continues until `max_cycles` is reached or the user interrupts it. However, each cycle appends all collected samples to `all_samples` even though samples are already streamed to `observer.jsonl`. For a real long-running or unlimited observation, memory usage grows without bound and can eventually crash the host-side supervisor or degrade the operator workstation. The repeated failure counting over `all_samples` also becomes increasingly expensive. This is a reliability/availability bug rather than a direct security boundary bypass in the stated lab threat model.

# Evidence
scripts/revalidation/a90harness/observer.py (L101 to 103)
  Note: When duration is unlimited, `deadline` is `None`, but the observer still initializes an in-memory list for all samples.
```
    started = time.monotonic()
    deadline = None if duration_sec is None else started + duration_sec
    all_samples: list[ObserverSample] = []
```

scripts/revalidation/a90harness/observer.py (L110 to 135)
  Note: Each cycle appends all samples to `all_samples`; with no deadline and no max cycle cap, this grows indefinitely.
```
        while True:
            cycle += 1
            cycle_samples = observe_cycle(client, store, cycle, seq, jsonl_name=jsonl_name)
            all_samples.extend(cycle_samples)
            seq += len(cycle_samples)
            now = time.monotonic()
            store.write_json("heartbeat.json", {
                "cycle": cycle,
                "samples": len(all_samples),
                "failures": sum(1 for sample in all_samples if not sample.ok),
                "host_ts": time.time(),
                "elapsed_sec": now - started,
                "duration_sec": duration_sec,
                "max_cycles": max_cycles,
            })
            if max_cycles is not None and cycle >= max_cycles:
                stop_reason = "max-cycles"
                break
            if deadline is not None and now >= deadline:
                stop_reason = "duration"
                break
            if deadline is None:
                sleep_sec = interval_sec
            else:
                sleep_sec = max(0.0, min(interval_sec, deadline - now))
            time.sleep(sleep_sec)
```

scripts/revalidation/a90harness/observer.py (L140 to 147)
  Note: The summary uses the retained full sample list for counts, showing why the unbounded list is kept alive for the entire run.
```
    failures = sum(1 for sample in all_samples if not sample.ok)
    summary = ObserverSummary(
        ok=failures == 0 and not interrupted,
        cycles=cycle,
        samples=len(all_samples),
        failures=failures,
        duration_sec=time.monotonic() - started,
        jsonl=str(store.path(jsonl_name)),
```

scripts/revalidation/native_test_supervisor.py (L173 to 179)
  Note: The parsed unlimited duration and optional max cycle limit are passed directly into the observer.
```
    observer_summary = run_observer(
        client,
        store,
        duration_sec=parse_duration(args.duration_sec),
        interval_sec=args.interval,
        max_cycles=args.max_cycles,
    )
```

scripts/revalidation/native_test_supervisor.py (L320 to 324)
  Note: `--max-cycles` is optional, so `--duration-sec unlimited` can run with no built-in stopping condition.
```
    observe = subparsers.add_parser("observe", help="run v171 read-only observer")
    observe.add_argument("--run-dir", type=Path)
    observe.add_argument("--duration-sec", default="60.0")
    observe.add_argument("--interval", type=float, default=10.0)
    observe.add_argument("--max-cycles", type=int)
```

scripts/revalidation/native_test_supervisor.py (L49 to 55)
  Note: `unlimited` is parsed as `None`, enabling a no-deadline observer run.
```
def parse_duration(value: str) -> float | None:
    if value.lower() == "unlimited":
        return None
    duration = float(value)
    if duration <= 0:
        raise argparse.ArgumentTypeError("duration must be positive or 'unlimited'")
    return duration
```
