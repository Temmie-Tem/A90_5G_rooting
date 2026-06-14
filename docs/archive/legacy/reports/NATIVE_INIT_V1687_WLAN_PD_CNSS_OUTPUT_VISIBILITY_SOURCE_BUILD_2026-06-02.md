# Native Init V1687 WLAN-PD cnss-daemon Output Visibility Source Build

## Summary

- Cycle: `V1687`
- Type: source/build-only rollbackable WLAN-PD firmware-serve output-visibility test boot artifact
- Decision: `v1687-wlan-pd-cnss-output-visibility-source-build-pass`
- Result: PASS
- Reason: preserves the V1680/V1679 internal-modem firmware-serve route and makes cnss-daemon kmsg logging visible through a private property root
- Manifest: `tmp/wifi/v1687-wlan-pd-cnss-output-visibility-test-boot/manifest.json`
- Boot image: `tmp/wifi/v1687-wlan-pd-cnss-output-visibility-test-boot/boot_linux_v1687_wlan_pd_cnss_output_visibility.img`
- Boot SHA256: `d0fba056e819c662270cab32823d81ef032c01ab3ad4a0052872bdf39b306d1c`
- Init: `A90 Linux init 0.9.123 (v1687-wlan-pd-cnss-output-visibility)`
- Helper marker: `a90_android_execns_probe v309`
- Helper SHA256: `8a1b5ade562c0da6bcd14734e00cf722fe10673a5889148eacbdf98a0914dabc`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-cnss-output-visibility-start-only`
- Property root: `/mnt/sdext/a90/private-property-v317/v1687/dev/__properties__`
- Actors: `qrtr-ns`, `pd-mapper`, `rmt_storage`, `tftp_server`, `/dev/subsys_modem` holder, `cnss_diag`, stock `cnss-daemon`
- No service-manager, PM trio, `/dev/subsys_esoc0`, forced RC1, fake-ONLINE, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping.

## cnss-daemon Visibility Properties

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Labels

- `wlfw-start-reached-downstream-block`
- `cnss-init-step-failed-<name>`
- `cnss-output-still-invisible`

## Failure Patterns

- `Failed to init nl_loop`
- `Failed to init netlink common`
- `Failed to init interop issues ap`
- `Failed to init hang issues ap`
- `Failed to init gw update loop`
- `Failed to init user interface`
- `Failed to start wlan service`
- `Failed to start wlan datapath service`

## Safety Scope

This build script performed host-side source/build work only. It did not issue device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.

## Next

A separate live handoff may deploy the generated private property root under the documented remote path, flash this test boot, run one bounded observation window, then roll back to `stage3/boot_linux_v724.img` and verify selftest `fail=0`.
