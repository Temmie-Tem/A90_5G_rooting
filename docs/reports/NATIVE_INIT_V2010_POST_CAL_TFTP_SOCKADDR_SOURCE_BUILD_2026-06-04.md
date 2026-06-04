# Native Init V2010 Post-Cal TFTP Sockaddr Source Build

## Summary

- Cycle: `V2010`
- Type: source/build-only rollbackable internal-modem post-cal tftp sockaddr discriminator
- Decision: `v2010-post-cal-tftp-sockaddr-source-build-pass`
- Result: PASS
- Reason: helper v374 keeps the V2008 downstream consumer route and adds only recvfrom source-sockaddr capture to the bounded single-child `tftp_server` trace.
- Manifest: `tmp/wifi/v2010-post-cal-tftp-sockaddr-test-boot/manifest.json`
- Boot image: `tmp/wifi/v2010-post-cal-tftp-sockaddr-test-boot/boot_linux_v2010_post_cal_tftp_sockaddr.img`
- Boot SHA256: `5494a8a10d7113fe954968adc960f23fb55b06b0a5dae1ffc14778f1fb48774c`
- Init: `A90 Linux init 0.9.187 (v2010-post-cal-tftp-sockaddr)`
- Helper marker: `a90_android_execns_probe v374`
- Helper SHA256: `a32bdb65c208b7eece93916dbcbd5a03b91ce79add6b4eda11fd49f6309852bb`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-post-pm-lower-state-observer-start-only`
- Helper timeout: `75`
- Property root: `/mnt/sdext/a90/private-property-v317/v2010/dev/__properties__`
- Light firmware trace: `True`
- TFTP-server syscall trace: `True`
- Kept: clean-DSP companion, service managers, `pm-service`, `/dev/subsys_modem` holder, `cnss_diag`, stock `cnss-daemon`, `rmt_storage`, `tftp_server`, `pd-mapper`, firmware mounts, readonly RFS bridge, readwrite tmpfs bridge, cap/BDF/cal probes, and light klog/ICNSS summaries.
- Added: `recvfrom` source `sockaddr`/`sockaddr_len` capture for the stock `tftp_server` trace, to distinguish modem QRTR traffic from local control packets.
- Excluded by construction: boot-time QRTR matrix, rild/cnss/pm-service multi-strace, private SDX50M mount, `/dev/subsys_esoc0` open, eSoC notify/BOOT_DONE, PCI rescan/bind, platform unbind, PMIC/GPIO/GDSC/regulator writes, forced RC1/case, restart-PD request, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping.

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, open `/dev/subsys_esoc0`, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
