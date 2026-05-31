# V1264 ext-mdm/AP2MDM Observer Plan

## Result

- decision: `v1264-ext-mdm-ap2mdm-observer-plan-pass`
- evidence: `tmp/wifi/v1264-ext-mdm-ap2mdm-observer-plan/manifest.json`
- scope: host-only classifier; no device mutation or live command
- next gate: V1265 source/build-only helper `a90_android_execns_probe v264`

## Inputs

| cycle | evidence | result used |
|---|---|---|
| V1263 | `tmp/wifi/v1263-ap2mdm-soft-reset-contract-classifier/manifest.json` | direct userspace PMIC GPIO9 line request/hold rejected |
| V1262 | `tmp/wifi/v1262-gpiochip-line-info-live/manifest.json` | PMIC GPIO9 offset `7` line flags `0x1`, `GPIOLINE_FLAG_KERNEL=1`, consumer `AP2MDM_SOFT_RESET` |
| V1243 | `tmp/wifi/v1243-sdx50m-power-prereq-response-live/manifest.json` | PM-service reaches `/dev/subsys_esoc0`; GPIO142/PCIe/MHI/`wlan0` remain silent in 14 samples |
| V1239 | `tmp/wifi/v1239-post-esoc0-powerup-gap-classifier/manifest.json` | blocker is after PM-service esoc0 entry and before GPIO142/PCIe/WLFW |

## Classification

V1243 already samples the late `per_proxy` / PM-service response window and sees
the PMIC soft-reset pinctrl text.  It does not sample GPIO chardev line-info
flags during that same response window.  V1262 proved the line is kernel-owned,
so the next useful observer is not a userspace line request/hold.  The next unit
must carry the read-only line-info observation into the same bounded PM-service
esoc0 window.

## V1265 Contract

The V1265 helper change should extend the existing late `per_proxy` response
sampler with read-only PMIC GPIO9 `GPIO_GET_LINEINFO_IOCTL` snapshots.

Required samples:

- PMIC GPIO9 line-info flags/name/consumer before, during, and after the
  PM-service `/dev/subsys_esoc0` response window.
- GPIO142 interrupt count and `mdm3` state.
- PCIe RC1 read-only link/runtime surface.
- MHI bus count and `/dev/mhi_0305_01.01.00_pipe_10` existence.
- PM-service `/dev/subsys_esoc0` attempt and `mdm_subsys_powerup` timing evidence.

Hard exclusions:

- No GPIO line request or hold.
- No PMIC write or debugfs control write.
- No direct eSoC ioctl such as `ESOC_NOTIFY` or `ESOC_BOOT_DONE`.
- No new daemon/HAL start beyond the existing bounded PM-service response path.
- No Wi-Fi scan/connect, credentials, DHCP/routes, or external ping.
- No flash, boot image write, or partition write.
