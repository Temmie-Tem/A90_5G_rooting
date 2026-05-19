# Native Init v290 Binder Devnode Feasibility Plan

- date: `2026-05-19`
- scope: read-only Binder devnode feasibility inventory
- baseline device build: `A90 Linux init 0.9.60 (v261)`
- target artifact: `scripts/revalidation/wifi_binder_devnode_feasibility.py`

## Summary

v289 proved that Binder kernel support is present but native init does not expose
`/dev/binder`, `/dev/hwbinder`, or `/dev/vndbinder`. v290 narrows the next step:
derive exact Binder character-device metadata from read-only kernel surfaces and
produce a guarded devnode creation plan.

v290 does not create device nodes. It does not mount binderfs, issue Binder
ioctls, start service managers, or execute Wi-Fi daemons. The goal is to decide
whether a later v291 can safely run a narrowly-scoped private devnode smoke.

## Reference Notes

- Android exposes three Binder domains: `/dev/binder`, `/dev/hwbinder`, and
  `/dev/vndbinder`. Android common kernels normally set
  `CONFIG_ANDROID_BINDER_DEVICES="binder,hwbinder,vndbinder"`:
  https://source.android.com/docs/core/architecture/hidl/binder-ipc?hl=en
- These Binder devices are registered as Linux misc devices. The misc-device
  framework assigns or records a minor number at registration time:
  https://docs.kernel.org/6.2/driver-api/misc_devices.html
- binderfs is a separate dynamic allocation model requiring a binderfs mount and
  `BINDER_CTL_ADD`; v289 showed binderfs is not available on this device, and
  v290 does not attempt it:
  https://docs.kernel.org/6.0/admin-guide/binderfs.html

## Inputs

- v289 report/evidence:
  - `tmp/wifi/v289-binder-service-manager-live-20260519-135726/manifest.json`
- current live native cmdv1 read-only captures:
  - `/proc/misc`
  - `/sys/class/misc/binder/dev`
  - `/sys/class/misc/hwbinder/dev`
  - `/sys/class/misc/vndbinder/dev`
  - `/dev/binder`, `/dev/hwbinder`, `/dev/vndbinder`
  - `/proc/mounts`
  - native version/status

## Checks

| Check | Meaning |
| --- | --- |
| v289 decision | previous blocker is exactly `binder-kernel-present-devnodes-missing` |
| sysfs misc `dev` attr | kernel-published `major:minor` for each Binder device |
| `/proc/misc` minor | cross-check misc minor for each Binder device |
| `/dev` current state | confirm nodes are still absent before proposing any action |
| major/minor consistency | reject if sysfs and `/proc/misc` disagree |
| proposed commands | emit non-executed `mknod -m 0600` candidates for later review |

## Guardrails

- No `mknod`.
- No binderfs mount.
- No Binder ioctl or open smoke.
- No service-manager execution.
- No Wi-Fi daemon execution.
- No QMI/QRTR packet.
- No Wi-Fi scan/connect/link-up/credential/DHCP/routing.
- No rfkill/ICNSS writes.
- No Android partition write.

## Expected Decisions

PASS inventory decisions:

- `binder-devnode-feasibility-ready`
- `binder-devnode-plan-ready`
- `binder-devnodes-already-present`

Blocked/error decisions:

- `binder-devnode-input-missing`
- `binder-devnode-metadata-mismatch`
- `binder-devnode-native-capture-failed`

## Validation

Static:

```bash
python3 -m py_compile \
  scripts/revalidation/wifi_binder_devnode_feasibility.py \
  scripts/revalidation/wifi_binder_service_manager_feasibility.py \
  scripts/revalidation/a90ctl.py
git diff --check
```

Live read-only:

```bash
python3 scripts/revalidation/wifi_binder_devnode_feasibility.py \
  --out-dir tmp/wifi/v290-binder-devnode-live-$(date +%Y%m%d-%H%M%S) \
  run
```

## Acceptance

- The tool derives exact Binder `major:minor` metadata from sysfs.
- `/proc/misc` minors match the sysfs minors.
- The tool emits the candidate devnode paths and commands without executing
  them.
- The result gives a concrete v291 choice:
  - approved temporary `/dev` node creation plus open-only Binder smoke, or
  - stop Binder/HAL path and continue non-HAL CNSS diagnostics.
