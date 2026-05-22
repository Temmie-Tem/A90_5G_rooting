# Native Init V638 Firmware-Backed Sibling SSCTL Composite Prep Report

- date: `2026-05-23 KST`
- status: `prep/preflight-ready`; Wi-Fi external ping is **not** complete
- runner: `scripts/revalidation/native_wifi_firmware_sibling_ssctl_composite_v638.py`
- plan evidence: `tmp/wifi/v638-firmware-sibling-plan-20260523-055908/`
- preflight evidence: `tmp/wifi/v638-firmware-sibling-preflight-20260523-055921/`
- decision: `v638-firmware-sibling-ssctl-composite-preflight-ready`

## Scope

V638 prepares a bounded live observer for the V637-selected blocker. The runner
uses the V635 firmware mount pattern, writes ADSP/CDSP/SLPI boot nodes in
separate child processes with timeouts, captures sibling `sysmon-qmi` and
service `74` markers, cleans up firmware mounts, and reboots back to native
baseline after live proof.

The prep and preflight did not execute sysfs writes, start daemons,
service-manager, Wi-Fi HAL, scan/connect, credentials, DHCP, routes, or external
ping.

## Result

```text
decision: v638-firmware-sibling-ssctl-composite-preflight-ready
pass: True
reason: firmware-backed sibling SSCTL prerequisites are present
next: run V638 sibling-proof
device_commands_executed: True
device_mutations: False
sysfs_writes_executed: False
wifi_bringup_executed: False
```

## Runner Contract

| item | contract |
| --- | --- |
| firmware mounts | `apnhlos -> /vendor/firmware_mnt`, `modem -> /vendor/firmware-modem`, read-only |
| node writes | ADSP, CDSP, SLPI each in a bounded child with timeout/reap |
| marker capture | sibling `sysmon-qmi`, service `180/74`, WLAN-PD, WLFW/BDF, firmware-ready, `wlan0`, warnings |
| cleanup | unmount firmware targets, then reboot cleanup and post-native health check |
| Wi-Fi bring-up | explicitly blocked |

## Guardrails

- no `boot_wlan`, `qcwlanstate`, or `shutdown_wlan` write;
- no service-manager, Wi-Fi HAL, supplicant, hostapd, scan/connect/link-up;
- no credential use, DHCP, routes, or external ping;
- stop classification on kernel warning, child timeout, cleanup failure, or
  post-health failure.

## Validation

- `python3 -m py_compile scripts/revalidation/native_wifi_firmware_sibling_ssctl_composite_v638.py`
  passed.
- V638 `plan` command passed and executed no device command.
- V638 `preflight` passed with `device_mutations=False`.

## Next Gate

Run `sibling-proof` only from a healthy native baseline. A successful live result
still does not authorize credentials or external ping unless service `74`,
WLAN-PD, WLFW/BDF, firmware-ready, or `wlan0` advances.
