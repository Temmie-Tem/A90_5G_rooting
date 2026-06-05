# Native Init V2120 Dual-RFS Shared Server Info Source Build

## Summary

- Cycle: `V2120`
- Type: source/build-only discriminator for the tftp_server startup `shared/server_info.txt` RFS bridge.
- Decision: `v2120-dual-rfs-shared-server-info-source-build-pass`
- Result: PASS
- Reason: helper v419 keeps the V2113 root `rmt_storage`/root `tftp_server` route and adds only a namespace-local tmpfs at `/vendor/rfs/msm/mpss/shared/server_info.txt`, matching the startup path that previously logged `Info file creation failed`.
- Manifest: `tmp/wifi/v2120-dual-rfs-shared-server-info-test-boot/manifest.json`
- Boot image: `tmp/wifi/v2120-dual-rfs-shared-server-info-test-boot/boot_linux_v2120_dual_rfs_shared_server_info.img`
- Boot SHA256: `b4a0584d745668744a0323669bef484aec3bebf5ebdf4844d03897d88d22e0a8`
- Init: `A90 Linux init 0.9.235 (v2120-dual-rfs-shared-server-info)`
- Helper marker: `a90_android_execns_probe v419`
- Helper SHA256: `d979538c8b405a31d1f7b4d9051502408599dc54e3ab278a5512d0e14fb8e49b`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-post-pm-lower-state-observer-start-only`
- Helper timeout: `75`
- Property root: `/mnt/sdext/a90/private-property-v317/v2120/dev/__properties__`
- Light firmware trace: `True`
- Kept: V2113 exact Android dual-RFS WLAN image path, readwrite tmpfs, persist-RFS leaf precreate, process namespace audit, root lower companions, PerMgr/WLFW focused summaries, and long lower-window hold.
- Added: `/vendor/rfs/msm/mpss/shared` tmpfs plus writable `server_info.txt`, owned `vendor_rfs:vendor_rfs_shared`, rootfs namespace only.
- Excluded: tftp identity changes, OTA ruleset fabrication, mcfg optimization, macloader retry, DIAG, boot-time QRTR matrix, rild/cnss/pm-service strace, `tftp_server` ptrace, AP QMI send, `/dev/subsys_esoc0`, eSoC notify/BOOT_DONE, PCI rescan/bind, platform unbind, PMIC/GPIO/GDSC/regulator writes, forced RC1/case, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, and firmware/partition writes.

## Branch

- If `shared/server_info.txt` clears startup errors and the Android-order `ota_firewall`/`wlanmdsp` branch appears, chase WLFW 69/BDF/FW-ready/`wlan0` next.
- If server_info clears but the route remains post-UP `server_check`/mcfg-only, this startup file is falsified as the WLAN-PD firmware-fetch trigger.
- If artifact validation fails, do not run the live handoff.

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, run Wi-Fi HAL, scan/connect, use credentials, configure DHCP/routes, perform external ping, write `/dev/wlan`, write `qcwlanstate`, open `/dev/subsys_esoc0`, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, use DIAG, ptrace `tftp_server`, send AP QMI payloads, or write firmware/boot/device partitions.
