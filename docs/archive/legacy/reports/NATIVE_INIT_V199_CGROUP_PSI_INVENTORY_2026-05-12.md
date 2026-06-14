# v199 Cgroup / PSI Resource Control Inventory

## Summary

v199 inventories resource-control and pressure-observation capability without
mounting cgroup filesystems or moving processes. This is a host tooling change
only; latest verified native init remains `A90 Linux init 0.9.59 (v159)`.

## Changes

- Added `scripts/revalidation/cgroup_psi_inventory.py`.
- Reused v197 config decoding helpers from `scripts/revalidation/a90_kernel_tools.py`.
- Produced read-only runtime evidence for cgroup controllers, PSI files, cgroup
  mount state, and service-isolation implications.

## Validation

```bash
python3 -m py_compile scripts/revalidation/cgroup_psi_inventory.py
```

Result: PASS.

```bash
python3 scripts/revalidation/cgroup_psi_inventory.py \
  --out tmp/cgroup-psi/v199-cgroup-psi.md \
  --json-out tmp/cgroup-psi/v199-cgroup-psi.json
```

Result: PASS.

Evidence:

- `tmp/cgroup-psi/v199-cgroup-psi.md`
- `tmp/cgroup-psi/v199-cgroup-psi.json`

Summary:

- Decision: `supported-unmounted-psi-present`
- Enabled controllers: `cpuset`, `cpu`, `cpuacct`, `schedtune`, `blkio`,
  `memory`, `freezer`
- PSI: CPU, memory, and I/O pressure files are present and readable.
- Mount state: no cgroup/cgroup2 mount in current native init runtime.
- `CONFIG_CGROUP_PIDS=n` and `CONFIG_CGROUP_DEVICE=n`, so PID-count and device
  controller policies are not available through kernel cgroup controllers.

## Acceptance

- Resource-control and PSI evidence is captured read-only.
- Future service isolation should start with an explicit cgroup mount plan before
  enforcing limits.
- No cgroup mount, cgroup write, process migration, or service lifecycle change
  was performed.

## Next

v200 should turn tracefs/pstore availability into a safe debug observability
plan for future USB/serial/NCM failure diagnosis.
