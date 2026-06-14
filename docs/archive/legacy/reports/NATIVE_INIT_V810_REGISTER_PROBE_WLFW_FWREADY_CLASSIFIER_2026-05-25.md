# Native Init V810 Register/Probe WLFW/FW_READY Classifier Report

## Result

- decision: `v810-register-probe-gated-by-missing-wlfw-fwready`
- pass: `true`
- runner: `scripts/revalidation/native_wifi_register_probe_wlfw_fwready_classifier_v810.py`
- evidence: `tmp/wifi/v810-register-probe-wlfw-fwready-classifier/`

## What Ran

```bash
python3 -m py_compile scripts/revalidation/native_wifi_register_probe_wlfw_fwready_classifier_v810.py

python3 scripts/revalidation/native_wifi_register_probe_wlfw_fwready_classifier_v810.py \
  --out-dir tmp/wifi/v810-register-probe-wlfw-fwready-classifier-plan-check \
  plan

python3 scripts/revalidation/native_wifi_register_probe_wlfw_fwready_classifier_v810.py run
```

V810 was host-only. It did not execute any device command.

## Evidence Summary

| Signal | Result |
| --- | --- |
| V809 input | `v809-modules-not-initialized-source-mapped`, pass |
| V808 input | `v808-overlap-service69-still-absent`, pass |
| V808 `wlan: Loading driver` | `1` |
| V808 qcwlanstate/module status | `34` |
| V808 WLFW / ICNSS-QMI / `FW_READY` | `0 / 0 / 0` |
| V808 BDF / wiphy / `wlan0` | `0 / 0 / 0` |
| V805/V806 support | WLFW service69 remains the selected missing gate |

## Source Classification

V810 maps the register/probe boundary as:

```text
wlan_hdd_register_driver()
  -> pld_register_driver()
    -> pld_snoc_register_driver()
      -> __icnss_register_driver()
        -> post ICNSS_DRIVER_EVENT_REGISTER_DRIVER asynchronously
          -> icnss_driver_event_register_driver()
            -> penv->ops = QCACLD callbacks
            -> if !ICNSS_FW_READY: return without probe

wlfw_new_server()
  -> ICNSS_DRIVER_EVENT_SERVER_ARRIVE
    -> ICNSS-QMI connect
      -> FW_READY indication
        -> set ICNSS_FW_READY
        -> icnss_call_driver_probe()
          -> QCACLD probe/start path
```

Therefore PLD/SNOC registration is not enough to start WLAN. ICNSS can accept
the QCACLD callback registration and still intentionally defer the actual probe
until WLFW service69 publishes and `FW_READY` arrives.

## Decision

The current blocker is not `qcwlanstate` and not a standalone register-driver
trigger. The source/evidence boundary is:

```text
missing WLFW/service69 publication
  -> no ICNSS-QMI connection
  -> no FW_READY
  -> no icnss_call_driver_probe()
  -> no DRIVER_MODULES_ENABLED
  -> qcwlanstate remains OFF
```

## Safety

- Host-only classifier; no device command executed.
- No custom kernel flash, boot image write, partition write, or reboot.
- No Wi-Fi HAL, `wificond`, supplicant, hostapd, scan/connect, credential use,
  DHCP, route change, or external ping.
- No `boot_wlan`, `qcwlanstate`, `esoc0`, bind/unbind, module load/unload, or
  driver override.
- No Wi-Fi secret material was written to tracked output.

## Next

V811 should classify WLFW service69 publication preconditions before another
live trigger. The next useful unit is to reconcile Android/native evidence for
WLAN-PD/modem firmware serving, QRTR service availability, and the lower
companion ordering that should let WLFW appear.
