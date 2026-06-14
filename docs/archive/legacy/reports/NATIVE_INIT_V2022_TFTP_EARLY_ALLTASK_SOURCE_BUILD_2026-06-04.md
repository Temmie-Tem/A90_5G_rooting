# Native Init V2022 TFTP Early All-Task Source Build

## Summary

- Cycle: `V2022`
- Type: source/build-only rollbackable internal-modem early TFTP discriminator
- Decision: `v2022-tftp-early-alltask-source-build-pass`
- Result: PASS
- Reason: helper v380 keeps the full consumer chain and moves the bounded all-task `tftp_server` trace to the immediate post-`/dev/subsys_modem` holder edge, before the observer snapshots that missed the initial `server_check` / `ota_firewall` / `wlanmdsp` branch in V2021.
- Manifest: `tmp/wifi/v2022-tftp-early-alltask-test-boot/manifest.json`
- Boot image: `tmp/wifi/v2022-tftp-early-alltask-test-boot/boot_linux_v2022_tftp_early_alltask.img`
- Boot SHA256: `cf4dc6f0ebcd220b6519be723daebe858c410bd21387fa7101c5e73fe6e6ec95`
- Init: `A90 Linux init 0.9.193 (v2022-tftp-early-alltask)`
- Helper marker: `a90_android_execns_probe v380`
- Helper SHA256: `c903a2453ed04a4400511b44aa2dfa388b4f69c1b87611c5910c39810d2f0727`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-post-pm-lower-state-observer-start-only`
- Helper timeout: `75`
- Property root: `/mnt/sdext/a90/private-property-v317/v2022/dev/__properties__`
- Light firmware trace: `True`
- TFTP-server syscall trace: `True`
- TFTP trace contract: all current and newly discovered `tftp_server` tasks, compact RRQ/WRQ/DATA/ACK/ERROR packet records plus focused filesystem results, immediate post-holder attach, timeout `45000ms`, record limit `4096`, stop limit `50000`, max tasks `32`, no QRTR send, no QMI payload send.
- Kept: clean-DSP companion, service managers, `pm-service`, `/dev/subsys_modem` holder, `cnss_diag`, stock `cnss-daemon`, `rmt_storage`, `tftp_server`, `pd-mapper`, firmware mounts, readonly RFS bridge, readwrite tmpfs bridge, cap/BDF/cal probes, indication probes, and light klog/ICNSS summaries.
- Excluded: boot-time QRTR matrix, rild/cnss/pm-service multi-strace, private SDX50M route, `/dev/subsys_esoc0` open, eSoC notify/BOOT_DONE, PCI rescan/bind, platform unbind, PMIC/GPIO/GDSC/regulator writes, forced RC1/case, restart-PD request, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping.

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, open `/dev/subsys_esoc0`, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
