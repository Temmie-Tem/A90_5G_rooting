# Native Init v141 LOG/NETWORK App Renderer Report

Date: `2026-05-08`
Version: `A90 Linux init 0.9.41 (v141)` / `0.9.41 v141 LOG NETWORK APP API`
Baseline: `A90 Linux init 0.9.40 (v140)`

## Summary

- Added `a90_app_log.c/h` and `a90_app_network.c/h`.
- Removed LOG and NETWORK summary renderer ownership from `v141/40_menu_apps.inc.c`.
- Preserved screen menu routing, netservice policy, exposure guardrails, storage, and shell behavior.
- Real-device flash, integrated validation, quick soak, and local targeted security rescan passed.

## Artifacts

| Artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v141` | `eadcac80ce21b6ba8253eb74ee47cd3aff22f433749db1fba5a81e414120b0c1` |
| `stage3/ramdisk_v141.cpio` | `82478b080a580ec4c677faaba70f28a3ebb24e3d18e49e54061c095c2ef89109` |
| `stage3/boot_linux_v141.img` | `92503d52ea753c45ed1f4c35a7bc5e0fe6b4de249c5cb1d6bf49415198e2d8ab` |

## Validation

- Static ARM64 build — PASS.
- `git diff --check` and host Python `py_compile` — PASS.
- Real-device flash with `native_init_flash.py` — PASS.
- `native_integrated_validate.py` — `PASS commands=25`.
- `native_soak_validate.py --cycles 3` — `PASS cycles=3 commands=14`.
- Local targeted security rescan — PASS=17/WARN=1/FAIL=0.

## Notes

- LOG/NETWORK app rendering is now a module boundary, but physical menu navigation UX is unchanged.
- The remaining accepted warning is the intentional trusted-lab USB ACM/local bridge root-control boundary.
