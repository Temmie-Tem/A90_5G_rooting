# Native Init V677 V676-residual Property Live Report

## Summary

- layout script: `scripts/revalidation/native_property_runtime_overlay_v677.py`
- delta deploy script: `scripts/revalidation/native_property_runtime_incremental_v677.py`
- replay runner: `scripts/revalidation/native_wifi_v535_property_android_order_orchestrator_v676.py`
- layout evidence: `tmp/wifi/v677-v676-residual-private-property-runtime/`
- delta evidence: `tmp/wifi/v677-v676-residual-property-incremental-live-serial-retry/`
- replay evidence: `tmp/wifi/v677-v676-residual-property-replay-live/`
- decision: `v676-property-clean-binder-gap-classified`
- pass: `true`
- cleanup: pass
- scan/connect/DHCP/external ping: not executed

V677 extended the private property layout with the V676 residual denial set,
deployed the delta into the versioned private property root, and reran the
V676-style Android userspace-order live arm. Property denials dropped to zero.

## V677 Layout

| Metric | Value |
| --- | ---: |
| residual denial total from V676 | `370` |
| residual unique keys | `20` |
| V677 property count | `123` |
| V677 context count | `21` |
| missing mappings | `0` |
| missing seeds | `0` |

Representative added keys:

| Property | Context |
| --- | --- |
| `persist.log.tag.ServiceManager` | `u:object_r:log_tag_prop:s0` |
| `log.tag.ServiceManager` | `u:object_r:log_tag_prop:s0` |
| `debug.ld.app.vndservicemanager` | `u:object_r:debug_prop:s0` |
| `debug.ld.app.android.hardware.wifi@1.0-service` | `u:object_r:debug_prop:s0` |
| `debug.ld.app.wificond` | `u:object_r:debug_prop:s0` |
| `ro.boot.product.vendor.sku` | `u:object_r:exported_default_prop:s0` |
| `ro.boot.product.hardware.sku` | `u:object_r:exported_default_prop:s0` |
| `arm64.memtag.process.wificond` | `u:object_r:arm64_memtag_prop:s0` |

## Delta Deploy

The first NCM attempt failed because the host-side NCM route was not configured
after reboot. Non-interactive sudo was unavailable, so the delta was deployed
over serial.

Serial delta upload wrote seven private-root files:

| File | Result |
| --- | --- |
| `property_info` | sha/mv/chmod pass |
| `u:object_r:arm64_memtag_prop:s0` | sha/mv/chmod pass |
| `u:object_r:bootloader_prop:s0` | sha/mv/chmod pass |
| `u:object_r:debug_prop:s0` | sha/mv/chmod pass |
| `u:object_r:exported_default_prop:s0` | sha/mv/chmod pass |
| `u:object_r:log_tag_prop:s0` | sha/mv/chmod pass |
| `u:object_r:vendor_default_prop:s0` | sha/mv/chmod pass |

The lookup phase in that deploy run failed because `/mnt/system` was not
mounted for the standalone lookup command. The wrapper was updated to include
`mountsystem ro` in preflight, and the post-fix preflight passed.

## Replay Result

After the delta deploy, the V676-style live replay produced:

| Marker | Count |
| --- | ---: |
| service-notifier `180` | `1` |
| service-notifier `74` | `1` |
| Binder transaction failure | `1` |
| CNSS Binder transaction failure | `1` |
| kernel warning | `1` |
| QRTR RX | `1` |
| QRTR TX | `1` |
| `sysmon-qmi` | `4` |
| WLFW | `0` |
| BDF | `0` |
| `wlan0` | `0` |

Property surface after V677:

| Metric | Value |
| --- | ---: |
| property denial total | `0` |
| property denial unique | `0` |
| Binder `-22` failures | `5` |

## Interpretation

V677 closes the property-info/property-area blocker that V674 through V676 had
been exposing:

```text
V535 + V677 private property root
  -> V676 residual property denials removed
  -> Android userspace-order children still start
  -> service-notifier 180/74 still present
  -> Binder failures remain
  -> WLFW/BDF/wlan0 still absent
```

The next blocker is now Binder registration/transaction behavior. More property
layout work is not the shortest next step unless a later run introduces new
denials. The next gate should capture or repair the `servicemanager`,
`hwservicemanager`, `wificond`, and `cnss-daemon` Binder `-22` failure path in
the same bounded private namespace.

## Cleanup

The replay arm performed reboot cleanup and returned to healthy native control:

| Check | Result |
| --- | --- |
| version seen | pass |
| status healthy | pass |
| wait | `32.34s` |

## Validation

```sh
python3 -m py_compile \
  scripts/revalidation/native_property_runtime_overlay_v677.py \
  scripts/revalidation/native_property_runtime_incremental_v677.py

python3 scripts/revalidation/native_property_runtime_overlay_v677.py \
  --out-dir tmp/wifi/v677-v676-residual-private-property-runtime \
  run

python3 scripts/revalidation/native_property_runtime_incremental_v677.py \
  --out-dir tmp/wifi/v677-v676-residual-property-incremental-preflight-postfix \
  preflight

python3 scripts/revalidation/native_wifi_v535_property_android_order_orchestrator_v676.py \
  --out-dir tmp/wifi/v677-v676-residual-property-replay-live \
  --apply \
  --assume-yes \
  run
```

The validation passed. The final replay confirmed `property_denial_total=0`
with no scan/connect, Wi-Fi bring-up, DHCP, or external ping.
