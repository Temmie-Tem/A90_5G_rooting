# Native Init V466 Raw hwbinder IWifi.start Surface Report

Date: 2026-05-21 KST
Status: `service-null`, bounded cleanup clean
Goal impact: native init Wi-Fi connect/ping is still blocked before credential/scan/connect.

## Summary

V466 added and deployed `a90_android_execns_probe v32`, then executed a bounded native-init
raw hwbinder `IServiceManager.get(android.hardware.wifi@1.0::IWifi/default)` proof while
private `servicemanager`, `hwservicemanager`, `android.hardware.wifi@1.0-service`, and
`cnss-daemon` were running inside the helper-owned namespace.

The run did not read SSID/password, did not scan/connect, did not request DHCP, did not
change routes, and did not send external packets.

## Latest Evidence

| Item | Result |
| --- | --- |
| Helper build | `tmp/wifi/v466-a90_android_execns_probe-v32/a90_android_execns_probe` |
| Helper sha256 | `29ce77fa7215287b3f3948fe19a3667330df52156d2fa8750220fb971d5fb685` |
| Deploy evidence | `tmp/wifi/v466-execns-helper-v32-redeploy3-run-20260521-003346/` |
| Live evidence | `tmp/wifi/v466-raw-hwbinder-iwifi-start-live-20260521-004018/` |
| Cleanup evidence | `tmp/wifi/v466-selinuxfs-runtime-cleanup-20260521-004118/` |
| Device health after cleanup | `status rc=0`, `selftest fail=0`, no Wi-Fi link |

## Live Decision

| Field | Value |
| --- | --- |
| Decision | `v466-raw-hwbinder-iwifi-start-service-null` |
| Pass | `true` |
| Reason | `IWifi/default handle was not returned while bounded process cleanup was clean` |
| daemon_start_executed | `true` |
| wifi_hal_start_executed | `true` |
| iwifi_start_executed | `false` |
| wifi_bringup_executed | `false` |

## Surface Result

| Phase | wlan | phy | proc wireless | Wi-Fi rfkill |
| --- | ---: | ---: | ---: | ---: |
| before | 0 | 0 | 0 | 0 |
| after_iwifi_start | 0 | 0 | 0 | 0 |
| during | 0 | 0 | 0 | 0 |
| after_cleanup | 0 | 0 | 0 | 0 |

## hwbinder Result

The raw client reached `/dev/hwbinder` and protocol `8`, and context handle acquire calls
returned `0`, but every `IServiceManager.get` attempt produced `BR_FAILED_REPLY` before a
non-null `IWifi/default` handle was returned.

The helper now tries manager interface tokens in this order:

1. `android.hidl.manager@1.2::IServiceManager`
2. `android.hidl.manager@1.1::IServiceManager`
3. `android.hidl.manager@1.0::IServiceManager`

All three returned the same failed-reply outcome in the latest live run.

## Interpretation

This no longer looks like a simple missing `IWifi.start()` call. The current blocker is
one layer earlier: native init cannot obtain the `IWifi/default` HIDL handle through the
raw hwbinder client while the bounded private HAL stack is running.

Most likely next branches:

1. Validate the raw parcel contract against a known-good simple hwbinder call such as
   `IServiceManager.list()` or `IBase.interfaceDescriptor()`.
2. Run a bounded `lshal wait/status` mirror in the same V466 namespace to prove whether
   `android.hardware.wifi@1.0::IWifi/default` is registered at all.
3. If `lshal` sees the service but raw hwbinder still fails, repair parcel/object layout.
4. If `lshal` also does not see the service, pivot to HAL registration inputs,
   VINTF/manifest/service rc, and Samsung vendor Wi-Fi HAL mapping.

## Guardrails Preserved

- No SSID/password read.
- No scan/connect/link-up.
- No DHCP, DNS, route, gateway ping, or external ping.
- No rfkill/sysfs write.
- No module load/unload or Android partition write.
- Postflight process/netdev cleanup is clean.
