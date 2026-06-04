# Native Init V2108 TFTP Persist-RFS Leaf Precreate Source Build

## Summary

- Cycle: `V2108`
- Type: source/build-only follow-up to V2107, fixing the remaining stock `tftp_server` persist-RFS ENOENT mkdir targets.
- Decision: `v2108-tftp-persist-rfs-leaf-precreate-source-build-pass`
- Result: PASS
- Reason: helper v414 keeps the V2106 light internal-modem route and adds only namespace-local `/mnt/vendor/persist/rfs/{mdm/mpss,apq/gnss}` precreation as `vendor_rfs:vendor_rfs 0770`. V2107 proved parent traversal works and exposed the remaining `mkdir failed: [2]` startup targets for stock `tftp_server`.
- Manifest: `tmp/wifi/v2108-tftp-persist-rfs-leaf-precreate-test-boot/manifest.json`
- Boot image: `tmp/wifi/v2108-tftp-persist-rfs-leaf-precreate-test-boot/boot_linux_v2108_tftp_persist_rfs_leaf_precreate.img`
- Boot SHA256: `cddeac619c7a80d743c0633c6529cc39d603f3830a94484c133bc8d6270836ff`
- Init: `A90 Linux init 0.9.230 (v2108-tftp-persist-rfs-leaf-precreate)`
- Helper marker: `a90_android_execns_probe v414`
- Helper SHA256: `25a9e1460d9b66a654e729ad3f3b5b4e08fc0157085707fe66ca2419f9293e23`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-post-pm-lower-state-observer-start-only`
- Helper timeout: `75`
- Property root: `/mnt/sdext/a90/private-property-v317/v2108/dev/__properties__`
- Light firmware trace: `True`
- Kept: V2106 route, readonly/readwrite RFS bridges, vendor-owned tombstone dirs, persist-RFS auto-dir targets, parent traversal parity, `tftp_server` logdw sink, focused PerMgr/WLFW summaries, process-namespace audit, post-BDF surface summary, and long lower-window hold.
- Added: rootfs-namespace-only precreation of `/mnt/vendor/persist/rfs/mdm/mpss` and `/mnt/vendor/persist/rfs/apq/gnss`; `sda29` remains read-only.
- Excluded: `ota_firewall/ruleset` fabrication, macloader retry, `boot_wlan`/`qcwlanstate` write, module load/unload, driver bind/unbind, DIAG, boot-time QRTR matrix, rild/cnss/pm-service strace, `tftp_server` ptrace, AP QMI send, `/dev/subsys_esoc0`, eSoC notify/BOOT_DONE, PCI rescan/bind, platform unbind, PMIC/GPIO/GDSC/regulator writes, forced RC1/case, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, and firmware/partition writes.

## Branch

- If persist-RFS mkdir failures clear and Android-order `server_check -> ota_firewall -> wlanmdsp` appears, chase WLFW 69/BDF/FW-ready/`wlan0` next.
- If mkdir failures clear but the TFTP bootstrap branch is still late/incomplete, the blocker is modem-internal before the producer chooses the full WLAN-PD firmware fetch branch.
- If mkdir failures persist, inspect exact missing persist-RFS leaves and stock `tftp_server` path expectations before moving to active modem-side DIAG.

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, run Wi-Fi HAL, scan/connect, use credentials, configure DHCP/routes, perform external ping, write `/dev/wlan`, write `qcwlanstate`, open `/dev/subsys_esoc0`, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, use DIAG, ptrace `tftp_server`, send AP QMI payloads, or write firmware/boot/device partitions.
