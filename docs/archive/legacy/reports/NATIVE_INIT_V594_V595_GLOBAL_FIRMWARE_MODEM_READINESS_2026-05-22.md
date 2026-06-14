# Native Init V594/V595 Global Firmware Modem Readiness Report

- date: `2026-05-22 KST`
- status: `classified`; Wi-Fi external ping is **not** complete

## Scope

- V594 runner: `scripts/revalidation/native_wifi_global_firmware_subsys_pil_v594.py`
- V595 runner: `scripts/revalidation/native_wifi_global_firmware_modem_open_v595.py`
- V594 evidence: `tmp/wifi/v594-global-firmware-subsys-pil-proof/`
- V595 evidence: `tmp/wifi/v595-global-firmware-modem-open-proof/`

## Guardrails

- No daemon start.
- No service-manager.
- No Wi-Fi HAL or `IWifi.start()`.
- No `qcwlanstate` or driver-state sysfs write.
- No supplicant, hostapd, or wificond.
- No scan/connect/link-up.
- No credentials, DHCP, route changes, or external ping.
- Firmware mounts were read-only and temporary.

## V594 Result

V594 combined global read-only firmware mounts with the existing V592 helper subsystem hold-open proof.

Runner result:

```text
decision: v594-global-firmware-subsys-cleanup-review
pass: False
reason: temporary subsystem hold child was not proven cleaned
daemon_start_executed: False
wifi_bringup_executed: False
```

Important positive evidence:

```text
firmware_class_path=/vendor/firmware_mnt/image
mounted_hits={'/vendor/firmware_mnt': True, '/vendor/firmware-modem': True}
modem_blob_visible={'/vendor/firmware-modem/image/modem.b00': True}
mss: OFFLINING -> ONLINE
rpmsg_ipcrtr_present: 0 -> 1
```

Dmesg delta proved the missing firmware mount was the key lower blocker:

```text
subsys-pil-tz 4080000.qcom,mss: modem: loading ...
subsys-pil-tz 4080000.qcom,mss: modem: Brought out of reset
qrtr: Modem QMI Readiness RX cmd:0x2 node[0x0]
```

V594 also opened `esoc0`; that path left the helper child not proven cleaned. Native was rebooted afterward and returned cleanly to `A90 Linux init 0.9.61 (v319)`.

## V595 Result

V595 removed the helper and opened only the modem subsystem char device while the same global firmware mounts were active.

Runner result:

```text
decision: v595-global-firmware-modem-open-readiness-delta
pass: True
reason: modem-only open reached lower readiness without esoc0 open
daemon_start_executed: False
wifi_bringup_executed: False
```

Evidence:

```text
v595.modem_open.opened=1
v595.modem_open.closed=1
mounted_hits={'/vendor/firmware_mnt': True, '/vendor/firmware-modem': True}
post_mount_hits={'/vendor/firmware_mnt': False, '/vendor/firmware-modem': False}
modem_blob_visible={'/vendor/firmware-modem/image/modem.b00': True}
```

Dmesg delta:

```text
subsys-pil-tz 4080000.qcom,mss: modem: loading ...
subsys-pil-tz 4080000.qcom,mss: modem: Brought out of reset
subsys-pil-tz 4080000.qcom,mss: modem: Power/Clock ready interrupt received
qrtr: Modem QMI Readiness RX cmd:0x2 node[0x0]
```

Safety caveat:

```text
subsystem_put: esoc0 count:0
esoc0: subsystem_put: Reference count mismatch
WARNING: CPU: 7 PID: 567 at drivers/soc/qcom/subsystem_restart.c
icnss: Modem went down
```

The V595 script was patched after this run so future executions classify this kernel WARNING as a failure instead of a clean pass. Native was rebooted afterward and returned cleanly to `A90 Linux init 0.9.61 (v319)`.

## Interpretation

- The V593 blocker was correct: native needed Android-style global firmware visibility for modem PIL loading.
- The required modem blobs are visible under `/vendor/firmware-modem/image`, not under `/vendor/firmware_mnt/image`.
- Global read-only `apnhlos` and `modem` mounts plus `subsys_modem` open are sufficient to reach modem PIL reset release and QRTR readiness RX.
- Raw subsystem char-device open/close is not yet a safe reusable trigger because close produces a subsystem reference mismatch and modem shutdown path.
- qcwlanstate, Wi-Fi HAL, scan/connect, credentials, DHCP, routing, and external ping remain blocked until the modem readiness trigger has a safe hold/release contract.

## Next Gate

Recommended V596:

1. Design a bounded modem-readiness holder that keeps only `subsys_modem` open while global firmware mounts are active.
2. Start the companion stack only while the modem fd is held.
3. Do not close the fd during the live window; use reboot as the cleanup boundary for the first proof if needed.
4. Observe QRTR TX, sysmon-qmi, service-notifier, WLAN-PD, WLFW/QMI, BDF, and `wlan0`.
5. Continue blocking Wi-Fi scan/connect and credentials until lower readiness markers advance beyond QRTR RX.

