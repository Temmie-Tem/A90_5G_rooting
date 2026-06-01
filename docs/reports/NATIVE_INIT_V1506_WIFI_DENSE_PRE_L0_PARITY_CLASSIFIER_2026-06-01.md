# Native Init V1506 Wi-Fi Dense Pre-L0 Parity Classifier

## Summary

- Cycle: `V1506`
- Type: host-only classifier over V1505 live handoff evidence
- Decision: `v1506-dense-pre-l0-captures-off-state-but-overruns-micro-window`
- Result: PASS
- Reason: V1505 captured focused regulator/clock/GPIO state and still failed before L0, but exact-match dense reads overrun the intended micro window
- Evidence: `tmp/wifi/v1505-wifi-dense-pre-l0-parity-handoff`

## Handoff Result

- V1505 decision: `v1505-test-boot-downstream-progress-rollback-pass`
- handoff pass: `True`
- rollback ok: `True`
- progress decision: `rc1-ltssm-link-failed-no-l0`
- RC1 progress/link failed/L0: `True/True/False`
- MHI/WLFW/BDF/FW-ready/wlan0: `False/False/False/False/False`

## Dense Focused Reads

- labels present: `9` / `9`
- focused marker present for every label: `True`
- `pcie_1_gdsc` off for every label: `True`
- PCIe1 focused clocks off for every label: `True`
- refgen clocks available for every label: `True`
- GPIO102/103/104/135/142 expected for every label: `True`
- GPIO142 mdm-status IRQ stays zero: `True`

## Timing Caveat

- first sample actual micro elapsed: `0` ms
- second sample actual micro elapsed: `1007` ms
- max sample actual micro elapsed: `12564` ms
- dense sampler overran intended micro window: `True`

The dense exact-match implementation is diagnostically useful but too slow for 0/1/2/5/10/20/50/100/150ms timing. Each sample scans several debugfs files repeatedly, so labels after 0ms do not represent their nominal offsets.

## Dmesg Classification

- LTSSM states: `LTSSM_DETECT_QUIET, LTSSM_POLL_ACTIVE, LTSSM_POLL_COMPLIANCE`
- case after esoc0: `30.189` ms
- link failed after case: `114.832` ms
- link failed marker: `True`
- L0/MHI/WLFW/BDF/FW-ready/wlan0: `False/False/False/False/False/False`

## Interpretation

V1505 reinforces the pre-L0 endpoint-response blocker: RC1 reaches PHY/LTSSM and fails before L0, while focused state reads show `pcie_1_gdsc` and PCIe1 clocks off with refgen available and GPIO142 inactive. However, because the dense exact-match reads overrun the micro schedule, this cannot be treated as precise first-150ms timing evidence.

## Safety Scope

This classifier is host-only. It performs no device command, flash, reboot, partition write, Wi-Fi HAL start, scan/connect, credential handling, DHCP/routes, external ping, PMIC/GPIO/GDSC write, eSoC notify/`BOOT_DONE` spoof, global PCI rescan, or platform bind/unbind.

## Next

- V1507 should replace per-needle exact-match scanning with a batched per-file micro sampler so each debugfs file is read at most once per sample.
- Do not move to firmware/MHI/WLFW/scan/connect work until RC1 L0 and PCI enumeration exist.
