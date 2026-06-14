# Native Init V809 ICNSS Modules-Not-Initialized Source Classifier Report

## Result

- decision: `v809-modules-not-initialized-source-mapped`
- pass: `true`
- runner: `scripts/revalidation/native_wifi_icnss_modules_not_initialized_source_classifier_v809.py`
- evidence: `tmp/wifi/v809-icnss-modules-not-initialized-source-classifier/`

## What Ran

```bash
python3 -m py_compile scripts/revalidation/native_wifi_icnss_modules_not_initialized_source_classifier_v809.py

python3 scripts/revalidation/native_wifi_icnss_modules_not_initialized_source_classifier_v809.py \
  --out-dir tmp/wifi/v809-icnss-modules-not-initialized-source-classifier-plan-check \
  plan

python3 scripts/revalidation/native_wifi_icnss_modules_not_initialized_source_classifier_v809.py run
```

V809 was host-only. It did not execute any device command.

## Evidence Summary

| Signal | Result |
| --- | --- |
| V808 decision | `v808-overlap-service69-still-absent` |
| V808 provider-first context | present |
| V808 helper alive before `boot_wlan` | present |
| V808 `boot_wlan` write | executed by V808 only |
| V808 `wlan: Loading driver` | `1` marker |
| V808 qcwlanstate/module status markers | `34` |
| V808 driver-loaded marker | `0` |
| V808 ICNSS-QMI / `FW_READY` / WLFW | `0 / 0 / 0` |
| V808 BDF / wiphy / `wlan0` | `0 / 0 / 0` |
| V751/V752 support | HDD/qcwlanstate stall before driver-loaded remains consistent |
| V795/V797 support | modem/PIL lower-window activity does not publish WLFW/service69 |

## Source Classification

V809 maps the runtime state to this source chain:

```text
show_qcwlanstate()
  -> current_driver_status == DRIVER_MODULES_UNINITIALIZED or CLOSED
  -> logs "Modules not initialized just return"
  -> returns OFF

hdd_wlan_start_modules()
  -> hdd_ctx->driver_status = DRIVER_MODULES_ENABLED
  -> hdd_sysfs_update_driver_status(DRIVER_MODULES_ENABLED)
  -> cnss_sysfs_update_driver_status(...)
  -> current_driver_status becomes ENABLED
```

The important source-order result is that `hdd_driver_load()` creates the
qcwlanstate surface before PLD/register-driver completion and before the
`driver loaded` marker. Therefore qcwlanstate existing and returning `OFF` is
not itself a trigger target; it is a status mirror showing QCACLD did not reach
`DRIVER_MODULES_ENABLED`.

The remaining path before `DRIVER_MODULES_ENABLED` is:

```text
boot_wlan
  -> hdd_driver_load()
  -> wlan_hdd_register_driver()
  -> pld_register_driver()
  -> icnss_register_driver()
  -> WLFW service69 arrival / ICNSS-QMI
  -> FW_READY
  -> icnss_call_driver_probe()
  -> hdd_wlan_start_modules()
  -> BDF / wiphy / wlan0
```

## Decision

`qcwlanstate OFF` is not the root cause. It is the visible status mirror for
the real blocker: the PLD/ICNSS register-to-WLFW/FW_READY path has not advanced
far enough for QCACLD to publish `DRIVER_MODULES_ENABLED`.

## Safety

- Host-only classifier; no device command executed.
- No custom kernel flash, boot image write, partition write, or reboot.
- No Wi-Fi HAL, `wificond`, supplicant, hostapd, scan/connect, credential use,
  DHCP, route change, or external ping.
- No `boot_wlan`, `qcwlanstate`, `esoc0`, bind/unbind, module load/unload, or
  driver override.
- No Wi-Fi secret material was written to tracked output.

## Next

V810 should classify the PLD/ICNSS register-to-WLFW/FW_READY boundary from
source and existing evidence before another live retry. The next useful unit is
to determine whether `icnss_register_driver()` is only waiting for WLFW service
`69`/`FW_READY`, or whether an earlier PLD/HDD register return path is failing
silently under stock-kernel observability.
