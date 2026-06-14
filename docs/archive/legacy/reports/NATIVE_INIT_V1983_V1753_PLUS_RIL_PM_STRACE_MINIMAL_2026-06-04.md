# Native Init V1983 V1753 Plus RIL PM Strace Minimal

## Summary

- Cycle: `V1983`
- Decision: `v1983-minimal-ril-pm-strace-rejected-pcie-mhi-contaminated`
- Pass: `False`
- Reason: minimal RIL/PM strace capture was rejected because pre-wlan0 external RC1/MHI/eSoC contamination appeared
- Evidence: `tmp/wifi/v1983-v1753-plus-ril-pm-strace-minimal-live`
- Base handoff: `v1521-handoff-sampler-files-missing-rollback-pass` / `False`

## Clean Baseline Gate

| field | value |
| --- | --- |
| wlan_pd | 9.709573 |
| wlan0 | 15.202059 |
| pre-wlan0 external RC1/MHI/eSoC | 17 |
| degraded 257s-like | False |
| requested_wlanmdsp | 1 |
| requested_pd_image | 1 |
| wlanmdsp logcat lines | 10 |
| request_summary | {"cnss_trace_lines": "0", "pm_service_trace_lines": "112", "requested_pd_image": "1", "requested_wlanmdsp": "1", "rild_trace_lines": "372", "rmt_storage_trace_lines": "0", "tftp_trace_lines": "0", "wlan0_seen": "0", "wlfw_seen": "1"} |

## Daemon Strace

| daemon | lines | sendto | recvfrom | sendmsg | recvmsg | hex payload |
| --- | --- | --- | --- | --- | --- | --- |
| rild | 372 | 100 | 257 | 0 | 5 | 361 |
| pm_service | 112 | 0 | 112 | 0 | 0 | 83 |
| cnss_daemon | 0 | 0 | 0 | 0 | 0 | 0 |

## Scope

- Built directly on the clean V1753 firmware-request baseline.
- Adds only early `rild` and `pm-service` AF_QIPCRTR strace; tracefs uprobes/kprobes and QRTR lookup matrix remain disabled.
- The result is producer observability only, not native Wi-Fi bring-up.

## Safety

Rollbackable Android-handoff to native v724 only. No QMI payload replay, Wi-Fi HAL start, scan/connect, credential handling, DHCP/routes, external ping, PMIC/GPIO/GDSC/regulator write, forced RC1/case write, `/dev/subsys_esoc0` open, fake ONLINE, eSoC notify/BOOT_DONE, PCI rescan, platform bind/unbind, or partition write beyond declared boot-image handoff/rollback.
