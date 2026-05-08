# Native Init v170 Harness Foundation Plan (2026-05-09)

## Summary

- label: `v170 Harness Foundation`
- baseline: `A90 Linux init 0.9.59 (v159)`
- objective: add a small host-side `a90harness` package for device command access, private evidence output, and shared result schema.

v170 is host tooling only. It does not change or flash the boot image.

## Scope

- Add `scripts/revalidation/a90harness/`.
- Add `DeviceClient` wrapper around `a90ctl.run_cmdv1_command`.
- Add private evidence writer with `0700` directories, `0600` files, and no-follow checks.
- Add common dataclasses for checks, command records, and run summaries.
- Add `native_test_supervisor.py smoke` as the first user-facing CLI.

## Out Of Scope

- No observer loop yet.
- No module runner yet.
- No storage/CPU/USB/NCM porting yet.
- No device code changes.

## Acceptance

- `python3 scripts/revalidation/native_test_supervisor.py smoke` returns PASS.
- Smoke bundle contains `manifest.json`, `summary.md`, and command transcripts.
- `version` and `status` commands return `rc=0`, `status=ok`.
- Static validation passes:

```bash
python3 -m py_compile \
  scripts/revalidation/native_test_supervisor.py \
  scripts/revalidation/a90harness/*.py
git diff --check
```

## Next

- v171 Observer API.
