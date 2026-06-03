# Native Init V1798 PM-service Devnode Access Observer Source Build

## Summary

- Cycle: `V1798`
- Type: source/build-only rollbackable WLAN-PD PM-service devnode access observer test boot artifact
- Decision: `v1798-pm-service-devnode-access-observer-source-build-pass`
- Result: PASS
- Reason: helper v340 keeps the V1795 PM-service count/sample trace observers and adds a no-open, no-mknod private-root `lstat`/`access(F_OK)` status block for both PM-service candidate devnodes (`subsys_esoc0` and `subsys_modem`) in the service-object route.
- Manifest: `tmp/wifi/v1798-pm-service-devnode-access-observer-test-boot/manifest.json`
- Boot image: `tmp/wifi/v1798-pm-service-devnode-access-observer-test-boot/boot_linux_v1798_pm_service_devnode_access_observer.img`
- Boot SHA256: `367da5a0ba41d25c27dffa586138aa757da3fbf1f0ca03ce8ad0ddc20a3e46ca`
- Init: `A90 Linux init 0.9.149 (v1798-pm-service-devnode-access-observer)`
- Helper marker: `a90_android_execns_probe v340`
- Helper SHA256: `207628058a80942b0775377f9bddb9453ad0dd416cab33de3dd7bf278b92f595`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-service-object-visible-trigger-start-only`
- Property root: `/mnt/sdext/a90/private-property-v317/v1798/dev/__properties__`
- Base route remains the bounded V1792/V1795 service-object route: service managers, firmware-serve stack, `pm_proxy_helper`, `pm-service`, `/dev/subsys_modem` holder, `cnss_diag`, and stock `cnss-daemon`.
- Added observer only: the route summary now emits `wlan_pd_service_object_visible_trigger.devnode_access.*` plus per-candidate `devnode.sdx50m.*` and `devnode.modem.*` fields.
- The new status uses `lstat` and `access(F_OK)` only; it does not open `/dev/subsys_esoc0`, create nodes, change modes, or attempt repair.
- Still excluded: full `pm-proxy`, `boot_wlan`, restart-PD request, `/dev/subsys_esoc0` open, forced RC1, fake-ONLINE, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping.

## New Output Fields

- `wlan_pd_service_object_visible_trigger.devnode_access.open_attempted=0`
- `wlan_pd_service_object_visible_trigger.devnode_access.mknod_attempted=0`
- `wlan_pd_service_object_visible_trigger.devnode.sdx50m.name=subsys_esoc0`
- `wlan_pd_service_object_visible_trigger.devnode.modem.name=subsys_modem`
- Per candidate: `path`, `access_f_ok`, `access_errno`, `lstat_ok`, `lstat_errno`, `char_device`, `major`, `minor`, `mode`, `uid`, and `gid`.

## Retained Observers

- `pm_service_init_first_count_load`: `first_count=%x8`
- `pm_service_init_second_count_load`: `second_count=%x8`
- `pm_service_init_first_add_peripheral_call`: `record=%x1 name=+4(%x1):string devnode=+68(%x1):string off_timeout=%x2 ack_timeout=%x3 flags=%x4`
- `pm_service_init_second_add_peripheral_call`: `record=%x1 name=+4(%x1):string devnode=+68(%x1):string off_timeout=%x2 ack_timeout=%x3 flags=%x4`
- PM-service event output still includes `sample_count` and `sample_line_0..3` for each `pm_server_uprobe` event.
- Retained: `pm_server_register_no_peripheral`: `peripheral=+0(%x26):string`
- Retained: `pm_service_add_peripheral_entry`: `record=%x1 name=+4(%x1):string devnode=+68(%x1):string`
- Retained: `pm_service_add_peripheral_known_name`: `record=%x25 name=+0(%x21):string devnode=+68(%x25):string`
- Retained: `pm_service_add_peripheral_init_fail`: `name=+0(%x21):string devnode=+0(%x25):string`

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Expected Live Discriminator

- V1799 should run one rollbackable live gate with this artifact and classify whether the PM-service candidates are absent, non-character, mode/owner mismatched, or already visible in the private Android `/dev` tree before any repair.
- `both-devnodes-absent`: `sdx50m` and `modem` both report `lstat_ok=0` / `access_f_ok=0`; return to private-dev materialization source, not PM-service list logic.
- `modem-present-sdx50m-absent`: only `subsys_modem` is present; keep repair scoped to candidate parity and do not open `/dev/subsys_esoc0`.
- `nonchar-or-mode-mismatch`: a path exists but is not a char device or has unexpected mode/owner; classify source of private-dev projection before repair.
- `candidate-visible-but-pm-fails`: helper sees both candidates but PM-service still fails; investigate process-domain/namespace parity without Wi-Fi HAL escalation.

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, open `/dev/subsys_esoc0`, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
