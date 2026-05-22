# Native Init V640 Safe Sibling Trigger Reclassification Report

- date: `2026-05-23 KST`
- status: `pass/classified`; Wi-Fi external ping is **not** complete
- runner: `scripts/revalidation/native_wifi_safe_sibling_trigger_reclassifier_v640.py`
- evidence: `tmp/wifi/v640-safe-sibling-trigger-reclassifier/`
- decision: `v640-boot-window-only-sibling-trigger-needed`

## Scope

V640 is host-only. It consolidates V622, V627, V628, V630, V631, V635, V636,
V638, and V639 evidence after late all-sibling direct writes were blocked by
the `pm_qos` warning class.

No device command, sysfs write, DSP boot-node write, boot image build/flash,
reboot, daemon start, service-manager start, Wi-Fi HAL start,
scan/connect/link-up, credential handling, DHCP, route change, or external ping
was executed.

## Result

```text
decision: v640-boot-window-only-sibling-trigger-needed
pass: True
reason: No untested non-write pre-service74 Android daemon remains; warning-free native service180 still lacks sibling sysmon/service74, late all-sibling writes are blocked, and prior boot-window attempts predate firmware-backed CDSP fix.
next: plan a rollback-ready firmware-backed early-boot sibling trigger proof; keep HAL/connect/credentials blocked
device_commands_executed: False
sysfs_writes_executed: False
wifi_bringup_executed: False
```

## Evidence Matrix

| subject | classification | evidence | next |
| --- | --- | --- | --- |
| Android V622 | target path | sibling `sysmon-qmi=True`, service `74=True`, `180->74=6.561 ms` | service `74` remains below HAL/connect |
| non-write services | no new pre-`74` target | untested pre-`74` services `[]`; `qrtr_ns`/`pd_mapper` already replayed | do not add random daemon starts |
| boot-node contract | Android early-boot only | ADSP/CDSP/SLPI boot-node writes are all visible under `on early-boot` | late live writes are not equivalent |
| V630/V631 boot window | attempted but firmware-incomplete | V630 timed out after ADSP; V631 isolated CDSP timeout | boot-window class remains relevant but needs firmware-backed redesign |
| V635/V636 | warning-free partial positive | CDSP-only warning-free; CDSP+V598 reaches service `180` warning-free | preserve this baseline |
| V638/V639 | late direct writes blocked | late all-sibling write produced `pm_qos` warnings and no service `74` | do not repeat all-sibling live writes |

## Android V622 Timing

| service | start | relation to service `74` | classification |
| --- | ---: | --- | --- |
| `qrtr_ns` | `6857.383 ms` | before service `74` by `64.756 ms` | already replayed |
| `pd_mapper` | `6863.201 ms` | before service `74` by `58.938 ms` | already replayed |
| `rmt_storage` | `6936.835 ms` | after service `74` by `14.696 ms` | not first service `74` trigger |
| `tftp_server` | `6946.547 ms` | after service `74` by `24.408 ms` | not first service `74` trigger |
| `mdm_launcher` | `7920.193 ms` | after service `74` by `998.054 ms` | later state |
| `cnss_diag` | `7928.702 ms` | after service `74` by `1006.563 ms` | later state |
| `mdm_helper` | `8098.546 ms` | after service `74` by `1176.407 ms` | later state |
| `cnss-daemon` | `8116.918 ms` | after service `74` by `1194.779 ms` | later state |

## Interpretation

V640 removes the remaining daemon-first explanation for service `74`. The only
non-write services that start before Android service `74` are `qrtr_ns` and
`pd_mapper`, and those are already part of the native warning-free lower-path
replays. Later services such as `rmt_storage`, `tftp_server`, `mdm_launcher`,
`mdm_helper`, `cnss_diag`, and `cnss-daemon` cannot be the first service `74`
publisher trigger by timestamp.

The remaining useful path is boot-window only:

- Android performs visible ADSP/CDSP/SLPI boot-node writes during `early-boot`;
- native V630/V631 boot-window attempts proved rollback and one-shot mechanics
  but predated the V634/V635 firmware mount/CDSP fix;
- V638/V639 prove late firmware-backed all-sibling writes are unsafe and still
  negative;
- therefore the next mutation, if pursued, must be rollback-ready and
  firmware-backed in an early-boot window, not a late live write.

## Blocker State

The Wi-Fi bring-up gate remains closed:

- service `74` is still missing under native;
- WLAN-PD, WLFW/BDF, firmware-ready, and `wlan0` are still missing;
- Wi-Fi credentials, scan/connect, DHCP, routes, and external ping remain
  blocked.

## Next Gate

Proceed to V641 planning:

1. design a rollback-ready firmware-backed early-boot sibling trigger proof;
2. keep the proof disabled by default and one-shot opt-in only;
3. mount/verify `apnhlos` and `modem` firmware surfaces before CDSP/ADSP/SLPI
   writes if feasible in the boot window;
4. capture marker-only evidence for sibling `sysmon-qmi`, service `74`,
   WLAN-PD, WLFW/BDF, firmware-ready, `wlan0`, and kernel warnings;
5. roll back to v319 and verify native health before any HAL/connect work.
