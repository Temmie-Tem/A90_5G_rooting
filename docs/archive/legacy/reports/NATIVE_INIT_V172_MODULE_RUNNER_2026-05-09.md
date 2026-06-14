# Native Init v172 Module Runner Report (2026-05-09)

## Summary

- label: `v172 Module Runner`
- baseline build: `A90 Linux init 0.9.59 (v159)`
- scope: host-side supervisor module interface only; no boot image change
- result: `PASS`

v172 adds the first common validation module path:

```text
native_test_supervisor.py run <module>
  └─ ModuleRunner
      ├─ optional read-only observer
      └─ TestModule prepare → run → cleanup → verify
```

## Implemented

- `scripts/revalidation/a90harness/module.py`
  - `TestModule`
  - `ModuleContext`
  - `StepResult`
  - `ModuleOutcome`
- `scripts/revalidation/a90harness/runner.py`
  - `ModuleRunner`
  - shared run directory for observer and module evidence
  - cleanup and verify attempted after every run
- `scripts/revalidation/a90harness/modules/kselftest_feasibility.py`
  - wraps existing `scripts/revalidation/kselftest_feasibility.py`
  - keeps standalone collector usable
- `scripts/revalidation/native_test_supervisor.py`
  - adds `run kselftest-feasibility`
  - writes top-level `manifest.json` and `summary.md`

## Validation

Static validation:

```bash
python3 -m py_compile \
  scripts/revalidation/native_test_supervisor.py \
  scripts/revalidation/a90harness/*.py \
  scripts/revalidation/a90harness/modules/*.py

git diff --check
```

Device validation:

```bash
python3 scripts/revalidation/native_test_supervisor.py \
  run kselftest-feasibility \
  --observer-duration-sec 5
```

Result:

```text
PASS run_dir=/home/temmie/dev/A90_5G_rooting/tmp/soak/harness/v172-kselftest-feasibility-20260508T175009Z module=kselftest-feasibility observer_failures=0
```

Evidence:

- run directory: `tmp/soak/harness/v172-kselftest-feasibility-20260508T175009Z/`
- top-level manifest: `manifest.json`
- top-level summary: `summary.md`
- observer stream: `observer.jsonl`
- observer summary: `observer-summary.json`
- module directory: `modules/kselftest-feasibility/`
- module result: `modules/kselftest-feasibility/module-result.json`
- child report: `modules/kselftest-feasibility/kselftest-feasibility-report.json`

Observed result:

- module result: `PASS`
- module steps: `prepare=True`, `run=True`, `cleanup=True`, `verify=True`
- module artifacts: `21`
- observer cycles: `2`
- observer samples: `14`
- observer failures: `0`
- version matches: `True`

## Acceptance

| Requirement | Evidence | Result |
| --- | --- | --- |
| `native_test_supervisor.py run kselftest-feasibility --observer-duration-sec 5` returns PASS | command output above | PASS |
| Run directory contains manifest, summary, observer stream, and module dir | `find tmp/soak/harness/v172-kselftest-feasibility-20260508T175009Z -maxdepth 3 -type f` | PASS |
| Module result records prepare/run/cleanup/verify | `module-result.json` and top-level `summary.md` | PASS |
| Static validation passes | `py_compile` and `git diff --check` | PASS |
| Existing standalone collector remains usable | wrapper invokes existing `kselftest_feasibility.py`; no CLI contract removed | PASS |

## Next

- v173 Storage/CPU Module Port:
  - wrap `storage_iotest.py`
  - wrap `cpu_mem_thermal_stability.py`
  - keep existing standalone scripts usable
