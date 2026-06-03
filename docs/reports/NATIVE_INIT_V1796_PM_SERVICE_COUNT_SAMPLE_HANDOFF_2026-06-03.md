# Native Init V1796 PM-service Count Sample Handoff

## Summary

- Cycle: `V1796`
- Type: one-run rollbackable WLAN-PD PM-service count/sample discriminator
- Decision: `v1796-modem-devnode-access-fail-rollback-pass`
- Result: PASS
- Reason: Primary PM-service discovery included modem and add-peripheral still failed before list commit; stop before any devnode repair
- Evidence: `tmp/wifi/v1796-pm-service-count-sample-handoff`
- Rollback attempt: `from-native`
- Rollback ok: `True`

## Gate Label

- helper label: `provider-visible-modem-holder-regression`
- PM server label: `pm-server-no-peripheral`
- PM-service count/sample label: `modem-devnode-access-fail`
- first/second count: `2` / `0`
- first add names/devnodes: `SDX50M,modem` / `/dev/subsys_esoc0,/dev/subsys_modem`
- second add names/devnodes: `` / ``
- add-peripheral observed names: `SDX50M,modem,SDX50M,modem,SDX50M,modem,SDX50M,modem`
- add-peripheral observed devnodes: `/dev/subsys_esoc0,/dev/subsys_modem,/dev/subsys_esoc0,/dev/subsys_modem,/dev/subsys_esoc0,/dev/subsys_modem,/dev/subsys_esoc0,/dev/subsys_modem`
- provider seen: `1`
- asInterface hits: `1`
- register/vote TX hits: `1`
- requested `wlanmdsp`: `0`
- WLFW service 69 seen: `0`
- wlan0 present: `0`

## PM-service Count Uprobes

- first count hits/fetchargs: `1` / `first_count=%x8`
- first count first hit: `pm-service-573   [003] ....     5.393288: pm_service_init_first_count_load: (0x5580b6ebf4) first_count=0x2`
- second count hits/fetchargs: `1` / `second_count=%x8`
- second count first hit: `pm-service-573   [003] ....     5.395550: pm_service_init_second_count_load: (0x5580b6ecd8) second_count=0x0`

## PM-service First-loop Samples

- first add call hits/fail hits: `2` / `2`
- first add fetchargs: `record=%x1 name=+4(%x1):string devnode=+68(%x1):string off_timeout=%x2 ack_timeout=%x3 flags=%x4`
- pm_service_init_first_add_peripheral_call sample 0: `pm-service-573   [003] ....     5.393507: pm_service_init_first_add_peripheral_call: (0x5580b6ecb4) record=0x7ff8883540 name="SDX50M" devnode="/dev/subsys_esoc0" off_timeout=0x1f4 ack_timeout=0xc8 flags=0x0`
- pm_service_init_first_add_peripheral_call sample 1: `pm-service-573   [003] ....     5.394770: pm_service_init_first_add_peripheral_call: (0x5580b6ecb4) record=0x7ff88838c4 name="modem" devnode="/dev/subsys_modem" off_timeout=0x1f4 ack_timeout=0xc8 flags=0x0`
- pm_service_init_first_add_peripheral_call sample 2: `unreliable-entry-fetcharg`
- pm_service_init_first_add_peripheral_call sample 3: `unreliable-entry-fetcharg`

## PM-service Add-peripheral Samples

- entry/init-fail/list-commit hits: `2` / `2` / `0`
- entry names/devnodes: `SDX50M,modem` / `/dev/subsys_esoc0,/dev/subsys_modem`
- known names/devnodes: `SDX50M,modem` / `/dev/subsys_esoc0,/dev/subsys_modem`
- init-fail names/devnodes: `SDX50M,modem` / `/dev/subsys_esoc0,/dev/subsys_modem`
- pm_service_add_peripheral_entry sample 0: `pm-service-573   [003] ....     5.393512: pm_service_add_peripheral_entry: (0x5580b6e5ec) record=0x7ff8883540 name="SDX50M" devnode="/dev/subsys_esoc0"`
- pm_service_add_peripheral_entry sample 1: `pm-service-573   [003] ....     5.394774: pm_service_add_peripheral_entry: (0x5580b6e5ec) record=0x7ff88838c4 name="modem" devnode="/dev/subsys_modem"`
- pm_service_add_peripheral_entry sample 2: `unreliable-entry-fetcharg`
- pm_service_add_peripheral_entry sample 3: `unreliable-entry-fetcharg`
- pm_service_add_peripheral_init_fail sample 0: `pm-service-573   [003] ....     5.394199: pm_service_add_peripheral_init_fail: (0x5580b6e68c) name="SDX50M" devnode="/dev/subsys_esoc0"`
- pm_service_add_peripheral_init_fail sample 1: `pm-service-573   [003] ....     5.395174: pm_service_add_peripheral_init_fail: (0x5580b6e68c) name="modem" devnode="/dev/subsys_modem"`
- pm_service_add_peripheral_init_fail sample 2: `unreliable-entry-fetcharg`
- pm_service_add_peripheral_init_fail sample 3: `unreliable-entry-fetcharg`

## PM Register Request Uprobes

- register entry hits: `1`
- register entry peripheral/client: `unreliable-entry-fetcharg` / `?`
- register strcmp candidate/requested: `` / ``
- no-peripheral requested: `modem`
- loop/match/success/no-peripheral hits: `0` / `0` / `0` / `1`

## Route Health

- policy-load result: `policy-load-pass`
- `pm_proxy_helper` ready: `1`
- `pm-service` ready: `1`
- `pm-service` state/zombie: `S` / `0`
- `tftp_server` running: `1`
- `cnss-daemon` running: `1`

## Property Runtime

- Remote root: `/mnt/sdext/a90/private-property-v317/v1795/dev/__properties__`
- Transport: `serial-uudecode-tar-gz`
- tar.gz bytes/SHA256: `10607` / `0b6d7713f3afce59789eff4155cf81533155582112ed1b52983a7a306aa1ee7d`
- Uploaded files: `22`
- Uploaded bytes: `2759988`
- property_info SHA verified: `True`
- vendor_default_prop SHA verified: `True`

## Safety Scope

- `/dev/subsys_esoc0`, forced RC1, fake-ONLINE, PMIC/GPIO/GDSC writes, eSoC notify, BOOT_DONE spoof, PCI rescan, platform bind/unbind, restart-PD request, full `pm-proxy`, `boot_wlan`, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping were not used.
- Mutation scope is private property runtime staging on `/mnt/sdext`, one test boot flash, and rollback to `stage3/boot_linux_v724.img`.

## Next

- Stop after this one label; do not repair PM-service devnodes, chase WLAN-PD cascade, start Wi-Fi HAL, scan/connect, DHCP/routes, or external ping in this run.
