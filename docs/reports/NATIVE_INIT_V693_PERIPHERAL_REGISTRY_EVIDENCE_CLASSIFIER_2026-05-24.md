# Native Init V693 Peripheral Registry Evidence Classifier Report

## Result

- decision: `v693-provider-registration-observability-gap-classified`
- pass: `true`
- evidence: `tmp/wifi/v693-peripheral-registry-evidence-classifier/`
- device commands: `false`
- device mutations: `false`
- Wi-Fi HAL start: `false`
- scan/connect/link-up: `false`
- DHCP/external ping: `false`

## Classification

V693 used only the V692 evidence. It did not rerun the helper or touch the
device.

The registry snapshot itself is complete, but it does not contain Binder
registry data:

| property | value |
| --- | --- |
| registry phases complete | `true` |
| Binder debug files captured | `false` |
| Binder child proc files captured | `false` |
| `/dev/socket` entries in every phase | `property_service` only |

`/dev/socket` remaining `property_service`-only is not enough to prove absence
of a vndbinder service, because the PeripheralManager path registers through
`vndservicemanager`/`/dev/vndbinder`, not through a named `/dev/socket` entry.
Since Binder debugfs is unavailable in this native surface, V692 cannot directly
prove provider service registration.

## Provider Surface

| child | order | observable | exited | exit | fd_count | vndbinder | SELinux result |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `per_mgr` | `10` | `1` | `1` | `0` | `8` | `true` | `no-default-context-for-target` |
| `per_proxy` | `11` | `1` | `1` | `1` | `0` | `false` | `no-default-context-for-target` |
| `cnss_daemon_retry` | `12` | `1` | `1` | `-1` | `16` | `true` | default `vendor_wcnss_service` |
| `vndservicemanager` | `9` | `1` | `1` | `-1` | `10` | `true` | default `vndservicemanager` |

The key new classification is narrower than V692's report:

- `pm-service` reaches `/dev/vndbinder`, then exits `0`;
- `pm-proxy` exits `1` before opening any fd;
- no residual provider process remains;
- registry snapshots are complete but cannot show Binder service names.

## Wi-Fi Markers

The lower Wi-Fi path is still not advanced:

| marker | count |
| --- | ---: |
| service-notifier `180` | `1` |
| service-notifier `74` | `1` |
| `cnss-daemon` netlink | `10` |
| `cnss-daemon` `cld80211` | `4` |
| QMI server connected | `0` |
| WLFW start/request | `0` |
| BDF `regdb`/`bdwlan` | `0` |
| WLAN firmware ready | `0` |
| `wlan0` | `0` |

## Interpretation

V692 did not prove that `vendor.qcom.PeripheralManager` is registered. It
proved that the current registry snapshot method lacks the Binder visibility
needed to answer that question. The next unit should not broaden property
shims, start Wi-Fi HAL, or attempt scan/connect. It should first query the
private `vndservicemanager` namespace directly.

## Validation

Executed:

```bash
python3 -m py_compile \
  scripts/revalidation/native_wifi_peripheral_registry_evidence_classifier_v693.py

python3 scripts/revalidation/native_wifi_peripheral_registry_evidence_classifier_v693.py \
  --out-dir tmp/wifi/v693-peripheral-registry-evidence-classifier-plan \
  plan

python3 scripts/revalidation/native_wifi_peripheral_registry_evidence_classifier_v693.py \
  --out-dir tmp/wifi/v693-peripheral-registry-evidence-classifier \
  run

git diff --check
```

The changed-file secret scan was restricted to the V693 script and docs plus
the docs index. It found only guardrail text and no configured Wi-Fi
credential.

## Next Gate

V694 should implement a bounded vndservice query proof inside the same private
Android namespace:

1. start through the V692 service `74` positive provider path;
2. query `vndservicemanager` for `vendor.qcom.PeripheralManager` or equivalent
   registration state;
3. keep Wi-Fi HAL, `wificond`, supplicant, hostapd, credentials, scan/connect,
   DHCP, route changes, and external ping blocked.
