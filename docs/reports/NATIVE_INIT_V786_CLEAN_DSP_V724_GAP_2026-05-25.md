# Native Init V786 Clean-DSP/v724 Gap Report

## Result

- decision: `v786-v724-clean-dsp-hook-available-but-unarmed`
- pass: `true`
- runner: `scripts/revalidation/native_wifi_clean_dsp_v724_gap_v786.py`
- evidence: `tmp/wifi/v786-clean-dsp-v724-gap/`

## What Ran

```bash
python3 -m py_compile scripts/revalidation/native_wifi_clean_dsp_v724_gap_v786.py
python3 scripts/revalidation/native_wifi_clean_dsp_v724_gap_v786.py plan
python3 scripts/revalidation/native_wifi_clean_dsp_v724_gap_v786.py run
```

V786 was host-only.  It did not execute any device command, reboot, flash, Wi-Fi
trigger, Wi-Fi HAL, scan/connect, credential use, DHCP, route change, or
external ping.

## Key Findings

| Signal | Result |
| --- | --- |
| V775 custom-kernel route | paused |
| v724 source contains V641 flag/runner/firmware mounts/nodes | yes |
| `stage3/boot_linux_v724.img` contains V641 markers | yes |
| v724 call order | QRTR hook line `963`, V641 hook line `964` |
| V782 V641 runtime marker count | `0` |
| V782 sibling sysmon count | `0` |
| V782 service-notifier count | `0` |
| V785 first divergence | `sysmon_slpi` |
| historical V641/V642/V644 clean-DSP branch | proven |
| service-74 warning risk | still present |

## Interpretation

Current v724 does not need a custom kernel or a rebuild to access the V641
clean-DSP one-shot path.  The hook is already present in source and in the local
v724 boot image.  V782 did not arm or execute that hook; it exercised the
lower-window `boot_wlan` path without clean-DSP preconditioning, which explains
why V785 still saw no sibling sysmon.

The next gate should therefore be narrower than a new kernel flash or a broader
CNSS/HAL retry: arm only `/cache/native-init-sibling-fwssctl-v641` on stock
v724, reboot, collect V641 proof/timeline/dmesg/rpmsg evidence, and stop.

## Safety

- device command: not executed
- boot image or partition write: not executed
- reboot: not executed
- custom OSRC kernel flash: not executed
- Wi-Fi HAL/service-manager: not executed
- scan/connect/credential use: not executed
- DHCP/routes/external ping: not executed
- `boot_wlan`, `qcwlanstate`, `esoc0`, bind/unbind, module load/unload: not
  executed

## Next

V787 should be a live arm-only proof on stock v724:

1. confirm current v724 health;
2. arm only `/cache/native-init-sibling-fwssctl-v641`;
3. reboot and collect V641 proof/timeline/dmesg/rpmsg evidence;
4. do not arm the v724 QRTR flag in the same boot;
5. do not start CNSS/HAL, scan/connect, DHCP, external ping, or flash a custom
   kernel.
