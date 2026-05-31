# Native Init V1351 Current Route CNSS/WLFW Precondition Observer Live

## Summary

- Cycle: `V1351`
- Type: bounded live lower-readiness precondition observer
- Decision: `v1351-current-route-cnss-netlink-only`
- Result: PASS
- Evidence:
  - `tmp/wifi/v1351-current-route-cnss-wlfw-precondition-observer-live/manifest.json`
  - `tmp/wifi/v1351-current-route-cnss-wlfw-precondition-observer-live/summary.md`
- Script: `scripts/revalidation/native_wifi_current_route_cnss_wlfw_precondition_observer_live_v1351.py`
- Helper: `/cache/bin/a90_android_execns_probe` (`a90_android_execns_probe v280`)

## Key Observations

| field | value |
| --- | --- |
| private_flag_in_child_script | 1 |
| precondition_flag_in_child_script | 1 |
| timing_sample_count | 120 |
| timing_pm_service_powerup_seen | True |
| pre_emitted | True |
| pre_sample_count | 120 |
| cnss_daemon_started | True |
| cnss_diag_started | False |
| cld80211_seen | True |
| pm_register_ret | not-observed |
| pm_connect_ret | not-observed |
| wlfw_start_seen | False |
| wlfw_service_request_seen | False |
| icnss_qmi_seen | False |
| bdf_seen | False |
| fw_ready_seen | False |
| wlan0_seen | False |
| last_checkpoint | cnss-netlink-only |
| safety_clear | True |

## Decision

current route precondition observer stopped at checkpoint=cnss-netlink-only

V1351 remains below Wi-Fi bring-up. It does not start Wi-Fi HAL, scan,
connect, credential handling, DHCP/routes, or external ping.

## Cleanup And Health

| Check | Result |
| --- | --- |
| helper deployed | `a90_android_execns_probe v280` / `509f7bb1eb599883d337afb167b29e271c3fe238e1bb1205fb9a93229263c278` |
| post selftest | `rc=0`, `fail=0` |
| post netservice | `enabled=no`, `ncm0=absent`, `tcpctl=stopped` |
| forbidden actions | Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping all `0` |

## Next

classify the next missing prerequisite before PMIC/GPIO/GDSC/eSoC mutation or Wi-Fi HAL bring-up
