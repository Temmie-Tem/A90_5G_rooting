# Native Init V1775 Service-object Property-contract Source Build

## Summary

- Cycle: `V1775`
- Type: source/build-only rollbackable WLAN-PD service-object property-contract test boot artifact
- Decision: `v1775-service-object-property-contract-source-build-pass`
- Result: PASS
- Reason: carries V1774 repair target into a rollbackable test boot: service-object route now uses the PM property/shutdown-critical-list contract surface.
- Manifest: `tmp/wifi/v1775-service-object-property-contract-test-boot/manifest.json`
- Boot image: `tmp/wifi/v1775-service-object-property-contract-test-boot/boot_linux_v1775_service_object_property_contract.img`
- Boot SHA256: `32e36a1df1c7f65d6742bb62fff7ff1f6bbcd60b8d8634e6277891bcdc0ed99b`
- Init: `A90 Linux init 0.9.141 (v1775-service-object-property-contract)`
- Helper marker: `a90_android_execns_probe v332`
- Helper SHA256: `4bbdfe9ae104f9903efa3cd9e01f317a3af515f8f976103aa0480fd21c8cf1b2`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-service-object-visible-trigger-start-only`
- Property root: `/mnt/sdext/a90/private-property-v317/v1775/dev/__properties__`
- Actors remain bounded: `servicemanager`, `hwservicemanager`, VND service-manager fallback, `qrtr-ns`, `pd-mapper`, `rmt_storage`, `tftp_server`, `pm_proxy_helper`, `pm-service`, `/dev/subsys_modem` holder, `cnss_diag`, and stock `cnss-daemon`.
- Repair target: service-object route is included in the PM property/shutdown-critical-list contract used by V1092.
- Still excluded: full `pm-proxy`, `boot_wlan`, restart-PD request, `/dev/subsys_esoc0`, forced RC1, fake-ONLINE, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping.

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Expected Live Discriminator

- `service-object-route-provider-visible` if `vendor.qcom.PeripheralManager` appears after `per_mgr`.
- `service-object-route-provider-still-hidden` if the PM property contract is present but provider remains absent.
- Subsequent CNSS labels remain separate: `asInterface`, register-TX, `wlanmdsp` request, WLFW service 69, and `wlan0` are not chased by this build unit.

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
