# Native Init V550 Vnd Service-Manager Copy-Real Replay Report

Date: `2026-05-21`

## Goal

Validate whether Android-captured real linkerconfig lets `vndservicemanager
/dev/vndbinder` stay observable in the bounded native companion replay.

## Scope

Allowed under bypass mode:

- deploy/use helper v76 already present on device;
- bounded `wifi-companion-vnd-service-manager-start-only` replay;
- private service-manager, vendor service-manager, QRTR, rmt/tftp/pd-mapper,
  `cnss_diag`, and `cnss-daemon` start-only window;
- timeout, cleanup, dmesg, process, fd, maps, and manifest capture.

Not executed:

- Wi-Fi HAL start;
- scan/connect/link-up, DHCP, routing, credentials, or external ping;
- boot image or partition write.

## Result

- Decision: `v550-companion-vnd-service-manager-binder-gap-cleared`
- Pass: `True`
- Reason: `vndservicemanager` was observable and real binder transaction
  failures disappeared, but no firmware readiness marker appeared.
- Evidence: `tmp/wifi/v550-companion-vnd-service-manager-copyreal`

## Key Findings

- `vndservicemanager /dev/vndbinder` now starts and is observable under
  `u:r:vndservicemanager:s0`.
- `copy-real` linkerconfig resolves the V549 unresolved `libbinder` symbol
  failure for `vndservicemanager`.
- `servicemanager`, `hwservicemanager`, `vndservicemanager`, QRTR companion
  services, `cnss_diag`, and `cnss-daemon` were all observable.
- Helper result was `companion-window-pass`.
- Postflight safety was clean: all helper-owned children were reaped and a
  host-side process check found no target residue.
- Dmesg showed `cnss_diag` and `cnss-daemon` netlink activity, but no QRTR/QMI,
  WLFW, BDF, WLAN firmware-ready, or `wlan0` readiness marker.

## Counts

- `cnss_diag_netlink`: `11`
- `cnss_daemon_netlink`: `25`
- `rmt_storage`: `2`
- `binder_transaction_failed`: `0`
- `binder_oneway_spam_ioctl_unsupported`: `2`

The two binder ioctl lines are `BINDER_ENABLE_ONEWAY_SPAM_DETECTION` returning
`-22` on this kernel. They are not counted as binder transaction failures.

## Implementation Fixes

- V550 wrapper now removes inherited `--capture-mode ptrace-lite` so the helper
  command stays within the native `cmdv1` argument budget.
- V548/V550 dmesg classification now distinguishes real binder transaction
  failures from unsupported binder oneway-spam-detection ioctls.

## Next Step

The current blocker moved from linker/binder startup to QRTR/QMI readiness:

1. inspect native QRTR/QMI state during the now-working companion window;
2. compare Android QRTR service presence against native replay;
3. only after a QRTR/QMI or WLFW marker appears, decide whether to run bounded
   HAL/qcwlanstate retry.
