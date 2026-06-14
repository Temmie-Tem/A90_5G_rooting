# Native Init V1620 pm-service System-info Surface Classifier

## Summary

- Cycle: `V1620`
- Type: host-only classifier over V1619 rollbackable live evidence
- Decision: `v1620-pm-service-offline-decision-despite-visible-esoc-surface`
- Result: PASS
- Reason: V1619 proves the private namespace exposes the expected eSoC/subsystem/dev-node surface, but `pm-service` still exits cleanly after publishing SDX50M/modem OFFLINE before Binder/PM fd setup

## Inputs

| input | path |
| --- | --- |
| v1619_manifest | tmp/wifi/v1619-pm-service-system-info-surface-handoff/manifest.json |
| v1619_helper | tmp/wifi/v1619-pm-service-system-info-surface-handoff/test-v1393-helper-result.stdout.txt |
| v1619_report | docs/reports/NATIVE_INIT_V1619_PM_SERVICE_SYSTEM_INFO_SURFACE_HANDOFF_2026-06-02.md |

## Checks

| check | value |
| --- | --- |
| handoff_rollback_ok | True |
| system_info_surface_enabled | True |
| snapshots_complete | True |
| snapshots_read_only | True |
| core_nodes_visible | True |
| android_property_area_missing | True |
| surface_reports_modem_online | True |
| surface_reports_esoc0_offlining | True |
| surface_reports_sdx50m_pcie | True |
| pm_service_exits_before_ipc_or_pm_fd | True |
| offline_property_decision_observed | True |
| downstream_absent | True |

## Runtime

| field | value |
| --- | --- |
| v1619_decision | v1619-test-boot-no-downstream-wifi-progress-blocked |
| handoff_pass | True |
| rollback_ok | True |
| strict_wifi_progress | True |
| progress_decision | modem-trigger-no-downstream |
| provider_trigger | False |
| modem_trigger | True |
| rc1_progress | False |
| mhi_progress | False |
| wlfw_progress | False |
| wlan0_present | False |
| helper_result | pm-service-owned-powerup-missing |
| helper_reason | pm-first-late-per-proxy-route-did-not-reach-dev-subsys-esoc0-mdm-subsys-powerup |
| helper_mode | guarded-pm-proxy-contract-pm-first-late-per-proxy-pph-gate-per-mgr-startup-trace-lower-marker |
| per_mgr_system_info_surface | 1 |
| startup_sample_count | 51 |
| last_alive_ms | 20 |
| first_gone_ms | 41 |
| startup_exit_code | 0 |
| startup_signal | 0 |
| max_subsys_modem_fd | 0 |
| max_subsys_esoc0_fd | 0 |
| max_vndbinder_fd | 0 |
| max_socket_fd | 0 |
| pm_proxy_helper_subsys_modem_fd_count | 1 |
| mdm_helper_esoc0_fd_count | 1 |
| pm_full_contract_seen | 0 |
| property_request_count | 3 |
| property_hwservicemanager_ready | True |
| property_sdx50m_offline | True |
| property_modem_offline | True |

## Surface Snapshot

| field | pre | post |
| --- | --- | --- |
| subsys0 | modem ONLINE | modem ONLINE |
| subsys9 | esoc0 OFFLINING | esoc0 OFFLINING |
| esoc0 | SDX50M PCIe 0305_01.01.00 | SDX50M PCIe 0305_01.01.00 |
| /dev/subsys_modem | 1 | 1 |
| /dev/subsys_esoc0 | 1 | 1 |
| /dev/esoc-0 | 1 | 1 |
| binder nodes | vnd=1 binder=1 hw=1 | vnd=1 binder=1 hw=1 |
| /dev/socket/property_service | 1 | 1 |
| /dev/__properties__ | 0 | 0 |

## Property Requests

| index | name | value | allowed | result |
| --- | --- | --- | --- | --- |
| 1 | hwservicemanager.ready | true | 1 | 0x00000000 |
| 2 | vendor.peripheral.SDX50M.state | OFFLINE | 1 | 0x00000000 |
| 3 | vendor.peripheral.modem.state | OFFLINE | 1 | 0x00000000 |

## Interpretation

V1619 eliminates a missing-device-node explanation for the current `pm-service` boundary.  The private namespace contains `/dev/subsys_modem`, `/dev/subsys_esoc0`, `/dev/esoc-0`, binder nodes, the property-service socket, `/sys/bus/msm_subsys`, `/sys/bus/esoc`, and `/sys/class/esoc-dev`.  The visible sysfs state is internally consistent: `subsys0=modem ONLINE`, `subsys9=esoc0 OFFLINING`, and `esoc0=SDX50M PCIe 0305_01.01.00`.

The remaining gap is narrower: `pm-service` still exits naturally with code `0` before opening binder, sockets, `/dev/subsys_modem`, or `/dev/subsys_esoc0`, after publishing `vendor.peripheral.SDX50M.state=OFFLINE` and `vendor.peripheral.modem.state=OFFLINE`.  `/dev/__properties__` is absent in this private namespace; Android normally provides the shared property area in addition to the property-service socket.  The next gate should classify whether the missing Android property area or missing initial property values make `libmdmdetect`/`get_system_info` choose the OFFLINE-only path.

## Next Gate

- Recommended cycle: `V1621`
- Type: source/build-only property-area/properties parity probe
- Focus: expose a read-only/minimal Android property area or capture exact `property_get` dependencies before changing lower eSoC/RC1 behavior
- Keep blocked: Wi-Fi HAL start, scan/connect, credentials, DHCP/routes, external ping, PMIC/GPIO/GDSC writes, blind eSoC notify/`BOOT_DONE`, global PCI rescan, platform bind/unbind, and direct scoped `/dev/subsys_esoc0` actor opens

## Safety Scope

This classifier is host-only. It performs no device command, flash, reboot, partition write, daemon start, Wi-Fi HAL start, scan/connect, credential handling, DHCP/routes, external ping, PMIC/GPIO/GDSC write, blind eSoC notify/`BOOT_DONE` spoof, pci-msm debugfs write, global PCI rescan, or platform bind/unbind.
