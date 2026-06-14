# Native Init V1317 Lower Trace-Line Classifier

## Summary

- Cycle: `V1317`
- Type: host-only classifier
- Decision: `v1317-sample-background-noise-classified-next-critical-only-dump`
- Result: PASS
- Evidence:
  - `tmp/wifi/v1317-lower-trace-line-classifier/manifest.json`
  - `tmp/wifi/v1317-lower-trace-line-classifier/summary.md`
- Script: `scripts/revalidation/native_wifi_lower_trace_line_classifier_v1317.py`

V1317 classifies the V1316 lower trace-line sample without contacting the device.
It confirms that V1316 captured lower-event counts while `pm-service` reached
`/dev/subsys_esoc0` / `mdm_subsys_powerup`, but the stored line sample is not yet
specific enough to identify SDX50M first-power-on rails or target GPIOs.

## Result

| field | value |
| --- | --- |
| V1316 decision | v1316-critical-first-power-on-events-captured |
| V1316 lower total / critical / noise | 81174 / 3936 / 77238 |
| classified line count | 260 |
| critical sample lines | 10 |
| target keyword lines | 0 |
| target GPIO lines | 0 |
| event counts | {"clk_enable": 16, "clk_enable_complete": 16, "clk_prepare": 16, "clk_prepare_complete": 16, "gpio_value": 6, "irq_handler_entry": 94, "irq_handler_exit": 92, "regulator_enable": 1, "regulator_enable_complete": 1, "regulator_set_voltage": 1, "regulator_set_voltage_complete": 1} |
| category counts | {"background_apps_rsc": 2, "background_display": 2, "background_sdcard": 24, "background_storage_ufs": 82, "background_timer": 16, "background_unclassified": 100, "background_usb_dwc3": 26, "critical_unclassified": 6, "generic_pmic_regulator": 2} |
| GPIO counts | {"96": 6} |

The stored sample contains critical lines for `ufs_phy_gdsc`, `pm8150l_l3`,
and GPIO `96`, but no lines containing SDX50M/PCIe/MHI/WLAN/CNSS target
keywords and no target GPIO `135`, `142`, or `1270`. The broad IRQ/clock
capture also consumed most of the saved trace-line budget.

## Decision

V1318 should be a narrower bounded live collector, not a lower mutation.
It should drop broad IRQ/clock events and preserve more critical-only
`regulator`, `gpio`, `power`, and `msm_pil_event` lines around the same
late `per_proxy` PM-service path.

## Safety

Host-only classifier. No device command, tracefs write, PM-service trigger,
PMIC write, userspace GPIO line request/hold, direct eSoC ioctl, direct GDSC
write, Wi-Fi HAL start, scan/connect, credential use, DHCP/routes, external
ping, flash, boot image write, or partition write occurred.
