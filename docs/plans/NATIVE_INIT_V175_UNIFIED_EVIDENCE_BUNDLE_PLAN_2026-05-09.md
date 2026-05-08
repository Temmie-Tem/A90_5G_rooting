# Native Init v175 Unified Evidence Bundle Plan (2026-05-09)

## Summary

- label: `v175 Unified Evidence Bundle`
- baseline: `A90 Linux init 0.9.59 (v159)`
- objective: standardize supervisor run output layout and bundle metadata.

v175 is host tooling only. It does not change or flash the boot image.

## Scope

- Add `a90harness/bundle.py`.
- Add common bundle finalizer for:
  - `manifest.json`
  - `summary.md`
  - `README.md`
  - `bundle-index.json`
- Apply finalizer to:
  - `native_test_supervisor.py smoke`
  - `native_test_supervisor.py observe`
  - `native_test_supervisor.py run <module>`
- Keep private/no-follow evidence writer policy.

## Guardrails

- Bundle finalization must not copy arbitrary paths.
- Bundle index must only describe files already inside the run directory.
- Symlinks inside evidence directories are rejected.
- Existing module outputs remain in-place.

## Acceptance

- Static validation passes:

```bash
python3 -m py_compile scripts/revalidation/native_test_supervisor.py scripts/revalidation/a90harness/*.py scripts/revalidation/a90harness/modules/*.py
git diff --check
```

- Bundle validation:

```bash
python3 scripts/revalidation/native_test_supervisor.py run kselftest-feasibility --observer-duration-sec 5
```

Expected output directory contains:

- `manifest.json`
- `summary.md`
- `README.md`
- `bundle-index.json`
- `observer.jsonl`
- `modules/kselftest-feasibility/module-result.json`

## Next

- v176 Long-Run Supervisor.
