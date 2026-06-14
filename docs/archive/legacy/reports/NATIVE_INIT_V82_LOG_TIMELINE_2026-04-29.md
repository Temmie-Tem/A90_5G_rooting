# Native Init v82 Log/Timeline API Report (2026-04-29)

## Summary

- Version: `A90 Linux init 0.8.13 (v82)`
- Source entrypoint: `stage3/linux_init/init_v82.c`
- Module directory: `stage3/linux_init/v82/`
- New base API files:
  - `stage3/linux_init/a90_log.h`
  - `stage3/linux_init/a90_log.c`
  - `stage3/linux_init/a90_timeline.h`
  - `stage3/linux_init/a90_timeline.c`
- Boot image: `stage3/boot_linux_v82.img`
- Goal: promote log and boot timeline state out of the include-module PID1 tree into real `.c/.h` APIs while keeping console, shell, storage, display, and netservice behavior stable.

## Change

- Added `a90_log.c/h` for native log state and file output.
- Moved log path selection and fallback behavior behind API calls:
  - `a90_log_set_path()`
  - `a90_log_select_or_fallback()`
  - `a90_logf()`
  - `a90_log_path()`
  - `a90_log_ready()`
- Added `a90_timeline.c/h` for boot timeline storage, replay, probe, summary, and read-only entry access.
- Replaced v82 include-tree direct access to `native_log_ready`, `native_log_path`, and `boot_timeline` with API calls.
- Kept `console_fd`, `cprintf`, shell dispatch, `cmdv1/cmdv1x`, storage, KMS/HUD/menu, and netservice in the v82 include tree.
- Added on-device changelog entry: `0.8.13 v82 LOG TIMELINE API`.

## Artifacts

- `stage3/linux_init/init_v82`
  - SHA256 `56073411436ded0d75ce53ca2bdb70ca486201588d68dae4dff69029f34a5646`
- `stage3/ramdisk_v82.cpio`
  - SHA256 `2d22fed414f101d0bd033754f127101730a6ad928ac7e6454e93587892cd3a4f`
- `stage3/boot_linux_v82.img`
  - SHA256 `b023e1cf38c5fa1f0328030975189e99bcbb47a9715dadde1af0070badb6ab73`

## Local Validation

- Static ARM64 multi-source build with `-Wall -Wextra` — PASS
- Strip and ELF/file check — PASS
- v82 ramdisk and boot image generation using v81 kernel/header args — PASS
- Boot image marker strings — PASS
  - `A90 Linux init 0.8.13 (v82)`
  - `A90v82`
  - `0.8.13 v82 LOG TIMELINE API`
  - `0.8.12 v81 CONFIG UTIL API`
- `python3 -m py_compile scripts/revalidation/a90ctl.py scripts/revalidation/native_init_flash.py` — PASS
- `git diff --check` — PASS

## Device Validation

- Native-init to recovery transition through bridge — PASS
- Flash `stage3/boot_linux_v82.img` from TWRP recovery — PASS
- Boot partition prefix SHA256 matched local image — PASS
  - `b023e1cf38c5fa1f0328030975189e99bcbb47a9715dadde1af0070badb6ab73`
- Post-boot `cmdv1 version` and `cmdv1 status` verification — PASS
- Bridge regression — PASS
  - `version`
  - `status`
  - `logpath`
  - `timeline`
  - `bootstatus`
  - `storage`
  - `mountsd status`
  - `displaytest safe`
  - `autohud 2`

## Verified Runtime Snapshot

- `version`: `A90 Linux init 0.8.13 (v82)`
- `bootstatus`: `BOOT OK shell 3S`, `timeline_entries: 16/32`
- `logpath`: `/mnt/sdext/a90/logs/native-init.log`, ready `yes`
- `storage`: backend `sd`, root `/mnt/sdext/a90`, fallback `no`
- `mountsd status`: UUID match `yes`, mounted `rw`, available `56863MB`

## Current Baseline

`0.8.13 (v82)` is the latest field-verified native init build.

The next module-extraction candidate should focus on `console + shell + cmdproto` boundaries while keeping v82 log/timeline APIs stable.
