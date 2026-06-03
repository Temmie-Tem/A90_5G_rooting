# Native Init V1843 PM-Service Post-Ack Branch Source Build

## Summary

- Cycle: `V1843`
- Type: source/build-only rollbackable PM-service post-ack branch observer test boot artifact
- Decision: `v1843-pm-service-post-ack-branch-source-build-pass`
- Result: PASS
- Reason: helper v355 keeps the V1841 current-route callback/ack observer and adds read-only `pm-service` uprobe hit counts for the `0x63f4` ack implementation body and its post-ack action path toward the devnode open branch.
- Manifest: `tmp/wifi/v1843-pm-service-post-ack-branch-test-boot/manifest.json`
- Boot image: `tmp/wifi/v1843-pm-service-post-ack-branch-test-boot/boot_linux_v1843_pm_service_post_ack_branch.img`
- Boot SHA256: `65b1adf5ba6df53a487437e3b9e366410002d03083461858beccc2cb13dede24`
- Init: `A90 Linux init 0.9.164 (v1843-pm-service-post-ack-branch)`
- Helper marker: `a90_android_execns_probe v355`
- Helper SHA256: `6c44a813472c7a5358ec1e8462f10deee067453d6dbf57414604d0922c1686b0`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-post-pm-lower-state-observer-start-only`
- Property root: `/mnt/sdext/a90/private-property-v317/v1843/dev/__properties__`
- Base route remains the bounded WLAN-PD post-PM lower observer from V1841, including callback/ack hit counters, PMIC/GDSC focus samples, and inherited bounded QRTR/QMI probes.
- Added PM-service post-ack labels: `pm_service_ack_impl_entry`, `pm_service_ack_impl_match_dispatch`, `pm_service_post_ack_action_entry`, `pm_service_post_ack_client_state_store`, `pm_service_post_ack_vote_scan_done`, `pm_service_post_ack_action_branch`, `pm_service_post_ack_timer_settime_call`, `pm_service_post_ack_power_state_load`, `pm_service_post_ack_qmi_restart_ind_call`, `pm_service_post_ack_power_on_open_call`, `pm_service_post_ack_power_on_open_ret`, `pm_service_post_ack_unlock_return`.
- Offsets are read-only tracefs uprobes on the already selected `/vendor/bin/pm-service` target: ack implementation entry/match dispatch, post-ack action entry, client state store, vote scan, action branch, timer/state checks, QMI restart indication branch, devnode open call/return, and unlock/return.
- Explicit limitation: V1843 is a build artifact only; a later rollbackable handoff must confirm which labels actually fire in the current route.
- Still excluded: direct `/dev/subsys_esoc0` open, fake-ONLINE, eSoC notify/BOOT_DONE, PCI rescan/bind, platform unbind, PMIC/GPIO/GDSC writes, `boot_wlan`, restart-PD request, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping.

## Expected Live Discriminator

- `post-ack-open-branch-reached`: `pm_service_post_ack_power_on_open_call` or `_ret` fires; stop and inspect lower state before any Wi-Fi action.
- `post-ack-action-no-open`: ack implementation and post-ack action labels fire, but the devnode open branch stays zero and lower state remains static.
- `post-ack-impl-no-action`: ack implementation entry/match fires, but `pm_service_post_ack_action_entry` stays zero.
- `post-ack-contract-missing`: expected PM-service post-ack labels fail to register or enable.
- `powerup-or-wlfw-progress`: powerup thread, inferred eSoC open, mdm-status IRQ, MHI, WLFW service 69, service74/WLAN-PD UP, or `wlan0` appears; stop before Wi-Fi HAL/scan/connect.
- `safety-regression`: any forbidden side effect appears; stop and roll back.

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, open `/dev/subsys_esoc0`, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
