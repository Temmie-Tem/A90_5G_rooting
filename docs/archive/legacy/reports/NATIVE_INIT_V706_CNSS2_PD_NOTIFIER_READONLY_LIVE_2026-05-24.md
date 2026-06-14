# Native Init V706 CNSS2 PD-Notifier Read-Only Live Report

- date: `2026-05-24 KST`
- runner: `scripts/revalidation/native_wifi_cnss2_pd_notifier_readonly_v706.py`
- evidence: `tmp/wifi/v706-cnss2-pd-notifier-readonly-live/`
- decision: `v706-service180-absent-current-boot`
- status: `pass`

## Scope Result

The live run was read-only:

- `device_mutations=False`
- `daemon_start_executed=False`
- `wifi_hal_start_executed=False`
- `dhcp_or_external_ping_executed=False`

No Wi-Fi HAL, scan/connect, credential use, DHCP, route change, external ping,
sysfs write, `esoc0` open, boot image write, or partition write was executed.

## Current-Boot Finding

V706 did not reproduce the earlier service-notifier `180` state in the current
boot:

| marker | count |
| --- | ---: |
| `service_notifier_180` | `0` |
| `service_notifier_74` | `0` |
| `pd_notifier` | `0` |
| `cnss2` | `0` |
| `qca6390` | `0` |
| `power_on` | `0` |
| `icnss_qmi` | `0` |
| `wlfw_service` | `0` |
| `bdf` | `0` |
| `fw_ready` | `0` |
| `wlan0` | `0` |

The relevant subsystem states were:

| surface | value |
| --- | --- |
| `firmware_class.path` | `/vendor/firmware_mnt/image` |
| `mss_state` | `OFFLINING` |
| `mdm3_state` | `OFFLINING` |
| `icnss_driver_dir_ok` | `True` |
| `cnss2_driver_dir_ok` | `False` |
| `icnss_device_ok` | `True` |
| `qca6390_device_ok` | `True` |
| `qca6390_runtime_status` | `unsupported` |
| `wlan0_visible` | `False` |
| `qrtr_service69_visible` | `False` |

## Interpretation

The user-provided causal chain remains useful, but the current boot is not yet
at the `service-notifier 180 -> cnss2/icnss callback` decision point. Both
`mss` and `mdm3` read as `OFFLINING`, and the current dmesg contains only early
ICNSS platform probe lines, not WLAN-PD, WLFW, BDF, or `wlan0` progression.

Therefore the next action is not another `cnss-daemon`, Wi-Fi HAL, or
scan/connect retry. The next action should restore or reproduce lower
modem/WLAN-PD readiness first, then rerun this classifier when service `180` is
actually present in the same boot.

## Validation

Executed:

```bash
python3 -m py_compile \
  scripts/revalidation/native_wifi_cnss2_pd_notifier_readonly_v706.py

python3 scripts/revalidation/native_wifi_cnss2_pd_notifier_readonly_v706.py \
  --out-dir tmp/wifi/v706-cnss2-pd-notifier-readonly-plan-check plan

python3 scripts/revalidation/native_wifi_cnss2_pd_notifier_readonly_v706.py \
  --out-dir tmp/wifi/v706-cnss2-pd-notifier-readonly-preflight-check preflight

python3 scripts/revalidation/native_wifi_cnss2_pd_notifier_readonly_v706.py \
  --out-dir tmp/wifi/v706-cnss2-pd-notifier-readonly-live \
  --approval '<approved read-only V666/V706 phrase>' \
  run
```

Results:

```text
v706-cnss2-pd-notifier-readonly-plan-ready
v706-cnss2-pd-notifier-readonly-preflight-ready
v706-service180-absent-current-boot
```

## Next Gate

Return to the lower modem readiness gate:

1. re-establish or prove `mss`/`mdm3` ONLINE/ready in current native boot;
2. reproduce service-notifier `180` in the same boot;
3. rerun V706 to classify whether the kernel `icnss`/CNSS path sees
   pd-notifier/server-arrive and powers QCA6390;
4. only after WLFW/service `69` or `wlan0` progresses, move back toward Wi-Fi
   HAL or connect testing.
