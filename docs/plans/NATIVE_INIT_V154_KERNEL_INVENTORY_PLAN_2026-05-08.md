# Native Init v154 Kernel Capability Inventory Plan

Target: `A90 Linux init 0.9.54 (v154)` / `0.9.54 v154 KERNEL INVENTORY`
Baseline: `A90 Linux init 0.9.53 (v153)`
Date: `2026-05-08`

## Summary

v154 returns to the kernel capability track that was paused for v153 security work.
The goal is a strictly read-only kernel inventory layer that records which stock
Android kernel facilities are available before choosing later pstore, tracefs,
watchdog, thermal, power, or Wi-Fi work.

## Scope

- Add `a90_kernelinv.c/h`.
- Add shell command `kernelinv [summary|full|paths]`.
- Add `kernelinv` summary to `status` and `bootstatus`.
- Add host collector `scripts/revalidation/kernel_inventory_collect.py` with private `0700/0600` output handling.
- Collect only passive evidence:
  - `/proc/config.gz` existence, mode, size, gzip magic.
  - `/proc/filesystems` support for pstore, tracefs, debugfs, cgroup, cgroup2, bpf.
  - `/proc/mounts` state for pstore, tracefs, debugfs, configfs, cgroup, cgroup2.
  - `/proc/cgroups` controller and enabled counts.
  - `/sys/fs/pstore`, `/sys/kernel/tracing` presence and entry counts.
  - `/sys/class/thermal`, `/sys/class/power_supply`, `/sys/class/watchdog` counts.
  - USB gadget ACM/ADB/UDC status via existing USB gadget API.

## Non-Goals

- Do not mount pstore, tracefs, debugfs, cgroup, or cgroup2.
- Do not open `/dev/watchdog*`.
- Do not enable tracing.
- Do not start/stop NCM, tcpctl, rshell, ADB, Wi-Fi, or Android services.
- Do not dump `/proc/config.gz` raw binary over cmdv1.

## Validation

- Static ARM64 build with `a90_kernelinv.c` included.
- `strings` marker check for `A90 Linux init 0.9.54 (v154)`, `A90v154`, and `0.9.54 v154 KERNEL INVENTORY`.
- `git diff --check`.
- Host Python `py_compile` for flash/control/collector scripts.
- Real-device flash with `native_init_flash.py` and cmdv1 `version/status` verify.
- Device commands: `kernelinv full`, `kernelinv paths`, `bootstatus`, `selftest verbose`, `exposure guard`.
- Host collector: `kernel_inventory_collect.py --expect-version "A90 Linux init 0.9.54 (v154)"`.
- Regression: `native_integrated_validate.py --expect-version "A90 Linux init 0.9.54 (v154)"`.

## Next

If v154 passes, v155 should bundle `kernelinv`, `diag`, `longsoak`, `exposure`,
`wifiinv`, and `wififeas` evidence into a single kernel diagnostics bundle.
