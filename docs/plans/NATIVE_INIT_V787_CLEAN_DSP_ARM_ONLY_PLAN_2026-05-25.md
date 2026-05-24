# Native Init V787 Clean-DSP Arm-Only Plan

## Goal

Run the V641 firmware-backed sibling SSCTL one-shot path that V786 proved is
already present in stock v724.  This gate restores the clean-DSP prerequisite
for later lower companion readback without starting CNSS/HAL, scanning,
connecting, or using Wi-Fi credentials.

## Scope

- Live stock-v724 proof.
- Arm only `/cache/native-init-sibling-fwssctl-v641`.
- Reboot once, collect proof/timeline/dmesg/rpmsg evidence, then unmount the
  read-only firmware mountpoints left by the one-shot.

## Explicitly Out of Scope

- Do not arm `/cache/native-init-qrtr-servloc-boot-v724`.
- Do not run `boot_wlan` or `qcwlanstate`.
- Do not start CNSS/HAL/service-manager/wificond/supplicant.
- Do not scan/connect, use credentials, run DHCP, change routes, or ping.
- Do not flash a custom kernel or write boot partitions.

## Success Criteria

- Current native version is `A90 Linux init 0.9.68 (v724)`.
- v724 QRTR flag is absent before arming.
- V641 timeline reaches `complete failures=0 timeouts=0`.
- ADSP/CDSP/SLPI each return `status=0x0` and show PIL reset/power/clock
  markers.
- No `pm_qos_add_request`, reference-count, or `esoc0` warning boundary appears.
- Firmware mountpoints are unmounted after evidence collection.
- Device remains `BOOT OK` with selftest passing after cleanup.

## Runner

```bash
python3 -m py_compile scripts/revalidation/native_wifi_clean_dsp_arm_only_v787.py
python3 scripts/revalidation/native_wifi_clean_dsp_arm_only_v787.py plan
python3 scripts/revalidation/native_wifi_clean_dsp_arm_only_v787.py run \
  --assume-yes \
  --allow-arm-clean-dsp \
  --allow-reboot \
  --allow-cleanup-umount
```
