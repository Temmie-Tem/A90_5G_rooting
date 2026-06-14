# Native Init V638 Firmware-Backed Sibling SSCTL Composite Live Report

- date: `2026-05-23 KST`
- status: `blocked/classified`; Wi-Fi external ping is **not** complete
- runner: `scripts/revalidation/native_wifi_firmware_sibling_ssctl_composite_v638.py`
- evidence: `tmp/wifi/v638-firmware-sibling-live-20260523-060104/`
- decision: `v638-firmware-sibling-ssctl-composite-blocked`

## Scope

V638 executed the previously prepared firmware-backed sibling SSCTL observer
from a healthy native baseline. It mounted firmware surfaces read-only, wrote
ADSP/CDSP/SLPI boot nodes in bounded child processes, captured dmesg markers,
cleaned up mounts, and rebooted back to the native baseline.

The run did not write `boot_wlan`, `qcwlanstate`, or `shutdown_wlan`; did not
start service-manager, Wi-Fi HAL, supplicant, hostapd, scan/connect/link-up,
credential handling, DHCP, route changes, or external ping.

## Result

```text
decision: v638-firmware-sibling-ssctl-composite-blocked
pass: False
reason: blocked by kernel-warning-clean
next: clear blockers before live proof
device_commands_executed: True
device_mutations: True
sysfs_writes_executed: True
wifi_bringup_executed: False
external_ping_executed: False
```

## Evidence Matrix

| subject | result | evidence | classification |
| --- | --- | --- | --- |
| firmware mounts | pass | `/vendor/firmware_mnt=True`, `/vendor/firmware-modem=True` | firmware surface was available for the proof window |
| ADSP node | returned | `child_write_rc0=True`, `timed_out=False`, `reaped=1` | bounded write path itself did not hang |
| CDSP node | returned | `child_write_rc0=True`, `timed_out=False`, `reaped=1` | V635 CDSP timeout class stayed fixed |
| SLPI node | returned | `child_write_rc0=True`, `timed_out=False`, `reaped=1` | bounded write path itself did not hang |
| sibling sysmon | absent | `sysmon_slpi=0`, `sysmon_cdsp=0`, `sysmon_adsp=0` delta | firmware-backed direct writes still did not reproduce Android sibling SSCTL publication |
| notifier/WLAN path | absent | `service_notifier_180=0`, `service_notifier_74=0`, `wlan_pd=0`, `wlan0=0` delta | no progress toward Wi-Fi bring-up gate |
| WLFW/BDF | absent | `qmi_server_connected=0`, `wlfw_start=0`, `bdf_regdb=0`, `bdf_bdwlan=0` delta | CNSS/HAL/connect remains blocked |
| kernel warning | blocked | `pm_qos_warning=13`, `kernel_warning=26` delta | direct all-sibling write path must not be repeated |
| cleanup | pass | post-mount hits both false; reboot returned healthy native status | live mutation was bounded and cleaned up |

## Interpretation

V638 closes the main remaining uncertainty from V637: simply making the
ADSP/CDSP/SLPI boot-node writes succeed under read-only firmware mounts is not
enough. All three child writes returned cleanly, but no Android-equivalent
sibling `sysmon-qmi`, service `74`, WLAN-PD, WLFW/BDF, firmware-ready, or
`wlan0` marker advanced.

The important negative result is the warning profile. The run introduced new
`pm_qos_add_request() called for already added request` warnings and kernel
warning frames around `kernel/power/qos.c:616`. This matches the older direct
DSP boot-node warning class and means further blind direct ADSP/CDSP/SLPI
write retries are not justified.

V638 therefore does not move the project to Wi-Fi credentials, scan/connect,
DHCP, routes, or external ping. The blocker is still lower than CNSS/HAL and
now specifically excludes the firmware-backed all-sibling direct-write path.

## Cleanup

Cleanup passed:

- firmware mounts were unmounted after the observation window;
- reboot cleanup completed even though the reboot command naturally did not
  return an `END` marker after reset began;
- post-reboot native health was confirmed with `version_seen=True` and
  `status_healthy=True`;
- current baseline is back on native v319 with `selftest` pass and NCM/tcpctl
  exposure stopped.

## Next Gate

Proceed to V639 as host-only warning-cause and trigger attribution:

1. classify whether V638 warnings are attributable to one node, node ordering,
   repeated all-sibling writes, or a missing Android sequencing prerequisite;
2. compare V638 warning timestamps and workqueue context against V615/V619 and
   warning-free V635/V636 runs;
3. avoid live ADSP/CDSP/SLPI write retries until a per-node or non-write trigger
   hypothesis is supported by existing evidence;
4. keep CNSS/HAL, scan/connect, credentials, DHCP, routes, and external ping
   blocked until service `74`, WLAN-PD, WLFW/BDF, firmware-ready, or `wlan0`
   advances under native init.
