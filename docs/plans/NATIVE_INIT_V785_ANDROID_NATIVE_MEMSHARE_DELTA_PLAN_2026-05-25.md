# Native Init V785 Android/Native Memshare Delta Plan

## Goal

Use existing Android V611 lower-surface evidence to decide whether the native
memshare/CMA failure from V782 is the actual Wi-Fi blocker or a common non-fatal
event.  V784 showed idle native CMA headroom is not obviously too small; V785
compares Android and native failure sizes and the downstream chain.

## Scope

- Host-only analysis.
- No Android handoff, device command, Wi-Fi trigger, reboot, flash, or
  credential use.
- Compare exact V611 Android dmesg with V782 native dmesg and V784 native
  memshare/CMA surface.

## Inputs

- Android dmesg: `tmp/wifi/v612-android-lower-surface-handoff-20260523-011739/v611-android-lower-surface-recapture-run/android/commands/dmesg-lower-surface-tail.txt`
- Android state: `tmp/wifi/v612-android-lower-surface-handoff-20260523-011739/v611-android-lower-surface-recapture-run/android-lower-surface-state.txt`
- Android manifest: `tmp/wifi/v612-android-lower-surface-handoff-20260523-011739/v611-android-lower-surface-recapture-run/manifest.json`
- Native V782 dmesg: `tmp/wifi/v782-bpf-counter-boot-wlan/native/dmesg-delta.txt`
- Native V782 manifest: `tmp/wifi/v782-bpf-counter-boot-wlan/manifest.json`
- V784 manifest: `tmp/wifi/v784-memshare-cma-surface/manifest.json`

## Method

1. Parse Android/native memshare request sizes, failed sizes, and CMA failures.
2. Compare Android/native lower-chain markers from QRTR through `wlan0`.
3. Identify the first marker present in Android but absent in native.
4. Use Android success after memshare failure to decide whether memshare/CMA is
   a terminal blocker or a common non-fatal event.
5. Select the next live target without repeating blind `boot_wlan`,
   `qcwlanstate`, or memshare-only probes.

## Success Criteria

- Required evidence files exist.
- Android and native memshare/CMA failure evidence is parsed.
- Android downstream success after memshare failure is proven from evidence.
- Native stop point is classified.
- Next work points closer to Wi-Fi bring-up.

## Safety Boundaries

- no device command
- no Android handoff
- no boot image or partition write
- no reboot
- no Wi-Fi HAL/service-manager start
- no scan/connect/credential use
- no DHCP/routes/external ping
- no `boot_wlan`, `qcwlanstate ON`, module load/unload, bind/unbind, or
  `esoc0` access

## Runner

```bash
python3 -m py_compile scripts/revalidation/native_wifi_android_native_memshare_delta_v785.py
python3 scripts/revalidation/native_wifi_android_native_memshare_delta_v785.py plan
python3 scripts/revalidation/native_wifi_android_native_memshare_delta_v785.py run
```
