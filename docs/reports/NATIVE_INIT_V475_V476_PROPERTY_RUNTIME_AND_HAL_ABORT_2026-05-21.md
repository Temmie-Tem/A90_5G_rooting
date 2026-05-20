# Native Init V475/V476 Property Runtime And HAL Abort Report

## Status

- Current device control: native init `A90 Linux init 0.9.61 (v319)`
- Final goal status: native-init Wi-Fi connect and external ping are still **not achieved**
- V475 result: Android-readable private property runtime modes repaired
- V476 result: observed property-context gaps removed from the private property root
- Current blocker: Samsung Wi-Fi HAL aborts with `SIGABRT` before `ISehWifi/default` registration

## Evidence

| Step | Decision | Evidence |
| --- | --- | --- |
| V475 mode repair | `v475-android-readable-property-mode-repaired` | `tmp/wifi/v475-android-readable-property-mode-repair-20260521-024612/manifest.json` |
| V476 overlay | `v476-observed-runtime-property-context-ready` | `tmp/wifi/v476-observed-runtime-property-context-overlay2-20260521-025718/manifest.json` |
| V476 incremental deploy | `v476-observed-property-context-incremental-deployed` | `tmp/wifi/v476-observed-property-context-incremental-deploy2-20260521-025726/manifest.json` |
| Samsung registration retry | `v473-samsung-wifi-registration-v471-property-absent` | `tmp/wifi/v473-samsung-registration-after-v476-context2-20260521-025740/manifest.json` |
| Vendor HAL static strings | captured | `tmp/wifi/v477-vendor-wifi-hal-static-20260521-025957/strings-hal.json` |

## What Changed

- V472 deployer now supports Android-compatible runtime modes:
  - property root directories: `0755`
  - property files: `0444`
  - evidence files remain host-private
- V475 repaired the already-deployed V471 remote root in place.
- V476 added observed runtime property keys from live HAL/manager/lshal stderr.
- V476 incremental deploy uploaded only:
  - updated `property_info`
  - missing context prop_area files needed for observed contexts

## Source Basis

- AOSP init writes `/dev/__properties__/property_info` with mode `0444`.
- AOSP bionic creates property area files with `0444`.
- Therefore the private runtime root must be readable by Android service/HAL children after they drop from root to Android UIDs.

References:

- `https://android.googlesource.com/platform/system/core/+/8908b264f4e6ba7a0e64bfc2a715b6b2b0f944e7/init/property_service.cpp`
- `https://android.googlesource.com/platform/bionic/+/refs/heads/main/libc/system_properties/prop_area.cpp`

## Runtime Delta

Before V475:

- `ro.property_service.version` direct lookup passed only as root.
- service-manager/HAL children still logged `old property service protocol`.
- cause: deployed private property files were `0600`, unreadable to uid `1000`/`1010` children.

After V475:

- `old property service protocol` disappeared.
- new gap exposed: many property-context warnings.

After V476:

- property-context warnings dropped to zero in the latest Samsung registration retry.
- remaining stderr is now:
  - `hwservicemanager.ready` property-set socket failure
  - Samsung HAL `SIGABRT`
  - `/dev/kmsg` logging redirection failures plus shell quote noise
  - `Service not found` from `lshal wait`

## Latest Registration Result

`tmp/wifi/v473-samsung-registration-after-v476-context2-20260521-025740/manifest.json`:

- `helper_result=service-query-runtime-gap`
- `micro_query_result=service-query-runtime-gap`
- `micro_query_reason=lshal-wait-nonzero`
- no WLAN/wiphy/rfkill surface appeared
- cleanup stayed clean
- Wi-Fi HAL child:
  - `observable=0`
  - `exited=1`
  - `signal=6`
  - `postflight_safe=1`

## Current Interpretation

The blocker is no longer basic property readability or property context mapping.

The Samsung HAL appears to abort before it can register `vendor.samsung.hardware.wifi@2.x::ISehWifi/default` with `hwservicemanager`. Static strings from the HAL show:

- `service->registerAsService()`
- `Failed to register ISehWifi HAL`
- `ISehWifi Hal is booting up...`
- `ISehWifi Hal is terminating...`
- `/data/vendor/log/wifi/`
- `/sys/wifi/*`
- `/mnt/vendor/efs/wifi/.mac.*`

The likely next gap is Android service execution context, especially SELinux domain parity. Android baseline previously observed the HAL as `u:r:hal_wifi_default:s0`, while native init commands currently run as `kernel`.

## Next Step

Plan V478 as a SELinux/domain parity proof before any scan/connect attempt:

1. Add read-only identity evidence for `/proc/self/attr/current` in helper child snapshots.
2. Add a bounded `selinux-context-proof` mode that attempts a child-only transition to expected Android domains without daemon start.
3. If transition is impossible, document that native init cannot faithfully register this HAL under current SELinux constraints without an init/SELinux-domain handoff.
4. If transition is possible, add an approval-gated HAL start retry with the expected service context and keep scan/connect blocked.

## Guardrails

- No global `/dev/__properties__` replacement.
- No property-service socket creation yet.
- No persistent daemon start.
- No Wi-Fi scan/connect/link-up.
- No credentials read.
- No DHCP/routing/external ping.
