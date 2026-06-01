# Native Init V1559 Android Pre-Endpoint Order Classifier

## Summary

- Cycle: `V1559`
- Type: host-only existing-evidence ordering classifier
- Decision: `v1559-ap2mdm-before-bdf-gap-endpoint-order-caveat`
- Result: `PASS`
- Reason: Android-good shows GPIO135/AP2MDM before BDF while native has AP-side RC1 power/refclk/PERST but no AP2MDM/endpoint response; retained Android IRQ/L0 evidence is late and must not be treated as first-L0 ordering
- Evidence: `tmp/wifi/v1559-android-pre-endpoint-order-classifier`

## Inputs

| input | path |
| --- | --- |
| native_v1552 | tmp/wifi/v1552-rc1-endpoint-response-tracefs-live/manifest.json |
| android_v1555 | tmp/wifi/v1555-android-good-minimal-trace-reference/manifest.json |
| native_v1557 | tmp/wifi/v1557-native-endpoint-long-hold-handoff/manifest.json |

## Comparison

| signal | android_v1555 | native | interpretation |
| --- | --- | --- | --- |
| esoc0/provider trigger | 43.547935 | provider=True modem=True | both routes reach a lower trigger |
| GPIO135/AP2MDM | 43.891220 | 0 | Android GPIO135 occurs +0.343285s from esoc0 and -0.622807s before BDF; native count stays zero |
| GPIO102/PERST | 248.790678/248.797650 | 2114.234879/2114.240612 | both can toggle PERST-like GPIO102 |
| pcie1 AP-side power/refclk/pipe | not in V1555 minimal trace | 2114.235963/2114.236190/2114.239511 | native AP-side pcie1 prerequisites are present |
| GPIO104/IRQ252 | trace=248.790386 sample=249.230000 | delta=0 count=0 | Android retained IRQ252 is +199.015111s after wlan0; native stays zero |
| GPIO142/IRQ290 | trace=250.786772 sample=252.890000 | delta=0 count=0 | Android retained IRQ290 is +201.011497s after wlan0; native stays zero |
| lower Wi-Fi | WLFW=43.444373 BDF=44.514027 FW=49.428211 wlan0=49.775275 | RC1=True L0=False MHI=False | firmware/MHI/WLFW remains downstream for native until endpoint response exists |

## Derived Checks

| check | value |
| --- | --- |
| android_ap2mdm_before_bdf | True |
| android_endpoint_late_vs_wlan0 | True |
| native_ap_side_ready | True |
| native_endpoint_silent | True |

## Interpretation

Existing evidence can order one important Android-good signal: GPIO135/AP2MDM is asserted after the esoc0 trigger and before BDF download. Native evidence already proves AP-side pcie1 power/refclk/pipe/PERST activity, but GPIO135/AP2MDM, GPIO104/WAKE, GPIO142/MDM2AP, IRQ252, IRQ290, L0, MHI, WLFW, BDF, FW-ready, and `wlan0` remain absent.

Existing V1555 evidence cannot prove that retained IRQ252/IRQ290/L0 are the first lower-Wi-Fi-enabling events, because those excerpts occur after the first retained `wlan0` lines. They are still useful positive endpoint proof, but not first-L0 ordering proof.

## Next Gate

- Recommended cycle: `V1560`
- Type: host-only/source-build or bounded read-only reference, no connect-side actions
- Focus: AP2MDM assertion/effective-level gap before BDF rather than late retained IRQ252/IRQ290 ordering

### Requirements

- treat Android GPIO135/AP2MDM before BDF as the earliest currently proven discriminating signal
- do not use V1555 late IRQ252/IRQ290/L0 excerpts as first-L0 proof
- explain why native provider/RC1 path does not produce GPIO135/AP2MDM or endpoint wake/status despite AP-side pcie1 power/refclk/PERST
- keep Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, PMIC/GPIO/GDSC direct writes, eSoC notify/BOOT_DONE spoof, global PCI rescan, and platform bind/unbind blocked

## Safety Scope

This classifier is host-only. It performs no device command, flash, reboot, partition write, Wi-Fi HAL start, scan/connect, credential handling, DHCP/routes, external ping, PMIC/GPIO/GDSC write, eSoC notify/BOOT_DONE spoof, pci-msm debugfs write, global PCI rescan, or platform bind/unbind.
