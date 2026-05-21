# Native Init V559 Companion Plus HAL Plus Wificond IWifi Registration Report

Date: `2026-05-21`

## Goal

Check whether AOSP `android.hardware.wifi@1.0::IWifi/default` registers in the
same 11-child native private namespace where V558 observed Samsung
`ISehWifi/default` registration.

## Result

- Decision: `v559-iwifi-registration-timeout`
- Pass: `True`
- Reason: AOSP `IWifi/default` did not appear even though V558 observed Samsung
  `ISehWifi` registration.
- Evidence: `tmp/wifi/v559-companion-hal-wificond-iwifi-registration`
- Helper: `a90_android_execns_probe v84`
- Helper SHA-256:
  `fd3080cea356958c583b0cb2c78e7d4e40584253041de693709036c396c76a55`
- Wi-Fi bring-up: not executed

## Scope Confirmation

- Helper v84 was deployed to `/cache/bin/a90_android_execns_probe`.
- The live proof started only the bounded 11-child helper-owned window.
- `lshal wait` was executed only for
  `android.hardware.wifi@1.0::IWifi/default`.
- `IWifi.start()`, supplicant, hostapd, scan/connect/link-up, credentials, DHCP,
  route changes, external ping, reboot, and boot partition writes were not
  executed.
- Post-run residue check found no target process.
- Post-run `/proc/net/dev` check found no Wi-Fi network device.

## Live Result

```text
wifi_hal_micro_query.result=service-query-timeout
wifi_hal_micro_query.reason=lshal-wait-timeout
wifi_companion_hal_order.service_query_result=12
wifi_companion_hal_order.result=service-query-timeout
wifi_companion_hal_order.all_postflight_safe=1
wifi_companion_hal_order.scan_connect_linkup=0
wifi_companion_hal_order.external_ping=0
post-run residue: none
wifi netdev: none
```

## Interpretation

V559 splits the registration state:

- Samsung extension registration is now proven by V558.
- AOSP `IWifi/default` registration is still absent in the Samsung-HAL-only
  window.
- Raw `IWifi.start()` should not be attempted yet because its target service
  handle is not proven.

The next likely missing piece is the Android legacy Wi-Fi HAL process:
Android boot-complete evidence showed both
`android.hardware.wifi@1.0-service` and
`vendor.samsung.hardware.wifi@2.0-service` running. Native V559 still starts
only the Samsung HAL binary.

## Validation

Commands run:

```bash
bash scripts/revalidation/build_android_execns_probe_helper.sh \
  tmp/wifi/v559-a90_android_execns_probe-v84/a90_android_execns_probe

python3 -m py_compile \
  scripts/revalidation/wifi_execns_helper_v84_deploy_preflight.py \
  scripts/revalidation/native_wifi_companion_hal_wificond_iwifi_registration_v559.py

python3 scripts/revalidation/wifi_execns_helper_v84_deploy_preflight.py \
  --apply --assume-yes \
  --approval-phrase "approve v559 deploy execns helper v84 only; no daemon start and no Wi-Fi bring-up" \
  run

python3 scripts/revalidation/native_wifi_companion_hal_wificond_iwifi_registration_v559.py preflight

python3 scripts/revalidation/native_wifi_companion_hal_wificond_iwifi_registration_v559.py \
  --apply --assume-yes \
  --approval-phrase "approve v559 companion plus HAL plus wificond IWifi registration wait only; no IWifi.start, no supplicant, no scan/connect/link-up and no external ping" \
  run
```

Result:

```text
decision: v559-iwifi-registration-timeout
pass: True
reason: AOSP IWifi/default did not appear even though V558 observed Samsung ISehWifi registration
```

## Next Gate

Recommended V560:

1. start both `android.hardware.wifi@1.0-service` and
   `vendor.samsung.hardware.wifi@2.0-service` in the bounded companion/wificond
   window;
2. wait for AOSP `IWifi/default` registration;
3. still block `IWifi.start()`, credentials, scan/connect/link-up, DHCP, routes,
   and external ping until registration is proven.
