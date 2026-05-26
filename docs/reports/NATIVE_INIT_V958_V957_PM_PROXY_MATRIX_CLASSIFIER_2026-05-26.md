# V958 V957 PM-Proxy Matrix Classifier Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| host-only classifier | `tmp/wifi/v958-v957-pm-proxy-matrix-classifier/manifest.json` | `v958-provider-lifecycle-repaired-wlfw-gap-remains` |

V958 compares V957 with V953. The `pm-proxy` comparator repaired the
provider-lifecycle gap, but the remaining blocker is still below that layer:
CNSS never emits the WLFW precondition.

## Findings

| Marker | Value |
| --- | --- |
| provider keys | `786` |
| V957 provider persisted | `true` |
| V953 provider degraded | `true` |
| `pm-proxy` clean | `true` |
| fail-closed safety | `true` |
| WLFW missing | `true` |

## Interpretation

`pm-proxy` is now justified as part of the native Android-userspace companion
set. It keeps `pm-service` and its vndbinder surface alive through
service-manager and CNSS actor startup. That means the previous provider
lifetime gap is no longer the primary blocker.

The next blocker is the post-provider WLFW/CNSS gap: even with `pm-service`,
`pm-proxy`, service managers, `mdm_helper`, `cnss_diag`, and `cnss-daemon`
present, the helper still records:

- `wlfw_precondition_observed=0`
- `subsys_esoc0_open_attempted=0`
- `wifi_hal_start_executed=0`
- `external_ping=0`

## Validation

Executed:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_v957_pm_proxy_matrix_classifier_v958.py
python3 scripts/revalidation/native_wifi_v957_pm_proxy_matrix_classifier_v958.py
```

## Next

Run a bounded full-surface `pm-proxy` matrix capture to classify the
post-provider WLFW/CNSS gap. Keep `pm_proxy_helper`, `/dev/subsys_esoc0`,
Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping blocked.
