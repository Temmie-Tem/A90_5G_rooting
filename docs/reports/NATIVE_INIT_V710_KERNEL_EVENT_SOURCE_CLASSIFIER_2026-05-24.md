# Native Init V710 Kernel Event Source Classifier Report

- date: `2026-05-24 KST`
- status: `host-only-pass`; Wi-Fi external ping is **not** complete
- classifier: `scripts/revalidation/native_wifi_kernel_event_source_classifier_v710.py`
- evidence: `tmp/wifi/v710-kernel-event-source-classifier-rerun/`
- input evidence: `tmp/wifi/v708-provider-first-cnss-v120-orchestrated-run-2/`, `tmp/wifi/v709-v708-stall-classifier/`, `tmp/wifi/v703-android-native-binding-compare/`
- decision: `v710-missing-qca6390-wlfw-kernel-event-source`

## Scope

V710 consumed existing evidence only. It did not contact the device, mount
filesystems, start daemons, start service-manager, start Wi-Fi HAL, scan or
connect, use credentials, run DHCP, change routes, ping externally, write
sysfs/debugfs, or write boot images/partitions.

## Result

```text
decision: v710-missing-qca6390-wlfw-kernel-event-source
pass: True
reason: native reaches service180/74, provider, and CNSS retry poll wait with no Binder failure, but QCA6390 remains unbound and WLFW/BDF/wlan0 are absent while Android reaches ICNSS-QMI/WLFW
next: target the QCA6390 bind/power/MHI-or-ICNSS event edge before Wi-Fi HAL, scan/connect, DHCP, or external ping
```

## Version Mapping

The user-provided V666 causal chain is valid, but V666/V667 already consumed the
basic `service-notifier 180/74` versus cnss2/WLFW progression question. V710
therefore rebases that direction onto the current V708/V709 stall point:

```text
service 180/74 + provider + CNSS netlink/poll wait
  -> missing QCA6390/ICNSS/WLFW event
  -> no BDF/FW-ready/wlan0
```

One important correction is preserved: Android evidence logs BDF activity
through `cnss-daemon` after ICNSS-QMI/WLFW readiness. V710 therefore targets the
missing prerequisite event rather than treating BDF download as proven
kernel-only behavior.

## Native Evidence

V708 reached the lower/provider/CNSS retry gate:

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
| `bdf_regdb` | `0` |
| `bdf_bdwlan` | `0` |
| `wlan_fw_ready` | `0` |
| `wlan0` | `0` |

V709 showed the post-provider retry `cnss-daemon` is alive in `poll`/`futex`,
not crashed, while waiting before WLFW.

Focused V708 helper sysfs captured the platform split:

| item | value |
| --- | --- |
| ICNSS device | present and driver-bound |
| QCA6390 node | present |
| QCA6390 driver symlink | absent |
| native `wlan0` | absent |
| native netdevs | `dummy0`, `sit0`, `lo`, `ip6_vti0`, `bonding_masters`, `ip6tnl0`, `ip_vti0`, `bond0` |

## Android Delta

Android reference has the missing continuation:

| marker | count |
| --- | ---: |
| `service_notifier_wlan_pd` | `2` |
| `icnss_qmi_connected` | `1` |
| `wlfw_start` | `1` |
| `wlfw_service_request` | `3` |
| `bdf_regdb` | `1` |
| `bdf_bdwlan` | `1` |
| `wlan_fw_ready` | `1` |
| `wlan0` | `12` |

Timing from the Android reference is tight after WLAN-PD:

| delta | ms |
| --- | ---: |
| Android WLAN-PD to ICNSS-QMI | `2.788` |
| Android ICNSS-QMI to BDF regdb | `71.065` |
| Android BDF to FW-ready | `4987.138` |
| Android FW-ready to `wlan0` | `302.933` |
| Native service `74` to ICNSS-QMI | `None` |
| Native service `74` to WLFW | `None` |

## Interpretation

The best current attribution is not Wi-Fi credentials, Wi-Fi HAL, scan/connect,
DHCP, or external network. It is also no longer a plain provider-registration or
post-provider CNSS Binder failure: the post-provider retry has no Binder
transaction failure and is alive waiting for events.

The missing edge is now narrower:

```text
QCA6390 visible but unbound
  + ICNSS bound
  + service 180/74 positive
  + CNSS retry alive
  - ICNSS-QMI/WLFW/BDF/FW-ready/wlan0
```

The next productive target is the QCA6390 bind/power/MHI-or-ICNSS event edge.
Wi-Fi HAL start, scan/connect, DHCP, credentials, and external ping remain
blocked until WLFW/BDF or `wlan0` advances.

## Validation

Executed:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_kernel_event_source_classifier_v710.py
python3 scripts/revalidation/native_wifi_kernel_event_source_classifier_v710.py --out-dir tmp/wifi/v710-kernel-event-source-plan-check plan
python3 scripts/revalidation/native_wifi_kernel_event_source_classifier_v710.py --out-dir tmp/wifi/v710-kernel-event-source-classifier-rerun run
```
