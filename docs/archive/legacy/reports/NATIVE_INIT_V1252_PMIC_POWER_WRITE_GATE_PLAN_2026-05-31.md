# V1252 PMIC/Power-surface Write-gate Plan

- report: `docs/reports/NATIVE_INIT_V1252_PMIC_POWER_WRITE_GATE_PLAN_2026-05-31.md`
- classifier: `scripts/revalidation/native_wifi_pmic_power_write_gate_plan_v1252.py`
- evidence: `tmp/wifi/v1252-pmic-power-write-gate-plan/manifest.json`
- result: `v1252-bounded-pmic-power-write-gate-plan-ready`
- pass: `true`

## Scope

V1252 is host-only. It reads existing V1251/V1247/V1244 evidence, the SDX50M
research note, and the current helper source to choose the next bounded
source/build gate. It does not execute a device command and does not mutate
device state.

## Evidence Checks

| Check | Result |
| --- | --- |
| V1251 manifest pass / candidate decision | pass |
| V1251 debugfs cleanup | pass |
| V1251 read contract ready | pass |
| V1251 native reproduction candidate | pass |
| V1251 zero-action markers | pass |
| PMIC soft-reset line remains unclaimed | pass |
| PCIe GDSC lines remain `0mV` | pass |
| `mdm3_state=OFFLINING` | pass |
| GPIO142 IRQ count remains `0` | pass |
| Android/native power-surface delta documented | pass |
| Prior unsafe candidates rejected | pass |
| SDX50M research maps soft-reset to PM8150L GPIO9 | pass |
| helper `--allow-pmic-soft-reset-write` remains reserved fail-closed | pass |

## Current Blocker Surface

| Field | Value |
| --- | --- |
| PMIC soft-reset line | `pin 7 (gpio9): (MUX UNCLAIMED) c440000.qcom,spmi:qcom,pm8150l@4:pinctrl@c000:1270` |
| PCIe 1 GDSC line | `pcie_1_gdsc 0 2 0 0mV 0mA 0mV 0mV` |
| PCIe 0 GDSC line | `pcie_0_gdsc 0 1 0 0mV 0mA 0mV 0mV` |
| `mdm3_state` | `OFFLINING` |
| GPIO142 IRQ count | `0` |

## Selected Next Gate

V1253 should be source/build-only:

- helper version: `a90_android_execns_probe v261`
- mode: `wifi-companion-pmic-power-surface-write-gate-preflight`
- purpose: add a fail-closed two-stage PMIC GPIO9 line-hold proof before any
  subsystem trigger

The helper must first verify the V1251 read contract, locate a PM8150L
`gpiochip` candidate without writing, and map PMIC GPIO9 only if chip identity
and line offset are exact. The expected mapping from current evidence is global
line `1270`, PM8150L GPIO range `1263-1273`, offset `7`, but V1253 must still
derive and print that mapping from live surfaces before any later live write.

## Later Live Gate Shape

The first later live write proof should only hold PMIC GPIO9 low through the
kernel GPIO character-device API for a bounded window, sample the read surfaces,
close the fd for cleanup, and verify postflight state. It must not open
`/dev/subsys_esoc0`, start PM actors, start CNSS/HAL, scan/connect, use
credentials, DHCP/routes, or external ping.

Only after that isolated line-hold proof changes the read surface as expected
should a separate cycle combine the PMIC line hold with the existing PM actor /
`/dev/subsys_esoc0` trigger path.

## Explicit Rejections

- no `/sys/class/gpio` export/write
- no debugfs pinctrl write
- no debugfs regulator write
- no direct PCIe GDSC enable
- no blind `/dev/subsys_esoc0` retry
- no Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping

## Validation

| Command | Result |
| --- | --- |
| `python3 -m py_compile scripts/revalidation/native_wifi_pmic_power_write_gate_plan_v1252.py` | pass |
| `python3 scripts/revalidation/native_wifi_pmic_power_write_gate_plan_v1252.py run` | pass |

## Safety

- host-only classifier; no device command or mutation executed
- no PMIC/GPIO/debugfs/regulator write, eSoC ioctl, PM actor, CNSS actor, Wi-Fi
  HAL, scan/connect, credentials, DHCP/routes, external ping, reboot, flash,
  boot image write, or partition write
