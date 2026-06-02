# Native Init V1699 WLAN-PD cnss-daemon Tracefs Uprobe Visibility Source Build

## Summary

- Cycle: `V1699`
- Type: source/build-only rollbackable WLAN-PD cnss-daemon tracefs uprobe visibility test boot artifact
- Decision: `v1699-wlan-pd-cnss-tracefs-uprobe-source-build-pass`
- Result: PASS
- Reason: preserves the V1680/V1691 internal-modem route and adds read-only `/proc` non-log cnss-daemon control-flow fallback fields
- Manifest: `tmp/wifi/v1699-wlan-pd-cnss-tracefs-uprobe-test-boot/manifest.json`
- Boot image: `tmp/wifi/v1699-wlan-pd-cnss-tracefs-uprobe-test-boot/boot_linux_v1699_wlan_pd_cnss_tracefs_uprobe.img`
- Boot SHA256: `61aa7c3c94b4921b9b2bf9f8a97eadde19c6b96bace5280f06ecfe4414ceabd2`
- Init: `A90 Linux init 0.9.127 (v1699-wlan-pd-cnss-tracefs-uprobe)`
- Helper marker: `a90_android_execns_probe v313`
- Helper SHA256: `33e9b907bbda162033b1cfab9bdccc407d8e57bb5dee5d911f9e9d56dc0c785d`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-cnss-output-visibility-start-only`
- Property root: `/mnt/sdext/a90/private-property-v317/v1699/dev/__properties__`
- Actors: `qrtr-ns`, `pd-mapper`, `rmt_storage`, `tftp_server`, `/dev/subsys_modem` holder, `cnss_diag`, stock `cnss-daemon`
- New evidence prefix: `wlan_pd_cnss_nonlog_control_flow.*`.
- The helper first attempts a bounded tracefs uprobe for `cnss-daemon+0xec00` and falls back to `/proc` PID/maps/fd/task-state evidence when uprobe registration is unavailable.
- No service-manager, PM trio, `boot_wlan`, `/dev/subsys_esoc0`, forced RC1, fake-ONLINE, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping.

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `4` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Live Labels

- `cnss-process-exited-before-wlfw`
- `cnss-wlfw-entry-hit-downstream-wait`
- `cnss-wlfw-entry-not-hit-init-stall`
- `cnss-uprobe-unavailable-fallback-needed`
- Existing output labels remain captured through `wlan_pd_cnss_output_visibility.label`.

## Safety Scope

This build script performed host-side source/build work only. It did not issue device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.

## V1699 Delta

- Uses helper `a90_android_execns_probe v313`.
- Arms a bounded tracefs uprobe for stock `/vendor/bin/cnss-daemon:0xec00` (`wlfw_start`) before starting `cnss-daemon`.
- Mounts debugfs in the test boot so `/sys/kernel/debug/tracing/uprobe_events` can be used when supported.
- Keeps `persist.vendor.cnss-daemon.kmsg_logging=4` and `debug_level=4`.
- Keeps the V1680 internal-modem firmware-serve route and does not add PM/service-window actors or `boot_wlan`.
