# Native Init V815 Subsystem/Sysmon Snapshot Report

## Result

- decision: `v815-idle-registration-snapshot-captured`
- pass: `true`
- runner: `scripts/revalidation/native_wifi_subsystem_sysmon_snapshot_v815.py`
- evidence: `tmp/wifi/v815-subsystem-sysmon-snapshot/`

## What Ran

```bash
python3 -m py_compile scripts/revalidation/native_wifi_subsystem_sysmon_snapshot_v815.py

python3 scripts/revalidation/native_wifi_subsystem_sysmon_snapshot_v815.py \
  --out-dir tmp/wifi/v815-subsystem-sysmon-snapshot-plan-check \
  plan

python3 scripts/revalidation/native_wifi_subsystem_sysmon_snapshot_v815.py \
  --allow-live-readonly \
  --assume-yes \
  run
```

## Evidence Summary

| Signal | Result |
| --- | --- |
| runtime health | stock v724 version matched; `selftest` passed |
| read-only command success | all V815 capture steps passed |
| `/sys/bus/msm_subsys/devices` | `10` subsystems captured |
| modem/mss idle state | `OFFLINING` |
| mdm3/esoc0 idle state | `OFFLINING` |
| esoc metadata | `esoc0` sysfs surface present; `/dev/esoc*` absent |
| ICNSS platform | `18800000.qcom,icnss` present |
| idle runtime markers | no service-notifier, service74, WLAN-PD, WLFW, BDF, or `wlan0` |
| service-locator idle marker | timeout markers present in dmesg focus |
| static surface strings | devicetree/sysfs contains sysmon and WLAN-related names, separated from runtime marker counts |

## Classification

V815 establishes the idle baseline:

```text
Idle native stock v724:
  msm_subsys surface present
  modem/mss OFFLINING
  mdm3/esoc0 OFFLINING
  ICNSS platform present
  service-locator timeout markers present
  no runtime service-notifier/service74/WLAN-PD/WLFW/BDF/wlan0
```

Compared with V812, the lower trigger window can move `mss` to `ONLINE` and
produce QRTR/sysmon markers, but V815 proves those markers are not already
present at idle and that service74/WLAN-PD/WLFW are not published without the
lower trigger. The next useful step is an idle-vs-trigger delta classifier using
V815 and V812 evidence.

## Safety

- Read-only device commands only.
- No custom kernel flash, boot image write, partition write, reboot, or
  bootloader handoff.
- No daemon start, service-manager start, Wi-Fi HAL start, scan/connect/link-up,
  or credential use.
- No DHCP, route change, or external ping.
- No `boot_wlan`, `qcwlanstate` write, `esoc0` open, bind/unbind, driver
  override, or module load/unload.
- No Wi-Fi secret material was written to tracked output.

## Next

V816 should compare V815 idle snapshot against V812 lower-trigger evidence and
classify the exact delta. The expected routing question is whether the next
bounded live work should sample subsystem/sysmon state inside the lower trigger
window or move to a narrower service-locator/sysmon registration proof.
