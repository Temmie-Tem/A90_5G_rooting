# Native Init V1846 PM-Service Open-Context Source Build

## Summary

- Cycle: `V1846`
- Type: source/build-only rollbackable PM-service post-ack open-context observer test boot artifact
- Decision: `v1846-pm-service-open-context-source-build-pass`
- Result: PASS
- Reason: helper v356 keeps the V1844 post-ack branch observer and adds read-only PM-service context uprobes for corrected power-state load, open-object fields, path load, fd store/compare, and open-success counter.
- Manifest: `tmp/wifi/v1846-pm-service-open-context-test-boot/manifest.json`
- Boot image: `tmp/wifi/v1846-pm-service-open-context-test-boot/boot_linux_v1846_pm_service_open_context.img`
- Boot SHA256: `d59877d8b162a0a3c24d764b6f6190e8a296473b58819c7d24086f7584abd411`
- Init: `A90 Linux init 0.9.165 (v1846-pm-service-open-context)`
- Helper marker: `a90_android_execns_probe v356`
- Helper SHA256: `85c3a6f5378b68f92e40b3dad1f83f49e70a1f188fcaa69e9f664684a5966791`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-post-pm-lower-state-observer-start-only`
- Property root: `/mnt/sdext/a90/private-property-v317/v1846/dev/__properties__`
- Base route remains the bounded WLAN-PD post-PM lower observer from V1844, including callback/ack hit counters, PM-service post-ack branch hit counters, PMIC/GDSC focus samples, and inherited bounded QRTR/QMI probes.
- Added PM-service open-context labels: `pm_service_post_ack_power_state_loaded`, `pm_service_post_ack_open_context`, `pm_service_post_ack_open_path_loaded`, `pm_service_post_ack_open_fd_store`, `pm_service_post_ack_open_fd_compare`, `pm_service_post_ack_open_success_counter`.
- The new context labels are read-only tracefs uprobes around `pm-service` offsets `0x88cc`, `0x8cc8`, `0x8ccc`, `0x8cd8`, `0x8ce0`, and `0x8ce8`.
- Explicit limitation: V1846 is a build artifact only; a later rollbackable handoff must confirm which context labels register and what field values are captured.
- Still excluded: direct `/dev/subsys_esoc0` open, fake-ONLINE, eSoC notify/BOOT_DONE, PCI rescan/bind, platform unbind, PMIC/GPIO/GDSC writes, `boot_wlan`, restart-PD request, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping.

## Expected Live Discriminator

- `open-context-modem-success-static`: context labels confirm `/dev/subsys_modem` open success while lower state stays static.
- `open-context-esoc0-or-powerup-progress`: context labels show `/dev/subsys_esoc0`, powerup thread, inferred eSoC open, MHI, WLFW service 69, or `wlan0`; stop before Wi-Fi HAL/scan/connect.
- `open-context-contract-missing`: expected context labels fail to register or enable.
- `safety-regression`: any forbidden side effect appears; stop and roll back.

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, open `/dev/subsys_esoc0`, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
