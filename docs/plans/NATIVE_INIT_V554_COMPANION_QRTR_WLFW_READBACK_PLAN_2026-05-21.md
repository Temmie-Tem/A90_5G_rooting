# Native Init V554 Companion QRTR WLFW Readback Plan

Date: `2026-05-21`

## Goal

Check whether the bounded companion service window exposes WLFW QRTR
nameservice events before any QMI payload, Wi-Fi HAL start, scan/connect/link-up,
DHCP, route change, credential handling, external ping, reboot, or boot
partition mutation.

## Changes

- Bump `a90_android_execns_probe` to helper v80.
- Add `--allow-qrtr-ns-readback` as an explicit companion-mode-only flag.
- While companion services are alive, send only QRTR `NEW_LOOKUP` plus cleanup
  `DEL_LOOKUP` for WLFW service `69`, instances `0` and `1`.
- Keep QMI payload, Wi-Fi HAL, scan/connect/link-up, and external ping disabled.

## Safety Contract

- Allowed: deploy helper v80 to `/cache/bin/a90_android_execns_probe`.
- Allowed: bounded companion start-only replay and QRTR nameservice control
  packets for WLFW service `69` only.
- Forbidden: QMI payload, Wi-Fi HAL start, qcwlanstate/write-trigger,
  scan/connect/link-up, DHCP, route changes, credential handling, external ping,
  boot partition writes, reboot, and unbounded receive loops.

## Success Criteria

- Static helper build is ARM64 static and advertises `a90_android_execns_probe v80`.
- Deploy preflight passes with helper v80.
- V554 live run exits with postflight-safe cleanup.
- Final evidence classifies WLFW QRTR readback as service events, end-of-list,
  timeout, or guard failure.
