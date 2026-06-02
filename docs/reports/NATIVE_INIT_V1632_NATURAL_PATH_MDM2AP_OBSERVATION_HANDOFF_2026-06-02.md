# Native Init V1632 Natural-path MDM2AP Observation Handoff

## Summary

- Cycle: `V1632`
- Type: one-run rollbackable natural-path live observation
- Decision: `v1632-natural-path-observation-incomplete`
- Result: BLOCKED
- Contract label: `natural-path-observation-incomplete`
- Reason: natural provider/PON/AP2MDM path was observed and short-window samples stayed low, but the required mdm2ap_timing IRQ-delta contract evidence was not collected
- Evidence: `tmp/wifi/v1632-natural-path-mdm2ap-observation-handoff`
- Test boot image: `tmp/wifi/v1630-natural-path-mdm2ap-observation-test-boot/boot_linux_v1630_natural_mdm2ap.img`
- Rollback image: `stage3/boot_linux_v724.img`
- Rollback ok: `True`

## Contract Checks

- `provider_trigger_seen`: `True`
- `pil_esoc_seen`: `True`
- `pon_low_seen`: `True`
- `pon_high_seen`: `True`
- `ap2mdm_seen`: `True`
- `gpio142_trace_seen`: `False`
- `gpio142_irq_delta`: `-1`
- `errfatal_irq_delta`: `-1`
- `mdm_status_zero_sample_count`: `14`
- `errfatal_zero_sample_count`: `1`
- `gpio142_low_sample_count`: `14`
- `limited_silent_window_evidence`: `True`
- `timing_powerup_seen`: `False`
- `timing_complete`: `False`
- `sample_count`: `0`
- `safety_zero`: `True`
- `forbidden_markers_seen`: `[]`

## Downstream Context

- `pcie_rc1_transition_seen`: ``
- `mhi_bus_max`: ``
- `wlfw_kmsg_max`: ``
- `wlan0_seen`: ``

## Safety Scope

This run observes the natural `__subsystem_get(esoc0)` provider path only.
It does not force RC1 enumerate, write pci-msm debugfs case values, spoof
ONLINE/system-info, write PMIC/GPIO/GDSC/regulator state, issue eSoC
notify/`BOOT_DONE`, rescan PCI, bind/unbind platforms, start Wi-Fi HAL,
scan/connect, use credentials, run DHCP/routes, or external ping.

## Next

Inspect evidence before any further live mutation.
