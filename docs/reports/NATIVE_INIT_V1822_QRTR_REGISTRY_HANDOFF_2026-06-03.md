# Native Init V1822 QRTR Registry Handoff

## Summary

- Cycle: `V1822`
- Type: one-run rollbackable QRTR/service-locator registry discriminator
- Decision: `v1822-qrtr-registry-unreadable-with-qmi-context-rollback-pass`
- Result: PASS
- Reason: sysmon/QMI context was visible, but read-only QRTR registry state was not readable
- Evidence: `tmp/wifi/v1822-qrtr-registry-handoff`
- Rollback attempt: `from-native`
- Rollback ok: `True`

## Gate Label

- QRTR registry label: `qrtr-registry-unreadable-with-qmi-context`
- service74 raw label: `service74-raw-absent`
- PM-client return label: `pm-client-return-success`
- lower-state label: `stable-mdm3-offlining`
- safety ok: `True`

## Registry Summary

- registry readable: `False`
- registry wlan/wlan-fw/wlan-pd/service74/qmi text: `False` / `False` / `False` / `False` / `False`
- proc_net_qrtr open/bytes/lines: `0,0,0` / `0,0,0` / `0,0,0`
- debug qrtr nodes open/bytes/lines: `0,0,0` / `0,0,0` / `0,0,0`
- debug qrtr services open/bytes/lines: `0,0,0` / `0,0,0` / `0,0,0`
- no lookup send/service start: `True` / `True`
- `after_holder_start` proc_net_qrtr open/bytes/lines/wlan/wlan_pd/service74: `0` / `0` / `0` / `0` / `0` / `0`
- `after_early_listener` proc_net_qrtr open/bytes/lines/wlan/wlan_pd/service74: `0` / `0` / `0` / `0` / `0` / `0`
- `after_post_listener_window` proc_net_qrtr open/bytes/lines/wlan/wlan_pd/service74: `0` / `0` / `0` / `0` / `0` / `0`

## Publication State

- service-locator/domain/wlan-fw/wlan-pd-domain/qmi-server: `2,2,2` / `0,0,0` / `0,0,0` / `0,0,0` / `0,0,0`
- service180/service74/wlan_pd raw: `1,1,1` / `0,0,0` / `0,0,0`
- precondition pd-mapper/subsys/pil/qmi/wlfw: `0,0,0` / `9,10,10` / `5,5,5` / `7,7,7` / `30,30,30`

## Lower State

- early/late service-notifier state: `uninit` / `uninit`
- mdm3/MHI/WLFW69/wlan0: `OFFLINING` / `False` / `False` / `False`
- PM-client register/connect/return-path rc: `0` / `0` / `0`

## Property Runtime

- Remote root: `/mnt/sdext/a90/private-property-v317/v1821/dev/__properties__`
- Transport: `serial-uudecode-tar-gz`
- Uploaded files/bytes: `22` / `2759988`
- property_info SHA verified: `True`
- vendor_default_prop SHA verified: `True`

## Safety Scope

- The route did not send QRTR lookup packets, did not start extra services, did not open `/dev/subsys_esoc0`, did not fake ONLINE, and did not write PMIC/GPIO/GDSC controls.
- Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, `boot_wlan`, restart-PD request, forced RC1, eSoC notify, BOOT_DONE spoof, PCI rescan, and platform bind/unbind were not used.
- Mutation scope is private property runtime staging on `/mnt/sdext`, one test boot flash, and rollback to `stage3/boot_linux_v724.img`.

## Next

- Stop after this one label; do not proceed to Wi-Fi HAL/scan/connect unless WLFW service 69 and `wlan0` are present.
