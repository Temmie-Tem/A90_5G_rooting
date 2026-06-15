# NATIVE_INIT V2497 — audio ACDB own-process namespace-aware loader design

Date: 2026-06-16

## Decision

`v2497-ownprocess-namespace-loader-design-host-only`

V2496 closed the plain `dlopen()` variants for the `/data/local/tmp` standalone
helper context:

- V2494: soname `dlopen("libaudcal.so", RTLD_NOW)` failed as not found even
  though `/vendor/lib/libaudcal.so` exists.
- V2496: absolute-path `dlopen("/vendor/lib/libaudcal.so", RTLD_NOW)` also
  failed as not found while the file exists.

This is now a linker namespace/policy wall for the current context, not a path or
flag issue. Repeating same-context soname/absolute `dlopen()` is low-information
churn.

## External source check

Primary sources confirm the intended bounded mechanism:

- Android's linker namespace documentation says isolated namespaces restrict
  load paths to their `search.paths` / `permitted.paths`, and that a visible
  namespace can be obtained with `android_get_exported_namespace()` and then used
  with `android_dlopen_ext()`.
  - Source: https://source.android.com/docs/core/architecture/vndk/linker-namespace
- The same documentation explicitly notes Android 11+ generates linker config
  at runtime under `/linkerconfig`, and that `namespace.sphal.visible = true`
  means `android_get_exported_namespace("sphal")` can return a usable handle.
  - Source: https://source.android.com/docs/core/architecture/vndk/linker-namespace
- AOSP `libvndksupport` implements the practical strategy: try exported namespace
  names `sphal`, `vendor`, then `default`; when a namespace handle exists, call
  `android_dlopen_ext()` with `ANDROID_DLEXT_USE_NAMESPACE` and that namespace.
  - Source: https://android.googlesource.com/platform/system/core/+/android16-qpr2-release/libvndksupport/linker.cpp
- Android NDK `libdl` docs define `ANDROID_DLEXT_USE_NAMESPACE` as the flag used
  to load a library in a different namespace, with the namespace passed in
  `android_dlextinfo.library_namespace`; `android_dlopen_ext()` otherwise uses
  the same filename/flags semantics as `dlopen()`.
  - Source: https://developer.android.com/ndk/reference/group/libdl
- AOSP bionic `dlext.h` pins `ANDROID_DLEXT_USE_NAMESPACE = 0x200` and the
  `android_dlextinfo` struct includes `library_namespace`.
  - Source: https://android.googlesource.com/platform/bionic/+/main/libc/include/android/dlext.h

## Local evidence

Private on-device evidence from V2494/V2496:

```text
-rw-r--r-- 1 root root 162124 /vendor/lib/libaudcal.so
-rw-r--r-- 1 root root  92500 /vendor/lib/libacdbloader.so
```

Current private workspace evidence has only the vendor ACDB libs copied under
`workspace/private/runs/audio/v2324-aud0-inventory/vendor_dump/...`; it does not
currently include Android `/linkerconfig` or 32-bit `/system/lib/libdl.so` /
`libc.so` symbol dumps. Therefore V2498 should make the namespace API probe
self-describing at runtime rather than assuming which namespace names are visible.

## V2498 implementation design

Modify the existing own-process helper, preserving pure-read ACDB behavior:

1. Keep `RTLD_NOW` only.
2. Add explicit declarations, still no libc/NDK headers:
   - opaque `struct android_namespace_t;`
   - `void *android_get_exported_namespace(const char *name);`
   - `void *android_dlopen_ext(const char *filename, int flags, const android_dlextinfo *info);`
   - local `android_dlextinfo` layout with `uint64_t flags`, reserved fields,
     fd fields, offset, and `library_namespace`.
   - `ANDROID_DLEXT_USE_NAMESPACE = 0x200`.
3. Probe namespace names in order: `sphal`, `vendor`, `default`, `vndk`.
   - Record one JSONL `namespace_probe` event per name with `found=true/false`.
4. For each found namespace, try loading `/vendor/lib/libaudcal.so` with
   `android_dlopen_ext(..., RTLD_NOW, {.flags=ANDROID_DLEXT_USE_NAMESPACE,
   .library_namespace=ns})`.
   - Stop on first success and record `namespace_selected`.
   - If all namespace attempts fail, record per-namespace `dlerror()` details and
     exit before loading `libacdbloader.so`.
5. Use the same selected namespace to load `/vendor/lib/libacdbloader.so`.
6. Keep existing `dlsym(acdb_loader_init_v3)` and `dlsym(acdb_ioctl)` logic.
7. Keep the operator GET matrix unchanged: `{0x11394, 0x12E01, 0x130DA,
   0x130DC}`, pure-read only.
8. Preserve private raw output policy and 4916/no-4916 partial-success policy.

## Validation additions

V2498 host-only verifier/tests should require:

- `android_dlopen_ext` token present;
- `android_get_exported_namespace` token present;
- `ANDROID_DLEXT_USE_NAMESPACE` token and value `0x200` present;
- namespace probe names include `sphal`, `vendor`, `default`, `vndk`;
- previous boundaries still true: no `/dev/msm_audio_cal`, no SET ioctl constant,
  no HAL injection, no playback, no Magisk module install.

Build checks should accept undefined dynamic linker imports if the Android linker
exports them through `libdl`/linker runtime on-device. If the host link step needs
a stub symbol for tests, the stub must stay private to the build harness and not
change device behavior.

## Live expectations after V2498

A future V2499 live run should be classified into one of these buckets:

- `namespace-api-symbol-missing`: helper cannot resolve namespace APIs;
- `namespace-none-visible`: all namespace probes return null;
- `namespace-visible-load-failed`: namespace exists but `android_dlopen_ext` still
  rejects `/vendor/lib/libaudcal.so`, with per-namespace `dlerror()`;
- `libaudcal-loaded-libacdbloader-block`: first library loads, second blocks;
- `init-v3-block`: both libraries/symbols load, but `acdb_loader_init_v3` fails;
- `acdb-get-success-4916`: raw 4916 topology captured privately;
- `acdb-get-full-outbuf-set-no-4916`: ordered out-buffer set captured but no 4916;
  operator-valuable partial success, not a dead retry.

## Boundary

This design does not resume in-HAL LD_PRELOAD/wrapper-exec. It keeps the
own-process path, no playback, no native speaker writes, and no
`/dev/msm_audio_cal` calibration SET ioctl. It also avoids copying vendor `.so`
files into tracked public paths.
