# Native Init V2064 DIAG DCI Canary-Mask Source Build

## Summary

- Cycle: `V2064`
- Type: source/build-only rollbackable internal-modem route with the V2058 PerMgr discriminator plus bounded `/dev/diag` DCI canary-mask set/status/clear probing
- Decision: `v2064-dci-canary-mask-source-build-pass`
- Result: PASS
- Reason: helper v396 keeps the V2058 readonly/readwrite RFS bridges, TFTP order sink, pre-vote readiness gate, compact PerMgr summary, and private-node DCI support/register/read/deinit probe, then adds one bounded DCI data write sequence: set/query/clear/query exactly log code `0x0000` and event id `0`. It does not call `DIAG_IOCTL_SWITCH_LOGGING`, configure DCI streams, set broad masks, send QMI, ptrace, or run AP-side strace/QRTR matrices.
- Manifest: `tmp/wifi/v2064-dci-canary-mask-test-boot/manifest.json`
- Boot image: `tmp/wifi/v2064-dci-canary-mask-test-boot/boot_linux_v2064_dci_canary_mask.img`
- Boot SHA256: `5e029254b9e748f0d7364e9a4069b298c0aafda10926745f5dd33ae25187385b`
- Init: `A90 Linux init 0.9.211 (v2064-dci-canary-mask)`
- Helper marker: `a90_android_execns_probe v396`
- Helper SHA256: `6778988410fe17aced5884569608c08e5a081a1f3da3f590483502551f9ad7ec`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-post-pm-lower-state-observer-start-only`
- Helper timeout: `75`
- Property root: `/mnt/sdext/a90/private-property-v317/v2064/dev/__properties__`
- Light firmware trace: `True`
- Observer: passive private `/dev/socket/logdw`; compact PerMgr register/vote uprobes; private `/dev/diag` DCI support/register/read/deinit plus one canary log/event mask set/status/clear.
- Kept: clean-DSP companion, service managers, `pm-service`, `/dev/subsys_modem` holder, `cnss_diag`, stock `cnss-daemon`, `rmt_storage`, `tftp_server`, `pd-mapper`, firmware mounts, Android-parity fallback readonly RFS bridge, readwrite tmpfs bridge, persist-RFS tmpfs mirrors, cap/BDF/cal probes, post-cal indication probes, and long lower-window hold.
- Excluded: DIAG logging-mode switch, broad DIAG log/event masks, DCI stream config, passive DIAG replay, boot-time QRTR matrix, rild/cnss/pm-service multi-strace, `tftp_server` ptrace, private SDX50M route, `/dev/subsys_esoc0` open, eSoC notify/BOOT_DONE, PCI rescan/bind, platform unbind, PMIC/GPIO/GDSC/regulator writes, forced RC1/case, restart-PD request, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, and firmware partition writes.

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, open `/dev/subsys_esoc0`, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
