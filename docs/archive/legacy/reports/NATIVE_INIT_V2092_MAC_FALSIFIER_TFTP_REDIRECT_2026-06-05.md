# Native Init V2092 MAC Falsifier / TFTP Redirect

## Summary

- Cycle: `V2092`
- Type: host-only classifier over committed rollback-verified evidence; no new boot or device mutation.
- Decision: `v2092-mac-no-write-tftp-producer-gate-retained-host-pass`
- Label: `mac-no-write-tftp-producer-gate-retained`
- Pass: `True`
- Reason: real sysfs was present and macloader was traced, but it never read .mac.info or wrote /sys/wifi/mac_addr; current AP-side route still reproduces PerMgr/WLFW publication while tftp has no server_check or wlanmdsp
- Evidence: `tmp/wifi/v2092-mac-falsifier-tftp-redirect`

## MAC Boundary

| field | value |
| --- | --- |
| real_sysfs_mac_addr | True |
| mac_addr_fs_type | 0x0000000062656572 |
| mac_addr_mode | 0220 |
| mac_info_readable_bytes | 17 |
| macloader_runtime_traced | 1 |
| macloader_records_seen | 14 |
| mac_info_read | False |
| mac_addr_open | False |
| mac_addr_write | False |
| mac_addr_write_shape | False |
| kernel_assign_line | False |
| property_shim_started | 1 |
| property_shim_requests | missing |
| property_shim_macloader_ack_count | 0 |

## Route Matrix

| run | label | rollback | per_mgr | cap_bdf_cal | msg21 | wlan_pd | icnss_qmi | server_check | mcfg | wlanmdsp | fw_ready | wlan0 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V2091 | macloader-no-mac-addr-write | True | True | False | True | 1 | 1 | 0 | 6 | 0 | 0 | 0 |
| V2083 | icnss-qcacld-no-wlanmdsp-request | True | True | True | True | 1 | 1 | 0 | 5 | 0 | 0 | 0 |
| V2081 | wlfw-late-msg21-native-msg21-no-fw-ready | True | True | True | True | 1 | 1 | 0 | 3 | 0 | 0 | 0 |
| V2059 | cnss-permgr-register-vote-success-no-wlanmdsp | True | True | True | False | 1 | 1 | 0 | 11 | 0 | 0 | 0 |

## Interpretation

- V2091 satisfies the requested quick falsifier: `/sys/wifi/mac_addr` was the real writable sysfs node, but `macloader` never read `.mac.info`, opened/wrote `mac_addr`, produced a colon/hex MAC write, or triggered the kernel `Assigning MAC from Macloader` line.
- That closes additional MAC plumbing as a low-value branch for the producer gate; a successful later MAC assignment would still be downstream of FW-ready/netdev creation, not evidence that the modem selected the WLAN image-request branch.
- Current committed native evidence already reproduces the AP-side PerMgr/WLFW path and reaches `wlan_pd`/`icnss_qmi`, while stock `tftp_server` logs remain `server_check=0` and `wlanmdsp=0` in the latest no-ptrace route.
- The next target remains the modem-internal TFTP producer branch: why native selects late `mcfg` traffic instead of Android's `server_check.txt -> ota_firewall/ruleset -> wlanmdsp.mbn` branch.

## Inputs

| key | path |
| --- | --- |
| v2091 | tmp/wifi/v2091-macloader-property-service-handoff/manifest.json |
| v2083 | tmp/wifi/v2083-icnss-qcacld-post-bdf-handoff/manifest.json |
| v2081 | tmp/wifi/v2081-wlfw-late-msg21-native-handoff/manifest.json |
| v2059 | tmp/wifi/v2059-permgr-vote-focused-handoff/manifest.json |
| v2053 | docs/reports/NATIVE_INIT_V2053_PRE_WLANMDSP_TRIGGER_EVENT_DIFF_2026-06-04.md |

## Safety

- Host-only parse/report generation; no flash, reboot, adb device mutation, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, DIAG, strace, QRTR matrix, QMI send, tftp ptrace, eSoC/PCIe/GDSC/PMIC/GPIO path, firmware/partition write, or `sda29` write.
