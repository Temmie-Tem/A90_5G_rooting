# Native Init V1790 PM-service Devnode String Observer Source Build

## Summary

- Cycle: `V1790`
- Type: source/build-only rollbackable WLAN-PD PM-service devnode string observer test boot artifact
- Decision: `v1790-pm-service-devnode-string-observer-source-build-pass`
- Result: PASS
- Reason: helper v337 keeps the V1787 route and adds tracefs fetchargs to the PM-service add-peripheral entry, known-name, and init-fail uprobes so the next live gate can capture discovered candidate names and `/dev/subsys_*` devnode strings before any repair.
- Manifest: `tmp/wifi/v1790-pm-service-devnode-string-observer-test-boot/manifest.json`
- Boot image: `tmp/wifi/v1790-pm-service-devnode-string-observer-test-boot/boot_linux_v1790_pm_service_devnode_string_observer.img`
- Boot SHA256: `01eab62010d3075b9d13b70d4dadb52d52b1c13ae226d20ae7a2440b63f4958c`
- Init: `A90 Linux init 0.9.146 (v1790-pm-service-devnode-string-observer)`
- Helper marker: `a90_android_execns_probe v337`
- Helper SHA256: `b7b44dc64c1e48964ac59059142f84e3e771b9225d825ef19be12bddf2128c7e`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-service-object-visible-trigger-start-only`
- Property root: `/mnt/sdext/a90/private-property-v317/v1790/dev/__properties__`
- Base route remains the bounded V1787 service-object route: service managers, firmware-serve stack, `pm_proxy_helper`, `pm-service`, `/dev/subsys_modem` holder, `cnss_diag`, and stock `cnss-daemon`.
- Added observer only: PM-service add-peripheral tracefs fetchargs record the candidate record pointer, name, and devnode string in `first_hit_line` for the entry, known-name, and init-fail probes.
- Still excluded: full `pm-proxy`, `boot_wlan`, restart-PD request, `/dev/subsys_esoc0`, forced RC1, fake-ONLINE, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping.

## Fetchargs

- `pm_service_add_peripheral_entry`: `record=%x1 name=+4(%x1):string devnode=+68(%x1):string`
- `pm_service_add_peripheral_known_name`: `record=%x25 name=+0(%x21):string devnode=+68(%x25):string`
- `pm_service_add_peripheral_init_fail`: `name=+0(%x21):string devnode=+0(%x25):string`

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Expected Live Discriminator

- V1791 should run one rollbackable live gate with this artifact and classify the exact candidate/devnode strings that fail `access(F_OK)`.
- If the strings show a missing private `/dev/subsys_modem` path, the next separately scoped repair can materialize read-only private devnode parity for PM-service discovery.
- If the strings show `/dev/subsys_esoc0` or another eSoC path, stop and classify host-only before any live repair; do not open the path blindly.
- The gate remains one-run: do not autonomously chain into PM repair, WLAN-PD cascade, Wi-Fi HAL, scan/connect, or external ping.

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
