# Native Init V823 SSCTL Nameservice Matrix Report

## Result

- decision: `v823-ssctl-nameservice-clean-empty-below-hal`
- pass: `true`
- runner: `scripts/revalidation/native_wifi_ssctl_nameservice_matrix_v823.py`
- evidence: `tmp/wifi/v823-ssctl-nameservice-matrix/`

## What Ran

```bash
python3 -m py_compile \
  scripts/revalidation/native_wifi_ssctl_nameservice_matrix_v823.py

python3 scripts/revalidation/native_wifi_ssctl_nameservice_matrix_v823.py \
  --out-dir tmp/wifi/v823-ssctl-nameservice-matrix-plan-check \
  plan

python3 scripts/revalidation/native_wifi_ssctl_nameservice_matrix_v823.py \
  preflight

python3 scripts/revalidation/native_wifi_ssctl_nameservice_matrix_v823.py \
  run
```

## Evidence Summary

| Signal | Result |
| --- | --- |
| V822 route | pass |
| helper | `a90_android_execns_probe v125` |
| helper deploy | executed |
| V817 lower window | pass |
| reboot cleanup | executed |
| expected matrix cases | `6` |
| matrix result | complete |
| AF_QIPCRTR sockets | all socket rc `0`, family `42` |
| nameservice lookup sends | all new/delete lookup rc `0` |
| timeouts | `0` |
| service events | `0` |
| QMI payload | `0` |

## Matrix Rows

| Case | Label | Service | Instance | Service events | End-of-list | Timeout | QMI attempted |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | `servloc` | `64` | `1` | `0` | `1` | `0` | `0` |
| 1 | `ssctl` | `43` | `16` | `0` | `1` | `0` | `0` |
| 2 | `servnotif` | `66` | `74` | `0` | `1` | `0` | `0` |
| 3 | `servnotif` | `66` | `180` | `0` | `1` | `0` | `0` |
| 4 | `wlfw` | `69` | `0` | `0` | `1` | `0` | `0` |
| 5 | `wlfw` | `69` | `1` | `0` | `1` | `0` | `0` |

## Runtime Snapshot

The lower window still reproduces the same kernel-side progress pattern:

| Phase | mss/modem | mdm3 | service-locator | sysmon-qmi | service-notifier | WLFW |
| --- | --- | --- | --- | --- | --- | --- |
| before-holder | `OFFLINING` | `OFFLINING` | `4` | `0` | `0` | `0` |
| after-holder | `ONLINE` | `OFFLINING` | `4` | `0` | `0` | `0` |
| after-companion | `ONLINE` | `OFFLINING` | `5` | `1` | `0` | `0` |

## Interpretation

V823 closes the specific V822 hypothesis. Adding the actual sysmon SSCTL
service `43/16` did not reveal a userspace nameservice publication. The helper
can open AF_QIPCRTR and send lookup/delete messages for all six cases, but every
case receives only end-of-list.

This means the next blocker is not simply "V821 forgot SSCTL." The current gap
is more precise: kernel QMI clients can produce dmesg evidence for
service-locator/sysmon progress, while a userspace AF_QIPCRTR lookup in the same
lower window does not observe service publications for service-locator, SSCTL,
service-notifier, or WLFW.

## Safety

- Helper deploy wrote only the approved helper path.
- Cleanup reboot restored healthy v724 native status.
- No custom kernel flash, boot image write, partition write, or bootloader
  handoff executed.
- No `esoc0` open, bind/unbind, driver override, or module load/unload
  executed.
- No QMI payload, service-manager, Wi-Fi HAL, wificond, scan/connect/link-up,
  credential use, DHCP, route change, or external ping executed.
- V775 custom OSRC kernel flashing pause remains active.
- No Wi-Fi secret material was written to tracked output.

## Next

V824 should classify kernel QMI client visibility versus userspace AF_QIPCRTR
nameservice visibility before any wider trigger. The next useful step is likely
host-only source/evidence classification of QRTR nameservice semantics,
qmi_handle lookup behavior, and whether userspace lookup is expected to observe
kernel QMI client-visible services on this stock 4.14 Samsung kernel.
