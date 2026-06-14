# Native Init V1742 WLAN-PD Service-manager Minimizer

## Summary

- Cycle: `V1742`
- Type: host-only route minimization classifier
- Decision: `v1742-minimum-observed-service-manager-bootstrap-route-pass`
- Result: `PASS`
- Label: `minimum-observed-service-manager-bootstrap-route`
- Evidence: `tmp/wifi/v1742-wlan-pd-service-manager-minimizer`

## Route Matrix

- `V1740` `pure_v1740`: service_manager `0`, children `6`, tracefs `0`, wlfw hits `0/0/0`, firmware `firmware-not-requested`, svc69/request `0/0`
- `V1727` `bootstrap_v1727`: service_manager `1`, children `11`, tracefs `1`, wlfw hits `1/1/1`, firmware `firmware-not-requested`, svc69/request `0/0`
- `V1729` `late_endpoint_v1729`: service_manager `1`, children `11`, tracefs `1`, wlfw hits `1/1/1`, firmware `firmware-not-requested`, svc69/request `0/0`
- `V1731` `late_listener_v1731`: service_manager `1`, children `11`, tracefs `1`, wlfw hits `1/1/1`, firmware `firmware-not-requested`, svc69/request `0/0`
- `V1736` `timestamped_v1736`: service_manager `1`, children `11`, tracefs `1`, wlfw hits `1/1/1`, firmware `firmware-not-requested`, svc69/request `0/0`

## Classification

V1727 is the earliest verified route in the compared chain that reaches `wlfw_start`, `wlfw_service_request`, and WLFW worker creation. V1729, V1731, and V1736 preserve that same CNSS entry state while adding late endpoint/listener/timestamped observation. Those later additions are therefore observation refinements, not required triggers for the observed `wlfw_start` entry.

V1742 intentionally classifies only the minimum observed route, not the atomically minimal subcomponent. The V1727 surface still starts the service-manager trio as a bounded bootstrap bundle, and the existing evidence does not isolate `servicemanager` vs `hwservicemanager` vs `vndservicemanager` vs tracefs/private-runtime side effects.

All service-manager routes remain downstream-blocked: no WLFW indication/capability QMI, no WLAN-PD UP indication, no WLFW service 69, no `wlanmdsp` request, and no `wlan0`.

## Next Gate

- V1743 should be source/build-only first: add a pure-route non-log parity gate that keeps service-manager disabled but makes the same tracefs/uprobe observer available.
- This closes the V1740 measurement gap without adding PM actors, `boot_wlan`, restart-PD, eSoC/RC1, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping.
- If pure-route non-log parity still shows no `wlfw_start`, the next live candidate can test the V1727 bootstrap route as the minimal known CNSS-entry route before returning to modem-side WLAN-PD publication.

## Checks

- `all_handoff_inputs_passed_and_rolled_back`: `True`
- `pure_route_has_no_service_manager_surface`: `True`
- `bootstrap_route_is_first_observed_success`: `True`
- `bootstrap_keeps_hard_stops`: `True`
- `bootstrap_still_downstream_blocked`: `True`
- `extension_routes_preserve_same_cnss_entry`: `True`
- `extension_routes_preserve_same_downstream_block`: `True`
- `extension_routes_keep_hard_stops`: `True`
- `late_endpoint_is_observational`: `True`
- `late_listener_is_observational`: `True`

## Safety Scope

This script performed host-only analysis only. It did not contact the device, flash, reboot, send QMI payloads, start services, start `boot_wlan`, use `/dev/subsys_esoc0`, force RC1, fake ONLINE state, start Wi-Fi HAL, scan/connect, use credentials, configure DHCP/routes, perform external ping, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE`, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
