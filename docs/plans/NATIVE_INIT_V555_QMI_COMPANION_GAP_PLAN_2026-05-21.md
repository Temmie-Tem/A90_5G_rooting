# Native Init V555 QMI Companion Gap Plan

Date: `2026-05-21`

## Goal

V554 proved that the bounded companion window can send WLFW QRTR nameservice
lookups, but WLFW service `69` still returns end-of-list with no service events.
V555 checks whether the next blocker is a missing extra QMI companion service
that exists in the mounted Android images and should be replayed before Wi-Fi
HAL work.

## Scope

Allowed:

- native read-only command execution through `cmdv1`
- mounted system/vendor path inspection
- init rc grep
- process and dmesg snapshots
- private evidence output

Forbidden:

- daemon/service start
- QRTR or QMI payload transmit
- Wi-Fi HAL start
- scan/connect/link-up
- credential handling
- DHCP, route changes, or external ping
- reboot or boot partition write

## Probe

Tool:

```bash
python3 scripts/revalidation/native_wifi_qmi_companion_gap_v555.py run
```

The probe captures:

- current mount and vendor symlink surfaces;
- required companion binary presence:
  `qrtr-ns`, `rmt_storage`, `tftp_server`, `pd-mapper`, `cnss_diag`,
  `cnss-daemon`;
- extra QMI companion candidates:
  `qmiproxy`, `ssgqmigd`, `sysmon-qmi`, `service-notifier`, `tqftpserv`,
  `rmtfs`;
- init rc declarations for Wi-Fi/QMI/CNSS services;
- process and dmesg snapshots for current readiness markers.

## Success Criteria

V555 passes if it proves one of these states:

1. extra QMI companion binaries exist and can be planned as a separate bounded
   start-only gate; or
2. extra QMI companion services are absent from mounted images, so replaying
   them would be a false target and the next gate should move to combined
   companion plus HAL ordering.

V555 blocks if the six required companion binaries are not visible, because
that would invalidate the current native companion replay basis.

## Next Gate

If V555 finds no startable extra QMI companion, proceed to a combined companion
plus HAL order proof. That next proof should still avoid scan/connect/link-up
and only observe whether Android-like service ordering makes WLFW/QMI/BDF
markers appear.
