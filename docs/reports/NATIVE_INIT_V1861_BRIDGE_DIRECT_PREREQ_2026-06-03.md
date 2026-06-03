# Native Init V1861 Bridge Direct Prerequisite Check

## Summary

- Cycle: `V1861`
- Type: live read-only direct prerequisite check with auto-menu busy handling
- Decision: `v1861-direct-prereq-pre-wifi-gap-confirmed-host-pass`
- Label: `direct-prereq-pre-wifi-gap-confirmed`
- Result: PASS
- Reason: Auto-menu busy was removed for direct read-only checks, and WLFW service 69 plus wlan0 remain absent/unproven; connect/ping remain blocked below the prerequisite gate
- Evidence: `tmp/wifi/v1861-bridge-direct-prereq`

## Input

- V1860: `v1860-read-only-smoke-pre-wifi-gap-host-pass` / `read-only-smoke-pre-wifi-gap` / pass `True`

## Direct Prerequisites

- terminal direct reads: `9` / `9`
- ok direct reads: `6` / `9`
- hide retry count: `0`
- busy remaining: `[]`
- wififeas decision: `baseline-required`
- WLFW service 69 present: `False` evidence `[]` direct_qrtr_terminal `True`
- `wlan0` present: `False` absent_confirmed `True` evidence `['stat: /sys/class/net/wlan0: No such file or directory']` wifiinv_wlan_like `0`
- git clean: `True`

## Commands

| name | command | hide | host rc | protocol | terminal |
| --- | --- | --- | ---: | --- | --- |
| status-after-hide | `status` | `False` | `0` | `ok/0` | `True` |
| sys-class-net | `ls /sys/class/net` | `False` | `0` | `ok/0` | `True` |
| wlan0-stat | `stat /sys/class/net/wlan0` | `False` | `0` | `error/-2` | `True` |
| sys-class-ieee80211 | `ls /sys/class/ieee80211` | `False` | `0` | `ok/0` | `True` |
| proc-net-wireless | `cat /proc/net/wireless` | `False` | `0` | `ok/0` | `True` |
| proc-net-qrtr | `cat /proc/net/qrtr` | `False` | `0` | `error/-2` | `True` |
| debug-qrtr-ns | `cat /sys/kernel/debug/qrtr/qrtr-ns` | `False` | `0` | `error/-2` | `True` |
| wifiinv-summary | `wifiinv summary` | `False` | `0` | `ok/0` | `True` |
| wififeas-gate | `wififeas gate` | `False` | `0` | `ok/0` | `True` |

## Safety Scope

This run executed only read-only `a90ctl.py --json --allow-error` observations. `--hide-on-busy` was allowed only to dismiss the native auto menu before retrying the same read-only command. It did not run `version`, start a serial bridge, flash, reboot, stage properties, start actors, open `/dev/subsys_esoc0`, start `boot_wlan`, issue restart-PD request, force RC1, fake ONLINE state, write PMIC/GPIO/GDSC controls, perform eSoC notify, BOOT_DONE spoof, PCI rescan, platform bind/unbind, start Wi-Fi HAL, scan/connect, use credentials, configure DHCP/routes, or external ping.

## Next

- Keep Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping blocked.
- Continue the reviewed SDX50M/PM bridge path; the next useful work must make WLFW service 69 or `wlan0` appear, not retry connect.
