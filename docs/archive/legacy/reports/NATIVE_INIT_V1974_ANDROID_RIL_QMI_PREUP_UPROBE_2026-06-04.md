# V1974 Android RIL QMI Pre-UP Uprobe

- generated: `2026-06-04`
- decision: `v1974-anonymous-dms-nas-wds-lookup-preup-no-explicit-rild-preup-rollback-pass`
- label: `anonymous-lead-lookup-preup-no-explicit-rild-preup`
- pass: `True`
- evidence: `tmp/wifi/v1974-ril-qmi-preup-uprobe-live-20260604-055336`

## Gate

Measure the producer side of the normal Android internal-modem path with pre-armed tracefs uprobes, not attach-time `strace`: does RIL issue DMS/NAS/WDS QMI before `msm/modem/wlan_pd` reaches UP, or is the pre-UP producer elsewhere?

## Implementation

V1974 extends the proven V1934 rollbackable Android handoff. It pre-arms `/vendor/lib64/libqmi_cci.so` uprobes for:

| symbol | offset | captured fields |
| --- | ---: | --- |
| `qmi_client_send_msg_sync` | `0x6dc0` | client, msg_id, req/resp pointers, lengths, timeout |
| `qmi_client_send_msg_async` | `0x659c` | client, msg_id, request pointer/length, callback, transaction handle |
| `qmi_client_send_raw_msg_sync` | `0x6ae0` | client, msg_id, request/response pointer/length, timeout |
| `qmi_client_send_raw_msg_async` | `0x5f88` | client, msg_id, request pointer/length, callback, transaction handle |
| `qmi_client_get_service_list` path | `0x5e08` / `0x5eec` / `0x5ef0` | service object, decoded service ID, found count |

## Result

Normal Android state-up was captured and rollback passed. The trace did not show any explicit `rild`-comm QMI send or DMS/NAS/WDS lookup before `wlan_pd` UP. It did show pre-UP DMS service lookup on anonymous trace threads, so the captured pre-UP producer edge is not proven to be RIL.

| field | value |
| --- | --- |
| `wlan_pd` UP | `9.587781` |
| `icnss_qmi` connected | `9.589148` |
| `wlan0` event | `15.214171` |
| PCIe/MHI before wlan0 | `0` |
| eSoC boot-failed before wlan0 | `0` |
| degraded 257s-like boot | `False` |
| rollback selftest | `pass=11 warn=1 fail=0` |

## Uprobe Decode

| field | value |
| --- | --- |
| libqmi events | `3256` |
| send events | `495` |
| send events before `wlan_pd` UP | `110` |
| explicit `rild` send events | `0` |
| explicit `rild` DMS/NAS/WDS lookups | `0` |
| any DMS/NAS/WDS lookups | `81` |
| any DMS/NAS/WDS lookups before UP | `5` |
| pre-UP lead service IDs | `DMS` |

First decoded pre-UP lead lookup:

```text
<...>-1272 [006] 8.830730: libqmi_get_service_list_lookup_call ... svc_id=0x2 ...
```

The last DMS lookup/return sequence for that anonymous thread completes at `9.315868`, about `0.272s` before `wlan_pd` UP. The same trace also shows pre-UP WLFW service `0x45` lookups at `8.842774` and `8.843707`. Bulk anonymous traffic with DMS/NAS-looking message IDs appears after `wlan_pd` UP and before `wlan0`, but V1974 did not capture enough process identity to safely label those anonymous PIDs as RIL.

## Interpretation

- Lead A as stated, “RIL DMS/NAS handshake triggers `wlan_pd`”, is not supported by explicit pre-UP `rild` evidence in V1974.
- The measured pre-UP producer edge is lower/earlier: anonymous libqmi service lookup for DMS (`0x02`) and WLFW (`0x45`) before `wlan_pd` UP.
- The next native gate should target reproducing that non-HAL internal-modem libqmi/CNSS service-discovery path, not another attach-time RIL strace and not SDX50M/eSoC/PCIe/GDSC.
- If RIL attribution still matters, the next measurement must add full early process/PID attribution or trace task ancestry; the current V1974 evidence should not be over-labeled as RIL.

## Safety

Rollbackable Android-handoff to native v724 only. No Wi-Fi HAL start, scan/connect, credentials, DHCP/routes, external ping, `/dev/subsys_esoc0`, eSoC notify/BOOT_DONE, PCI rescan, platform bind/unbind, PMIC/GPIO/GDSC/regulator write, fake ONLINE state, forced RC1/case write, or sda29 remount-write was performed.
