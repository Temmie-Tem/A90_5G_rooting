# Native Init V589 Android Subsystem State Gap Plan

- date: `2026-05-22 KST`
- objective: compare Android QRTR/sysmon/service-notifier readiness timing with V588 native modem/esoc subsystem window values
- status: `planned`

## Context

V588 captured the native companion-window modem and external modem subsystem values. Both `modem` and `esoc0` reported `OFFLINING`, while QRTR/QMI/WLFW/BDF/FW-ready markers remained absent.

Existing Android evidence already proves that Android reaches:

- QRTR modem readiness RX/TX,
- `sysmon-qmi` modem SSCTL connection,
- `service-notifier` service 180 connection,
- WLAN-PD indication,
- later `sysmon-qmi` `esoc0` SSCTL connection.

However, current Android evidence does not include a direct read-only sysfs sample for `/sys/devices/platform/soc/4080000.qcom,mss/subsys0/state` or `/sys/devices/platform/soc/soc:qcom,mdm3/subsys9/state` at those readiness points. V589 should make that evidence gap explicit instead of guessing that Android is non-offline.

## Gate

- Gate: `host-only` evidence comparison.
- Runner: `scripts/revalidation/native_wifi_android_subsys_state_gap_v589.py`.
- Inputs:
  - `tmp/wifi/v519-android-native-qrtr-modem-delta/manifest.json`
  - `tmp/wifi/v582-modem-companion-classifier/manifest.json`
  - `tmp/wifi/v588-modem-subsys-window-values/manifest.json`
  - `tmp/wifi/v519-android-native-qrtr-modem-delta/inputs/android-dmesg-wifi-cnss-tail.txt`

## Guardrails

- No device command.
- No boot image flash.
- No reboot or recovery handoff.
- No daemon start.
- No subsystem sysfs write.
- No qcwlanstate/sysfs driver-state write.
- No Wi-Fi HAL or `IWifi.start()`.
- No supplicant/hostapd/wificond.
- No scan/connect/link-up/DHCP/routing.
- No external ping.
- No credential use or credential-bearing evidence.

## Implementation

1. Parse Android dmesg timeline markers for QRTR readiness, `sysmon-qmi`, `service-notifier`, WLAN-PD, and `esoc0` SSCTL.
2. Parse V588 native in-window values and lower marker counts.
3. Classify whether:
   - Android readiness timeline is missing,
   - V588 native window data is missing,
   - native remains `OFFLINING` while Android readiness exists,
   - direct Android subsystem state sample is missing,
   - or a true Android/native non-offline state delta is already proven.

## Success Criteria

V589 passes if it produces a defensible host-only classification and explicitly chooses the next gate. It must not attempt live Wi-Fi bring-up. It should only advance to a live trigger if direct evidence proves the lower readiness marker changed or Android/native subsystem state delta is known.

## Expected Decision

Likely decision: `v589-android-subsys-state-sample-needed`.

That means native has in-window `OFFLINING` subsystem values and Android has the readiness timeline, but the current evidence set still lacks direct Android sysfs state values.

## Next Gate After V589

If V589 confirms the direct Android state sample is absent, V590 should collect a read-only Android subsystem state sample around boot/Wi-Fi readiness before planning any subsystem readiness trigger.
