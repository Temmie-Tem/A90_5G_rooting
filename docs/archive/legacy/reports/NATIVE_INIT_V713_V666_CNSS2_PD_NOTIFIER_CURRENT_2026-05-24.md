# Native Init V713 V666 CNSS2 PD-Notifier Current-Boot Rerun

- date: `2026-05-24 KST`
- runner: `scripts/revalidation/native_wifi_cnss2_pd_notifier_readonly_v706.py`
- evidence: `tmp/wifi/v713-v666-cnss2-pd-notifier-current-20260524-100429/`
- approval: V666 read-only CNSS2 pd-notifier check
- decision: `v706-service180-absent-current-boot`
- status: `pass`

## Scope

This rerun used the user-provided V666 causal-chain direction, but executed it
with the existing V706 read-only classifier because the runner already captures
the requested surface:

- `dmesg | grep`-equivalent CNSS/ICNSS/WLAN-PD marker classification;
- `/sys/bus/msm_subsys/devices/` and subsystem state reads;
- `/sys/bus/platform/drivers/icnss` and `cnss2` visibility;
- ICNSS/QCA6390 platform-device and `wlan0` visibility;
- `/proc/net/qrtr` service `69` visibility when available.

No sysfs write, `esoc0` open/hold, daemon start, Wi-Fi HAL start,
scan/connect, DHCP, route change, external ping, boot image write, or partition
write was executed.

## Result

The current boot is not at the V666 decision point. The classifier did not see
service-notifier `180` or `74`, so it cannot test whether a kernel
`pd_notifier` callback fires after service `180`.

| marker | count |
| --- | ---: |
| `service_notifier_180` | `0` |
| `service_notifier_74` | `0` |
| `pd_notifier` | `0` |
| `icnss` | `5` |
| `cnss2` | `0` |
| `qca6390` | `0` |
| `icnss_qmi` | `0` |
| `wlfw_service` | `0` |
| `bdf` | `0` |
| `fw_ready` | `0` |
| `wlan0` | `0` |

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

The causal chain remains the right model:

```text
modem ONLINE
  -> service-locator can resolve WLAN-PD
    -> service-notifier 180/74 appears
      -> kernel ICNSS/CNSS notifier path should progress
        -> QCA6390/WLFW service 69
          -> BDF/fw_ready/wlan0
```

This run proves only that the current boot is before the `service-notifier
180/74` gate. It does not contradict the V710/V711 evidence where older live
windows already reached service `180/74` plus provider/CNSS retry and still
failed to reach ICNSS-QMI/WLFW/BDF/`wlan0`.

## Next

- For current-boot work, restore lower modem/WLAN-PD readiness before another
  CNSS retry or Wi-Fi HAL/connect attempt.
- For the service `180/74` positive path already captured by V708/V710, continue
  the current V712 route: deploy helper v121 and capture the ICNSS-QMI/WLFW edge
  inside the provider-first service `180/74` window.
- Do not retry Wi-Fi connect until WLFW/service `69`, BDF/fw-ready, or `wlan0`
  progresses.

## Validation

Executed:

```bash
python3 scripts/revalidation/native_wifi_cnss2_pd_notifier_readonly_v706.py \
  --out-dir tmp/wifi/v713-v666-cnss2-pd-notifier-current-20260524-100429 \
  --approval 'approve v666 cnss2 pd-notifier firing check and modem subsys state read; no Wi-Fi HAL start, no scan/connect, no DHCP, no external ping' \
  run
```

Result:

```text
decision: v706-service180-absent-current-boot
pass: True
device_mutations: False
daemon_start_executed: False
wifi_hal_start_executed: False
dhcp_or_external_ping_executed: False
```
