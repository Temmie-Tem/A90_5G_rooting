# NATIVE_INIT V2502 — audio ACDB soname namespace fallback host-only

Date: 2026-06-16

## Decision

`v2502-acdb-soname-namespace-fallback-host-only`

V2501 proved the helper can resolve the device's loader-private namespace getter
and can enumerate visible namespaces, but every load of the absolute path
`/vendor/lib/libaudcal.so` failed with `library ... not found`. V2502 is a
host-only helper update for the next live handoff. It fixes two linker-assumption
problems before any further device run:

1. the helper now uses Android's 32-bit `RTLD_DEFAULT` sentinel instead of a null
   handle for default-scope `dlsym()` probes;
2. namespaced loads now try the library soname first and the absolute vendor path
   second.

No live device action was performed in this unit.

## Source Basis

AOSP bionic source supports both changes:

- Android 32-bit `RTLD_DEFAULT` is `((void*) 0xffffffff)`, not NULL. Source:
  https://android.googlesource.com/platform/bionic/+/d51bc71/libc/include/dlfcn.h
- Android's linker treats filenames containing `/` as direct paths instead of
  namespace search-path lookups. Source:
  https://android.googlesource.com/platform/bionic/+/master/linker/linker.cpp

This matches V2501's symptoms: default-scope probes using NULL returned
`library handle is null`, and absolute-path namespace loads reported the vendor
library as not found despite visible `sphal`/`default`/`vndk` namespaces.

## Implementation

Updated `workspace/public/src/android/acdb_payload_capture/a90_acdb_ownprocess_get_v2489.c`:

- added `A90_RTLD_DEFAULT ((void *)0xffffffffU)` and uses it for default-scope
  `dlsym()` symbol probes;
- added `libaudcal` load candidates:
  - `libaudcal.so`
  - `/vendor/lib/libaudcal.so`
- added `libacdbloader` load candidates:
  - `libacdbloader.so`
  - `/vendor/lib/libacdbloader.so`
- added a bounded helper to try candidate library names in the selected namespace
  and record every `namespace_load` attempt.

The capture contract remains unchanged after library load:

- resolve `acdb_loader_init_v3` and `acdb_ioctl`;
- call `acdb_loader_init_v3("/vendor/etc/acdbdata", <delta-dir>, 0)`;
- issue only the bounded pure-read GET command matrix;
- dump raw out-buffers privately only.

## Boundary Check

Unchanged hard boundaries:

- no `/dev/msm_audio_cal`;
- no `0xC00461CB`;
- no `AUDIO_SET_CALIBRATION` or calibration SET path;
- no `acdb_loader_send_common_custom_topology`;
- no HAL injection, Magisk module, HAL restart, AudioTrack/playback, or native
  speaker write;
- no raw ACDB payload committed.

The public helper still imports only `dlopen`, `dlsym`, and `dlerror`; Android
namespace symbols remain runtime-probed strings, not ELF undefined imports.

## Private Build Artifact

Private build output, not committed:

```text
path: workspace/private/builds/audio/v2489-acdb-ownprocess-get-host-only/bin/a90_acdb_ownprocess_get_v2489
sha256: 86da1cc9b415ba848f35800032bcf752a12b3b59ae0c55da43c6def40d80a836
file: ELF 32-bit LSB shared object, ARM, EABI5, dynamically linked, interpreter /system/bin/linker
readelf undefined imports: dlopen, dlsym, dlerror only
```

## Validation

Commands run:

```text
python3 -m py_compile \
  workspace/public/src/scripts/revalidation/build_android_acdb_ownprocess_get_v2489.py \
  tests/test_build_android_acdb_ownprocess_get_v2489.py

PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest \
  tests.test_build_android_acdb_ownprocess_get_v2489 -v

python3 workspace/public/src/scripts/revalidation/build_android_acdb_ownprocess_get_v2489.py --build

python3 workspace/public/src/scripts/revalidation/native_audio_acdb_ownprocess_get_live_handoff_v2490.py \
  --dry-run --from-native
```

Result:

```text
py_compile: pass
unit tests: 5 passed
source required_ok: true
source prohibited_ok: true
build: ok
live dry-run: live_ready=true, command_safety.ok=true
```

The live dry-run now selects helper SHA:

```text
86da1cc9b415ba848f35800032bcf752a12b3b59ae0c55da43c6def40d80a836
```

## Next Unit

Run one bounded Android handoff with the V2502 helper. Expected decisive signal:

- if `libaudcal.so` loads by soname, proceed to `libacdbloader.so`, init-v3, and
  the pure-read GET matrix;
- if soname and absolute path both fail in all visible namespaces, the own-process
  namespace path is blocked by linkerconfig policy and the next unit should stage
  private same-directory copies of the ACDB dependency set or inspect `/linkerconfig`
  and device linker metadata privately.

Do not return to in-HAL injection or wrapper-exec.
