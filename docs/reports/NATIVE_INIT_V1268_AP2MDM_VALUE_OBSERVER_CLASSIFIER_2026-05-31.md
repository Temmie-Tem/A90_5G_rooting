# V1268 AP2MDM Value Observer Classifier

## Result

- decision: `v1268-ap2mdm-value-observer-selected`
- evidence: `tmp/wifi/v1268-ap2mdm-value-observer-classifier/manifest.json`
- scope: host-only classifier; no device mutation or live command
- next gate: V1269 source/build-only helper `a90_android_execns_probe v265`

## Classification

V1267 proved PMIC GPIO9 is kernel-owned output in the active PM-service
`/dev/subsys_esoc0` response window:

- `gpiochip_lineinfo_line_flags=0x3` in `14/14` samples.
- `gpiochip_lineinfo_flag_kernel=1` in `14/14` samples.
- `gpiochip_lineinfo_flag_is_out=1` in `14/14` samples.
- `gpiochip_lineinfo_line_consumer=AP2MDM_SOFT_RESET` in `14/14` samples.

V1262 had previously seen the idle line-info flags as `0x1` with output flag
`0`, so V1267 established a meaningful in-window state change.  However, the
same V1267 samples still show no downstream SDX50M response:

- GPIO142 IRQ count stays `0`.
- `mdm3` stays `OFFLINING`.
- PCI device count stays `0`.
- MHI bus count stays `0`.
- MHI pipe and `wlan0` stay absent.
- PCIe GDSC regulator lines remain `0mV`.

The next missing fact is no longer line ownership.  The missing fact is whether
the kernel-owned AP2MDM soft-reset/status path is asserting the expected value
and whether the power rail/pinconf state is sufficient for SDX50M to respond.

## V1269 Contract

V1269 should remain source/build-only and extend the V1267 response sampler with
read-only value/power snapshots:

- `/sys/kernel/debug/gpio` line for global GPIO1270 if present.
- PMIC GPIO9 pinmux/pinconf lines from PM8150L pinctrl debugfs.
- TLMM GPIO135/AP2MDM and GPIO142/MDM2AP pinmux/pinconf lines.
- PCIe GDSC `regulator_summary` lines and PCIe RC1 read-only state.
- Existing GPIO142 IRQ, `mdm3`, PCI/MHI/`wlan0` counters.

Hard exclusions remain unchanged: no GPIO line request or hold, no PMIC/debugfs
write, no regulator write, no direct eSoC ioctl, no new daemon/HAL start beyond
the existing bounded PM-service response path, no Wi-Fi scan/connect,
credentials, DHCP/routes, external ping, flash, boot image write, or partition
write.
