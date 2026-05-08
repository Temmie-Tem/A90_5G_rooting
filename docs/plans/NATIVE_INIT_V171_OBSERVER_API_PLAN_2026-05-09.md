# Native Init v171 Observer API Plan (2026-05-09)

## Summary

- label: `v171 Observer API`
- baseline: `A90 Linux init 0.9.59 (v159)`
- objective: add a shared read-only observer that can run independently of test modules.

v171 is host tooling only. It does not change or flash the boot image.

## Scope

- Add `a90harness/observer.py`.
- Add append-safe private JSONL writer support.
- Add `native_test_supervisor.py observe`.
- Default observer commands:
  - `version`
  - `status`
  - `selftest verbose`
  - `bootstatus`
  - `longsoak status verbose`
  - `storage`
  - `netservice status`
- Output:
  - `observer.jsonl`
  - `observer-summary.json`
  - `manifest.json`
  - `summary.md`

## Guardrails

- Observer is read-only.
- No mount/remount, USB rebind, NCM start/stop, reboot, watchdog open, fault injection, or tracefs write.
- Serial commands remain single-writer through `DeviceClient`.

## Acceptance

- `python3 scripts/revalidation/native_test_supervisor.py observe --duration-sec 15 --interval 5` returns PASS.
- Observer sample failures are 0.
- `observer.jsonl` contains repeated command samples.
- Static validation passes:

```bash
python3 -m py_compile scripts/revalidation/native_test_supervisor.py scripts/revalidation/a90harness/*.py
git diff --check
```

## Next

- v172 Module Runner.
