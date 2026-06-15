# NATIVE_INIT V2505 — audio ACDB local dependency staging live

Date: 2026-06-16

## Decision

`v2505-local-libaudcal-reached-missing-libdiag`

V2505 ran the V2504 own-process ACDB helper through one checked Android handoff,
staged the available private ACDB libraries next to the helper, and rolled back
to V2321. The local-path load changed the failure mode: the helper reached the
staged `/data/local/tmp/a90-acdb-ownget/libaudcal.so`, but the dynamic loader
then failed on its next DT_NEEDED dependency:

```text
library "libdiag.so" not found: needed by /data/local/tmp/a90-acdb-ownget/libaudcal.so
```

No ACDB GET call was reached. No raw ACDB payload was captured.

## Live Run

Private run directory, not committed:

```text
workspace/private/runs/audio/v2505-acdb-ownprocess-local-staging-live-20260616-025344
```

Runner decision:

```text
v2490-namespace-visible-load-failed-before-rollback-rollback-pass
```

The runner name/build tag remains the reused V2490 live handoff harness; the
iteration/result identity for this report is V2505.

Helper artifact used:

```text
path: workspace/private/builds/audio/v2489-acdb-ownprocess-get-host-only/bin/a90_acdb_ownprocess_get_v2489
sha256: 4fe262f5ef57390c306656ce6693ca57430b67479efac16c4b87f0ef75321834
```

Staged private ACDB libraries:

```text
libaudcal.so      sha256=3f214dc18758d360cbc39d8a5323ff76baf6b5eb6c247de141bd6d5e91f4295d
libacdbloader.so  sha256=25ae25afda6f52fc75d9b72e7f9df22094c7e3b243efb7257654ec9445bcd0a1
```

Sealed Android boot copy:

```text
sha256=c15ce425abb8da41f0b1696d19d05a625fd7cec949b4ae50651a5f1e7293057b
mode=0600
```

## Observed Events

The first local load attempt produced the decisive blocker:

```text
plain-local load /data/local/tmp/a90-acdb-ownget/libaudcal.so:
  failed: library "libdiag.so" not found: needed by /data/local/tmp/a90-acdb-ownget/libaudcal.so
```

The fallback namespace probes still matched the V2503 result:

```text
symbol_probe libdl:android_get_exported_namespace             found=false
symbol_probe default:android_get_exported_namespace           found=false
symbol_probe default:__loader_android_get_exported_namespace  found=true
symbol_probe libdl:android_dlopen_ext                         found=true

sphal   visible=true   load libaudcal.so: failed
sphal   visible=true   load /vendor/lib/libaudcal.so: failed
vendor  visible=false
default visible=true   load libaudcal.so: failed with local libdiag dependency error
default visible=true   load /vendor/lib/libaudcal.so: failed
vndk    visible=true   load libaudcal.so: failed
vndk    visible=true   load /vendor/lib/libaudcal.so: failed
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
namespace_event_count: 11
symbol_event_count: 4
ownget stdout/stderr: empty
```

## Dependency Interpretation

V2505 proves local staging is not blocked at the first library path. The next
blocker is the `libaudcal.so` dependency closure, starting with `libdiag.so`.

The current private V2324 vendor dump used by the runner does not contain:

```text
libdiag.so
libtinyalsa.so
libacdbrtac.so
libadiertac.so
libacdb-fts.so
libion.so
```

The next useful unit should not retry namespace names or in-HAL injection. It
should stage or pull the missing dependency closure into the same private
temporary directory, still using the own-process pure-read boundary. `libdiag.so`
is the first required addition; after `libaudcal.so` loads, `libacdbloader.so` is
expected to expose the remaining ACDB loader dependency set.

## Boundary Check

The live unit stayed inside the own-process pure-read boundary:

- no in-HAL `LD_PRELOAD` or wrapper-exec injection;
- no Magisk module install;
- no HAL restart;
- no AudioTrack/playback;
- no native speaker write;
- no `/dev/msm_audio_cal` open or SET ioctl;
- no `0xC00461CB` path;
- no `acdb_loader_send_common_custom_topology`;
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

## Validation

Commands/results:

```text
live runner: completed
artifact pull: completed
rollback to V2321: completed
post-rollback selftest: fail=0
git diff --check: pending at report creation
```

## Next Unit

Host-only first:

1. locate or pull `libdiag.so` and the remaining ACDB loader dependencies from a
   private stock Android/vendor source;
2. extend the V2504 local-staging dependency inventory without committing vendor
   libraries;
3. rerun the helper only after the dependency closure is complete enough to
   load `libaudcal.so` and then `libacdbloader.so`.

Do not return to in-HAL injection or wrapper-exec.
