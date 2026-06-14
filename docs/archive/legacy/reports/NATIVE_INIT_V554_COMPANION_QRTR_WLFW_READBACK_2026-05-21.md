# Native Init V554 Companion QRTR WLFW Readback Report

Date: `2026-05-21`

## Goal

Check whether the bounded native companion service window exposes WLFW QRTR
nameservice events before any QMI payload, Wi-Fi HAL start, scan/connect/link-up,
DHCP, route change, credential handling, external ping, reboot, or boot
partition mutation.

## Result

- Decision: `v554-wlfw-qrtr-readback-empty`
- Pass: `True`
- Reason: WLFW QRTR readback reached end-of-list without service events.
- Evidence: `tmp/wifi/v554-companion-qrtr-readback`

## Scope Confirmation

- Helper v80 was deployed to `/cache/bin/a90_android_execns_probe`.
- Companion daemons were started only in a bounded start-only window.
- Sent only QRTR `NEW_LOOKUP` plus cleanup `DEL_LOOKUP` for WLFW service `69`,
  instances `0` and `1`.
- QMI payload, Wi-Fi HAL start, scan/connect/link-up, DHCP, route changes,
  credential handling, external ping, reboot, and boot partition writes were
  not executed.
- Postflight process check found no target residue.

## Key Evidence

| case | service | instance | socket rc | new lookup rc | del lookup rc | events | service events | end of list | timeout | qmi attempted |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 69 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 |
| 1 | 69 | 1 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 |

Additional evidence:

- `qrtr_readback_service_events=0`
- `qrtr_readback_timeouts=0`
- `qrtr_readback_end_of_list=2`
- `qrtr_readback_qmi_attempted=0`
- Dmesg still lacks `qmi_server_connected`, `BDF`, `WLFW`, `WLAN ready`, or
  `wlan0` markers.

## Interpretation

V554 is a useful negative result:

- The QRTR nameservice control path worked: both `NEW_LOOKUP` and cleanup
  `DEL_LOOKUP` returned `rc=0`.
- The companion window did not expose WLFW service `69` to nameservice readback.
- This argues against immediately retrying Wi-Fi HAL or qcwlanstate; the HAL
  still has no proven firmware-control service behind it.
- The next blocker is likely a missing Android companion/modem readiness piece,
  not the basic QRTR socket or nameservice packet format.

## Next Step

V555 should compare Android and native runtime for modem/QRTR companion services
that are not yet replayed in the native window, especially:

- `qmiproxy`
- `sysmon-qmi`
- `service-notifier`
- any Samsung/vendor init service that owns QRTR/QMI readiness before WLFW
  registration

Then add the smallest bounded start-only replay for the missing service set
before another HAL or Wi-Fi bring-up attempt.
