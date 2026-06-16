# NATIVE_INIT V2553 — ACDB full-manifest capture build gate

Date: 2026-06-16
Run ID: V2553
Build tag: v2553-acdb-full-manifest-capture-host-only
Scope: native audio / ACDB per-device calibration capture preparation

## Purpose

V2552 proved the native path can materialize `/dev/ion`, issue the topology-only
`AUDIO_SET_CALIBRATION` for cal_type `39`, and explicitly deallocate. It still failed at PCM
write/prepare with `EINVAL`, matching the earlier evidence that topology alone is insufficient:
per-device AFE / AUDPROC / ASM / ADM / VOL calibration is still missing.

V2553 prepares the next substantive unit: capture the full ordered ACDB out-buffer manifest from
stock `libacdbloader.so` without another HAL injection attempt and without a native speaker write.
This is host-only build preparation for a later recoverable live measurement.

## Design

The V2553 approach reuses the working V2547/V2540 own-process path, but changes the target from
"topology only" to "topology plus speaker per-device calibration":

1. initialize ACDB with `acdb_loader_init_v3("/vendor/etc/audconf/OPEN", delta_dir, 0)`;
2. call exported `a90_arm_capture()` after init so init-time `acdb_ioctl` calls remain pass-through;
3. call `acdb_loader_send_common_custom_topology()` to capture the custom topology GETs;
4. call `acdb_loader_send_audio_cal_v5(15, 0, 0x11135, 48000, 48000, 0, 1)` to trigger the same
   speaker/media per-device ACDB fetch path observed in Android-good logs;
5. pair the helper with a combined preload that:
   - interposes `acdb_ioctl` and dumps all `out_len>0` buffers after arming;
   - no longer exits after the first valid 4916-byte topology record;
   - interposes `ioctl` and fake-succeeds `AUDIO_ALLOCATE_CALIBRATION`,
     `AUDIO_DEALLOCATE_CALIBRATION`, and `AUDIO_SET_CALIBRATION` when
     `A90_ACDB_FAKE_ALLOCATE=1` is set.

The helper itself does not open the audio-calibration device and does not issue any ioctl. The
future live run must use the fake-ioctl preload to prevent libacdbloader's normal SET path from
reaching the kernel while still allowing all read-side `acdb_ioctl` GETs to run.

## Implemented files

- `workspace/public/src/android/acdb_payload_capture/a90_acdb_full_manifest_exec_linked_v2553.c`
  - new ARM32 own-process helper;
  - direct DT_NEEDED-style calls into stock `libacdbloader.so`;
  - calls both topology and `send_audio_cal_v5` speaker calibration edges;
  - writes only small helper stage events under `/data/local/tmp/a90-acdb-ownget/`.
- `workspace/public/src/android/acdb_payload_capture/libacdbtap_v2475.c`
  - added `A90_ACDBTAP_EXIT_ON_TARGET`, defaulting to `1` to preserve old behavior;
  - V2553 builds it with `-DA90_ACDBTAP_EXIT_ON_TARGET=0` so capture continues after topology.
- `workspace/public/src/scripts/revalidation/build_android_acdb_full_manifest_v2553.py`
  - host-only builder for the helper PIE and no-exit combined preload;
  - validates source boundaries, vendor symbols, ELF properties, exported symbols, and private modes.
- `tests/test_build_android_acdb_full_manifest_v2553.py`
  - focused source-state, dry-run, and private build tests.

## Private build outputs

The build produced private artifacts under:

```text
workspace/private/builds/audio/v2553-acdb-full-manifest-capture-host-only/
```

Helper:

```text
workspace/private/builds/audio/v2553-acdb-full-manifest-capture-host-only/bin/a90_acdb_full_manifest_exec_linked_v2553
sha256=d93bbeb645dbb48f34f50451338058ce5c8b5648ee707aea889fcd03cd795406
mode=0600
```

Combined preload:

```text
workspace/private/builds/audio/v2553-acdb-full-manifest-capture-host-only/bin/liba90_acdb_full_manifest_preload_v2553.so
sha256=98d684f8af27c1bbd17325f2acfe6120ee4886c0a5a4246431a4eefa5edd14ac
mode=0600
```

These binaries are private and are not committed.

## Validation

Commands run:

```bash
python3 -m py_compile \
  workspace/public/src/scripts/revalidation/build_android_acdb_full_manifest_v2553.py

PYTHONPATH=tests python3 -m unittest \
  tests.test_build_android_acdb_full_manifest_v2553

python3 workspace/public/src/scripts/revalidation/build_android_acdb_full_manifest_v2553.py
python3 workspace/public/src/scripts/revalidation/build_android_acdb_full_manifest_v2553.py --build
```

Results:

- source-state dry-run: `ok=true`;
- focused tests: `3` tests passed;
- private build manifest: `ok=true`;
- helper checks passed:
  - PIE/DYN ELF;
  - `NEEDED libacdbloader.so` and `NEEDED libaudcal.so`;
  - undefined imports for `acdb_loader_init_v3`, `acdb_loader_send_common_custom_topology`,
    `acdb_loader_send_audio_cal_v5`, and `a90_arm_capture`;
- preload checks passed:
  - exports `acdb_ioctl`, `ioctl`, and `a90_arm_capture`;
  - SONAME is `liba90_acdb_full_manifest_preload_v2553.so`.

## Boundaries

No device action occurred in V2553.

The future live unit must remain measurement-only:

- run under stock Android / su own-process helper, not in-HAL injection;
- set `A90_ACDB_FAKE_ALLOCATE=1`;
- set `LD_PRELOAD` to the V2553 combined preload;
- preserve raw buffers only under `workspace/private/`;
- no native speaker write, no native route write, no real audio calibration SET ioctl to the kernel;
- checked rollback to V2321 if the live handoff boots Android.

## Conclusion

V2553 closes the host-side build gap for the next ACDB calibration frontier. The project now has a
private ARM32 helper/preload pair capable of collecting topology plus speaker per-device
`acdb_ioctl` out-buffer records, while suppressing the kernel SET path through the fake-ioctl
preload.

Next meaningful unit: a recoverable live Android/own-process measurement runner that stages the
V2553 helper/preload/dependencies, runs with `A90_ACDB_FAKE_ALLOCATE=1`, pulls the ordered private
manifest, and classifies whether non-zero topology plus per-device cal records were captured.
