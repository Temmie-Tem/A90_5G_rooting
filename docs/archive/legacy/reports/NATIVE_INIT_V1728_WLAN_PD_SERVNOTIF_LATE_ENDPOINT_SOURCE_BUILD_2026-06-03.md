# Native Init V1728 WLAN-PD Service-notifier Late Endpoint Source Build

## Summary

- Cycle: `V1728`
- Type: source/build-only rollbackable WLAN-PD service-notifier late endpoint test boot artifact
- Decision: `v1728-wlan-pd-servnotif-late-endpoint-source-build-pass`
- Result: PASS
- Reason: carries V1727 forward and adds a post-window service-notifier endpoint lookup to distinguish persistent endpoint absence from early-probe timing.
- Manifest: `tmp/wifi/v1728-wlan-pd-servnotif-late-endpoint-test-boot/manifest.json`
- Boot image: `tmp/wifi/v1728-wlan-pd-servnotif-late-endpoint-test-boot/boot_linux_v1728_wlan_pd_servnotif_late_endpoint.img`
- Boot SHA256: `359a399ce1b087809f6b8d74d5d18e8835f6ee3248cbc04c1a3a2ea7023b20d2`
- Init: `A90 Linux init 0.9.137 (v1728-wlan-pd-servnotif-late-endpoint)`
- Helper marker: `a90_android_execns_probe v324`
- Helper SHA256: `4b46166952a7842dd78b56e92434f9a136b847d4439d78d072b5da3fda3fb9a3`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-service-window-trigger-start-only`
- Property root: `/mnt/sdext/a90/private-property-v317/v1728/dev/__properties__`
- Actors: `servicemanager`, `hwservicemanager`, VND service-manager fallback (`/system/bin/servicemanager /dev/vndbinder`), `qrtr-ns`, `pd-mapper`, `rmt_storage`, `tftp_server`, `/dev/subsys_modem` holder, `cnss_diag`, stock `cnss-daemon`.
- Added evidence: `wifi_companion_service_notifier_late_probe.*`, `wlan_pd_cnss_nonlog_control_flow.service_manager=1`, and existing CNSS/WLFW/peripheral uprobes.
- No PM trio, `vendor.qcom.PeripheralManager` actor, `boot_wlan`, `/dev/subsys_esoc0`, forced RC1, fake-ONLINE, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping.

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Live Labels

- `wifi_companion_service_notifier_late_probe.result=endpoint-found` means the service-notifier endpoint appears by the late post-window check.
- `wifi_companion_service_notifier_late_probe.result=no-endpoint` means the endpoint remains absent even after `wlfw_service_request` starts.
- `cnss-target-unavailable` remains non-diagnostic and must not trigger PM trio expansion.

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
