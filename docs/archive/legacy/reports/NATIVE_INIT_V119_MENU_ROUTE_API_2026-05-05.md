# A90 Native Init v119 Menu Route API

Date: 2026-05-05
Build: `A90 Linux init 0.9.19 (v119)`
Marker: `0.9.19 v119 MENU ROUTE API`

## Summary

v119 reduces menu routing duplication by adding `a90_menu` route helpers and removing the long About/Changelog case block from the v119 menu controller include file. App renderers and menu UX remain unchanged.

## Changes

- Added `a90_menu_action_opens_app()` to route action-to-app selection through `a90_menu.c/h`.
- Added `a90_menu_app_is_changelog()` and simplified `a90_menu_app_is_about()` to avoid stale changelog category lists.
- Removed the long changelog/About `case` list from `v119/40_menu_apps.inc.c`.
- Added About/changelog entry `0.9.19 v119 MENU ROUTE API`.
- Preserved nonblocking `screenmenu`, foreground `blindmenu`, power-page busy gate, displaytest/cutoutcal, and input app behavior.

## Artifacts

| artifact | sha256 |
|---|---|
| `stage3/linux_init/init_v119` | `0994d7817f82e6f41d3d8bdf6cbc32d22a30cb541501a0358ffa53117b9cf220` |
| `stage3/ramdisk_v119.cpio` | `0b2bed4591a07bbdb4f8fa8f25fa1d512963be7ad08b82d066af345f95576e94` |
| `stage3/boot_linux_v119.img` | `409759a4aa83d89c492cb62d328f9047db2d0b29731d6925c65595d444643969` |
| `tmp/soak/v119-quick-soak.txt` | `4d02c7f1a4755ff3579a9b0287e5716aea29c2b0f58ce4fff9bf1c64ed0f2504` |

## Validation

### Static

- `aarch64-linux-gnu-gcc -static -Os -Wall -Wextra` — PASS
- `strings` marker check for `A90 Linux init 0.9.19 (v119)`, `A90v119`, `0.9.19 v119 MENU ROUTE API` — PASS
- `git diff --check` — PASS
- host Python `py_compile` for flash/control scripts — PASS
- `rg` confirmed v119 menu include no longer contains the long changelog/About case block — PASS

### Flash

Command:

```sh
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v119.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.19 (v119)" \
  --verify-protocol auto
```

Result: PASS

Evidence:

- local image marker and SHA256 verified
- TWRP push and remote SHA256 verified
- boot partition prefix SHA256 matched image SHA256
- post-boot `cmdv1 version/status` PASS with `rc=0 status=ok`

### Runtime Regression

- `selftest verbose` — PASS (`pass=11 warn=0 fail=0`)
- `cmdmeta` — PASS
- `screenmenu` — PASS, nonblocking
- `status` while menu visible — PASS
- `hide` — PASS
- `displaytest safe` — PASS
- `cutoutcal` — PASS
- `statushud` — PASS
- `native_soak_validate.py --cycles 3 --sleep 2` — PASS (`cycles=3 commands=14`)

Note: `inputmonitor 0` was intentionally cancelled with `q` during validation because it is an infinite monitor mode; bounded automated regression should not use `0` for that command.

## Next

Proceed to v120 `COMMAND GROUP API`:

- split low-risk command group metadata/wrappers out of the monolithic shell dispatch path,
- keep `cmdv1/cmdv1x`, command table, and shell loop semantics stable,
- validate storage/runtime/helper/userland/network observer command groups.
