# Native Init V1980 Android RIL QMI Strace QRTR Retry

## Summary

- Cycle: `V1980`
- Runner: `scripts/revalidation/android_ril_qmi_strace_qrtr_handoff_v1979.py`
- Decision: `v1979-android-capture-rejected-degraded-or-pcie-mhi`
- Label: `android-capture-rejected-degraded-or-pcie-mhi`
- Pass: `False`
- Reason: Android capture was rejected because it is degraded or has pre-wlan0 PCIe/MHI/eSoC contamination
- Evidence: `tmp/wifi/v1980-android-ril-qmi-strace-qrtr-clean-retry`

## Outcome

- Rejected as Android-good producer evidence because pre-`wlan0` PCIe/MHI contamination was present: `30` lines before `wlan0`.
- The boot still reached internal-modem WLAN markers: `wlan_pd` UP at `9.757418` and `wlan0` at `15.000279`.
- The capture proves the exact observer path can collect raw daemon QRTR payloads, but this contaminated run must not be used as the normal Android reference.

## Producer Evidence

| field | value |
| --- | --- |
| wlan_pd UP | 9.757418 |
| wlan0 | 15.000279 |
| contamination pcie-mhi/esoc/degraded257 | 30/0/False |
| libqmi events/send/rild-send | 3601/579/0 |
| pre-UP lead lookups | 5 |
| pre-UP WLFW lookups | 2 |
| pre-UP lead rild count | 0 |
| pre-UP lead unresolved count | 5 |
| unfiltered dmesg lines | 8942 |
| task map present | True |

## Daemon Strace

| daemon | lines | sendto | recvfrom | sendmsg | recvmsg | hex payload lines |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `rild` | 400 | 112 | 278 | 0 | 5 | 394 |
| `cnss_daemon` | 28 | 5 | 17 | 0 | 2 | 24 |
| `pm_service` | 175 | 0 | 175 | 0 | 0 | 121 |

## QRTR Lookup Matrix

- Corrected parser note: the live `qrtr-lookup-matrix.txt` was `14,800,402` bytes, so the V1979 host parser needed a larger read cap than 8 MB.
- Corrected case count: `9`.
- Labels: `wildcard, wds0, wds1, dms0, dms1, nas0, nas1, wlfw0, wlfw1`.
- Statuses: `{"dms0": "lookup-readback-complete", "dms1": "lookup-readback-complete", "nas0": "lookup-readback-complete", "nas1": "lookup-readback-complete", "wds0": "lookup-readback-complete", "wds1": "del-lookup-send-failed", "wildcard": "lookup-readback-complete", "wlfw0": "lookup-readback-complete", "wlfw1": "lookup-readback-complete"}`.
- Service-event counts: `{"dms0": "0", "dms1": "0", "nas0": "0", "nas1": "0", "wds0": "0", "wds1": "0", "wildcard": "0", "wlfw0": "0", "wlfw1": "0"}`.

## Evidence Files

| file | bytes | lines |
| --- | ---: | ---: |
| `rild.strace.txt` | 107475 | 400 |
| `cnss_daemon.strace.txt` | 5232 | 28 |
| `pm_service.strace.txt` | 32553 | 175 |
| `dmesg-unfiltered.txt` | 992380 | 8942 |
| `libqmi-uprobe-trace.txt` | 507051 | 3601 |
| `qrtr-lookup-matrix.txt` | 14800402 | 548130 |

## Safety

- Rollbackable Android-handoff to native v724 only.
- No QMI payload replay, Wi-Fi HAL start, scan/connect, credential handling, DHCP/routes, external ping, PMIC/GPIO/GDSC/regulator write, forced RC1/case write, `/dev/subsys_esoc0` open, fake ONLINE, eSoC notify/BOOT_DONE, PCI rescan, platform bind/unbind, or partition write beyond the declared boot-image handoff/rollback.
- Native rollback selftest fail=0: `True`.

## Next Gate

- Do not decode this run as the normal Android-good producer reference because it is contaminated.
- The next bounded unit should either produce one clean V1979-style Android-good capture or narrow why the V1979 observer repeatedly introduces/observes pre-`wlan0` PCIe/MHI contamination before escalating to Frida.
