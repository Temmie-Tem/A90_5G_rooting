# V948 V947 Provider-Readiness Classifier Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| host-only classifier | `tmp/wifi/v948-v947-provider-readiness-classifier/manifest.json` | `v948-provider-surface-present-matrix-instrumentation-selected` |

V948 classifies V947 as a provider lifecycle/instrumentation gap, not as a
missing private binder/property surface.

## Findings

| Marker | Value |
| --- | --- |
| provider keys | `558` |
| contract result | `mdm-helper-esoc-fd-observed` |
| binder nodes ready | `true` |
| property socket ready | `true` |
| `per_mgr` vndbinder fd | `true` |
| service-manager trio absent in V947 | `true` |
| `pm-proxy` and `pm_proxy_helper` absent in V947 | `true` |
| `per_mgr` subsystem fds absent | `true` |
| `mdm_helper` `/dev/esoc-0` observed | `true` |
| prior `pm_proxy_helper` D-state risk | `true` |
| prior service-manager-only result insufficient | `true` |

The blocker is now narrower:

1. V947 proves private binder/property surfaces are present.
2. V947 proves `pm-service` opens `vndbinder`.
3. V947 proves `mdm_helper` reaches `/dev/esoc-0`.
4. V947 still has no service-manager/proxy lifecycle and no `per_mgr`
   subsystem fd.
5. V867/V868 still make blind `pm_proxy_helper` retry unsafe.
6. V933 already showed simple service-manager ordering is not enough.

## Guardrails

- Host-only classifier only.
- No device command.
- No actor start.
- No `/dev/subsys_esoc0` open.
- No eSoC ioctl.
- No Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping.
- No boot image or partition write.

## Validation

Executed:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_v947_provider_readiness_classifier_v948.py
python3 scripts/revalidation/native_wifi_v947_provider_readiness_classifier_v948.py
```

## Next

Add provider-readiness diagnostics to the existing CNSS/service-manager matrix
path. That is the next safe comparator because it can answer whether the
service-manager/CNSS matrix has the same `per_mgr` provider fd gap without
starting `pm_proxy_helper`, opening `/dev/subsys_esoc0`, or starting Wi-Fi HAL.
