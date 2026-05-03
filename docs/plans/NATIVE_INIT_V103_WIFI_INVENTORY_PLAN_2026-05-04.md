# v103 Plan: Wi-Fi Read-Only Inventory

Date: `2026-05-04`

## Summary

- v103 target: `A90 Linux init 0.9.3 (v103)` / `0.9.3 v103 WIFI INVENTORY`.
- Baseline: v102 verified diagnostics/log bundle.
- Goal: identify the concrete Wi-Fi hardware, firmware, kernel module, sysfs, and Android/vendor userspace prerequisites before attempting any Wi-Fi bring-up.
- Scope is intentionally read-only: add inventory collection and reporting, but do not enable Wi-Fi, change rfkill, load/unload modules, start supplicant, or mutate Android/vendor state.
- USB ACM serial remains the required rescue/control channel; USB NCM remains optional and must not be required for inventory.

## Current Problem

The project is now stable enough to consider wireless networking, but the Wi-Fi path is still mostly unknown from native init:

- native init may or may not see `wlan0`, rfkill nodes, Qualcomm/CNSS module state, or vendor firmware mounts;
- TWRP and Android may expose different sysfs/module/firmware state from the custom init environment;
- blindly trying `ip link set wlan0 up`, `svc wifi enable`, `wpa_supplicant`, or firmware writes would risk mixing Android policy with native init policy;
- v102 diagnostics does not yet separate Wi-Fi-specific evidence from general boot/runtime diagnostics.

v103 should answer what is visible and what is missing without changing the device state.

## Design Direction

### 1. Add read-only `wifiinv` command

Recommended shell surface:

```text
wifiinv [summary|full|paths]
```

Behavior:

- `wifiinv` / `wifiinv summary`: compact operator view for serial console.
- `wifiinv full`: verbose inventory printed to console.
- `wifiinv paths`: list candidate paths/patterns being inspected.

The command must not:

- enable Wi-Fi;
- write to `/sys/class/rfkill/*/state`;
- write to `/sys/class/net/*`;
- run `ip link set wlan0 up`;
- run `svc wifi enable`;
- start `wpa_supplicant`, Android HALs, vendor daemons, or `netd`;
- load/unload kernel modules;
- bind/unbind USB gadget;
- mount/unmount/format SD or vendor partitions;
- dump private identity/security partitions.

### 2. Keep the first implementation native-init safe

Preferred implementation is a small `a90_wifiinv.c/h` module compiled into PID1.

Candidate API:

```c
int a90_wifiinv_print_summary(void);
int a90_wifiinv_print_full(void);
int a90_wifiinv_print_paths(void);
int a90_wifiinv_collect(struct a90_wifiinv_snapshot *snapshot);
```

Allowed dependencies:

```text
wifiinv -> config/util/log/storage/console
```

Forbidden dependencies:

```text
wifiinv -> hud/menu/input/kms/netservice service lifecycle
```

Reason: Wi-Fi inventory is evidence collection. It should not become a bring-up controller.

### 3. Inventory targets

Native init should inspect these categories using read-only opens, `stat`, `readlink`, and directory scans:

```text
/sys/class/net
/sys/class/rfkill
/sys/module
/proc/modules
/proc/cmdline
/proc/device-tree
/vendor
/vendor/firmware
/vendor/firmware_mnt
/vendor/etc/wifi
/vendor/bin
/vendor/lib
/vendor/lib64
/odm/etc/wifi
/product/etc/wifi
/system/etc/wifi
```

Name patterns to flag:

```text
wlan
wifi
WCNSS
wcnss
cnss
qca
qcacld
ath
bdwlan
qwlan
wlanmdsp
Data.msc
wpa_supplicant
hostapd
android.hardware.wifi
vendor.qti.hardware.wifi
```

The output should distinguish:

- path exists / missing;
- readable / unreadable;
- symlink target;
- regular file / directory / character device / block device;
- likely firmware / module / config / HAL / daemon / interface.

### 4. Compare native, TWRP, and Android only when safe

v103 implementation should support native init inventory first. TWRP and Android baselines are useful but must remain explicitly read-only.

Safe Android/TWRP baseline examples:

```text
adb shell getprop | grep -Ei 'wifi|wlan|qca|cnss'
adb shell ip link
adb shell ls -l /sys/class/net /sys/class/rfkill
adb shell cat /proc/modules
adb shell find /vendor /odm /product /system -maxdepth 4 -iname '*wifi*' -o -iname '*wlan*'
adb shell cmd wifi status
```

Forbidden Android/TWRP baseline actions:

```text
svc wifi enable
svc wifi disable
cmd wifi set-wifi-enabled enabled
insmod
rmmod
modprobe
ip link set wlan0 up
echo ... > /sys/class/rfkill/*/state
```

If Android/TWRP comparison is needed, it should be a separate manual/host collector step after native init remains recoverable.

### 5. Optional host collector

Add `scripts/revalidation/wifi_inventory_collect.py` only if it keeps evidence consistent.

Default mode should be native serial-only:

```bash
python3 scripts/revalidation/wifi_inventory_collect.py --native-only --out tmp/wifiinv/latest.txt
```

Candidate behavior:

- run `wifiinv full` through `a90ctl.py`;
- optionally append `diag summary`;
- collect host git commit/status and boot image SHA if provided;
- optionally collect TWRP/Android read-only baselines when explicitly requested;
- write a timestamped text file under `tmp/wifiinv/` or a user-specified path.

Optional flags:

```text
--boot-image stage3/boot_linux_v103.img
--native-only
--android-adb
--twrp-adb
```

The collector must refuse unsafe commands and should print the exact command list before optional Android/TWRP collection.

## Key Changes

- Copy v102 to `stage3/linux_init/init_v103.c` and `stage3/linux_init/v103/*.inc.c`.
- Bump version markers:
  - `INIT_VERSION "0.9.3"`
  - `INIT_BUILD "v103"`
  - `A90 Linux init 0.9.3 (v103)`
  - `A90v103`
  - `0.9.3 v103 WIFI INVENTORY`
- Add `wifiinv [summary|full|paths]` to help and command table.
- Add `a90_wifiinv.c/h` for read-only inventory if the command would otherwise duplicate too much shell code.
- Add `scripts/revalidation/wifi_inventory_collect.py` if host-side capture is useful during validation.
- Write `docs/reports/NATIVE_INIT_V103_WIFI_INVENTORY_2026-05-04.md` after real-device validation.
- Promote README/latest verified only after real-device PASS.

## Non-Goals

- No Wi-Fi enablement.
- No WPA supplicant bring-up.
- No production wireless networking.
- No Wi-Fi service manager entry.
- No rfkill writes.
- No kernel module load/unload.
- No firmware copy/overwrite.
- No Android property/service mutation.
- No NCM/tcpctl dependency for inventory.

## Implementation Order

1. Copy v102 source tree to v103 and bump markers.
2. Define read-only path scan helpers and stable output format.
3. Add `wifiinv summary` and `wifiinv paths`.
4. Add `wifiinv full`.
5. Add optional host collector if repeated capture needs it.
6. Build v103 boot image and flash.
7. Validate native inventory and v102 regressions.
8. Write v103 report and promote latest verified only after PASS.

## Test Plan

### Local Build

```bash
aarch64-linux-gnu-gcc -static -Os -Wall -Wextra \
  -o stage3/linux_init/init_v103 \
  stage3/linux_init/init_v103.c \
  stage3/linux_init/a90_util.c \
  stage3/linux_init/a90_log.c \
  stage3/linux_init/a90_timeline.c \
  stage3/linux_init/a90_console.c \
  stage3/linux_init/a90_cmdproto.c \
  stage3/linux_init/a90_run.c \
  stage3/linux_init/a90_service.c \
  stage3/linux_init/a90_kms.c \
  stage3/linux_init/a90_draw.c \
  stage3/linux_init/a90_input.c \
  stage3/linux_init/a90_hud.c \
  stage3/linux_init/a90_menu.c \
  stage3/linux_init/a90_metrics.c \
  stage3/linux_init/a90_shell.c \
  stage3/linux_init/a90_controller.c \
  stage3/linux_init/a90_storage.c \
  stage3/linux_init/a90_selftest.c \
  stage3/linux_init/a90_usb_gadget.c \
  stage3/linux_init/a90_netservice.c \
  stage3/linux_init/a90_runtime.c \
  stage3/linux_init/a90_helper.c \
  stage3/linux_init/a90_userland.c \
  stage3/linux_init/a90_diag.c \
  stage3/linux_init/a90_wifiinv.c
```

Confirm:

```bash
strings stage3/linux_init/init_v103 | grep -E 'A90 Linux init 0.9.3|A90v103|0.9.3 v103 WIFI INVENTORY'
file stage3/linux_init/init_v103
sha256sum stage3/linux_init/init_v103
```

### Static Checks

```bash
git diff --check
python3 -m py_compile \
  scripts/revalidation/a90ctl.py \
  scripts/revalidation/native_init_flash.py \
  scripts/revalidation/diag_collect.py \
  scripts/revalidation/wifi_inventory_collect.py
rg -n "svc wifi enable|ip link set wlan0 up|rfkill.*/state|insmod|rmmod|modprobe" stage3/linux_init/v103 stage3/linux_init/a90_wifiinv.c scripts/revalidation/wifi_inventory_collect.py
```

The unsafe-command `rg` should show no implementation paths except documentation strings or explicit deny-list checks.

### Boot Image

- Reuse v102 boot image header/kernel args.
- Replace ramdisk with `stage3/ramdisk_v103.cpio`.
- Produce `stage3/boot_linux_v103.img`.
- Confirm ramdisk has `/init`, `/bin/a90sleep`, `/bin/a90_cpustress`, `/bin/a90_rshell`, and existing helper layout unchanged.

### Device Validation

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v103.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.3 (v103)" \
  --verify-protocol auto
```

Required commands:

```text
version
status
bootstatus
selftest verbose
diag
diag full
wifiinv
wifiinv paths
wifiinv full
storage
mountsd status
runtime
service list
netservice status
statushud
autohud 2
screenmenu
hide
cpustress 3 2
```

Optional host capture:

```bash
python3 scripts/revalidation/wifi_inventory_collect.py \
  --native-only \
  --boot-image stage3/boot_linux_v103.img \
  --out tmp/wifiinv/v103-native.txt
```

## Acceptance

- `wifiinv` runs without changing Wi-Fi/rfkill/module/service state.
- Known-good A90 boot remains `selftest fail=0`.
- Serial bridge remains the primary control path after inventory.
- v102 diagnostics, storage, runtime, service, HUD/menu, and CPU stress regressions still pass.
- The v103 report identifies whether native init sees:
  - `wlan*` network interfaces;
  - rfkill entries;
  - WLAN/CNSS/QCA kernel modules;
  - firmware/config candidates;
  - vendor HAL/daemon/supplicant candidates.
- v104 Wi-Fi feasibility is gated on concrete v103 evidence, not guesses.

## Assumptions

- v102 `A90 Linux init 0.9.2 (v102)` remains latest verified until v103 real-device validation passes.
- v103 is evidence collection, not bring-up.
- Android/TWRP comparison may require manual mode switches and should not be part of default native flash acceptance.
- If native init cannot see Wi-Fi hardware, that is a valid v103 result and should become a v104 blocker or prerequisite, not a v103 failure.
