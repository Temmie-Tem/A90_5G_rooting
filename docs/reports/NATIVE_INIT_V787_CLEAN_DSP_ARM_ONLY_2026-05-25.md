# Native Init V787 Clean-DSP Arm-Only Report

## Result

- decision: `v787-clean-dsp-arm-only-proof-pass`
- pass: `true`
- runner: `scripts/revalidation/native_wifi_clean_dsp_arm_only_v787.py`
- evidence: `tmp/wifi/v787-clean-dsp-arm-only/`

## What Ran

```bash
python3 -m py_compile scripts/revalidation/native_wifi_clean_dsp_arm_only_v787.py
python3 scripts/revalidation/native_wifi_clean_dsp_arm_only_v787.py run \
  --assume-yes \
  --allow-arm-clean-dsp \
  --allow-reboot \
  --allow-cleanup-umount
```

The first live attempt exposed an autohud/menu busy handling gap in the runner.
The runner was updated to hide/retry on busy responses and to count proof
markers from the current boot timeline rather than the cumulative proof log.
The final V787 run passed.

## Key Findings

| Signal | Result |
| --- | --- |
| current version | `A90 Linux init 0.9.68 (v724)` |
| V641 one-shot arm | pass |
| reboot back to v724 | pass |
| V641 timeline | `complete failures=0 timeouts=0` |
| ADSP/CDSP/SLPI status | `0x0` each |
| DSP PIL markers | ADSP `3`, CDSP `3`, SLPI `3` |
| sibling sysmon/service-notifier | `0` / `0` |
| WLFW/BDF/`wlan0` | absent |
| warning boundary | no `pm_qos`/reference/esoc warning |
| cleanup | `/vendor/firmware-modem` and `/vendor/firmware_mnt` unmounted |
| post-cleanup health | `BOOT OK`, selftest `pass=11 warn=1 fail=0` |

## Interpretation

V787 restores the clean-DSP prerequisite on the current stock v724 path.  The
one-shot itself does not produce sibling `sysmon-qmi`, service-notifier,
WLAN-PD, WLFW/BDF, or `wlan0`, which matches the historical V641 behavior.

The next useful gate is not Wi-Fi scan/connect yet.  V788 should combine a fresh
V641 clean-DSP arm-only boot with the lower companion readback path and observe
whether QRTR TX, sibling sysmon, service-notifier `180/74`, WLAN-PD, WLFW/BDF,
or `wlan0` advances without triggering the service-74 warning boundary.

## Safety

- boot image or partition write: not executed
- custom kernel flash: not executed
- v724 QRTR flag: not armed
- `boot_wlan`/`qcwlanstate`: not executed
- CNSS/HAL/service-manager: not started
- scan/connect/credential use: not executed
- DHCP/routes/external ping: not executed
- firmware mounts: cleaned up

## Evidence

- `tmp/wifi/v787-clean-dsp-arm-only/manifest.json`
- `tmp/wifi/v787-clean-dsp-arm-only/summary.md`
- `tmp/wifi/v787-clean-dsp-arm-only/native/post-timeline.txt`
- `tmp/wifi/v787-clean-dsp-arm-only/native/post-dmesg-markers.txt`
- `tmp/wifi/v787-clean-dsp-arm-only/native/cleanup-firmware-mounts.txt`
