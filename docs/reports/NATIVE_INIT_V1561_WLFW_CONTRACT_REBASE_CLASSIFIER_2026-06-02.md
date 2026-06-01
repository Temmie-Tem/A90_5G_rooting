# Native Init V1561 WLFW Contract Rebase Classifier

## Summary

- Cycle: `V1561`
- Type: host-only WLFW contract rebase classifier
- Decision: `v1561-current-wlfw-contract-rebases-v966-service-window-next`
- Result: `PASS`
- Reason: V966 and V1560 agree that Android reaches cnss-daemon wlfw_start before esoc0/BDF while the current native test route never reaches wlfw_start; current v1393 test boot is hardcoded to the post-PM observer route, but the helper already contains bounded Android Wi-Fi service-window modes
- Evidence: `tmp/wifi/v1561-wlfw-contract-rebase-classifier`

## Inputs

| input | path |
| --- | --- |
| v966_wlfw_attribution | tmp/wifi/v966-android-wlfw-start-attribution/manifest.json |
| v1560_current_order | tmp/wifi/v1560-android-order-vs-native-route-classifier/manifest.json |
| native_v1496_log | tmp/wifi/v1496-wifi-rc1-window-short-hold-handoff/test-v1393-log.stdout.txt |
| native_v1557_log | tmp/wifi/v1557-native-endpoint-long-hold-handoff/test-log.stdout.txt |
| helper_source | stage3/linux_init/helpers/a90_android_execns_probe.c |
| pid1_wifi_test_source | stage3/linux_init/v724/90_main.inc.c |

## Contract Comparison

| source | wlfw_start | esoc0 | BDF | FW-ready | wlan0 |
| --- | --- | --- | --- | --- | --- |
| Android prior attribution | 8.349631 | 8.402277 | 9.476146 | 14.580127 | 14.950217 |
| Android current reference | 43.444373 | 43.547935 | 44.514027 | 49.428211 | 49.775275 |
| Native V1496 current route | missing | 9.132753 | missing | missing | missing |
| Native V1557 current route | missing | 9.102002 | missing | missing | missing |

## Derived Checks

| check | value |
| --- | --- |
| v966_pass | True |
| v966_wlfw_before_esoc0 | True |
| v966_native_cnss_netlink_without_wlfw | True |
| v1560_pass | True |
| v1560_android_order_ok | True |
| v1560_native_route_lacks_wlfw | True |
| native_v1496_mode_post_pm_observer | True |
| native_v1557_mode_post_pm_observer | True |
| current_route_not_service_window | True |
| pid1_test_boot_hardcoded_post_pm_observer | True |
| helper_service_window_ready | True |

## Current Native Route

| artifact | modes |
| --- | --- |
| native_v1496 | wifi-companion-post-pm-mdm-helper-esoc-observer |
| native_v1557 | wifi-companion-post-pm-mdm-helper-esoc-observer |

The current v1393 Wi-Fi test boot is still wired to `wifi-companion-post-pm-mdm-helper-esoc-observer` via `/bin/a90_android_execns_probe`. That route is useful for PM/eSoC observer diagnostics, but it does not reproduce Android's pre-`esoc0` `cnss-daemon wlfw_start` contract.

## Helper Service-Window Surface

| capability | present |
| --- | --- |
| service_window_start_only_mode | yes |
| service_window_subsys_capture_mode | yes |
| service_window_allow_flag | yes |
| service_window_capture_allow_flag | yes |
| service_window_rejects_scan_connect | yes |
| service_window_rejects_other_actor_flags | yes |
| wificond_target_profile | yes |
| wifi_hal_legacy_profile | yes |
| wifi_hal_ext_profile | yes |
| wificond_property_key | yes |
| cnss_daemon_property_key | yes |
| wlfw_kmsg_summary | yes |

## PID1 Test-Boot Flags

| flag | present |
| --- | --- |
| --allow-pm-service-trigger-observer | yes |
| --allow-post-pm-mdm-helper-esoc-observer | yes |
| --allow-post-pm-mdm-helper-lower-trace | yes |
| --pm-observer-start-mdm-helper-after-cnss | yes |
| --pm-observer-start-mdm-helper-before-cnss | yes |
| --pm-observer-mknod-esoc-dev-node-before-cnss | yes |
| --pm-observer-private-firmware-mounts | yes |
| --allow-android-wifi-service-window | no |

## Interpretation

V966 and V1560 now agree on the important ordering: Android reaches `cnss-daemon wlfw_start`/`wlfw_service_request` before `/dev/subsys_esoc0`, BDF, FW-ready, and `wlan0`. Native V1496/V1557 reaches generic `cnss-daemon` netlink and the PM/eSoC observer route, then forced RC1 diagnostics fail before L0, but the route never emits `wlfw_start`.

Therefore the next live-relevant unit should not be another credentialed connect attempt and should not treat forced RC1 enumerate as the primary trigger. First rebuild or select a bounded Android Wi-Fi service-window route and verify whether native can produce `wlfw_start`/`wlfw_service_request` at all.

## Next Gate

- Recommended cycle: `V1562`
- Type: source/build-only route selector before live
- Focus: make the native Wi-Fi test boot select the existing Android Wi-Fi service-window start-only mode, or build an equivalent bounded helper runner

### Success Markers

- boot/test artifact uses wifi-companion-android-wifi-service-window-start-only or the subsys-trigger-capture variant
- artifact contains --allow-android-wifi-service-window and no scan/connect/DHCP/external-ping flags
- live follow-up observes cnss-daemon wlfw_start/wlfw_service_request before treating RC1/L0 as primary

### Guardrails

- no credentialed connect attempt
- no Wi-Fi scan/connect
- no DHCP/routes or external ping
- no direct PMIC/GPIO/GDSC writes
- no blind eSoC notify or BOOT_DONE spoof
- no global PCI rescan or platform bind/unbind

## Safety Scope

This classifier is host-only. It performs no device command, flash, reboot, partition write, daemon start, Wi-Fi HAL start, scan/connect, credential handling, DHCP/routes, external ping, PMIC/GPIO/GDSC write, eSoC notify/BOOT_DONE spoof, pci-msm debugfs write, global PCI rescan, or platform bind/unbind.
