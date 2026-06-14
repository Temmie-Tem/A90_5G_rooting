# Native Init V1558 Post-V1557 Next Gate Classifier

## Summary

- Cycle: `V1558`
- Type: host-only evidence/classifier
- Decision: `v1558-next-gate-android-pre-endpoint-sequence-classifier`
- Result: `PASS`
- Reason: same-path TEST:11 and long-hold retries are closed; next work is Android-good pre-endpoint/pre-IRQ sequence comparison

## Inputs

| input | path |
| --- | --- |
| v1523_msm_pcie_static | tmp/wifi/v1523-msm-pcie-test11-vs-normal-path-classifier/manifest.json |
| v1552_native_endpoint_trace | tmp/wifi/v1552-rc1-endpoint-response-tracefs-live/manifest.json |
| v1555_android_good_reference | tmp/wifi/v1555-android-good-minimal-trace-reference/manifest.json |
| v1556_endpoint_comparator | tmp/wifi/v1556-v1555-vs-v1552-endpoint-signal-comparator/manifest.json |
| v1557_native_long_hold | tmp/wifi/v1557-native-endpoint-long-hold-handoff/manifest.json |

## Checks

| check | status | detail |
| --- | --- | --- |
| v1523-test11-shares-common-enable | pass | debugfs TEST:11, sysfs/client enumerate, and endpoint-wake normal paths converge on msm_pcie_enumerate() |
| v1552-native-ap-side-ready-endpoint-silent | pass | native has AP-side pcie1 power/refclk/PERST but no GPIO104/GPIO142/IRQ252/IRQ290/L0 |
| v1555-android-good-has-lower-wifi | pass | Android-good reaches WLFW, BDF, FW-ready, wlan0, and endpoint-positive GPIO/IRQ signals |
| v1556-stable-delta-fixed | pass | host-only comparator fixes Android endpoint-positive versus native endpoint-zero as the stable delta |
| v1557-long-hold-rejects-delay | pass | 280s native test-boot hold still has RC1 link-failed/no-L0 and no endpoint wake/status signal |

## Interpretation

V1557 closes the delayed-response hypothesis for the current native provider/RC1 test-boot route. Combined with V1523, this means the next useful work is not another TEST:11 or long-hold retry: the AP-side enable path is shared enough to reach PHY/LTSSM, but native never receives the endpoint-positive signals Android gets.

The active blocker remains before firmware/MHI/WLFW: Android produces GPIO104/WAKE, GPIO142/MDM2AP, IRQ252, and IRQ290 while native remains endpoint-silent after AP-side power/refclk/PERST activity.

## Next Gate

- Recommended cycle: `V1559`
- Type: host-only first, then read-only reference if needed
- Focus: Android-good pre-endpoint/pre-IRQ sequence versus native provider-driven endpoint-silent path

### Must Compare

- first provider/esoc0 trigger and mdm_subsys_powerup timing
- GPIO135/AP2MDM effective level and trace timing
- GPIO102/PERST assert/release timing
- pcie1 refclk/pipe-clock/GDSC timing
- GPIO104/WAKE and IRQ252 first positive event
- GPIO142/MDM2AP and IRQ290 first positive event
- first RC1 L0 / PCI enumeration / MHI marker if the evidence can order it

### Blocked Retries

- same V1493/V1496 native long-hold retry
- blind pci-msm TEST:11 timing retry
- firmware/MHI/WLFW analysis before RC1 L0 or PCI enumeration

## Safety Scope

This classifier is host-only. It performs no device command, flash, reboot, partition write, Wi-Fi HAL start, scan/connect, credential handling, DHCP/routes, external ping, PMIC/GPIO/GDSC write, eSoC notify/BOOT_DONE spoof, pci-msm debugfs write, global PCI rescan, or platform bind/unbind.
