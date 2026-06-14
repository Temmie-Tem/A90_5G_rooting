# Native Init V1819 Publication Text Handoff

## Summary

- Cycle: `V1819`
- Type: one-run rollbackable wlan_pd publication text discriminator
- Decision: `v1819-servloc-init-visible-domain-absent-rollback-pass`
- Result: PASS
- Reason: generic service-locator init text was visible with sysmon/QMI context, but wlan_pd/domain-QMI/service74 publication remained absent
- Evidence: `tmp/wifi/v1819-publication-text-handoff`
- Rollback attempt: `from-native`
- Rollback ok: `True`

## Gate Label

- publication text label: `servloc-init-visible-domain-absent`
- service74 raw label: `service74-raw-absent`
- PM-client return label: `pm-client-return-success`
- lower-state label: `stable-mdm3-offlining`
- safety ok: `True`

## Publication Counters

- service-locator/domain/wlan-fw/wlan-pd-domain/qmi-server: `2,2,2` / `0,0,0` / `0,0,0` / `0,0,0` / `0,0,0`
- positives service-locator/domain/wlan-fw/wlan-pd-domain/qmi-server: `True` / `False` / `False` / `False` / `False`
- publication text positive: `True`
- domain publication text positive: `False`
- service180/service74/wlan_pd raw: `1,1,1` / `0,0,0` / `0,0,0`
- precondition pd-mapper/subsys/pil/qmi/wlfw: `0,0,0` / `9,10,10` / `5,5,5` / `7,7,7` / `30,30,30`
- `after_holder_start` service-locator/domain/wlan-fw/wlan-pd-domain/qmi-server: `2` / `0` / `0` / `0` / `0`
- `after_holder_start` last locator/domain/wlan-fw/wlan-pd-domain/qmi-server: `<6>[    2.833137]  [7:    kworker/7:1:   74] servloc: init_service_locator: Service locator initialized` / `missing` / `missing` / `missing` / `missing`
- `after_early_listener` service-locator/domain/wlan-fw/wlan-pd-domain/qmi-server: `2` / `0` / `0` / `0` / `0`
- `after_early_listener` last locator/domain/wlan-fw/wlan-pd-domain/qmi-server: `<6>[    2.833137]  [7:    kworker/7:1:   74] servloc: init_service_locator: Service locator initialized` / `missing` / `missing` / `missing` / `missing`
- `after_post_listener_window` service-locator/domain/wlan-fw/wlan-pd-domain/qmi-server: `2` / `0` / `0` / `0` / `0`
- `after_post_listener_window` last locator/domain/wlan-fw/wlan-pd-domain/qmi-server: `<6>[    2.833137]  [7:    kworker/7:1:   74] servloc: init_service_locator: Service locator initialized` / `missing` / `missing` / `missing` / `missing`

## Lower State

- early/late service-notifier state: `uninit` / `uninit`
- mdm3/MHI/WLFW69/wlan0: `OFFLINING` / `False` / `False` / `False`
- PM-client register/connect/return-path rc: `0` / `0` / `0`

## Property Runtime

- Remote root: `/mnt/sdext/a90/private-property-v317/v1818/dev/__properties__`
- Transport: `serial-uudecode-tar-gz`
- Uploaded files/bytes: `22` / `2759988`
- property_info SHA verified: `True`
- vendor_default_prop SHA verified: `True`

## Safety Scope

- The route did not open `/dev/subsys_esoc0`, did not fake ONLINE, and did not write PMIC/GPIO/GDSC controls.
- Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, `boot_wlan`, restart-PD request, forced RC1, eSoC notify, BOOT_DONE spoof, PCI rescan, and platform bind/unbind were not used.
- Mutation scope is private property runtime staging on `/mnt/sdext`, one test boot flash, and rollback to `stage3/boot_linux_v724.img`.

## Next

- Stop after this one label; do not proceed to Wi-Fi HAL/scan/connect unless WLFW service 69 and `wlan0` are present.
