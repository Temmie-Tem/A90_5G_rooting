# NATIVE_INIT V2620 — ACDB VOL-isolated build

Date: 2026-06-16

## Scope

Host-only build-only unit after V2618/V2619. V2618 captured AFE/AUDPROC
payload candidates but SIGSEGVed after entering `0x12eeb` before the VOL
sweep. V2620 builds a helper/preload pair that keeps the proven init and
manual-arm capture path, skips `0x12eeb`, and runs only the safe prelude plus
VOL direct GET commands. No device handoff or native replay occurred.

## Decision

- decision: `v2620-acdb-vol-isolated-build-only`
- ok: `True`
- build_root: `workspace/private/builds/audio/v2620-acdb-vol-isolated-build-only`
- helper: `workspace/private/builds/audio/v2620-acdb-vol-isolated-build-only/bin/a90_acdb_vol_isolated_exec_linked_v2620`
- helper_sha256: `682f7a1438d22728a248698cfd8f521e5e1152b3b80060f3ac3de0876617532a`
- preload: `workspace/private/builds/audio/v2620-acdb-vol-isolated-build-only/bin/liba90_acdb_vol_isolated_combined_preload_v2620.so`
- preload_sha256: `1b3393576583a069fa131c37e4ed0b604e8afa97c30058e1a927e0822b1de40f`

## Contract

- safe_prelude_commands: `['0x1122e', '0x1122d']`
- skipped_v2618_crash_command: `0x12eeb`
- vol_sweep: `{'commands': ['0x1326d', '0x1326e'], 'gain_steps': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]}`
- `acdb_ioctl` capture stays unarmed during init and arms only after `init_v3` returns.
- `send_audio_cal_v5`, `/dev/msm_audio_cal` open, native replay `SET`, and speaker writes are absent.
- Live execution is deferred to the next checked Android-good handoff unit.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/build_android_acdb_vol_isolated_v2620.py tests/test_build_android_acdb_vol_isolated_v2620.py`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_build_android_acdb_vol_isolated_v2620 -v`
- `python3 workspace/public/src/scripts/revalidation/build_android_acdb_vol_isolated_v2620.py --build`
- `git diff --check`
