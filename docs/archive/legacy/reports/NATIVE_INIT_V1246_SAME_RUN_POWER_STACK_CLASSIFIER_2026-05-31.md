# V1246 Same-run Stack + PMIC/GDSC Classifier

- report: `docs/reports/NATIVE_INIT_V1246_SAME_RUN_POWER_STACK_CLASSIFIER_2026-05-31.md`
- classifier: `scripts/revalidation/native_wifi_same_run_power_stack_classifier_v1246.py`
- evidence: `tmp/wifi/v1246-same-run-power-stack-classifier/manifest.json`
- result: `v1246-same-run-mdm-powerup-pmic-gdsc-silent`
- pass: `true`

## Scope

V1246 is host-only. It tightens V1245 by proving that V1243 already contains
same-run evidence: the same late-`per_proxy` observer window sees the
`pm-service` Binder thread blocked in `mdm_subsys_powerup` and simultaneously
sees PM8150L/GDSC/GPIO142/PCI/MHI/`wlan0` remain silent.

No device command or mutation is executed.

## Findings

| Field | Value |
| --- | --- |
| Same-run powerup phases | `12` |
| First same-run phase | `late_per_proxy_poll_00` |
| Binder wchan | `mdm_subsys_powerup` |
| PM8150L soft-reset line | `pin 7 (gpio9): (MUX UNCLAIMED) c440000.qcom,spmi:qcom,pm8150l@4:pinctrl@c000:1270` |
| PCIe GDSC lines | `pcie_1_gdsc` and `pcie_0_gdsc` remain `0mV` |
| GPIO142 / PCI / MHI / wlan0 | `gpio142=0`, `pci=0`, `mhi=0`, `pipe=0`, `wlan0=0` |
| Android contrast | Android-positive evidence claims PM8150L `gpio9` and reaches PCIe RC1/WLAN-PD/ICNSS-QMI/FW-ready/`wlan0` |

## Interpretation

V1246 removes the last timing ambiguity in the current evidence set. The
PM8150L/GDSC silence is not from a different run, and not merely a pre-trigger
snapshot. It is observed in the same late-`per_proxy` phases where `pm-service`
Binder threads are already blocked in `mdm_subsys_powerup`.

The next useful gate is V1247: choose the first bounded PMIC pinctrl
reproduction path. That should be source/Android-contract planning first, then
only a tightly bounded write gate if the exact PM8150L pinctrl/regulator surface
is defensible. Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external
ping remain blocked until lower readiness appears.

## Validation

| Command | Result |
| --- | --- |
| `python3 -m py_compile scripts/revalidation/native_wifi_same_run_power_stack_classifier_v1246.py` | pass |
| `python3 scripts/revalidation/native_wifi_same_run_power_stack_classifier_v1246.py run` | pass |

## Safety

- host-only classifier; no device command or mutation executed
- no Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, Wi-Fi bring-up, flash, boot image write, or partition write
