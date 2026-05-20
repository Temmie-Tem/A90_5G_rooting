# Native Init v408 Wi-Fi HAL Registration/Service-Surface Evidence Plan

## Scope

V408 classifies the already-approved V407 composite HAL start-only transcript.

It is a host-only evidence packet.  It does not contact the device, start new
processes, start Wi-Fi HAL again, scan, connect, link up, write credentials,
change DHCP/routing, or perform Wi-Fi bring-up.

## Input

- V407 live report: `docs/reports/NATIVE_INIT_V407_COMPOSITE_HAL_START_ONLY_RETRY_LIVE_2026-05-20.md`
- V407 manifest: `tmp/wifi/v407-composite-hal-start-only-retry-live-20260520-101410/manifest.json`
- V407 native transcript: `tmp/wifi/v407-composite-hal-start-only-retry-live-20260520-101410/native/run-composite-hal.txt`

## Classification Rules

The packet is PASS only when all of these are true:

- V407 decision is `v407-composite-hal-start-only-retry-pass`.
- V407 postflight is clean and `wifi_bringup_executed` is false.
- The transcript keeps the no-bring-up boundary:
  - `scan_connect_linkup=0`
  - `wificond=0`
  - `supplicant=0`
  - `hostapd=0`
  - `cnss_diag=0`
- `servicemanager`, `hwservicemanager`, and the first HAL candidate all started.
- Private Binder nodes are present:
  - `/dev/binder c 10:81`
  - `/dev/hwbinder c 10:80`
  - `/dev/vndbinder c 10:79`
- `plat_hwservice_contexts`, `system_ext_hwservice_contexts`, and `vendor_hwservice_contexts` are present.
- `hwservicemanager` and the Wi-Fi HAL child are observable and have proc/fd/maps captures.
- The Wi-Fi HAL maps show the target binary, HwBinder, `libhidlbase`, Android Wi-Fi HIDL libraries, and Samsung Wi-Fi HIDL libraries.
- Fatal runtime markers are absent:
  - `CANNOT LINK EXECUTABLE`
  - missing library errors
  - fatal signal / segmentation fault / abort
  - `avc: denied`

## Output

- runner: `scripts/revalidation/wifi_hal_registration_surface_v408_packet.py`
- evidence directory: `tmp/wifi/v408-hal-registration-surface-packet-*`
- manifest: `manifest.json`
- summary: `README.md`

Output files are written with private handling:

- evidence directory mode `0700`
- files mode `0600`
- exclusive create
- no symlink-follow writes

## Expected Decision

```text
v408-hal-registration-service-surface-evidence-ready
```

This decision means the V407 evidence is strong enough to route the next gate.
It does not prove that the HAL has published a service through
`hwservicemanager`.

## Next Gate

V409 should prove registration more directly while preserving the same safety
boundary:

- start only the same bounded trio in one private namespace
- query `hwservicemanager`/HIDL service surface while the children are alive
- clean all children after the observe window
- keep scan/connect/link-up, credentials, DHCP, routing, and Wi-Fi bring-up
  blocked behind later approvals
