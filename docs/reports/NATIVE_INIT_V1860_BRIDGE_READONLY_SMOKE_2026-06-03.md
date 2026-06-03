# Native Init V1860 Bridge Read-Only Smoke

## Summary

- Cycle: `V1860`
- Type: live read-only native-init bridge smoke for Wi-Fi prerequisite gating
- Decision: `v1860-read-only-smoke-pre-wifi-gap-host-pass`
- Label: `read-only-smoke-pre-wifi-gap`
- Result: PASS
- Reason: Read-only bridge commands succeed, but WLFW service 69 and wlan0 are absent/unproven; Wi-Fi HAL, scan/connect, DHCP, routes, credentials, and external ping remain blocked
- Evidence: `tmp/wifi/v1860-bridge-readonly-smoke`

## Input

- V1859: `v1859-transport-locator-repo-bridge-ready-host-pass` / `transport-locator-repo-bridge-ready` / pass `True`

## Prerequisite State

- core read-only commands ok: `True` details `{'status': True, 'bootstatus': True, 'selftest': True}`
- successful read-only commands: `6` / `12`
- busy read-only commands after menu activation: `6`
- wifiinv `wlan_like` count: `0`
- wififeas decision: `baseline-required`
- WLFW service 69 present: `False` evidence `[]`
- `wlan0` present: `False` evidence `[]`
- git clean: `True`

## Commands

| name | command | host rc | protocol | ok |
| --- | --- | ---: | --- | --- |
| status | `status` | `0` | `ok/0` | `True` |
| bootstatus | `bootstatus` | `0` | `ok/0` | `True` |
| selftest | `selftest` | `0` | `ok/0` | `True` |
| netservice-status | `netservice status` | `0` | `ok/0` | `True` |
| wifiinv-summary | `wifiinv summary` | `0` | `ok/0` | `True` |
| wififeas-gate | `wififeas gate` | `0` | `ok/0` | `True` |
| sys-class-net | `ls /sys/class/net` | `0` | `busy/-16` | `False` |
| wlan0-stat | `stat /sys/class/net/wlan0` | `0` | `busy/-16` | `False` |
| sys-class-ieee80211 | `ls /sys/class/ieee80211` | `0` | `busy/-16` | `False` |
| proc-net-wireless | `cat /proc/net/wireless` | `0` | `busy/-16` | `False` |
| proc-net-qrtr | `cat /proc/net/qrtr` | `0` | `busy/-16` | `False` |
| debug-qrtr-ns | `cat /sys/kernel/debug/qrtr/qrtr-ns` | `0` | `busy/-16` | `False` |

## Safety Scope

This run executed only read-only `a90ctl.py --json --allow-error` commands from the safe observation set. It did not run `version`, start a serial bridge, flash, reboot, stage properties, start actors, open `/dev/subsys_esoc0`, start `boot_wlan`, issue restart-PD request, force RC1, fake ONLINE state, write PMIC/GPIO/GDSC controls, perform eSoC notify, BOOT_DONE spoof, PCI rescan, platform bind/unbind, start Wi-Fi HAL, scan/connect, use credentials, configure DHCP/routes, or external ping.

## Next

- Keep Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping blocked.
- Next useful unit is below this gate: continue the reviewed SDX50M/PM bridge path until WLFW service 69 and `wlan0` appear.
