# Native Init V551 QRTR Window Snapshot Report

Date: `2026-05-21`

## Goal

Capture QRTR/QMI readiness state while the V550 companion services are alive,
without Wi-Fi HAL start, QRTR nameservice transmit, QMI payload, scan/connect,
or external ping.

## Result

- Decision: `v551-qrtr-window-no-qipcrtr-sockets`
- Pass: `True`
- Reason: `QIPCRTR` is present in `/proc/net/protocols`, but the in-window
  socket count stayed `0`.
- Evidence: `tmp/wifi/v551-companion-qrtr-window`

## Scope Confirmation

- Helper v77 was deployed with NCM transfer.
- Companion daemons were started only in a bounded start-only window.
- Wi-Fi HAL, scan/connect/link-up, DHCP, route change, credential handling, and
  external ping were not executed.
- Postflight process check found no target residue.

## Key Evidence

- `wifi_companion_start.net_before.qipcrtr_sockets=0`
- `wifi_companion_start.net_after_spawn.qipcrtr_sockets=0`
- `wifi_companion_start.net_window.qipcrtr_sockets=0`
- `wifi_companion_start.net_after_cleanup.qipcrtr_sockets=0`
- `/proc/net/qrtr` was absent: `wifi_companion_start.net_window.qrtr_captured=0`
- `qrtr-ns` had one generic socket fd: `capture.wifi_hal_composite_qrtr_ns.fd_links.socket_count=1`
- `tftp_server`, `pd-mapper`, `cnss_diag`, and `cnss-daemon` had socket fds, but
  V551 did not yet map those socket inodes to protocol families.

## Interpretation

V551 moved the blocker again:

- V550 cleared the linker/binder service-manager layer.
- V551 shows the companion daemons can hold socket fds, but no in-window
  `QIPCRTR` socket is counted by the kernel protocol table.
- The immediate unknown is whether these fds are UNIX, netlink, binder-related,
  or QRTR sockets that this kernel does not expose through the protocol counter.

## Next Step

Run a bounded socket-family mapper during the same companion window:

1. capture `/proc/net/unix`, `/proc/net/netlink`, and related socket tables;
2. map child fd socket inode numbers to their table family;
3. only if QRTR service sockets are proven, consider QRTR nameservice readback;
4. still do not send QMI payload, start Wi-Fi HAL, scan/connect, or ping.
