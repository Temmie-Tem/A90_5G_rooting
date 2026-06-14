# Native Init V635 Firmware CDSP-Only Proof Live Report

- date: `2026-05-23 KST`
- status: `pass/classified`; Wi-Fi external ping is **not** complete
- runner: `scripts/revalidation/native_wifi_firmware_cdsp_only_proof_v635.py`
- evidence: `tmp/wifi/v635-cdsp-proof-20260523-052940/`
- decision: `v635-cdsp-returned-no-lower-marker`

## Scope

V635 combined the V634 read-only firmware mount parity with exactly one bounded
runtime trigger: `/sys/kernel/boot_cdsp/boot`.

It did not write ADSP/SLPI boot nodes, touch `boot_wlan`, `qcwlanstate`, or
`shutdown_wlan`, start daemons/service-manager/CNSS/Wi-Fi HAL, scan/connect,
use credentials, run DHCP, change routes, or ping externally.

## Result

```text
decision: v635-cdsp-returned-no-lower-marker
pass: True
reason: CDSP write returned but no lower readiness marker advanced
next: inspect dmesg/state for non-QMI CDSP result
device_commands_executed: True
device_mutations: True
sysfs_writes_executed: True
wifi_bringup_executed: False
```

## Checks

| check | result | detail |
| --- | --- | --- |
| native health before proof | pass | native baseline was healthy |
| firmware partition resolution | pass | `apnhlos=sda20`, `modem=sda21` |
| firmware read-only mounts | pass | `/vendor/firmware_mnt` and `/vendor/firmware-modem` mounted during proof |
| CDSP node | pass | `/sys/kernel/boot_cdsp/boot` present |
| CDSP bounded write | pass | child write returned `rc=0`; no timeout |
| cleanup | pass | firmware mounts removed after proof |
| post-health | pass | native health remained `fail=0` |
| Wi-Fi bring-up guardrail | pass | no scan/connect/link-up/external ping was attempted |

## Marker Delta

| marker | delta |
| --- | ---: |
| `cdsp_pil` | 1 |
| `cdsp_power_clock` | 1 |
| `cdsp_brought_reset` | 1 |
| `sysmon_cdsp` | 0 |
| `service_notifier_74` | 0 |
| `service_notifier_180` | 0 |
| `wlan_pd` | 0 |
| `qmi_server_connected` | 0 |
| `wlfw_start` | 0 |
| `bdf_regdb` | 0 |
| `bdf_bdwlan` | 0 |
| `wlan_fw_ready` | 0 |
| `wlan0` | 0 |
| `pm_qos_warning` | 0 |
| `direct_firmware_fail` | 0 |

## CDSP Write Log

```text
v635 cdsp-only begin timeout_sec=8
parent pid=800
child start path=/sys/kernel/boot_cdsp/boot
child write rc=0
parent rc=0 status=0 reaped=1
```

## Interpretation

V635 resolves the earlier CDSP timeout class from V631 under the restored
firmware mount surface. The CDSP loader now reaches PIL/reset/power-clock and
the subsystem state is `ONLINE`, without `pm_qos` warnings or direct firmware
load failures.

That progress still does not publish the lower Wi-Fi QMI readiness chain:
`sysmon_cdsp`, service-notifier `74`, WLAN-PD, WLFW/BDF, firmware-ready, and
`wlan0` all remain absent. CNSS/HAL, Wi-Fi scan/connect, credentials, DHCP, and
external ping therefore remain blocked.

## Next Gate

The next cycle should classify the post-CDSP-online gap. The highest-value
candidate is a bounded no-CNSS/no-HAL observer that starts from a fresh native
baseline, recreates read-only firmware mounts, brings CDSP online, then observes
which additional sibling/service-locator/QRTR condition is missing before
service-notifier `74`.
