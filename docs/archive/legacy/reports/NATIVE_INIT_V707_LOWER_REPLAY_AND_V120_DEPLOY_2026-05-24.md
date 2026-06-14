# Native Init V707 Lower Replay and Helper v120 Deploy Report

- date: `2026-05-24 KST`
- status: `pass/partial`; Wi-Fi external ping is **not** complete
- V598-class evidence: `tmp/wifi/v707-v598-class-live/`
- helper v120 deploy evidence: `tmp/wifi/v708-helper-v120-deploy-run/`

## Scope

V707 refreshed the lower modem/WLAN precondition after V706 showed the current
idle boot had no service-notifier `180`.

Executed:

- current-boot `mountsystem ro`;
- V401 SELinuxfs mount proof;
- V490 SELinux policy-load proof with helper v119 SHA pinned;
- V598-class modem holder + lower companion WLFW QRTR readback;
- reboot cleanup;
- helper v120 deploy only.

Not executed:

- Wi-Fi HAL, wificond, supplicant, or hostapd start;
- scan/connect/link-up or credential use;
- DHCP, route change, or external ping;
- `qcwlanstate`, `boot_wlan`, or sysfs subsystem writes;
- `esoc0` open/hold;
- boot image or partition writes.

## V598-Class Replay Result

The V598-class replay passed but only restored QRTR/sysmon, not
service-notifier:

```text
decision: v598-wlfw-readback-empty
pass: True
holder_started: True
mss_after_holder: ONLINE
mss_after_companion: ONLINE
mdm3_after_companion: OFFLINING
kernel_warning: 0
```

Marker counts:

| marker | count |
| --- | ---: |
| `qrtr_rx` | `1` |
| `qrtr_tx` | `1` |
| `sysmon_qmi` | `1` |
| `service_notifier` | `0` |
| `wlan_pd` | `0` |
| `qmi_server_connected` | `0` |
| `wlfw` | `0` |
| `bdf` | `0` |
| `wlan0` | `0` |

WLFW service `69` readback was clean but empty:

```text
service_events=0
timeouts=0
end_of_list=2
qmi_attempted=0
```

## Helper v120 Deploy

Helper v120 deployed successfully:

```text
decision: execns-helper-v120-deploy-pass
sha256: acc43d21f948c88350099e1a652a26c7a5f4f0352e06396c6d30dd6908d1ba28
marker: a90_android_execns_probe v120
daemon_start_executed: False
wifi_bringup_executed: False
```

Transfer fell back to serial append and completed successfully. The deploy
itself did not start daemons or Wi-Fi.

## Interpretation

V707 confirms two separate facts:

1. The old V598-class lower replay can still produce QRTR RX/TX and modem
   `sysmon-qmi`, but it did not reproduce service `180` in this boot.
2. Helper v120 is now available for the stronger provider-first path, where
   service `180/74` had previously been reproducible.

The correct next action is therefore not Wi-Fi connect. It is a provider-first
v120 run that captures the live `cnss_daemon_retry` stall point after service
`180/74` and provider registration.
