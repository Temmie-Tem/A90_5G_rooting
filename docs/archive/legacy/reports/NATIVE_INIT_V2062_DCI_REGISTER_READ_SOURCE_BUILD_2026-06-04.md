# Native Init V2062 DIAG DCI Register-Read Source Build

## Summary

- Cycle: `V2062`
- Type: source/build-only rollbackable internal-modem route with the V2058 PerMgr discriminator plus private `/dev/diag` DCI register/read probing
- Decision: `v2062-dci-register-read-source-build-pass`
- Result: PASS
- Reason: helper v395 keeps the V2058 readonly/readwrite RFS bridges, TFTP order sink, pre-vote readiness gate, and compact PerMgr summary, and adds private-node `DIAG_IOCTL_DCI_SUPPORT`, `DIAG_IOCTL_DCI_REG`, nonblocking reads, and `DIAG_IOCTL_DCI_DEINIT`. It does not call `DIAG_IOCTL_SWITCH_LOGGING`, write to `/dev/diag`, set log/event masks, configure DCI streams, send QMI, ptrace, or run AP-side strace/QRTR matrices.
- Manifest: `tmp/wifi/v2062-dci-register-read-test-boot/manifest.json`
- Boot image: `tmp/wifi/v2062-dci-register-read-test-boot/boot_linux_v2062_dci_register_read.img`
- Boot SHA256: `6ef0227c5113eeb1f63d4d2abc30363a6ae8e4d03c985c98d27c8f5c1fff5468`
- Init: `A90 Linux init 0.9.210 (v2062-dci-register-read)`
- Helper marker: `a90_android_execns_probe v395`
- Helper SHA256: `d549290545e6252f1da32fac9df06da8b7f66785dcd117ca5a87b65a1509be8a`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-post-pm-lower-state-observer-start-only`
- Helper timeout: `75`
- Property root: `/mnt/sdext/a90/private-property-v317/v2062/dev/__properties__`
- Light firmware trace: `True`
- Observer: passive private `/dev/socket/logdw`; compact PerMgr register/vote uprobes; private `/dev/diag` DCI support/register/read/deinit probe.
- Kept: clean-DSP companion, service managers, `pm-service`, `/dev/subsys_modem` holder, `cnss_diag`, stock `cnss-daemon`, `rmt_storage`, `tftp_server`, `pd-mapper`, firmware mounts, Android-parity fallback readonly RFS bridge, readwrite tmpfs bridge, persist-RFS tmpfs mirrors, cap/BDF/cal probes, post-cal indication probes, and long lower-window hold.
- Excluded: DIAG logging-mode switch, DIAG writes, DIAG log/event mask writes, DCI stream config, passive DIAG replay, boot-time QRTR matrix, rild/cnss/pm-service multi-strace, `tftp_server` ptrace, private SDX50M route, `/dev/subsys_esoc0` open, eSoC notify/BOOT_DONE, PCI rescan/bind, platform unbind, PMIC/GPIO/GDSC/regulator writes, forced RC1/case, restart-PD request, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, and firmware partition writes.

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, open `/dev/subsys_esoc0`, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
