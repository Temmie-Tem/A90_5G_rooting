# Native Init v175 Unified Evidence Bundle Report (2026-05-09)

## Summary

- label: `v175 Unified Evidence Bundle`
- baseline build: `A90 Linux init 0.9.59 (v159)`
- scope: host-side supervisor evidence layout only; no boot image change
- result: `PASS`

v175 adds a common bundle finalizer for supervisor runs. It standardizes:

- `manifest.json`
- `summary.md`
- `README.md`
- `bundle-index.json`

The finalizer only inventories files inside the run directory and rejects
symlinks in the evidence tree.

## Implemented

- `scripts/revalidation/a90harness/bundle.py`
  - `collect_bundle_files()`
  - `render_bundle_readme()`
  - `finalize_bundle()`
- `scripts/revalidation/native_test_supervisor.py`
  - uses `finalize_bundle()` for `smoke`
  - uses `finalize_bundle()` for `observe`
  - uses `finalize_bundle()` for `run <module>`

## Validation

Static validation:

```bash
python3 -m py_compile \
  scripts/revalidation/native_test_supervisor.py \
  scripts/revalidation/a90harness/*.py \
  scripts/revalidation/a90harness/modules/*.py

git diff --check
```

Bundle validation:

```bash
python3 scripts/revalidation/native_test_supervisor.py \
  run kselftest-feasibility \
  --observer-duration-sec 5 \
  --run-dir tmp/soak/harness/v175-bundle-20260508T175913Z
```

Result:

```text
PASS run_dir=/home/temmie/dev/A90_5G_rooting/tmp/soak/harness/v175-bundle-20260508T175913Z module=kselftest-feasibility observer_failures=0
```

Evidence:

- run directory: `tmp/soak/harness/v175-bundle-20260508T175913Z/`
- `manifest.json`: present
- `summary.md`: present
- `README.md`: present
- `bundle-index.json`: present
- `observer.jsonl`: present
- `modules/kselftest-feasibility/module-result.json`: present

Observed bundle state:

- manifest pass: `True`
- bundle schema: `a90-harness-v175`
- indexed file count: `27`
- run directory mode: `0700`
- `manifest.json` mode: `0600`
- `README.md` mode: `0600`
- `bundle-index.json` mode: `0600`

## Acceptance

| Requirement | Evidence | Result |
| --- | --- | --- |
| Common finalizer writes manifest/summary/readme/index | `v175-bundle-20260508T175913Z/` | PASS |
| Module output stays in same run directory | `modules/kselftest-feasibility/module-result.json` | PASS |
| Observer output stays in same run directory | `observer.jsonl`, `observer-summary.json` | PASS |
| Private file handling remains intact | mode check shows `0700` dir and `0600` files | PASS |
| Static validation passes | `py_compile` and `git diff --check` | PASS |

## Next

- v176 Long-Run Supervisor.
