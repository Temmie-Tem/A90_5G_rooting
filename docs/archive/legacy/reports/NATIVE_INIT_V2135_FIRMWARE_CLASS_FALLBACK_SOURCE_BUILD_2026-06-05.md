# Native Init V2135 Firmware Class Fallback Source Build

## Summary

- Cycle: `V2135`
- Type: source/build-only discriminator for the exact kernel firmware-class fallback request edge.
- Decision: `v2135-firmware-class-fallback-source-build-pass`
- Result: PASS
- Reason: helper v425 keeps the V2133 global firmware_class vendor-path bridge and V2131 stack sampler, then adds a bounded read-only `/sys/class/firmware` and `/sys/devices/virtual/firmware` snapshot at the stuck `request_firmware -> qdf_ini_parse` window.
- Manifest: `tmp/wifi/v2135-firmware-class-fallback-test-boot/manifest.json`
- Boot image: `tmp/wifi/v2135-firmware-class-fallback-test-boot/boot_linux_v2135_firmware_class_fallback.img`
- Boot SHA256: `a92b0ef208d257a5532cc8f6cb436d0affa4a9ba4c00075d6dd81a087efd93cc`
- Init: `A90 Linux init 0.9.242 (v2135-firmware-class-fallback)`
- Helper marker: `a90_android_execns_probe v425`
- Helper SHA256: `6ca1a61f71fd68df2d3ce1d015e61830490cb1f63a4e0ae059389f74eb1f3d8d`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-post-pm-lower-state-observer-start-only`
- Helper timeout: `75`
- Property root: `/mnt/sdext/a90/private-property-v317/v2135/dev/__properties__`
- Light firmware trace: `True`
- Kept: V2133 rollbackable `firmware_class.path=/mnt/vendor/firmware` apply/restore, read-only `sda29` mount, dual-RFS bridges, readwrite tmpfs bridge, post-FW_READY `boot_wlan` gate, stack sampler, focused PerMgr/WLFW summaries, post-BDF summary, and long lower-window hold.
- Added: `firmware_class_fallback_sampler` at `after_boot_wlan_trigger` and `after_boot_wlan_long_window`, with hard-capped read-only sysfs enumeration and no reads from firmware `data` nodes.
- Excluded: firmware fallback writes, tracefs writes, sysrq, DIAG, boot-time QRTR matrix, rild/cnss/pm-service strace, `tftp_server` ptrace, AP QMI send, module load/unload, driver bind/unbind, `/dev/subsys_esoc0`, eSoC notify/BOOT_DONE, PCI rescan/bind, platform unbind, PMIC/GPIO/GDSC/regulator writes, forced RC1/case, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, and firmware/partition writes.

## Branch

- If the sampler captures a `WCNSS`/`qca`/`qdf`/`cfg` fallback entry while the stack remains in `qdf_ini_parse`, the exact request name/error is the next bounded fix target.
- If no firmware-class fallback entry exists while the stack remains in `qdf_ini_parse`, the next unit should capture the `qdf_file_read()` argument rather than retrying the AP-side producer path.
- If `wlan0` appears, stop before credentials and run the dedicated connectivity gate.

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Safety Scope

This build script performed host-side source/build work only. The eventual live handoff is rollbackable and permits only the existing temporary `firmware_class.path` sysfs write with restore plus read-only firmware-class sysfs snapshots. It does not write firmware fallback `loading`/`data` nodes, `sda29`, firmware files, EFS, boot partitions, Wi-Fi credentials, network routes, or external pings.
