# Native Init V471 Extended Private Property Runtime Report

## Status

- Decision: `v471-extended-private-property-runtime-ready`
- Result: host-only layout generated; native Wi-Fi connect/ping is still **not achieved**
- Evidence: `tmp/wifi/v471-extended-private-property-runtime/manifest.json`
- Tool: `scripts/revalidation/native_property_runtime_overlay_v471.py`

## What V471 Builds

V471 generates a host-only private `/dev/__properties__` layout that covers the V470 property gap:

- 29 selected properties
- 16 SELinux property contexts
- serialized `property_info`
- `properties_serial`
- one generated `prop_area` file per mapped context

No generated file was installed on the device in V471.

## Key Coverage

| Group | Examples |
| --- | --- |
| build/vendor basics | `ro.build.version.sdk`, `ro.hardware`, `ro.product.name`, `ro.vendor.build.version.sdk` |
| property-service protocol | `ro.property_service.version=2` |
| boot status | `sys.boot_completed=1`, `dev.bootcomplete=1` |
| Wi-Fi hints | `wifi.interface=wlan0`, `wlan.driver.status=ok` |
| service status | `init.svc.servicemanager`, `init.svc.hwservicemanager`, `init.svc.vendor.wifi_hal_ext`, `init.svc.cnss-daemon` |
| bionic/linker reads | `ro.debuggable`, `ro.vndk.version`, `ro.vendor.redirect_socket_calls`, debug/libc/heapprofd keys |

## Validation

| Check | Result |
| --- | --- |
| V295 context input | PASS |
| V470 gap input | PASS |
| selected key mapping | PASS |
| context filenames | PASS |
| property_info/prop_area roundtrip | PASS |
| runtime safety gate | PASS |

## Generated Layout

| Metric | Value |
| --- | ---: |
| property count | 29 |
| context count | 16 |
| output files | 18 |
| `property_info` size | 3268 bytes |
| device commands executed | 0 |
| runtime files installed | 0 |

## Guardrails

- No global `/dev/__properties__` replacement.
- No `/dev/socket/property_service` creation.
- No property mutation or `setprop`.
- No service-manager/HAL/CNSS/wificond/supplicant start.
- No Wi-Fi scan/connect/link-up/DHCP/routing/external ping.

## Next Step

Deploy this layout under a versioned private root such as `/mnt/sdext/a90/private-property-v317/v471/dev/__properties__`, then rerun:

1. property lookup proof against the V471 root;
2. Samsung `ISehWifi/default` registration proof against the V471 root;
3. only if registration passes, proceed to bounded Wi-Fi HAL readiness before scan/connect.
