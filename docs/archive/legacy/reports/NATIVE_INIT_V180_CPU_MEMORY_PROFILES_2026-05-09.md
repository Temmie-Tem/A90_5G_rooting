# A90 v180 CPU/Memory Workload Profiles Report

Date: `2026-05-09`
Device build under test: `A90 Linux init 0.9.59 (v159)`
Cycle label: `v180` host harness, not a native-init boot image
Plan: `docs/plans/NATIVE_INIT_V180_CPU_MEMORY_PROFILES_PLAN_2026-05-09.md`
Roadmap: `docs/plans/NATIVE_INIT_V178_V184_MIXED_SOAK_SECURITY_ROADMAP_2026-05-09.md`

## Summary

Result: `PASS`

v180 adds the `cpu-memory-profiles` workload module. It runs bounded CPU stress
and temporary memory write/hash/cleanup profiles through the shared
`DeviceClient`, so the read-only observer and workload commands do not open
competing bridge connections.

## Implementation

- Added `scripts/revalidation/a90harness/modules/cpu_memory_profiles.py`.
- Registered `cpu-memory-profiles` in `scripts/revalidation/native_test_supervisor.py`.
- Updated `a90harness/scheduler.py` so the default CPU workload is
  `cpu-memory-profiles`.
- Replaced the initial legacy-helper approach with direct `DeviceClient` command
  execution after mixed smoke exposed bridge reset risk from concurrent direct
  bridge clients.

## Validation

Static:

```bash
python3 -m py_compile \
  scripts/revalidation/native_test_supervisor.py \
  scripts/revalidation/a90harness/*.py \
  scripts/revalidation/a90harness/modules/*.py

git diff --check
```

Results:

- Python compile: `PASS`
- diff whitespace: `PASS`
- `cpu-memory-profiles` appears in `list`/`plan`: `PASS`

Quick profile run:

```bash
python3 scripts/revalidation/native_test_supervisor.py run cpu-memory-profiles \
  --profile quick \
  --observer-duration-sec 30 \
  --observer-interval 5 \
  --run-dir tmp/soak/harness/v180-cpumem-quick-20260509-045117
```

Result:

- `PASS`
- profiles: `4`
- max CPU usage observed by module: `38%`
- memory mismatch: `0`
- observer failures: `0`
- observer samples: `35`
- evidence: `tmp/soak/harness/v180-cpumem-quick-20260509-045117/`

Mixed-soak smoke:

```bash
python3 scripts/revalidation/native_test_supervisor.py mixed-soak \
  --duration-sec 30 \
  --observer-interval 5 \
  --seed 180 \
  --run-dir tmp/soak/harness/v180-mixed-smoke-20260509-045226
```

Result:

- `PASS`
- schedule includes: `ncm-tcp-preflight`, `storage-io`, `cpu-memory-profiles`
- workload pass: `1`
- structured blocked/skipped: `2`
- observer failures: `0`
- evidence: `tmp/soak/harness/v180-mixed-smoke-20260509-045226/`

## Notes

The first mixed-smoke attempt exposed a valid integration issue: the legacy
`cpu_mem_thermal_stability.py` wrapper opens independent bridge connections, so
it can collide with the concurrent observer. v180 fixes this by implementing the
profile workload directly on the shared `DeviceClient` lock.

## Result

v180 is accepted. v181 can now integrate NCM/TCP and storage workloads into the
same scheduler while preserving the safety-gated skip/block behavior.
