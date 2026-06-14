# Native Init v83 Console API Report (2026-04-29)

## Summary

- Version: `A90 Linux init 0.8.14 (v83)`
- Source entrypoint: `stage3/linux_init/init_v83.c`
- Module directory: `stage3/linux_init/v83/`
- New console API files:
  - `stage3/linux_init/a90_console.h`
  - `stage3/linux_init/a90_console.c`
- Boot image: `stage3/boot_linux_v83.img`
- Goal: move USB ACM console fd ownership, attach/reattach, readline, cancel polling, and console write/printf behind a real `.c/.h` API while keeping shell, cmdv1/cmdv1x, storage, display, and netservice behavior stable.

## Change

- Added `a90_console.c/h` as the owner of `console_fd` and `last_console_reattach_ms`.
- Exposed console behavior through narrow APIs:
  - `a90_console_wait_tty()`
  - `a90_console_attach()`
  - `a90_console_reattach()`
  - `a90_console_printf()`
  - `a90_console_write()`
  - `a90_console_readline()`
  - `a90_console_dup_stdio()`
  - `a90_console_read_cancel_event()`
  - `a90_console_poll_cancel()`
  - `a90_console_cancelled()`
- Added `a90_console_drain_input()` to preserve the old attach-time serial input flush behavior without exposing the raw fd.
- Replaced v83 include-tree direct console use with API calls:
  - `cprintf` → `a90_console_printf`
  - `attach_console` → `a90_console_attach`
  - `reattach_console` → `a90_console_reattach`
  - `read_line` → `a90_console_readline`
  - `poll_console_cancel` → `a90_console_poll_cancel`
  - `read_console_cancel_event` → `a90_console_read_cancel_event`
  - `command_cancelled` → `a90_console_cancelled`
  - `write_all(console_fd, ...)` → `a90_console_write(...)`
  - child `dup2(console_fd, ...)` → `a90_console_dup_stdio()`
- Kept shell dispatch, `cmdv1/cmdv1x`, storage, KMS/HUD/menu, and netservice in the v83 include tree.
- Added on-device changelog entry: `0.8.14 v83 CONSOLE API`.

## Artifacts

- `stage3/linux_init/init_v83`
  - SHA256 `0ae4f025d1c9bff5cb2bd89f42a15d2065c62eac18aa568cc13b9e8b0812e8e5`
- `stage3/ramdisk_v83.cpio`
  - SHA256 `28d5cb735da2b3180df7f8aa100a3a1b47c5ec6f9870363a9f20b82d317cd878`
- `stage3/boot_linux_v83.img`
  - SHA256 `1a9bdc7582485c95eee107753627e66aa4d2f53ed03bdb3039da18fab027c124`

## Local Validation

- Static ARM64 multi-source build with `-Wall -Wextra` — PASS
- Strip and ELF/file check — PASS
- v83 ramdisk and boot image generation using v82 kernel/header args — PASS
- Boot image marker strings — PASS
  - `A90 Linux init 0.8.14 (v83)`
  - `A90v83`
  - `0.8.14 v83 CONSOLE API`
  - `0.8.13 v82 LOG TIMELINE API`
- Direct fd cleanup check — PASS
  - v83 include tree no longer references `console_fd`, `cprintf`, `attach_console`, `reattach_console`, `read_line`, or old cancel helpers.
- `python3 -m py_compile scripts/revalidation/a90ctl.py scripts/revalidation/native_init_flash.py` — PASS
- `git diff --check` — PASS

## Device Validation

- Native-init to recovery transition through bridge — PASS
- Flash `stage3/boot_linux_v83.img` from TWRP recovery — PASS
- Boot partition prefix SHA256 matched local image — PASS
  - `1a9bdc7582485c95eee107753627e66aa4d2f53ed03bdb3039da18fab027c124`
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
- Console regression — PASS
  - `cat /mnt/sdext/a90/.a90-native-id`
  - `logcat`
  - `run /bin/a90sleep 1`
  - `cpustress 3 2`
  - `watchhud 1 2`
- Cancel regression — PASS
  - `run /bin/a90sleep 10` cancelled by `q` with `rc=-125` / `errno=125`.
- Reattach regression — PASS
  - `reattach`
  - `usbacmreset` followed by `cmdv1 version`

## Verified Runtime Snapshot

- `version`: `A90 Linux init 0.8.14 (v83)`
- `bootstatus`: `BOOT OK shell 3S`, `timeline_entries: 16/32`
- `logpath`: `/mnt/sdext/a90/logs/native-init.log`, ready `yes`
- `storage`: backend `sd`, root `/mnt/sdext/a90`, fallback `no`
- `mountsd status`: UUID match `yes`, mounted `rw`, available `56863MB`

## Current Baseline

`0.8.14 (v83)` is the latest field-verified native init build.

The next module-extraction candidate should focus on the shell/cmdproto boundary while keeping the v83 console API stable.
