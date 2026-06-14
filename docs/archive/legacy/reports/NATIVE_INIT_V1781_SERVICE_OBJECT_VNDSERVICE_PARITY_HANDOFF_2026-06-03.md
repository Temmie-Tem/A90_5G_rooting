# Native Init V1781 Service-object VND-service Parity Handoff

## Summary

- Cycle: `V1781`
- Type: one-run rollbackable WLAN-PD service-object vndservice-parity discriminator
- Decision: `v1781-service-object-nonnull-vote-sent-no-request-rollback-pass`
- Result: PASS
- Reason: PeripheralManager object was non-null and register/vote TX was observed, but wlanmdsp was not requested; stop for functional PM forwarding plan
- Evidence: `tmp/wifi/v1781-service-object-vndservice-parity-handoff`
- Rollback attempt: `from-native`

## Policy / Property Contract

- Policy-load precondition required: `1`
- Policy-load precondition requested: `1`
- Policy-load result: `policy-load-pass`
- Policy-load pass: `1`
- Shutdown-list allow flag: `1`
- Shutdown-list values: ``

Interpretation: V1781 tests only whether the bounded service-object route makes
`vendor.qcom.PeripheralManager` non-null and lets cnss-daemon reach
asInterface/register-vote before any wlanmdsp/WLFW cascade. It does not
autonomously chase the next gate.

## Gate Label

- helper label: `provider-visible-modem-holder-regression`
- provider seen: `1`
- asInterface hits: `1`
- register/vote TX hits: `1`
- success path hits: `0`
- requested `wlanmdsp`: `0`
- WLFW service 69 seen: `0`
- wlan0 present: `0`
- late listener state: `uninit`
- late listener indication seen: `0`

## Route Health

- `pm_proxy_helper` ready: `1`
- `pm-service` ready: `1`
- `pm-service` state: `S`
- `pm-service` zombie: `0`
- `tftp_server` running: `1`
- `cnss-daemon` running: `1`

## Property Runtime

- Remote root: `/mnt/sdext/a90/private-property-v317/v1780/dev/__properties__`
- Uploaded files: `22`
- Uploaded bytes: `2759988`
- property_info SHA verified: `True`
- vendor_default_prop SHA verified: `True`

## Safety Scope

- `/dev/subsys_esoc0`, forced RC1, fake-ONLINE, PMIC/GPIO/GDSC writes, eSoC notify, BOOT_DONE spoof, PCI rescan, platform bind/unbind, restart-PD request, full `pm-proxy`, `boot_wlan`, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping were not used.
- Mutation scope is private property runtime staging on `/mnt/sdext`, one test boot flash, and rollback to `stage3/boot_linux_v724.img`.

## Next

- Stop after this one label; do not autonomously chain into PM forwarding, WLAN-PD cascade, Wi-Fi HAL, scan/connect, DHCP/routes, or external ping.
