# Native Init V589 Android Subsystem State Gap Classifier

- date: `2026-05-22 KST`
- objective: compare Android QRTR/sysmon/service-notifier readiness timing with V588 native modem/esoc subsystem window values
- status: `classified`; Wi-Fi external ping is **not** complete

## Scope

- Runner: `scripts/revalidation/native_wifi_android_subsys_state_gap_v589.py`
- Evidence: `tmp/wifi/v589-android-subsys-state-gap/`
- Plan: `docs/plans/NATIVE_INIT_V589_ANDROID_SUBSYS_STATE_GAP_PLAN_2026-05-22.md`
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

## V589 Result

```text
decision: v589-android-subsys-state-sample-needed
pass: True
reason: native V588 window captured modem/esoc OFFLINING and Android reaches QRTR/sysmon/service-notifier/WLAN-PD, but current Android evidence lacks direct subsystem state values
next: collect Android read-only subsystem state around boot/Wi-Fi readiness, then decide whether a subsystem readiness trigger is justified
device_commands_executed: False
device_mutations: False
wifi_bringup_executed: False
```

## Checks

```text
android-readiness-timeline-present=pass
v519-reference-consistent=pass
v582-kernel-path-classification-present=pass
v588-native-window-present=pass
native-subsys-offlining-captured=pass
native-lower-markers-absent=pass
android-direct-subsys-state-sample=warn
```

## Android Readiness Timeline

Android reaches the lower modem/QRTR readiness path:

```text
qrtr_modem_readiness_rx @ 6.356s
qrtr_modem_readiness_tx @ 7.001s
sysmon_qmi_modem @ 7.006s
service_notifier_180 @ 7.028s
wlan_pd_indication @ 9.421s
sysmon_qmi_esoc0 @ 11.364s
```

## Native V588 Window Values

Native companion-window values remain below that Android readiness path:

```text
mss_name=modem
mss_state=OFFLINING
mdm3_name=esoc0
mdm3_state=OFFLINING
rpmsg_drivers_autoprobe=1
subsys_value_captures=12
```

Native lower marker counts remain zero:

```text
qrtr_modem_readiness=0
qmi_server_connected=0
wlfw_start=0
wlfw_thread=0
bdf_regdb=0
bdf_bdwlan=0
wlan_fw_ready=0
wlan0_event=0
wma_service_ready=0
```

## Interpretation

- V589 confirms the current blocker is still below qcwlanstate/HAL/scan/connect.
- Android proves the QRTR/sysmon/service-notifier/WLAN-PD path exists on this kernel and vendor userspace.
- Native proves companion start-only plus private firmware mounts do not move `modem` or `esoc0` out of `OFFLINING`.
- The missing evidence is now narrow: direct Android sysfs state values for `modem` and `esoc0` around boot/Wi-Fi readiness.
- Without that direct Android state sample, a subsystem readiness trigger would still be speculative.

## Validation

```bash
python3 -m py_compile scripts/revalidation/native_wifi_android_subsys_state_gap_v589.py
git diff --check
python3 scripts/revalidation/native_wifi_android_subsys_state_gap_v589.py plan
python3 scripts/revalidation/native_wifi_android_subsys_state_gap_v589.py run
```

Tracked diff secret scan for the target network strings returned no hits.

## Next Gate

Recommended V590:

1. Boot Android or use an Android-side collector window.
2. Collect read-only values for:
   - `/sys/devices/platform/soc/4080000.qcom,mss/subsys0/{name,state,restart_level,firmware_name,crash_count}`
   - `/sys/devices/platform/soc/soc:qcom,mdm3/subsys9/{name,state,restart_level,firmware_name,crash_count}`
   - `/sys/bus/rpmsg/devices`
   - `/proc/net/qrtr`
3. Timestamp the sample relative to QRTR/sysmon/service-notifier/WLAN-PD readiness if possible.
4. Return to native and compare V590 Android values against V588 native values.
5. Only plan a subsystem readiness trigger if Android proves a non-offline state delta before the Wi-Fi HAL/scan/connect gate.
