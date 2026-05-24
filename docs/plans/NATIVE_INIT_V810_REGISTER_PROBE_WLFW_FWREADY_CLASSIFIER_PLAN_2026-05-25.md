# Native Init V810 Register/Probe WLFW/FW_READY Classifier Plan

## Goal

Use V809, V808, V805/V806, and Samsung OSRC source to decide whether the
current blocker is PLD/SNOC/ICNSS registration itself or the later WLFW
service69 / `FW_READY` gate that allows ICNSS to call the QCACLD probe path.

## Scope

- Target script:
  - `scripts/revalidation/native_wifi_register_probe_wlfw_fwready_classifier_v810.py`
- Inputs:
  - V809 qcwlanstate status-mirror source mapping.
  - V808 true-overlap provider-first + `boot_wlan` evidence.
  - V805/V806 WLFW service69 gate evidence.
  - Samsung OSRC source under
    `tmp/wifi/v766-icnss-qcacld-patch-apply-build/source`.
- Source targets:
  - QCACLD HDD register ops.
  - PLD common and PLD SNOC registration.
  - ICNSS register event, event queue, WLFW server arrival, and `FW_READY`
    event handlers.

## Hard Gates

- Host-only: no device command.
- No custom kernel flash, boot image write, partition write, or reboot.
- No Wi-Fi HAL, `wificond`, supplicant, hostapd, scan/connect, credentials,
  DHCP, route change, or external ping.
- No `boot_wlan`, `qcwlanstate`, `esoc0`, bind/unbind, module load/unload, or
  driver override.
- No Wi-Fi secret material in tracked output.

## Success Criteria

- V810 compiles and plan-only manifest passes.
- Source confirms the HDD -> PLD -> PLD SNOC -> ICNSS register path exists.
- Source confirms `__icnss_register_driver()` posts `REGISTER_DRIVER`
  asynchronously with no `ICNSS_EVENT_SYNC` wait.
- Source confirms `icnss_driver_event_register_driver()` stores the callback ops
  but defers probe while `ICNSS_FW_READY` is absent.
- Source confirms `icnss_driver_event_fw_ready_ind()` sets `ICNSS_FW_READY` and
  calls `icnss_call_driver_probe()`.
- V808 still matches that gate: `wlan: Loading driver` and qcwlanstate appear,
  while WLFW/service69, ICNSS-QMI, `FW_READY`, BDF, wiphy, and `wlan0` are
  absent.
- Classifier selects the next pre-HAL blocker without running a live trigger.

## Validation

```bash
python3 -m py_compile scripts/revalidation/native_wifi_register_probe_wlfw_fwready_classifier_v810.py

python3 scripts/revalidation/native_wifi_register_probe_wlfw_fwready_classifier_v810.py \
  --out-dir tmp/wifi/v810-register-probe-wlfw-fwready-classifier-plan-check \
  plan

python3 scripts/revalidation/native_wifi_register_probe_wlfw_fwready_classifier_v810.py run

git diff --check
```
