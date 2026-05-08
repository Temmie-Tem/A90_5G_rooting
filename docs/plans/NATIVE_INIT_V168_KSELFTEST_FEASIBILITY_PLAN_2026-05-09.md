# Native Init v168 Kernel Selftest Feasibility Plan (2026-05-09)

## Summary

- label: `v168 Kernel Selftest Feasibility`
- roadmap build target: `A90 Linux init 0.9.68 (v168)`
- validation baseline: current verified `A90 Linux init 0.9.59 (v159)`
- objective: classify safe mainline kselftest/LTP-style userspace subset candidates before adding new kernel-facing helpers.

v168 is a host-side, read-only feasibility step. It does not bump or flash the boot image.

## Scope

- Collect current kernel/userland capability evidence through the serial bridge.
- Classify candidates into `safe`, `conditional/unknown`, and `blocked`.
- Record why each blocked class is blocked and what would be required before revisiting it.

## Allowed Checks

- `kernelinv full`
- `userland status`
- `helpers status`
- `tracefs status`
- `pstore status`
- `watchdoginv status`
- `sensormap summary`
- read-only `/proc` and `/sys/class` queries
- toybox applet inventory

## Hard Blocks

- no full LTP or full kselftest run
- no mount or remount
- no module load/unload
- no hotplug mutation
- no watchdog open
- no fault injection enable
- no active tracefs/ftrace writes
- no raw block/device mutation
- no reboot/crash/LKDTM trigger

## Implementation

- Add `scripts/revalidation/kselftest_feasibility.py`.
- Output private evidence under `tmp/soak/kselftest-feasibility/<run-id>`.
- Enforce `0700` directories, `0600` files, and no symlink-following output writes.
- Preserve each command transcript plus JSON/Markdown summaries.

## Acceptance

- Mandatory inventory commands pass.
- Report includes non-empty safe candidate list.
- Report includes non-empty conditional/unknown list.
- Report includes non-empty blocked list.
- Manifest explicitly records `mutation_performed=false`.
- Next implementation candidates are bounded helper tests only.

## Validation Commands

```bash
python3 -m py_compile scripts/revalidation/kselftest_feasibility.py
python3 scripts/revalidation/kselftest_feasibility.py
git diff --check
```

## Expected Outcome

The expected output is a feasibility report, not a new boot image. If the current
device remains ACM-only and NCM is absent, network-related kselftest smoke remains
conditional rather than failed.
