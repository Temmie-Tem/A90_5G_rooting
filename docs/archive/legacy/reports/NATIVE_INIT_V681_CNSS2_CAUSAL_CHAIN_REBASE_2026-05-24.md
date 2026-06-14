# Native Init V681 cnss2/WLFW Causal-chain Rebase Report

- date: `2026-05-24 KST`
- status: `host-only-pass`; Wi-Fi external ping is **not** complete
- script: `scripts/revalidation/native_wifi_cnss2_causal_chain_rebase_v681.py`
- plan evidence: `tmp/wifi/v681-cnss2-causal-chain-rebase-plan/`
- run evidence: `tmp/wifi/v681-cnss2-causal-chain-rebase/`
- decision: `v681-cnss2-causal-chain-rebased`

## Scope

V681 consumes existing evidence only. It does not contact the device, mount
filesystems, write sysfs, start daemons, start Wi-Fi HAL, scan/connect, run
DHCP, change routes, use credentials, write boot partitions, or ping externally.

The purpose is to fold the clarified dependency model back into current routing:

```text
modem ONLINE
  -> service-locator can resolve WLAN-PD location
  -> service-notifier 180/74 become visible
  -> cnss2/icnss kernel progression should power QCA6390
  -> QCA6390 WLFW boot should publish service 69
  -> BDF download, firmware-ready, and wlan0 should follow
```

## Result

| key | value |
| --- | --- |
| decision | `v681-cnss2-causal-chain-rebased` |
| pass | `True` |
| device_commands_executed | `False` |
| device_mutations | `False` |
| mount_executed | `False` |
| daemon_start_executed | `False` |
| wifi_bringup_executed | `False` |
| external_ping_executed | `False` |

## Checks

| check | result |
| --- | --- |
| source evidence ready | pass |
| service `74` positive but cnss2 progression absent | finding |
| icnss/QCA6390 sysfs present but no netdev | finding |
| Android advances while native does not | finding |
| Binder debugfs is secondary observability gap | finding |

## Key Evidence

V667 already answered the proposed cnss2 `pd_notifier` and modem-state read-only
question from the V666 window:

| marker | V667 count |
| --- | ---: |
| service-notifier `180` | `1` |
| service-notifier `74` | `1` |
| cnss2 `pd_notifier` | `0` |
| cnss2 power-on | `0` |
| WLFW service `69` | `0` |
| BDF `bdwlan` | `0` |
| `wlan0` | `0` |

V668 then proved the platform sysfs objects are visible but do not progress:

| marker | V668 count |
| --- | ---: |
| service-notifier aggregate | `2` |
| focused icnss device captured | `1` |
| focused QCA6390 device captured | `1` |
| focused `wlan0` captured | `0` |
| WLFW | `0` |
| WLAN-PD | `0` |
| BDF | `0` |
| `wlan0` | `0` |

V669 showed Android reaches the missing downstream path while native does not:

| marker | Android | Native V668 |
| --- | ---: | ---: |
| WLFW start | `1` | `0` |
| WLFW service request | `1` | `0` |
| WLAN-PD indication | `2` | `0` |
| QMI server connected | `1` | `0` |
| BDF `bdwlan` | `1` | `0` |
| WLAN firmware ready | `1` | `0` |
| `wlan0` event | `3` | `0` |

V680 remains useful for diagnostics, but not as the primary bring-up route:

| marker | V680 count |
| --- | ---: |
| Binder debug ENOENT | `72` |
| Binder debug path blocks | `20` |
| Binder debug nonzero blocks | `0` |

## Interpretation

The user-provided causal model is consistent with existing evidence, but the
proper version routing is V681+, not a new V666 live retry. V666 was consumed by
the repaired private CNSS retry; V667 and V668 already implemented the proposed
`service-notifier 180/74` versus cnss2 progression check.

The important routing correction is that Binder debugfs should be treated as
secondary observability. It can help explain a `cnss-daemon` Binder transaction,
but Wi-Fi cannot advance until cnss2/WLFW progression moves toward service
`69`, BDF download, firmware-ready, and `wlan0`.

## Next Gate

Plan V682 as a bounded cnss2/WLFW progression observer:

- observe dmesg/sysfs/debug-surface state around service-notifier `180/74` and
  CNSS retry;
- look for cnss2/icnss callback, QCA6390 power, WLFW service `69`, BDF,
  firmware-ready, and `wlan0` markers;
- keep Wi-Fi HAL scan/connect, credentials, DHCP, route changes, and external
  ping blocked until `wlan0` exists.

## References

- Android kernel CNSS2 Kconfig:
  `https://android.googlesource.com/kernel/msm-modules/wlan-platform/+/refs/heads/android-msm-eos-android13-wear-kr3-pixel-watch/cnss2/Kconfig`
- WLFW service id locator:
  `docs/reports/NATIVE_INIT_V274_WLFW_SERVICE_LOCATOR_2026-05-19.md`
- Original V666 follow-up hypothesis:
  `docs/reports/NATIVE_INIT_V666_REPAIRED_PRIVATE_CNSS_RETRY_LIVE_2026-05-24.md`

## Validation

```sh
python3 -m py_compile \
  scripts/revalidation/native_wifi_cnss2_causal_chain_rebase_v681.py

python3 scripts/revalidation/native_wifi_cnss2_causal_chain_rebase_v681.py \
  --out-dir tmp/wifi/v681-cnss2-causal-chain-rebase-plan \
  plan

python3 scripts/revalidation/native_wifi_cnss2_causal_chain_rebase_v681.py \
  --out-dir tmp/wifi/v681-cnss2-causal-chain-rebase \
  run
```

The validation passed with `v681-cnss2-causal-chain-rebased`.
