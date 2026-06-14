# Native Init V1318 Critical Lower Trace Collector

## Summary

- Cycle: `V1318`
- Type: bounded live collector
- Decision: `v1318-target-critical-lines-captured`
- Result: PASS
- Evidence:
  - `tmp/wifi/v1318-critical-lower-trace-collector-live/manifest.json`
  - `tmp/wifi/v1318-critical-lower-trace-collector-live/summary.md`
- Script: `scripts/revalidation/native_wifi_critical_lower_trace_collector_live_v1318.py`

V1318 reruns the bounded late `per_proxy` PM-service path with only critical
lower tracefs events enabled. This removes broad IRQ/clock noise from V1316
and preserves a larger sample of regulator/GPIO/power/PIL lines.

## Result

| field | value |
| --- | --- |
| decision | v1318-target-critical-lines-captured |
| critical total count | 3920 |
| line count | 2000 |
| target keyword lines | 2 |
| target GPIO lines | 7 |
| GPIO1270 / GPIO135 / GPIO142 lines | 5 / 2 / 0 |
| GPIO135 high count | 1 |
| post GPIO135 sample span sec | 49.28001900000004 |
| eSoC PIL notif count | 2 |
| group counts | {"gpio": 1582, "msm_pil_event": 40, "power": 0, "regulator": 2298} |
| event counts | {"gpio_direction": 459, "gpio_value": 509, "pil_notif": 30, "regulator_enable": 71, "regulator_enable_complete": 71, "regulator_set_voltage": 430, "regulator_set_voltage_complete": 430} |
| category counts | {"background_sdcard": 382, "background_storage_ufs": 62, "critical_unclassified": 1006, "generic_pmic_regulator": 548, "target_keyword": 2} |
| GPIO counts | {"116": 6, "1270": 5, "135": 2, "141": 2, "79": 273, "80": 634, "96": 46} |

## Target Samples

| event | category | name | gpio | line |
| --- | --- | --- | --- | --- |
| pil_notif | target_keyword |  | None |    Binder:9229_3-9837  [000] ....  1073.348301: pil_notif: event_name=before_send_notif code=2 fw=esoc0 |
| pil_notif | target_keyword |  | None |    Binder:9229_3-9837  [000] ....  1073.348304: pil_notif: event_name=after_send_notif code=2 fw=esoc0 |
| gpio_value | critical_unclassified |  | 1270 |    Binder:9229_3-9837  [000] ....  1073.348332: gpio_value: 1270 get 1 |
| gpio_value | critical_unclassified |  | 1270 |    Binder:9229_3-9837  [000] ....  1073.348409: gpio_value: 1270 set 0 |
| gpio_direction | critical_unclassified |  | 1270 |    Binder:9229_3-9837  [000] ....  1073.348411: gpio_direction: 1270 out (0) |
| gpio_value | critical_unclassified |  | 1270 |    Binder:9229_3-9837  [002] ....  1073.528561: gpio_value: 1270 set 1 |
| gpio_direction | critical_unclassified |  | 1270 |    Binder:9229_3-9837  [002] ....  1073.528567: gpio_direction: 1270 out (0) |
| gpio_value | critical_unclassified |  | 135 |    Binder:9229_3-9837  [003] ....  1073.680188: gpio_value: 135 set 1 |
| gpio_direction | critical_unclassified |  | 135 |    Binder:9229_3-9837  [003] ....  1073.680193: gpio_direction: 135 out (0) |

## Next

build the next gate around GPIO135 assertion with GPIO142/PCIe response absence as the explicit blocker

## Safety

No Wi-Fi HAL start, scan/connect, credential use, DHCP/routes, external ping,
PMIC write, userspace GPIO line request/hold, direct eSoC ioctl, direct GDSC
write, flash, boot image write, or partition write occurred.
