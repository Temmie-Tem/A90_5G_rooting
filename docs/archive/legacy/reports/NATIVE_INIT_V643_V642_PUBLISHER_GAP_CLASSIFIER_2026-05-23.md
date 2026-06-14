# Native Init V643 V642 Publisher Gap Classifier Report

- date: `2026-05-23 KST`
- status: `classified`; Wi-Fi external ping is **not** complete
- runner: `scripts/revalidation/native_wifi_v642_publisher_gap_classifier_v643.py`
- evidence: `tmp/wifi/v643-v642-publisher-gap-classifier/`
- decision: `v643-cnss-correlated-service180-mdm3-service74-gap`

## Scope

V643 is host-only. It compares existing native evidence and does not contact
the device, mutate sysfs, start daemons, start Wi-Fi HAL, scan/connect, use
credentials, run DHCP, change routes, or ping externally.

## Result

```text
decision: v643-cnss-correlated-service180-mdm3-service74-gap
pass: True
reason: V642 clean-DSP no-CNSS path reaches QRTR TX/sysmon with no notifier; V625/V627 CNSS-including path reaches service 180 only; service 74/WLAN-PD/WLFW remain absent with mdm3 OFFLINING
next: plan V644 clean-DSP CNSS/WLFW readback replay before any HAL/scan/connect
```

## Comparison

| run | pass | decision | order | children | cnss | warning | qrtr_tx | sysmon | svc180 | svc74 | wlan_pd | qmi | mdm3 |
| --- | --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| V598 | true | `v598-wlfw-readback-empty` | `qrtr_ns,rmt_storage,tftp_server,pd_mapper,cnss_diag,cnss_daemon` | 6 | true | 0 | 1 | 1 | 1 | 0 | 0 | 0 | `OFFLINING` |
| V625 | true | `v598-wlfw-readback-empty` | `qrtr_ns,rmt_storage,tftp_server,pd_mapper,cnss_diag,cnss_daemon` | 6 | true | 0 | 1 | 1 | 1 | 0 | 0 | 0 | `OFFLINING` |
| V627 | true | `v627-post-180-service74-missing` | `qrtr_ns,rmt_storage,tftp_server,pd_mapper,cnss_diag,cnss_daemon` | 6 | true | 0 | 1 | 1 | 1 | 0 | 0 | 0 | `OFFLINING` |
| V619 | false | `v619-unsafe-kernel-warning` | `qrtr_ns,pd_mapper,rmt_storage,tftp_server` | 4 | false | 21 | 1 | 4 | 0 | 0 | 0 | 0 | `OFFLINING` |
| V642 | true | `v642-lower-modem-readiness-only` | `qrtr_ns,pd_mapper,rmt_storage,tftp_server` | 4 | false | 0 | 1 | 4 | 0 | 0 | 0 | 0 | `OFFLINING` |

## Interpretation

V642 removed the V619 direct-DSP warning class while preserving QRTR
TX/`sysmon-qmi` advancement. That makes the no-CNSS Android-order lower
companion path safe, but it is insufficient for service-notifier publication.

The only safe native paths that reproduce service-notifier `180` are the
V598/V625/V627 class, where the companion window includes:

```text
cnss_diag,cnss_daemon
```

That does not mean Wi-Fi is ready. V627 still proves the next boundary remains:

```text
service 74 missing
WLAN-PD missing
WLFW service 69 end-of-list / QMI server absent
BDF and wlan0 absent
mdm3 OFFLINING
```

## Next Gate

Proceed to V644 as a bounded clean-DSP CNSS/WLFW readback replay:

1. keep V641/V642 clean-DSP and current V490 prerequisites;
2. use helper v104 if compatible with the V598-class
   `wifi-companion-start-only` + WLFW QRTR readback path;
3. start only the lower CNSS-including companion window below HAL/scan/connect;
4. verify whether service `180` still appears warning-free in the clean-DSP
   v641 state and whether service `74`/WLAN-PD/WLFW changes.

Wi-Fi HAL, scan/connect, credentials, DHCP, route changes, and external ping
remain blocked until service `74`, WLAN-PD, WLFW/BDF, or `wlan0` advances.
