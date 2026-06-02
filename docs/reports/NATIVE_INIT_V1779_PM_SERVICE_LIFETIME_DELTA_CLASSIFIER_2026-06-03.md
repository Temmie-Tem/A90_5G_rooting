# Native Init V1779 PM-service Lifetime Delta Classifier

## Summary

- Cycle: `V1779`
- Type: host-only classifier
- Decision: `v1779-vndservicemanager-spawn-parity-gap-host-pass`
- Result: `PASS`
- Reason: V1778 fails after policy-load because pm-service exits zombie; V1092 keeps pm-service alive and publishes the provider with vendor vndservicemanager, while V1778 uses the system servicemanager fallback
- Evidence: `tmp/wifi/v1779-pm-service-lifetime-delta-classifier`

## Delta

- V1778 policy-load result: `policy-load-pass`
- V1778 `pm-service` state: `Z`
- V1778 provider seen: `0`
- V1778 VND service-manager target: `/system/bin/servicemanager /dev/vndbinder`
- V1778 shutdown-list values: ``
- V1092 provider-positive: `True`
- V1092 `pm-service` sleeping: `True`
- V1092 VND service-manager target: `/vendor/bin/vndservicemanager /dev/vndbinder`
- V1092 shutdown-list values: `SDX50M, SDX50M modem`
- Source currently forces VND service-manager fallback: `True`

## Interpretation

- The V1778 result is not a modem/WLAN-PD response result: it fails before `vendor.qcom.PeripheralManager` is visible.
- Policy-load and SELinux domain transition are no longer the missing precondition.
- The strongest host-side delta is VND service-manager parity: V1092 uses `/vendor/bin/vndservicemanager /dev/vndbinder`, while V1778 uses `/system/bin/servicemanager /dev/vndbinder` through the helper fallback.
- The next source/build gate should restore vendor `vndservicemanager` spawning for the narrow service-object route, then rerun the same four-label discriminator.

## Safety

- Host-only analysis. No live device command, flash, reboot, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping was performed.
