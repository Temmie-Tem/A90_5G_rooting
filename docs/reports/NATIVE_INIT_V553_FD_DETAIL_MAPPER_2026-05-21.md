# Native Init V553 FD Detail Mapper Report

Date: `2026-05-21`

## Goal

Explain the V552 `unmapped` companion socket fds while the companion service
set is alive, without Wi-Fi HAL start, scan/connect/link-up, DHCP, route
changes, credential handling, external ping, QMI payload, or boot partition
mutation.

## Result

- Decision: `v553-fd-detail-unmapped-sockets`
- Pass: `True`
- Reason: expanded socket-table capture still leaves 13 companion socket fds
  unmapped: `unmapped=13`, `unix=9`, `netlink=6`.
- Evidence: `tmp/wifi/v553-companion-fd-detail`

## Scope Confirmation

- Helper v79 was deployed to `/cache/bin/a90_android_execns_probe`.
- Companion daemons were started only in a bounded start-only window.
- Captured additional `fdinfo`, `tcp6`, `udp6`, `raw`, and `raw6` evidence.
- QRTR nameservice transmit, QMI payload, Wi-Fi HAL start, scan/connect/link-up,
  DHCP, route changes, credential handling, external ping, reboot, and boot
  partition writes were not executed.
- Postflight process check found no target residue.

## Key Evidence

- Socket family counts: `netlink=6`, `unix=9`, `unmapped=13`
- `fdinfo_count=28`, `fdinfo_missing_count=0`
- `fdinfo_ino_missing_count=28`; this kernel exposes `pos`, `flags`, and
  `mnt_id` for these socket fds, but not `ino` in `/proc/<pid>/fdinfo/<fd>`.
- `qrtr-ns` fd `03` remains unmapped with `flags=02`, `mnt_id=6`.
- `tftp_server` fd `06` through `15` remain unmapped with `flags=02`,
  `mnt_id=6`.
- `pd-mapper` fd `04` remains unmapped with `flags=02004002`, `mnt_id=6`.
- `cnss-daemon` fd `13` remains unmapped with `flags=02000002`, `mnt_id=6`.
- Dmesg still lacks `qmi_server_connected`, `BDF`, `WLFW`, `WLAN ready`, or
  `wlan0` markers.

## Interpretation

V553 rules out the simple missing-table hypothesis:

- Adding `tcp6`, `udp6`, `raw`, and `raw6` did not explain the unmapped fds.
- Generic `/proc/net/*` table matching and current `fdinfo` evidence are not
  enough to identify the remaining socket domains on this kernel.
- The unmapped fd distribution still points at the companion QRTR/TFTP path,
  but that remains an inference, not a proven socket-domain classification.
- Generic `sock_diag` is not guaranteed to solve this alone because its visible
  set aligns with the named sockets exposed through `/proc/net/*`.

## References

- Linux `sock_diag(7)` documents kernel socket diagnostics and notes the
  relationship to `/proc/net/unix`, `/proc/net/tcp`, `/proc/net/udp`, and
  related named socket tables:
  <https://man7.org/linux/man-pages/man7/sock_diag.7.html>
- Android common kernel QRTR source shows `AF_QIPCRTR` datagram socket creation
  and the `QIPCRTR` protocol object:
  <https://android.googlesource.com/kernel/common/+/d4d74449367e/net/qrtr/qrtr.c>

## Next Step

V554 should choose one bounded path before QMI/HAL retry:

1. QRTR-specific readback inside the same companion window, using only
   `NEW_LOOKUP` plus cleanup `DEL_LOOKUP` for WLFW service `69`, no QMI payload;
2. or a socket-domain metadata proof that can identify the remaining socket
   domains without relying on `/proc/net/*` table membership.

The more direct Wi-Fi path is option 1, because earlier standalone QRTR probes
already proved the basic QRTR socket/control path and the current blocker is
whether the companion window exposes the WLFW/modem readiness state.
