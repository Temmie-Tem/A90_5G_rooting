# Native Init V1863 SDX50M Private Mount Source Build

## Summary

- Cycle: `V1863`
- Type: source/build-only rollbackable v356 lower-state observer with private SDX50M cnss-daemon bind mount enabled
- Decision: `v1863-sdx50m-private-mount-source-build-pass`
- Result: PASS
- Reason: helper v356 and PID1 route now allow the bounded WLAN-PD post-PM lower-state observer to bind-mount the pre-staged private SDX50M `cnss-daemon` artifact over `/vendor/bin/cnss-daemon` inside the helper namespace.
- Manifest: `tmp/wifi/v1863-sdx50m-private-mount-test-boot/manifest.json`
- Boot image: `tmp/wifi/v1863-sdx50m-private-mount-test-boot/boot_linux_v1863_sdx50m_private_mount.img`
- Boot SHA256: `1cd1af8bdba3e64d6ba0d1e0ad7ae19338195acb683f6301e5ceb9fa518de0a9`
- Init: `A90 Linux init 0.9.166 (v1863-sdx50m-private-mount)`
- Helper marker: `a90_android_execns_probe v356`
- Helper SHA256: `b974950b5fa19b5bb7dcce1f5a1be47aec4dde650fcc0a565fe0594eb4cf0af5`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-post-pm-lower-state-observer-start-only`
- Property root: `/mnt/sdext/a90/private-property-v317/v1863/dev/__properties__`
- Private CNSS mount: `True` path `/cache/bin/cnss-daemon.sdx50m`
- The private mount is still namespace-local; it does not write `/vendor` and depends on the remote cache artifact already verified by V1862.
- PM-service open-context labels retained: `pm_service_post_ack_power_state_loaded`, `pm_service_post_ack_open_context`, `pm_service_post_ack_open_path_loaded`, `pm_service_post_ack_open_fd_store`, `pm_service_post_ack_open_fd_compare`, `pm_service_post_ack_open_success_counter`.
- Lower-state observer guardrails remain: no direct `/dev/subsys_esoc0` open, no fake ONLINE, no eSoC notify/BOOT_DONE, no forced RC1, no PCI rescan/bind, no PMIC/GPIO/GDSC writes, no Wi-Fi HAL, no scan/connect, no credentials, no DHCP/routes, and no external ping.

## Expected Live Discriminator

- `private-mount-bind-failed`: private artifact did not bind; stop before live bridge interpretation.
- `private-mount-sdx50m-selected`: SDX50M private daemon path executed and changed PM selection; inspect lower publication before connect.
- `private-mount-lower-publication-progress`: WLFW service 69, BDF, MHI, or `wlan0` appears; stop before Wi-Fi HAL/scan/connect.
- `private-mount-pre-wifi-gap`: private mount works but WLFW service 69 and `wlan0` still remain absent.

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, open `/dev/subsys_esoc0`, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
