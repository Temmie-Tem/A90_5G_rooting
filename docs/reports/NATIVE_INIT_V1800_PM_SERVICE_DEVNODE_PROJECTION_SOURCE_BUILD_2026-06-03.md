# Native Init V1800 PM-service Devnode Projection Source Build

## Summary

- Cycle: `V1800`
- Type: source/build-only rollbackable WLAN-PD PM-service private-dev projection test boot artifact
- Decision: `v1800-pm-service-devnode-projection-source-build-pass`
- Result: PASS
- Reason: helper v341 adds a scoped service-object route variant that projects only the two V1799-proven absent PM-service candidate char nodes (`subsys_esoc0` and `subsys_modem`) into the private Android `/dev` tree before `pm-service` starts.
- Manifest: `tmp/wifi/v1800-pm-service-devnode-projection-test-boot/manifest.json`
- Boot image: `tmp/wifi/v1800-pm-service-devnode-projection-test-boot/boot_linux_v1800_pm_service_devnode_projection.img`
- Boot SHA256: `d03323520529f437a6c5f9a5c1e22c4dff577ff3f5e75e0deffc10cb6ca05e95`
- Init: `A90 Linux init 0.9.150 (v1800-pm-service-devnode-projection)`
- Helper marker: `a90_android_execns_probe v341`
- Helper SHA256: `61b85eb5134c89d91cc83a9c3d74e07cf12d89a7ca6e5826e510a07fae44fa6b`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-service-object-devnode-projection-trigger-start-only`
- Property root: `/mnt/sdext/a90/private-property-v317/v1800/dev/__properties__`
- Base route remains the bounded service-object route: service managers, firmware-serve stack, `pm_proxy_helper`, `pm-service`, `/dev/subsys_modem` holder, `cnss_diag`, and stock `cnss-daemon`.
- Added projection only: setup reads `/sys/class/subsys/subsys_esoc0/dev` and `/sys/class/subsys/subsys_modem/dev`, then creates private char nodes `subsys_esoc0` and `subsys_modem` with mode `0640` and owner/group `system`.
- Added early observer: `wifi_companion_start.private_node.subsys_esoc0.*` and `wifi_companion_start.private_node.subsys_modem.*` record private-dev status before child startup.
- Retained observer: the V1798 final no-open `wlan_pd_service_object_visible_trigger.devnode_access.*` block remains present.
- Still excluded: `esoc-0` projection, `/dev/subsys_esoc0` open, forced RC1, fake-ONLINE, full `pm-proxy`, `boot_wlan`, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping.

## Expected Live Discriminator

- V1801 should run one rollbackable live gate with this artifact and classify whether PM-service reaches supported-list commit, still fails despite visible private nodes, or loses route safety.
- `list-commit-progress`: PM-service list commit becomes nonzero; stop before restart-PD request, WLAN-PD cascade, Wi-Fi HAL, or scan/connect.
- `projection-visible-still-fails`: early private-node fields show both char nodes but PM-service still hits init-fail/list-commit `0`; inspect process-domain or ioctl/open behavior without opening `/dev/subsys_esoc0` in the runner.
- `projection-setup-failed`: early private-node fields are missing or non-char; return to sysfs/dev projection setup.
- `safety-regression`: any hard-stop field regresses; roll back and stop.

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, open `/dev/subsys_esoc0`, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
