# Native Init V744 V122 CNSS-only Comparison Report

- date: `2026-05-24 KST`
- runner: `scripts/revalidation/native_wifi_current_cnss_only_observer_v735.py`
- helper: `a90_android_execns_probe v122`
- prep evidence: `tmp/wifi/v744-v122-cnss-only-comparison-prep-after-hide/`
- live evidence: `tmp/wifi/v744-v122-cnss-only-comparison-retry/`
- decision: `v735-current-cnss-only-service-publication-advance`
- pass: `true`

## Summary

V744 reran the known V735 CNSS-only sequence with helper v122. After hiding the
auto menu and refreshing current-boot SELinuxfs/policy state, the comparison
passed: helper v122 still reproduces QRTR TX, `sysmon-qmi`, and
service-notifier publication evidence without Wi-Fi HAL or connect actions.

This separates the V743 result: helper v122 itself is not the regression.
The service-`74` gated `mdm_helper` mode is checking the gate too early, or its
gate logic does not match the dmesg/service-notifier signal used by the older
CNSS-only observer.

## Key Results

| item | result |
| --- | --- |
| helper mode | `wifi-companion-start-only` |
| helper order | `qrtr_ns,rmt_storage,tftp_server,pd_mapper,cnss_diag,cnss_daemon` |
| child lifecycle | six children started, observable, and postflight safe |
| `mss` | `OFFLINING -> ONLINE -> ONLINE` |
| `mdm3` | stayed `OFFLINING` |
| QRTR RX | present |
| QRTR TX | present |
| `sysmon-qmi` | present |
| service-notifier | service `180` marker present |
| service `69` readback | no service events |
| MHI/QCA6390/WLFW/BDF/`wlan0` | absent |
| postflight | reboot cleanup and native health passed |

## Evidence

```text
decision: v735-current-cnss-only-service-publication-advance
pass: True
reason: CNSS-only window produced service publication evidence but no MHI/WLFW
service_manager_start_executed: False
wifi_hal_start_executed: False
scan_connect_executed: False
external_ping_executed: False
```

## Interpretation

The active blocker remains below Wi-Fi HAL/connect:

```text
mss ONLINE
  -> QRTR TX + sysmon-qmi + service-notifier 180 present
  -> mdm3 still OFFLINING
  -> MHI/QCA6390/WLFW/service 69/BDF/wlan0 absent
```

The next implementation should repair the gated `mdm_helper` decision point so
it can start after the observed service publication marker, or add a two-phase
observer that first confirms CNSS-only service publication and then starts
`mdm_helper` in the same bounded window.
