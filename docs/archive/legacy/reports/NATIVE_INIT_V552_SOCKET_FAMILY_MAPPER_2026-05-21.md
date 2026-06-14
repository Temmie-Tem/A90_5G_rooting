# Native Init V552 Socket Family Mapper Report

Date: `2026-05-21`

## Goal

Map companion child `socket:[inode]` file descriptors to in-window kernel
socket tables while the V550/V551 companion service set is alive, without QRTR
nameservice transmit, QMI payload, Wi-Fi HAL start, scan/connect/link-up, DHCP,
route changes, credential handling, or external ping.

## Result

- Decision: `v552-socket-family-unmapped-sockets`
- Pass: `True`
- Reason: companion socket fds mapped to `unix` and `netlink`, but 13 socket
  fds stayed outside the captured socket tables.
- Evidence: `tmp/wifi/v552-companion-socket-family`

## Scope Confirmation

- Helper v78 was deployed with NCM transfer.
- Companion daemons were started only in a bounded start-only window.
- Wi-Fi HAL, scan/connect/link-up, DHCP, route changes, credential handling,
  and external ping were not executed.
- Postflight process check found no target residue.
- Host-side family parsing was tightened to use socket-table `inode` columns,
  not broad numeric-token matching, before the final V552 run.

## Key Evidence

- Socket family counts: `netlink=6`, `unix=9`, `unmapped=13`
- `qrtr-ns` fd `03` remained unmapped.
- `tftp_server` fd `03` mapped to `unix`; fd `06` through `15` remained
  unmapped.
- `pd-mapper` fd `03` mapped to `unix`; fd `04` remained unmapped.
- `cnss_diag` fd `03` mapped to `netlink`; fd `04` through `06` mapped to
  `unix`.
- `cnss-daemon` fd `03`, `07`, `08`, `09`, and `10` mapped to `netlink`; fd
  `04`, `05`, `06`, and `11` mapped to `unix`; fd `13` remained unmapped.

## Interpretation

V552 narrows the blocker but does not clear it:

- V550 cleared the linker/binder service-manager layer.
- V551 showed `QIPCRTR` exists in `/proc/net/protocols`, but no counted QRTR
  sockets appeared in the companion window.
- V552 proves several companion sockets are ordinary `unix` or `netlink`
  sockets, while the QRTR-facing candidates are still not explained by the
  captured tables.
- The next safe unknown is whether the unmapped fds are QRTR-family sockets,
  IPv6 sockets not yet captured, eventfd/signalfd-like descriptors exposed as
  sockets, or a namespace/table visibility gap.

## Next Step

Run a read-only V553 fd-detail mapper before any QRTR nameservice transmit:

1. capture `/proc/<pid>/fdinfo/<fd>` for the companion socket fds;
2. add `tcp6`/`udp6` socket table capture;
3. if feasible, query socket metadata with a bounded diagnostic helper that
   does not send QRTR nameservice or QMI payload;
4. only after the unmapped fds are explained, decide whether a QRTR
   nameservice readback is justified.
