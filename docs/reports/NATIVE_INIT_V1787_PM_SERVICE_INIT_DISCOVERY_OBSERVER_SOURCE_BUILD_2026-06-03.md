# Native Init V1787 PM Service Init-discovery Observer Source Build

## Summary

- Cycle: `V1787`
- Type: source/build-only rollbackable WLAN-PD PM-service init-discovery observer test boot artifact
- Decision: `v1787-pm-service-init-discovery-observer-source-build-pass`
- Result: PASS
- Reason: helper v336 extends the V1783 PM server observer with `pm-service` init/discovery uprobes for `get_system_info`, add-peripheral calls, and supported-list insertion before Binder registration.
- Manifest: `tmp/wifi/v1787-pm-service-init-discovery-observer-test-boot/manifest.json`
- Boot image: `tmp/wifi/v1787-pm-service-init-discovery-observer-test-boot/boot_linux_v1787_pm_service_init_discovery_observer.img`
- Boot SHA256: `1265c8ee9e60d933aa4e8cfbb6fe40f7562d930b03688b2729785f3aa11a7a3c`
- Init: `A90 Linux init 0.9.145 (v1787-pm-service-init-discovery-observer)`
- Helper marker: `a90_android_execns_probe v336`
- Helper SHA256: `de12704a608535b09b5118656d0eafe61eb76f03bc270f07b42653a6b62b805d`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-service-object-visible-trigger-start-only`
- Property root: `/mnt/sdext/a90/private-property-v317/v1787/dev/__properties__`
- Base route remains the bounded V1783 service-object route: service managers, firmware-serve stack, `pm_proxy_helper`, `pm-service`, `/dev/subsys_modem` holder, `cnss_diag`, and stock `cnss-daemon`.
- Added observer only: `pm-service` main/list init, `get_system_info`, first/second add-peripheral calls, add-peripheral list commit, and pre-Binder init-done uprobes.
- Still excluded: full `pm-proxy`, `boot_wlan`, restart-PD request, `/dev/subsys_esoc0`, forced RC1, fake-ONLINE, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping.

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Expected Live Discriminator

- `pm_service_init_get_system_info_call.hit_count > 0` proves PM service discovery was reached.
- `pm_service_add_peripheral_list_commit.hit_count > 0` proves supported-list population before Binder registration.
- `pm_service_init_get_system_info_call.hit_count > 0` with zero list commits identifies a discovery namespace/input gap.
- The gate remains one-run: do not autonomously chain into PM repair, WLAN-PD cascade, Wi-Fi HAL, scan/connect, or external ping.

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
