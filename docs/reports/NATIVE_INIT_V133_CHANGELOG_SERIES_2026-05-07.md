# A90 Native Init v133 Changelog Series

Date: 2026-05-07
Build: `A90 Linux init 0.9.33 (v133)`
Marker: `0.9.33 v133 CHANGELOG SERIES`

## Summary

v133 changes ABOUT/changelog navigation from one long version list to a two-step
series flow. The first changelog page shows version series such as
`0.9.x RECENT` and `0.8.x LEGACY`; selecting a series opens only that series'
version entries, and selecting a version opens the existing detail renderer.

The v132 shared changelog table remains the only source of changelog data.

## Changes

- Added `0.9.33 v133 CHANGELOG SERIES` to `a90_changelog.c`.
- Added `a90_changelog_series_*` APIs to group entries by semantic version
  prefix.
- Added `SCREEN_MENU_PAGE_CHANGELOG_SERIES` and `SCREEN_MENU_CHANGELOG_SERIES`.
- Changed ABOUT `CHANGELOG >` to open the series page first.
- Added series-local selected-row to global changelog index mapping for detail
  screens.
- Updated `native_soak_validate.py` default expected version to v133.

## Artifacts

| artifact | sha256 |
|---|---|
| `stage3/linux_init/init_v133` | `9ea80cd9849ac1d8c9989bf7103fb17e44f94b5f9146b024c7f67addf9a3d225` |
| `stage3/ramdisk_v133.cpio` | `c1be3d25e59bab8aa6e697e8c183e9ab11a78f634c774842ffba0a972110e52d` |
| `stage3/boot_linux_v133.img` | `0001fc3ddadc600bbe0b1e8ff90b147f805e80ee31f57f4146188167ce7ef92a` |

## Validation

### Static

- ARM64 static init build — PASS.
- `strings` marker check for `A90 Linux init 0.9.33 (v133)`, `A90v133`, and
  `0.9.33 v133 CHANGELOG SERIES` — PASS.
- host changelog/menu harness — PASS, `PASS v133 series=9 first=0.9.x RECENT second_first=0.8.29 v98`.
- host Python `py_compile` for control/diagnostic scripts and
  `mkbootimg/gki/certify_bootimg.py` — PASS.
- shell syntax checks for repository shell scripts — PASS.
- `git diff --check` — PASS.

### Flash

Command:

```sh
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v133.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.33 (v133)" \
  --verify-protocol auto
```

Result: PASS.

Evidence:

- local image marker and SHA256 verified.
- TWRP push and remote SHA256 verified.
- boot partition prefix SHA256 matched image SHA256.
- post-boot `cmdv1 version/status` PASS with `rc=0 status=ok`.
- device reported `A90 Linux init 0.9.33 (v133)`.

### Runtime Checks

- `status` — PASS, reports `A90 Linux init 0.9.33 (v133)`.
- `selftest verbose` — PASS, `pass=10 warn=1 fail=0 duration=37ms entries=11`.
- `screenmenu` — PASS, nonblocking show request returns `rc=0 status=ok`.
- menu-visible `run /bin/a90sleep 1` — PASS, blocked with `rc=-16 status=busy`.
- `hide` — PASS, returns `rc=0 status=ok`.
- post-hide `run /bin/a90sleep 1` — PASS, returns `rc=0 status=ok`.
- `native_soak_validate.py --cycles 3` — PASS, `cycles=3 commands=14`.

## Manual Visual Check

Pending user confirmation on device display:

- `APPS / ABOUT / CHANGELOG` shows series groups first.
- `0.9.x RECENT` opens v133/v132/v131 entries.
- Selecting `0.9.33 v133` opens the v133 detail screen.
- Back/hide and hold-scroll behavior remain usable.
