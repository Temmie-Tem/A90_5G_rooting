# V1590 PM-service Lifetime Route Classifier

- generated: `2026-06-01T22:59:14.994787+00:00`
- decision: `v1590-route-current-service-window-loses-pm-service-owned-powerup`
- pass: `True`
- reason: V1589 lower-marker route starts the scoped trigger but loses the PM-service-owned route; V1238/V1303 prove late-per_proxy can reach the correct PM-service /dev/subsys_esoc0 powerup boundary
- next_step: V1591 source/build-only: derive a firmware-mount-preserving late-per_proxy-only service-window test boot with lower-marker sampling, no direct scoped trigger, and explicit PM-service lifetime/exit markers

## Inputs

| input | path |
| --- | --- |
| v1589_manifest | tmp/wifi/v1589-service-window-lower-marker-handoff/manifest.json |
| v1589_helper | tmp/wifi/v1589-service-window-lower-marker-handoff/test-v1393-helper-result.stdout.txt |
| v1589_dmesg | tmp/wifi/v1589-service-window-lower-marker-handoff/test-v1393-dmesg.stdout.txt |
| v1238_manifest | tmp/wifi/v1238-late-per-proxy-only-live/manifest.json |
| v1238_summary | tmp/wifi/v1238-late-per-proxy-only-live/summary.md |
| v1303_manifest | tmp/wifi/v1303-compact-powerup-marker-live/manifest.json |
| v1303_summary | tmp/wifi/v1303-compact-powerup-marker-live/summary.md |

## Checks

| check | status | detail |
| --- | --- | --- |
| v1589-current-lower-marker-valid | pass | V1589 handoff passed and rollback verified |
| v1589-pm-service-route-missing | pass | per_mgr exits 0, pm_proxy exits 1, no PM-service-owned /dev/subsys_esoc0/powerup marker |
| older-positive-pm-route-exists | pass | V1238/V1303 show late-per_proxy path reaching /dev/subsys_esoc0/mdm_subsys_powerup |
| not-ready-for-connect | pass | wlan0/connect remain absent; credentials/connect/DHCP/ping are still downstream |

## Current V1589 Route

| field | value |
| --- | --- |
| handoff_pass | True |
| rollback_ok | True |
| final_decision | firmware-progress-no-wlan0 |
| provider_trigger | True |
| modem_trigger | True |
| helper_result_contract_seen | True |
| helper_result_subsys_trigger_started | True |
| helper_result_mdm_helper_esoc0_fd_count | 1 |
| pm_proxy_contract | 1 |
| pm_proxy_helper_subsys_modem_fd_count | 0 |
| per_mgr_subsys_modem_fd_count | -1 |
| pm_full_contract_seen | 0 |
| per_mgr_alive_seen | 0 |
| per_mgr_child_observable | 0 |
| per_mgr_child_exited | 1 |
| per_mgr_child_exit_code | 0 |
| pm_proxy_child_exited | 1 |
| pm_proxy_child_exit_code | 1 |
| global_subsys_esoc0_fd_max | 0 |
| pm_service_powerup_seen | 0 |
| max_powerup_thread_count | 0 |
| trigger_child_alive_seen | 1 |
| trigger_child_stack_powerup_lines | 3 |
| dmesg_pm_proxy_helper_modem_get | 1 |
| dmesg_scoped_esoc0_get | 1 |
| dmesg_pm_service_esoc0_get | 0 |
| wlan0_present | False |
| connect_ready | False |

## Positive PM-service Route References

| field | value |
| --- | --- |
| v1238_pass | True |
| v1238_decision | v1238-late-per-proxy-reached-pm-service-esoc0-reboot-required |
| v1238_late_per_proxy_started | 1 |
| v1238_pm_service_actor_esoc0_attempt | True |
| v1238_post_pm_fd_esoc0_count | 1 |
| v1238_wlan0_seen | False |
| v1303_pass | True |
| v1303_decision | v1303-powerup-marker-pm-esoc0-trigger-sampled-mdm2ap-silent-reboot-required |
| v1303_powerup_marker_emitted | True |
| v1303_max_powerup_thread_count | 1 |
| v1303_powerup_subsys_esoc0_inferred_seen | True |
| v1303_powerup_first_path_values | /dev/subsys_esoc0 |
| v1303_powerup_first_wchans | mdm_subsys_powerup |
| v1303_powerup_first_syscall_names | openat |
| v1303_wlan0_seen | False |

## Interpretation

V1589 proves the compact lower-marker sampler is useful, but the current
service-window ordering does not keep `pm-service` alive long enough to own
`/dev/subsys_esoc0`.  The live powerup stack in V1589 belongs to the scoped
helper trigger child, not to Android's PM-service Binder route.  V1238 and
V1303 remain the better PM-service-owned route references because late
`pm-proxy` caused PM-service to reach `/dev/subsys_esoc0` and
`mdm_subsys_powerup`.

## Safety

Host-only classifier. No device command, Wi-Fi HAL, scan/connect,
credentials, DHCP/routes, external ping, flash, boot image write, or
partition write occurred.
