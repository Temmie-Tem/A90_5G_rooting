# Native Init v164 Scheduler/Latency Baseline Report (2026-05-09)

## Result

- status: PASS
- label: `v164 Scheduler/Latency Baseline`
- baseline build: `A90 Linux init 0.9.59 (v159)`
- device build was not bumped for this host-side validation step.
- objective: record PID1 run/cmdv1 latency proxy stats across idle, post-cpustress, and post-tmpfs-I/O profiles.

## Implemented

- Added `scripts/revalidation/scheduler_latency_baseline.py`.
- Added `docs/plans/NATIVE_INIT_V164_SCHED_LATENCY_PLAN_2026-05-09.md`.
- The validator captures private host evidence under `tmp/soak/scheduler-latency/<run-id>`.
- The validator computes min/max/avg/p95/p99/max excess and missed deadline count.

## Evidence Paths

```text
tmp/soak/scheduler-latency/v164-smoke-20260509-015120/scheduler-latency-report.md
tmp/soak/scheduler-latency/v164-smoke-20260509-015120/scheduler-latency-report.json
tmp/soak/scheduler-latency/v164-sched-latency-20260509-015147/scheduler-latency-report.md
tmp/soak/scheduler-latency/v164-sched-latency-20260509-015147/scheduler-latency-report.json
```

## Smoke Profile

```text
run_id: v164-smoke-20260509-015120
result: PASS
duration: 8.707s
samples_per_profile: 3
sleep_us: 10000
deadline_ms: 300
```

## Full Profile

```text
run_id: v164-sched-latency-20260509-015147
result: PASS
duration: 35.398s
samples_per_profile: 20
sleep_us: 10000
deadline_ms: 300
```

| Profile | Count | Min ms | Avg ms | P95 ms | P99 ms | Max ms | Max Excess ms | Missed |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `idle` | `20` | `100` | `100.65` | `101.0` | `102.0` | `102` | `92.0` | `0` |
| `post-cpustress` | `20` | `100` | `100.75` | `101.0` | `102.0` | `102` | `92.0` | `0` |
| `post-tmpfs-io` | `20` | `100` | `100.65` | `101.0` | `101.0` | `101` | `91.0` | `0` |

## Check Matrix

| Check | Result | Detail |
|---|---|---|
| tmpfs io profile | PASS | `ok=3 total=3` |
| idle sample count | PASS | `count=20 expected=20` |
| idle missed deadlines | PASS | `missed=0 deadline=300.0ms` |
| post-cpustress sample count | PASS | `count=20 expected=20` |
| post-cpustress missed deadlines | PASS | `missed=0 deadline=300.0ms` |
| post-tmpfs-io sample count | PASS | `count=20 expected=20` |
| post-tmpfs-io missed deadlines | PASS | `missed=0 deadline=300.0ms` |
| cpustress primer | PASS | `post-cpustress profile prepared` |
| final status | PASS | `rc=0 status=ok` |
| final longsoak | PASS | `rc=0 status=ok` |

## Static Validation

```text
python3 -m py_compile scripts/revalidation/scheduler_latency_baseline.py
git diff --check
```

Result: PASS.

## Known Limitation

- v164 uses `toybox usleep` through PID1 `run`/cmdv1 as a latency proxy.
- It is not a true in-process `clock_nanosleep` or `cyclictest` measurement.
- The observed 100ms floor is expected from the current PID1 run wait cadence, so this report is a regression baseline for the current architecture.

## Next

- v165: USB Recovery Stability.
