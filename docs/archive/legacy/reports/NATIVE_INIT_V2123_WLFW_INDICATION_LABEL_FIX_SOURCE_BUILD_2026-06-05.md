# Native Init V2123 WLFW Indication Label Fix Source Build

## Summary

- Cycle: `V2123`
- Type: source/build-only observability correction for the post-cal WLFW indication edge.
- Decision: `v2123-wlfw-indication-label-fix-source-build-pass`
- Result: PASS
- Reason: helper v420 keeps the V2120 shared-server-info route unchanged and only corrects the Samsung `cnss-daemon` uprobe labels: `0xe2f0` is MSA-ready (`msg 0x2b`) and `0xe328` is FW-memory-ready (`msg 0x37`).
- Manifest: `tmp/wifi/v2123-wlfw-indication-label-fix-test-boot/manifest.json`
- Boot image: `tmp/wifi/v2123-wlfw-indication-label-fix-test-boot/boot_linux_v2123_wlfw_indication_label_fix.img`
- Boot SHA256: `cd21b1e428e0f645c63328d9c11306580636648311c7926da79cad36837e2906`
- Init: `A90 Linux init 0.9.236 (v2123-wlfw-indication-label-fix)`
- Helper marker: `a90_android_execns_probe v420`
- Helper SHA256: `e5f6a31724a429fd34cc10df3cc9633325a07637b3ac225d2b90db860ae6a3ae`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-post-pm-lower-state-observer-start-only`
- Helper timeout: `75`
- Property root: `/mnt/sdext/a90/private-property-v317/v2123/dev/__properties__`
- Light firmware trace: `True`
- Kept: V2120 dual-RFS read-only/read-write/shared bridges, root lower companions, PerMgr/WLFW focused summaries, post-BDF summary, and long lower-window hold.
- Added: corrected focused fields `saw_msg37`, `msa_ready_flag.hit_count`, and `fw_mem_ready_flag.hit_count`.
- Excluded: route behavior changes, tftp identity changes, OTA ruleset fabrication, mcfg optimization, macloader retry, DIAG, boot-time QRTR matrix, rild/cnss/pm-service strace, `tftp_server` ptrace, AP QMI send, `/dev/subsys_esoc0`, eSoC notify/BOOT_DONE, PCI rescan/bind, platform unbind, PMIC/GPIO/GDSC/regulator writes, forced RC1/case, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, and firmware/partition writes.

## Branch

- If `msg 0x21` appears but kernel FW_READY/`wlan0` does not, classify the gap as userspace FW_READY indication seen but not converted into kernel FW_READY.
- If MSA-ready appears without FW-memory-ready, classify the gap at the MSA-to-FW-memory-ready indication edge.
- If artifact validation fails, do not run the live handoff.

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, run Wi-Fi HAL, scan/connect, use credentials, configure DHCP/routes, perform external ping, write `/dev/wlan`, write `qcwlanstate`, open `/dev/subsys_esoc0`, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, use DIAG, ptrace `tftp_server`, send AP QMI payloads, or write firmware/boot/device partitions.
