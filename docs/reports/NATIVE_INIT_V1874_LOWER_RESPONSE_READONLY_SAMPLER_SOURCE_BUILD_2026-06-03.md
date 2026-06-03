# Native Init V1874 Lower Response Read-only Sampler Source Build

## Summary

- Cycle: `V1874`
- Type: source/build-only rollbackable v357 lower-response input sampler on the private SDX50M post-PM route
- Decision: `v1874-lower-response-readonly-sampler-source-build-pass`
- Result: PASS
- Reason: V1873 selected the next source/build-only contract: extend the private SDX50M post-PM lower observer with a dense read-only lower-response input window before any new mutation or Wi-Fi connect attempt.
- Manifest: `tmp/wifi/v1874-lower-response-readonly-sampler-test-boot/manifest.json`
- Boot image: `tmp/wifi/v1874-lower-response-readonly-sampler-test-boot/boot_linux_v1874_lower_response_readonly_sampler.img`
- Boot SHA256: `9f79cdf9b9dfaac1ac512fc04f712a352f0afb40e1bb0438303c9a4cb8171f5e`
- Init: `A90 Linux init 0.9.170 (v1874-lower-response-readonly-sampler)`
- Helper marker: `a90_android_execns_probe v357`
- Helper SHA256: `8ec9d4153e5dcc966888170bfef0c3428f2261b30c0e58836697c91442386d87`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-post-pm-lower-state-observer-start-only`
- Property root: `/mnt/sdext/a90/private-property-v317/v1874/dev/__properties__`
- Private CNSS mount: `True` path `/cache/bin/cnss-daemon.sdx50m`
- New helper marker: `a90_android_execns_probe v357`.
- New output namespace: `wlan_pd_lower_response_input_contract.post_powerup_dense.*`.
- Dense offsets: `0,1,2,5,10,20,50,100,150,250,500,1000 ms`.
- Each sample reuses existing read-only lower-state and PM/eSoC/GPIO/GDSC/PCIe/MHI/ks surfaces; it does not write rc_sel/case, rescan PCI, bind/unbind, or directly open `/dev/subsys_esoc0`.
- PM-service open-context labels retained: `pm_service_post_ack_power_state_loaded`, `pm_service_post_ack_open_context`, `pm_service_post_ack_open_path_loaded`, `pm_service_post_ack_open_fd_store`, `pm_service_post_ack_open_fd_compare`, `pm_service_post_ack_open_success_counter`.

## Expected Live Discriminator

- `lower-input-mdm2ap-silent`: private SDX50M path selected, but GPIO142/MDM2AP and PCIe/MHI/WLFW stay silent.
- `lower-input-rc1-natural-attempt-no-l0`: natural PCIe/RC1 state changes appear but no L0/MHI/WLFW publication follows.
- `lower-input-power-clock-snapshot-gap`: pcie1 GDSC/clock/regulator read-only samples stay different from Android-good evidence.
- `lower-input-mhi-or-wlfw-progress-readonly-stop`: MHI, WLFW service 69, BDF, firmware-ready, or `wlan0` appears; stop before connect.
- `lower-input-wifi-prereq-present-readonly-stop`: WLFW service 69 and `wlan0` both exist; only then plan Wi-Fi HAL/connect.

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, open `/dev/subsys_esoc0`, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
