# A90 Native Init v129 Changelog Paging

Date: 2026-05-07
Build: `A90 Linux init 0.9.29 (v129)`
Marker: `0.9.29 v129 CHANGELOG PAGING`

## Summary

v129 addresses changelog clipping caused by the project history growing beyond a
single phone screen. It adds viewport rendering for long menu pages, moves the
current changelog list/menu/detail data to `a90_changelog.c/h`, and adds
page-aware ABOUT rendering so long text screens can use VOL+/VOL- page changes.

This is a UI/maintainability change. It does not change the v128 menu-visible
security policy.

## Changes

- Added `a90_changelog.c/h` as the shared changelog table.
- Changed `ABOUT / CHANGELOG` menu construction to populate from the shared
  changelog table and append `BACK` dynamically.
- Added `SCREEN_MENU_CHANGELOG_ENTRY` and `SCREEN_APP_CHANGELOG_DETAIL` for
  generic index-based changelog detail routing.
- Added menu viewport rendering with selected-row auto-scroll and range marker.
- Added page-aware ABOUT renderer and page count helper.
- Added VOL+/VOL- page navigation for ABOUT/changelog app screens.
- Bumped version metadata to `0.9.29 (v129)`.

## Artifacts

| artifact | sha256 |
|---|---|
| `stage3/linux_init/init_v129` | `932f3a041d77b290f4d33c27d7546435ffa8025166235cdbdb02a9ca6147e2ed` |
| `stage3/ramdisk_v129.cpio` | `4092a81b1d72bc04b3eda5f6c508966d02112c180f63293e8f429623330fb8d7` |
| `stage3/boot_linux_v129.img` | `6b05f2ba4758caaf968c2df22268eaf7f42893a901c3eac9501aa8412f854cb9` |

## Validation

### Static

- ARM64 static init build — PASS.
- `strings` marker check for `A90 Linux init 0.9.29 (v129)`, `A90v129`, and
  `0.9.29 v129 CHANGELOG PAGING` — PASS.
- host changelog table/menu mapping harness — PASS.
- host Python `py_compile` for control/diagnostic scripts and
  `mkbootimg/gki/certify_bootimg.py` — PASS.
- shell syntax checks for repository shell scripts — PASS.
- `git diff --check` — PASS.

### Flash

Command:

```sh
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v129.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.29 (v129)" \
  --verify-protocol auto
```

Result: PASS.

Evidence:

- local image marker and SHA256 verified.
- TWRP push and remote SHA256 verified.
- boot partition prefix SHA256 matched image SHA256.
- post-boot `cmdv1 version/status` PASS with `rc=0 status=ok`.

### Runtime Checks

- `version` — PASS, reports `A90 Linux init 0.9.29 (v129)`.
- `status` — PASS, includes `selftest: pass=10 warn=1 fail=0`.
- `selftest verbose` — PASS, `pass=10 warn=1 fail=0`.
- `screenmenu` — PASS, nonblocking show request returns `rc=0 status=ok`.
- menu-visible `run /bin/a90sleep 1` — PASS, blocked with `rc=-16 status=busy`.
- `hide` — PASS, returns `rc=0 status=ok`.
- post-hide `run /bin/a90sleep 1` — PASS, returns `rc=0 status=ok`.

## Manual Visual Check Needed

The code path for viewport and ABOUT page navigation is built and flashed, but
final UX quality still depends on physical-button observation on the phone:

- Open `APPS > ABOUT > CHANGELOG` and verify the range marker and selected-row
  auto-scroll are visible.
- Select the first changelog entry and verify the detail screen opens.
- On any multi-page ABOUT/changelog screen, use VOL+/VOL- to page and POWER to
  return.

## Notes

- v129 keeps the v128 menu busy policy. Mutating commands remain blocked while
  the menu is visible.
- Old per-version detail functions remain in source for compatibility, but the
  current UI routes through `a90_changelog.c/h`.
