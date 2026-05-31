# V1247 PMIC Pinctrl Reproduction Plan

- report: `docs/reports/NATIVE_INIT_V1247_PMIC_PINCTRL_REPRO_PLAN_2026-05-31.md`
- classifier: `scripts/revalidation/native_wifi_pmic_pinctrl_repro_plan_v1247.py`
- evidence: `tmp/wifi/v1247-pmic-pinctrl-repro-plan/manifest.json`
- result: `v1247-select-fail-closed-pmic-preflight-before-write`
- pass: `true`

## Scope

V1247 is host-only. It does not execute a device command and does not mutate the
device. The goal is to choose the first defensible PMIC pinctrl reproduction
path after V1246 proved that the same live run reaches `mdm_subsys_powerup`
while PM8150L soft-reset `gpio9`, PCIe GDSC, GPIO142, PCI/MHI, and `wlan0`
remain silent.

## Findings

| Field | Value |
| --- | --- |
| Same-run native gap | V1246 has 12 late-`per_proxy` phases with `pm-service` in `mdm_subsys_powerup` and PMIC/GDSC/downstream silence |
| Native PMIC state | `pin 7 (gpio9): (MUX UNCLAIMED) c440000.qcom,spmi:qcom,pm8150l@4:pinctrl@c000:1270` |
| Native GDSC state | `pcie_1_gdsc` and `pcie_0_gdsc` remain `0mV` |
| Android PMIC reference | PM8150L `gpio9` is output/high in Android debug GPIO evidence |
| Android GPIO class reference | `/sys/class/gpio/gpio9`, `/sys/class/gpio/gpio135`, and `/sys/class/gpio/gpio142` are absent |
| DTS soft-reset contract | `qcom,ap2mdm-soft-reset-gpio = <0x3d 0x9 0x0>;` |
| OSRC source gap | Scanned OSRC source does not contain the proprietary `sdx50m_toggle_soft_reset` implementation |

## Candidate Classification

| Candidate | Result | Reason |
| --- | --- | --- |
| Direct `/sys/class/gpio` export/write | Reject | Android does not expose the relevant lines through GPIO class, and PM8150L GPIO9 is a PMIC pinctrl line rather than a proven userspace GPIO contract |
| Debugfs pinctrl/regulator write | Reject | Debugfs is only an observation surface in current evidence; mutating it bypasses vendor eSoC sequencing |
| Direct PCIe GDSC enable | Reject | GDSC silence is downstream evidence; enabling it directly does not reproduce the Android PMIC soft-reset claim or SDX50M sequence |
| Blind `/dev/subsys_esoc0` retry | Reject | V1246 already proves this path blocks in `mdm_subsys_powerup` while PMIC/GDSC/downstream stay silent |
| Fail-closed PMIC preflight helper | Select | It can verify exact PMIC/DTS/native-state invariants first and require a separate explicit write flag before any bounded reproduction attempt |

## Interpretation

The next safe step is not a live PMIC write. The evidence rejects generic GPIO,
debugfs, direct GDSC, and blind retry paths. V1248 should be source/build-only:
add a fail-closed helper gate that can read and validate the PMIC/DTS/native
contract, print the exact intended surface, and refuse to mutate unless a later
cycle adds a separate explicit write approval path.

Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, flash, boot
image write, and partition write remain blocked.

## Validation

| Command | Result |
| --- | --- |
| `python3 -m py_compile scripts/revalidation/native_wifi_pmic_pinctrl_repro_plan_v1247.py` | pass |
| `python3 scripts/revalidation/native_wifi_pmic_pinctrl_repro_plan_v1247.py run` | pass |

## Safety

- host-only classifier; no device command or mutation executed
- no direct sysfs GPIO, debugfs pinctrl/regulator, direct GDSC, or blind eSoC retry action
- no Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, flash, boot image write, or partition write
