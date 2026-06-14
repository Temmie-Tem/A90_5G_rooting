# Native Init V1736 WLAN-PD Timestamped Observer Handoff

## Summary

- Cycle: `V1736`
- Type: one-run rollbackable read-only WLAN-PD timestamped observer gate
- Decision: `v1736-test-boot-flash-or-verify-failed`
- Result: BLOCKED
- Reason: test boot flash/verify failed; live_error=tcpctl did not become ready: timed out
- Evidence: `tmp/wifi/v1753-native-wlan-pd-firmware-request-sm-route`
- Rollback attempt: `from-native`

## Gate Label

- service-window label: ``
- timestamped observer seen: `False`
- observer monotonic ms: `None`
- nonlog label: ``
- old firmware-serve label: `None`
- service_manager: `None`
- cnss-daemon running: `None`
- tftp running: `None`
- wlfw start seen: `0`
- WLFW service 69 seen: `0`
- requested `wlanmdsp`: `0`
- late listener result: `None`
- late listener state: ``
- late listener indication seen: ``
- late listener hold ms: `None`

## Uprobe Fields

- wlfw_start hits: `0`
- wlfw_service_request hits: `0`
- wlfw worker create success hits: `0`
- wlfw indication-register QMI hits: `None`
- wlfw capability QMI hits: `None`

## Safety Scope

- `/dev/subsys_esoc0`, forced RC1, fake-ONLINE, PMIC/GPIO/GDSC writes, eSoC notify, BOOT_DONE spoof, PCI rescan, and platform bind/unbind were not used.
- PM trio, `vendor.qcom.PeripheralManager` actor, `boot_wlan`, restart-PD request, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping were not used.
- Mutation scope was private property runtime staging on `/mnt/sdext`, test boot flash, and rollback to `stage3/boot_linux_v724.img`.

## Property Runtime

- Remote root: `None`
- Uploaded files: `None`
- Uploaded bytes: `None`
- property_info SHA verified: `None`
- vendor_default_prop SHA verified: `None`

## Next

- Stop after this label. Do not spin timing/window variants from this gate.
- If label is `wlfw-start-reached-downstream-block`, the next work is modem-side WLAN-PD image/start trigger analysis, not PM actors or QCACLD registration.
- If label is `wlan-pd-progress-before-connect`, plan the next bounded WLFW/BDF/wlan0 gate before any credentialed connection attempt.
