# Native Init v169 Fault/Debug Feasibility Plan (2026-05-09)

## Summary

- label: `v169 Fault/Debug Feasibility`
- roadmap build target: `A90 Linux init 0.9.69 (v169)`
- validation baseline: current verified `A90 Linux init 0.9.59 (v159)`
- objective: classify fault/debug facilities before any active tracing, pstore reboot, usbmon, or fault-injection test.

v169 is a host-side, read-only feasibility step. It does not bump or flash the
boot image.

## Scope

- Collect debugfs, tracefs, pstore, watchdog, fault-injection, usbmon, and crash-trigger availability.
- Classify each facility as `unavailable`, `read-only-only`, `opt-in-safe-candidate`, or `blocked`.
- Document recovery preconditions for anything that remains blocked or opt-in.

## Allowed Checks

- `kernelinv full`
- `tracefs full`
- `pstore full`
- `watchdoginv status`
- `diag paths`
- read-only `/proc/filesystems` and `/proc/cmdline`
- read-only `stat`/`ls` of `/sys/kernel` debug paths

## Hard Blocks

- no debugfs mount
- no tracefs mount
- no fault injection enable
- no active tracing enable
- no usbmon capture
- no LKDTM or crash trigger
- no pstore reboot preservation test
- no watchdog open
- no raw block/device mutation

## Implementation

- Add `scripts/revalidation/fault_debug_feasibility.py`.
- Output private evidence under `tmp/soak/fault-debug-feasibility/<run-id>`.
- Enforce `0700` directories, `0600` files, and no-follow destination checks.
- Preserve each command transcript plus JSON/Markdown summaries.

## Acceptance

- Mandatory inventory commands pass.
- Every debug/fault facility has a status classification.
- Blocked items include exact reason and recovery preconditions.
- Manifest explicitly records `mutation_performed=false`.
- Wi-Fi/network exposure work can proceed with known debug fallback options.

## Validation Commands

```bash
python3 -m py_compile scripts/revalidation/fault_debug_feasibility.py
python3 scripts/revalidation/fault_debug_feasibility.py
git diff --check
```

## Expected Outcome

The expected output is a feasibility report, not an active debug run. pstore reboot
preservation, usbmon capture, active ftrace, and fault injection remain separate
explicit-plan work.
