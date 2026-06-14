# Native Init V1851 SDX50M Selection Bridge Plan

## Summary

- Cycle: `V1851`
- Type: source/build-only bridge-plan classifier; no live device action
- Decision: `v1851-sdx50m-selection-bridge-plan-ready-no-live-host-pass`
- Label: `sdx50m-selection-bridge-plan-ready-no-live`
- Result: PASS
- Reason: No-live bridge inputs are coherent: private SDX50M selection can be reused only under current PM-closure instrumentation and lower-response guardrails, with Wi-Fi connect still blocked until WLFW service 69 and wlan0 appear
- Evidence: `tmp/wifi/v1851-sdx50m-selection-bridge-plan`

## Input Checks

- patch artifact: `v1220-private-cnss-daemon-sdx50m-patch-ready` sha_ok `True` output `tmp/wifi/v1220-cnss-daemon-sdx50m-patch/artifacts/cnss-daemon.sdx50m`
- private route: `v1221-sdx50m-per-mgr-esoc0` registrations `['modem', 'SDX50M']` esoc `True` powerup `True`
- current PM closure: register/connect/return `0` / `0` / `0` open `/dev/subsys_modem`
- current selection: `v1848-cnss-pm-register-selects-modem-not-sdx50m-host-pass` / `cnss-pm-register-selects-modem-record`
- private route reuse: `v1849-private-sdx50m-route-known-lower-gap-host-pass` / `private-sdx50m-route-known-lower-gap`
- PM prereq reconcile: `v1850-pm-register-prereq-closed-for-modem-selection-remains-host-pass` / `pm-register-prereq-closed-for-modem-selection-remains`
- lower window/runtime: `v1345-current-route-mdm2ap-full-window-no-transition` / `v1349-cnss-pm-register-blocker-is-next-prereq`

## Bridge Contract

- live action executed: `False`
- Wi-Fi/credential/network allowed: `False` / `False` / `False` / `False` / `False`
- direct lower mutation allowed: subsys_esoc0 `False`, PMIC/GPIO/GDSC `False`, eSoC ioctl/notify `False`, forced RC1/rescan `False`
- future live inputs: `['private SDX50M cnss-daemon artifact from V1220', 'current PM register/connect/open-context labels from V1847', 'CNSS PM selection compare labels from V1848', 'lower-response stop conditions from V1345/V1849']`
- future minimum success: `['patched CNSS request selects SDX50M rather than modem', 'PM-service post-ack open context selects /dev/subsys_esoc0 by PM-service path, not direct host open', 'rollback to v724 verifies filtered version and selftest fail=0', 'no Wi-Fi HAL/scan/connect unless WLFW service 69 and wlan0 appear first']`
- future stop conditions: `['PM register/connect does not return rc=0', 'PM-service still selects modem', 'mdm3 remains OFFLINING with no GPIO142/PCIe/MHI/WLFW/wlan0 response', 'modem crash/down markers rise before WLFW publication', 'any guardrail action outside the bridge contract is needed']`

## Interpretation

- V1851 does not run the private SDX50M route. It only validates that the next possible live unit has coherent inputs and explicit stop conditions.
- The bridge preserves V1847 PM closure instrumentation and V1848 selection comparison so a future run can distinguish `modem` selection from `SDX50M` selection.
- V1849/V1345 keep the known lower-response gap authoritative; a future SDX50M run is useful only if it adds bounded evidence beyond the already-known eSoC-powerup/no-response result.
- Wi-Fi connect and ping remain blocked until lower publication proves WLFW service 69 and `wlan0` exist.

## Safety Scope

Host-only. This classifier did not issue live device commands, flash, reboot, stage properties, start actors, open `/dev/subsys_esoc0`, start `boot_wlan`, issue restart-PD request, force RC1, fake ONLINE state, write PMIC/GPIO/GDSC controls, perform eSoC notify, BOOT_DONE spoof, PCI rescan, platform bind/unbind, start Wi-Fi HAL, scan/connect, use credentials, configure DHCP/routes, or external ping.

## Next

- Do not proceed to Wi-Fi HAL/scan/connect unless WLFW service 69 and `wlan0` are present.
- Next implementation candidate is a source/build-only V1852 gate scaffold that combines V1847 PM open-context labels with SDX50M-selection compare labels, but still defaults to dry-run/no-live.
