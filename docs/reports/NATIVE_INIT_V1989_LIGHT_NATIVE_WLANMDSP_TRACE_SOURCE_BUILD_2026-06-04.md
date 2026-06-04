# Native Init V1989 Light Native Wlanmdsp Trace Source Build

## Summary

- Cycle: `V1989`
- Type: source/build-only rollbackable internal-modem light `wlanmdsp.mbn` request/load trace artifact
- Decision: `v1989-light-native-wlanmdsp-trace-source-build-pass`
- Result: PASS
- Reason: V1979/V1982 exhausted AP-side producer differences; this artifact keeps the current native PM/CNSS/tftp route but removes boot-time QRTR readback matrix, service-locator probing, and service-notifier listener probing so the next live run observes only the native firmware-request edge.
- Manifest: `tmp/wifi/v1989-light-native-wlanmdsp-trace-test-boot/manifest.json`
- Boot image: `tmp/wifi/v1989-light-native-wlanmdsp-trace-test-boot/boot_linux_v1989_light_native_wlanmdsp_trace.img`
- Boot SHA256: `7940c9f2042b8360791e955adfbe0f71aad1c7897e34c7a729aea84d50e84cd5`
- Init: `A90 Linux init 0.9.177 (v1989-light-native-wlanmdsp-trace)`
- Helper marker: `a90_android_execns_probe v363`
- Helper SHA256: `90b98eff707bb69744f9bc9824424d13651aed26380a1aa71d02936434fbb8da`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-post-pm-lower-state-observer-start-only`
- Property root: `/mnt/sdext/a90/private-property-v317/v1989/dev/__properties__`
- Light firmware trace: `True`
- Kept: clean-DSP companion, service managers, `pm-service`, `/dev/subsys_modem` holder, `cnss_diag`, stock `cnss-daemon`, `rmt_storage`, `tftp_server`, firmware mounts, klog lower-window summaries, and libqmi/ICNSS read-only uprobes already present in helper v363.
- Removed from init argv by contract: `--allow-qrtr-ns-readback`, `--allow-servloc-domain-list-probe`, `--allow-service-notifier-listener-probe`, and `--qrtr-readback-matrix wlfw:69:0,1`.
- Live discriminator: whether native requests `wlanmdsp.mbn`, serves it, and reaches modem PIL/PD-load markers without boot-time QRTR matrix or multi-strace observer perturbation.
- Stop condition: `wlanmdsp.mbn` request/serve/load, WLAN-PD UP, WLFW 69, BDF, or `wlan0`; do not proceed to Wi-Fi HAL/scan/connect.
- Excluded by construction: private SDX50M mount, `/dev/subsys_esoc0` open, eSoC notify/BOOT_DONE, PCI rescan/bind, platform unbind, PMIC/GPIO/GDSC/regulator writes, forced RC1/case, restart-PD request, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping.

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, open `/dev/subsys_esoc0`, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
