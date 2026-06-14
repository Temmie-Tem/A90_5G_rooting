# Native Init v102 Diagnostics Report

Date: `2026-05-03`

## Summary

- Version: `A90 Linux init 0.9.2 (v102)` / `0.9.2 v102 DIAGNOSTICS`.
- Baseline: v101 minimal service manager.
- v102 adds a read-only `diag [summary|full|bundle|paths]` command.
- v102 adds `scripts/revalidation/diag_collect.py`, a serial-first host collector.
- Diagnostics are intentionally non-destructive: no USB rebind, no service lifecycle change, no mount mutation, no token display by default.

## Key Changes

- Added `stage3/linux_init/init_v102.c` and `stage3/linux_init/v102/*.inc.c`.
- Updated `stage3/linux_init/a90_config.h` to `0.9.2` / `v102`.
- Added `stage3/linux_init/a90_diag.c/h` with:
  - `a90_diag_print_summary()`
  - `a90_diag_print_full()`
  - `a90_diag_write_bundle()`
  - `a90_diag_default_dir()`
- Added `diag [summary|full|bundle|paths]` to help and shell command table.
- Added `scripts/revalidation/diag_collect.py` for host-side serial bridge collection.
- Updated ABOUT/changelog top entry to `0.9.2 v102 DIAGNOSTICS`.

## Artifacts

| Artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v102` | `49499e5da3c84ef50996655605e06d1f33cd514862aeb361a97411e9b9db154a` |
| `stage3/ramdisk_v102.cpio` | `375110ae184997fcf5334704ed1a8f738a3088e7e150467e9fc995f01ff86780` |
| `stage3/boot_linux_v102.img` | `aca7aef3077334eb4b7e0f61fdfa27943b8ca23736271b10dd414f8029d1c49d` |

Ramdisk entries:

```text
/init
/bin/a90sleep
/bin/a90_cpustress
/bin/a90_rshell
```

## Static Validation

- Static ARM64 init build with `-Wall -Wextra` — PASS.
- `stage3/ramdisk_v102.cpio` and `stage3/boot_linux_v102.img` generated from v101 boot args with only ramdisk replaced — PASS.
- Boot image markers found:
  - `A90 Linux init 0.9.2 (v102)`
  - `A90v102`
  - `0.9.2 v102 DIAGNOSTICS`
  - `diag [summary|full|bundle|paths]`
- `git diff --check` — PASS.
- Host Python `py_compile` for `a90ctl.py`, `native_init_flash.py`, `rshell_host.py`, `helper_deploy.py`, `diag_collect.py` — PASS.
- v102 stale marker scan for `A90v101`, `mark_step(...v101)`, `init_v101`, and mixed version strings — PASS.

## Flash Validation

Command:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v102.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.2 (v102)" \
  --verify-protocol auto
```

Result:

- Local image marker and SHA256 check — PASS.
- TWRP push and remote SHA256 check — PASS.
- boot partition prefix SHA256 matched `stage3/boot_linux_v102.img` — PASS.
- Post-boot `cmdv1 version/status` — PASS.

## Device Validation

- `version`: PASS, `A90 Linux init 0.9.2 (v102)`.
- `status`: PASS, `selftest pass=11 warn=0 fail=0`, SD runtime, autohud running, netservice disabled, rshell stopped.
- `bootstatus`: PASS.
- `selftest verbose`: PASS, `pass=11 warn=0 fail=0`.
- `diag`: PASS, compact summary includes version, bootstatus, selftest, storage, runtime, helpers, userland, service, network, rshell.
- `diag full`: PASS, verbose report includes timeline, selftest entries, helper/userland entries, `/proc/mounts`, `/proc/partitions`, and native log tail.
- `diag paths`: PASS, default dir `/mnt/sdext/a90/logs`, log path `/mnt/sdext/a90/logs/native-init.log`.
- `diag bundle`: PASS, wrote `/mnt/sdext/a90/logs/a90-diag-30812.txt` with mode `0644` and size `25236` bytes.
- `diag_collect.py --out tmp/diag/v102-smoke.txt`: PASS, collected host metadata and `diag full` output.
- `diag_collect.py --device-bundle --boot-image stage3/boot_linux_v102.img --out tmp/diag/v102-bundle.txt`: PASS, captured boot image SHA and device bundle path `/mnt/sdext/a90/logs/a90-diag-64094.txt`.
- `stat /mnt/sdext/a90/logs/a90-diag-64094.txt`: PASS, mode `0644`, size `25236` bytes.
- `service list`: PASS.
- `storage`: PASS.
- `runtime`: PASS.
- `statushud`: PASS.
- `autohud 2`: PASS.
- `screenmenu`: PASS, nonblocking.
- `hide`: PASS.
- `cpustress 3 2`: PASS, `/bin/a90_cpustress` completed.

## Notes

- The host collector reports `git_dirty=yes` during validation because v102 source changes were intentionally uncommitted while testing.
- A mistyped host check sent `--allow-error` as a device argv to `stat`; this was a host invocation mistake only and did not affect device state.
- NCM/tcpctl/rshell network checks were left optional and were not required for v102 acceptance because v102 diagnostics are serial-first and read-only.

## Current Baseline

`A90 Linux init 0.9.2 (v102)` is now the latest verified native init baseline.

Next planned target: v103 Wi-Fi read-only inventory.
