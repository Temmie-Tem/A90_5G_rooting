# Native Init V716 QCA Bind Reconciliation Report

- date: `2026-05-24 KST`
- runner: `scripts/revalidation/native_wifi_qca_bind_reconciliation_v716.py`
- V715 source: `tmp/wifi/v715-icnss-edge-surface-classifier-live-evidence-r2/manifest.json`
- V703 reference: `docs/reports/NATIVE_INIT_V703_ANDROID_NATIVE_BINDING_COMPARE_2026-05-24.md`
- evidence: `tmp/wifi/v716-qca-bind-reconciliation/`
- decision: `v716-qca-child-unbound-not-bind-target`
- status: `pass`

## Scope Result

V716 was host-only:

- `device_commands_executed=False`
- `device_mutations=False`
- `daemon_start_executed=False`
- `wifi_hal_start_executed=False`
- `wifi_bringup_executed=False`
- `external_ping_executed=False`

No live device command, sysfs write, `bind`/`unbind`, `driver_override`, daemon
start, Wi-Fi HAL, scan/connect, DHCP, route change, external ping, boot image
write, or partition write was executed.

## Result

V716 reconciles two true facts:

1. V715 proves native service `180/74` positive edge has ICNSS parent bound and
   QCA6390 child unbound.
2. V703 proves Android reaches working Wi-Fi netdevs under the ICNSS parent
   path and explicitly rejected QCA6390 `bind`/`unbind` as the next target.

| check | status | detail |
| --- | --- | --- |
| `v715-input-qca-child-unbound` | `pass` | `decision=v715-qca6390-platform-child-unbound` |
| `native-icnss-parent-bound` | `pass` | `service74_open=True window=True` |
| `native-qca-child-unbound` | `pass` | `service74_open=False window=False` |
| `native-wlfw-absent` | `pass` | `qmi_server_connected=0 wlfw_start=0 bdf=0 fw_ready=0 wlan0=0` |
| `android-icnss-parent-netdev-reference` | `pass` | Android report contains ICNSS-parent netdev paths |
| `android-qca-bind-target-rejected` | `pass` | Android/native comparison rejects QCA bind/unbind |
| `android-wlfw-reference-present` | `pass` | Android report contains ICNSS-QMI/WLFW/BDF/fw-ready markers |

## Interpretation

The missing QCA6390 child `driver` symlink is a valid observation, but it is not
a sufficient target for mutation. Android's reference path reaches Wi-Fi
through ICNSS parent netdev creation and ICNSS-QMI/WLFW readiness, not a proven
manual QCA6390 platform bind.

Therefore V716 supersedes the risky interpretation of V715:

```text
do not write qca6390 bind/unbind/driver_override
target ICNSS-QMI/WLFW readiness trigger instead
```

The next gate should focus on why service `180/74` plus provider/CNSS retry
does not transition into:

- `icnss_qmi: QMI Server Connected`
- `cnss-daemon wlfw_start`
- BDF download
- firmware-ready
- `wlan0`

## Validation

Executed:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_qca_bind_reconciliation_v716.py

python3 scripts/revalidation/native_wifi_qca_bind_reconciliation_v716.py \
  --out-dir tmp/wifi/v716-qca-bind-reconciliation-plan-check \
  plan

python3 scripts/revalidation/native_wifi_qca_bind_reconciliation_v716.py \
  --out-dir tmp/wifi/v716-qca-bind-reconciliation \
  run

git diff --check
```

Results:

```text
v716-qca-bind-reconciliation-plan-ready
v716-qca-child-unbound-not-bind-target
```
