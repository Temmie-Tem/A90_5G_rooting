# Native Init v410 HAL Registration Query Live

Date: 2026-05-20
Scope: exact-approved bounded `lshal` registration query only

## Result

```text
decision: v410-hal-registration-query-runtime-gap
pass: True
reason: service query failed: lshal-timeout
next: classify lshal/HIDL query failure before wider Wi-Fi work
```

The run stayed inside the approved boundary:

```text
device_commands_executed: True
device_mutations: True
daemon_start_executed: True
wifi_hal_start_executed: True
wifi_bringup_executed: False
scan_connect_linkup: 0
credentials: 0
dhcp_routing: 0
```

`device_mutations=True` here means bounded runtime process start/stop inside the
helper-owned namespace.  It does not mean Android partition writes, firmware
mutation, rfkill writes, scan/connect, DHCP, routing, or persistent Wi-Fi state.

## Approval Boundary

Approved phrase:

```text
approve v410 bounded lshal registration query only; no scan/connect/link-up and no Wi-Fi bring-up
```

The approved command stayed within the native argument budget:

```text
argc: 29
mode: wifi-hal-composite-lshal-list
data_wifi_mode: private-empty
allow_service_manager_start_only: 1
allow_wifi_hal_start_only: 1
allow_hal_service_query: 1
```

## Evidence

Live evidence:

```text
tmp/wifi/v410-registration-query-live-20260520-111836/
```

Preflight immediately before live query:

```text
tmp/wifi/v410-registration-query-ready-preflight-20260520-111747/
decision: v410-hal-registration-query-preflight-ready
pass: True
device_mutations: False
daemon_start_executed: False
wifi_hal_start_executed: False
wifi_bringup_executed: False
```

Live manifest:

```text
v408-registration-surface-pass: pass
native-version: pass
native-clean: pass
helper-v26: pass
lshal-binary: pass
runtime-materials: pass
system-ext-vndk-v30: pass
service-manager-binaries: pass
process-surface-clean: pass
wifi-link-clean: pass
approval-gate: pass
```

## Runtime Observation

The bounded trio started and remained observable until timeout:

```text
servicemanager: child_started=1 observable=1 term_sent=1 kill_sent=0 reaped=1 postflight_safe=1
hwservicemanager: child_started=1 observable=1 term_sent=1 kill_sent=0 reaped=1 postflight_safe=1
wifi_hal: child_started=1 observable=1 term_sent=1 kill_sent=0 reaped=1 postflight_safe=1
all_observable_at_timeout=1
all_postflight_safe=1
```

The query child executed `/system/bin/lshal` but timed out:

```text
wifi_hal_service_query.tool=/system/bin/lshal
wifi_hal_service_query.exists=1
wifi_hal_service_query.executable=1
wifi_hal_service_query.exec_attempted=1
wifi_hal_service_query.child_started=1
wifi_hal_service_query.child.preexec_status=pass
wifi_hal_service_query.child.exec_target=/system/bin/lshal
wifi_hal_service_query.exit_code=-1
wifi_hal_service_query.signal=15
wifi_hal_service_query.timed_out=1
wifi_hal_service_query.result=service-query-timeout
wifi_hal_service_query.reason=lshal-timeout
```

Postflight remained clean:

```text
postflight.clean: True
postflight.processes: []
postflight.wifi_links: []
```

## Interpretation

V410 proves that the private namespace can run the service-manager trio and the
Samsung Wi-Fi HAL candidate together while preserving cleanup and no-Wi-Fi-bringup
boundaries.  It does not yet prove `hwservicemanager` publication listing,
because the default `lshal` invocation timed out before producing a successful
service list.

The timeout is plausible because AOSP `lshal` default listing is broader than the
single question we need.  AOSP documents `lshal` as a device-side tool for HAL
listing, and the source shows default list sections include binderized services,
passthrough clients, and passthrough libraries (`bcl`).  For the next gate, the
query should be narrowed to binderized services only before considering wider
Wi-Fi bring-up.

References:

- <https://source.android.com/docs/core/architecture/vintf/resources>
- <https://android.googlesource.com/platform/frameworks/native/+/013be5f/cmds/lshal/ListCommand.cpp>

## Next Target

V411 should add a helper/runner gate for binderized-only `lshal` listing:

```text
/system/bin/lshal list --types=binderized --neat
```

The next gate must still preserve:

```text
no scan/connect/link-up
no credentials
no DHCP/routing
no persistent Wi-Fi state
postflight clean process surface
postflight clean Wi-Fi link surface
```
