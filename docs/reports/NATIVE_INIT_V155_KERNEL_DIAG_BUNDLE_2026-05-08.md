# Native Init v155 Kernel Diagnostics Bundle Report

Date: `2026-05-08`
Version: `A90 Linux init 0.9.55 (v155)` / `0.9.55 v155 KERNEL DIAG BUNDLE`
Baseline: `A90 Linux init 0.9.54 (v154)`

## Summary

- Added host `kernel_diag_bundle.py` read-only evidence bundle.
- Bundles `kernelinv`, `diag`, `longsoak`, `exposure`, `wifiinv`, and `wififeas` transcripts into one private directory.
- Kept device-side probing policy unchanged from v154: no pstore/tracefs mounts, no watchdog open, no tracing enable, no Wi-Fi or network service mutation.

## Artifacts

| Artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v155` | `0264a77c01f393cc623cbf0082a4e7619dad11fc511c407e2b4e9a02ac1c6c26` |
| `stage3/ramdisk_v155.cpio` | `f287f31446b9e2a1789fab00e04de5b8f4e3ae146598f438bbf9214f2c859b44` |
| `stage3/boot_linux_v155.img` | `a13d2bec1e2036ccfaf5ca685c5bbca78dccaf10c38f98e827732a7c62240dbe` |

## Validation

- Static ARM64 build for `init_v155` — PASS.
- Marker checks for `A90 Linux init 0.9.55 (v155)`, `A90v155`, and `0.9.55 v155 KERNEL DIAG BUNDLE` — PASS.
- `git diff --check` and host Python `py_compile` — PASS.
- Real-device flash with `native_init_flash.py` and cmdv1 version/status verify — PASS.
- `kernel_diag_bundle.py --expect-version "A90 Linux init 0.9.55 (v155)"` — `PASS bundle=tmp/kerneldiag/a90-kerneldiag-v155-bundle failed_commands=0`.
- `kernel_inventory_collect.py --expect-version "A90 Linux init 0.9.55 (v155)"` — PASS.
- `native_integrated_validate.py --expect-version "A90 Linux init 0.9.55 (v155)"` — `PASS commands=25`.

## Notes

- This is a host tooling and evidence packaging version; native runtime behavior is intentionally unchanged from v154 except for version/changelog markers.
- The v155 bundle is the input artifact for v156 thermal/power sensor mapping and later pstore/watchdog/tracefs feasibility decisions.
