# v146 Plan: Long Soak Foundation

Date: `2026-05-08`
Target: `A90 Linux init 0.9.46 (v146)` / `0.9.46 v146 LONG SOAK FOUNDATION`
Baseline: `A90 Linux init 0.9.45 (v145)`

## Summary

v146 starts the long-duration stability track before broader network/Wi-Fi work.
The design intentionally splits observation into two sides:

- device-side recorder keeps sampling even when the host/USB bridge disconnects;
- host-side harness records PC-to-device command reachability, latency, and failures.

## Scope

- Copy v145 into `init_v146.c` and `v146/*.inc.c` with version/changelog bump.
- Add `/bin/a90_longsoak` static ARM64 helper.
- Add `a90_longsoak.c/h` PID1 control API and `longsoak` shell command.
- Track `longsoak` in the service registry as a monitor service.
- Add `scripts/revalidation/native_long_soak.py` host observation harness.
- Keep NCM/Wi-Fi bring-up and 24h soak policy for later versions.

## Validation

- Static ARM64 build for PID1 and helper.
- Real-device flash and `cmdv1 version/status` verify.
- `native_long_soak.py` short host/device observation run.
- `longsoak status` and `longsoak tail` device-side sample evidence.
- Integrated validation, quick soak, and local targeted security rescan.
