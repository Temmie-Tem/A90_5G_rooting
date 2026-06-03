# Native Init V1981 V1974 Control Contamination Rerun

## Summary

- Cycle: `V1981`
- Runner: `scripts/revalidation/android_ril_qmi_preup_uprobe_handoff_v1974.py`
- Decision: `v1974-android-capture-rejected-degraded-or-pcie-mhi`
- Label: `android-capture-rejected-degraded-or-pcie-mhi`
- Pass: `False`
- Reason: Android capture was rejected because it is degraded or has pre-wlan0 PCIe/MHI/eSoC contamination
- Evidence: `tmp/wifi/v1981-v1974-preup-uprobe-control-rerun`

## Control Result

- V1974 was the last known clean producer observer: original report had `PCIe/MHI before wlan0 = 0` and `wlan0 = 15.214171`.
- The same V1974 observer rerun now rejects with `pcie_mhi_before_wlan0 = 30` and `wlan0 = 16.255964`.
- This narrows V1978/V1979/V1980 contamination away from the added PID attribution, daemon strace, or QRTR matrix as sole causes.
- Current Android handoff state itself can enter the external `esoc0`/RC1/MHI path before `wlan0`, so another RIL producer capture must first prove a clean Android-good baseline in the same session.

## Timeline

| field | value |
| --- | --- |
| wlan_pd UP | 10.92615 |
| wlan0 | 16.255964 |
| contamination pcie-mhi/esoc/degraded257 | 30/0/False |
| libqmi events/send/rild-send | 3662/582/0 |
| pre-UP DMS/NAS/WDS lookups | 5 |
| pre-UP lead services | DMS |

## Pre-wlan0 Contamination Lines

- `[   10.019125]  [6:   Binder:931_2:  971] subsys-restart: __subsystem_get(): __subsystem_get: esoc0 count:0`
- `[   10.019135]  [6:   Binder:931_2:  971] subsys-restart: __subsystem_get(): Changing subsys fw_name to esoc0`
- `[   10.308389]  [0:    kworker/0:1:  119] msm_pcie_enable: PCIe RC1 link initialized`
- `[   10.325735]  [0:    kworker/0:1:  119] mhi 0001:01:00.0: BAR 0: assigned [mem 0x40300000-0x40300fff 64bit]`
- `[   10.325827]  [0:    kworker/0:1:  119] mhi 0001:01:00.0: enabling device (0000 -> 0002)`
- `[   12.952862]  [5: kworker/u17:15:  748] msm_pcie_enable: PCIe RC1 link initialized`
- `[   12.970504]  [4: kworker/u17:15:  748] mhi 0001:01:00.0: enabling device (0000 -> 0002)`
- `[   13.433340]  [0:    kworker/0:1:  119] msm_pcie_enable: PCIe RC1 link initialized`
- `[   13.450454]  [0:    kworker/0:1:  119] mhi 0001:01:00.0: enabling device (0000 -> 0002)`
- `[   14.093935]  [0:    kworker/0:1:  119] msm_pcie_enable: PCIe RC1 link initialized`
- `[   14.110369]  [0:    kworker/0:1:  119] mhi 0001:01:00.0: enabling device (0000 -> 0002)`
- `[   14.532883]  [0:    kworker/0:1:  119] msm_pcie_enable: PCIe RC1 link initialized`
- `[   14.550445]  [0:    kworker/0:1:  119] mhi 0001:01:00.0: enabling device (0000 -> 0002)`
- `[   14.974970]  [0:    kworker/0:1:  119] msm_pcie_enable: PCIe RC1 link initialized`
- `[   14.990539]  [0:    kworker/0:1:  119] mhi 0001:01:00.0: enabling device (0000 -> 0002)`
- `[   15.443937]  [0:    kworker/0:1:  119] msm_pcie_enable: PCIe RC1 link initialized`
- `[   15.460541]  [0:    kworker/0:1:  119] mhi 0001:01:00.0: enabling device (0000 -> 0002)`

## Evidence Files

| file | bytes | lines |
| --- | ---: | ---: |
| `dmesg-filtered.txt` | 39825 | 380 |
| `libqmi-uprobe-trace.txt` | 515932 | 3662 |
| `libqmi-uprobe-summary.txt` | 5687 | 65 |
| `cnss_daemon.strace.txt` | 1460 | 19 |
| `tftp_server.strace.txt` | 173803 | 1204 |
| `rmt_storage.strace.txt` | 20747 | 132 |
| `request-lines.txt` | 286208 | 2000 |

## Safety

- Rollbackable Android-handoff to native v724 only.
- No Wi-Fi HAL start, scan/connect, credential handling, DHCP/routes, external ping, `/dev/subsys_esoc0`, eSoC notify/BOOT_DONE, PCI rescan, platform bind/unbind, PMIC/GPIO/GDSC/regulator write, fake ONLINE state, forced RC1/case write, or sda29 remount-write was performed.
- Native rollback selftest fail=0: `True`.

## Next Gate

- Run a minimal V1753-style Android-good baseline rerun with no RIL producer additions. If it is clean, rebuild producer capture on that exact baseline; if it is contaminated, stop retrying producer decode and first restore/identify the clean Android handoff condition.
- Do not decode V1978/V1979/V1980/V1981 as normal Android-good producer evidence because each has pre-`wlan0` external RC1/MHI contamination.
