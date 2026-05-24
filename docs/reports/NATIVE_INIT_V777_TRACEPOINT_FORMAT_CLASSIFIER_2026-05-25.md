# Native Init V777 Tracepoint Format Classifier Report

## Result

- decision: `v777-tracepoint-format-fields-classified`
- pass: `true`
- runner: `scripts/revalidation/native_wifi_tracepoint_format_classifier_v777.py`
- evidence: `tmp/wifi/v777-tracepoint-format-classifier/`

## What Ran

```bash
python3 -m py_compile scripts/revalidation/native_wifi_tracepoint_format_classifier_v777.py
python3 scripts/revalidation/native_wifi_tracepoint_format_classifier_v777.py plan
python3 scripts/revalidation/native_wifi_tracepoint_format_classifier_v777.py preflight
python3 scripts/revalidation/native_wifi_tracepoint_format_classifier_v777.py run \
  --allow-tracefs-mount \
  --assume-yes
```

## Evidence Summary

| Tracepoint | ID | Fields | Event-specific Fields |
| --- | ---: | ---: | --- |
| `msm_pil_event:pil_event` | `594` | `6` | `event_name`, `fw_name` |
| `msm_pil_event:pil_notif` | `595` | `7` | `event_name`, `code`, `fw_name` |
| `msm_pil_event:pil_func` | `596` | `5` | `func_name` |
| `dfc:dfc_qmi_tc` | `576` | `7` | `dev_name`, `txq`, `enable` |
| `cfg80211:cfg80211_report_wowlan_wakeup` | `1258` | `16` | `wiphy_name`, `id`, `disconnect`, `rfkill_release`, `packet_len`, `packet`, others |

Safety flags:

| Signal | Value |
| --- | --- |
| mounted before V777 | `false` |
| mounted by V777 | `true` |
| unmounted after V777 | `true` |
| BPF attach executed | `false` |
| ftrace control write executed | `false` |
| Wi-Fi action executed | `false` |
| scan/connect/credential use | `false` |
| DHCP/routes/external ping | `false` |
| reboot/flash/partition write | `false` |

## Interpretation

V777 confirms that the selected stock-kernel tracepoints have readable `format`
files and event-specific fields. This is enough to design a narrow BPF
tracepoint proof without returning to custom kernel flashing.

Best target for V778 is `msm_pil_event:pil_notif`:

- it is modem/PIL-adjacent, matching the current mdm3/PIL/WLAN-PD blocker area;
- it exposes `event_name`, `code`, and `fw_name`;
- it does not require Wi-Fi HAL, scan/connect, credentials, DHCP, routes, or
  external network traffic;
- it should observe subsystem transitions if the later proof only attaches,
  waits briefly, and detaches.

`msm_pil_event:pil_event` is the second candidate. `dfc:dfc_qmi_tc` is QMI-ish
but appears traffic-control oriented. `cfg80211_report_wowlan_wakeup` is
Wi-Fi-related but likely only useful after a wiphy exists, so it is not the
right next proof target for the current pre-`wlan0` blocker.

## Safety

V777 performed temporary tracefs mount/read/cleanup only. It did not attach BPF,
write trace controls, trigger Wi-Fi, start service-manager/Wi-Fi HAL, scan,
connect, use credentials, change DHCP/routes, ping externally, reboot, flash, or
write partitions.

## Next

V778 should plan a bounded BPF feasibility proof for exactly one target:
`msm_pil_event:pil_notif`. The first proof should only attach/read/detach for a
short idle window. It should not trigger modem, Wi-Fi, HAL, scan/connect, or any
network path. If idle attach/read/detach is safe, a later gate can consider
observing an already-safe modem/PIL window.
