# S22+ — Ramoops Vendor Boot + M13 Path Retirement (2026-07-08)

## Summary

Codex retired the superseded vendor_boot-only M13 positive-control path.

No device action, reboot, flash, partition write, ADB live operation, or Odin
live operation was performed by this unit.

Updated helper:

`workspace/public/src/scripts/revalidation/s22plus_ramoops_vendor_boot_m13_capture_live_gate.py`

Updated policy/doc state:

- `AGENTS.md` now marks the old vendor_boot+M13 exception as consumed/retired.
- `GOAL.md` no longer presents vendor_boot+M13 as the current positive-control
  route.

## Reason

The direct vendor_boot patch was already tested live. It booted Android and the
partition hash matched, but live
`/proc/device-tree/reserved-memory/ramoops_region/status` remained `disabled`.
The later active-DTB provenance audit showed why: stock DTBO overlays the ramoops
node and applies `status = "disabled"`.

After the DTBO status-only live gate passed, the current positive-control route
became the DTBO-enabled M13 helper:

`workspace/public/src/scripts/revalidation/s22plus_ramoops_dtbo_m13_capture_live_gate.py`

The old vendor_boot-only helper should not remain runnable as a normal dry-run
or live path just because historical `AGENTS.md` markers still exist.

## Behavior

The helper now preserves:

- `--offline-check`, so historical package/hash checks still work without device
  access;
- explicit recovery modes, so stock vendor_boot or boot rollback cleanup remains
  available if ever needed.

The helper now rejects default dry-run and `--live` before Android/device access:

```text
retired: direct vendor_boot-only ramoops did not affect the live DT; use s22plus_ramoops_dtbo_m13_capture_live_gate.py
```

## Validation

Commands:

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/s22plus_ramoops_vendor_boot_m13_capture_live_gate.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache \
python3 workspace/public/src/scripts/revalidation/s22plus_ramoops_vendor_boot_m13_capture_live_gate.py \
  --offline-check

PYTHONPYCACHEPREFIX=/tmp/a90_pycache \
python3 workspace/public/src/scripts/revalidation/s22plus_ramoops_vendor_boot_m13_capture_live_gate.py
```

Results:

```text
py_compile: pass
offline-check: pass; no device action
default execution: rc=1 with retired-route message before Android/device access
```

## Current Frontier

The current prepared but inactive live path is still DTBO-enabled M13:

`workspace/public/src/scripts/revalidation/s22plus_ramoops_dtbo_m13_capture_live_gate.py`

`AGENTS.md` has not been promoted for that path yet. Live execution remains a
separate attended action.
