# NATIVE_INIT V2503 — audio ACDB soname namespace fallback live

Date: 2026-06-16

## Decision

`v2503-namespace-visible-load-failed-libaudcal`

V2503 ran the V2502 helper once through the checked Android handoff and rolled
back to V2321. The 32-bit `RTLD_DEFAULT` fix worked: default-scope symbol probes
now execute as real linker probes instead of failing with `library handle is
null`. The soname fallback also executed. However, `libaudcal.so` and
`/vendor/lib/libaudcal.so` both failed to load in every visible namespace.

No ACDB GET call was reached. No raw ACDB payload was captured.

## Live Run

Private run directory, not committed:

```text
workspace/private/runs/audio/v2503-acdb-ownprocess-soname-live-20260616-024058
```

Helper artifact used:

```text
path: workspace/private/builds/audio/v2489-acdb-ownprocess-get-host-only/bin/a90_acdb_ownprocess_get_v2489
sha256: 86da1cc9b415ba848f35800032bcf752a12b3b59ae0c55da43c6def40d80a836
```

Runner decision:

```text
v2490-namespace-visible-load-failed-before-rollback-rollback-pass
```

The runner name/build tag remains the reused V2490 live handoff harness; the
iteration/result identity for this report is V2503.

## Observed Events

`symbol_probe` records:

```text
libdl:android_get_exported_namespace                 found=false detail="undefined symbol: android_get_exported_namespace"
default:android_get_exported_namespace               found=false detail="undefined symbol: android_get_exported_namespace"
default:__loader_android_get_exported_namespace      found=true
libdl:android_dlopen_ext                             found=true
```

Compared with V2501, the default-scope probe no longer fails with `library handle
is null`; the ARM32 `RTLD_DEFAULT` sentinel is correct. The public
`android_get_exported_namespace` wrapper is still absent, but the loader-private
namespace getter remains visible.

Namespace/library load attempts:

```text
sphal   visible=true   load libaudcal.so: failed, not found
sphal   visible=true   load /vendor/lib/libaudcal.so: failed, not found
vendor  visible=false
default visible=true   load libaudcal.so: failed, not found
default visible=true   load /vendor/lib/libaudcal.so: failed, not found
vndk    visible=true   load libaudcal.so: failed, not found
vndk    visible=true   load /vendor/lib/libaudcal.so: failed, not found
```

Final helper error:

```text
stage: namespace-visible-load-failed-libaudcal
code: -5
```

Artifact summary:

```text
acdb_ioctl row_count: 0
raw_file_count: 0
target_4916_count: 0
namespace_event_count: 10
symbol_event_count: 4
ownget stdout/stderr: empty
```

## Boundary Check

The live unit stayed inside the own-process pure-read boundary:

- no in-HAL `LD_PRELOAD` or wrapper-exec injection;
- no Magisk module install;
- no HAL restart;
- no AudioTrack/playback;
- no native speaker write;
- no `/dev/msm_audio_cal` open or SET ioctl;
- no `0xC00461CB` path;
- no raw payload committed.

## Rollback / Health

The checked handoff booted Android, staged and ran the helper, pulled the private
artifact directory, cleaned `/data/local/tmp/a90-acdb-ownget`, rebooted recovery,
and flashed V2321 through `native_init_flash.py`.

Post-rollback native health was verified:

```text
version: 0.9.285 build=v2321-usb-clean-identity-rodata
selftest: fail=0
```

The selftest output contained a stray serial byte in the prompt line, but the
protocol end marker and `fail=0` result were present. The device is back on V2321.

## Interpretation

V2503 closes the cheap namespace-name hypothesis. The own-process helper can
reach the namespace APIs and can see `sphal`, `default`, and `vndk`, but those
namespaces do not resolve `libaudcal.so` by soname or absolute vendor path for
this shell/su process.

The next useful unit should not retry namespace name variants. The next bounded
step is to remove namespace search from the equation by staging private copies of
the ACDB dependency set into the same temporary helper directory and loading them
by local path, still with the same pure-read boundary:

```text
/data/local/tmp/a90-acdb-ownget/libaudcal.so
/data/local/tmp/a90-acdb-ownget/libacdbloader.so
/data/local/tmp/a90-acdb-ownget/libacdb-fts.so
/data/local/tmp/a90-acdb-ownget/libacdbrtac.so
/data/local/tmp/a90-acdb-ownget/libadiertac.so
```

The report should also preserve a host-only option to inspect `/linkerconfig` and
device linker metadata privately, but that is diagnostic. The direct unblock path
is same-directory dependency staging.

Do not return to in-HAL injection or wrapper-exec.
