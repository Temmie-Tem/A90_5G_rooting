# Native Init v169 Fault/Debug Feasibility Report (2026-05-09)

## Result

- status: PASS
- label: `v169 Fault/Debug Feasibility`
- baseline build: `A90 Linux init 0.9.59 (v159)`
- roadmap target: `A90 Linux init 0.9.69 (v169)`
- device build was not bumped for this host-side feasibility step.
- objective: classify debug/fault facilities before active tracing, usbmon, pstore reboot, or fault-injection work.

## Implemented

- Added `scripts/revalidation/fault_debug_feasibility.py`.
- Added `docs/plans/NATIVE_INIT_V169_FAULT_DEBUG_FEASIBILITY_PLAN_2026-05-09.md`.
- The collector uses read-only native commands and read-only `stat`/`ls` probes.
- The collector writes private evidence with `0700` directories, `0600` files, and no-follow destination checks.

## Evidence Path

```text
tmp/soak/fault-debug-feasibility/v169-fault-debug-20260508T171514Z/
```

Primary files:

```text
tmp/soak/fault-debug-feasibility/v169-fault-debug-20260508T171514Z/fault-debug-feasibility-report.md
tmp/soak/fault-debug-feasibility/v169-fault-debug-20260508T171514Z/fault-debug-feasibility-report.json
```

## Run Summary

```text
result: PASS
expect_version: A90 Linux init 0.9.59 (v159)
version_matches: True
failed_mandatory: 0
failed_optional: 7
mutation_performed: False
facilities: 8
```

The optional failures are expected absence evidence for debugfs paths that are not
mounted or not present in the current safe baseline.

## Mandatory Inventory

All mandatory commands returned `rc=0` and `status=ok`.

| Command | Result |
|---|---|
| `version` | PASS |
| `kernelinv full` | PASS |
| `tracefs full` | PASS |
| `pstore full` | PASS |
| `watchdoginv status` | PASS |
| `diag paths` | PASS |
| `cat /proc/filesystems` | PASS |
| `cat /proc/cmdline` | PASS |

## Facility Classification

| Facility | Status | Reason |
|---|---|---|
| `debugfs` | `read-only-only` | filesystem listed, not mounted; no mount performed |
| `tracefs-active-mode` | `read-only-only` | tracefs available, not mounted; active tracing writes blocked by default |
| `usbmon` | `unavailable` | usbmon debugfs path unavailable because debugfs is not mounted |
| `fault-injection` | `blocked` | requires kernel/debugfs writes and can destabilize runtime paths |
| `lkdtm-crash-trigger` | `blocked` | intentionally panics/reboots the device |
| `pstore-reboot-preservation` | `opt-in-safe-candidate` | pstore support visible, but reboot preservation requires explicit plan |
| `watchdog-debug` | `blocked` | watchdog open can arm reboot behavior |
| `raw-block-or-modem-debug` | `blocked` | outside the native-init safety envelope |

## Required Preconditions Before Revisit

- debugfs/tracefs/usbmon: explicit mount/capture plan, ACM rescue verified, bounded duration and output, privacy review for host-side packet capture.
- pstore reboot preservation: explicit reboot plan, pre/post evidence bundle, no crash trigger by default.
- fault injection/LKDTM: known-good boot image, TWRP access, pstore/ramoops preservation plan, physical recovery path, explicit operator approval.
- watchdog: dedicated watchdog safety plan before any `/dev/watchdog*` open.
- raw block/modem/EFS/security partitions: remain blocked for current Wi-Fi/network baseline work.

## Static Validation

```text
python3 -m py_compile scripts/revalidation/fault_debug_feasibility.py
```

Result: PASS.

## Notes

- No debugfs or tracefs mount was performed.
- No fault injection, active tracing, usbmon capture, crash trigger, pstore reboot, watchdog open, or raw block/device mutation was performed.
- Wi-Fi/network exposure work can proceed with known debug fallback options: pstore read-only inventory is available, tracefs/debugfs are read-only-only unless explicitly mounted later, and crash/fault paths remain blocked.

## Next

- v170+: Wi-Fi baseline refresh.
- v171+: network exposure hardening before any non-USB-local control path.
