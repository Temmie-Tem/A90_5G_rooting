# Native Init V1729 WLAN-PD Service-notifier Late Endpoint Handoff

## Summary

- Cycle: `V1729`
- Type: one-run rollbackable WLAN-PD service-notifier late endpoint gate
- Decision: `v1729-servnotif-late-endpoint-found-rollback-pass`
- Result: PASS
- Reason: late service-notifier endpoint appeared after the service window; rollback verified
- Evidence: `tmp/wifi/v1729-wlan-pd-servnotif-late-endpoint-handoff`
- Rollback attempt: `from-native`

## Gate Label

- late service-notifier result: `endpoint-found`
- late endpoint found: `1`
- late endpoint node: `0`
- late endpoint port: `2`
- early listener result: `no-endpoint`
- early listener status: `not-found`
- nonlog label: `wlfw-worker-thread-started-waiting-for-qmi-service`
- service-window label: `wlfw-start-reached`
- service-locator domain result: `domain-list-response-success`
- service-locator domain name: `msm/modem/wlan_pd`
- service_manager: `1`
- companion order: `servicemanager,hwservicemanager,vndservicemanager,qrtr_ns,pd_mapper,rmt_storage,tftp_server,subsys_modem_holder,cnss_diag,cnss_daemon,service-window-trigger-summary`
- cnss-daemon running: `1`
- tftp running: `1`
- WLFW service 69 seen: `0`
- requested `wlanmdsp`: `0`

## Uprobe Fields

- tracefs available: `1` (`errno=0`)
- wlfw_start hits: `1`
- wlfw_service_request hits: `1`
- wlfw worker create success hits: `1`
- wlfw indication-register QMI hits: `0`
- wlfw capability QMI hits: `0`
- peripheral defaultServiceManager hits: `None`
- peripheral service name hits: `None`
- peripheral service-manager get hits: `None`
- cnss fd counts: `vndbinder=1`, `socket=10`

## Property Runtime

- Remote root: `/mnt/sdext/a90/private-property-v317/v1728/dev/__properties__`
- Uploaded files: `22`
- Uploaded bytes: `2759988`
- property_info SHA verified: `True`
- vendor_default_prop SHA verified: `True`

## Safety Scope

- `/dev/subsys_esoc0`, forced RC1, fake-ONLINE, PMIC/GPIO/GDSC writes, eSoC notify, BOOT_DONE spoof, PCI rescan, and platform bind/unbind were not used.
- PM trio, `vendor.qcom.PeripheralManager` actor, `boot_wlan`, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping were not used.
- Mutation scope was private property runtime staging on `/mnt/sdext`, test boot flash, and rollback to `stage3/boot_linux_v724.img`.

## Interpretation

- `endpoint-found` means the service-notifier endpoint appears late; the next gate should re-arm the listener in that later window.
- `no-endpoint` means the endpoint remains absent even after `wlfw_service_request`; the next gate should classify the service-notifier publication / modem-side WLAN-PD state-up surface, not repeat early timing variants.
