# Native Init V484 Samsung Wi-Fi HAL Abort Capture

- Date: 2026-05-21 KST
- Scope: bounded native-init Samsung Wi-Fi HAL registration smoke
- Result: `v484-samsung-wifi-hal-abort-capture-pass`
- Pass meaning: crash evidence was captured and cleanup stayed safe; native-init Wi-Fi connect and external ping are still not achieved

## What Changed

- Added `a90_android_execns_probe v43`.
- Added `wifi-surface-composite-lshal-wait-samsung-ptrace` helper mode.
- The mode keeps the V483 private property-service shim and traces only the Samsung Wi-Fi HAL child.
- Captured compact ptrace evidence on HAL `SIGABRT`.
- No scan, connect, link-up, credential read, DHCP, routing change, or external ping was executed.

## Evidence

- Build artifact: `tmp/wifi/v484-a90_android_execns_probe-v43/a90_android_execns_probe`
- Build SHA-256: `1b061faf5031225066d5d58fdef32512b488b72520a2d828a148c5466972ba49`
- Deploy evidence: `tmp/wifi/v484-execns-helper-v43-deploy-rerun-20260521-044744/manifest.json`
- Preflight evidence: `tmp/wifi/v484-samsung-abort-preflight-rerun-20260521-045421/manifest.json`
- Live evidence: `tmp/wifi/v484-samsung-abort-run-rerun-20260521-045432/manifest.json`
- Live transcript: `tmp/wifi/v484-samsung-abort-run-rerun-20260521-045432/native/run-iwifi-registration.txt`

Key captured facts:

```text
wifi_hal_composite_start.child.wifi_hal.traced=1
wifi_hal_composite_start.child.wifi_hal.trace.initial_stop=1
wifi_hal_composite_start.child.wifi_hal.trace.exec_stop=1
wifi_hal_composite_start.child.wifi_hal.trace.crash_stop=1
capture.crash.siginfo.signo=6
capture.crash.maprow.pc.path=/tmp/a90-v231-2785/root/apex/com.android.runtime/lib64/bionic/libc.so
capture.crash.maprow.pc.relative_offset=0x8bebc
capture.crash.maprow.lr.path=/tmp/a90-v231-2785/root/apex/com.android.runtime/lib64/bionic/libc.so
capture.crash.maprow.lr.relative_offset=0x8be90
capture.crash.maprow.frame0_ra.path=/tmp/a90-v231-2785/root/apex/com.android.vndk.v30/lib64/libbase.so
capture.crash.maprow.frame0_ra.relative_offset=0x11db4
capture.crash.maprow.frame3_ra.path=/tmp/a90-v231-2785/root/vendor/bin/hw/vendor.samsung.hardware.wifi@2.0-service
capture.crash.maprow.frame3_ra.relative_offset=0x5384
capture.crash.maprow.frame5_ra.path=/tmp/a90-v231-2785/root/vendor/bin/hw/vendor.samsung.hardware.wifi@2.0-service
capture.crash.maprow.frame5_ra.relative_offset=0x5048
wifi_bringup_executed=false
```

## Android Reference

Reference evidence:

- `tmp/wifi/v425-settled-handoff-live-20260520-134752/v423-android-hwservice-bootcomplete-run/manifest.json`
- `tmp/wifi/v425-settled-handoff-live-20260520-134752/v423-android-hwservice-bootcomplete-run/commands/service-processes.txt`
- `tmp/wifi/v425-settled-handoff-live-20260520-134752/v423-android-hwservice-bootcomplete-run/commands/identity-props.txt`

Android boot-complete process surface showed:

```text
u:r:servicemanager:s0          system  ... S servicemanager
u:r:hwservicemanager:s0        system  ... S hwservicemanager
u:r:vndservicemanager:s0       system  ... S vndservicemanager
u:r:hal_wifi_default:s0        wifi    ... S android.hardware.wifi@1.0-service
u:r:hal_wifi_default:s0        wifi    ... S vendor.samsung.hardware.wifi@2.0-service
u:r:vendor_wcnss_service:s0    system  ... S cnss_diag
u:r:wificond:s0                wifi    ... S wificond
u:r:vendor_wcnss_service:s0    system  ... S cnss-daemon
```

Relevant Android properties:

```text
init.svc.servicemanager=running
init.svc.hwservicemanager=running
init.svc.wificond=running
init.svc.vendor.wifi_hal_ext=running
```

## Interpretation

- V483 already showed that the missing `/dev/socket/property_service` path is not the dominant blocker after `hwservicemanager.ready=true` is accepted.
- V484 shows the Samsung Wi-Fi HAL aborts through libc/libbase with vendor HAL frames still on the stack.
- This strongly points to a HAL-side fatal check or runtime precondition failure, not a simple missing lshal target.
- The Android reference confirms the same HAL normally runs under `u:r:hal_wifi_default:s0` as user `wifi`.
- Native helper attempts that SELinux handoff, but previous V478/V482 evidence still showed unproven domain transition from `kernel`.
- The most likely next blockers are SELinux domain transition mismatch, missing Android init-managed companion services, or missing HAL runtime environment/fd/socket details.

## Next Work

1. Capture Android boot-complete HAL `/proc` surface for the Samsung HAL: `status`, `cmdline`, `environ`, `fd`, `maps`, and SELinux context.
2. Compare Android HAL process surface against V484 native crash surface.
3. Add a native-only `vndservicemanager` bounded start variant only if Android comparison shows it is required.
4. Re-test SELinux domain handoff with an executable that does not crash immediately, or capture post-exec context before HAL fatal.
5. Only after Samsung HAL registration succeeds, proceed to HAL readiness method calls, then scan/connect/link-up, then external ping.
