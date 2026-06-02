# Native Init V1777 Service-object Policy-load Source Build

## Summary

- Cycle: `V1777`
- Type: source/build-only rollbackable WLAN-PD service-object policy-load test boot artifact
- Decision: `v1777-service-object-policy-load-source-build-pass`
- Result: PASS
- Reason: carries V1774 repair target into a rollbackable test boot: service-object route now loads precompiled SELinux policy before PM actors and rejects zombie per_mgr as ready.
- Manifest: `tmp/wifi/v1777-service-object-policy-load-test-boot/manifest.json`
- Boot image: `tmp/wifi/v1777-service-object-policy-load-test-boot/boot_linux_v1777_service_object_policy_load.img`
- Boot SHA256: `14cfe7f0ca1c672a21904b8554102aee9c0b506a9a92fb0b846a48d7d25f0a1d`
- Init: `A90 Linux init 0.9.142 (v1777-service-object-policy-load)`
- Helper marker: `a90_android_execns_probe v333`
- Helper SHA256: `527972344940f2ed2456b4a2186aab31c33d4d69e4cf1a30e1aa024ce2da346b`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-service-object-visible-trigger-start-only`
- Property root: `/mnt/sdext/a90/private-property-v317/v1777/dev/__properties__`
- Actors remain bounded: `servicemanager`, `hwservicemanager`, VND service-manager fallback, `qrtr-ns`, `pd-mapper`, `rmt_storage`, `tftp_server`, `pm_proxy_helper`, `pm-service`, `/dev/subsys_modem` holder, `cnss_diag`, and stock `cnss-daemon`.
- Repair target: service-object route now applies the V1092 SELinux policy-load precondition before PM actors and does not treat zombie `pm-service` as ready.
- Still excluded: full `pm-proxy`, `boot_wlan`, restart-PD request, `/dev/subsys_esoc0`, forced RC1, fake-ONLINE, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping.

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Expected Live Discriminator

- `service-object-route-provider-visible` if `vendor.qcom.PeripheralManager` appears after `per_mgr`.
- `service-object-route-provider-still-hidden` if the SELinux policy-load precondition is present but provider remains absent.
- Subsequent CNSS labels remain separate: `asInterface`, register-TX, `wlanmdsp` request, WLFW service 69, and `wlan0` are not chased by this build unit.

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
