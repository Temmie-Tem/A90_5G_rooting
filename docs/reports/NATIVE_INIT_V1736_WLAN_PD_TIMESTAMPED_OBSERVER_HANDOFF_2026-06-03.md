# Native Init V1736 WLAN-PD Timestamped Observer Handoff

## Summary

- Cycle: `V1736`
- Type: one-run rollbackable read-only WLAN-PD timestamped observer gate
- Decision: `v1736-wlfw-start-reached-downstream-block-rollback-pass`
- Result: PASS
- Reason: cnss-daemon reached WLFW start/request path, but WLAN-PD stayed uninit with no WLFW service 69 or wlanmdsp request; rollback verified
- Evidence: `tmp/wifi/v1736-wlan-pd-timestamped-observer-handoff`
- Rollback attempt: `from-native`

## Gate Label

- service-window label: `wlfw-start-reached`
- timestamped observer seen: `True`
- observer monotonic ms: `50225`
- nonlog label: `wlfw-worker-thread-started-waiting-for-qmi-service`
- old firmware-serve label: `firmware-not-requested`
- service_manager: `1`
- cnss-daemon running: `1`
- tftp running: `1`
- wlfw start seen: `1`
- WLFW service 69 seen: `0`
- requested `wlanmdsp`: `0`
- late listener result: `listener-response-success`
- late listener state: `uninit`
- late listener indication seen: `0`
- late listener hold ms: `15015`

## Uprobe Fields

- wlfw_start hits: `1`
- wlfw_service_request hits: `1`
- wlfw worker create success hits: `1`
- wlfw indication-register QMI hits: `0`
- wlfw capability QMI hits: `0`

## Safety Scope

- `/dev/subsys_esoc0`, forced RC1, fake-ONLINE, PMIC/GPIO/GDSC writes, eSoC notify, BOOT_DONE spoof, PCI rescan, and platform bind/unbind were not used.
- PM trio, `vendor.qcom.PeripheralManager` actor, `boot_wlan`, restart-PD request, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping were not used.
- Mutation scope was private property runtime staging on `/mnt/sdext`, test boot flash, and rollback to `stage3/boot_linux_v724.img`.

## Property Runtime

- Remote root: `/mnt/sdext/a90/private-property-v317/v1735/dev/__properties__`
- Uploaded files: `22`
- Uploaded bytes: `2759988`
- property_info SHA verified: `True`
- vendor_default_prop SHA verified: `True`

## Next

- Stop after this label. Do not spin timing/window variants from this gate.
- If label is `wlfw-start-reached-downstream-block`, the next work is modem-side WLAN-PD image/start trigger analysis, not PM actors or QCACLD registration.
- If label is `wlan-pd-progress-before-connect`, plan the next bounded WLFW/BDF/wlan0 gate before any credentialed connection attempt.
