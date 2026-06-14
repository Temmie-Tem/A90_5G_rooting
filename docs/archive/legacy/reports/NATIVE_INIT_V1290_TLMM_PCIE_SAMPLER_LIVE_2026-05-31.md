# Native Init V1290 TLMM/PCIe Sampler Live

- generated: 2026-05-31
- cycle: V1290
- command: bounded live observation
- decision: `v1290-pm-esoc0-trigger-sampled-mdm2ap-silent-reboot-required`
- pass: true
- helper: `a90_android_execns_probe v270`

## Result

V1290 reran the bounded PM-service `/dev/subsys_esoc0` response sampler with
helper v270. The exact TLMM target scan succeeded.

| field | value |
| --- | --- |
| sample count | `14` |
| PM-service `/dev/subsys_esoc0` attempt | true |
| kmsg source | `syslog-read-all` |
| exact GPIO135 target line | `gpio135 : out 0 16mA no pull` |
| exact GPIO142 target line | `gpio142 : in  0 8mA no pull` |
| GPIO142 IRQ count | `0` |
| PCIe kmsg markers | `0` |
| MHI kmsg markers | `0` |
| WLFW kmsg markers | `0` |
| SDX50M kmsg markers | `0` |
| PCI devices | `0` |
| MHI bus devices | `0` |
| MHI pipe | absent |
| `wlan0` | absent |
| post-reboot health | v724 selftest `pass=11 warn=1 fail=0` |

Evidence:

- `tmp/wifi/v1290-tlmm-pcie-sampler-live/manifest.json`
- `tmp/wifi/v1290-tlmm-pcie-sampler-live/summary.md`

## Interpretation

V1290 proves that the helper can see exact TLMM GPIO135/GPIO142 state in the
response window. Those static lines match the Android-positive evidence:
GPIO135 is `out 0 16mA no pull`, and GPIO142 is `in 0 8mA no pull`.

This further narrows the blocker: static PMIC9 and TLMM GPIO shape are no longer
the shortest explanation. The remaining gap is dynamic SDX50M/PCIe power-up
progression after PM-service enters the eSoC path.

## Safety

No Wi-Fi HAL start, scan/connect, credential use, DHCP/route change, external
ping, flash, boot image write, partition write, PMIC write, GPIO line request,
or direct eSoC ioctl was executed. The live actor remained the existing bounded
PM-service response path.

## Next

V1291 should classify V1290 against Android-positive evidence and select the
next gate around dynamic PCIe/GDSC/eSoC power sequencing rather than static GPIO
shape.
