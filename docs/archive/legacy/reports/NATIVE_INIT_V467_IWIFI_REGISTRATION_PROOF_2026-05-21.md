# Native Init V467 IWifi/default Registration Proof

## Status

- Decision: `v467-iwifi-registration-wait-timeout`
- Result: bounded classification passed, but native Wi-Fi connect/ping is still **not achieved**
- Evidence: `tmp/wifi/v467-iwifi-registration-live-20260521-010150/manifest.json`
- Helper deployed: `a90_android_execns_probe v33`
- Helper SHA-256: `93b93cade7ce1698c2c4b2f5351ab36f5d9032c8167629aa7ae59bb71b0d53aa`

## What Changed

- Added helper mode `wifi-surface-composite-lshal-wait-iwifi`.
- Added an IWifi-specific `lshal wait` target: `android.hardware.wifi@1.0::IWifi/default`.
- Added `scripts/revalidation/native_iwifi_registration_v467.py`.
- Added `scripts/revalidation/wifi_execns_helper_v33_deploy_preflight.py`.
- Kept the live proof bounded to private service-manager, hwservicemanager, legacy Wi-Fi HAL, CNSS, and `lshal wait`.

## Guardrails

- `IWifi.start()` was not called.
- Wi-Fi credentials were not read.
- Scan/connect/link-up/DHCP/route/external ping were not executed.
- `wificond`, supplicant, and hostapd were not started.
- No Android partition write, firmware mutation, rfkill write, driver bind/unbind, or boot autostart was approved.

## Live Result

| Field | Value |
| --- | --- |
| helper result | `service-query-runtime-gap` |
| helper reason | `lshal-wait-query-failed` |
| lshal result | `service-query-timeout` |
| lshal reason | `lshal-wait-timeout` |
| matched fqinstance | empty |
| service-manager started | yes |
| hwservicemanager started | yes |
| Wi-Fi HAL started | yes |
| CNSS started | yes |
| IWifi.start executed | no |
| Wi-Fi bring-up executed | no |
| postflight clean | yes |

## Surface Result

| Phase | wlan | phy | /proc/net/wireless | Wi-Fi rfkill |
| --- | ---: | ---: | ---: | ---: |
| before | 0 | 0 | 0 | 0 |
| during | 0 | 0 | 0 | 0 |
| after cleanup | 0 | 0 | 0 | 0 |

## Interpretation

V466 proved the raw hwbinder `IServiceManager.get(IWifi/default)` path returned a null service handle. V467 then used Android's own `lshal wait android.hardware.wifi@1.0::IWifi/default` inside the same private namespace. That also failed to observe `IWifi/default` within the current bounded wait window.

This shifts the current blocker away from “raw hwbinder parcel/client is definitely wrong” and toward one of these:

1. The legacy Wi-Fi HAL does not register `android.hardware.wifi@1.0::IWifi/default` under this native-init private runtime.
2. Registration needs a longer bounded wait than the current helper gives `lshal wait`.
3. A runtime prerequisite is still incomplete, likely property/init-script/service-context/data-wifi related.

The live proof stayed cleanup-safe: all child processes were reaped, no WLAN/wiphy/rfkill surface remained, and native status after cleanup still reported `fail=0`.

## Next Step

Run an extended registration-latency proof before any scan/connect attempt:

- Increase the bounded `lshal wait IWifi/default` window to use the helper runtime timeout.
- Rebuild/deploy the next helper version.
- Re-run the same private service-manager/HAL/CNSS registration proof.
- Only if `IWifi/default` becomes visible should the flow return to `IWifi.start()` or scan/connect work.
