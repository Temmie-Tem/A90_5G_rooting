# Native Init V816 Idle-vs-Trigger Delta Classifier Plan

## Goal

Compare V815 idle stock-v724 snapshot with V812 lower-trigger evidence to
identify which subsystem/sysmon/service-publication state changes only during
the bounded trigger window.

## Scope

- Target script:
  - `scripts/revalidation/native_wifi_idle_trigger_delta_classifier_v816.py`
- Inputs:
  - V815 idle read-only subsystem/sysmon snapshot.
  - V812 below-HAL lower-trigger observer.

## Hard Gates

- Host-only: no device command.
- No custom kernel flash, boot image write, partition write, reboot, or
  bootloader handoff.
- No daemon start, service-manager start, Wi-Fi HAL start, scan/connect/link-up,
  or credential use.
- No DHCP, route change, or external ping.
- No `boot_wlan`, `qcwlanstate`, `esoc0`, bind/unbind, driver override, or
  module load/unload.

## Success Criteria

- V816 compiles and plan-only manifest passes.
- V815 and V812 manifests are present and passed.
- Idle baseline shows modem/mdm3 `OFFLINING` and no service publication.
- Trigger evidence shows mss/QRTR/sysmon advancement.
- Trigger evidence still shows mdm3/service74/WLAN-PD/WLFW/BDF/`wlan0` absent.
- Classifier selects the next live gate as in-window subsystem/sysmon/service
  state sampling, not HAL/connect or custom-kernel flash.

## Validation

```bash
python3 -m py_compile scripts/revalidation/native_wifi_idle_trigger_delta_classifier_v816.py

python3 scripts/revalidation/native_wifi_idle_trigger_delta_classifier_v816.py \
  --out-dir tmp/wifi/v816-idle-trigger-delta-classifier-plan-check \
  plan

python3 scripts/revalidation/native_wifi_idle_trigger_delta_classifier_v816.py run

git diff --check
```
