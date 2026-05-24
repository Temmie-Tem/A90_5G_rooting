# Native Init V790 Clean-DSP Lower-Only Plan

## Goal

Run a narrower live isolation gate after V789: repeat clean-DSP and current
SELinux prep, then run only the lower companion stack without `cnss_diag` or
`cnss-daemon`.

## Scope

- Arm only the V641 clean-DSP one-shot flag and reboot.
- Refresh V401 SELinuxfs mount and V490 policy load after the clean-DSP reboot.
- Run only:
  - `qrtr-ns`;
  - `rmt_storage`;
  - `tftp_server`;
  - `pd-mapper`.
- Capture QRTR, RPMSG, dmesg marker, process, and cleanup evidence.

## Hard Gates

- No `cnss_diag` or `cnss-daemon`.
- No service-manager, Wi-Fi HAL, wificond, supplicant, scan/connect, credential
  use, DHCP/routes, or external ping.
- No `esoc0` open, subsystem state write, module load/unload, bind/unbind,
  boot image write, partition write, or custom kernel flash.
- Stop on `pm_qos`, reference-count, esoc, or equivalent warning boundary.

## Validation

```bash
python3 -m py_compile scripts/revalidation/native_wifi_clean_dsp_lower_only_v790.py
python3 scripts/revalidation/native_wifi_clean_dsp_lower_only_v790.py plan
python3 scripts/revalidation/native_wifi_clean_dsp_lower_only_v790.py run \
  --assume-yes \
  --allow-arm-clean-dsp \
  --allow-reboot \
  --allow-cleanup-umount \
  --allow-system-mount \
  --allow-selinuxfs-mount \
  --allow-policy-load \
  --allow-firmware-mounts \
  --allow-subsys-modem-holder \
  --allow-lower-companion \
  --allow-cleanup-reboot
```

## Expected Routing

- Warning-free lower-only: isolate V788 warning to CNSS-only addition or timing.
- Warning repeats lower-only: isolate the warning to clean-DSP plus lower
  companion/audio deferred-probe ordering before any CNSS/HAL retry.
