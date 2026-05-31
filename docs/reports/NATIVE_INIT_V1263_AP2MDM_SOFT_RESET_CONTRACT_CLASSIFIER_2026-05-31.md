# V1263 AP2MDM Soft-reset Contract Classifier

- report: `docs/reports/NATIVE_INIT_V1263_AP2MDM_SOFT_RESET_CONTRACT_CLASSIFIER_2026-05-31.md`
- runner: `scripts/revalidation/native_wifi_ap2mdm_soft_reset_contract_classifier_v1263.py`
- evidence: `tmp/wifi/v1263-ap2mdm-soft-reset-contract-classifier/manifest.json`
- result: `v1263-kernel-owned-soft-reset-line-request-rejected`
- pass: `true`

## Scope

V1263 is host-only. It classifies existing V1262, V1239, V1242, and V1243
evidence. It does not execute a bridge/device command, create a live device node,
request a GPIO line, write PMIC/GPIO/debugfs or regulator state, open
`/dev/subsys_esoc0`, start PM/CNSS/HAL actors, scan/connect, use credentials,
DHCP/routes, external ping, reboot, flash, boot image write, or partition write.

## Evidence Inputs

| Input | Path | Decision |
| --- | --- | --- |
| V1262 | `tmp/wifi/v1262-gpiochip-line-info-live/manifest.json` | `v1262-gpiochip-line-info-pass` |
| V1239 | `tmp/wifi/v1239-post-esoc0-powerup-gap-classifier/manifest.json` | `v1239-gap-is-after-pm-service-esoc0-before-gpio142-pcie-wlfw` |
| V1242 | `tmp/wifi/v1242-late-per-proxy-response-sampler-live/manifest.json` | `v1242-pm-esoc0-trigger-sampled-mdm2ap-silent-reboot-required` |
| V1243 | `tmp/wifi/v1243-sdx50m-power-prereq-response-live/manifest.json` | `v1243-pm-esoc0-trigger-sampled-mdm2ap-silent-reboot-required` |

## Findings

| Field | Value |
| --- | --- |
| line offset | `7` |
| global line | `1270` |
| line flags | `0x1` |
| `GPIOLINE_FLAG_KERNEL` | `1` |
| line consumer | `AP2MDM_SOFT_RESET` |
| direct userspace line request | rejected |
| downstream response evidence | no GPIO142/PCIe/MHI/WLFW response in V1239/V1242/V1243 chain |

## Interpretation

V1263 rejects the previous direct userspace PMIC GPIO9 line request/hold idea. The
line is already owned by the kernel as `AP2MDM_SOFT_RESET`, so claiming it from
userspace would fight the ext-mdm provider rather than repair it.

The remaining Wi-Fi blocker is still below the already reproduced PM-service
`/dev/subsys_esoc0` entry: native reaches `mdm_subsys_powerup`, but does not get
the downstream GPIO142/PCIe/MHI/WLFW response that Android reaches.

## Next

V1264 should plan a read-only ext-mdm/AP2MDM contract observer. It should avoid
userspace GPIO line request/hold and instead correlate existing kernel-owned line
state, GPIO142 IRQ count, PCIe RC1/MHI surfaces, and `mdm_subsys_powerup` timing
around the existing PM-service path.

## Safety

- host-only classifier; no device command
- no GPIO line request or PMIC write
- no eSoC ioctl, PM actor, CNSS actor, Wi-Fi HAL, scan/connect, credentials,
  DHCP/routes, external ping, reboot, flash, boot image write, or partition write
