# Native Init V639 Sibling Warning Attribution Report

- date: `2026-05-23 KST`
- status: `pass/classified`; Wi-Fi external ping is **not** complete
- runner: `scripts/revalidation/native_wifi_sibling_warning_attribution_v639.py`
- evidence: `tmp/wifi/v639-sibling-warning-attribution-classifier/`
- decision: `v639-all-sibling-warning-attributed-single-node-unresolved`

## Scope

V639 is host-only. It compares V638 all-sibling firmware-backed writes with
V619, V635, and V636 evidence to decide whether another ADSP/CDSP/SLPI direct
write retry is justified.

No device command, sysfs write, DSP boot-node write, boot image build/flash,
reboot, daemon start, service-manager start, Wi-Fi HAL start,
scan/connect/link-up, credential handling, DHCP, route change, or external ping
was executed.

## Result

```text
decision: v639-all-sibling-warning-attributed-single-node-unresolved
pass: True
reason: V638 warnings are temporally tied to the late all-sibling ADSP/CDSP/SLPI boot sequence, while CDSP-only and CDSP+V598 stayed warning-free. A single culprit is not proven.
next: avoid direct all-sibling write retries; next classify a non-write or Android-sequenced lower publisher path
device_commands_executed: False
sysfs_writes_executed: False
wifi_bringup_executed: False
```

## Evidence Matrix

| case | decision | evidence | classification |
| --- | --- | --- | --- |
| V619 all-sibling replay | `v619-unsafe-kernel-warning` | `kernel_warning=21`, sibling sysmon present | warning-positive all-sibling precedent |
| V635 CDSP-only firmware proof | `v635-cdsp-returned-no-lower-marker` | `cdsp_returned=True`, `pm_qos=0` | warning-free single-node contrast |
| V636 CDSP+V598 composite | `v636-cdsp-v598-service180-only` | `service180=1`, `service74=0`, `kernel_warning=0` | warning-free lower-path contrast |
| V638 firmware all-sibling | `v638-firmware-sibling-ssctl-composite-blocked` | `pm_qos=13`, `kernel_warning=26`, lower markers absent | warning-positive no-progress result |

## V638 Warning Attribution

| node | first start | first ready | `pm_qos` warnings |
| --- | ---: | ---: | ---: |
| ADSP | `742.139117` | `742.352289` | 4 |
| CDSP | `743.158353` | `743.236354` | 5 |
| SLPI | `745.183914` | `745.301284` | 4 |

V638 also captured state progression:

| snapshot | ADSP | CDSP | SLPI |
| --- | --- | --- | --- |
| initial | `OFFLINING` | `OFFLINING` | `OFFLINING` |
| after ADSP | `ONLINE` | `OFFLINING` | `OFFLINING` |
| after CDSP | `ONLINE` | `ONLINE` | `OFFLINING` |
| after SLPI | `ONLINE` | `ONLINE` | `ONLINE` |

## Interpretation

The warning source is now narrower but not single-node proven:

- V638 warnings are timestamp-adjacent to all three late direct node boots.
- V619 previously showed the same warning class on an all-sibling replay.
- V635 proves CDSP-only firmware-backed boot can return without `pm_qos`
  warnings.
- V636 proves the CDSP+V598 lower path can reproduce service `180` without
  kernel warnings.

Therefore CDSP alone is not the warning root by itself, and a blind late
all-sibling direct-write retry is not justified. The safe useful partial
positive remains the warning-free service `180` path, not the V638 all-sibling
path.

## Blocker State

V639 keeps the Wi-Fi bring-up gate closed:

- no service `74`;
- no WLAN-PD;
- no WLFW/BDF;
- no firmware-ready marker;
- no `wlan0`;
- no scan/connect credentials;
- no DHCP/routes/external ping.

## Next Gate

V640 should stay below CNSS/HAL/connect and avoid direct all-sibling writes.
The next useful direction is one of:

1. host-only Android/native comparison for the non-write lower publisher path
   that follows warning-free service `180` and precedes service `74`;
2. a stricter Android-sequenced proof that does not repeat late direct
   ADSP/CDSP/SLPI boot-node writes;
3. if live testing is needed later, a narrower warning-free path derived from
   V635/V636 evidence rather than an all-sibling retry.
