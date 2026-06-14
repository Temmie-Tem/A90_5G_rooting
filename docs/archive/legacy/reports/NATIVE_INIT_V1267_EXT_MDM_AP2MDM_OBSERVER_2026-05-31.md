# V1267 ext-mdm/AP2MDM Response Observer

## Result

- decision: `v1267-pm-esoc0-trigger-sampled-mdm2ap-silent-reboot-required`
- evidence: `tmp/wifi/v1267-ext-mdm-ap2mdm-observer-live/manifest.json`
- helper: `a90_android_execns_probe v264`
- live action: bounded late `per_proxy` / PM-service response sampler
- post-run recovery: reboot executed, native version returns `A90 Linux init 0.9.68 (v724)`, selftest returns `fail=0`

## New Evidence

| field | result |
|---|---|
| response samples | `14` |
| PM-service `/dev/subsys_esoc0` attempt | `true` |
| PMIC GPIO9 line-info present | `true` |
| PMIC GPIO9 flags | `0x3` in all samples |
| PMIC GPIO9 kernel-owned | `true` in all samples |
| PMIC GPIO9 output flag | `true` in all samples |
| PMIC GPIO9 consumer | `AP2MDM_SOFT_RESET` in all samples |
| forbidden line request/write/ioctl markers | all zero |
| GPIO142 IRQ count | `0` in all samples |
| `mdm3` state | `OFFLINING` in all samples |
| PCI device count | `0` in all samples |
| MHI bus count | `0` in all samples |
| MHI pipe | absent |
| `wlan0` | absent |

## Interpretation

V1267 closes the previous helper gap from V1264.  The same PM-service
`/dev/subsys_esoc0` response window now proves that PMIC GPIO9 is not merely
named by pinctrl text: the GPIO chardev reports it as kernel-owned and output,
with consumer `AP2MDM_SOFT_RESET`, throughout the response window.

The blocker remains below or inside the proprietary ext-mdm power-up path.  Even
with PM-service reaching `mdm_subsys_powerup` and AP2MDM soft-reset line-info
showing kernel-owned output state, the native path still gets no GPIO142 response,
no PCIe RC1 enumeration, no MHI pipe, no WLFW/BDF, and no `wlan0`.

## Cleanup

The live manifest classified cleanup as reboot-required because postflight could
not prove all transient actors and mounts were safely stopped.  A reboot was
performed.  After reboot:

- `version` returned `A90 Linux init 0.9.68 (v724)`.
- `selftest` returned `pass=11 warn=1 fail=0`.
- `/proc/mounts` no longer showed `debugfs`, `/vendor/firmware_mnt`,
  `/vendor/firmware-modem`, or `/mnt/system`.

## Next

V1268 should be host-only classification for the next observer target.  The
strongest next target is read-only line value / power-state evidence in the same
PM-service window: PMIC GPIO9 value if exposed by debugfs gpio, TLMM GPIO135/142
value/pinconf if exposed, and PCIe GDSC/regulator state.  Continue to block
GPIO line request/hold, PMIC write, direct eSoC ioctl, Wi-Fi scan/connect,
credentials, DHCP/routes, external ping, flash, boot image write, and partition
write.
