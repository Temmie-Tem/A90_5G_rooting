# Native Init v154 Kernel Capability Inventory Report

Date: `2026-05-08`
Version: `A90 Linux init 0.9.54 (v154)` / `0.9.54 v154 KERNEL INVENTORY`
Baseline: `A90 Linux init 0.9.53 (v153)`

## Summary

- Added `a90_kernelinv.c/h` read-only kernel capability inventory module.
- Added `kernelinv [summary|full|paths]` command and wired summary into `status`/`bootstatus`.
- Added private-output host collector `scripts/revalidation/kernel_inventory_collect.py`.
- Confirmed key facilities exist without enabling them: `/proc/config.gz`, pstore support, tracefs support, cgroup/cgroup2 support, thermal zones, power supplies, watchdog class, and ACM USB gadget state.

## Artifacts

| Artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v154` | `6f35e073993d3c83944cc8e87893fe34ffff86b074e1f1702a3d01d12df2fb4b` |
| `stage3/ramdisk_v154.cpio` | `62a96ac8908d483484004d835ac8bdddb077062ef0b3e1eca2703570cbb9753a` |
| `stage3/boot_linux_v154.img` | `f3457a3f12c928f7ff90d8e2c7d58e1fa5749cebe8ed7e7ad974fea5778ed13b` |

## Device Inventory Snapshot

- `config.gz`: present `yes`, mode `0444`, size `42126`, gzip magic `yes`.
- filesystems: pstore `yes`, tracefs `yes`, debugfs `yes`, cgroup `yes`, cgroup2 `yes`, bpf `yes`.
- mounts: pstore `no`, tracefs `no`, debugfs `no`, configfs `yes`, cgroup `no`, cgroup2 `no`.
- cgroup: controllers `7`, enabled `7`.
- pstore: dir `yes`, entries `0`, mounted `no`.
- tracefs: dir `yes`, entries `0`, mounted `no`.
- thermal: zones `78`, cooling devices `15`.
- power_supply: total `10`, battery `yes`, usb `yes`, wireless `yes`, chargers `4`.
- watchdog: class devices `1`, `/dev/watchdog*` nodes absent; policy remains read-only/no-open.
- USB gadget: configfs `yes`, gadget `yes`, ACM function/link `yes`, ADB link `no`, UDC bound `a600000.dwc3`.

## Validation

- Static ARM64 build for `init_v154` — PASS.
- Boot image marker checks for `A90 Linux init 0.9.54 (v154)`, `A90v154`, and `0.9.54 v154 KERNEL INVENTORY` — PASS.
- `git diff --check` and host Python `py_compile` — PASS.
- Real-device flash with `native_init_flash.py` and cmdv1 version/status verify — PASS.
- `kernelinv full` — PASS; long `/proc/cmdline` is wrapped and marked `cmdline_truncated: yes` when capped.
- `kernelinv paths` — PASS.
- `kernel_inventory_collect.py` — `PASS ... failed_commands=0`.
- `native_integrated_validate.py --expect-version "A90 Linux init 0.9.54 (v154)"` — `PASS commands=25`.
- `selftest verbose` — `pass=11 warn=1 fail=0`.
- `exposure guard` — `guard=ok warn=0 fail=0`.

## Notes

- `/proc/config.gz` is intentionally not dumped as raw binary over cmdv1 in v154.
- pstore and tracefs are supported by the kernel but not mounted in the current native-init boot state.
- Watchdog feasibility remains read-only; opening watchdog devices is deferred because it can trigger reboot behavior.
- v155 should consume this inventory through a broader diagnostics bundle instead of re-probing each subsystem ad hoc.
