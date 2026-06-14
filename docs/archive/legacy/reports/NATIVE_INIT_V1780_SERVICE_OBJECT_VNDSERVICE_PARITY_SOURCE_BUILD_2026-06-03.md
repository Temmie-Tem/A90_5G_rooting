# Native Init V1780 Service-object VND-service Parity Source Build

## Summary

- Cycle: `V1780`
- Type: source/build-only rollbackable WLAN-PD service-object vndservice-parity test boot artifact
- Decision: `v1780-service-object-vndservice-parity-source-build-pass`
- Result: PASS
- Reason: carries V1779 repair target into a rollbackable test boot: service-object route now keeps the vendor vndservicemanager executable path, preserving V1092 provider-positive VND service-manager parity.
- Manifest: `tmp/wifi/v1780-service-object-vndservice-parity-test-boot/manifest.json`
- Boot image: `tmp/wifi/v1780-service-object-vndservice-parity-test-boot/boot_linux_v1780_service_object_vndservice_parity.img`
- Boot SHA256: `11b7778633423505ecb7756a25e79817cca05bebd2c1caf328ea624a02db51b5`
- Init: `A90 Linux init 0.9.143 (v1780-service-object-vndservice-parity)`
- Helper marker: `a90_android_execns_probe v334`
- Helper SHA256: `bc99790004cd82fceea33eb4e0db41adbf4ea663c2b5706d03ae1aaba03482cb`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-service-object-visible-trigger-start-only`
- Property root: `/mnt/sdext/a90/private-property-v317/v1780/dev/__properties__`
- Actors remain bounded: `servicemanager`, `hwservicemanager`, vendor `vndservicemanager` (`/vendor/bin/vndservicemanager /dev/vndbinder`), `qrtr-ns`, `pd-mapper`, `rmt_storage`, `tftp_server`, `pm_proxy_helper`, `pm-service`, `/dev/subsys_modem` holder, `cnss_diag`, and stock `cnss-daemon`.
- Repair target: service-object route now uses `/vendor/bin/vndservicemanager /dev/vndbinder`, while preserving the V1092 SELinux policy-load precondition and zombie `pm-service` readiness guard.
- Still excluded: full `pm-proxy`, `boot_wlan`, restart-PD request, `/dev/subsys_esoc0`, forced RC1, fake-ONLINE, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping.

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Expected Live Discriminator

- `service-object-route-provider-visible` if `vendor.qcom.PeripheralManager` appears after `per_mgr`.
- `service-object-route-provider-still-hidden` if vendor vndservicemanager parity is present but provider remains absent.
- Subsequent CNSS labels remain separate: `asInterface`, register-TX, `wlanmdsp` request, WLFW service 69, and `wlan0` are not chased by this build unit.

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
