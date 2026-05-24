# Native Init V809 ICNSS Modules-Not-Initialized Source Classifier Plan

## Goal

Map V808's repeated `icnss: Modules not initialized just return` evidence to
the Samsung OSRC ICNSS/QCACLD source path and decide whether `qcwlanstate OFF`
is the cause or only a status mirror for a deeper pre-WLFW blocker.

## Scope

- Target script:
  - `scripts/revalidation/native_wifi_icnss_modules_not_initialized_source_classifier_v809.py`
- Inputs:
  - V808 true-overlap provider-first + `boot_wlan` evidence.
  - V751/V752 HDD/qcwlanstate stall evidence.
  - V795/V797 modem/PIL lower-window evidence.
  - Samsung OSRC source staged under
    `tmp/wifi/v766-icnss-qcacld-patch-apply-build/source`.
- Source targets:
  - `drivers/soc/qcom/icnss.c`
  - `drivers/soc/qcom/icnss_qmi.c`
  - QCACLD HDD `wlan_hdd_main.c`
  - QCACLD HDD driver ops and PLD SNOC registration path.

## Hard Gates

- Host-only: no device command.
- No custom kernel flash, boot image write, partition write, or reboot.
- No Wi-Fi HAL, `wificond`, supplicant, hostapd, scan/connect, credentials,
  DHCP, route change, or external ping.
- No `boot_wlan`, `qcwlanstate`, `esoc0`, bind/unbind, module load/unload, or
  driver override.
- No Wi-Fi secret material in tracked output.

## Success Criteria

- V809 compiles and plan-only manifest passes.
- Source confirms `show_qcwlanstate()` reports `OFF` while
  `current_driver_status` remains `DRIVER_MODULES_UNINITIALIZED` or
  `DRIVER_MODULES_CLOSED`.
- Source confirms QCACLD publishes `DRIVER_MODULES_ENABLED` through
  `hdd_sysfs_update_driver_status()` only after `hdd_wlan_start_modules()`
  succeeds.
- Source confirms `boot_wlan` calls `hdd_driver_load()`, which creates the
  qcwlanstate surface before PLD/register-driver completion and before the
  `driver loaded` marker.
- V808 evidence remains consistent: true overlap reached `wlan: Loading driver`
  and qcwlanstate, but not driver-loaded, ICNSS-QMI, `FW_READY`, BDF, wiphy, or
  `wlan0`.
- Classifier selects the next blocker without widening into HAL/scan/connect or
  reviving custom-kernel flashing.

## Validation

```bash
python3 -m py_compile scripts/revalidation/native_wifi_icnss_modules_not_initialized_source_classifier_v809.py

python3 scripts/revalidation/native_wifi_icnss_modules_not_initialized_source_classifier_v809.py \
  --out-dir tmp/wifi/v809-icnss-modules-not-initialized-source-classifier-plan-check \
  plan

python3 scripts/revalidation/native_wifi_icnss_modules_not_initialized_source_classifier_v809.py run

git diff --check
```
