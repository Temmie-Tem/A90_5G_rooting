# Native Init V816 Idle-vs-Trigger Delta Classifier Report

## Result

- decision: `v816-trigger-advances-mss-sysmon-not-mdm3-service`
- pass: `true`
- runner: `scripts/revalidation/native_wifi_idle_trigger_delta_classifier_v816.py`
- evidence: `tmp/wifi/v816-idle-trigger-delta-classifier/`

## What Ran

```bash
python3 -m py_compile scripts/revalidation/native_wifi_idle_trigger_delta_classifier_v816.py

python3 scripts/revalidation/native_wifi_idle_trigger_delta_classifier_v816.py \
  --out-dir tmp/wifi/v816-idle-trigger-delta-classifier-plan-check \
  plan

python3 scripts/revalidation/native_wifi_idle_trigger_delta_classifier_v816.py run
```

V816 was host-only. It did not execute any device command.

## Evidence Summary

| Signal | Idle V815 | Trigger V812 |
| --- | --- | --- |
| modem/mss | `OFFLINING` | `ONLINE -> ONLINE` |
| mdm3/esoc0 | `OFFLINING` | `OFFLINING -> OFFLINING` |
| QRTR/sysmon | no runtime `sysmon_qmi` | QRTR RX/TX and `sysmon_qmi` present |
| service-notifier/service74 | absent | absent in V812 bounded window |
| WLAN-PD/WLFW/BDF/`wlan0` | absent | absent |
| service69 readback | no idle event | complete; service events `0`, timeouts `0` |

## Classification

V816 narrows the delta:

```text
Idle:
  modem/mss OFFLINING
  mdm3/esoc0 OFFLINING
  no runtime service publication

Lower trigger:
  modem/mss ONLINE
  QRTR/sysmon appears
  mdm3/esoc0 still OFFLINING
  service74/WLAN-PD/WLFW/service69 still absent
```

So the lower trigger is sufficient for modem/sysmon but insufficient for mdm3
and service-publication. The next live gate must sample the V815 surfaces inside
the existing bounded lower-trigger window at before/after holder/companion
points. It should not move upward to service-manager, Wi-Fi HAL, scan/connect,
credentials, DHCP/routes, external ping, or custom-kernel flash.

## Safety

- Host-only classifier; no device command executed.
- No custom kernel flash, boot image write, partition write, reboot, or
  bootloader handoff.
- No daemon start, service-manager start, Wi-Fi HAL start, scan/connect/link-up,
  or credential use.
- No DHCP, route change, or external ping.
- No `boot_wlan`, `qcwlanstate`, `esoc0`, bind/unbind, driver override, or
  module load/unload.
- No Wi-Fi secret material was written to tracked output.

## Next

V817 should add an in-window read-only sampler around the existing lower trigger
window. It should capture the V815 subsystem/sysmon/service-locator surfaces at
least before holder, after holder, and after lower companion, then cleanup via
the established V812/V735 path.
