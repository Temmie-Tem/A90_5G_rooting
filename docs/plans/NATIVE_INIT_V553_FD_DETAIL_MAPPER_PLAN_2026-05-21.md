# Native Init V553 FD Detail Mapper Plan

Date: `2026-05-21`

## Goal

Explain the V552 `unmapped` companion socket fds without QRTR nameservice
transmit, QMI payload, Wi-Fi HAL start, scan/connect/link-up, DHCP, route
changes, credential handling, or external ping.

## Changes

- Bump `a90_android_execns_probe` to helper v79.
- Add compact `/proc/<pid>/fdinfo/<fd>` capture for socket fds observed in the
  bounded companion window.
- Add in-window capture for `/proc/net/tcp6`, `/proc/net/udp6`,
  `/proc/net/raw`, and `/proc/net/raw6`.
- Add host-side V553 classification that keeps V552 socket-family mapping but
  includes fdinfo `ino`, `mnt_id`, and `flags` for each companion socket fd.

## Safety Contract

- Allowed: deploy helper v79 to `/cache/bin/a90_android_execns_probe`.
- Allowed: bounded companion start-only replay with existing cleanup.
- Forbidden: QRTR nameservice transmit, QMI payload, Wi-Fi HAL start,
  qcwlanstate/write-trigger, scan/connect/link-up, DHCP, route changes,
  credential handling, external ping, boot partition writes, and reboot.

## Success Criteria

- Static helper build is ARM64 static and advertises `a90_android_execns_probe v79`.
- Deploy preflight passes with helper v79.
- V553 live run exits with postflight-safe cleanup.
- Report identifies whether V552 unmapped fds are resolved by expanded tables
  or still require a socket-domain metadata/readback step.
