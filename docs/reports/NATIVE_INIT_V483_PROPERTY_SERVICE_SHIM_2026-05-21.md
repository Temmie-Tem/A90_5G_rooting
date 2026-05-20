# Native Init V483 Property-Service Shim Result

- Date: 2026-05-21 KST
- Scope: native-init bounded Samsung Wi-Fi HAL registration smoke
- Goal: move toward native-init Wi-Fi connect and external ping by isolating the Android property-service blocker
- Result: `v483-samsung-registration-property-shim-negative`
- Pass meaning: bounded negative evidence only; Wi-Fi scan/connect/link-up and external ping are still not achieved

## What Changed

- Added `a90_android_execns_probe v42`.
- Added a helper-owned private `/dev/socket/property_service` shim inside the temporary chroot root only.
- The shim implements only the `PROP_MSG_SETPROP2` shape needed for this proof.
- The allowlist returns success only for `hwservicemanager.ready=true`.
- Any other property set request is denied.
- The shim is killed, reaped, and unlinked during helper cleanup.

## AOSP Basis

- bionic property set path uses `/dev/socket/property_service` and sends `PROP_MSG_SETPROP2`.
- Android init property service replies with a `uint32_t` result.
- `PROP_SUCCESS` is the success result used by property clients.

References:

- <https://android.googlesource.com/platform/bionic/+/master/libc/bionic/system_property_set.cpp>
- <https://android.googlesource.com/platform/system/core/+/8908b264f4e6ba7a0e64bfc2a715b6b2b0f944e7/init/property_service.cpp>
- <https://android.googlesource.com/platform/prebuilts/ndk/+/4448347db136fb3d172c0349c32295c6691df3be/headers/sys/_system_properties.h>

## Evidence

- Build artifact: `tmp/wifi/v483-a90_android_execns_probe-v42/a90_android_execns_probe`
- Build SHA-256: `1204c44843c90e4b7799c6126abfd6036a6e7fbb2560ba21a9c75b3ff7878ff1`
- Deploy evidence: `tmp/wifi/v483-execns-helper-v42-deploy-run-20260521-042433/manifest.json`
- Preflight evidence: `tmp/wifi/v483-samsung-registration-preflight-20260521-043104/manifest.json`
- Live evidence: `tmp/wifi/v483-samsung-registration-run-20260521-043125/manifest.json`
- Live transcript: `tmp/wifi/v483-samsung-registration-run-20260521-043125/native/run-iwifi-registration.txt`

Important live keys:

```text
wifi_hal_composite_start.property_service_shim.started=1
wifi_hal_composite_start.property_service_shim.protocol=PROP_MSG_SETPROP2
wifi_hal_composite_start.property_service_shim.request.1.name=hwservicemanager.ready
wifi_hal_composite_start.property_service_shim.request.1.value=true
wifi_hal_composite_start.property_service_shim.request.1.allowed=1
wifi_hal_composite_start.property_service_shim.request.1.result=0x00000000
wifi_hal_composite_start.property_service_shim.postflight_safe=1
wifi_hal_composite_start.child.wifi_hal.signal=6
wifi_hal_composite_start.result=service-query-runtime-gap
wifi_hal_micro_query.result=service-query-runtime-gap
```

## Interpretation

- The previous `hwservicemanager.ready` property socket absence is no longer the dominant blocker in this proof.
- `hwservicemanager.ready=true` was accepted by the private shim with `PROP_SUCCESS`.
- `vendor.samsung.hardware.wifi@2.x::ISehWifi/default` still did not register.
- The Samsung Wi-Fi HAL process still aborts with `SIGABRT`.
- No Wi-Fi network interface or wireless phy appeared during the smoke.
- Cleanup stayed clean: no residual service-manager/HAL/CNSS processes and no Wi-Fi links.

## Current Native Wi-Fi Status

- Native init Wi-Fi connection: not achieved.
- External ping over Wi-Fi from native init: not achieved.
- Safe bounded registration smoke: achieved for this specific blocker split.
- Next blocker class: Samsung Wi-Fi HAL abort / SELinux domain handoff / runtime surface mismatch.

## Next Work

1. Capture a tighter Samsung HAL abort reason without starting scan/connect.
2. Compare Android boot-complete Samsung HAL process context, argv, env, fds, service files, and SELinux domain against the native private namespace.
3. Re-test whether the `kernel` SELinux context remains the reason HAL aborts after property-service write succeeds.
4. Only after HAL registration is proven, move to bounded HAL readiness calls.
5. Only after HAL readiness is proven, move to scan/connect/link-up and external ping.
