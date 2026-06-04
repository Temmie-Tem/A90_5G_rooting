# Native Init V2050 Passive DIAG Pre-WLANMDSP Trigger Source Build

## Summary

- Cycle: `V2050`
- Type: source/build-only rollbackable internal-modem route with passive pre-`wlanmdsp` ordering timestamps plus a capped O_RDONLY `/dev/diag` sink
- Decision: `v2050-passive-diag-pre-wlanmdsp-trigger-source-build-pass`
- Result: PASS
- Reason: helper v390 keeps the V2045 fallback readonly bridge, readwrite tmpfs, persist-RFS tmpfs mirrors, passive logdw, and read-only mcfg observer, and adds only a private-node, O_RDONLY, O_NONBLOCK `/dev/diag` passive sink with no ioctl/write/log-mask operations.
- Manifest: `tmp/wifi/v2050-passive-diag-pre-wlanmdsp-trigger-test-boot/manifest.json`
- Boot image: `tmp/wifi/v2050-passive-diag-pre-wlanmdsp-trigger-test-boot/boot_linux_v2050_passive_diag_pre_wlanmdsp_trigger.img`
- Boot SHA256: `86356ee510d4881fb4de25467753428c2c8e76366525135e30f41b73b99679cf`
- Init: `A90 Linux init 0.9.205 (v2050-passive-diag-pre-wlanmdsp-trigger)`
- Helper marker: `a90_android_execns_probe v390`
- Helper SHA256: `816dc5f316dbb31afe82d23e1993936e37c9b486ca39b6c3ce9a2e28fb149f74`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-post-pm-lower-state-observer-start-only`
- Helper timeout: `75`
- Property root: `/mnt/sdext/a90/private-property-v317/v2050/dev/__properties__`
- Light firmware trace: `True`
- Observer: passive private `/dev/socket/logdw` with monotonic record timestamps plus passive private `/dev/diag` O_RDONLY reads; no DIAG ioctl/write/log-mask, ptrace, AP-side strace, QRTR matrix, or QMI send.
- Kept: clean-DSP companion, service managers, `pm-service`, `/dev/subsys_modem` holder, `cnss_diag`, stock `cnss-daemon`, `rmt_storage`, `tftp_server`, `pd-mapper`, firmware mounts, Android-parity fallback readonly RFS bridge, readwrite tmpfs bridge, persist-RFS tmpfs mirrors, cap/BDF/cal probes, post-cal indication probes, and long lower-window hold.
- Excluded: boot-time QRTR matrix, rild/cnss/pm-service multi-strace, `tftp_server` ptrace, private SDX50M route, `/dev/subsys_esoc0` open, eSoC notify/BOOT_DONE, PCI rescan/bind, platform unbind, PMIC/GPIO/GDSC/regulator writes, forced RC1/case, restart-PD request, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, and firmware partition writes.

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, open `/dev/subsys_esoc0`, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
