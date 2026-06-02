# Native Init V1784 PM Server Forwarding Observer Handoff

## Summary

- Cycle: `V1784`
- Type: one-run rollbackable WLAN-PD PM server forwarding observer discriminator
- Decision: `v1784-service-object-nonnull-vote-sent-no-request-rollback-pass`
- Result: PASS
- Reason: PeripheralManager object was non-null and register/vote TX was observed, but `wlanmdsp` was not requested; PM server label `pm-server-no-peripheral` fixes the next boundary.
- Evidence: `tmp/wifi/v1784-pm-server-forwarding-observer-handoff`
- Rollback attempt: `from-native`

## Classification Correction

- Original runner label: `v1784-service-object-still-null-rollback-pass`
- Corrected label: `v1784-service-object-nonnull-vote-sent-no-request-rollback-pass`
- Reason: `null_branch_hits=2` is an early branch artifact. The fixed discriminator keys are `provider_seen=1`, `asInterface=1`, and `register/vote TX=1`, so this is not a service-object-null result.
- PM server boundary: `pm-server-no-peripheral` with register entry hit `1` and no-peripheral return hit `1`.

## Gate Label

- helper label: `provider-visible-modem-holder-regression`
- provider seen: `1`
- asInterface hits: `1`
- register/vote TX hits: `1`
- client success path hits: `0`
- null branch hits: `2`
- requested `wlanmdsp`: `0`
- WLFW service 69 seen: `0`
- wlan0 present: `0`
- late listener state: `uninit`
- late listener indication seen: `0`

## PM Server Uprobes

- label: `pm-server-no-peripheral`
- attempted/registered/enabled: `1` / `1` / `1`
- target: `/tmp/a90-v231-548/root/vendor/bin/pm-service` (index `0`)
- total hits: `2`
- first hit: `Binder:573_2-576   [002] ....     6.695177: pm_server_register_entry: (0x55745b0048)`
- register entry hits: `1`
- loop/match hits: loop=`0`, strcmp=`0`, match=`0`
- permission/add-client/success hits: `0` / `0` / `0`
- no-peripheral hits: `1`

## Route Health

- policy-load result: `policy-load-pass`
- `pm_proxy_helper` ready: `1`
- `pm-service` ready: `1`
- `pm-service` state/zombie: `S` / `0`
- `tftp_server` running: `1`
- `cnss-daemon` running: `1`

## Property Runtime

- Remote root: `/mnt/sdext/a90/private-property-v317/v1783/dev/__properties__`
- Uploaded files: `22`
- Uploaded bytes: `2759988`
- property_info SHA verified: `True`
- vendor_default_prop SHA verified: `True`

## Safety Scope

- `/dev/subsys_esoc0`, forced RC1, fake-ONLINE, PMIC/GPIO/GDSC writes, eSoC notify, BOOT_DONE spoof, PCI rescan, platform bind/unbind, restart-PD request, full `pm-proxy`, `boot_wlan`, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping were not used.
- Mutation scope is private property runtime staging on `/mnt/sdext`, one test boot flash, and rollback to `stage3/boot_linux_v724.img`.

## Next

- Stop after this one label; do not autonomously chain into functional PM forwarding repair, WLAN-PD cascade, Wi-Fi HAL, scan/connect, DHCP/routes, or external ping.
