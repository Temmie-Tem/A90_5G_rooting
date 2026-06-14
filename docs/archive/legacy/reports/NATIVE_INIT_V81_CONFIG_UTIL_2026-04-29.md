# Native Init v81 Config/Util API Report (2026-04-29)

## Summary

- Version: `A90 Linux init 0.8.12 (v81)`
- Source entrypoint: `stage3/linux_init/init_v81.c`
- Module directory: `stage3/linux_init/v81/`
- New base API files:
  - `stage3/linux_init/a90_config.h`
  - `stage3/linux_init/a90_util.h`
  - `stage3/linux_init/a90_util.c`
- Boot image: `stage3/boot_linux_v81.img`
- Goal: start true `.c/.h` module extraction from the v80 include-module layout, beginning with the safest base layer.

## Change

- Added `a90_config.h` for shared version/path/constant definitions.
- Added `a90_util.c/h` as the first real compiled module.
- Moved common utility helpers out of the PID1 include modules:
  - `monotonic_millis()`
  - `ensure_dir()`
  - `negative_errno_or()`
  - `write_all_checked()`
  - `write_all()`
  - `read_text_file()`
  - `trim_newline()`
  - `flatten_inline_text()`
  - `read_trimmed_text_file()`
- Kept PID1 behavior stable and left high-risk modules such as shell, storage, KMS/HUD/menu, and netservice in the v81 include tree.
- Added on-device changelog entry: `0.8.12 v81 CONFIG UTIL API`.

## Artifacts

- `stage3/linux_init/init_v81`
  - SHA256 `65d2b356cbde24bfcecaa3474ee851aa49fd114e3a8665f7e93529473d855f5d`
- `stage3/ramdisk_v81.cpio`
  - SHA256 `cf4f69ce4e56cab5d924ce95278047db8689bd28d61601b20fe4d7165055971d`
- `stage3/boot_linux_v81.img`
  - SHA256 `875411a96af4dd26f9a3941440a10b1a627c5fbabd9ca16c4fbbaf2c93e372a9`

## Local Validation

- Static ARM64 multi-source build with `-Wall -Wextra` — PASS
- Strip and ELF/file check — PASS
- v81 ramdisk and boot image generation using v80 kernel/header args — PASS
- Boot image marker strings:
  - `A90 Linux init 0.8.12 (v81)`
  - `A90v81`
  - `0.8.12 v81 CONFIG UTIL API`
  - `0.8.11 v80 SOURCE MODULES`

## Device Validation

- Native-init to recovery transition through bridge — PASS
- Flash `stage3/boot_linux_v81.img` from TWRP recovery — PASS
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

## Current Baseline

`0.8.12 (v81)` is the latest field-verified native init build.

The next module-extraction candidate should focus on `a90_log.c/h` and `a90_timeline.c/h` while keeping the shell/storage/display layers stable.
