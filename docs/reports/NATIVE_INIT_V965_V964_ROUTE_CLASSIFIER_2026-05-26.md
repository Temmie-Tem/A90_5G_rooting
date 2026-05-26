# V965 V964 Route Classifier Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| host-only route classifier | `tmp/wifi/v965-v964-route-classifier/manifest.json` | `v965-select-wlfw-start-trigger-attribution` |

V965 routes the next work after V963/V964.

## Inputs

- V964: post-provider `/dev/subsys_esoc0` trigger stalls in
  `sdx50m_toggle_soft_reset`.
- V960: provider lifecycle and CNSS netlink are repaired, but MHI/WLFW/BDF and
  `wlan0` remain absent.
- V919/V913: Android positive ordering shows `cnss-daemon wlfw_start` before
  `__subsystem_get(): esoc0 count:0`, then WLAN-PD/BDF/`wlan0`.
- V580: unchanged `qcwlanstate`/`IWifi.start` retries remain demoted because
  the lower module/readiness state has not changed.

## Decision

Do not repeat these as the next gate:

- blind `/dev/subsys_esoc0` open;
- `qcwlanstate ON` retry;
- `IWifi.start` retry;
- Wi-Fi HAL scan/connect;
- credential, DHCP, or external ping work.

The next useful unit is host-only attribution of the Android
`cnss-daemon wlfw_start` trigger source. The question to answer is whether
Android gets `wlfw_start` from HAL/framework, `qcwlanstate`, an init property,
`mdm_helper`/PeripheralManager queue state, or another preceding event.

## Validation

Executed:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_v964_route_classifier_v965.py
python3 scripts/revalidation/native_wifi_v964_route_classifier_v965.py
```

Result:

- decision: `v965-select-wlfw-start-trigger-attribution`
- pass: true
- device commands: false
- device mutations: false

## Next

V966 should analyze existing same-boot Android dmesg/process/property evidence
around the short window before `cnss-daemon wlfw_start`. No new live native
trigger should be attempted before that attribution is complete.
