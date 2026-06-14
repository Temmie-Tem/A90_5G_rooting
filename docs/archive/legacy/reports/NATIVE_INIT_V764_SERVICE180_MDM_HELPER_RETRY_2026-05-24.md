# Native Init V764 Service180-gated MDM Helper Retry Report

- date: `2026-05-24 KST`
- status: `pass`
- decision: `v764-mdm-helper-started-no-lower-progress`
- runner: `scripts/revalidation/native_wifi_mdm_helper_service180_retry_v764.py`
- evidence: `tmp/wifi/v764-mdm-helper-service180-retry/`

## Summary

V764 replaced the kernel-source instrumentation plan with the requested
service-notifier `180` gated `mdm_helper` live retry. The current boot did open
the service180 gate, `mdm_helper` started and was postflight-safe, but mdm3,
WLAN-PD, MHI/QCA6390, WLFW service `69`, BDF, and `wlan0` did not advance.

Result:

```text
decision: v764-mdm-helper-started-no-lower-progress
mdm_helper_start_executed: True
esoc0_open_executed: False
service_manager_start_executed: False
wifi_hal_start_executed: False
scan_connect_executed: False
external_ping_executed: False
```

## Prior Evidence Classification

| evidence | result |
| --- | --- |
| V745 | service180 gate stayed closed; `mdm_helper` did not start |
| V746 | sysmon gate opened; `mdm_helper` started; lower markers stayed 0 |
| V747 | QCA6390 bind/unbind remains rejected |
| V748 | blind `mdm_helper` retry was previously eliminated |
| V749 | lower-window `boot_wlan` was selected |

## V764 Live Result

| check | result |
| --- | --- |
| helper mode/order | pass |
| service180 gate | pass; gate opened |
| `mdm_helper` lifecycle | pass; started, observable, terminated by bounded cleanup |
| `mss` | `OFFLINING -> ONLINE -> ONLINE` |
| `mdm3` | `OFFLINING -> OFFLINING -> OFFLINING` |
| QRTR RX/TX | present |
| `sysmon-qmi` | present |
| service-notifier | present |
| WLFW service `69` readback | empty |
| MHI/QCA6390/WLFW/BDF/`wlan0` | absent |
| kernel warning | absent |
| postflight cleanup | pass; native status healthy after reboot |

## Access Surface

| surface | result |
| --- | --- |
| global `/vendor/bin/mdm_helper` | not visible in native global namespace |
| `/mnt/system/system/vendor/bin/mdm_helper` | not visible |
| `/sys/bus/esoc/devices/esoc0` | visible; points to `soc:qcom,mdm3/esoc0` |
| `/sys/class/subsys/subsys_esoc0` | visible |
| `/dev/subsys_esoc0` | absent |
| esoc0 safe attrs | `SDX50M`, `PCIe`, `0305_01.01.00` |
| esoc0 char-device open/hold | not executed |
| subsystem write | not executed |

## Interpretation

This resolves the requested retry: current service180 can gate `mdm_helper`, and
`mdm_helper` can start safely below HAL/connect. However, it is still not the
missing lower trigger. The lower gap remains before WLFW service `69` / BDF /
`wlan0`.

The direct esoc0 evidence matters: esoc sysfs metadata exists, but the
`/dev/subsys_esoc0` char node is absent in this native boot. That means a raw
esoc0 open/hold path is not currently available and was not attempted.

## Validation

Commands:

```text
python3 -m py_compile scripts/revalidation/native_wifi_mdm_helper_service180_retry_v764.py
python3 scripts/revalidation/wifi_selinuxfs_toybox_mount_live_executor.py --out-dir tmp/wifi/v764-v401-toybox-selinuxfs-mount --approval-phrase "approve v401 toybox mount selinuxfs runtime surface only; no daemon start and no Wi-Fi bring-up" --apply --assume-yes run
python3 scripts/revalidation/native_wifi_mdm_helper_service180_retry_v764.py run
python3 scripts/revalidation/a90ctl.py status
```

Postflight status:

```text
init: A90 Linux init 0.9.68 (v724)
selftest: pass=11 warn=1 fail=0
uptime: rebooted by bounded cleanup
```

## Next Gate

Do not repeat `mdm_helper` as the primary trigger unless new evidence changes
the esoc/service180 model. The stronger next candidate is to reconcile this
result with V749/V750 lower-window `boot_wlan` and the later HDD/PLD stall
evidence, then choose between:

1. a lower-window `boot_wlan` retry with the now-confirmed service180 window; or
2. minimal ICNSS/QCACLD source log instrumentation if the lower-window path
   remains unclassified.
