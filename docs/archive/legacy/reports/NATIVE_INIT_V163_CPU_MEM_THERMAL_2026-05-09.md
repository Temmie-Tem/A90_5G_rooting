# Native Init v163 CPU/Memory/Thermal Stability Report (2026-05-09)

## Result

- status: PASS
- label: `v163 CPU/Memory/Thermal Stability`
- baseline build: `A90 Linux init 0.9.59 (v159)`
- device build was not bumped for this host-side validation step.
- objective: verify bounded CPU stress, tmpfs memory verify, thermal/power trend, and PID1 responsiveness.

## Implemented

- Added `scripts/revalidation/cpu_mem_thermal_stability.py`.
- Added `docs/plans/NATIVE_INIT_V163_CPU_MEM_THERMAL_PLAN_2026-05-09.md`.
- The validator captures private host evidence under `tmp/soak/cpu-mem-thermal/<run-id>`.
- The validator checks tmpfs write/hash/cleanup, repeated `/bin/a90_cpustress`, `status` trend samples, thermal thresholds, longsoak health, process zombies, PID1 fd count, final selftest, and final longsoak.

## Evidence Paths

```text
tmp/soak/cpu-mem-thermal/v163-smoke-20260509-014514/cpu-mem-thermal-report.md
tmp/soak/cpu-mem-thermal/v163-smoke-20260509-014514/cpu-mem-thermal-report.json
tmp/soak/cpu-mem-thermal/v163-cpu-mem-thermal-20260509-014606/cpu-mem-thermal-report.md
tmp/soak/cpu-mem-thermal/v163-cpu-mem-thermal-20260509-014606/cpu-mem-thermal-report.json
```

## Smoke Profile

```text
run_id: v163-smoke-20260509-014514
result: PASS
duration: 6.405s
cycles: 1
stress: 1s x 1 worker
memory_verify: 1MiB hash_ok=True
max_cpu_temp_c: 37.6
max_gpu_temp_c: 35.1
max_battery_temp_c: 31.0
max_status_duration_ms: 33
controlled_zombies: 0
```

## Full Profile

```text
run_id: v163-cpu-mem-thermal-20260509-014606
result: PASS
duration: 24.489s
cycles: 5
stress: 3s x 2 workers
memory_verify: 32MiB hash_ok=True
max_cpu_temp_c: 43.1
max_gpu_temp_c: 39.4
max_battery_temp_c: 31.1
max_power_now_w: 0.4
max_mem_used_mb: 271
max_status_duration_ms: 32
pid_count: 392
pid1_fd_count: 5
global_zombies: 0
controlled_zombies: 0
```

## Check Matrix

| Check | Result | Detail |
|---|---|---|
| tmpfs memory verify | PASS | `size=33554432 hash_ok=True cleanup=ok/0` |
| cpustress cycles | PASS | `ok=5 total=5` |
| status samples | PASS | `ok=6 total=6` |
| cpu temp threshold | PASS | `max=43.1 limit=85.0` |
| gpu temp threshold | PASS | `max=39.4 limit=85.0` |
| battery temp threshold | PASS | `max=31.1 limit=45.0` |
| status responsiveness | PASS | `max=32ms limit=2000ms` |
| longsoak health | PASS | `samples=6` |
| controlled zombies | PASS | `controlled=0 global=0` |
| final selftest | PASS | `rc=0 status=ok` |
| final longsoak | PASS | `rc=0 status=ok` |

## Static Validation

```text
python3 -m py_compile scripts/revalidation/cpu_mem_thermal_stability.py
git diff --check
```

Result: PASS.

## Notes

- The stress profile is intentionally short and bounded. It is a regression baseline, not a maximum thermal qualification run.
- Memory verification uses `/tmp` tmpfs and removes the file after hashing.
- Host NCM ping is available as a warning-only option, but the v163 acceptance is based on serial/cmdv1 status responsiveness because v160 already covered a 1-hour NCM/TCP soak.

## Next

- v164: Scheduler/Latency Baseline.
