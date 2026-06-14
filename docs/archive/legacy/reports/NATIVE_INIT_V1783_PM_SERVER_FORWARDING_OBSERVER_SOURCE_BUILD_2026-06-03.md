# Native Init V1783 PM Server Forwarding Observer Source Build

## Summary

- Cycle: `V1783`
- Type: source/build-only rollbackable WLAN-PD PM server forwarding observer test boot artifact
- Decision: `v1783-pm-server-forwarding-observer-source-build-pass`
- Result: PASS
- Reason: carries V1782 repair target into a rollbackable test boot: the service-object route keeps VND service-manager parity and helper v335 adds PM server-side register-path uprobes.
- Manifest: `tmp/wifi/v1783-pm-server-forwarding-observer-test-boot/manifest.json`
- Boot image: `tmp/wifi/v1783-pm-server-forwarding-observer-test-boot/boot_linux_v1783_pm_server_forwarding_observer.img`
- Boot SHA256: `d6fed20d3c72bf68d2b7bba55ec40691e84ca437f6d8d07ad189c4fde3f42612`
- Init: `A90 Linux init 0.9.144 (v1783-pm-server-forwarding-observer)`
- Helper marker: `a90_android_execns_probe v335`
- Helper SHA256: `e906119056137401737bbe5741418f6a79505d134a8cffa92cbcfa6d12ea6c65`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-service-object-visible-trigger-start-only`
- Property root: `/mnt/sdext/a90/private-property-v317/v1783/dev/__properties__`
- Actors remain bounded: `servicemanager`, `hwservicemanager`, `vndservicemanager` (`/vendor/bin/vndservicemanager /dev/vndbinder`), `qrtr-ns`, `pd-mapper`, `rmt_storage`, `tftp_server`, `pm_proxy_helper`, `pm-service`, `/dev/subsys_modem` holder, `cnss_diag`, and stock `cnss-daemon`.
- Repair target: helper v335 adds `pm-service` server-side register entry / supported-peripheral match / add-client / return tracefs uprobes while preserving the V1781 route and V1092 SELinux policy-load precondition.
- Still excluded: full `pm-proxy`, `boot_wlan`, restart-PD request, `/dev/subsys_esoc0`, forced RC1, fake-ONLINE, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping.

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Expected Live Discriminator

- `pm-server-register-success-return` if server-side PM forwarding reaches the retained success checkpoint.
- `pm-server-register-entry-only`, `pm-server-prematch-list-traversal`, `pm-server-match-no-permission`, or `pm-server-add-client-no-success` if the forwarding path stops earlier.
- Subsequent CNSS labels remain separate: `asInterface`, register-TX, `wlanmdsp` request, WLFW service 69, and `wlan0` are not chased by this build unit.

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
