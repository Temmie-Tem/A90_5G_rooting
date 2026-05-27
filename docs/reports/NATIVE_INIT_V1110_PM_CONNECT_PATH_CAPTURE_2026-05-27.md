# V1110 PM Connect Path Capture Report

Date: 2026-05-27

## Result

- Decision: `v1110-pm-connect-syscall-path-read-error`
- Pass: `true`
- Evidence: `tmp/wifi/v1110-pm-connect-path-capture-live/manifest.json`

## Key Evidence

- The target owner thread was reproduced:
  - comm: `Binder:16706_2`
  - wchan: `__subsystem_get`
  - syscall: `openat`
  - path pointer: `0xb400007f8be06198`
- The first `process_vm_readv` probe rejected this as `not-plausible-user-pointer`.

## Interpretation

The V1110 helper captured the right syscall but treated an AArch64 tagged userspace pointer as invalid. The next retry must clear the top-byte tag before reading the string.

## Safety

- Wi-Fi HAL, scan/connect, DHCP, credentials, routes, and external ping remained disabled.
- `subsys_esoc0_open_attempted=0`
- Postflight had no forbidden Wi-Fi link or actor hits.

