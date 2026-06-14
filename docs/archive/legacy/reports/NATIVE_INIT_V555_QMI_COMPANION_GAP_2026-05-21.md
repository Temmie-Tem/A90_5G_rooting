# Native Init V555 QMI Companion Gap Report

Date: `2026-05-21`

## Goal

Classify whether V554's empty WLFW QRTR readback is likely caused by an
unreplayed extra QMI companion service such as `qmiproxy`, `ssgqmigd`,
`sysmon-qmi`, or `service-notifier`.

## Result

- Decision: `v555-extra-qmi-companion-declared-but-absent`
- Pass: `True`
- Reason: init declares extra QMI companion services, but mounted images have
  no startable binaries for `qmiproxy` or `ssgqmigd`.
- Evidence: `tmp/wifi/v555-qmi-companion-gap`
- Wi-Fi bring-up: not executed

## Scope Confirmation

- V555 used read-only native commands only.
- Daemon start, service-manager start, Wi-Fi HAL start, QRTR/QMI payload,
  scan/connect/link-up, DHCP, route changes, external ping, reboot, and boot
  partition writes were not executed.
- Evidence was written through the private evidence helper path.

## Key Evidence

Required companion binaries remain visible:

| binary | present |
| --- | --- |
| `qrtr-ns` | yes |
| `rmt_storage` | yes |
| `tftp_server` | yes |
| `pd-mapper` | yes |
| `cnss_diag` | yes |
| `cnss-daemon` | yes |

Extra QMI companion candidates:

| candidate | init declared | binary present |
| --- | --- | --- |
| `qmiproxy` | yes | no |
| `ssgqmigd` | yes | no |
| `sysmon-qmi` | no | no |
| `service-notifier` | no | no |
| `tqftpserv` | no | no |
| `rmtfs` | no | no |

Init rc evidence:

```text
/mnt/vendor_ro/etc/init/hw/init.qcom.rc:service qmiproxy /system/bin/qmiproxy
/mnt/vendor_ro/etc/init/hw/init.qcom.rc:service ssgqmigd /vendor/bin/ssgqmigd
/mnt/vendor_ro/etc/init/hw/init.qcom.rc:    socket ssgqmig seqpacket 0660 radio inet
```

Known path evidence:

```text
ls: /mnt/system/system/bin/qmiproxy: No such file or directory
ls: /mnt/vendor_ro/bin/ssgqmigd: No such file or directory
ls: /mnt/vendor_ro/bin/sysmon-qmi: No such file or directory
ls: /mnt/vendor_ro/bin/service-notifier: No such file or directory
ls: /mnt/vendor_ro/bin/tqftpserv: No such file or directory
ls: /mnt/vendor_ro/bin/rmtfs: No such file or directory
```

Readiness markers remained absent:

| marker | present |
| --- | --- |
| `qmi_server_connected` | no |
| `WLFW` | no |
| `BDF` | no |
| `wlan0` | no |
| `Modem QMI Readiness` | no |

## Interpretation

V555 rules out the immediate plan of replaying `qmiproxy`, `ssgqmigd`,
`sysmon-qmi`, or `service-notifier` as standalone native services, because the
mounted Android images do not provide startable binaries for them.

The useful blocker moves back to ordering and composition:

- V287 showed Android's first Wi-Fi boundary is `vendor.wifi_hal_ext`, followed
  by `cnss_diag`, `wificond`, then `cnss-daemon`.
- V554 showed the current companion-only window still does not expose WLFW.
- V555 shows there is no obvious extra QMI binary to insert before HAL work.

The next gate should therefore combine the already-proven companion set with
the HAL/service-manager surface in a bounded start-only observe window. The
purpose is not scan or connect; it is only to see whether Android-like ordering
produces `WLFW`, `QMI Server Connected`, `BDF`, or `wlan0` readiness markers.

## Validation

Commands run:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_qmi_companion_gap_v555.py

python3 scripts/revalidation/native_wifi_qmi_companion_gap_v555.py plan
python3 scripts/revalidation/native_wifi_qmi_companion_gap_v555.py preflight
python3 scripts/revalidation/native_wifi_qmi_companion_gap_v555.py run
```

Result:

```text
decision: v555-extra-qmi-companion-declared-but-absent
pass: True
```

## Next Gate

Recommended V556:

1. implement a bounded combined companion plus HAL order proof;
2. start no scan/connect/link-up path;
3. include cleanup and postflight residue checks;
4. capture WLFW/QMI/BDF/wlan0 markers before, during, and after the window;
5. only if readiness markers appear, move to scan-only or `IWifi.start`
   follow-up.
