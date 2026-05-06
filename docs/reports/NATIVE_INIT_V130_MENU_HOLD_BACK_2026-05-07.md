# A90 Native Init v130 Menu Hold Back

Date: 2026-05-07
Build: `A90 Linux init 0.9.30 (v130)`
Marker: `0.9.30 v130 MENU HOLD BACK`

## Summary

v130 improves the v129 long changelog/menu UX. It accepts volume key repeat
(`EV_KEY value=2`) as continuous movement/page input and adds a physical
`VOLUP+VOLDOWN` shortcut for back/hide behavior.

This is a small UI/input usability change. It does not change the v128/v129
menu-visible command security policy.

## Changes

- Added v130 changelog entry in `a90_changelog.c`.
- Changed menu event handling to treat volume hold-repeat as repeated movement.
- Added `VOLUP+VOLDOWN` combo handling in the auto HUD/menu loop:
  - active app: returns to menu and stops CPU stress app if needed.
  - submenu: goes to parent page.
  - main menu: hides menu and returns to HUD/log-tail.
- Updated menu/footer hints for hold-scroll and physical back.
- Bumped version metadata to `0.9.30 (v130)`.

## Artifacts

| artifact | sha256 |
|---|---|
| `stage3/linux_init/init_v130` | `b36248761f58b0fa764b31ede2b14e49ee3bcd926ce1b655c4affdcb1444e759` |
| `stage3/ramdisk_v130.cpio` | `a997ff9dbb79e0ff5ef6f430327d777a1f05b1280141aa66ebfc21d402b480b0` |
| `stage3/boot_linux_v130.img` | `8ce9624753d83fd65cf8111150ab14c456121aaab2affe9ce25185898011cea2` |

## Validation

### Static

- ARM64 static init build — PASS.
- `strings` marker check for `A90 Linux init 0.9.30 (v130)`, `A90v130`, and
  `0.9.30 v130 MENU HOLD BACK` — PASS.
- host Python `py_compile` for control/diagnostic scripts and
  `mkbootimg/gki/certify_bootimg.py` — PASS.
- shell syntax checks for repository shell scripts — PASS.
- `git diff --check` — PASS.

### Flash

Command:

```sh
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v130.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.30 (v130)" \
  --verify-protocol auto
```

Result: PASS.

Evidence:

- local image marker and SHA256 verified.
- TWRP push and remote SHA256 verified.
- boot partition prefix SHA256 matched image SHA256.
- post-boot `cmdv1 version/status` PASS with `rc=0 status=ok`.

### Runtime Checks

- `status` — PASS, reports `A90 Linux init 0.9.30 (v130)`.
- `selftest verbose` — PASS, `pass=10 warn=1 fail=0`.
- `screenmenu` — PASS, nonblocking show request returns `rc=0 status=ok`.
- menu-visible `run /bin/a90sleep 1` — PASS, blocked with `rc=-16 status=busy`.
- `hide` — PASS, returns `rc=0 status=ok`.
- post-hide `run /bin/a90sleep 1` — PASS, returns `rc=0 status=ok`.

## Manual Visual Check Needed

The code path is built and flashed, but physical UX still needs observation:

- Open `APPS > ABOUT > CHANGELOG` and hold VOL+/VOL- to confirm continuous
  scroll over long entries.
- Press VOLUP+VOLDOWN together in changelog/submenus to confirm back behavior.
- Press VOLUP+VOLDOWN on the main menu to confirm it hides back to HUD/log-tail.
