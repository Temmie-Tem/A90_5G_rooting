# Native Init v146 Long Soak Foundation Report

Date: `2026-05-08`
Version: `A90 Linux init 0.9.46 (v146)` / `0.9.46 v146 LONG SOAK FOUNDATION`
Baseline: `A90 Linux init 0.9.45 (v145)`

## Summary

- Added `/bin/a90_longsoak`, a device-side JSONL recorder for battery, thermal, memory, load, power, and uptime samples.
- Added `a90_longsoak.c/h` and `longsoak [status|start|stop|path|tail]` shell control.
- Added service registry metadata for the `longsoak` monitor service.
- Added `scripts/revalidation/native_long_soak.py` to record host cmdv1 reachability alongside device recorder state.
- Verified the design on real hardware with flash, short long-soak run, integrated validation, quick soak, and local security scan.

## Artifacts

| Artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v146` | `634ceed19c87812afbe9875d4d370d8fb13e14b0d2a93ca9c084e815473d392d` |
| `stage3/linux_init/helpers/a90_longsoak` | `1d15080f6361ca194d115d05f3cefa546d97dfe963c1b0afa36f9447208f64c3` |
| `stage3/ramdisk_v146.cpio` | `1c4c1e5681d252238e6d86103767ded5b2fb2ebeddaccec90ef7617a488ed684` |
| `stage3/boot_linux_v146.img` | `5164cc0ecf431127681f2ac1e198301b706745cb1df09c9892929f314dbe9ce6` |

## Validation

- Static ARM64 build for `init_v146` and `a90_longsoak` — PASS.
- `git diff --check` and host Python `py_compile` — PASS.
- Real-device flash with `native_init_flash.py` — PASS.
- `native_long_soak.py --duration-sec 10 --device-interval 2 --start-device` — `PASS samples=8 failures=0`.
- `longsoak tail 3` showed device JSONL samples and final stop event from `/mnt/sdext/a90/logs/longsoak-v146-19358.jsonl`.
- `native_integrated_validate.py` — `PASS commands=25`.
- `native_soak_validate.py --cycles 3` — `PASS cycles=3 commands=14`.
- Local targeted security rescan — PASS=17/WARN=1/FAIL=0.

## Notes

- v146 is the foundation only; it does not attempt 24h soak or network correlation yet.
- The device-side recorder is independent from the host harness, so samples continue while the PC bridge is disconnected.
- `longsoak` is allowed through the menu controller policy because it is a monitoring control, not a network/root-exposure feature.
