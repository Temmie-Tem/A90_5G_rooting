# Native Init V1837 WLAN-PD Lower-Continuation Sampler Source Build

## Summary

- Cycle: `V1837`
- Type: source/build-only rollbackable WLAN-PD lower-continuation sampler test boot artifact
- Decision: `v1837-wlan-pd-lower-continuation-sampler-source-build-pass`
- Result: PASS
- Reason: helper v353 keeps the V1834/V1835 bounded lower route and adds read-only PMIC/GDSC focus samples inside the same WLAN-PD post-PM lower observer path.
- Manifest: `tmp/wifi/v1837-wlan-pd-lower-continuation-sampler-test-boot/manifest.json`
- Boot image: `tmp/wifi/v1837-wlan-pd-lower-continuation-sampler-test-boot/boot_linux_v1837_wlan_pd_lower_continuation_sampler.img`
- Boot SHA256: `cb27f0adb43822f0a5ddc0b21ede63f9e7ecd237e87b28895fda54e71add1dc1`
- Init: `A90 Linux init 0.9.162 (v1837-wlan-pd-lower-continuation-sampler)`
- Helper marker: `a90_android_execns_probe v353`
- Helper SHA256: `eb8d827062d861f4096de86b0b4530241cc6e84c19cdf087cfae34b2b484fd0d`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-post-pm-lower-state-observer-start-only`
- Property root: `/mnt/sdext/a90/private-property-v317/v1837/dev/__properties__`
- Base route remains the bounded lower handoff observer and retains the unbound, node-zero bind, observed-local-node bind, and bound passive poll/recv QRTR snapshots.
- Added read-only PMIC/GDSC focus sample prefixes: `pm_service_trigger_observer.response_sample.wlan_pd_after_holder_start.*` and `pm_service_trigger_observer.response_sample.wlan_pd_after_post_listener_window.*`.
- These samples reuse the existing PMIC/GDSC transition observer surface only as a no-write lower-state sampler for mdm3/ext-SDX50M prerequisites, GPIO 135/142 target-line state, PMIC soft-reset line state, PCIe/GDSC state, MHI presence, and `wlan0` presence.
- Explicit non-actions in the reused sample: `gpiochip_line_request_executed=0`, `pmic_write_executed=0`, and `esoc_ioctl_executed=0`.
- Still excluded: direct `/dev/subsys_esoc0` open, fake-ONLINE, eSoC notify/BOOT_DONE, PCI rescan/bind, platform unbind, PMIC/GPIO/GDSC writes, `boot_wlan`, restart-PD request, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping.

## Expected Live Discriminator

- V1838 should run one rollbackable live gate with this artifact only if the read-only lower-continuation sampler is accepted as the next bounded surface.
- `lower-continuation-static-gap`: mdm3/ext-SDX50M, PMIC/GDSC, MHI, WLFW/service 69, and `wlan0` remain unchanged from V1834/V1836; stop and classify the remaining prerequisite gap.
- `pmic-gdsc-or-mdm-status-progress`: one of the PMIC/GDSC, mdm3, IRQ, or PCIe prerequisite surfaces changes during the guarded holder/listener windows; stop and classify the transition.
- `mhi-wlfw-wlan0-progress`: MHI, WLFW service 69, `wlan0`, WLAN-PD UP, or service 74 appears; stop before Wi-Fi HAL/scan/connect.
- `safety-regression`: any forbidden side effect appears; stop and roll back.

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, open `/dev/subsys_esoc0`, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
