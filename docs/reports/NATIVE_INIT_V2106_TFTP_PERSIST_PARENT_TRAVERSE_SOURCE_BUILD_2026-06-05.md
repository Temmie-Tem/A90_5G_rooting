# Native Init V2106 TFTP Persist Parent Traverse Source Build

## Summary

- Cycle: `V2106`
- Type: source/build-only follow-up to V2103, fixing the unclosed parent-traversal cause of `tftp_server` persist-RFS EACCES.
- Decision: `v2106-tftp-persist-parent-traverse-source-build-pass`
- Result: PASS
- Reason: helper v413 keeps the V2102 light internal-modem route and changes only namespace-local `/mnt`, `/mnt/vendor`, and `/mnt/vendor/persist` from root-only traversal to `root:system 0750`. V2103 proved the leaf persist-RFS directories existed as `vendor_rfs`, but their parents were `0750 root:root`; stock `tftp_server` runs as `vendor_rfs` with supplemental group `system`, so it could not traverse to the leaf directories.
- Manifest: `tmp/wifi/v2106-tftp-persist-parent-traverse-test-boot/manifest.json`
- Boot image: `tmp/wifi/v2106-tftp-persist-parent-traverse-test-boot/boot_linux_v2106_tftp_persist_parent_traverse.img`
- Boot SHA256: `adf74a379c0f54da8da01a1c5df6e8f4b80fc65679a7b0031bdf2817422de6a0`
- Init: `A90 Linux init 0.9.229 (v2106-tftp-persist-parent-traverse)`
- Helper marker: `a90_android_execns_probe v413`
- Helper SHA256: `6750bdf217a2a41e5d97877dd1dd1a7d344e287b8b7aabe15725c91d05ab5bb5`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-post-pm-lower-state-observer-start-only`
- Helper timeout: `75`
- Property root: `/mnt/sdext/a90/private-property-v317/v2106/dev/__properties__`
- Light firmware trace: `True`
- Kept: V2102 route, readonly/readwrite RFS bridges, vendor-owned tombstone dirs, persist-RFS auto-dir targets, `tftp_server` logdw sink, focused PerMgr/WLFW summaries, process-namespace audit, post-BDF surface summary, and long lower-window hold.
- Added: rootfs-namespace-only parent traversal parity for `/mnt`, `/mnt/vendor`, and `/mnt/vendor/persist`; `sda29` remains read-only.
- Excluded: `ota_firewall/ruleset` fabrication, macloader retry, `boot_wlan`/`qcwlanstate` write, module load/unload, driver bind/unbind, DIAG, boot-time QRTR matrix, rild/cnss/pm-service strace, `tftp_server` ptrace, AP QMI send, `/dev/subsys_esoc0`, eSoC notify/BOOT_DONE, PCI rescan/bind, platform unbind, PMIC/GPIO/GDSC/regulator writes, forced RC1/case, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, and firmware/partition writes.

## Branch

- If persist-RFS EACCES clears and Android-order `server_check -> ota_firewall -> wlanmdsp` appears, chase WLFW 69/BDF/FW-ready/`wlan0` next.
- If EACCES clears but the TFTP bootstrap branch is still absent, the blocker is modem-internal before the producer chooses WLAN-PD firmware fetch.
- If EACCES persists, inspect SELinux label parity for `/mnt/vendor/persist*` before moving to active modem-side DIAG.

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, run Wi-Fi HAL, scan/connect, use credentials, configure DHCP/routes, perform external ping, write `/dev/wlan`, write `qcwlanstate`, open `/dev/subsys_esoc0`, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, use DIAG, ptrace `tftp_server`, send AP QMI payloads, or write firmware/boot/device partitions.
