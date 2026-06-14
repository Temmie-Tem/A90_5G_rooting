# Native Init V708 Provider-First CNSS v120 Stall Live Report

- date: `2026-05-24 KST`
- status: `bounded-live-pass-with-finding`; Wi-Fi external ping is **not**
  complete
- runner: `scripts/revalidation/native_wifi_provider_first_cnss_orchestrator_v708.py`
- live evidence: `tmp/wifi/v708-provider-first-cnss-v120-orchestrated-run-2/`
- helper marker: `a90_android_execns_probe v120`
- helper sha256:
  `acc43d21f948c88350099e1a652a26c7a5f4f0352e06396c6d30dd6908d1ba28`
- decision: `v708-provider-first-cnss-gap-persists`

## Scope Result

V708 executed the bounded provider-first path and still blocked Wi-Fi bring-up:

```text
wifi_hal_start_executed=False
scan_connect_executed=False
wifi_bringup_executed=False
external_ping_executed=False
```

No Wi-Fi HAL, wificond, supplicant, hostapd, scan/connect, credentials, DHCP,
route change, external ping, sysfs subsystem write, `esoc0` open, boot image
write, or partition write was executed.

## Live Result

The provider-first path reproduced the stronger lower state:

| surface | result |
| --- | --- |
| service-notifier `180` | `1` |
| service-notifier `74` | `1` |
| initial pre-provider CNSS | suppressed |
| `vendor.qcom.PeripheralManager` query | exact match |
| post-provider `cnss_daemon_retry` | started |
| CNSS Binder failure | `0` |
| generic Binder failure | `0` |
| helper v120 stall snapshot | captured |
| reboot cleanup | healthy |

The remaining Wi-Fi progression markers stayed absent:

| marker | count |
| --- | ---: |
| `qmi_server_connected` | `0` |
| `wlfw_start` | `0` |
| `wlfw_service_request` | `0` |
| `wlan_pd` | `0` |
| `bdf_regdb` | `0` |
| `bdf_bdwlan` | `0` |
| `wlan_fw_ready` | `0` |
| `wlan0` | `0` |

One kernel warning was observed, matching the prior V700 class:

```text
kernel_warning=1
```

## Stall Capture

Helper v120 emitted:

```text
wifi_companion_start.child.cnss_daemon_retry.stall_snapshot_captured=1
```

The raw transcript contains the detailed read-only snapshot under:

```text
tmp/wifi/v708-provider-first-cnss-v120-orchestrated-run-2/arm-v700-v119-provider-first-cnss/live/native/companion-start-only-with-holder.txt
```

Key extracted values:

| item | value |
| --- | --- |
| main `wchan` | `do_sys_poll` |
| main syscall | `73` / `ppoll` |
| task wchans | `do_sys_poll`, `futex_wait_queue_me` |
| `/proc/net/qrtr` inside snapshot | `open-error=No such file or directory` |
| netlink pid entry | present for the retry process |

## Interpretation

V708 proves the provider-first userspace path is no longer the primary missing
piece:

- service `180/74` is present;
- provider registration is visible;
- `cnss-daemon` reaches netlink/`cld80211`;
- it does not crash or hit the old Binder failure;
- it waits in poll/futex state before WLFW/QMI/BDF/`wlan0` appears.

The next gate should classify the missing kernel ICNSS/WLFW event source from
the captured stall surface, not attempt Wi-Fi HAL, qcwlanstate, scan/connect,
or credentials.
