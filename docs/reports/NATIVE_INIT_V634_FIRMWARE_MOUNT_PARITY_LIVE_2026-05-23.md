# Native Init V634 Firmware Mount Parity Live Report

- date: `2026-05-23 KST`
- status: `verified/live-mount-cleanup`; Wi-Fi external ping is **not** complete
- runner: `scripts/revalidation/native_wifi_firmware_mount_parity_v584.py`
- preflight evidence: `tmp/wifi/v634-v584-preflight-20260523-052042/`
- mount-proof evidence: `tmp/wifi/v634-v584-mount-proof-20260523-052129/`
- decision: `v584-firmware-modem-mount-proof-no-readiness-delta`
- result label: `v634-firmware-mount-parity-clean-no-delta`

## Scope

V634 reused the existing V584 firmware/modem mount-parity runner as a bounded
live mount proof for the V633 blocker.

The run created temporary native paths, mounted firmware partitions read-only,
verified the mount surface, then unmounted and removed the temporary paths.

No ADSP/CDSP/SLPI boot-node write, `boot_wlan`, `qcwlanstate`, companion daemon
start, service-manager start, CNSS start, Wi-Fi HAL start, scan/connect,
credential use, DHCP, route change, or external ping was executed.

## Preflight Result

```text
decision: v584-firmware-modem-mount-proof-preflight-ready
pass: True
reason: apnhlos/modem read-only mount proof prerequisites are present
device_mutations: False
wifi_bringup_executed: False
```

Resolved partitions:

| partition | device | major:minor | size_blocks |
| --- | --- | --- | --- |
| `apnhlos` | `sda20` | `259:4` | `97280` |
| `modem` | `sda21` | `259:5` | `199680` |

## Mount-Proof Result

```text
decision: v584-firmware-modem-mount-proof-no-readiness-delta
pass: True
reason: read-only firmware/modem mount parity completed and cleaned up, but no QRTR/modem marker delta appeared without companion activity
device_mutations: True
wifi_bringup_executed: False
```

Mounts established:

| target | result |
| --- | --- |
| `/vendor/firmware_mnt` | mounted read-only from temporary `apnhlos` block node |
| `/vendor/firmware-modem` | mounted read-only from temporary `modem` block node |

Cleanup:

| cleanup check | result |
| --- | --- |
| `/vendor/firmware-modem` unmount | pass |
| `/vendor/firmware_mnt` unmount | pass |
| temporary `/vendor` directories | removed |
| temporary proof block nodes | removed |
| post native health | pass |

Marker delta during mount-only window:

| marker | delta |
| --- | --- |
| QRTR modem RX | `0` |
| QRTR modem TX | `0` |
| sysmon-qmi | `0` |
| service-notifier | `0` |
| WLAN-PD | `0` |
| QMI server connected | `0` |
| WLFW | `0` |

## Interpretation

V634 proves the V633 missing firmware surface can be recreated and cleaned up
safely with read-only mounts:

```text
apnhlos -> /vendor/firmware_mnt
modem   -> /vendor/firmware-modem
```

Mount-only does not trigger lower QRTR/sysmon/service-notifier readiness. That
is expected: the next gate must combine the now-proven firmware mount parity
with a narrow CDSP-specific trigger rather than retry ADSP/SLPI or attempt
Wi-Fi HAL/connection.

## Next Gate

Proceed to V635:

1. create the same read-only firmware mount surface;
2. write only `/sys/kernel/boot_cdsp/boot` in a bounded child;
3. capture CDSP PIL, `sysmon_cdsp`, service `74`, WLAN-PD, WLFW/BDF, and
   kernel warnings;
4. cleanup by unmounting when safe and rebooting if CDSP state requires it;
5. keep Wi-Fi HAL, `boot_wlan`, `qcwlanstate`, scan/connect, credentials,
   DHCP, routes, and external ping blocked unless lower markers advance.
