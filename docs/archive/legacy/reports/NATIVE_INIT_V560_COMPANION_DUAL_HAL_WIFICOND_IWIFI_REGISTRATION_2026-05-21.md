# Native Init V560 Companion Dual-HAL Wificond IWifi Registration Report

Date: `2026-05-21`

## Goal

Check whether AOSP `android.hardware.wifi@1.0::IWifi/default` registers when
the bounded native private namespace starts both Android-observed Wi-Fi HAL
binaries plus the companion and `wificond` surface.

## Result

- Decision: `v560-dual-hal-iwifi-registration-observed`
- Pass: `True`
- Reason: AOSP IWifi registration observed in dual-HAL window:
  `android.hardware.wifi@1.0::IWifi/default`
- Evidence: `tmp/wifi/v560-companion-dual-hal-wificond-iwifi-registration`
- Helper: `a90_android_execns_probe v85`
- Helper SHA-256:
  `e98dac60aa3317e86e7ca3053264b7d28257b8c9bd25723bff52438719c148b6`
- Wi-Fi bring-up: not executed

## Scope Confirmation

- Helper v85 was deployed to `/cache/bin/a90_android_execns_probe`.
- The live proof started only the bounded 12-child helper-owned window.
- `lshal wait` was executed only for
  `android.hardware.wifi@1.0::IWifi/default`.
- `IWifi.start()`, supplicant, hostapd, scan/connect/link-up, credentials, DHCP,
  route changes, external ping, reboot, and boot partition writes were not
  executed.
- Post-run residue check found no target process.
- Post-run `/proc/net/dev` check found no Wi-Fi network device.

## Live Result

```text
wifi_companion_hal_order.dual_hal=1
wifi_hal_micro_query.result=service-query-pass
wifi_hal_micro_query.reason=lshal-wait-exit-zero
wifi_hal_micro_query.matched_fqinstance=android.hardware.wifi@1.0::IWifi/default
wifi_companion_hal_order.service_query_result=0
wifi_companion_hal_order.result=service-query-pass
wifi_companion_hal_order.all_postflight_safe=1
wifi_companion_hal_order.scan_connect_linkup=0
wifi_companion_hal_order.external_ping=0
post-run residue: none
wifi netdev: none
```

## Interpretation

V560 closes the registration gap:

- V558 proved Samsung `ISehWifi/default` registration.
- V559 proved AOSP `IWifi/default` does not register with Samsung HAL alone.
- V560 proves the Android-like dual-HAL window registers AOSP
  `IWifi/default`.

The blocker has moved to the next controlled HAL action: one bounded
`IWifi.start()` transaction. Credentials, scan/connect, DHCP, routing, and
external ping remain blocked until a WLAN surface or scan-only-ready marker is
proven.

## Validation

Commands run:

```bash
bash scripts/revalidation/build_android_execns_probe_helper.sh \
  tmp/wifi/v560-a90_android_execns_probe-v85/a90_android_execns_probe

python3 -m py_compile \
  scripts/revalidation/wifi_execns_helper_v85_deploy_preflight.py \
  scripts/revalidation/native_wifi_companion_dual_hal_wificond_iwifi_registration_v560.py

python3 scripts/revalidation/wifi_execns_helper_v85_deploy_preflight.py \
  --apply --assume-yes \
  --approval-phrase "approve v560 deploy execns helper v85 only; no daemon start and no Wi-Fi bring-up" \
  run

python3 scripts/revalidation/native_wifi_companion_dual_hal_wificond_iwifi_registration_v560.py preflight

python3 scripts/revalidation/native_wifi_companion_dual_hal_wificond_iwifi_registration_v560.py \
  --apply --assume-yes \
  --approval-phrase "approve v560 companion plus dual HAL plus wificond IWifi registration wait only; no IWifi.start, no supplicant, no scan/connect/link-up and no external ping" \
  run
```

Result:

```text
decision: v560-dual-hal-iwifi-registration-observed
pass: True
reason: AOSP IWifi registration observed in dual-HAL window: android.hardware.wifi@1.0::IWifi/default
```

## Next Gate

Recommended V561:

1. keep the V560 dual-HAL companion/wificond window;
2. perform exactly one bounded `IWifi.start()` transaction;
3. capture firmware/netdev/readiness markers and cleanup state;
4. still block credentials, scan/connect/link-up, DHCP, routes, and external
   ping until a WLAN surface or scan-only-ready marker is proven.
