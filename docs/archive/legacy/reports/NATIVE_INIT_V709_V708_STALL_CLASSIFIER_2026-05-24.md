# Native Init V709 V708 Stall Classifier Report

- date: `2026-05-24 KST`
- status: `host-only-pass`; Wi-Fi external ping is **not** complete
- classifier: `scripts/revalidation/native_wifi_v708_stall_classifier_v709.py`
- evidence: `tmp/wifi/v709-v708-stall-classifier/`
- input evidence:
  `tmp/wifi/v708-provider-first-cnss-v120-orchestrated-run-2/`
- decision: `v709-cnss-retry-polling-pre-wlfw-kernel-event-gap`

## Scope

V709 consumed existing V708 evidence only. It did not contact the device, mount
filesystems, start daemons, start Wi-Fi HAL, scan/connect, use credentials, run
DHCP, change routes, ping externally, write sysfs/debugfs, or write boot
images/partitions.

## Result

```text
decision: v709-cnss-retry-polling-pre-wlfw-kernel-event-gap
pass: True
reason: cnss-daemon retry is alive in poll/futex wait after service180/74 and provider registration, while WLFW/QMI/BDF/wlan0 remain absent
next: classify missing kernel ICNSS/WLFW event source before Wi-Fi HAL or scan/connect
```

## Stall Surface

| item | value |
| --- | --- |
| main `wchan` | `do_sys_poll` |
| main syscall | `73` / `ppoll` |
| main stack | `do_sys_poll -> SyS_ppoll` |
| task count | `4` |
| task wchans | `do_sys_poll: 2`, `futex_wait_queue_me: 2` |
| QRTR proc table | unavailable in helper namespace |
| netlink entry for retry pid | present |

Task detail:

| tid class | wchan | syscall class |
| --- | --- | --- |
| main/event thread | `do_sys_poll` | `ppoll` |
| worker/wait thread | `futex_wait_queue_me` | `futex` |

## Marker Context

V708 had the required lower/provider state:

| marker | count |
| --- | ---: |
| `service_notifier_180` | `1` |
| `service_notifier_74` | `1` |
| `cnss_daemon_netlink` | `5` |
| `cnss_daemon_cld80211` | `2` |
| `cnss_binder_transaction_failed` | `0` |
| `binder_transaction_failed` | `0` |
| `qmi_server_connected` | `0` |
| `wlfw_start` | `0` |
| `wlfw_service_request` | `0` |
| `wlan_pd` | `0` |
| `bdf_bdwlan` | `0` |
| `wlan_fw_ready` | `0` |
| `wlan0` | `0` |

## Interpretation

The current blocker is below Wi-Fi HAL and credentials. The retry
`cnss-daemon` is alive and waiting for events after service `180/74` and
provider registration. Since WLFW/QMI/BDF/`wlan0` still do not appear, the next
productive target is the kernel/platform event source that should wake CNSS:

```text
service 180/74 + provider + CNSS netlink
  -> missing ICNSS/WLFW/QCA6390 event
  -> no BDF/FW-ready/wlan0
```

Do not move to Wi-Fi HAL, scan/connect, DHCP, credentials, or external ping
until WLFW/BDF or `wlan0` advances.
