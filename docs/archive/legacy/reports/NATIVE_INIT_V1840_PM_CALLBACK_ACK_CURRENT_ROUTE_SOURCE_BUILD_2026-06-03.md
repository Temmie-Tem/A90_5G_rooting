# Native Init V1840 PM Callback/Ack Current-route Source Build

## Summary

- Cycle: `V1840`
- Type: source/build-only rollbackable current-route PM callback/ack observer test boot artifact
- Decision: `v1840-pm-callback-ack-current-route-source-build-pass`
- Result: PASS
- Reason: helper v354 keeps the V1838 lower-continuation sampler and adds read-only current-route `libperipheral_client.so` uprobe hit counts for PM callback/transact and PM acknowledge branch offsets.
- Manifest: `tmp/wifi/v1840-pm-callback-ack-current-route-test-boot/manifest.json`
- Boot image: `tmp/wifi/v1840-pm-callback-ack-current-route-test-boot/boot_linux_v1840_pm_callback_ack_current_route.img`
- Boot SHA256: `13fc50d3f1562d4284d26ae8811a606d87276584c95df0299f5616d8b03990e8`
- Init: `A90 Linux init 0.9.163 (v1840-pm-callback-ack-current-route)`
- Helper marker: `a90_android_execns_probe v354`
- Helper SHA256: `72be56993b5acea0446c3f99bee9b2043695def355d9e32a80ebe138a59c666f`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-post-pm-lower-state-observer-start-only`
- Property root: `/mnt/sdext/a90/private-property-v317/v1840/dev/__properties__`
- Base route remains the bounded WLAN-PD post-PM lower observer from V1838, including PMIC/GDSC focus samples and inherited bounded QRTR/QMI probes.
- Added current-route peripheral uprobe hit-count labels: `periph_pm_callback_stub_entry`, `periph_pm_callback_write_state`, `periph_pm_callback_remote_binder`, `periph_pm_callback_transact_call`, `periph_pm_callback_transact_return`, `periph_pm_client_ack_entry`, `periph_pm_client_ack_match`, `periph_pm_client_ack_virtual_call`, `periph_pm_server_ontransact_entry`, `periph_pm_server_ack_read_state`, `periph_pm_server_ack_impl_call`, and `periph_pm_server_ack_write_ret`.
- These additions reuse the existing `wlan_pd_cnss_nonlog_control_flow.peripheral_uprobe.*` reporting path and record registration, enablement, hit count, and first-hit line only.
- Explicit limitation: current helper peripheral uprobe records are entry-probe hit counters without fetch-arg decoding or uretprobe return decoding.
- Still excluded: direct `/dev/subsys_esoc0` open, fake-ONLINE, eSoC notify/BOOT_DONE, PCI rescan/bind, platform unbind, PMIC/GPIO/GDSC writes, `boot_wlan`, restart-PD request, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping.

## Expected Live Discriminator

- V1841 should run one rollbackable live gate with this artifact only if current-route callback/ack hit counting is accepted as the next read-only target.
- `callback-ack-absent-current-route`: PM list/register/connect still succeed, but callback/ack branch hit counts remain zero and lower state remains static.
- `callback-ack-present-no-powerup`: callback/transact/ack branch hit counts appear, but powerup thread count, inferred eSoC open, mdm-status IRQ, MHI, WLFW service 69, and `wlan0` stay absent.
- `powerup-or-wlfw-progress`: powerup thread, inferred eSoC open, mdm-status IRQ, MHI, WLFW service 69, service74/WLAN-PD UP, or `wlan0` appears; stop before Wi-Fi HAL/scan/connect.
- `safety-regression`: any forbidden side effect appears; stop and roll back.

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, open `/dev/subsys_esoc0`, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
