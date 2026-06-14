# Native Init v96 Structure Audit Report

Date: `2026-05-03`

## Summary

- Version: `A90 Linux init 0.8.27 (v96)` / `0.8.27 v96 STRUCTURE AUDIT`
- Goal: audit v95 module boundaries before adding SD runtime/userland layers.
- Result: PASS on local build, flash, `cmdv1 version/status`, selftest, storage, HUD/menu, and netservice status regression.
- User-facing feature changes: none intended.

## Artifacts

| artifact | sha256 |
|---|---|
| `stage3/linux_init/init_v96` | `2cee558e62f840dd9337ec1852d49116f4ffff99092a35bddece90f9659e65be` |
| `stage3/ramdisk_v96.cpio` | `f41140ae0c8ad45170adc2927a438c70b002985e1b8e0f493b5711998cc2fe61` |
| `stage3/boot_linux_v96.img` | `e890a3f4ac3ae59f3bff7a7307551c0545189e664e272b120198eb3b3762dacf` |

## Changes

- Copied v95 source layout to `stage3/linux_init/init_v96.c` and `stage3/linux_init/v96/*.inc.c`.
- Updated version/build markers to `0.8.27` / `v96` and boot marker strings to `A90v96`.
- Added v96 ABOUT/changelog entry and menu mapping for `0.8.27 v96 STRUCTURE AUDIT`.
- Fixed stale console reattach klog markers in `a90_console.c`:
  - old fixed string: `A90v83`
  - new dynamic marker: `A90%s` with `INIT_BUILD`
- No SD runtime, BusyBox, remote shell, service manager, or Wi-Fi functionality was added.

## Audit Findings

### Fixed

| finding | action |
|---|---|
| `a90_console.c` still logged console reattach kmsg as `A90v83` | replaced with `INIT_BUILD` based marker so future builds log the active build tag |
| v96 ABOUT/changelog needed a new top entry | added `0.8.27 v96 STRUCTURE AUDIT` in menu model and detail page |

### Intentional / False Positive

| search hit | decision |
|---|---|
| `kms_state` in `a90_kms.c` | intentionally internal static KMS state hidden behind `a90_kms_*` APIs |
| `console_fd` in `a90_console.c` | intentionally internal static console fd hidden behind `a90_console_*` APIs |
| `a90_timeline_record` call sites | public timeline API, not stale pre-module residue |
| `a90_tcpctl.c` fork/wait/kill | helper process owns its client child lifecycle; not PID1 command duplication |
| `a90_usbnet.c` fork/setsid | helper-level USB rebind behavior; not PID1 command duplication |
| hardcoded `/mnt/sdext/a90` in changelog/help text | informational UI text only; storage policy remains in `a90_storage` and `a90_config.h` |

### Deferred

| finding | deferred target |
|---|---|
| `auto_hud_loop` foreground/background child fork remains in `v96/40_menu_apps.inc.c` | v101 service manager or a smaller HUD service extraction |
| SD workspace currently has early runtime-like directories but no formal runtime root contract | v97 SD runtime root |
| helper inventory/deployment is still manual | v98 helper deployment/package manifest |

## Local Validation

- Static ARM64 build with `-Wall -Wextra`: PASS
- `readelf -d stage3/linux_init/init_v96`: no dynamic section
- `stage3/ramdisk_v96.cpio` generated with:
  - `/init`
  - `/bin/a90sleep`
  - `/bin/a90_cpustress`
- `stage3/boot_linux_v96.img` generated from v95 boot image args with ramdisk swapped.
- Marker strings present:
  - `A90 Linux init 0.8.27 (v96)`
  - `A90v96`
  - `0.8.27 v96 STRUCTURE AUDIT`
- `git diff --check`: PASS
- Host Python compile: PASS

## Device Validation

Flash command:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v96.img \
  --from-native \
  --expect-version "A90 Linux init 0.8.27 (v96)" \
  --verify-protocol auto
```

Result:

- local image marker: PASS
- remote pushed image sha256: `e890a3f4ac3ae59f3bff7a7307551c0545189e664e272b120198eb3b3762dacf`
- boot partition prefix sha256: `e890a3f4ac3ae59f3bff7a7307551c0545189e664e272b120198eb3b3762dacf`
- post-boot `cmdv1 version/status`: PASS

Regression:

| command | result |
|---|---|
| `bootstatus` | PASS, `BOOT OK shell 4.1s`, selftest `pass=8 warn=0 fail=0` |
| `selftest verbose` | PASS, 8 PASS entries |
| `storage` | PASS, SD backend `/mnt/sdext/a90`, fallback `no` |
| `mountsd status` | PASS, SD mounted rw, UUID match |
| `statushud` | PASS, framebuffer presented |
| `autohud 2` | PASS |
| `screenmenu` | PASS, nonblocking show request |
| `hide` | PASS |
| `netservice status` | PASS, disabled, `ncm0=absent`, `tcpctl=stopped` |

## Acceptance

- v95 UX behavior preserved under v96 versioning.
- Boot selftest remains known-good with `fail=0`.
- The only code cleanup is low-risk marker/version/changelog cleanup.
- v97 can start from a documented SD runtime root plan without carrying stale v83 console marker debt.
