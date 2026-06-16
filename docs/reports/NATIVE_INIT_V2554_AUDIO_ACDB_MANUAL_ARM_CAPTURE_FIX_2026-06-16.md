# NATIVE_INIT V2554 — ACDB manual-arm capture fix

Date: 2026-06-16

## Scope

Host-only correction for the V2553 own-process ACDB full-manifest capture path.
No device action, no flash, no Android boot, no raw ACDB payload committed.

The operator handover identified the V2538/V2535 instability class: the
`acdb_ioctl` wrapper must not dump during ACDB init. It must pass through all
init-time calls silently, then dump only after the helper explicitly arms capture
after `acdb_loader_init_v3()` returns.

## Change

- Removed the automatic `acdb_ioctl` arming path tied to `ACDB_CMD_INITIALIZE_V2`.
- Kept the exported `a90_arm_capture()` setter as the only arm transition.
- Updated the V2553 build manifest contract to say `manual-arm acdb_ioctl dump after init_v3`.
- Added a source-state/test guard that rejects reintroducing
  `cmd == A90_CMD_INITIALIZE_V2` auto-arm behavior.

## Private Artifact Result

The rebuilt private V2553 artifacts remain under
`workspace/private/builds/audio/v2553-acdb-full-manifest-capture-host-only/`.

| Artifact | SHA-256 | Note |
| --- | --- | --- |
| `a90_acdb_full_manifest_exec_linked_v2553` | `d93bbeb645dbb48f34f50451338058ce5c8b5648ee707aea889fcd03cd795406` | unchanged helper |
| `liba90_acdb_full_manifest_preload_v2553.so` | `a271fcda7260e0175a19cb0b3ed0c7c505b2835a018522ddfe536afe64c1db36` | rebuilt manual-arm preload |

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/build_android_acdb_full_manifest_v2553.py`
- `PYTHONPATH=tests python3 -m unittest tests.test_build_android_acdb_full_manifest_v2553`
- `python3 workspace/public/src/scripts/revalidation/build_android_acdb_full_manifest_v2553.py --build`
- `git diff --check`

All passed. The private manifest reports:

- `ok=true`
- `tap_manual_arm_only=true`
- preload policy `manual-arm acdb_ioctl dump after init_v3, no exit on 4916, fake audio calibration ioctls when A90_ACDB_FAKE_ALLOCATE=1`

## Next Unit

V2555 should be the Android own-process live handoff using the rebuilt V2553
helper/preload:

1. boot stock Android through the checked handoff;
2. stage the helper, manual-arm preload, and ACDB dependency closure;
3. run with `LD_PRELOAD=<manual-arm preload>` and `A90_ACDB_FAKE_ALLOCATE=1`;
4. pull the full ordered `/data/local/tmp/a90-acdb-tap/` and own-process event set privately;
5. classify success only for `ret==0` and non-all-zero buffers, with the topology `out_len==4916`
   plus any per-device records preserved in order;
6. rollback to V2321 and verify `selftest fail=0`.

