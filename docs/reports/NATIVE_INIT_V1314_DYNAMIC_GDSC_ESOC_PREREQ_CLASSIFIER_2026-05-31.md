# Native Init V1314 Dynamic GDSC/eSoC Prerequisite Classifier

## Summary

- Cycle: `V1314`
- Type: host-only classifier
- Decision: `v1314-provider-internal-first-power-on-trace-gate-selected`
- Result: PASS
- Evidence:
  - `tmp/wifi/v1314-dynamic-gdsc-esoc-prereq-classifier/manifest.json`
  - `tmp/wifi/v1314-dynamic-gdsc-esoc-prereq-classifier/summary.md`
- Script: `scripts/revalidation/native_wifi_dynamic_gdsc_esoc_prereq_classifier_v1314.py`

V1314 classifies the next safe dynamic prerequisite after V1313 proved the full lower-sequence window: `pm-service` reaches `/dev/subsys_esoc0` and blocks in `mdm_subsys_powerup`, but PCIe GDSC, GPIO142/MDM status, PCI/MHI, `ks`, WLFW, and `wlan0` still do not transition.

## Result

| field | value |
| --- | --- |
| V1313 summary samples | `81` |
| V1313 summary end marker | `true` |
| helper stdout truncated | `false` |
| `mdm_subsys_powerup` seen | `true` |
| MDM status / PCI / MHI max | `0 / 0 / 0` |
| MHI pipe / `ks` / `wlan0` | `false / 0 / false` |
| PCIe1 GDSC | `0mV` |
| PCIe0 GDSC | `0mV` |
| PMIC/TLMM static surfaces | already closed by V1276/V1291/V1310 |

The selected prerequisite is not a direct lower mutation. The safest next proof is provider-internal first-power-on event visibility:

```text
existing bounded PM-service path
  → mdm_subsys_powerup
  → tracefs static events for regulator/gpio/irq/clk/power/PIL
  → classify whether first-power-on reaches PMIC/GPIO/GDSC operations
```

## Checks

| check | result |
| --- | --- |
| V1313 full-window no-transition | pass |
| V1313 PCIe GDSC stayed zero | pass |
| V1313 lower safety markers clean | pass |
| static PMIC/TLMM surfaces already closed | pass |
| prior dense sampler need satisfied | pass |
| provider power-up contract present in docs/source | pass |
| trace event source files present | pass |
| tracefs read feasibility proven by V776 | pass |

## Decision

V1314 rejects these next gates:

- direct PMIC GPIO9 write or hold
- userspace TLMM GPIO135/GPIO142 line request or hold
- direct PCIe GDSC regulator write
- direct `ESOC_CMD_EXE` / eSoC ioctl retry
- Wi-Fi HAL, scan, connect, credentials, DHCP, or external ping before WLFW/`wlan0` readiness

V1315 should implement a targeted tracefs-event preflight for:

- `regulator:regulator_enable*` / `regulator_set_voltage*`
- `gpio:gpio_direction` / `gpio_value`
- `irq:irq_handler_entry` / `irq_handler_exit`
- `clk:clk_enable*` / `clk_prepare*`
- `power:power_domain_target` / `device_pm_callback_*`
- `msm_pil_event:pil_event` / `pil_notif` / `pil_func`

V1316 can then run a bounded tracefs event collector around the same late `per_proxy` PM-service path, still without Wi-Fi HAL/connect or lower writes.

## Safety

Host-only classifier. No device command, PMIC write, GPIO line request/hold, direct eSoC ioctl, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, flash, boot image write, or partition write occurred.
