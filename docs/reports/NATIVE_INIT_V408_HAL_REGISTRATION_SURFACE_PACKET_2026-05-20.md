# Native Init v408 Wi-Fi HAL Registration/Service-Surface Evidence Packet

## Summary

V408 completed as a host-only evidence classification of the V407 live
transcript.

No device command was executed during V408.  No daemon or HAL was started by
V408, and Wi-Fi bring-up remains blocked.

Result:

```text
decision: v408-hal-registration-service-surface-evidence-ready
pass: True
reason: all V407 registration/service-surface evidence checks passed
next_step: plan V409 bounded hwservicemanager/service-list registration query; keep Wi-Fi bring-up blocked
device_commands_executed: False
device_mutations: False
daemon_start_executed: False
wifi_hal_start_executed: False
wifi_bringup_executed: False
```

## Evidence

- V408 runner: `scripts/revalidation/wifi_hal_registration_surface_v408_packet.py`
- V408 evidence: `tmp/wifi/v408-hal-registration-surface-packet-20260520-102249/`
- V408 manifest: `tmp/wifi/v408-hal-registration-surface-packet-20260520-102249/manifest.json`
- V408 summary: `tmp/wifi/v408-hal-registration-surface-packet-20260520-102249/README.md`
- V407 source manifest: `tmp/wifi/v407-composite-hal-start-only-retry-live-20260520-101410/manifest.json`
- V407 source transcript: `tmp/wifi/v407-composite-hal-start-only-retry-live-20260520-101410/native/run-composite-hal.txt`

Evidence output permissions:

```text
700 tmp/wifi/v408-hal-registration-surface-packet-20260520-102249
600 tmp/wifi/v408-hal-registration-surface-packet-20260520-102249/manifest.json
600 tmp/wifi/v408-hal-registration-surface-packet-20260520-102249/README.md
```

## Checks

All V408 checks passed:

```text
v407-start-only-pass: pass
no-bringup-boundary: pass
composite-children-started: pass
private-binder-devnodes: pass
hwservice-context-inputs: pass
wifi-hal-observable-capture: pass
hwservicemanager-observable-capture: pass
wifi-hal-hidl-hwbinder-maps: pass
fatal-runtime-noise-absent: pass
postflight-clean: pass
```

## Boundary Confirmed

The V407 source evidence kept the no-bring-up guard:

```text
wifi_hal_composite_start.scan_connect_linkup=0
wifi_hal_composite_start.wificond=0
wifi_hal_composite_start.supplicant=0
wifi_hal_composite_start.hostapd=0
wifi_hal_composite_start.cnss_diag=0
```

The bounded trio started in the same helper-owned namespace:

```text
wifi_hal_composite_start.child.servicemanager.child_started=1
wifi_hal_composite_start.child.hwservicemanager.child_started=1
wifi_hal_composite_start.child.wifi_hal.child_started=1
```

All relevant postflight markers stayed safe:

```text
wifi_hal_composite_start.child.hwservicemanager.proc_status_captured=1
wifi_hal_composite_start.child.hwservicemanager.fd_summary_captured=1
wifi_hal_composite_start.child.hwservicemanager.maps_summary_captured=1
wifi_hal_composite_start.child.hwservicemanager.postflight_safe=1

wifi_hal_composite_start.child.wifi_hal.proc_status_captured=1
wifi_hal_composite_start.child.wifi_hal.fd_summary_captured=1
wifi_hal_composite_start.child.wifi_hal.maps_summary_captured=1
wifi_hal_composite_start.child.wifi_hal.postflight_safe=1

wifi_hal_composite_start.all_postflight_safe=1
wifi_hal_composite_start.result=start-only-pass
```

## Service Surface Evidence

The private namespace provided Binder/HwBinder/VndBinder nodes:

```text
context.dev_binder.exists=1
context.dev_binder.rdev=10:81
context.dev_hwbinder.exists=1
context.dev_hwbinder.rdev=10:80
context.dev_vndbinder.exists=1
context.dev_vndbinder.rdev=10:79
```

The hwservice context inputs were visible:

```text
context.plat_hwservice_contexts.exists=1
context.system_ext_hwservice_contexts.exists=1
context.vendor_hwservice_contexts.exists=1
```

The Wi-Fi HAL process maps included the expected HIDL/HwBinder surface:

```text
/vendor/bin/hw/vendor.samsung.hardware.wifi@2.0-service
/dev/hwbinder
libhidlbase.so
android.hardware.wifi@1.0.so
vendor.samsung.hardware.wifi@2.0.so
```

Fatal runtime markers were absent in the transcript:

```text
CANNOT LINK EXECUTABLE: absent
library not found: absent
Fatal signal: absent
Segmentation fault: absent
Aborted: absent
avc: denied: absent
```

## Interpretation

V408 proves a narrower point than Wi-Fi bring-up: the V407 bounded composite
run reached a viable Wi-Fi HAL service surface.  The HAL stayed alive through
the observe window with Binder/HwBinder nodes, hwservice context inputs,
HIDL/HwBinder library maps, and clean postflight.

V408 does not prove actual service publication through `hwservicemanager`.
That remains the correct next gate.

## Next Target

Proceed to V409: bounded `hwservicemanager`/service-list registration query.

V409 must keep the V407 boundary:

- no scan/connect/link-up
- no credentials
- no DHCP/routing
- no Wi-Fi interface bring-up
- no persistence/autostart
- same bounded cleanup and postflight checks
