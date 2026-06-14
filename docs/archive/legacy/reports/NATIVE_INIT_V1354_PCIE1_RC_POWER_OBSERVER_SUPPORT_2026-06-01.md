# Native Init V1354 pcie1 RC Power Observer Support

## Summary

- Cycle: `V1354`
- Type: source/build-only observer support
- Decision: `v1354-pcie1-rc-power-observer-support-ready`
- Result: PASS
- Helper source: `stage3/linux_init/helpers/a90_android_execns_probe.c`
- Local helper binary (ignored build artifact): `stage3/linux_init/helpers/a90_android_execns_probe_v281`
- Helper marker: `a90_android_execns_probe v281`
- Helper SHA256: `a68b2fb226d02d949890781ff72af8853958fcfb073a8d055068a48ba50d8c6f`
- Deploy wrapper: `scripts/revalidation/wifi_execns_helper_v281_deploy_preflight_v1354.py`

V1354 adds the read-only pcie1 RC observer support required by the
2026-06-01 eSoC-provider pivot. It does not deploy to the device and does not
run the live lower-window experiment. The live run remains a separate gate.

## Added Observer Fields

The existing MDM2AP timing sampler now records pcie1 RC power/refclk and
endpoint-side signal visibility during the bounded current-route lower window:

| Field | Meaning |
| --- | --- |
| `mdm2ap_timing.pcie1_gdsc_seen` | `pcie_1_gdsc` line was found in regulator/debugfs summaries |
| `mdm2ap_timing.pcie1_gdsc_nonzero_seen` | observed `pcie_1_gdsc` state was not the previous `0mV` pattern |
| `mdm2ap_timing.pcie1_clkref_seen` | clk summary exposed a pcie1 clock/refclk-like line |
| `mdm2ap_timing.pcie1_phy_refgen_seen` | clk summary exposed a PCIe PHY refgen-like line |
| `mdm2ap_timing.pcie1_pipe_clk_seen` | clk summary exposed a pcie1 pipe clock-like line |
| `mdm2ap_timing.gpio102_perst_seen` | debugfs GPIO line for pcie1 PERST was visible |
| `mdm2ap_timing.gpio103_clkreq_seen` | debugfs GPIO line for pcie1 CLKREQ was visible |
| `mdm2ap_timing.gpio104_wake_seen` | debugfs GPIO line for SDX50M WAKE was visible |

Each visible surface also emits an `*_initial` and `*_last` value so the live
observer can classify whether the lower power-up window changes pcie1 RC state.

## Parser/Report Support

`scripts/revalidation/native_wifi_mdm2ap_timing_sampler_live_v1328.py` now
parses the new `mdm2ap_timing.*` keys and includes them in summary rows. This
keeps downstream wrappers able to classify the pcie1 RC surfaces without
changing the bounded live action.

## Safety

- No device command or bridge command was executed for this support cycle.
- No helper deploy, daemon start, Wi-Fi HAL start, scan/connect, credential
  handling, DHCP/routes, external ping, flash, boot image write, or partition
  write was performed.
- The helper additions are read-only: they read regulator/clock/GPIO debug text
  and existing sysfs state only. They do not write sysfs/debugfs, request GPIO
  lines, change GDSC/regulator state, or call eSoC notify/`BOOT_DONE`.

## Validation

```bash
python3 -m py_compile scripts/revalidation/native_wifi_mdm2ap_timing_sampler_live_v1328.py
python3 -m py_compile scripts/revalidation/native_wifi_current_route_mdm2ap_timing_sampler_live_v1345.py scripts/revalidation/native_wifi_current_route_cnss_wlfw_precondition_observer_live_v1351.py scripts/revalidation/wifi_execns_helper_v280_deploy_preflight_v1352.py
scripts/revalidation/build_android_execns_probe_helper.sh tmp/wifi/v1354-execns-helper-v281-build/a90_android_execns_probe_v281
file stage3/linux_init/helpers/a90_android_execns_probe_v281
aarch64-linux-gnu-readelf -d stage3/linux_init/helpers/a90_android_execns_probe_v281
strings stage3/linux_init/helpers/a90_android_execns_probe_v281 | rg 'a90_android_execns_probe v281|pcie1_clkref|gpio102_perst|gpio103_clkreq|gpio104_wake'
```

All validation passed. The build emitted only existing `-Wformat-truncation`
warnings in unrelated `pm_observer_trigger_mdm_power_on` paths.

## Next

Run the separate deploy/live gate:

1. `python3 scripts/revalidation/wifi_execns_helper_v281_deploy_preflight_v1354.py preflight`
2. `python3 scripts/revalidation/wifi_execns_helper_v281_deploy_preflight_v1354.py run --assume-yes --apply --approval-phrase "approve v1354 deploy execns helper v281 only; no daemon start and no Wi-Fi bring-up"`
3. Run the bounded current-route MDM2AP timing sampler with helper v281 and
   classify whether pcie1 GDSC/refclk/PERST/CLKREQ/WAKE changes during the
   existing `pm-service -> subsys_esoc0 -> mdm_subsys_powerup` window.

Keep the 2026-06-01 pivot exclusions active until this read-only observer
justifies a specific bounded mutation.
