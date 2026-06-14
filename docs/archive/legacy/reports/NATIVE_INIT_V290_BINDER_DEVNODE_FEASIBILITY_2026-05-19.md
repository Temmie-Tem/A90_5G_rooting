# Native Init v290 Binder Devnode Feasibility

- date: `2026-05-19`
- scope: read-only Binder devnode feasibility inventory
- baseline device build: `A90 Linux init 0.9.60 (v261)`
- plan: `docs/plans/NATIVE_INIT_V290_BINDER_DEVNODE_FEASIBILITY_PLAN_2026-05-19.md`
- tool: `scripts/revalidation/wifi_binder_devnode_feasibility.py`
- evidence:
  - plan mode: `tmp/wifi/v290-binder-devnode-plan/`
  - live mode: `tmp/wifi/v290-binder-devnode-live-20260519-140441/`

## Result

- decision: `binder-devnode-plan-ready`
- pass: `True`
- reason: Binder misc metadata is consistent and non-executed devnode
  candidates were produced.

## Validation

Static validation passed:

```bash
python3 -m py_compile \
  scripts/revalidation/wifi_binder_devnode_feasibility.py \
  scripts/revalidation/wifi_binder_service_manager_feasibility.py \
  scripts/revalidation/a90ctl.py
git diff --check
```

Plan mode passed:

```bash
python3 scripts/revalidation/wifi_binder_devnode_feasibility.py \
  --out-dir tmp/wifi/v290-binder-devnode-plan \
  plan
```

Live read-only mode passed:

```bash
python3 scripts/revalidation/wifi_binder_devnode_feasibility.py \
  --out-dir tmp/wifi/v290-binder-devnode-live-20260519-140441 \
  run
```

## Devnode Candidates

| name | path | sysfs major:minor | `/proc/misc` minor | status | non-executed candidate |
| --- | --- | --- | --- | --- | --- |
| `binder` | `/dev/binder` | `10:81` | `81` | ready | `mknod -m 0600 /dev/binder c 10 81` |
| `hwbinder` | `/dev/hwbinder` | `10:80` | `80` | ready | `mknod -m 0600 /dev/hwbinder c 10 80` |
| `vndbinder` | `/dev/vndbinder` | `10:79` | `79` | ready | `mknod -m 0600 /dev/vndbinder c 10 79` |

## Interpretation

v289 established that Binder kernel support is present and the native `/dev`
nodes are absent. v290 confirms the exact registered misc-device metadata from
two independent read-only surfaces:

- `/sys/class/misc/*/dev` publishes `10:81`, `10:80`, and `10:79`.
- `/proc/misc` lists `binder`, `hwbinder`, and `vndbinder` with matching minor
  numbers.

This makes a later temporary devnode smoke feasible. It still does not prove
that Android service managers, SELinux policy, property runtime, HAL
registration, or `wificond` can run under native init.

## Guardrails Kept

- no `mknod`
- no binderfs mount
- no Binder ioctl or open smoke
- no service-manager execution
- no Wi-Fi daemon execution
- no QMI/QRTR packet
- no Wi-Fi scan/connect/link-up/credential/DHCP/routing
- no rfkill/ICNSS writes
- no Android partition write

## Next

- v291 should plan a temporary Binder devnode creation and cleanup smoke.
- v291 must make the non-read-only step explicit:
  - create only `/dev/binder`, `/dev/hwbinder`, `/dev/vndbinder`
  - use the v290-derived major/minor values
  - verify node existence
  - optionally run open-only static helper smoke
  - remove the temporary nodes or reboot to clear ramdisk `/dev`
- Do not start service managers or Wi-Fi HALs in v291.
