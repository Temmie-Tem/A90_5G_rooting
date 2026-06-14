# Native Init V1453 Provider-Trigger Micro Handoff Classifier

## Summary

- Cycle: `V1453`
- Type: host-only classifier over V1452 provider-trigger micro evidence
- Decision: `v1453-provider-window-low-no-downstream`
- Result: PASS
- Reason: V1452 safely sampled the provider-trigger window without explicit RC1 debugfs writes; GPIO135/GPIO142 and endpoint IRQs stayed low and no RC1/MHI/WLFW/wlan0 progress appeared
- Evidence: `tmp/wifi/v1452-wifi-test-boot-provider-trigger-micro-endpoint-handoff`
- Handoff decision: `v1452-test-boot-provider-trigger-no-downstream-rollback-pass`
- Rollback v724 verified: `True`
- Test boot version verified: `True`

## Provider Window

- micro sample count: `9`
- micro offsets ms: `[0, 11, 21, 31, 39, 44, 50, 100, 150]`
- expected micro count: `True`
- complete micro offsets: `True`
- context sample count: `1`
- modem `__subsystem_get` ts: `3.253644`
- esoc0 `__subsystem_get` ts: `9.10303`
- explicit RC1 debugfs test ts: `None`
- trigger chunk prefix not exact provider line: `True`

## Endpoint State

- GPIO135 all low: `True`
- GPIO142 all low: `True`
- MDM status IRQ all zero: `True`
- PCIe wake IRQ all zero: `True`
- pcie1 GDSC all 0mV in context sample: `True`
- pcie1 clocks all zero-enable in context sample: `True`
- pcie link-state unreadable micro samples: `9`
- pcie current-link-state unreadable micro samples: `9`

## Progress Classification

- explicit RC1 test write observed: `False`
- `rc1_phy_ready`: `False`
- `rc1_l0`: `False`
- `rc1_link_failed`: `False`
- `mhi_progress`: `False`
- `wlfw_progress`: `False`
- `fw_ready_progress`: `False`
- `wlan0_present`: `False`
- `connect_ready`: `False`

## Interpretation

The rollbackable Wi-Fi test-boot strategy is valid for this phase: it can
capture boot-time lower bring-up evidence and return to the main v724 image.
V1452 did not prove Wi-Fi bring-up. It proved the opposite boundary: while
the PM/CNSS path reached the esoc0 provider region, AP2MDM GPIO135 and
MDM2AP GPIO142 stayed low, endpoint IRQs stayed at zero, pcie1 did not expose
a readable link state, and no RC1/MHI/WLFW/BDF/FW-ready/`wlan0` marker
appeared.

One measurement weakness remains: the PID1 kmsg reader records the raw chunk
that triggered the match, so the stored line prefix can show an earlier
cnss-daemon netlink message even when the chunk also contains the provider
line. The next image should split kmsg chunks into exact lines and extend
the read-only provider window beyond `150ms`.

## Safety Scope

This classifier was host-only. It did not issue device commands, flash,
reboot, start Wi-Fi HAL, scan/connect, use credentials, configure
DHCP/routes, or perform external ping.

## Next

V1454 should be source/build-only and create an exact-line provider-trigger
test boot. It should split `/proc/kmsg` chunks into individual lines, trigger
only on the exact `__subsystem_get: esoc0` or `mdm_subsys_powerup` line, keep
the run read-only, and extend endpoint samples to include at least `250ms`,
`300ms`, `500ms`, and `1000ms` after the exact provider trigger.
