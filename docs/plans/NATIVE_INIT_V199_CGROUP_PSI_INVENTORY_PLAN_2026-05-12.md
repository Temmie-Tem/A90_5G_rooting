# v199 Plan: Cgroup / PSI Resource Control Inventory

## Summary

v199 adds a host-side, read-only cgroup and PSI inventory. The goal is to know
whether future server-style services can be observed or isolated before adding
more long-running network workloads.

## Scope

- Add `scripts/revalidation/cgroup_psi_inventory.py`.
- Decode cgroup/namespace/PSI `CONFIG_*` values from `/proc/config.gz`.
- Collect `/proc/cgroups`, `/proc/self/cgroup`, `/proc/pressure/*`, mount state,
  and common cgroup mount path presence.
- Summarize service isolation implications for `tcpctl`, `rshell`, stress, and
  helper workloads.

## Non-Goals

- Do not mount cgroup or cgroup2.
- Do not write cgroup control files.
- Do not migrate processes between cgroups.
- Do not enforce CPU/memory/I/O limits yet.

## Validation

```bash
python3 -m py_compile scripts/revalidation/cgroup_psi_inventory.py

python3 scripts/revalidation/cgroup_psi_inventory.py \
  --out tmp/cgroup-psi/v199-cgroup-psi.md \
  --json-out tmp/cgroup-psi/v199-cgroup-psi.json
```

## Acceptance

- cgroup controller and PSI evidence is captured.
- The report states whether cgroup support is mounted or only available.
- Output is private/no-follow and read-only.
