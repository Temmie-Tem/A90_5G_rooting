# Native Init V822 Sysmon Nameservice Gap Report

## Result

- decision: `v822-sysmon-ssctl-matrix-gap-classified`
- pass: `true`
- runner: `scripts/revalidation/native_wifi_sysmon_nameservice_gap_classifier_v822.py`
- evidence: `tmp/wifi/v822-sysmon-nameservice-gap-classifier/`

## What Ran

```bash
python3 -m py_compile \
  scripts/revalidation/native_wifi_sysmon_nameservice_gap_classifier_v822.py

python3 scripts/revalidation/native_wifi_sysmon_nameservice_gap_classifier_v822.py \
  --out-dir tmp/wifi/v822-sysmon-nameservice-gap-plan-check \
  plan

python3 scripts/revalidation/native_wifi_sysmon_nameservice_gap_classifier_v822.py \
  run
```

## Evidence Summary

| Check | Result |
| --- | --- |
| V821 input | pass |
| V821 matrix transport | pass |
| source constants | pass |
| sysmon SSCTL source service | `43` (`0x2b`) |
| sysmon SSCTL version | `2` |
| board mdm3 SSCTL instance | `16` (`0x10`) |
| V821 included SSCTL | no |
| device commands | not executed |

## Source Model

| Component | Source lookup | Service | Version | Instance |
| --- | --- | --- | --- | --- |
| service-locator | `service-locator.c:qmi_add_lookup` | `64` | `1` | `1` |
| service-notifier | `service-notifier.c:qmi_add_lookup(instance_id)` | `66` | `1` | `74`, `180` |
| sysmon SSCTL | `sysmon-qmi.c:qmi_add_lookup(desc->ssctl_instance_id)` | `43` | `2` | `16` |
| WLFW | `icnss_qmi.c:qmi_add_lookup(..., instance 0)` | `69` | `1` | `0` |

## Matrix Coverage

| Component | Service | Instance | V821 included | Service events |
| --- | --- | --- | --- | --- |
| service-locator | `64` | `1` | yes | `0` |
| service-notifier | `66` | `74` | yes | `0` |
| service-notifier | `66` | `180` | yes | `0` |
| sysmon SSCTL | `43` | `16` | no | n/a |
| WLFW | `69` | `0` | yes | `0` |

## Interpretation

V822 explains the apparent mismatch without another live action. V821 correctly
covered service-locator, service-notifier, and WLFW candidates, and those
queries returned clean end-of-list results. However, the `sysmon-qmi` path that
V817/V821 runtime counters observe is not service-locator or service-notifier.
OSRC source shows `sysmon-qmi.c` performs `qmi_add_lookup()` against SSCTL
service `0x2b`, version `2`, with `desc->ssctl_instance_id`. The r3q board DTS
sets mdm3 `qcom,ssctl-instance-id = <0x10>`.

Therefore the next useful live gate is not a blind lower retry. It is a narrow
matrix extension that adds `ssctl:43:16` while preserving the no-QMI-payload and
below-HAL guardrails.

## Safety

- Host-only run; no device command executed.
- No QRTR socket opened and no QRTR/QMI packet transmitted.
- No custom kernel flash, boot image write, partition write, reboot, or
  bootloader handoff executed.
- No service-manager, Wi-Fi HAL, scan/connect/link-up, credential use, DHCP,
  route change, or external ping executed.
- V775 custom OSRC kernel flashing pause remains active.
- No Wi-Fi secret material was written to tracked output.

## Next

V823 should reuse helper v125 and run a bounded no-QMI nameservice matrix that
adds `ssctl:43:16`. If SSCTL publishes while service-notifier/WLFW remain empty,
the next blocker is the SSCTL-to-service-notifier/WLAN-PD transition. If SSCTL is
also clean-empty, the next blocker is QRTR nameservice visibility for kernel QMI
clients versus userspace AF_QIPCRTR readback.
