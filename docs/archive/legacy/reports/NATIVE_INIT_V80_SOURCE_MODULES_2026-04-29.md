# Native Init v80 Source Modules Report (2026-04-29)

## Summary

- Version: `A90 Linux init 0.8.11 (v80)`
- Source entrypoint: `stage3/linux_init/init_v80.c`
- Module directory: `stage3/linux_init/v80/`
- Boot image: `stage3/boot_linux_v80.img`
- Goal: split the growing PID1 source into functional modules without changing the runtime model or exporting static PID1 internals yet.

## Change

- Added an include-based source layout for the first safe modularization pass.
- Kept one static `/init` binary and one C translation unit at compile time.
- Preserved existing static globals and helper visibility to avoid behavior drift.
- Preserved `stage3/linux_init/init_v79.c` as the previous field-verified monolithic source.
- Added on-device changelog entry: `0.8.11 v80 SOURCE MODULES`.

## Module Layout

- `stage3/linux_init/init_v80.c` — small entrypoint that includes modules in dependency order.
- `stage3/linux_init/v80/00_prelude.inc.c` — headers, version constants, global state, shared structs, early prototypes.
- `stage3/linux_init/v80/10_core_log_console.inc.c` — common helpers, native log, timeline, console, early device-node helpers.
- `stage3/linux_init/v80/20_device_display.inc.c` — input/DRM/fb discovery and KMS drawing primitives.
- `stage3/linux_init/v80/30_status_hud.inc.c` — sensor snapshots, status HUD, watch/autohud lifecycle.
- `stage3/linux_init/v80/40_menu_apps.inc.c` — screen menu, apps, input monitor, display test, changelog/about UI.
- `stage3/linux_init/v80/50_boot_services.inc.c` — base mounts, cache mount, USB ACM gadget setup.
- `stage3/linux_init/v80/60_shell_basic_commands.inc.c` — basic shell/status/filesystem commands.
- `stage3/linux_init/v80/70_storage_android_net.inc.c` — SD boot storage, mountsd, Android/adbd helpers, netservice, recovery.
- `stage3/linux_init/v80/80_shell_dispatch.inc.c` — command table, cmdv1/cmdv1x protocol, shell loop.
- `stage3/linux_init/v80/90_main.inc.c` — PID1 boot sequence and handoff into the shell loop.

## Artifacts

- `stage3/linux_init/init_v80`
  - SHA256 `f8ad48229cc96cc9a580dbf54b6a5aad847499fa1b9ca5abc517523bbf34292a`
- `stage3/ramdisk_v80.cpio`
  - SHA256 `8d8c4485ae2d65dfcfff3c867b75dba712fa45b28738dca665af1051b24c6fed`
- `stage3/boot_linux_v80.img`
  - SHA256 `15a23e7485cc08e3eb46aa515ddc341ba2b14b115415b1216b805947f9612181`

## Local Validation

- Static ARM64 build with `-Wall -Wextra` — PASS
- Strip and ELF/file check — PASS
- v80 ramdisk and boot image generation using v79 kernel/header args — PASS
- Boot image marker strings:
  - `A90 Linux init 0.8.11 (v80)`
  - `A90v80`
  - `0.8.11 v80 SOURCE MODULES`
  - `0.8.10 v79 BOOT SD PROBE`

## Device Validation

- Flash `stage3/boot_linux_v80.img` from TWRP recovery — PASS
- Boot partition prefix SHA256 matched local image — PASS
- Post-boot `cmdv1 version` and `cmdv1 status` verification — PASS
- `storage` through the bridge — PASS
  - `backend=sd`
  - `root=/mnt/sdext/a90`
  - `fallback=no`
  - `expected=yes`
  - `rw=yes`
  - `uuid=c6c81408-f453-11e7-b42a-23a2c89f58bc`
- `mountsd status` through the bridge — PASS
  - `match=yes`
  - `state=mounted`
  - `mode=rw`
  - `size=59968MB`
  - `avail=56863MB`
- Shell/display regression through the bridge — PASS
  - `help`
  - `inputlayout`
  - `displaytest safe`
  - `statushud`
  - `logpath`
  - `timeline`
  - `autohud 2`

`screenmenu` remains a manual visual/input check because it intentionally enters a blocking physical-button UI.

## Current Baseline

`0.8.11 (v80)` is the latest field-verified native init build.
