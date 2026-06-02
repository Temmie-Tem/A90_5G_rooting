# Native Init V1725 WLAN-PD cnss-daemon Output Visibility Handoff

## Summary

- Cycle: `V1725`
- Type: one-run rollbackable WLAN-PD cnss-daemon output-visibility gate
- Decision: `v1725-cnss-output-still-invisible-rollback-pass`
- Result: PASS
- Reason: one cnss output visibility gate run produced a fixed label and rollback verified
- Evidence: `tmp/wifi/v1725-cnss-output-visible-route-handoff`
- Rollback attempt: `from-native`

## Gate Label

- Label: `cnss-output-still-invisible`
- legacy firmware-serve label: `firmware-not-requested`
- wlfw_start seen: `0`
- first failure slug: `none`
- syslog available: `1`
- syslog errno: `0`
- syslog filtered count: `0`
- cnss-daemon running: `1`
- tftp running: `1`
- companion order: `qrtr_ns,pd_mapper,rmt_storage,tftp_server,subsys_modem_holder,cnss_diag,cnss_daemon,cnss-output-visibility-summary`

## Property Runtime

- Remote root: `/mnt/sdext/a90/private-property-v317/v1724/dev/__properties__`
- Uploaded files: `22`
- Uploaded bytes: `2759988`
- property_info SHA verified: `True`
- vendor_default_prop SHA verified: `True`

## Property Lookup

- `persist.vendor.cnss-daemon.kmsg_logging`: expected `1`, value `1`, match `1`
- `persist.vendor.cnss-daemon.debug_level`: expected `4`, value `4`, match `1`
- all property lookups matched: `1`

## Supplemental Fields

- non-log helper contract: `wlan_pd_cnss_nonlog_control_flow.begin=1`
- cnss-daemon maps text seen: `1`
- cnss-daemon running: `1`
- tracefs available: `0` (`errno=2`)
- cnss-daemon fd counts: `vndbinder=1`, `kmsg=0`
- non-log fallback label: `cnss-target-unavailable`

## Interpretation

- The corrected kmsg property contract is consumed in the same namespace, but no `wlfw_start: Starting` line or pre-WLFW `Failed to ...` string reaches kmsg/stdout/stderr.
- This run fixes the old helper expectation mismatch (`kmsg_logging=4` vs actual `1`) and still returns `cnss-output-still-invisible`.
- This is an output visibility result only. It does not justify adding PM/service-window actors, `boot_wlan`, eSoC/RC1, or Wi-Fi HAL work inside this gate.

## Safety Scope

- `/dev/subsys_esoc0`, forced RC1, fake-ONLINE, PMIC/GPIO/GDSC writes, eSoC notify, BOOT_DONE spoof, PCI rescan, and platform bind/unbind were not used.
- service-manager, PM trio, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping were not used.
- Mutation scope was private property runtime staging on `/mnt/sdext`, test boot flash, and rollback to `stage3/boot_linux_v724.img`.

## Next

- Stop after this one label.
- If label is `wlfw-start-reached-downstream-block`, classify the blocker as downstream of cnss-daemon entry.
- If label starts with `cnss-init-step-failed-`, classify that named init step before any WLAN-PD/firmware expansion.
- If label is `cnss-output-still-invisible`, inspect property shim/kmsg visibility before adding actors.
