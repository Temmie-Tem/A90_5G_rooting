# Native Init V1805 Post-PM Lower-state Observer Source Build

## Summary

- Cycle: `V1805`
- Type: source/build-only rollbackable WLAN-PD post-PM lower-state observer test boot artifact
- Decision: `v1805-post-pm-lower-state-observer-source-build-pass`
- Result: PASS
- Reason: helper v342 keeps the V1800 private-dev PM-service projection route and adds a compact no-write lower-state sampler after the PM vote boundary.
- Manifest: `tmp/wifi/v1805-post-pm-lower-state-observer-test-boot/manifest.json`
- Boot image: `tmp/wifi/v1805-post-pm-lower-state-observer-test-boot/boot_linux_v1805_post_pm_lower_state_observer.img`
- Boot SHA256: `27a70ec712913b8ade7b4b7fd683871c9ee276116207c52bc59ac8ad2a00b74d`
- Init: `A90 Linux init 0.9.151 (v1805-post-pm-lower-state-observer)`
- Helper marker: `a90_android_execns_probe v342`
- Helper SHA256: `387a7df01f5dd93bf2fe3e1dfc10fe93c5c3c0900c530bc3eaaa5a4dd471a995`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-post-pm-lower-state-observer-start-only`
- Property root: `/mnt/sdext/a90/private-property-v317/v1805/dev/__properties__`
- Base route remains the V1800 bounded service-object route: service managers, firmware-serve stack, `pm_proxy_helper`, `pm-service`, `/dev/subsys_modem` holder, `cnss_diag`, and stock `cnss-daemon`.
- Retained projection: private Android `/dev` receives only `subsys_esoc0` and `subsys_modem` char nodes from sysfs major/minor metadata before `pm-service` starts; the runner still does not open `/dev/subsys_esoc0`.
- Added observer: `wlan_pd_post_pm_lower_state_observer.after_holder_start.*` captures an immediate compact read-only lower-state sample.
- Added observer window: `wlan_pd_post_pm_lower_state_observer.post_listener_window.*` captures 12 samples at 500 ms spacing after the bounded service-notifier listener path.
- Captured fields are read-only: mss/mdm3 states and crash counts, mdm status/errfatal IRQ totals, PCI/MHI/rpmsg/msm_subsys counts, MHI pipe presence, and `wlan0` presence.
- Still excluded: `esoc-0` projection, `/dev/subsys_esoc0` open, forced RC1, fake-ONLINE, full `pm-proxy`, `boot_wlan`, restart-PD request, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, and PMIC/GPIO/GDSC writes.

## Expected Live Discriminator

- V1806 should run one rollbackable live gate with this artifact and classify whether post-PM lower-state sampling shows mdm3 or IRQ/MHI progress after PM client connect, or confirms a stable `mdm3=OFFLINING` stall.
- `lower-progress`: mdm3 leaves `OFFLINING`, mdm status IRQ increases, MHI appears, WLFW service 69 appears, or `wlan0` appears; stop before Wi-Fi HAL/scan/connect.
- `stable-mdm3-offlining`: PM register/connect still succeeds but all compact samples keep mdm3 `OFFLINING`, MHI absent, WLFW service 69 absent, and `wlan0` absent; route next to host/source classification of the PM-service-owned lower continuation.
- `safety-regression`: any hard-stop field regresses; roll back and stop.

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, open `/dev/subsys_esoc0`, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
