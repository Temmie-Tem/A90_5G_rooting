# Native Init V1502 Wi-Fi Pre-L0 Parity Classifier

## Summary

- Cycle: `V1502`
- Type: host-only classifier over V1501 live handoff evidence
- Decision: `v1502-pre-l0-parity-confirms-rc1-link-fail-with-endpoint-lines-low`
- Result: PASS
- Reason: V1501 evidence confirms corrected RC1 enumerate reaches PHY/LTSSM but endpoint-side lines remain non-responsive and no L0/MHI/WLFW/wlan0 appears
- Evidence: `tmp/wifi/v1501-wifi-pre-l0-parity-handoff`

## V1501 Handoff Result

- V1501 manifest decision: `v1501-test-boot-downstream-progress-rollback-pass`
- handoff pass: `True`
- rollback ok: `True`
- progress decision: `rc1-ltssm-link-failed-no-l0`
- provider trigger: `True`
- modem trigger: `True`
- RC1 progress: `True`
- RC1 L0: `False`
- RC1 link failed: `True`
- MHI/WLFW/BDF/FW-ready/wlan0: `False/False/False/False/False`

## Corrected RC1 Enumerate

- writer summary ok: `True`
- writer line: `rc1_micro_writer_summary pid=620 writer_wait_rc=0 status=0x0 micro_writer rc=0 errno=0 rc_sel_elapsed_ms=7385 case_elapsed_ms=7501`
- LTSSM states: `LTSSM_DETECT_QUIET, LTSSM_POLL_ACTIVE, LTSSM_POLL_COMPLIANCE`
- case after esoc0: `39.336` ms
- PHY ready after case: `5.871` ms
- link failed after case: `114.859` ms

## Micro Endpoint Samples

- expected labels present: `True`
- micro sample count: `9`
- GPIO expected through micro window: `True`
- GPIO104 wake / GPIO142 mdm-status IRQ counts stay zero: `True`
- PCIe1 link-state sysfs unreadable in every micro sample: `True`

| line | state through 0/1/2/5/10/20/50/100/150ms |
|---|---|
| `gpio102` | `out 0` stable = `True` |
| `gpio103` | `in 1` stable = `True` |
| `gpio104` | `in 0` stable = `True` |
| `gpio135` | `out 0` stable = `True` |
| `gpio142` | `in 0` stable = `True` |

## Post Micro Full Sample

- post sample present: `True`
- GPIO142 mdm-status IRQ count: `0`
- pcie_1_gdsc off at 200ms: `True`
- PCIe1 focused clocks off at 200ms: `True`
- PCIe1 refgen available at 200ms: `True`
- focused GPIO expected at 200ms: `True`

## Dmesg Classification

- link failed marker: `True`
- L0 marker: `False`
- MHI marker: `False`
- WLFW marker: `False`
- BDF marker: `False`
- FW-ready marker: `False`
- wlan0 marker: `False`

## Key Lines

- `[    3.393606] [2:pm_proxy_helper:  559] subsys-restart: __subsystem_get(): __subsystem_get: modem count:0`
- `[    9.242694] [0:   Binder:591_3:  612] subsys-restart: __subsystem_get(): __subsystem_get: esoc0 count:0`
- `[    9.281963] [3:           init:  620] PCIe: rc_sel is now: 0x2`
- `[    9.282030] [3:           init:  620] PCIe: TEST: 11`
- `[    9.282088] [3:           init:  620] msm_pcie_enable: PCIe: Assert the reset of endpoint of RC1.`
- `[    9.287901] [3:           init:  620] msm_pcie_enable: PCIe RC1 PHY is ready!`
- `[    9.287916] [3:           init:  620] msm_pcie_enable: PCIe: Release the reset of endpoint of RC1.`
- `[    9.294090] [3:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_DETECT_QUIET`
- `[    9.299226] [3:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_DETECT_QUIET`
- `[    9.304363] [3:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_ACTIVE`
- `[    9.309499] [3:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_ACTIVE`
- `[    9.314634] [3:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_ACTIVE`
- `[    9.319770] [3:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_ACTIVE`
- `[    9.324906] [3:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_ACTIVE`
- `[    9.330076] [3:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.335214] [3:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.340354] [3:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.345492] [3:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.350630] [3:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.355767] [3:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.360903] [3:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.366039] [3:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.371174] [3:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.376309] [3:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.381446] [3:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.386582] [3:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.391720] [3:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.396857] [3:           init:  620] msm_pcie_enable: PCIe RC1: LTSSM_STATE: LTSSM_POLL_COMPLIANCE`
- `[    9.396873] [3:           init:  620] msm_pcie_enable: PCIe: Assert the reset of endpoint of RC1.`
- `[    9.396889] [3:           init:  620] msm_pcie_enable: PCIe RC1 link initialization failed (LTSSM_STATE:0x3)`
- `[    9.397205] [3:           init:  620] msm_pcie_sel_debug_testcase: PCIe: RC1 enumeration failed`

## Interpretation

V1501 confirms the intended corrected RC1 enumerate path is no longer the blocker: the write succeeds, the RC1 PHY becomes ready, and LTSSM advances to `POLL_COMPLIANCE`. The failure remains pre-L0: no endpoint response reaches L0, GPIO142/MDM2AP interrupt count stays zero, and no MHI/WLFW/BDF/FW-ready/`wlan0` evidence appears.

The GPIO micro samples cover 0/1/2/5/10/20/50/100/150ms after `case=11`. The focused regulator/clock evidence is currently captured in the 200ms post sample, likely after link failure cleanup, so it should not be over-read as proof of the exact clock/GDSC state during the first 150ms.

## Safety Scope

This classifier is host-only. It performs no device command, flash, reboot, partition write, Wi-Fi HAL start, scan/connect, credential handling, DHCP/routes, external ping, PMIC/GPIO/GDSC write, eSoC notify/`BOOT_DONE` spoof, global PCI rescan, or platform bind/unbind.

## Next

- V1503 should either add dense focused regulator/clock/GDSC sampling into each 0/1/2/5/10/20/50/100/150ms micro sample or capture an Android-good RC1 parity reference with the same fields.
- Keep firmware/MHI/WLFW/scan/connect work parked until RC1 L0 and PCI enumeration exist.
