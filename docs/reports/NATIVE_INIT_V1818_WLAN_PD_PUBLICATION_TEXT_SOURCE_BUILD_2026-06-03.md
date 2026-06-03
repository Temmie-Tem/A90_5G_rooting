# Native Init V1818 WLAN-PD Publication Text Source Build

## Summary

- Cycle: `V1818`
- Type: source/build-only rollbackable WLAN-PD publication text observer test boot artifact
- Decision: `v1818-wlan-pd-publication-text-source-build-pass`
- Result: PASS
- Reason: helper v347 keeps the V1815/V1816 lower observer and adds read-only service-locator/domain-QMI publication text counters for the missing wlan_pd/service74 path.
- Manifest: `tmp/wifi/v1818-wlan-pd-publication-text-test-boot/manifest.json`
- Boot image: `tmp/wifi/v1818-wlan-pd-publication-text-test-boot/boot_linux_v1818_wlan_pd_publication_text.img`
- Boot SHA256: `3111b96ef2424ca47a00d4d75693ff0fcf8c5e29336b805dce736ea7fe5e82c6`
- Init: `A90 Linux init 0.9.156 (v1818-wlan-pd-publication-text)`
- Helper marker: `a90_android_execns_probe v347`
- Helper SHA256: `aa5d63de8a697082f0bf8cd5ffdc0117aab2d91046fe7822ff0de6b3a51c5c33`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-post-pm-lower-state-observer-start-only`
- Property root: `/mnt/sdext/a90/private-property-v317/v1818/dev/__properties__`
- Base route remains the V1815 bounded lower handoff observer: PM-client return fetchargs, lower-state samples, service-notifier listener state, raw service-notifier 180/74 samples, and lower precondition klog samples.
- Added publication counters: `raw_count_service_locator_text`, `raw_count_servloc_domain_text`, `raw_count_wlan_fw_text`, `raw_count_wlan_pd_domain_text`, and `raw_count_qmi_server_connected_text`.
- Added last-line fields: `last_service_locator`, `last_servloc_domain`, `last_wlan_fw`, `last_wlan_pd_domain`, and `last_qmi_server_connected`.
- Still excluded: direct `/dev/subsys_esoc0` open, fake-ONLINE, eSoC notify/BOOT_DONE, PCI rescan/bind, platform unbind, PMIC/GPIO/GDSC writes, `boot_wlan`, restart-PD request, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping.

## Expected Live Discriminator

- V1819 should run one rollbackable live gate with this artifact and classify whether service-locator/domain-QMI publication text appears before service 74/wlan_pd remain absent.
- `publication-text-absent-with-qmi-context`: qmi/sysmon/subsys/PIL context remains visible, but service-locator/domain-QMI/wlan_pd publication text remains absent.
- `publication-text-parser-gap`: broad text appears without useful fixed last-line attribution.
- `lower-publication-progress`: service 74, wlan_pd, WLFW service 69, MHI, or `wlan0` appears; stop before Wi-Fi HAL/scan/connect.
- `safety-regression`: any forbidden side effect appears; stop and roll back.

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, open `/dev/subsys_esoc0`, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
