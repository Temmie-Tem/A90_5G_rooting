# Native Init v106 UI App About Report

Date: `2026-05-04`
Version: `A90 Linux init 0.9.6 (v106)` / `0.9.6 v106 APP ABOUT API`
Baseline: `A90 Linux init 0.9.5 (v105)`

## Summary

- v106 starts the post-v105 UI/App Architecture split.
- Added `a90_app_about.c/h` and moved ABOUT/version/changelog/credits rendering out of `v106/40_menu_apps.inc.c`.
- Preserved `screenmenu` nonblocking behavior and v105 runtime/storage/network policy.
- Real-device flash and quick soak passed.

## Code Changes

- Added `stage3/linux_init/init_v106.c` and `stage3/linux_init/v106/*.inc.c` copied from v105.
- Updated `stage3/linux_init/a90_config.h` to `0.9.6` / `v106`.
- Added `stage3/linux_init/a90_app_about.c` and `stage3/linux_init/a90_app_about.h`.
- Updated `stage3/linux_init/a90_menu.c` and `stage3/linux_init/a90_menu.h` with the v106 changelog entry/action/app id.
- Replaced ABOUT renderer ownership in `v106/40_menu_apps.inc.c` with `a90_app_about_draw(app_id)`.

## Artifacts

| Artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v106` | `566e7b4abba3a98de1c3787cb4db2ad78aa3c4d96271fb08b5ba169ed379c171` |
| `stage3/ramdisk_v106.cpio` | `f3f30f7bc44468d6c9a582f934f99387c820ce1c0250acd7144557896186c390` |
| `stage3/boot_linux_v106.img` | `8e54c57098b7df4d44a7fbf76a2908e739c4e5624149a252f5b42d6d4d23b059` |

## Static Validation

- Static ARM64 build with `aarch64-linux-gnu-gcc -static -Os -Wall -Wextra` — PASS.
- Marker strings in init and boot image — PASS:
  - `A90 Linux init 0.9.6 (v106)`
  - `A90v106`
  - `0.9.6 v106 APP ABOUT API`
- `git diff --check` — PASS.
- Host Python `py_compile` — PASS:
  - `scripts/revalidation/a90ctl.py`
  - `scripts/revalidation/native_init_flash.py`
  - `scripts/revalidation/diag_collect.py`
  - `scripts/revalidation/wifi_inventory_collect.py`
  - `scripts/revalidation/native_soak_validate.py`
- v106 include tree no longer contains the old static ABOUT renderer implementations — PASS.

## Device Validation

Flash command:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v106.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.6 (v106)" \
  --verify-protocol auto
```

Result: PASS.

- Local image marker and SHA check — PASS.
- Recovery ADB push and remote SHA check — PASS.
- Boot partition prefix SHA matched `stage3/boot_linux_v106.img` — PASS.
- Post-boot `cmdv1 version/status` — PASS.

Manual command regression:

- `version` — PASS, reports `A90 Linux init 0.9.6 (v106)`.
- `status` — PASS, `selftest pass=11 warn=0 fail=0`.
- `bootstatus` — PASS.
- `selftest verbose` — PASS, `pass=11 warn=0 fail=0`.
- `statushud` — PASS.
- `autohud 2` — PASS.
- `diag` — PASS, includes v106 banner.
- `runtime` — PASS, SD runtime root active.
- `storage` — PASS, SD mounted rw.
- `screenmenu` — PASS, nonblocking show request returns `rc=0`.
- `hide` — PASS.

Quick soak:

```bash
python3 scripts/revalidation/native_soak_validate.py \
  --cycles 3 \
  --sleep 1 \
  --expect-version "A90 Linux init 0.9.6 (v106)" \
  --out tmp/soak/v106-quick-soak.txt
```

Result: `PASS cycles=3 commands=14`.

## Notes

- The first local manual loop passed full validation, but quoted multi-word commands were invoked incorrectly once through `a90ctl.py`; this was host command usage error, not a device regression. The same commands passed when rerun with proper argv.
- v106 does not change Wi-Fi, storage, netservice, runtime, or rshell policy.
- Next planned step: v107 displaytest/cutout renderer split.
