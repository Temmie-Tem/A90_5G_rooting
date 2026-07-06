# S22+ Observable Native-Init M3 Evidence Collector Preflight - 2026-07-07

## Scope

Tightened the guarded M3 v0.2 live helper before any live boot flash. This unit
did not flash, reboot, write partitions, install Magisk modules, load/unload
kernel modules, or change running Android sysfs/configfs state.

## Reason

M3 emits its proof marker through kmsg and pmsg, then attempts a software
`download` reboot after the bounded observation window. Host-side USB/NCM
snapshots are useful but transient. The live helper should also preserve any
reboot-surviving pstore/pmsg evidence after rollback to Android, otherwise a
brief M3 marker could be missed by the host.

## Change

Updated:

```text
workspace/public/src/scripts/revalidation/s22plus_m3_observable_live_gate.py
GOAL.md
```

The helper now:

- reads `/sys/fs/pstore` after rollback Android and Magisk root are verified;
- writes pstore payloads only under the private run directory;
- logs the pstore file list;
- logs whether `S22_NATIVE_INIT_OBSERVABLE_M3` was found in those payloads.

This is collection only. Missing pstore marker does not by itself fail rollback,
because the host USB/NCM observation path may still be the primary live proof
and pstore availability is platform/runtime dependent.

## Validation

Commands:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/s22plus_m3_observable_live_gate.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_m3_observable_live_gate.py
```

Results:

```text
py_compile: pass
no-flash dry-run: pass
```

Dry-run private log:

```text
workspace/private/runs/s22plus_m3_observable_live_gate_20260706T181915Z/
```

Read-only pstore smoke test on the current rooted Android baseline:

```text
marker_found=0
smoke_pstore_files=[]
smoke_pstore_marker_found=0
```

That empty pstore state is expected before an M3 candidate boot and validates
that the helper handles the no-file case without failing.

## Live Boundary

Live M3 remains gated and was not executed in this unit.

The live command remains:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_m3_observable_live_gate.py \
  --live \
  --ack S22PLUS-M3-OBSERVABLE-LIVE-GATE
```

The operator still needs to supervise because if M3's software `download`
reboot is not honored, physical download-mode entry is required for rollback.
