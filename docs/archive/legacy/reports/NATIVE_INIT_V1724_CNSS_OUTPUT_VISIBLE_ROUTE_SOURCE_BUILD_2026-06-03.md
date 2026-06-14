# Native Init V1724 CNSS Output-visible Route Source Build

## Summary

- Cycle: `V1724`
- Type: source/build-only rollbackable WLAN-PD cnss-daemon output-visibility test boot artifact
- Decision: `v1724-cnss-output-visible-route-source-build-pass`
- Result: PASS
- Reason: corrects the helper CNSS kmsg property contract to `persist.vendor.cnss-daemon.kmsg_logging=1` without adding PM/service-window actors
- Manifest: `tmp/wifi/v1724-cnss-output-visible-route-test-boot/manifest.json`
- Boot image: `tmp/wifi/v1724-cnss-output-visible-route-test-boot/boot_linux_v1724_cnss_output_visible_route.img`
- Boot SHA256: `44c12fd4320db430c1b3ee0f32230b76a2194bf7657218e26a1a9b513aa0aac5`
- Init: `A90 Linux init 0.9.135 (v1724-cnss-output-visible-route)`
- Helper marker: `a90_android_execns_probe v322`
- Helper SHA256: `9d369ceed2e352114cd7e9e453f8bcddb84914a7e35a819f7094709e78b2e35c`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-cnss-output-visibility-start-only`
- Property root: `/mnt/sdext/a90/private-property-v317/v1724/dev/__properties__`
- Actors: `qrtr-ns`, `pd-mapper`, `rmt_storage`, `tftp_server`, `/dev/subsys_modem` holder, `cnss_diag`, stock `cnss-daemon`.
- Output classifier watches for `wlfw_start: Starting` and the eight pre-WLFW `Failed to ...` init strings.
- No service-manager, PM trio, `vendor.qcom.PeripheralManager`, `boot_wlan`, `/dev/subsys_esoc0`, forced RC1, fake-ONLINE, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping.

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Live Labels

- `wlfw-start-reached-downstream-block`
- `cnss-init-step-failed-<name>`
- `cnss-output-still-invisible`

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
