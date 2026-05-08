# Native Init v171 Observer API Report (2026-05-09)

## Result

- status: PASS
- label: `v171 Observer API`
- baseline build: `A90 Linux init 0.9.59 (v159)`
- device build was not bumped for this host-side tooling step.
- objective: add shared read-only observer and supervisor `observe` command.

## Implemented

- Added `scripts/revalidation/a90harness/observer.py`.
- Extended `scripts/revalidation/a90harness/evidence.py` with private append JSONL support.
- Extended `scripts/revalidation/native_test_supervisor.py` with `observe`.
- Added `docs/plans/NATIVE_INIT_V171_OBSERVER_API_PLAN_2026-05-09.md`.

## Evidence Path

```text
tmp/soak/harness/v171-observer-20260508T174309Z/
```

Primary files:

```text
tmp/soak/harness/v171-observer-20260508T174309Z/manifest.json
tmp/soak/harness/v171-observer-20260508T174309Z/summary.md
tmp/soak/harness/v171-observer-20260508T174309Z/observer.jsonl
tmp/soak/harness/v171-observer-20260508T174309Z/observer-summary.json
```

## Run Summary

```text
result: PASS
duration: 17.865s
cycles: 3
samples: 21
failures: 0
version_matches: True
```

## Observed Commands

- `version`
- `status`
- `selftest verbose`
- `bootstatus`
- `longsoak status verbose`
- `storage`
- `netservice status`

## Checks

| Check | Result |
|---|---|
| observer samples > 0 | PASS |
| observer failures == 0 | PASS |
| expected version string observed | PASS |

## Static Validation

```text
python3 -m py_compile scripts/revalidation/native_test_supervisor.py scripts/revalidation/a90harness/*.py
git diff --check
```

Result: PASS.

## Notes

- The observer is read-only.
- No mount/remount, USB rebind, NCM start/stop, reboot, watchdog open, fault injection, or tracefs write was performed.
- `DeviceClient` remains the single writer for serial `cmdv1` calls.

## Next

- v172 Module Runner.
