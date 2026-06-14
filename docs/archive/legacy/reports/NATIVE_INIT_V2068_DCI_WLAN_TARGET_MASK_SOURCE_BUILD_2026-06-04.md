# Native Init V2068 DIAG DCI WLAN Target-Mask Source Build

## Summary

- Cycle: `V2068`
- Type: source/build-only rollbackable internal-modem route with V2059 PerMgr success retained and bounded `/dev/diag` DCI WLAN log/event target masks
- Decision: `v2068-dci-wlan-target-mask-source-build-pass`
- Result: PASS
- Reason: helper v398 keeps the V2058 readonly/readwrite RFS bridges, TFTP order sink, pre-vote readiness gate, compact PerMgr summary, and private-node DCI support/register/read/deinit probe, then arms exactly three WLAN log codes and three WLAN event IDs through the lower window and clears them during cleanup. It does not call `DIAG_IOCTL_SWITCH_LOGGING`, configure DCI streams, set broad masks, send QMI, ptrace, or run AP-side strace/QRTR matrices.
- Manifest: `tmp/wifi/v2068-dci-wlan-target-mask-test-boot/manifest.json`
- Boot image: `tmp/wifi/v2068-dci-wlan-target-mask-test-boot/boot_linux_v2068_dci_wlan_target_mask.img`
- Boot SHA256: `cd5b6d1a555c9bf2597d70d813e008c947d92cc156e920df2b8a23adaca586af`
- Init: `A90 Linux init 0.9.213 (v2068-dci-wlan-target-mask)`
- Helper marker: `a90_android_execns_probe v398`
- Helper SHA256: `cb62d077c41c9e0fdd63f83609f3cd549fa234cc74d136bcf57608b3509fee96`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-post-pm-lower-state-observer-start-only`
- Helper timeout: `75`
- Property root: `/mnt/sdext/a90/private-property-v317/v2068/dev/__properties__`
- Light firmware trace: `True`
- Observer: passive private `/dev/socket/logdw`; compact PerMgr register/vote uprobes; private `/dev/diag` DCI support/register/read/deinit plus bounded WLAN target log/event masks held until cleanup.
- Target logs: `LOG_WLAN_PKT_LOG_INFO_C` (`0x18e0`), `LOG_WLAN_COLD_BOOT_CAL_DATA_C` (`0x1a18`), `LOG_WLAN_DP_PROTO_PKT_INFO_C` (`0x1a1e`).
- Target events: `EVENT_WLAN_BRINGUP_STATUS` (`0x0680`), `EVENT_WLAN_LOG_COMPLETE` (`0x0aa7`), `EVENT_WLAN_STATUS_V2` (`0x0ab3`).
- Kept: clean-DSP companion, service managers, `pm-service`, `/dev/subsys_modem` holder, `cnss_diag`, stock `cnss-daemon`, `rmt_storage`, `tftp_server`, `pd-mapper`, firmware mounts, Android-parity fallback readonly RFS bridge, readwrite tmpfs bridge, persist-RFS tmpfs mirrors, cap/BDF/cal probes, post-cal indication probes, and long lower-window hold.
- Excluded: DIAG logging-mode switch, broad DIAG log/event masks, DCI stream config, passive DIAG replay, boot-time QRTR matrix, rild/cnss/pm-service multi-strace, `tftp_server` ptrace, private SDX50M route, `/dev/subsys_esoc0` open, eSoC notify/BOOT_DONE, PCI rescan/bind, platform unbind, PMIC/GPIO/GDSC/regulator writes, forced RC1/case, restart-PD request, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, and firmware partition writes.

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, open `/dev/subsys_esoc0`, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
