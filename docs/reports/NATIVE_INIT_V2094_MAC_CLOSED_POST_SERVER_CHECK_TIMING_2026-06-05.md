# Native Init V2094 MAC Closed Post-Server-Check Timing

## Summary

- Cycle: `V2094`
- Type: host-only refinement over existing rollback-verified native captures.
- Decision: `v2094-mac-closed-post-up-server-check-no-ota-wlanmdsp-host-pass`
- Label: `mac-closed-post-up-server-check-no-ota-wlanmdsp`
- Pass: `True`
- Reason: MAC assignment is closed as a bounded downstream falsifier; native server_check.txt appears only after wlan_pd UP and never advances into Android's ota_firewall/wlanmdsp producer branch
- Evidence: `tmp/wifi/v2094-mac-closed-post-server-check-timing`

## MAC Falsifier

| field | value |
| --- | --- |
| real_sysfs_mac_addr | True |
| mac_addr | exists=1 writable=1 mode=0220 fs=0x0000000062656572 |
| .mac.info | exists=1 readable=1 writable=0 bytes=17 |
| macloader_trace | runtime_traced=1 records=14 |
| macloader_access | mac_info_read=False mac_addr_open=False mac_addr_write=False shape=False |
| kernel_assign | icnss_assigning_mac_line=False |

## TFTP Timing

| run | label | rollback | per_mgr | wlan_pd_s | server_ms | server_payload | server_after_per_mgr_ms | server_after_wlan_pd_ms | ota_file | ota_log | mcfg_ms | mcfg_payload | mcfg_after_server_ms | wlanmdsp | fw_ready | wlan0 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V2059 | cnss-permgr-register-vote-success-no-wlanmdsp | True | True | 9.175118 | 15706 | hello | 7575 | 6531 | False | 0 | 16992 |  | 1286 | 0 | 0 | 0 |
| V2081 | wlfw-late-msg21-native-msg21-no-fw-ready | True | True | 9.166252 | 15665 | hello | 7574 | 6499 | False | 0 | 0 |  | None | 0 | 0 | 0 |
| V2083 | icnss-qcacld-no-wlanmdsp-request | True | True | 9.215261 | 15684 | hello | 7571 | 6469 | False | 0 | 0 |  | None | 0 | 0 | 0 |
| V2091 | macloader-no-mac-addr-write | True | True | 9.180145 | 16384 | hello | 7575 | 7204 | False | 0 | 17007 |  | 623 | 0 | 0 | 0 |

## Interpretation

- `/sys/wifi/mac_addr` is the real sysfs node and `.mac.info` is readable, but `macloader` never reads the MAC source or writes the kernel node; there is no `icnss: Assigning MAC from Macloader` proof.
- This closes MAC as a bounded falsifier for this producer gate. Even a later successful MAC assign feeds `cnss_utils`/HDD at netdev creation after `FW_READY`, so it is downstream of the missing `wlanmdsp` producer branch.
- The native `server_check.txt=hello` transition is real, but in these current captures it is first visible after `wlan_pd` UP, not in Android's pre-`wlanmdsp` bootstrap order.
- Native then never shows `ota_firewall/ruleset` or `wlanmdsp.mbn`; `mcfg.tmp` remains later/noise, not the initial WLAN-PD firmware-fetch trigger.

## Next Gate

- Do not spend more cycles on MAC/macloader, `server_check` reachability, AP PerMgr/pm-service/rild, mcfg readback, or SDX50M/PCIe/eSoC.
- Next live unit should target the modem-internal state before Android's pre-spawn TFTP branch: why native reaches a post-UP `server_check` write but never issues the Android-order `ota_firewall/ruleset` and `wlanmdsp.mbn` requests.

## Inputs

| run | manifest | helper |
| --- | --- | --- |
| v2059 | tmp/wifi/v2059-permgr-vote-focused-handoff/manifest.json | tmp/wifi/v2059-permgr-vote-focused-handoff/v2058-handoff/test-v1393-helper-result.stdout.txt |
| v2081 | tmp/wifi/v2081-wlfw-late-msg21-native-handoff/manifest.json | tmp/wifi/v2081-wlfw-late-msg21-native-handoff/v2080-handoff/test-v1393-helper-result.stdout.txt |
| v2083 | tmp/wifi/v2083-icnss-qcacld-post-bdf-handoff/manifest.json | tmp/wifi/v2083-icnss-qcacld-post-bdf-handoff/v2082-handoff/test-v1393-helper-result.stdout.txt |
| v2091 | tmp/wifi/v2091-macloader-property-service-handoff/manifest.json | tmp/wifi/v2091-macloader-property-service-handoff/v2090-handoff/test-v1393-helper-result.stdout.txt |

## Related Reports

- Android ordering reference: `docs/reports/NATIVE_INIT_V2053_PRE_WLANMDSP_TRIGGER_EVENT_DIFF_2026-06-04.md`
- MAC source proof: `docs/reports/NATIVE_INIT_V2091_MACLOADER_PROPERTY_SERVICE_HANDOFF_2026-06-05.md`
- Server-check correction: `docs/reports/NATIVE_INIT_V2093_SERVER_CHECK_POST_BRANCH_2026-06-05.md`

## Safety

- Host-only parse/report generation; no flash, reboot, adb mutation, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, DIAG, strace, QRTR matrix, QMI send, tftp ptrace, eSoC/PCIe/GDSC/PMIC/GPIO path, firmware/partition write, or `sda29` write.
