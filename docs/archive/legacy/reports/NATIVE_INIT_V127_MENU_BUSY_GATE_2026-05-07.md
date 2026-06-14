# A90 Native Init v127 Menu Busy Gate Hardening

Date: 2026-05-07
Build: `A90 Linux init 0.9.27 (v127)`
Marker: `0.9.27 v127 MENU BUSY GATE`

## Summary

v127 closes F023 by replacing the non-power auto-menu allow-by-default busy gate
with a deny-by-default allowlist. While the screen menu is visible, observation
and menu-control commands remain available, but root side-effect commands are
blocked until the operator sends `hide`/`hidemenu`/`resume` or uses the menu
itself.

This is intentionally the conservative first pass. Subcommand-aware relaxations
such as allowing only `diag summary` or `mountsd status` can be considered later,
but v127 prioritizes a clear security boundary.

## Changes

- Added `command_allowed_during_menu()` in `a90_controller.c` for non-power
  menu-active states.
- Changed non-power menu-active policy from allow-by-default to explicit
  allowlist.
- Preserved menu-control commands such as `screenmenu`, `menu`, `hide`,
  `hidemenu`, `resume`, and `stophud`.
- Kept core observation commands such as `status`, `storage`, `timeline`, and
  `logpath` usable while the menu is visible.
- Blocked side-effect commands such as `run`, `runandroid`, `writefile`,
  `mountfs`, `mknodc`, and `mknodb` while the menu is visible.
- Bumped version metadata to `0.9.27 (v127)` and added the changelog entry.

## Finding Coverage

| finding | result |
|---|---|
| F023 | Mitigated: menu-active non-power command policy is now deny-by-default and blocks previously allowed risky commands. |

## Artifacts

| artifact | sha256 |
|---|---|
| `stage3/linux_init/init_v127` | `cf099f7ba433ed788e6cdf7dbd5dff4acaf94cf6cfd63733ffb6efaaffefb8b8` |
| `stage3/ramdisk_v127.cpio` | `4c955edd84115f35198c8c8ade7bc9870e59bde620161596b5e8191b5087262d` |
| `stage3/boot_linux_v127.img` | `7677a34514ee764ab1e9188a884c508e4e510b3ca4325fbce5ee1b16fd62efd2` |

## Validation

### Static

- ARM64 static init build — PASS.
- `strings` marker check for `A90 Linux init 0.9.27 (v127)`, `A90v127`, and
  `0.9.27 v127 MENU BUSY GATE` — PASS.
- host-side controller policy harness — PASS.
- host Python `py_compile` for control/diagnostic scripts and
  `mkbootimg/gki/certify_bootimg.py` — PASS.
- shell syntax checks for archived legacy scripts and revalidation shell scripts
  — PASS.
- `git diff --check` — PASS.

### Flash

Command:

```sh
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v127.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.27 (v127)" \
  --verify-protocol auto
```

Result: PASS.

Evidence:

- local image marker and SHA256 verified.
- TWRP push and remote SHA256 verified.
- boot partition prefix SHA256 matched image SHA256.
- post-boot `cmdv1 version/status` PASS with `rc=0 status=ok`.

### Runtime Checks

With `screenmenu` visible:

- `status` — PASS, `rc=0 status=ok`.
- `storage` — PASS, `rc=0 status=ok`.
- `timeline` — PASS, `rc=0 status=ok`.
- `logpath` — PASS, `rc=0 status=ok`.
- `run /bin/a90sleep 1` — PASS, blocked with `rc=-16 status=busy`.
- `runandroid /system/bin/toybox true` — PASS, blocked with `rc=-16 status=busy`.
- `writefile /tmp/a90-f023-test blocked` — PASS, blocked with `rc=-16 status=busy`.
- `mountfs /dev/null /tmp tmpfs` — PASS, blocked with `rc=-16 status=busy`.
- `mknodc /tmp/a90-f023-node 1 3` — PASS, blocked with `rc=-16 status=busy`.
- `mknodb /tmp/a90-f023-block 1 0` — PASS, blocked with `rc=-16 status=busy`.
- `hide` — PASS, `rc=0 status=ok`.

After `hide`:

- `run /bin/a90sleep 1` — PASS, `rc=0 status=ok`.
- `selftest verbose` — PASS, `pass=10 warn=1 fail=0`.
- `status` — PASS, reports `A90 Linux init 0.9.27 (v127)`.

## Notes

- F021 and F030 remain accepted trusted-lab-boundary issues because the USB ACM
  root console and localhost serial bridge are still intentional rescue/control
  channels.
- v127 only closes the F023 busy-gate policy gap. It does not add authentication
  to the USB ACM root console or bridge.
