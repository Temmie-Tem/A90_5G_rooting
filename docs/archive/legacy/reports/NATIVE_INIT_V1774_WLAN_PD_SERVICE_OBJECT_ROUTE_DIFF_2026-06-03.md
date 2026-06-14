# Native Init V1774 WLAN-PD Service-object Route Diff

## Summary

- Cycle: `V1774`
- Type: host-only route/source diff classifier
- Decision: `v1774-service-object-route-lacks-pm-property-contract-host-pass`
- Label: `service-object-route-lacks-pm-property-contract`
- Result: PASS
- Reason: V1772 service-object route omitted the PM property/shutdown-critical-list contract that the V1092 provider-positive route used before provider registration
- Evidence: `tmp/wifi/v1774-wlan-pd-service-object-route-diff`

## Diff Result

- The failed V1772 service-object route did not enable the PM property contract.
- The provider-positive V1092 route did enable `vendor.peripheral.shutdown_critical_list` handling.
- Source inspection shows `wlan_pd_service_object_visible_trigger` is not included in either the `peripheral_manager_property_contract` expression or the property-shim `allow_peripheral_shutdown_list` expression.
- Therefore the next source/build repair target is narrow: include the V1772 service-object route in the same PM property/shutdown-critical-list contract surface, without adding `per_proxy`, eSoC, RC1, Wi-Fi HAL, scan/connect, DHCP/routes, or external ping.

## V1772 Failed Route

- Property contract flag: `False`
- Init contract flag: `False`
- Property shim allows shutdown list: `False`
- Allowlist contains `vendor.peripheral.shutdown_critical_list`: `False`
- Shutdown-list values observed: `[]`
- Provider seen: `False`
- `pm_proxy_helper` / `pm-service` clean exits: `True` / `True`
- Order: `servicemanager,hwservicemanager,vndservicemanager,qrtr_ns,pd_mapper,rmt_storage,tftp_server,pm_proxy_helper,per_mgr,vndservice_query,subsys_modem_holder,cnss_diag,cnss_daemon,service-object-visible-summary`
- Allowlist: `hwservicemanager.ready:true,ctl.stop:vendor.rmt_storage,vendor.peripheral.SDX50M.state:OFFLINE,vendor.peripheral.modem.state:OFFLINE`

## V1092 Positive Control

- Provider-positive control: `True`
- Property shim started: `True`
- Property shim allows shutdown list: `True`
- Allowlist contains `vendor.peripheral.shutdown_critical_list`: `True`
- Shutdown-list values observed: `['SDX50M', 'SDX50M modem']`
- Provider seen after `per_mgr`: `True`
- After-`per_mgr` query before `per_proxy`: `True`
- Order: `servicemanager,hwservicemanager,vndservicemanager,vndservicemanager_ready,pm_proxy_helper,per_mgr,vndservice_query,per_proxy,vndservice_query`
- Allowlist: `hwservicemanager.ready:true,ctl.stop:vendor.rmt_storage,vendor.peripheral.SDX50M.state:OFFLINE,vendor.peripheral.modem.state:OFFLINE,vendor.peripheral.shutdown_critical_list:SDX50M_|SDX50M_modem_`

## Source Check

- Service-object mode exists: `True`
- Property-contract expression present: `True`
- Shutdown-list allow expression present: `True`
- Service-object mode included in property-contract expression: `False`
- Service-object mode included in shutdown-list allow expression: `False`

## Next

- Source/build-only: patch `a90_android_execns_probe.c` so `wlan_pd_service_object_visible_trigger` enables the PM property/shutdown-critical-list contract used by V1092.
- Keep the live route bounded: no full `per_proxy`, no `/dev/subsys_esoc0`, no forced RC1, no fake-ONLINE, no Wi-Fi HAL, no scan/connect, no credentials, no DHCP/routes, and no external ping.
- After source/build validation, a separate rollbackable live gate can test only whether the provider becomes visible and whether CNSS reaches `asInterface` / register-TX / `wlanmdsp` request.

## Safety

- This unit is host-only and retained-evidence/source-only.
- No device command, flash, reboot, actor start, Wi-Fi HAL, scan/connect, credential use, DHCP/routes, external ping, firmware write, partition write, PMIC/GPIO/GDSC write, eSoC action, PCI action, platform bind/unbind, or tracefs write was performed.
