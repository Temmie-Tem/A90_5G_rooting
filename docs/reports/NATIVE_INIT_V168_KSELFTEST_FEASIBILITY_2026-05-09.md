# Native Init v168 Kernel Selftest Feasibility Report (2026-05-09)

## Result

- status: PASS
- label: `v168 Kernel Selftest Feasibility`
- baseline build: `A90 Linux init 0.9.59 (v159)`
- roadmap target: `A90 Linux init 0.9.68 (v168)`
- device build was not bumped for this host-side feasibility step.
- objective: classify safe kselftest/LTP-style userspace subset candidates without kernel mutation.

## Implemented

- Added `scripts/revalidation/kselftest_feasibility.py`.
- Added `docs/plans/NATIVE_INIT_V168_KSELFTEST_FEASIBILITY_PLAN_2026-05-09.md`.
- The collector uses only read-only native commands and `/proc`/`/sys/class` reads.
- The collector writes private evidence with `0700` directories, `0600` files, and no-follow destination checks.

## Evidence Path

```text
tmp/soak/kselftest-feasibility/v168-kselftest-20260508T171140Z/
```

Primary files:

```text
tmp/soak/kselftest-feasibility/v168-kselftest-20260508T171140Z/kselftest-feasibility-report.md
tmp/soak/kselftest-feasibility/v168-kselftest-20260508T171140Z/kselftest-feasibility-report.json
```

## Run Summary

```text
result: PASS
expect_version: A90 Linux init 0.9.59 (v159)
version_matches: True
failed_mandatory: 0
failed_optional: 0
safe_candidates: 4
conditional_or_unknown: 5
blocked: 6
mutation_performed: False
commands: 18
```

## Mandatory Inventory

All mandatory commands returned `rc=0` and `status=ok`.

| Command | Result |
|---|---|
| `version` | PASS |
| `kernelinv full` | PASS |
| `userland status` | PASS |
| `helpers status` | PASS |
| `tracefs status` | PASS |
| `pstore status` | PASS |
| `watchdoginv status` | PASS |
| `sensormap summary` | PASS |

## Optional Inventory

All optional commands returned `rc=0` and `status=ok`.

| Command | Result |
|---|---|
| `diag summary` | PASS |
| `cat /proc/version` | PASS |
| `cat /proc/cmdline` | PASS |
| `cat /proc/filesystems` | PASS |
| `cat /proc/self/status` | PASS |
| `cat /proc/meminfo` | PASS |
| `cat /proc/uptime` | PASS |
| `ls /sys/class/thermal` | PASS |
| `ls /sys/class/power_supply` | PASS |
| `run /cache/bin/toybox` | PASS |

## Safe Candidates

- `timers-basic-userspace-helper`: bounded static helper can measure sleep/jitter without kernel mutation.
- `procfs-readers`: `/proc` readers are safe and already work through current shell/cat path.
- `sysfs-thermal-power-readers`: thermal and power_supply readers are safe read-only probes.
- `filesystem-non-destructive-tempdir`: v167 already validates bounded operation sequences under `/mnt/sdext/a90/test-fsx`.

## Conditional Or Unknown

- `network-smoke-kselftest-subset`: conditional on operator-configured USB NCM.
- `static-kselftest-helper-build`: per-test dependency and static ARM64 build audit still required.
- `pstore-read-only-inventory`: available for read-only inventory; mount/reboot persistence requires explicit plan.
- `tracefs-read-only-inventory`: available for read-only inventory; active tracing/mounts remain opt-in.
- `cgroup-bpf-read-only-inventory`: filesystems are visible, but mounts/controllers/userspace coverage need a smaller follow-up.

## Blocked

- `hotplug-module-tests`: blocked because module/hotplug mutation is outside the recovery envelope.
- `fault-injection`: blocked until v169 read-only fault/debug classification and explicit recovery preconditions.
- `watchdog-tests`: blocked because watchdog open can arm reboot behavior.
- `raw-device-mutation`: blocked by partition/device mutation guardrails.
- `crash-reboot-lkdtm`: blocked without explicit pstore/recovery plan and operator approval.
- `active-ftrace-tracing`: blocked by default; read-only tracefs evidence only for now.

## Static Validation

```text
python3 -m py_compile scripts/revalidation/kselftest_feasibility.py
```

Result: PASS.

## Notes

- This step intentionally did not run full kselftest or LTP.
- No mount, remount, watchdog open, fault-injection write, tracefs write, module mutation, raw block access, reboot, or crash trigger was performed.
- Network-related kselftest smoke remains conditional because the current final device state is ACM-only and v166 throughput remains deferred until host NCM is configured.

## Next

- v169: Fault/Debug Feasibility.
