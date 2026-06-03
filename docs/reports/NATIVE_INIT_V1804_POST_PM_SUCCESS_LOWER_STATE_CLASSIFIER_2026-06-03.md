# Native Init V1804 Post-PM-success Lower-state Classifier

## Summary

- Cycle: `V1804`
- Type: host-only classifier over V1801/V1803 current evidence and retained Android-positive lower-state evidence
- Decision: `v1804-post-pm-success-mdm3-offlining-before-wlanpd-up-host-pass`
- Result: PASS
- Reason: V1801 repaired PM register/connect and reached MSS ONLINE, but mdm3 stayed OFFLINING and wlan_pd remained uninit while Android-good reaches mdm3 ONLINE, wlan_pd UP, WLFW/BDF, and wlan0
- Evidence: `tmp/wifi/v1804-post-pm-success-lower-state-classifier`

## Current PM Gate

- V1801 decision: `v1801-list-commit-progress-rollback-pass`
- V1803 decision: `v1803-wlan-pd-servnotif-uninit-wlfw-service69-absent-host-pass`
- projection / PM server labels: `list-commit-progress` / `pm-server-register-success-return`
- list commit / PM register success hits: `2` / `1`
- `pm_init_pm_client_register_retcheck` hits/registered/enabled: `1` / `1` / `1`
- `pm_init_pm_client_register_retcheck` first hit: `cnss-daemon-609   [002] ....     6.757752: pm_init_pm_client_register_retcheck: (0x55918c0628)`
- `pm_init_pm_client_connect_retcheck` hits/registered/enabled: `1` / `1` / `1`
- `pm_init_pm_client_connect_retcheck` first hit: `cnss-daemon-609   [002] ....     6.758685: pm_init_pm_client_connect_retcheck: (0x55918c0654)`
- `periph_binder_object_present_check` hits/registered/enabled: `1` / `1` / `1`
- `periph_binder_object_present_check` first hit: `cnss-daemon-609   [002] ....     6.756694: periph_binder_object_present_check: (0x7fbd88820c)`
- `periph_as_interface_call` hits/registered/enabled: `1` / `1` / `1`
- `periph_as_interface_call` first hit: `cnss-daemon-609   [002] ....     6.756698: periph_as_interface_call: (0x7fbd888218)`
- `periph_manager_register_tx_retcheck` hits/registered/enabled: `1` / `1` / `1`
- `periph_manager_register_tx_retcheck` first hit: `cnss-daemon-609   [002] ....     6.757418: periph_manager_register_tx_retcheck: (0x7fbd888278)`
- `periph_success_path` hits/registered/enabled: `1` / `1` / `1`
- `periph_success_path` first hit: `cnss-daemon-609   [002] ....     6.757434: periph_success_path: (0x7fbd888538)`

## Current Lower State

- mss before/after holder: `ONLINE` / `ONLINE`
- mdm3 before/after holder: `OFFLINING` / `OFFLINING`
- rpmsg count/ipcrtr: `7` / `1`
- MHI pipe fd count: `0`
- service-notifier state/indication: `uninit` / `0`
- WLFW service69 QRTR case events: `0` / `0`
- requested `wlanmdsp` / summary service69 / wlan0: `0` / `0` / `0`

## Android-positive Baseline

- V739 decision: `v739-mdm3-online-delta-active-blocker`
- V739 Android mss/mdm3: `ONLINE` / `ONLINE`
- V739 Android service-notifier 180/74, wlan_pd, wlan0, QMI connected: `1` / `1` / `2` / `3` / `1`
- V852 decision: `v852-android-mdm3-online-provider-surface-captured`
- V852 Android mss/mdm3: `ONLINE` / `ONLINE`
- V852 hints wlan_pd/WLFW/BDF/wlan0: `True` / `True` / `True` / `True`
- V852 surface raw_esoc/esoc0_sysfs/mdm3_sysfs/subsys9: `True` / `True` / `True` / `True`
- V852 timeline esoc0_get/wlan_pd_up/ack/BDF_events/wlan0_events: `True` / `True` / `True` / `2` / `2`

## Interpretation

- V1801/V1803 close the previous PM service-object/register/connect blocker enough to treat PM client voting as reached.
- The current native stall is now below that PM vote boundary: MSS is online and rpmsg/IPCRTR exists, but mdm3 remains `OFFLINING`; wlan_pd service-notifier remains `uninit`, WLFW service 69 is absent, and no firmware request or `wlan0` follows.
- Android-positive evidence on the same stock kernel reaches mdm3 `ONLINE`, wlan_pd UP/ACK, WLFW/BDF, and `wlan0`; this makes the active blocker a safe mdm3/ext-sdx50m continuation discriminator, not Wi-Fi HAL, credentials, DHCP, or external ping.
- The next unit should classify PM-service-owned lower continuation around modem vote to mdm3/ext-sdx50m state without direct `/dev/subsys_esoc0` open, fake-ONLINE, eSoC notify, PCI rescan/bind, platform unbind, or PMIC/GPIO/GDSC writes.

## Safety Scope

Host-only. This classifier did not issue live device commands, flash, reboot, stage properties, open `/dev/subsys_esoc0`, start `boot_wlan`, issue restart-PD request, start Wi-Fi HAL, scan/connect, use credentials, configure DHCP/routes, or external ping.
