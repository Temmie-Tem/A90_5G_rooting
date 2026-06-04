# Native Init V2042 OTA Firewall Ruleset Source Build

## Summary

- Cycle: `V2042`
- Type: source/build-only rollbackable internal-modem full-chain route with passive TFTP logdw plus persist-RFS and ota_firewall readwrite bridges
- Decision: `v2042-ota-firewall-ruleset-source-build-pass`
- Result: PASS
- Reason: helper v387 keeps the V2040 dual-RFS/readwrite and persist-RFS mirror route, then adds an Android-style namespace-local `/vendor/rfs/msm/mpss/readwrite/ota_firewall/ruleset` file before `tftp_server` starts.
- Manifest: `tmp/wifi/v2042-ota-firewall-ruleset-test-boot/manifest.json`
- Boot image: `tmp/wifi/v2042-ota-firewall-ruleset-test-boot/boot_linux_v2042_ota_firewall_ruleset.img`
- Boot SHA256: `5a20dfba5a00a80403a683edec54539d73cff9339aaacb88df14887e9074533b`
- Init: `A90 Linux init 0.9.202 (v2042-ota-firewall-ruleset)`
- Helper marker: `a90_android_execns_probe v387`
- Helper SHA256: `65ea5b7b2e968ebd0ed0d8087657097ce83a583eb4701cec29a6ca4aa564cda9`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-post-pm-lower-state-observer-start-only`
- Helper timeout: `75`
- Property root: `/mnt/sdext/a90/private-property-v317/v2042/dev/__properties__`
- Light firmware trace: `True`
- Observer: passive private `/dev/socket/logdw` plus read-only post-WRQ `mcfg.tmp` stat/open/readback; no ptrace, AP-side strace, QRTR matrix, or QMI send.
- Kept: clean-DSP companion, service managers, `pm-service`, `/dev/subsys_modem` holder, `cnss_diag`, stock `cnss-daemon`, `rmt_storage`, `tftp_server`, `pd-mapper`, firmware mounts, dual-RFS WLAN image bridge, readwrite tmpfs bridge, cap/BDF/cal probes, post-cal indication probes, and long lower-window hold.
- Added: namespace-only `readwrite/ota_firewall/ruleset` file on the existing tmpfs bridge, visible through `/vendor/rfs/msm/mpss/readwrite` and the persist-RFS mirrors, without writing `sda29` or firmware partitions.
- Excluded: boot-time QRTR matrix, rild/cnss/pm-service multi-strace, `tftp_server` ptrace, private SDX50M route, `/dev/subsys_esoc0` open, eSoC notify/BOOT_DONE, PCI rescan/bind, platform unbind, PMIC/GPIO/GDSC/regulator writes, forced RC1/case, restart-PD request, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping.

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, open `/dev/subsys_esoc0`, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
