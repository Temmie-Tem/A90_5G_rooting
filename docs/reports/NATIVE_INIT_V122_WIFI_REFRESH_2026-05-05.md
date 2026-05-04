# A90 Native Init v122 Wi-Fi Refresh

Date: 2026-05-05
Build: `A90 Linux init 0.9.22 (v122)`
Marker: `0.9.22 v122 WIFI REFRESH`

## Summary

v122 refreshes the Wi-Fi evidence path without attempting bring-up. The implementation adds read-only `wifiinv refresh` and `wififeas refresh` views, compares current native evidence against v103/v104 default and mounted-system baselines, and keeps active Wi-Fi work blocked because kernel-facing WLAN/rfkill/module gates are still absent.

## Changes

- Added `a90_wifiinv_print_refresh()`.
- Added `a90_wififeas_print_refresh()`.
- Added `wifiinv [summary|full|refresh|paths]`.
- Added `wififeas [summary|full|gate|refresh|paths]`.
- Updated `wifi_inventory_collect.py` to capture native `wifiinv refresh` and `wififeas refresh`.
- Added About/changelog entry `0.9.22 v122 WIFI REFRESH`.

## Artifacts

| artifact | sha256 |
|---|---|
| `stage3/linux_init/init_v122` | `4c9a8f366077ae03d68ed6705183b39abe88eeff32f77a9c7af0952752a679a8` |
| `stage3/ramdisk_v122.cpio` | `094d78ff8b57e5f07f7cc5b8b64713571bc8afb289741ee38cf591d666ec2c10` |
| `stage3/boot_linux_v122.img` | `010670c139b54e2a17c6a34c617f1a0b0f86334313fa87d45c8c1ed432867bf8` |
| `tmp/wifiinv/v122-device-validation.txt` | `9b41c96237d3b4b51ead05c1196580d79550ac1ecd5d5464d8fde25130a80897` |
| `tmp/wifiinv/v122-native.txt` | `4e2800fbedfca5c90d45bc4012d82b0d7fbeeb24e8a211e9e1244bac93c557a5` |
| `tmp/soak/v122-quick-soak.txt` | `cd219f6421788d56011c4d9373f7aa31c9bc5f45c03c9f99e2c3ef59402964a6` |

## Validation

### Static

- `aarch64-linux-gnu-gcc -static -Os -Wall -Wextra` — PASS
- `strings` marker check for `A90 Linux init 0.9.22 (v122)`, `A90v122`, `0.9.22 v122 WIFI REFRESH`, `wifiinv refresh` — PASS
- `git diff --check` — PASS
- host Python `py_compile` for flash/control/Wi-Fi collector scripts — PASS
- stale `v121` marker check in v122 source tree — PASS

### Flash

Command:

```sh
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v122.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.22 (v122)" \
  --verify-protocol auto
```

Result: PASS

Evidence:

- local image marker and SHA256 verified
- TWRP push and remote SHA256 verified
- boot partition prefix SHA256 matched image SHA256
- post-boot `cmdv1 version/status` PASS with `rc=0 status=ok`

### Runtime Wi-Fi Refresh

Default native state:

- `wifiinv` — PASS: `net total=8 wlan_like=0`, `rfkill total=1 wifi_like=0`, `modules matches=0`, `paths existing=6/26 file_matches=0`
- `wifiinv refresh` — PASS: `relation=unchanged-native-default`
- `wififeas gate` — PASS: `decision=baseline-required`
- `wififeas refresh` — PASS: `active_wifi=blocked`

Mounted system read-only state:

- `mountsystem ro` — PASS
- `wifiinv refresh` — PASS: `paths=7/26 files=8`, `relation=android-candidates-visible`
- `wififeas full` — PASS: `decision=no-go`
- Interpretation: Android-side candidates are visible, but native kernel-facing WLAN interface, Wi-Fi rfkill, and driver module evidence are still absent.

Host collector:

```sh
python3 scripts/revalidation/wifi_inventory_collect.py \
  --native-only \
  --boot-image stage3/boot_linux_v122.img \
  --out tmp/wifiinv/v122-native.txt
```

Result: PASS

### Regression

- `pid1guard` — PASS (`pass=11 warn=0 fail=0`)
- `selftest verbose` — PASS (`pass=11 warn=0 fail=0`)
- `native_soak_validate.py --cycles 3 --sleep 2` — PASS (`cycles=3 commands=14`)

## Conclusion

Active Wi-Fi bring-up remains blocked after v122. The current evidence matches prior default native constraints and mounted-system evidence still lacks the kernel-facing gates required for a safe controlled bring-up. Next Wi-Fi work should remain read-only unless a separate plan explicitly defines an approved nl80211/iw probe and rollback criteria.
