# Native Init v104 Wi-Fi Feasibility Report

Date: `2026-05-04`

## Summary

- Version: `A90 Linux init 0.9.4 (v104)` / `0.9.4 v104 WIFI FEASIBILITY`.
- Baseline: v103 Wi-Fi read-only inventory.
- v104 adds a read-only `wififeas [summary|full|gate|paths]` command.
- The command converts native and mounted-system Wi-Fi evidence into a deterministic `go-read-only-only`, `no-go`, or `baseline-required` decision.
- Wi-Fi bring-up remains intentionally blocked: no `svc wifi enable`, no `wlan0` link-up, no rfkill write, no module load/unload, and no firmware/vendor mutation.

## Key Changes

- Added `stage3/linux_init/init_v104.c` and `stage3/linux_init/v104/*.inc.c`.
- Updated `stage3/linux_init/a90_config.h` to `0.9.4` / `v104`.
- Added `stage3/linux_init/a90_wififeas.c/h` with:
  - `a90_wififeas_evaluate()`
  - `a90_wififeas_decision_name()`
  - `a90_wififeas_print_summary()`
  - `a90_wififeas_print_full()`
  - `a90_wififeas_print_gate()`
  - `a90_wififeas_print_paths()`
- Added `wififeas [summary|full|gate|paths]` to help and shell command table.
- Reused v103 `a90_wifiinv.c/h` read-only collector as the evidence source.
- Updated ABOUT/changelog top entry to `0.9.4 v104 WIFI FEASIBILITY`.

## Artifacts

| Artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v104` | `ac3220826e78782a7c4fa523b62d893bd3764d6df48b8d68e32065fe111cb802` |
| `stage3/ramdisk_v104.cpio` | `0816ff76577702d28238e86ee32bdc9388646a5c5ca7ae685a544b937947029c` |
| `stage3/boot_linux_v104.img` | `c1fe4f5fe6d569e8ff19ee73d2e6c3742948c605fa36c41c6beef9d1c86fe8eb` |

Ramdisk entries:

```text
/init
/bin/a90sleep
/bin/a90_cpustress
/bin/a90_rshell
```

## Static Validation

- Static ARM64 init build with `-Wall -Wextra` — PASS.
- `stage3/ramdisk_v104.cpio` and `stage3/boot_linux_v104.img` generated from v103 boot args with only ramdisk replaced — PASS.
- Boot image markers found:
  - `A90 Linux init 0.9.4 (v104)`
  - `A90v104`
  - `0.9.4 v104 WIFI FEASIBILITY`
  - `wififeas [summary|full|gate|paths]`
- `git diff --check` — PASS.
- Host Python `py_compile` for `a90ctl.py`, `native_init_flash.py`, `diag_collect.py`, `wifi_inventory_collect.py` — PASS.
- v104 stale marker scan for current-version v103 strings in `init_v104.c`, `v104/*.inc.c`, `a90_config.h`, `a90_menu.c`, and `a90_wififeas.c/h` — PASS.
- Unsafe Wi-Fi operation scan found only deny-list/help text references — PASS.

## Flash Validation

Command:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v104.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.4 (v104)" \
  --verify-protocol auto
```

Result:

- Local image marker and SHA256 check — PASS.
- TWRP push and remote SHA256 check — PASS.
- boot partition prefix SHA256 matched `stage3/boot_linux_v104.img` — PASS.
- Post-boot `cmdv1 version/status` — PASS.

## Device Validation

- `version`: PASS, `A90 Linux init 0.9.4 (v104)`.
- `status`: PASS, `selftest pass=11 warn=0 fail=0`, SD runtime, autohud running, netservice disabled, rshell stopped.
- `bootstatus`: PASS, `BOOT OK shell 4.0s`.
- `selftest verbose`: PASS, `pass=11 warn=0 fail=0`.
- `wifiinv`: PASS, default native summary reports `net total=8 wlan_like=0`, `rfkill total=1 wifi_like=0`, `modules matches=0`, `paths existing=6/26 file_matches=0`.
- `wifiinv full`: PASS, no `wlan*` interface, only `rfkill0 name=bt_power type=bluetooth`, and no WLAN/CNSS/QCA module match in `/proc/modules`.
- `wififeas`: PASS, default native decision `baseline-required`.
- `wififeas gate`: PASS, reports native read-only baseline is required before bring-up.
- `wififeas full`: PASS, gate report shows WLAN interface, Wi-Fi rfkill, module evidence, and firmware/vendor candidates are all absent in default native state.
- `wififeas paths`: PASS, prints native commands, optional Android/TWRP read-only baseline commands, and forbidden operation list.
- `diag`: PASS, compact summary includes v104 version and existing diagnostics coverage.
- `storage`: PASS.
- `runtime`: PASS.
- `service list`: PASS.
- `netservice status`: PASS after `hide`; an initial attempt correctly hit menu busy gate while menu/auto-HUD was active.
- `statushud`: PASS.
- `autohud 2`: PASS.
- `screenmenu`: PASS, nonblocking.
- `hide`: PASS.
- `cpustress 3 2`: PASS, `/bin/a90_cpustress` completed.

Captured host logs:

- `tmp/wififeas/v104-device-validation.txt`
- `tmp/wififeas/v104-mounted-system-feas.txt`
- `tmp/wififeas/v104-native-collector.txt`

## Extended Read-Only Feasibility

Default native init does not mount Android system/vendor paths automatically. A separate read-only check was run:

```text
mountsystem ro
wififeas full
wifiinv full
```

Result:

- `mountsystem ro`: PASS, `/mnt/system` mounted read-only.
- `wififeas full` after mount: PASS, decision `no-go`.
- Reason: Android-side candidates exist, but kernel-facing WLAN/rfkill/module gates are still missing.
- `wifiinv full` after mount: PASS, `paths existing=7/26 file_matches=8`.
- Still no `wlan*` interface, Wi-Fi rfkill entry, or WLAN/CNSS/QCA kernel module match.
- Read-only file matches found under `/mnt/system/system/etc`, including:
  - `/mnt/system/system/etc/init/wifi.rc`
  - `/mnt/system/system/etc/init/wificond.rc`
  - `/mnt/system/system/etc/sysconfig/carrierwifi-sysconfig.xml`
  - `/mnt/system/system/etc/permissions/carrierwifi.xml`
  - `/mnt/system/system/etc/permissions/privapp-permissions-com.samsung.android.server.wifi.mobilewips.xml`
- `/mnt/system/vendor/firmware`, `/mnt/system/vendor/etc/wifi`, and vendor library/bin Wi-Fi paths were not visible in this read-only system mount.

## Host Collector

- `wifi_inventory_collect.py --native-only --boot-image stage3/boot_linux_v104.img --out tmp/wififeas/v104-native-collector.txt`: PASS.
- The collector captured v104 boot image metadata and the native `wifiinv` read-only view.

## Feasibility Decision

Current v104 evidence does **not** justify attempting Wi-Fi enablement from native init.

- Default native state: `baseline-required` because no WLAN/rfkill/module evidence and no Android/vendor candidates are visible.
- Mounted-system read-only state: `no-go` because Android-side config candidates exist, but the required kernel-facing gates are still absent.
- Safe next step is Android/TWRP read-only baseline comparison or a long-run soak/recovery baseline, not direct native Wi-Fi bring-up.

## Current Baseline

`A90 Linux init 0.9.4 (v104)` is now the latest verified native init baseline.

Next planned target: v105 long-run soak/recovery release candidate, unless Android/TWRP Wi-Fi baseline collection is explicitly prioritized first.
