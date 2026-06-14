# V1291 Static GPIO Parity Classifier

- date: 2026-05-31
- scope: host-only evidence classifier
- script: `scripts/revalidation/native_wifi_v1290_static_gpio_parity_classifier_v1291.py`
- evidence: `tmp/wifi/v1291-static-gpio-parity-classifier/manifest.json`
- result: `v1291-static-gpio-parity-dynamic-power-gap`
- pass: `true`

## Purpose

V1290 added exact no-write TLMM GPIO target scans around the bounded PM-service
`/dev/subsys_esoc0` response window. This classifier compares that native
surface against Android-positive evidence to decide whether static GPIO shape is
still a plausible shortest blocker.

## Result

V1291 passes. Static TLMM GPIO shape is no longer the shortest blocker:

- native GPIO135: `gpio135 : out 0 16mA no pull`
- Android GPIO135: `gpio135 : out 0 16mA no pull`
- native GPIO142: `gpio142 : in  0 8mA no pull`
- Android GPIO142: `gpio142 : in  0 8mA no pull`

V1287 had already demoted PMIC9 static shape. The remaining gap is dynamic:
after PM-service enters the eSoC path, native PCIe GDSC still stays at `0mV`
and GPIO142/PCIe/MHI/WLFW/SDX50M/`wlan0` response remains absent.

## Checks

| check | result |
|---|---|
| V1290 live path valid | pass |
| V1290 klogctl/syslog collector valid | pass |
| TLMM GPIO135 static parity with Android | pass |
| TLMM GPIO142 static parity with Android | pass |
| PMIC9 demoted by V1287 | pass |
| native PCIe GDSC still zero | pass |
| native downstream response absent | pass |
| Android-positive contrast present | pass |
| safety clean | pass |

## Key Evidence

| field | value |
|---|---|
| V1290 decision | `v1290-pm-esoc0-trigger-sampled-mdm2ap-silent-reboot-required` |
| sample count | `14` |
| kmsg source | `syslog-read-all` |
| GPIO142 IRQ count | `0` |
| PCI devices | `0` |
| MHI bus count | `0` |
| MHI pipe | `false` |
| `wlan0` | `false` |
| PCIe/MHI/WLFW/SDX50M kmsg counts | `0/0/0/0` |
| PCIe GDSC | `pcie_1_gdsc=0mV`, `pcie_0_gdsc=0mV` |

Android-positive contrast remains present: Android reaches PCIe RC1 link
initialization, WLAN-PD, ICNSS QMI, FW ready, and `wlan0`.

## Safety

- host-only classifier; no device command or mutation executed
- no PMIC write
- no userspace GPIO line request or hold
- no direct eSoC ioctl
- no new daemon/HAL start
- no scan/connect, credentials, DHCP/routes, or external ping
- no flash, boot image write, or partition write

## Verification

```bash
python3 -m py_compile scripts/revalidation/native_wifi_v1290_static_gpio_parity_classifier_v1291.py
python3 scripts/revalidation/native_wifi_v1290_static_gpio_parity_classifier_v1291.py run
```

## Next

V1292 should classify dynamic PCIe/GDSC/eSoC power sequencing observability
before any PMIC write, userspace GPIO hold, direct eSoC ioctl, or Wi-Fi bring-up
gate.
