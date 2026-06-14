# Native Init V1995 PD-Mapper Syscall Trace Source Build

## Summary

- Cycle: `V1995`
- Type: source/build-only rollbackable internal-modem pd-mapper producer observer
- Decision: `v1995-pd-mapper-syscall-trace-source-build-pass`
- Result: PASS
- Reason: helper v367 keeps the V1991/V1993 RFS-bridge light route and adds an opt-in late-attach single-child ptrace payload trace for stock `pd-mapper` only.
- Manifest: `tmp/wifi/v1995-pd-mapper-syscall-trace-test-boot/manifest.json`
- Boot image: `tmp/wifi/v1995-pd-mapper-syscall-trace-test-boot/boot_linux_v1995_pd_mapper_syscall_trace.img`
- Boot SHA256: `2c343be7f4213a6d9d4d612670b98269686b25442719e3fadfaa0b2760ecd016`
- Init: `A90 Linux init 0.9.180 (v1995-pd-mapper-syscall-trace)`
- Helper marker: `a90_android_execns_probe v367`
- Helper SHA256: `2295b070e422a1b917d1588dcbfe2d6217d9df994d1e99799c1b875a616d4901`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-post-pm-lower-state-observer-start-only`
- Property root: `/mnt/sdext/a90/private-property-v317/v1995/dev/__properties__`
- Light firmware trace: `True`
- PD-mapper syscall trace: `True`
- Kept: clean-DSP companion, service managers, `pm-service`, `/dev/subsys_modem` holder, `cnss_diag`, stock `cnss-daemon`, `rmt_storage`, `tftp_server`, `pd-mapper`, firmware mounts, RFS bridge, and klog lower-window summaries.
- Added: late-attach single-child ptrace of already-running `pd-mapper` `sendmsg`/`recvmsg`/`sendto`/`recvfrom` payloads, bounded to answer whether the modem queries PD mapping before the missing `wlanmdsp.mbn` request.
- Still excluded from init argv: rild/cnss/pm-service strace, boot-time QRTR matrix, service-locator probe, service-notifier listener, active QRTR send/readback, and QMI payload send.
- Live discriminator: no pd-mapper QRTR payload before no-request, pd-mapper query seen but no tftp request, or query plus wlanmdsp request/load progress.
- Excluded by construction: private SDX50M mount, `/dev/subsys_esoc0` open, eSoC notify/BOOT_DONE, PCI rescan/bind, platform unbind, PMIC/GPIO/GDSC/regulator writes, forced RC1/case, restart-PD request, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping.

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, open `/dev/subsys_esoc0`, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
