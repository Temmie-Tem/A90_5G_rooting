# Native Init v173 Storage/CPU Module Port Report (2026-05-09)

## Summary

- label: `v173 Storage/CPU Module Port`
- baseline build: `A90 Linux init 0.9.59 (v159)`
- scope: host-side supervisor module wrappers only; no boot image change
- result: `PASS with storage SKIP`

v173 ports two existing validators onto the v172 module runner:

- `cpu-mem-thermal`
- `storage-io`

The CPU module ran a real bounded smoke test. The storage module reached its
preflight gate and correctly skipped because host USB NCM (`192.168.7.2`) was not
reachable in the current ACM-only environment. It did not attempt sudo, USB
rebind, or host network mutation.

## Implemented

- `scripts/revalidation/a90harness/modules/cpu_mem_thermal.py`
  - wraps `scripts/revalidation/cpu_mem_thermal_stability.py`
  - smoke profile: `cycles=1`, `stress_sec=1`, `mem_size=4M`
- `scripts/revalidation/a90harness/modules/storage_io.py`
  - wraps `scripts/revalidation/storage_iotest.py`
  - smoke profile: `sizes=4096`
  - NCM preflight ping before side effects
  - structured SKIP when NCM is absent
- `scripts/revalidation/a90harness/module.py`
  - adds module `cycle_label`
  - adds `StepResult.skipped`
  - adds `ModuleOutcome.skipped`
- `scripts/revalidation/native_test_supervisor.py`
  - adds `--profile smoke|quick`
  - registers `cpu-mem-thermal` and `storage-io`

## Validation

Static validation:

```bash
python3 -m py_compile \
  scripts/revalidation/native_test_supervisor.py \
  scripts/revalidation/a90harness/*.py \
  scripts/revalidation/a90harness/modules/*.py

git diff --check
```

CPU module validation:

```bash
python3 scripts/revalidation/native_test_supervisor.py \
  run cpu-mem-thermal \
  --profile smoke \
  --observer-duration-sec 5
```

Result:

```text
PASS run_dir=/home/temmie/dev/A90_5G_rooting/tmp/soak/harness/v173-cpu-mem-thermal-20260508T175358Z module=cpu-mem-thermal observer_failures=0
```

CPU evidence:

- run directory: `tmp/soak/harness/v173-cpu-mem-thermal-20260508T175358Z/`
- module result: `modules/cpu-mem-thermal/module-result.json`
- child report: `modules/cpu-mem-thermal/v173-cpu-*/cpu-mem-thermal-report.json`
- observer samples: `14`
- observer failures: `0`
- module skipped: `False`
- module steps: `prepare=True`, `run=True`, `cleanup=True`, `verify=True`

Storage module validation:

```bash
python3 scripts/revalidation/native_test_supervisor.py \
  run storage-io \
  --profile smoke \
  --observer-duration-sec 5
```

Result:

```text
PASS run_dir=/home/temmie/dev/A90_5G_rooting/tmp/soak/harness/v173-storage-io-20260508T175421Z module=storage-io observer_failures=0
```

Storage evidence:

- run directory: `tmp/soak/harness/v173-storage-io-20260508T175421Z/`
- module result: `modules/storage-io/module-result.json`
- preflight transcript: `modules/storage-io/preflight-ping.txt`
- observer samples: `14`
- observer failures: `0`
- module skipped: `True`
- skip reason: `host NCM path 192.168.7.2 is not reachable; not attempting sudo or USB rebind`

## Acceptance

| Requirement | Evidence | Result |
| --- | --- | --- |
| CPU module wrapper runs under supervisor | `v173-cpu-mem-thermal-20260508T175358Z/manifest.json` | PASS |
| CPU module observer shares one run directory | `observer.jsonl` and `modules/cpu-mem-thermal/` in same run dir | PASS |
| Storage module wrapper exists and preflights NCM | `v173-storage-io-20260508T175421Z/modules/storage-io/preflight-ping.txt` | PASS |
| Storage avoids host mutation when NCM absent | structured SKIP; no sudo/rebind attempted | PASS |
| Existing standalone scripts remain usable | wrappers invoke existing scripts; no CLI contract removed | PASS |
| Static validation passes | `py_compile` and `git diff --check` | PASS |

## Follow-Up

- Re-run `storage-io` with host NCM configured to obtain full storage I/O PASS evidence.
- Proceed to v174 USB/NCM Module Port.
