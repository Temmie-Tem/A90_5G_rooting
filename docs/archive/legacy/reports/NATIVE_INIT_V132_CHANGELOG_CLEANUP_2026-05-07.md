# A90 Native Init v132 Changelog Cleanup

Date: 2026-05-07
Build: `A90 Linux init 0.9.32 (v132)`
Marker: `0.9.32 v132 CHANGELOG CLEANUP`

## Summary

v132 removes the old ABOUT/changelog per-version UI route and keeps changelog
rendering on the shared `a90_changelog.c/h` table. The visible menu still uses
the existing changelog list/detail flow, but the active code path no longer has
separate enum/app/draw functions for each historical version.

v131 physical hold-scroll behavior remains unchanged and was kept as the
rollback baseline.

## Changes

- Added `0.9.32 v132 CHANGELOG CLEANUP` to `a90_changelog.c`.
- Removed legacy `SCREEN_MENU_CHANGELOG_...` and `SCREEN_APP_CHANGELOG_...`
  enum routes from the active menu API.
- Removed legacy `draw_screen_changelog_v...()` per-version render functions.
- Kept `SCREEN_MENU_CHANGELOG_ENTRY` → `SCREEN_APP_CHANGELOG_DETAIL` as the
  single changelog detail route.
- Updated `native_soak_validate.py` default expected version to v132.
- Bumped source, build tag, kmsg marker, and boot image to v132.

## Artifacts

| artifact | sha256 |
|---|---|
| `stage3/linux_init/init_v132` | `dc27f844fc97f9e3057c0ab1929b6ab90c3909898f9b1428fe85407ef26e9360` |
| `stage3/ramdisk_v132.cpio` | `ecb9d4e489fbc594bb22f2705df1236b3e4e96e6a6368b87376f6f8f49809fde` |
| `stage3/boot_linux_v132.img` | `db490438cb55208d4ff1f2245c0dbdad1756696f2674bd1430c2d05d7df833d1` |

## Validation

### Static

- ARM64 static init build — PASS.
- `strings` marker check for `A90 Linux init 0.9.32 (v132)`, `A90v132`, and
  `0.9.32 v132 CHANGELOG CLEANUP` — PASS.
- Legacy active-route symbol scan in current shared menu/about files — PASS.
- host changelog harness — PASS, `PASS v132 changelog single-route count=77`.
- host Python `py_compile` for control/diagnostic scripts and
  `mkbootimg/gki/certify_bootimg.py` — PASS.
- shell syntax checks for repository shell scripts — PASS.
- `git diff --check` — PASS.

### Flash

Command:

```sh
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v132.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.32 (v132)" \
  --verify-protocol auto
```

Result: PASS.

Evidence:

- local image marker and SHA256 verified.
- TWRP push and remote SHA256 verified.
- boot partition prefix SHA256 matched image SHA256.
- post-boot `cmdv1 version/status` PASS with `rc=0 status=ok`.
- device reported `A90 Linux init 0.9.32 (v132)`.

### Runtime Checks

- `status` — PASS, reports `A90 Linux init 0.9.32 (v132)`.
- `selftest verbose` — PASS, `pass=10 warn=1 fail=0 duration=36ms entries=11`.
- `screenmenu` — PASS, nonblocking show request returns `rc=0 status=ok`.
- menu-visible `run /bin/a90sleep 1` — PASS, blocked with `rc=-16 status=busy`.
- `hide` — PASS, returns `rc=0 status=ok`.
- post-hide `run /bin/a90sleep 1` — PASS, returns `rc=0 status=ok`.
- `native_soak_validate.py --cycles 3` — PASS, `cycles=3 commands=14`.

## Follow-Up

- Manually open `APPS / ABOUT / CHANGELOG` and confirm the latest v132 entry and
  detail text on the device display.
- Decide next priority between shell/serial usability, security closure docs, or
  the next UI cleanup item.
