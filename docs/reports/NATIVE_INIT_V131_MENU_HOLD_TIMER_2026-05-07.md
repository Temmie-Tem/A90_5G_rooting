# A90 Native Init v131 Menu Hold Timer

Date: 2026-05-07
Build: `A90 Linux init 0.9.31 (v131)`
Marker: `0.9.31 v131 MENU HOLD TIMER`

## Summary

v130 added hold-scroll by accepting `EV_KEY value=2` repeat events, but the A90
physical volume keys did not emit usable repeat events in the tested menu path.
v131 fixes that by tracking volume key down/up state and generating repeat
steps from a monotonic timer inside the auto HUD/menu loop.

The v130 `VOLUP+VOLDOWN` physical back shortcut is preserved.

## Changes

- Added timer-based hold-repeat constants:
  - start delay: `450ms`
  - repeat interval: `120ms`
- Added `auto_menu_handle_volume_step()` to share single-step and repeat-step
  behavior for menus and ABOUT/changelog paged screens.
- Poll timeout now shortens to the next scheduled repeat while a volume key is
  held, so repeat does not depend on kernel key-repeat events.
- Cleared hold-repeat state on release, menu request reset, and VOLUP+VOLDOWN
  combo back.
- Bumped version metadata to `0.9.31 (v131)`.

## Artifacts

| artifact | sha256 |
|---|---|
| `stage3/linux_init/init_v131` | `5665cac5254e486a33acdb43181866d5ffac5006ebf62fe7d05a826cf04997c3` |
| `stage3/ramdisk_v131.cpio` | `75ad3b802beb363cb7ac7d30dab4e48eb103844be0c52c0fd987f1d9850ee143` |
| `stage3/boot_linux_v131.img` | `e6bb64987ff75affdb6d9900901086052a6a81c992f32f6252d3cc105e31ddee` |

## Validation

### Static

- ARM64 static init build — PASS.
- `strings` marker check for `A90 Linux init 0.9.31 (v131)`, `A90v131`, and
  `0.9.31 v131 MENU HOLD TIMER` — PASS.
- host Python `py_compile` for control/diagnostic scripts and
  `mkbootimg/gki/certify_bootimg.py` — PASS.
- shell syntax checks for repository shell scripts — PASS.
- `git diff --check` — PASS.

### Flash

Command:

```sh
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v131.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.31 (v131)" \
  --verify-protocol auto
```

Result: PASS.

Evidence:

- local image marker and SHA256 verified.
- TWRP push and remote SHA256 verified.
- boot partition prefix SHA256 matched image SHA256.
- post-boot `cmdv1 version/status` PASS with `rc=0 status=ok`.

### Runtime Checks

- `status` — PASS, reports `A90 Linux init 0.9.31 (v131)`.
- `selftest verbose` — PASS, `pass=10 warn=1 fail=0`.
- `screenmenu` — PASS, nonblocking show request returns `rc=0 status=ok`.
- menu-visible `run /bin/a90sleep 1` — PASS, blocked with `rc=-16 status=busy`.
- `hide` — PASS, returns `rc=0 status=ok`.
- post-hide `run /bin/a90sleep 1` — PASS, returns `rc=0 status=ok`.

## Manual Visual Check

Result: PASS. User confirmed physical behavior on device.

- `APPS > ABOUT > CHANGELOG` VOL long-hold continuous movement — PASS.
- Timer-based repeat works without kernel `EV_KEY value=2` repeat events — PASS.
- `VOLUP+VOLDOWN` back/hide behavior remains usable — PASS.
