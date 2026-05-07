# Native Init v155 Kernel Diagnostics Bundle Plan

Target: `A90 Linux init 0.9.55 (v155)` / `0.9.55 v155 KERNEL DIAG BUNDLE`
Baseline: `A90 Linux init 0.9.54 (v154)`
Date: `2026-05-08`

## Summary

v155 packages the v154 kernel inventory with the existing diagnostics, long-soak,
exposure, Wi-Fi inventory, and Wi-Fi feasibility outputs. The goal is one
read-only evidence directory that can drive the next kernel-feature decisions
without manually re-running each command.

## Scope

- Copy v154 to `init_v155.c` and `v155/*.inc.c`.
- Bump version/build/changelog to `0.9.55 v155 KERNEL DIAG BUNDLE`.
- Add host collector `scripts/revalidation/kernel_diag_bundle.py`.
- Capture read-only command transcripts:
  - `version`, `status`, `bootstatus`, `selftest verbose`.
  - `kernelinv`, `kernelinv full`, `kernelinv paths`.
  - `diag full`, `diag paths`.
  - `longsoak status verbose`.
  - `exposure guard`.
  - `wifiinv refresh`, `wififeas refresh`.
- Use private output handling: bundle directory `0700`, files `0600`, no-follow symlink rejection.

## Non-Goals

- Do not add new device-side probing beyond v154 `kernelinv`.
- Do not mount pstore/tracefs/debugfs/cgroup.
- Do not open watchdog devices.
- Do not enable tracing, Wi-Fi, NCM, tcpctl, rshell, or ADB.

## Validation

- Static ARM64 build and marker check.
- `git diff --check` and Python `py_compile`.
- Real-device flash with `native_init_flash.py`.
- `kernel_diag_bundle.py --expect-version "A90 Linux init 0.9.55 (v155)"`.
- `kernel_inventory_collect.py --expect-version "A90 Linux init 0.9.55 (v155)"`.
- `native_integrated_validate.py --expect-version "A90 Linux init 0.9.55 (v155)"`.

## Next

If v155 passes, v156 should turn the existing thermal/power summary into a
full thermal zone and power-supply sensor map for long-run stability analysis.
