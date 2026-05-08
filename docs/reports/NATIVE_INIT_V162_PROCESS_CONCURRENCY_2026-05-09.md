# Native Init v162 Process/Concurrency Stability Report (2026-05-09)

## Result

- status: PASS
- label: `v162 Process/Concurrency Stability`
- baseline build: `A90 Linux init 0.9.59 (v159)`
- device build was not bumped for this host-side validation step.
- objective: verify PID1 shell/run/service/tcpctl concurrency behavior while longsoak, autohud, tcpctl, and short CPU stress are active.

## Implemented

- Added `scripts/revalidation/process_concurrency_validate.py`.
- Added `docs/plans/NATIVE_INIT_V162_PROCESS_CONCURRENCY_PLAN_2026-05-09.md`.
- The validator captures private host evidence under `tmp/soak/process-concurrency/<run-id>`.
- The validator checks helper churn, tcpctl parallel clients, short cpustress via tcpctl, menu busy gate, process snapshot, zombie count, and PID1 fd growth.

## Evidence Paths

```text
tmp/soak/process-concurrency/v162-smoke-20260509-013543/process-concurrency-report.md
tmp/soak/process-concurrency/v162-smoke-20260509-013543/process-concurrency-report.json
tmp/soak/process-concurrency/v162-process-20260509-013720/process-concurrency-report.md
tmp/soak/process-concurrency/v162-process-20260509-013720/process-concurrency-report.json
```

## Smoke Profile

```text
run_id: v162-smoke-20260509-013543
result: PASS
duration: 11.427s
churn: 4/4
tcpctl_ops: 4/4
controlled_zombies: 0
pid1_fd_count: 5 -> 5
```

## Full Profile

```text
run_id: v162-process-20260509-013720
result: PASS
duration: 26.086s
churn: 32/32
tcpctl_ops: 18/18
cpustress: run /bin/a90_cpustress 3 2 PASS
before_pid_count: 393
after_pid_count: 392
before_pid1_fd_count: 5
after_pid1_fd_count: 5
after_zombies: 0
after_controlled_zombies: 0
```

## Check Matrix

| Check | Result | Detail |
|---|---|---|
| background services requested | PASS | `initial-hide=ok/0`, `longsoak-start=ok/0`, `autohud-start=ok/0`, `post-autohud-hide=ok/0` |
| helper churn | PASS | `ok=32 total=32` |
| tcpctl parallel ops | PASS | `ok=18 total=18` |
| tcpctl shutdown | PASS | `shutdown_error='' serial_done=True` |
| concurrent cpustress | PASS | `ok=1 total=1` |
| busy gate blocks run | PASS | `screenmenu=ok/0 probe=busy/-16 hide=ok/0` |
| policycheck pass | PASS | `rc=0 status=ok` |
| controlled zombies | PASS | `controlled_zombies=0 global_zombies=0` |
| pid1 fd growth | PASS | `before=5 after=5 limit=8` |

## Static Validation

```text
python3 -m py_compile scripts/revalidation/process_concurrency_validate.py
git diff --check
```

Result: PASS.

## Notes

- An earlier smoke attempt used `max_clients=8`; tcpctl exited after serving the bounded client limit before all planned requests finished. The validator now defaults to `max_clients=32` and raises it when the requested operation count requires more.
- Serial and tcpctl concurrency are intentionally separated: the tcpctl listener occupies one serial `run`, so concurrent CPU stress is executed through tcpctl as `/bin/a90_cpustress`.
- This validates process lifecycle and control-plane behavior only; it does not perform destructive reboot, partition, watchdog, or tracing operations.

## Next

- v163: CPU/Memory/Thermal Stability.
