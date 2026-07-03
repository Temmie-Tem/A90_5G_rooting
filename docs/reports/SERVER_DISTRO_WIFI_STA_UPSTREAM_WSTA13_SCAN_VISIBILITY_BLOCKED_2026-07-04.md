# Server-Distro WSTA13 Scan Visibility Blocked

- Date: 2026-07-04
- Scope: Debian scan visibility diagnostic after native WSTA2 materialization
- Native resident: `0.11.140 (v3384-server-distro-hardware-contract)`
- Public exposure: not started
- Final device state: native V3384, `selftest fail=0`

## Summary

WSTA13 instrumented the point that WSTA12 exposed: Debian can start the STA helper and the
supplicant control socket accepts scan commands, but no scan results appear after handoff.

Live result: WSTA2 native materialization passed after the default wait window.  D4 guarded
format/populate passed, the WSTA13 rootfs contained the new scan-visibility helper, and
Debian `switch_root` succeeded on retry after display-owner cleanup.  In Debian, the helper
recorded successful scan trigger return codes but `SCAN_RESULTS` stayed empty through the
initial scan window and both retry scan windows.  The interface operstate stayed `down` and
carrier stayed `0` throughout those scan samples.

No API probe or cloudflared retry was run.

## Source Changes

- `a90_dpublic_wifi_sta.sh`
  - adds `sample_regulatory_state`;
  - adds `scan_visibility_probe`;
  - records `SCAN` trigger rc, scan-result counts, supplicant state, interface operstate,
    and carrier across a six-sample scan window;
  - runs the scan-visibility probe before the first association attempt and before each
    bounded reassociation retry;
  - records whether retry-triggered scans found any results.
- `prepare_wsta3_sta_rootfs.py`
  - records `scan_visibility_present` so private rootfs summaries fail closed when this
    diagnostic helper was not staged.
- Tests now assert the WSTA13 scan visibility marker surface.

## Live Evidence

The live path was:

```text
native V3384 -> native reboot to clear stale link-up state -> WSTA2 materialization
-> WSTA13 private rootfs -> SD upload -> D4 guarded format/populate
-> Debian switch_root -> firstboot STA helper
```

WSTA2 materialization:

```text
first attempt: wlan0_present=1 but link-up failed
native reboot: V3384, selftest fail=0
retry: wsta2-native-materialization-pass
wlan0_wait_elapsed_ms=100261
wlan0_present=1
link_up_rc=0
decision=softap-iftype-probe-pass
```

D4 userdata refresh:

```text
format=done formatter=e2fsprogs-mkfs.ext4 node=/dev/block/a90-userdata label=A90D4ROOT has_journal=1
populate=done root=/mnt/a90-userdata-root marker=userdata=appliance-root
```

WSTA13 helper presence:

```text
scan_visibility_rc=0
scan_marker_rc=0
reg_marker_rc=0
firstboot_rc=0
```

Debian scan visibility markers:

```text
wifi_sta_reg_after_country_country_get_rc=0
wifi_sta_reg_after_country_country_present=0
wifi_sta_reg_after_country_iw_present=0
wifi_sta_scan_initial_trigger_rc=0
wifi_sta_scan_initial_sample_1_results_count=0
wifi_sta_scan_initial_sample_1_wpa_state=DISCONNECTED
wifi_sta_scan_initial_sample_1_operstate=down
wifi_sta_scan_initial_sample_1_carrier=0
...
wifi_sta_scan_initial_sample_6_results_count=0
wifi_sta_scan_initial_sample_6_operstate=down
wifi_sta_scan_initial_found=0
wifi_sta_scan_initial_final_results_count=0
```

Retry scan windows showed the same pattern:

```text
wifi_sta_scan_retry_1_trigger_rc=0
wifi_sta_scan_retry_1_final_results_count=0
wifi_sta_assoc_attempt_1_retry_scan_found=0
wifi_sta_scan_retry_2_trigger_rc=0
wifi_sta_scan_retry_2_final_results_count=0
wifi_sta_assoc_attempt_2_retry_scan_found=0
wifi_sta_wpa_completed=0
wifi_sta_wpa_completed_attempts=3
wifi_sta_carrier_up=0
wifi_sta_decision=wifi-sta-assoc-failed
```

A manual Debian relink/scan check after firstboot did not change the result:

```text
relink_rc=0
scan_1_rc=0
sample_1_count=0
sample_1_operstate=down
scan_2_rc=0
sample_2_count=0
sample_2_operstate=down
scan_3_rc=0
sample_3_count=0
sample_3_operstate=down
```

Interpretation: the blocker is now below association and before gateway/L3.  The native
side can materialize and link-up `wlan0`, but after handoff the Debian scan engine accepts
scan commands while the interface remains effectively down and returns zero visible BSS
results.

## Hygiene

- No public tunnel was started.
- No SSID, PSK, BSSID, MAC, DHCP lease, Wi-Fi private address, gateway, DNS server, public
  URL, generated hostname, or raw API response is recorded in this report.
- Raw transcripts remain under `workspace/private/runs/`.
- The device ended on native V3384 with `selftest: pass=12 warn=1 fail=0`.

## Next

WSTA14 should target the Debian link-state / scan-engine boundary:

- add an optional `iw`-backed diagnostic path to the private rootfs, if available through
  the host package staging flow;
- compare `ip link`/sysfs state immediately before and after `wpa_supplicant` start;
- test whether reasserting link-up after supplicant start changes operstate or scan results;
- capture redacted driver/regulatory/scan failure evidence without printing BSSIDs or SSIDs;
- do not return to gateway keepalive, API probe, or cloudflared until Debian can reliably
  see scan results and associate again.
