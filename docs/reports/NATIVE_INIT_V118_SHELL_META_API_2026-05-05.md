# A90 Native Init v118 Shell Metadata API

Date: 2026-05-05
Build: `A90 Linux init 0.9.18 (v118)`
Marker: `0.9.18 v118 SHELL META API`

## Summary

v118 starts the PID1 slimdown work by moving command metadata/count/report helpers into `a90_shell.c/h`. Command handler bodies, the command table, `cmdv1/cmdv1x`, and shell loop behavior remain in the include tree.

## Changes

- Added `struct a90_shell_command_stats` and command stats helpers to `a90_shell.c/h`.
- Added command flag formatting and inventory printing helpers to `a90_shell.c/h`.
- Added read-only `cmdmeta [verbose]` command using the new shell metadata API.
- Updated help/About/changelog for `0.9.18 v118 SHELL META API`.
- Preserved existing command result framing, unknown command handling, menu busy policy, and raw-control reboot/recovery semantics.

## Artifacts

| artifact | sha256 |
|---|---|
| `stage3/linux_init/init_v118` | `291106ab7d477714b41966d232a5036013880a2d9b27f9df6927542de4f7779a` |
| `stage3/ramdisk_v118.cpio` | `3680d035cdfc9fe2cbeb8d93952de1881ebdcb7ff3e2f1701e36075fa2bf0bcc` |
| `stage3/boot_linux_v118.img` | `e76353265c58af0e606b2d22d3eb5e2bfd7b4a6793a8892540f3e37331610972` |
| `tmp/soak/v118-quick-soak.txt` | `721b3fb4025f30829c1c5083559ec642d5da357c33482013927fe77a9a009757` |
| `tmp/soak/v118-cmdmeta-verbose.txt` | `1cb527e811959d703594a1bccfa3ae7d9771ef537707fac45975910771034f95` |
| `tmp/soak/v118-unknown.txt` | `3086bd5fe446d541fb26dd34497c35a5232201b74327e5a2e96a69bae24a716a` |

## Validation

### Static

- `aarch64-linux-gnu-gcc -static -Os -Wall -Wextra` — PASS
- `strings` marker check for `A90 Linux init 0.9.18 (v118)`, `A90v118`, `0.9.18 v118 SHELL META API`, `cmdmeta` — PASS
- `git diff --check` — PASS
- host Python `py_compile` for flash/control scripts — PASS

### Flash

Command:

```sh
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v118.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.18 (v118)" \
  --verify-protocol auto
```

Result: PASS

Evidence:

- local image marker and SHA256 verified
- TWRP push and remote SHA256 verified
- boot partition prefix SHA256 matched image SHA256
- post-boot `cmdv1 version/status` PASS with `rc=0 status=ok`

### Runtime Regression

- `cmdmeta` — PASS (`total=80 display=11 blocking=12 dangerous=7 background=9 no_done=3`)
- `cmdmeta verbose` — PASS, command inventory written to `tmp/soak/v118-cmdmeta-verbose.txt`
- `help` — PASS
- unknown `cmdv1 not_a_command` — PASS (`status=unknown`, `rc=-2`, `errno=2`)
- `last` after unknown command — PASS
- `bootstatus` — PASS
- `selftest verbose` — PASS (`pass=11 warn=0 fail=0`)
- `statushud` — PASS
- `screenmenu` while shell remains responsive — PASS
- `status` with menu visible — PASS
- `hide` — PASS
- `native_soak_validate.py --cycles 3 --sleep 2` — PASS (`cycles=3 commands=14`)

## Next

Proceed to v119 `MENU ROUTE API`:

- reduce repeated menu/changelog dispatch logic through `a90_menu` helpers,
- keep screen app renderers unchanged,
- preserve nonblocking `screenmenu`, foreground `blindmenu`, and power-page busy gate behavior.
