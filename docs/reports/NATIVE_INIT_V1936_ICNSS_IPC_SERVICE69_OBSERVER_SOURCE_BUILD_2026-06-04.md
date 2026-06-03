# Native Init V1936 ICNSS IPC Service69 Observer Source Build

## Summary

- Cycle: `V1936`
- Type: source/build-only rollbackable internal-modem ICNSS IPC/WLFW-server-arrive observer test boot artifact
- Decision: `v1936-icnss-ipc-service69-observer-source-build-pass`
- Result: PASS
- Reason: V1935 localized the native stall to the WLFW service69 wait-return edge; helper v363 keeps the V1929 libqmi service-ID route and adds read-only ICNSS IPC/debugfs summaries at the post-PM phases.
- Manifest: `tmp/wifi/v1936-icnss-ipc-service69-observer-test-boot/manifest.json`
- Boot image: `tmp/wifi/v1936-icnss-ipc-service69-observer-test-boot/boot_linux_v1936_icnss_ipc_service69_observer.img`
- Boot SHA256: `7595fc32567a8f1cbd6945a85058eea7e1df454723a1b9c9684b108f380fabcb`
- Init: `A90 Linux init 0.9.176 (v1936-icnss-ipc-service69-observer)`
- Helper marker: `a90_android_execns_probe v363`
- Helper SHA256: `90b98eff707bb69744f9bc9824424d13651aed26380a1aa71d02936434fbb8da`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-post-pm-lower-state-observer-start-only`
- Property root: `/mnt/sdext/a90/private-property-v317/v1936/dev/__properties__`
- Base route remains the bounded internal-modem post-PM lower observer: clean-DSP companion, service managers, `pm-service`, `/dev/subsys_modem` holder, `cnss_diag`, stock `cnss-daemon`, service-locator/domain-list, service-notifier listener, WLFW QRTR readback, and libqmi service-ID uprobes.
- Added read-only prefix: `wlan_pd_icnss_ipc_snapshot.<phase>.*` for `/sys/kernel/debug/ipc_logging`, `/proc/ipc_logging`, and `/sys/kernel/debug/icnss/stats` at `after_holder_start`, `after_early_listener`, and `after_post_listener_window`.
- The new discriminator checks for Android-good comparator edges: `Get service notify`, `msm/modem/wlan_pd`, `PD notification registration happened`, and `WLFW server arrive` before WLFW service69 wait return.
- Stop condition: WLFW service 69, `wlan_pd`, requested `wlanmdsp`, `wlfw_ind_register_qmi`, `wlfw_cap_qmi`, or `wlan0` appears; do not proceed to HAL/scan/connect in this unit.
- Excluded by construction: private SDX50M mount, `/dev/subsys_esoc0` open, eSoC notify/BOOT_DONE, PCI rescan/bind, platform unbind, PMIC/GPIO/GDSC/regulator writes, forced RC1/case, restart-PD request, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping.

## Expected Live Discriminator

- `native-icnss-ipc-wlfw-server-arrive-gap`: native reproduces service74/180, PM open, holder, WLFW lookup69, and libqmi wait, but ICNSS IPC/debugfs has no `WLFW server arrive` and service69 wait does not return.
- `native-icnss-ipc-pd-registration-no-wlfw-arrive`: native records `msm/modem/wlan_pd` or PD notification registration but never records `WLFW server arrive`; focus next on the post-registration modem-to-WLFW publication edge.
- `native-icnss-ipc-unreadable`: debugfs IPC and ICNSS stats are absent/unreadable in the rollbackable test boot; fall back to userland libqmi/servnotif-only observers.
- `lower-publication-progress`: service69, WLAN-PD, `wlanmdsp`, WLFW QMI, or `wlan0` appears; stop before Wi-Fi HAL/scan/connect and classify the new downstream state.

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, open `/dev/subsys_esoc0`, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
