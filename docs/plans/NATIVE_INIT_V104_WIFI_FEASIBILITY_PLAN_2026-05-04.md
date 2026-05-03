# v104 Plan: Wi-Fi Enablement Feasibility Gate

Date: `2026-05-04`

## Summary

- v104 target: `A90 Linux init 0.9.4 (v104)` / `0.9.4 v104 WIFI FEASIBILITY`.
- Baseline: v103 verified Wi-Fi read-only inventory.
- Goal: decide whether a Wi-Fi bring-up experiment is safe and technically possible from native init.
- Current v103 evidence is **not enough for direct bring-up**: native init sees no `wlan*` interface, no Wi-Fi rfkill entry, and no WLAN/CNSS/QCA module match.
- v104 should therefore add a feasibility gate and Android/TWRP read-only comparison path first. Actual Wi-Fi enablement remains blocked unless the gate conditions are met.

## Reference Notes

- AOSP Wi-Fi architecture places Wi-Fi services in Android system service and talks to HALs; `wificond` talks to the driver with standard `nl80211` commands: <https://source.android.com/docs/core/connect/wifi-overview>.
- AOSP documents three Wi-Fi HAL surfaces: Vendor HAL, Supplicant HAL, and Hostapd HAL; Supplicant HAL fronts `wpa_supplicant`: <https://source.android.com/docs/core/connect/wifi-hal>.
- Linux wireless documents `nl80211` as the 802.11 netlink interface used by tools such as `iw`, `hostapd`, and `wpa_supplicant -Dnl80211`: <https://wireless.docs.kernel.org/en/latest/en/developers/documentation/nl80211.html>.
- Linux wireless `wpa_supplicant` documentation requires a supported Linux wireless driver and control interface configuration before supplicant control is useful: <https://wireless.docs.kernel.org/en/latest/en/users/documentation/wpa_supplicant.html>.

## Current Evidence From v103

Default native init:

```text
wifiinv:
  net total=8 wlan_like=0
  rfkill total=1 wifi_like=0
  modules readable=yes matches=0
  paths existing=6/26 file_matches=0
```

After explicit read-only `mountsystem ro`:

```text
wifiinv:
  net total=8 wlan_like=0
  rfkill total=1 wifi_like=0
  modules matches=0
  paths existing=7/26 file_matches=8
```

Notable mounted-system file matches:

```text
/mnt/system/system/etc/init/wifi.rc
/mnt/system/system/etc/init/wificond.rc
/mnt/system/system/etc/sysconfig/carrierwifi-sysconfig.xml
/mnt/system/system/etc/permissions/carrierwifi.xml
```

Interpretation:

- Android framework-side Wi-Fi config exists on the system image.
- Native init still lacks the kernel-facing prerequisite: no `wlan*`, no Wi-Fi rfkill, no driver/module evidence.
- Vendor firmware and HAL paths were not visible in the current read-only system mount.

## Design Direction

### 1. Add `wififeas` command

Recommended shell surface:

```text
wififeas [summary|full|gate|paths]
```

Behavior:

- `wififeas` / `wififeas summary`: compact feasibility result.
- `wififeas gate`: explicit `go`, `no-go`, or `baseline-required` decision.
- `wififeas full`: verbose explanation and read-only evidence.
- `wififeas paths`: print Android/TWRP/native baseline commands and candidate paths.

The command should return `0` for a cleanly computed `no-go`; `no-go` is an expected feasibility result, not a PID1 failure.

### 2. Add `a90_wififeas.c/h`

Candidate API:

```c
enum a90_wififeas_decision {
    A90_WIFI_FEAS_NO_GO,
    A90_WIFI_FEAS_BASELINE_REQUIRED,
    A90_WIFI_FEAS_GO_READ_ONLY_ONLY,
};

int a90_wififeas_evaluate(struct a90_wififeas_result *out);
int a90_wififeas_print_summary(void);
int a90_wififeas_print_full(void);
int a90_wififeas_print_gate(void);
int a90_wififeas_print_paths(void);
```

Allowed dependencies:

```text
wififeas -> wifiinv/config/util/log/console/userland/helper
```

Forbidden dependencies:

```text
wififeas -> hud/menu/input/kms/service lifecycle/netservice start-stop
```

Reason: feasibility is a policy report, not a network controller.

### 3. Define hard gates before any bring-up

Minimum `go` conditions:

```text
1. a WLAN-like interface is visible, or a read-only Android/TWRP baseline identifies the exact driver/module/firmware path needed.
2. Wi-Fi rfkill state is visible and not hard-blocked, or blocking reason is documented.
3. firmware/vendor dependency path is visible read-only.
4. userspace approach is explicit: Android HAL/wificond path or standalone Linux nl80211/wpa_supplicant path.
5. rollback path is independent of Wi-Fi: USB ACM serial and native init boot remain available.
```

If any condition is missing, v104 should report `no-go` or `baseline-required`, not attempt bring-up.

### 4. Optional host baseline collector

Extend or add a host collector only if it keeps evidence deterministic.

Preferred option:

```bash
python3 scripts/revalidation/wifi_inventory_collect.py \
  --native-only \
  --boot-image stage3/boot_linux_v104.img \
  --out tmp/wifiinv/v104-native.txt
```

Optional Android/TWRP read-only baselines:

```bash
python3 scripts/revalidation/wifi_inventory_collect.py --android-adb --out tmp/wifiinv/v104-android.txt
python3 scripts/revalidation/wifi_inventory_collect.py --twrp-adb --out tmp/wifiinv/v104-twrp.txt
```

The collector must continue to refuse unsafe operations.

## Key Changes

- Copy v103 to `stage3/linux_init/init_v104.c` and `stage3/linux_init/v104/*.inc.c`.
- Bump version markers:
  - `INIT_VERSION "0.9.4"`
  - `INIT_BUILD "v104"`
  - `A90 Linux init 0.9.4 (v104)`
  - `A90v104`
  - `0.9.4 v104 WIFI FEASIBILITY`
- Add `wififeas [summary|full|gate|paths]` to help and command table.
- Add `a90_wififeas.c/h` if implementation stays cleaner than embedding policy in the v104 include tree.
- Update `wifi_inventory_collect.py` only if needed for v104 evidence capture.
- Write `docs/reports/NATIVE_INIT_V104_WIFI_FEASIBILITY_2026-05-04.md` after real-device validation.
- Promote README/latest verified only after real-device PASS.

## Non-Goals

- No production Wi-Fi networking.
- No automatic Wi-Fi enablement.
- No `svc wifi enable`.
- No `ip link set wlan0 up` unless a later explicitly approved experiment meets all gates.
- No rfkill writes.
- No module load/unload.
- No firmware copy/overwrite.
- No Android property/service mutation.
- No boot-time Wi-Fi service.
- No remote shell over Wi-Fi.

## Implementation Order

1. Copy v103 source tree to v104 and bump markers.
2. Add `a90_wififeas.c/h` with gate result model.
3. Add `wififeas summary/gate/paths`.
4. Add `wififeas full`.
5. Reuse `wifiinv` evidence and host collector output.
6. Build v104 boot image and flash.
7. Validate v103 regressions plus feasibility output.
8. Write v104 report and promote latest verified only after PASS.

## Test Plan

### Local Build

```bash
aarch64-linux-gnu-gcc -static -Os -Wall -Wextra \
  -o stage3/linux_init/init_v104 \
  stage3/linux_init/init_v104.c \
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
  stage3/linux_init/a90_wifiinv.c \
  stage3/linux_init/a90_wififeas.c
```

Confirm:

```bash
strings stage3/linux_init/init_v104 | grep -E 'A90 Linux init 0.9.4|A90v104|0.9.4 v104 WIFI FEASIBILITY'
file stage3/linux_init/init_v104
sha256sum stage3/linux_init/init_v104
```

### Static Checks

```bash
git diff --check
python3 -m py_compile \
  scripts/revalidation/a90ctl.py \
  scripts/revalidation/native_init_flash.py \
  scripts/revalidation/diag_collect.py \
  scripts/revalidation/wifi_inventory_collect.py
rg -n "svc wifi enable|ip link set wlan0 up|rfkill.*/state|insmod|rmmod|modprobe" stage3/linux_init/v104 stage3/linux_init/a90_wififeas.c scripts/revalidation/wifi_inventory_collect.py
```

The unsafe-command scan should show no implementation paths except documentation strings or explicit deny-list checks.

### Device Validation

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v104.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.4 (v104)" \
  --verify-protocol auto
```

Required commands:

```text
version
status
bootstatus
selftest verbose
wifiinv
wifiinv full
wififeas
wififeas gate
wififeas full
wififeas paths
diag
storage
runtime
service list
netservice status
statushud
autohud 2
screenmenu
hide
cpustress 3 2
```

Optional read-only comparison:

```text
mountsystem ro
wifiinv full
wififeas full
```

## Acceptance

- `wififeas` reports a deterministic decision from read-only evidence.
- Current known-good A90 result is expected to be `no-go` or `baseline-required`, not silent failure.
- No Wi-Fi/rfkill/module/service state is changed.
- `selftest fail=0`.
- v103 `wifiinv` and v102 diagnostics regressions still pass.
- The v104 report clearly states whether v105 should proceed to soak/RC or whether a separate Android/TWRP baseline is required before any Wi-Fi enablement experiment.

## Assumptions

- v103 `A90 Linux init 0.9.3 (v103)` remains latest verified until v104 real-device validation passes.
- v104 is a feasibility gate, not a Wi-Fi feature promise.
- If `wlan*` and Wi-Fi rfkill remain absent, v104 should intentionally block bring-up and document prerequisites for a future track.
