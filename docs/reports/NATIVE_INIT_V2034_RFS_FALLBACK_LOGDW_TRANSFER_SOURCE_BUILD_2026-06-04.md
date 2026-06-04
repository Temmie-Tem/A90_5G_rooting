# Native Init V2034 RFS Fallback Logdw Transfer Source Build

## Summary

- Cycle: `V2034`
- Type: source/build-only rollbackable internal-modem Android-parity RFS fallback with passive stock `tftp_server` logdw transfer observer
- Decision: `v2034-rfs-fallback-logdw-transfer-source-build-pass`
- Result: PASS
- Reason: helper v383 keeps the Android-parity RFS bridge (`firmware_mnt/image` probe absent, `vendor/firmware` fallback present), keeps readwrite tmpfs, and adds only a private `/dev/socket/logdw` datagram sink so stock `tftp_server` can report whether `wlanmdsp.mbn` transfer completes without ptrace.
- Manifest: `tmp/wifi/v2034-rfs-fallback-logdw-transfer-test-boot/manifest.json`
- Boot image: `tmp/wifi/v2034-rfs-fallback-logdw-transfer-test-boot/boot_linux_v2034_rfs_fallback_logdw_transfer.img`
- Boot SHA256: `7121000824b033096cf7b2e513f536c8ffb40eadaf46e9fedaa8104ca8665bc5`
- Init: `A90 Linux init 0.9.198 (v2034-rfs-fallback-logdw-transfer)`
- Helper marker: `a90_android_execns_probe v383`
- Helper SHA256: `4d0b3523e43a2343a8bd6878a2acc1ef3b5f19c32c783605ce1614b5745dca15`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-post-pm-lower-state-observer-start-only`
- Helper timeout: `75`
- Property root: `/mnt/sdext/a90/private-property-v317/v2034/dev/__properties__`
- Light firmware trace: `True`
- TFTP observer: passive private `/dev/socket/logdw` datagram sink; no `tftp_server` ptrace, no AP-side strace, no QRTR matrix, no QMI send.
- Kept: clean-DSP companion, service managers, `pm-service`, `/dev/subsys_modem` holder, `cnss_diag`, stock `cnss-daemon`, `rmt_storage`, `tftp_server`, `pd-mapper`, firmware mounts, Android-parity readonly RFS bridge, readwrite tmpfs bridge, cap/BDF/cal probes, post-cal indication probes, and light klog/ICNSS summaries.
- Excluded: boot-time QRTR matrix, rild/cnss/pm-service multi-strace, `tftp_server` ptrace, private SDX50M route, `/dev/subsys_esoc0` open, eSoC notify/BOOT_DONE, PCI rescan/bind, platform unbind, PMIC/GPIO/GDSC/regulator writes, forced RC1/case, restart-PD request, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping.

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, open `/dev/subsys_esoc0`, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
