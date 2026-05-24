# Native Init V716 QCA Bind Reconciliation Plan

- date: `2026-05-24 KST`
- cycle: `V716`
- gate: host-only classifier
- script: `scripts/revalidation/native_wifi_qca_bind_reconciliation_v716.py`

## Objective

Reconcile the V715 QCA6390 child-unbound finding with the earlier V703
Android-vs-native reference before planning any live mutation.

V715 proves the QCA6390 child has no `driver` symlink during the native
service `180/74` positive window. V703 already proved that Android reaches
working Wi-Fi netdevs under the ICNSS parent path and rejected `qca6390`
`bind`/`unbind` as the next target.

## Scope

Allowed:

- parse V715 host-only classifier evidence;
- parse committed V703 Android reference report;
- emit a host-only manifest and summary.

Forbidden:

- device commands;
- sysfs writes;
- `bind`, `unbind`, or `driver_override` writes;
- daemon start;
- Wi-Fi HAL, `wificond`, supplicant, or hostapd start;
- scan/connect/link-up, credentials, DHCP, route changes, or external ping;
- boot image or partition writes.

## Success Label

| decision | meaning |
| --- | --- |
| `v716-qca-child-unbound-not-bind-target` | V715 child-unbound is real, but Android reference keeps the next target on ICNSS-QMI/WLFW readiness rather than QCA bind/unbind |

## Validation

```bash
python3 -m py_compile scripts/revalidation/native_wifi_qca_bind_reconciliation_v716.py
python3 scripts/revalidation/native_wifi_qca_bind_reconciliation_v716.py \
  --out-dir tmp/wifi/v716-qca-bind-reconciliation-plan-check \
  plan
python3 scripts/revalidation/native_wifi_qca_bind_reconciliation_v716.py \
  --out-dir tmp/wifi/v716-qca-bind-reconciliation \
  run
```
