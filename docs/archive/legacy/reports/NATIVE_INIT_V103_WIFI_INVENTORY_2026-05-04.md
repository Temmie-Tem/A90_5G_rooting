# Native Init v103 Wi-Fi Inventory Report

Date: `2026-05-04`

## Summary

- Version: `A90 Linux init 0.9.3 (v103)` / `0.9.3 v103 WIFI INVENTORY`.
- Baseline: v102 diagnostics/log bundle.
- v103 adds a read-only `wifiinv [summary|full|paths]` command.
- v103 adds `scripts/revalidation/wifi_inventory_collect.py`, a serial-first host collector.
- Wi-Fi inventory is intentionally non-destructive: no Wi-Fi enablement, no rfkill write, no `wlan0` link-up, no module load/unload, and no vendor/firmware mutation.

## Key Changes

- Added `stage3/linux_init/init_v103.c` and `stage3/linux_init/v103/*.inc.c`.
- Updated `stage3/linux_init/a90_config.h` to `0.9.3` / `v103`.
- Added `stage3/linux_init/a90_wifiinv.c/h` with:
  - `a90_wifiinv_collect()`
  - `a90_wifiinv_print_summary()`
  - `a90_wifiinv_print_full()`
  - `a90_wifiinv_print_paths()`
- Added `wifiinv [summary|full|paths]` to help and shell command table.
- Added `scripts/revalidation/wifi_inventory_collect.py` for host-side serial bridge collection.
- Updated ABOUT/changelog top entry to `0.9.3 v103 WIFI INVENTORY`.

## Artifacts

| Artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v103` | `9d1bac55549abb0e7aac2112896f66c362cc38dd1093212d4beb4bcb65c33a85` |
| `stage3/ramdisk_v103.cpio` | `0758b63988b2edfb27cf2bc05da484dac099391bfc488f8a6c13aa976b7c61c4` |
| `stage3/boot_linux_v103.img` | `dca3ee7ac77f366176d833b40450b0b1e3e55ebaf46ddc11c4d3a5f19454622b` |

Ramdisk entries:

```text
/init
/bin/a90sleep
/bin/a90_cpustress
/bin/a90_rshell
```

## Static Validation

- Static ARM64 init build with `-Wall -Wextra` — PASS.
- `stage3/ramdisk_v103.cpio` and `stage3/boot_linux_v103.img` generated from v102 boot args with only ramdisk replaced — PASS.
- Boot image markers found:
  - `A90 Linux init 0.9.3 (v103)`
  - `A90v103`
  - `0.9.3 v103 WIFI INVENTORY`
  - `wifiinv [summary|full|paths]`
- `git diff --check` — PASS.
- Host Python `py_compile` for `a90ctl.py`, `native_init_flash.py`, `diag_collect.py`, `wifi_inventory_collect.py` — PASS.
- v103 stale marker scan for current-version v102 strings in `init_v103.c` and `v103/*.inc.c` — PASS.

## Flash Validation

Command:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v103.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.3 (v103)" \
  --verify-protocol auto
```

Result:

- Local image marker and SHA256 check — PASS.
- TWRP push and remote SHA256 check — PASS.
- boot partition prefix SHA256 matched `stage3/boot_linux_v103.img` — PASS.
- Post-boot `cmdv1 version/status` — PASS.

## Device Validation

- `version`: PASS, `A90 Linux init 0.9.3 (v103)`.
- `status`: PASS, `selftest pass=11 warn=0 fail=0`, SD runtime, autohud running, netservice disabled, rshell stopped.
- `bootstatus`: PASS.
- `selftest verbose`: PASS, `pass=11 warn=0 fail=0`.
- `wifiinv`: PASS, default native summary reports `net total=8 wlan_like=0`, `rfkill total=1 wifi_like=0`, `modules matches=0`, `paths existing=6/26 file_matches=0`.
- `wifiinv paths`: PASS, prints candidate paths, scan roots, patterns, and forbidden operation summary.
- `wifiinv full`: PASS, read-only inventory shows no `wlan*` interface, only `rfkill0 name=bt_power type=bluetooth`, and no WLAN/CNSS/QCA module match in `/proc/modules`.
- `diag`: PASS, compact summary includes v103 version and existing v102 diagnostics coverage.
- `storage`: PASS.
- `mountsd status`: PASS.
- `runtime`: PASS.
- `service list`: PASS.
- `netservice status`: PASS.
- `statushud`: PASS.
- `autohud 2`: PASS.
- `screenmenu`: PASS, nonblocking.
- `hide`: PASS.
- `cpustress 3 2`: PASS, `/bin/a90_cpustress` completed.

## Extended Read-Only Inventory

Default native init does not mount Android system/vendor paths automatically. A separate read-only check was run:

```text
mountsystem ro
wifiinv
wifiinv full
```

Result:

- `mountsystem ro`: PASS, `/mnt/system` mounted read-only.
- `wifiinv` after mount: PASS, `paths existing=7/26 file_matches=8`.
- Still no `wlan*` interface, Wi-Fi rfkill entry, or WLAN/CNSS/QCA kernel module match.
- Read-only file matches found under `/mnt/system/system/etc`, including:
  - `/mnt/system/system/etc/init/wifi.rc`
  - `/mnt/system/system/etc/init/wificond.rc`
  - `/mnt/system/system/etc/sysconfig/carrierwifi-sysconfig.xml`
  - `/mnt/system/system/etc/permissions/carrierwifi.xml`
  - `/mnt/system/system/etc/permissions/privapp-permissions-com.samsung.android.server.wifi.mobilewips.xml`
- `/mnt/system/vendor/firmware`, `/mnt/system/vendor/etc/wifi`, and vendor library/bin Wi-Fi paths were not visible in this read-only system mount.

## Host Collector

- `wifi_inventory_collect.py --native-only --boot-image stage3/boot_linux_v103.img --out tmp/wifiinv/v103-native-rerun.txt`: PASS.
- `wifi_inventory_collect.py --native-only --boot-image stage3/boot_linux_v103.img --out tmp/wifiinv/v103-native-mounted.txt`: PASS after `mountsystem ro`, captured boot image SHA and mounted-system Wi-Fi matches.

## Notes

- The host collector reports `git_dirty=yes` during validation because v103 source changes were intentionally uncommitted while testing.
- One initial validation batch passed multi-word commands as a single argv to `a90ctl.py`; this was a host invocation mistake only and was rerun successfully with correct argv separation.
- v103 evidence suggests Wi-Fi bring-up should not start by toggling `wlan0` or rfkill from native init because neither a WLAN interface nor Wi-Fi rfkill node is visible in the current native boot state.

## Current Baseline

`A90 Linux init 0.9.3 (v103)` is now the latest verified native init baseline.

Next planned target: v104 Wi-Fi enablement feasibility, gated on additional read-only Android/TWRP/vendor dependency evidence.
