# Native Init v172 Module Runner Plan (2026-05-09)

## Summary

- label: `v172 Module Runner`
- baseline: `A90 Linux init 0.9.59 (v159)`
- objective: add `prepare → run → cleanup → verify` module interface and supervisor `run` command.

v172 is host tooling only. It does not change or flash the boot image.

## Scope

- Add `a90harness/module.py`.
- Add `a90harness/runner.py`.
- Add first module wrapper: `kselftest-feasibility`.
- Extend `native_test_supervisor.py run kselftest-feasibility`.
- Keep existing standalone `kselftest_feasibility.py` usable.

## Guardrails

- Module runner uses one run directory for observer and module evidence.
- `cleanup` and `verify` are attempted even if `prepare` or `run` fails.
- First module is read-only.
- No device boot image changes.

## Acceptance

- `python3 scripts/revalidation/native_test_supervisor.py run kselftest-feasibility --observer-duration-sec 5` returns PASS.
- Run directory contains `manifest.json`, `summary.md`, `observer.jsonl`, and `modules/kselftest-feasibility/`.
- Module result records `prepare`, `run`, `cleanup`, and `verify` steps.
- Static validation passes:

```bash
python3 -m py_compile scripts/revalidation/native_test_supervisor.py scripts/revalidation/a90harness/*.py scripts/revalidation/a90harness/modules/*.py
git diff --check
```

## Next

- v173 Storage/CPU Module Port.
