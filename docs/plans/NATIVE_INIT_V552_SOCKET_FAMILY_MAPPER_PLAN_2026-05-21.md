# Native Init V552 Socket Family Mapper Plan

Date: `2026-05-21`

## Goal

Map companion child socket fd inode numbers to kernel socket tables during the
working V551 companion window.

## Basis

V551 showed:

- `QIPCRTR` protocol exists in `/proc/net/protocols`;
- `QIPCRTR` socket count stays `0` before, during, and after the companion
  window;
- `qrtr-ns`, `tftp_server`, `pd-mapper`, `cnss_diag`, and `cnss-daemon` all hold
  generic `socket:[inode]` fds.

The next useful question is not whether the processes are alive, but which
socket families those fds actually belong to.

## Scope

Allowed under bypass mode:

- build/deploy helper v78;
- rerun bounded companion start-only;
- capture in-window `/proc/net/unix`, `/proc/net/netlink`, `/proc/net/packet`,
  `/proc/net/tcp`, `/proc/net/udp`, and sockstat files;
- host-side classify child socket inodes as `netlink`, `unix`, `tcp`, `udp`,
  `packet`, `unmapped`, or `unknown`.

Forbidden:

- QRTR nameservice transmit;
- QMI payload;
- Wi-Fi HAL start;
- qcwlanstate/write-trigger;
- scan/connect/link-up, DHCP, route changes, credentials, or external ping;
- boot image or partition writes.

## Success Criteria

- Bounded run remains cleanup-safe.
- Socket fd inode mapping is captured for QRTR-related companion children.
- The next blocker is classified as:
  - no QRTR socket family visible;
  - only netlink/UNIX/binder runtime visible;
  - or QRTR-like surface needs a nameservice readback proof.

## Next Decision

If no QRTR socket family is proven, inspect Android-only service prerequisites
such as `qmiproxy`, `sysmon-qmi`, and `service-notifier` before any HAL retry.
If a QRTR socket path is proven, the next bounded candidate is QRTR nameservice
readback inside the companion window, still without QMI payload or Wi-Fi
bring-up.
