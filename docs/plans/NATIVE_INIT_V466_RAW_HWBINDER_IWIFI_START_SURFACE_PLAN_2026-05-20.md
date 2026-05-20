# Native Init V466 Raw hwbinder IWifi.start Surface Plan

Date: 2026-05-20

## Goal

Implement the first bounded native-init `IWifi.start()` live proof.

V466 must answer one narrow question:

> When native init starts the minimal private Android runtime and sends exactly
> one `android.hardware.wifi@1.0::IWifi/default.start()` hwbinder transaction,
> does a WLAN surface appear?

It is still not a Wi-Fi credential, scan, connect, DHCP, route, or external
ping test.

## Inputs

- V462: native connect/ping remains blocked by no `wlan0`/`phy*` surface.
- V464: service-manager + Wi-Fi HAL + `cnss-daemon` stayed clean but created no
  WLAN surface.
- V465: generated-client and existing-tool strategies are not usable now; raw
  hwbinder is the selected next strategy.

## Target Runtime

V466 should prefer the AOSP legacy Wi-Fi HAL target for the first
`IWifi.start()` attempt:

```text
target_profile: vendor-wifi-hal-legacy
target binary: /vendor/bin/hw/android.hardware.wifi@1.0-service
descriptor: android.hardware.wifi@1.0::IWifi
instance: default
```

Reason:

- `IWifi.start()` belongs to the AOSP `android.hardware.wifi@1.0::IWifi`
  interface.
- The Samsung `vendor.samsung.hardware.wifi@2.x::ISehWifi` surface is a vendor
  extension target and should not be treated as a drop-in substitute for
  `IWifi.start()`.
- If the legacy HAL target cannot publish `IWifi/default`, route to a later
  dual-HAL or Samsung-extension-specific gate instead of silently substituting
  another interface.

## Helper Design

Add helper version:

```text
a90_android_execns_probe v32
```

Add mode:

```text
wifi-iwifi-start-surface
```

Add allow flag:

```text
--allow-iwifi-start-only
```

The mode should:

1. materialize the existing V464 private namespace;
2. start `servicemanager`;
3. start `hwservicemanager`;
4. start exactly one Wi-Fi HAL target, defaulting to
   `vendor-wifi-hal-legacy`;
5. start `cnss-daemon -n -l`;
6. snapshot WLAN surface before the hwbinder call;
7. run a short-lived raw hwbinder client child;
8. call `IServiceManager.get(IWifi, default)`;
9. if a non-null handle is returned, call `IWifi.start()` exactly once;
10. snapshot WLAN surface after the call;
11. terminate/reap all children;
12. snapshot WLAN surface after cleanup.

## Raw hwbinder Contract

Pinned transaction contract:

| Step | Descriptor | Code | Args |
| --- | --- | --- | --- |
| Get service | `android.hidl.manager@1.0::IServiceManager` | `1` | `android.hardware.wifi@1.0::IWifi`, `default` |
| Start Wi-Fi HAL | `android.hardware.wifi@1.0::IWifi` | `3` | none |

The raw client should emit machine-readable fields:

```text
iwifi_start.begin=1
iwifi_start.service_get_attempted=1
iwifi_start.service_get_reply=...
iwifi_start.service_handle=...
iwifi_start.start_attempted=...
iwifi_start.start_reply=...
iwifi_start.result=...
iwifi_start.end=1
```

## Runner Design

Add host runner:

```text
scripts/revalidation/native_iwifi_start_surface_v466.py
```

Runner commands:

- `plan`: no device command.
- `preflight`: read-only native state, helper marker, mode/flag strings,
  V465 contract result, no existing Wi-Fi surface.
- `run`: exact approval phrase required, then one bounded helper execution.

Proposed approval phrase:

```text
approve v466 raw hwbinder IWifi.start surface proof only; no scan/connect/link-up and no Wi-Fi bring-up
```

## Decision Labels

- `v466-iwifi-start-plan-ready`
- `v466-iwifi-start-preflight-ready`
- `v466-iwifi-start-approval-required`
- `v466-iwifi-start-service-null`
- `v466-iwifi-start-transaction-failed`
- `v466-iwifi-start-surface-observed-cleaned`
- `v466-iwifi-start-no-surface-delta`
- `v466-iwifi-start-surface-leaked`
- `v466-iwifi-start-review-required`

## Guardrails

- No SSID/password read.
- No scan/connect/link-up.
- No `wpa_supplicant` network configuration.
- No DHCP, DNS, route, or external ping.
- No rfkill write.
- No module load/unload.
- No driver bind/unbind.
- No firmware mutation.
- No Android partition write.
- No persistent boot autostart.
- No unbounded daemon persistence.

## Validation

Host/static:

```text
python3 -m py_compile scripts/revalidation/wifi_iwifi_start_contract_v465.py
python3 -m py_compile scripts/revalidation/native_iwifi_start_surface_v466.py
bash scripts/revalidation/build_android_execns_probe_helper.sh tmp/wifi/v466-a90_android_execns_probe-v32/a90_android_execns_probe
strings tmp/wifi/v466-a90_android_execns_probe-v32/a90_android_execns_probe | rg 'a90_android_execns_probe v32|wifi-iwifi-start-surface|--allow-iwifi-start-only|iwifi_start'
git diff --check
```

Live:

```text
python3 scripts/revalidation/wifi_iwifi_start_contract_v465.py preflight
python3 scripts/revalidation/native_iwifi_start_surface_v466.py plan
python3 scripts/revalidation/native_iwifi_start_surface_v466.py preflight
python3 scripts/revalidation/native_iwifi_start_surface_v466.py run
python3 scripts/revalidation/native_wifi_connect_ping_v462.py preflight
```

## Routing

- If `IWifi.start()` creates a surface and cleanup is clean: rerun V462 and
  advance to a scan-only native gate.
- If service lookup returns null: inspect whether the legacy HAL is absent,
  fails to register, or requires dual-HAL startup.
- If `IWifi.start()` returns successfully but no surface appears: route to
  Android framework mediation rather than widening daemon starts.
- If any process or WLAN surface leaks: stop and require recovery review before
  further Wi-Fi work.
