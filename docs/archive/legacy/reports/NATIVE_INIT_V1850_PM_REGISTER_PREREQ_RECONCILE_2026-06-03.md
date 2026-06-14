# Native Init V1850 PM Register Prerequisite Reconcile

## Summary

- Cycle: `V1850`
- Type: host-only reconciliation of the historical CNSS PM-register prerequisite against current V184x evidence
- Decision: `v1850-pm-register-prereq-closed-for-modem-selection-remains-host-pass`
- Label: `pm-register-prereq-closed-for-modem-selection-remains`
- Result: PASS
- Reason: The old CNSS PM-register/connect prerequisite is closed on the current modem-selected route, so the remaining branch is PM peripheral selection versus known lower SDX50M response gap, not another generic register helper/mutex observer
- Evidence: `tmp/wifi/v1850-pm-register-prereq-reconcile`

## Historical Prerequisite

- V1349 decision: `v1349-cnss-pm-register-blocker-is-next-prereq` / pass `True`
- V1349 reason: existing evidence converges on CNSS PM register/connect/vote as the missing prerequisite: native CNSS reaches netlink but not wlfw_start, Android wlfw_start belongs to the service window, CNSS PM register blocks in pm-service before connect, and the PM callback body is ack-only
- V1349 next step then: `V1350 should define a compact PM register helper/mutex observer before any lower eSoC mutation`

## Current Closure

- V1841 callback/ack: `v1841-callback-ack-present-no-powerup-rollback-pass` / `callback-ack-present-no-powerup` hits `28`
- V1847 register/connect/return rc: `0` / `0` / `0`
- V1847 register call/retcheck hits: `1` / `1`
- V1847 retcheck line: `cnss-daemon-608   [003] ....     6.817518: pm_init_pm_client_register_retcheck: (0x55578a2628) rc=0x0`
- V1847 post-ack/open: `post-ack-open-branch-reached` / `/dev/subsys_modem` fd `0x7`
- V1847 lower state: `lower-continuation-static-gap` / `stable-mdm3-offlining` service69 `False` wlan0 `False`

## Remaining Branch

- V1848 selection: `v1848-cnss-pm-register-selects-modem-not-sdx50m-host-pass` / `cnss-pm-register-selects-modem-record`
- V1849 private route: `v1849-private-sdx50m-route-known-lower-gap-host-pass` / `private-sdx50m-route-known-lower-gap`

## Interpretation

- The generic CNSS PM-register/connect blocker from V1349 is stale for the current route: V1847 shows register/connect/return rc `0` and post-ack PM-service action.
- That closure applies to the selected `modem` record; V1848 proves current CNSS still requests `modem`, so PM-service opens `/dev/subsys_modem`.
- V1849 proves the private `SDX50M` selection route is already known to reach eSoC powerup but then falls into the lower MDM2AP/PCIe/WLFW response gap.
- The next useful unit is not another broad PM-register observer and not a blind lower mutation; it is a source/build-only bridge between current PM closure and any future SDX50M-selection route gate.

## Safety Scope

Host-only. This classifier did not issue live device commands, flash, reboot, stage properties, start actors, open `/dev/subsys_esoc0`, start `boot_wlan`, issue restart-PD request, force RC1, fake ONLINE state, write PMIC/GPIO/GDSC controls, perform eSoC notify, BOOT_DONE spoof, PCI rescan, platform bind/unbind, start Wi-Fi HAL, scan/connect, use credentials, configure DHCP/routes, or external ping.

## Next

- Do not proceed to Wi-Fi HAL/scan/connect unless WLFW service 69 and `wlan0` are present.
- Next source/build-only unit: define a no-live SDX50M-selection bridge plan that reuses current PM closure instrumentation and explicitly gates any future live private-route run on lower-response guardrails.
