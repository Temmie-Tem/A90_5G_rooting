# NATIVE_INIT V2586 — ACDB per-device RX cap-mask build

Date: 2026-06-16

## Scope

Host-only build-only unit after V2585. No Android handoff, device flash, native replay SET,
speaker write, or raw ACDB payload publication was performed.

## Decision

- decision: `v2586-acdb-perdevice-rx-capmask-build-only`
- ok: `True`
- build_root: `workspace/private/builds/audio/v2586-acdb-perdevice-rx-capmask-build-only`
- helper: `workspace/private/builds/audio/v2586-acdb-perdevice-rx-capmask-build-only/bin/a90_acdb_perdevice_rx_capmask_exec_linked_v2586`
- helper_sha256: `5cc7b9c6f2bacdb7c4789bb9f9f62ec2f2ec7488e9124e97b0364b3644af023d`
- preload: `workspace/private/builds/audio/v2586-acdb-perdevice-rx-capmask-build-only/bin/liba90_acdb_perdevice_rx_capmask_capture_v2586.so`
- preload_sha256: `f247bd9e2afa31ef872bf59d6a25d060947a7bfe364a41b2fec58956fdbe5107`

## Why This Unit

V2585 safely exhausted the current direct `store_get` selector guesses: the hook entered and
all five cases returned `-19`/`-20` with zero output. The active GOAL now explicitly reopens
the `send_audio_cal_v5` path because V2574/V2575 used `arg2=0`, and operator RE shows that
`(arg2 & 0x3)==0` bails before useful per-device GETs. This unit creates the same V2572
generic direct/indirect capture shape, but compiles the second argument as RX cap mask `1`.

## Contract

- future per-device call: `acdb_loader_send_audio_cal_v5(15, 1, 0x11135, 48000, 48000, 0, 1)`
- real common-topology public call stays skipped; V2547 already pinned topology.
- capture arms only after the initialized-flag patch inside the pre-init hook.
- `A90_ACDB_FAKE_ALLOCATE=1` remains required for any future live run.
- success remains `ret==0` plus non-all-zero direct/indirect payload, never requested length alone.
- native calibration replay SET and speaker playback remain blocked.

## Build Evidence

- preinit_compile_ok: `True`
- preinit_compile_command_contains_capmask: `True`
- helper_checks: `{'is_pie': True, 'entry_start': True, 'undefined_init_v3': True, 'needed_libacdbloader': True, 'needed_libaudcal': True, 'mode_0600': True}`
- preload_checks: `{'exports_acdb_ioctl': True, 'exports_ioctl': True, 'exports_common_topology': True, 'exports_a90_arm_capture': True, 'undefined_dlsym': True, 'undefined_errno': True, 'soname_v2586': True, 'mode_0600': True}`

## Next Unit

Add a V2587 live runner wrapper that selects these V2586 private artifacts and reuses the V2573
classification logic. The live unit should be a single rollbackable Android handoff and must
stop after preserving ordered ACDB tap records for operator Gate-2 mapping.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/build_android_acdb_perdevice_rx_capmask_v2586.py tests/test_build_android_acdb_perdevice_rx_capmask_v2586.py`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_build_android_acdb_perdevice_rx_capmask_v2586`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/build_android_acdb_perdevice_rx_capmask_v2586.py --build --write-report`
- `git diff --check`
