# Native Init V551 QRTR Window Snapshot Plan

Date: `2026-05-21`

## Goal

Inspect QRTR/QMI readiness during the now-working V550 companion start-only
window without starting Wi-Fi HAL, scanning, connecting, or sending external
traffic.

## Basis

V550 proved that `servicemanager`, `hwservicemanager`, `vndservicemanager`,
QRTR companion services, `cnss_diag`, and `cnss-daemon` can all be observable
and cleaned up under `copy-real` linkerconfig. It also cleared the previous
`vndservicemanager` linker/binder blocker.

Remaining gap:

- `cnss_diag` and `cnss-daemon` reach netlink;
- no QRTR/QMI, WLFW, BDF, WLAN firmware-ready, or `wlan0` marker appears;
- `/proc/net/qrtr` is absent on this 4.14 kernel even though `QIPCRTR` appears
  in `/proc/net/protocols`.

External references used for this plan:

- Linux QRTR Kconfig describes QRTR as the Qualcomm IPC Router used to
  communicate with services from other hardware blocks and notes that userspace
  service listing is required for lookups:
  `https://sbexr.rabexc.org/latest/sources/a9/0605b7d2f4022b.html`
- `linux-msm/tqftpserv` documents that tqftpserv is TFTP over `AF_QIPCRTR`
  and serves Linux filesystem files to other Qualcomm SoC processors:
  `https://github.com/linux-msm/tqftpserv`

## Scope

Allowed under bypass mode:

- build and deploy helper v77;
- rerun the V550 bounded companion start-only window;
- capture in-window `/proc/net/protocols`, `/proc/net/netlink`, attempted
  `/proc/net/qrtr`, and per-child fd symlink summaries;
- classify whether `QIPCRTR` sockets appear while `qrtr-ns`, `tftp_server`,
  `pd-mapper`, `cnss_diag`, and `cnss-daemon` are alive.

Forbidden:

- Wi-Fi HAL start;
- QRTR nameservice transmit;
- QMI payload;
- qcwlanstate/write-trigger;
- scan/connect/link-up, DHCP, route changes, credentials, or external ping;
- boot image or partition writes.

## Implementation

1. Extend `a90_android_execns_probe` to v77.
2. Add in-window `QIPCRTR` protocol socket count snapshots:
   - before companion start;
   - after spawn;
   - after bounded poll while children are still alive;
   - after cleanup.
3. Add per-child fd symlink summaries so QRTR/socket usage is visible without
   ptrace or packet transmission.
4. Add a V551 host wrapper that imports V550, expects helper v77, and classifies:
   - `qrtr-window-sockets-visible-no-fw-marker`;
   - `qrtr-window-no-qipcrtr-sockets`;
   - `qrtr-window-protocol-missing`;
   - or inherited cleanup/runtime failures.

## Success Criteria

- Bounded run remains cleanup-safe.
- No Wi-Fi HAL/scan/connect/external ping is executed.
- Evidence shows whether `QIPCRTR` socket count changes during the companion
  window.
- Evidence records fd-link summaries for QRTR-related children.

## Next Decision

- If no `QIPCRTR` sockets appear, inspect daemon identity/SELinux/runtime setup
  before any HAL retry.
- If `QIPCRTR` sockets appear but no WLFW marker appears, the next bounded
  candidate is QRTR nameservice readback inside the working companion window,
  still with no QMI payload and no Wi-Fi bring-up.
