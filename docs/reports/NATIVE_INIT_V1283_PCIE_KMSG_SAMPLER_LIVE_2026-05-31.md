# Native Init V1283 PCIe/GDSC/kmsg Sampler Live

- generated: 2026-05-31
- cycle: V1283
- command: bounded live observation
- decision: `v1283-pm-esoc0-trigger-sampled-mdm2ap-silent-reboot-required`
- pass: true
- helper: `a90_android_execns_probe v268`

## Result

V1283 reran the bounded PM-service `/dev/subsys_esoc0` response sampler with
helper v268.

| field | value |
| --- | --- |
| sample count | `14` |
| PM-service `/dev/subsys_esoc0` attempt | true |
| late `per_proxy` started | `1` |
| `/dev/kmsg` open | false |
| `/dev/kmsg` errno | `2` (`ENOENT`) |
| kmsg filtered markers | `0` |
| GPIO142 IRQ count | `0` |
| PCI devices | `0` |
| MHI bus devices | `0` |
| MHI pipe | absent |
| `wlan0` | absent |
| TLMM GPIO135/GPIO142 range | visible (`0-174`) |
| post-run health | v724 selftest `pass=11 warn=1 fail=0` |

Additional check after V1283:

- `/dev/kmsg` is absent.
- `/proc/kmsg` exists.
- `/cache/bin/busybox dmesg` can read kernel log output.

Evidence:

- `tmp/wifi/v1283-pcie-kmsg-sampler-live/manifest.json`
- `tmp/wifi/v1283-pcie-kmsg-sampler-live/summary.md`

## Interpretation

The helper-side kmsg read path was invalid for the native runtime because
`/dev/kmsg` does not exist. Therefore V1283 does not prove absence of PCIe,
GDSC, MHI, eSoC, SDX50M, or WLFW kernel messages; it proves that the helper needs
a non-`/dev/kmsg` read path.

The rest of the response window remains unchanged: PM-service reaches
`/dev/subsys_esoc0`, but no GPIO142 IRQ, PCIe enumeration, MHI device, MHI pipe,
or `wlan0` appears.

## Safety

No Wi-Fi HAL start, scan/connect, credential use, DHCP/route change, external
ping, flash, boot image write, partition write, PMIC write, GPIO line request,
or direct eSoC ioctl was executed. The live actor remained the existing bounded
PM-service response path.

## Next

V1284 should repair the kmsg collector with a read-only syslog/klogctl fallback
or wrapper-level `busybox dmesg` capture, then rebuild before retrying the live
PCIe/GDSC/dmesg sampler.
