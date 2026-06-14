# Native Init V2060 DIAG Query-Only Source Build

## Summary

- Cycle: `V2060`
- Type: source/build-only rollbackable internal-modem route with the V2058 PerMgr discriminator plus query-only `/dev/diag` DCI-support probing
- Decision: `v2060-diag-query-only-source-build-pass`
- Result: PASS
- Reason: helper v394 keeps the V2058 readonly/readwrite RFS bridges, TFTP order sink, pre-vote readiness gate, and compact PerMgr summary, and adds only private-node `DIAG_IOCTL_DCI_SUPPORT` queries. It does not call `DIAG_IOCTL_SWITCH_LOGGING`, write to `/dev/diag`, set log/event masks, send QMI, ptrace, or run AP-side strace/QRTR matrices.
- Manifest: `tmp/wifi/v2060-diag-query-only-test-boot/manifest.json`
- Boot image: `tmp/wifi/v2060-diag-query-only-test-boot/boot_linux_v2060_diag_query_only.img`
- Boot SHA256: `6b62d3b1035ecb8a6fe59df736002147cd1b16fd6c658503c09b4632fd5fbcfb`
- Init: `A90 Linux init 0.9.209 (v2060-diag-query-only)`
- Helper marker: `a90_android_execns_probe v394`
- Helper SHA256: `19acfcc77a06083d2e9f26e4b51468af12bc8c3e8782c48367cce2aa3cfcaa8d`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-post-pm-lower-state-observer-start-only`
- Helper timeout: `75`
- Property root: `/mnt/sdext/a90/private-property-v317/v2060/dev/__properties__`
- Light firmware trace: `True`
- Observer: passive private `/dev/socket/logdw`; compact PerMgr register/vote uprobes; query-only private `/dev/diag` DCI-support ioctl probes.
- Kept: clean-DSP companion, service managers, `pm-service`, `/dev/subsys_modem` holder, `cnss_diag`, stock `cnss-daemon`, `rmt_storage`, `tftp_server`, `pd-mapper`, firmware mounts, Android-parity fallback readonly RFS bridge, readwrite tmpfs bridge, persist-RFS tmpfs mirrors, cap/BDF/cal probes, post-cal indication probes, and long lower-window hold.
- Excluded: DIAG logging-mode switch, DIAG writes, DIAG log/event mask writes, passive DIAG replay, boot-time QRTR matrix, rild/cnss/pm-service multi-strace, `tftp_server` ptrace, private SDX50M route, `/dev/subsys_esoc0` open, eSoC notify/BOOT_DONE, PCI rescan/bind, platform unbind, PMIC/GPIO/GDSC/regulator writes, forced RC1/case, restart-PD request, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, and firmware partition writes.

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, open `/dev/subsys_esoc0`, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
