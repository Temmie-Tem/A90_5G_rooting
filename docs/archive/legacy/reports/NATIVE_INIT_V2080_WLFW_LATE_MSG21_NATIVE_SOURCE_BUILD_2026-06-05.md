# Native Init V2080 WLFW Late Msg21 Native Source Build

## Summary

- Cycle: `V2080`
- Type: source/build-only no-DIAG native route with compact WLFW late `msg_id=0x21` summary emitted before verbose trace output truncation
- Decision: `v2080-wlfw-late-msg21-native-source-build-pass`
- Result: PASS
- Reason: helper v403 keeps the V2058 light internal-modem route and adds only a compact `wlfw_late_msg21_focused` summary over existing cnss-daemon tracefs uprobes; no DIAG, strace, QRTR matrix, QMI send, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping.
- Manifest: `tmp/wifi/v2080-wlfw-late-msg21-native-test-boot/manifest.json`
- Boot image: `tmp/wifi/v2080-wlfw-late-msg21-native-test-boot/boot_linux_v2080_wlfw_late_msg21_native.img`
- Boot SHA256: `99a6449fdfea93372def677b74cf1e2c8fd48a26e2980406083456c016ba83d1`
- Init: `A90 Linux init 0.9.218 (v2080-wlfw-late-msg21-native)`
- Helper marker: `a90_android_execns_probe v403`
- Helper SHA256: `2f6a3fab0842282a7f1f5a76ef55be25d1413ee89daf0adc0cf79bf4204cd034`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-post-pm-lower-state-observer-start-only`
- Helper timeout: `75`
- Property root: `/mnt/sdext/a90/private-property-v317/v2080/dev/__properties__`
- Light firmware trace: `True`
- Kept: clean-DSP companion, service managers, `pm-service`, `/dev/subsys_modem` holder, `cnss_diag`, stock `cnss-daemon`, `rmt_storage`, `tftp_server`, `pd-mapper`, Android-parity RFS bridges, cap/BDF/cal probes, post-cal WLFW indication probes, PerMgr compact summary, and long lower-window hold.
- Excluded: DIAG ioctl/write/log-mask, passive DIAG, active DIAG, boot-time QRTR matrix, rild/cnss/pm-service strace, `tftp_server` ptrace, private SDX50M route, `/dev/subsys_esoc0` open, eSoC notify/BOOT_DONE, PCI rescan/bind, platform unbind, PMIC/GPIO/GDSC/regulator writes, forced RC1/case, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, and firmware partition writes.

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, open `/dev/subsys_esoc0`, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
