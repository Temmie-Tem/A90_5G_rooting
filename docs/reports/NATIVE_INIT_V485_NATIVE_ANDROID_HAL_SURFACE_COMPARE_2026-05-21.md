# Native Init V485 Native/Android HAL Surface Compare

- Date: 2026-05-21 KST
- Scope: offline evidence comparison
- Result: `v485-hal-surface-domain-and-companion-gap`
- Pass meaning: comparison produced actionable blockers; native-init Wi-Fi connect and external ping are still not achieved

## Evidence

- V485 output: `tmp/wifi/v485-native-android-hal-surface-compare-20260521-045941/manifest.json`
- V485 summary: `tmp/wifi/v485-native-android-hal-surface-compare-20260521-045941/summary.md`
- Android reference: `tmp/wifi/v425-settled-handoff-live-20260520-134752/v423-android-hwservice-bootcomplete-run/manifest.json`
- Android process surface: `tmp/wifi/v425-settled-handoff-live-20260520-134752/v423-android-hwservice-bootcomplete-run/commands/service-processes.txt`
- Native crash evidence: `tmp/wifi/v484-samsung-abort-run-rerun-20260521-045432/manifest.json`
- Native crash transcript: `tmp/wifi/v484-samsung-abort-run-rerun-20260521-045432/native/run-iwifi-registration.txt`

## Android Normal Surface

Android boot-complete evidence shows the Samsung Wi-Fi HAL normally runs as:

```text
u:r:hal_wifi_default:s0 wifi ... vendor.samsung.hardware.wifi@2.0-service
```

Android also has these relevant companion processes:

```text
u:r:hal_wifi_default:s0  wifi   ... android.hardware.wifi@1.0-service
u:r:vndservicemanager:s0 system ... vndservicemanager
u:r:hwservicemanager:s0 system  ... hwservicemanager
u:r:vendor_wcnss_service:s0 system ... cnss-daemon
u:r:vendor_wcnss_service:s0 system ... cnss_diag
u:r:wificond:s0 wifi ... wificond
```

Relevant Android properties:

```text
sys.boot_completed=1
init.svc.servicemanager=running
init.svc.hwservicemanager=running
init.svc.wificond=running
init.svc.vendor.wifi_hal_ext=running
```

## Native Crash Surface

Native V484 starts only the bounded service-manager/HAL/CNSS surface and captures:

```text
wifi_hal.uid=1010
wifi_hal.gid=1010
wifi_hal.groups=1010,1021,3004,3005
wifi_hal.selinux.target=u:r:hal_wifi_default:s0
wifi_hal.selinux.current=kernel
wifi_hal.selinux.exec=kernel
wifi_hal.signal=6
property_service_shim.ready=true accepted
postflight_clean=true
wifi_bringup_executed=false
```

Crash frames:

```text
pc: libc.so +0x8bebc
lr: libc.so +0x8be90
frame0: libbase.so +0x11db4
frame1: libbase.so +0x1397c
frame2: libbase.so +0x12fa8
frame3: vendor.samsung.hardware.wifi@2.0-service +0x5384
frame5: vendor.samsung.hardware.wifi@2.0-service +0x5048
```

## Interpretation

- The dominant proven gap is SELinux domain mismatch.
- Android normal HAL context is `u:r:hal_wifi_default:s0`.
- Native helper requests `u:r:hal_wifi_default:s0`, but observed native current/exec remains `kernel`.
- V483 already removed the simple property-service socket blocker for `hwservicemanager.ready=true`.
- Companion gaps remain: Android runs `android.hardware.wifi@1.0-service` and `vndservicemanager`, while the native bounded smoke does not.
- Those companion gaps should be treated as secondary until the domain mismatch is either fixed or proven non-fatal.

## Next Decision

Recommended order:

1. Capture or prove real post-exec SELinux domain transition for a HAL-like child before any scan/connect.
2. If domain handoff cannot be fixed immediately, run only bounded no-scan companion experiments:
   - dual HAL start: `android.hardware.wifi@1.0-service` plus `vendor.samsung.hardware.wifi@2.0-service`
   - optional `vndservicemanager` start-only surface
3. Re-run Samsung `ISehWifi/default` registration wait.
4. Only after registration succeeds, proceed to HAL readiness method calls.
5. Only after readiness succeeds, proceed to scan/connect/link-up and external ping.

## Safety

- V485 executed no device commands.
- V485 performed no mutation.
- V485 is not Wi-Fi connection proof.
