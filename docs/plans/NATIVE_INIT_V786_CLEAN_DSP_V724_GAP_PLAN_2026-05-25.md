# Native Init V786 Clean-DSP/v724 Gap Plan

## Goal

Reconcile the V775 custom-kernel pause and the V785 Android/native sibling
sysmon gap against the current stock v724 source and boot image.  The key
question is whether the V641 clean-DSP one-shot path is missing from v724, or
present but not exercised by V782.

## Scope

- Host-only analysis.
- No device command, reboot, boot image write, partition write, Wi-Fi HAL,
  scan/connect, credential use, DHCP, route change, or external ping.
- Read only exact source and evidence files; no broad tmp or kernel tree scan.

## Inputs

- `stage3/linux_init/v724/90_main.inc.c`
- `stage3/linux_init/v641/90_main.inc.c`
- `stage3/boot_linux_v724.img`
- `tmp/wifi/v775-boot-incompat-postmortem/manifest.json`
- `tmp/wifi/v782-bpf-counter-boot-wlan/manifest.json`
- `tmp/wifi/v782-bpf-counter-boot-wlan/native/dmesg-delta.txt`
- `tmp/wifi/v785-android-native-memshare-delta/manifest.json`
- V641/V642/V644/V645/V768 reports

## Method

1. Confirm V775 keeps custom OSRC-kernel flashing paused.
2. Scan current v724 source and boot image for the V641 one-shot flag, firmware
   mount path, ADSP/CDSP/SLPI nodes, and call site.
3. Check whether V782 actually executed V641 runtime markers or sibling sysmon.
4. Compare historical V641/V642/V644 clean-DSP branch evidence and warning risk.
5. Select the next gate without repeating blind `boot_wlan`, mdm_helper, esoc,
   subsystem writes, or custom-kernel flashing.

## Success Criteria

- Required exact files exist.
- v724 clean-DSP hook presence is classified from source and boot image.
- V782 clean-DSP execution state is classified from existing evidence.
- Historical clean-DSP branch and service-74 warning boundary are preserved.
- Next gate is narrow and rollback-aware.

## Safety Boundaries

- no device command
- no reboot
- no boot image or partition write
- no custom OSRC kernel flash
- no `boot_wlan`, `qcwlanstate`, CNSS/HAL, scan/connect, credentials,
  DHCP/routes, or external ping
- no raw `esoc0`, subsystem state write, bind/unbind, module load/unload, or
  late direct DSP boot-node write

## Runner

```bash
python3 -m py_compile scripts/revalidation/native_wifi_clean_dsp_v724_gap_v786.py
python3 scripts/revalidation/native_wifi_clean_dsp_v724_gap_v786.py plan
python3 scripts/revalidation/native_wifi_clean_dsp_v724_gap_v786.py run
```
