# NATIVE_INIT_V2476_AUDIO_ACDBTAP_LIVE_PLANNER_2026-06-15

## Decision

`v2476-acdbtap-live-planner-host-only`

V2476 adds the host-only live-run planner for using the V2475 ARM32
`libacdbtap.so` interposer in the stock Android audio HAL. No Android boot,
Magisk staging, HAL restart, AudioTrack playback, native speaker write, or
native `/dev/msm_audio_cal` calibration ioctl ran in this unit.

The generated private plan is:

- `workspace/private/runs/audio/v2476-acdbtap-live-plan/plan.json`

## Scope

Added:

- `workspace/public/src/scripts/revalidation/native_audio_acdbtap_live_planner_v2476.py`
- `tests/test_native_audio_acdbtap_live_planner_v2476.py`

Private-only staging performed:

- `workspace/private/inputs/audio/acdb-cross-validation/v2476/`

The staged private directory contains only currently available ACDB-related
libraries from the V2324 dump. It is not committed.

## Planner result

The planner verifies the V2475 tap artifact:

- path: `workspace/private/builds/audio/v2475-acdbtap-interposer-build/bin/libacdbtap.so`
- SHA-256: `7bf64bb04530202a8dc859db0826cd399ff34d51ea4628eb586808de82968be4`
- status: OK

The command-safety scan is OK. The future live recipe is marked ready from the
interposer/command-safety perspective, but the host cross-validation inventory is
incomplete:

- available dep libraries: `libacdbloader.so`, `libaudcal.so`
- missing requested dep libraries: `libacdb-fts.so`, `libacdbrtac.so`, `libadiertac.so`
- `.acdb` file count in current private dump: `0`
- private staged file count: `4` (32-bit and 64-bit `libacdbloader.so` / `libaudcal.so` copies)

This does **not** block the LD_PRELOAD capture path, because the live Android HAL
will use its real `/vendor` files. It only blocks offline host cross-validation
until a fuller vendor/acdbdata pull is provided.

## Live strategy pinned by V2476

The selected first live candidate is `manual-root-reexec-preload-candidate`:

1. Use the checked Android handoff and Magisk-root settle already proven in the
   V2451/V2458 family.
2. Stage `libacdbtap.so` under `/data/local/tmp/a90-acdbtap-v2476/lib/`.
3. Create the tap output directory `/data/local/tmp/a90-acdb-tap/`.
4. Stop init's `vendor.audio-hal` service.
5. Start `/vendor/bin/hw/android.hardware.audio.service` manually with
   `LD_PRELOAD=/data/local/tmp/a90-acdbtap-v2476/lib/libacdbtap.so`.
6. Verify `/proc/<pid>/maps` contains `libacdbtap` before playback.
7. Run the existing bounded Android framework `AudioTrack` speaker stimulus.
8. Pull `/data/local/tmp/a90-acdb-tap/` privately.
9. Kill the manual HAL process, restart init's `vendor.audio-hal`, clean all
   temporary paths, reboot to recovery, and checked-rollback to V2321.

This route is intentionally chosen before heavier Magisk rootdir/rc overlay work:
it is ephemeral, touches only `/data/local/tmp`, and directly tests whether the
HAL binary can run with the preload. If it fails, the failure is useful and
classifiable.

## Why not ordinary `service.sh` as the preload mechanism

Android init supports `setenv` inside service definitions, so an init `.rc`
service definition is the clean way to launch a service with `LD_PRELOAD`. Android
init also treats service names as unique, and duplicate service definitions are
ignored. Therefore an ordinary late-start Magisk `service.sh` cannot modify the
environment of the already-defined `vendor.audio-hal` service.

Magisk modules do provide boot scripts, system overlays, `sepolicy.rule`, and a
rootdir `overlay.d` mechanism, but those are heavier follow-on routes. They are
not needed until the ephemeral manual-reexec candidate proves whether SELinux,
linker policy, or service registration blocks the tap.

References used for the planner:

- Android init language README: `setenv` sets environment variables for launched
  service processes, and service names are unique.
  <https://android.googlesource.com/platform/system/core/+/master/init/README.md>
- Magisk module guide: `service.sh`, system overlay, `sepolicy.rule`, and
  rootdir `overlay.d` mechanisms.
  <https://github.com/topjohnwu/Magisk/blob/master/docs/guides.md>

## Abort classifiers for the next live unit

V2476 pins these first-class outcomes:

- `preload-not-in-maps`: HAL starts, but `libacdbtap` is absent from maps.
- `audio-hal-reexec-failed`: manual HAL launch does not create a usable process.
- `selinux-preload-open-denied`: AVC/linker denial blocks loading the tap.
- `selinux-capture-write-denied`: tap loads, but output writes are denied.
- `no-acdbtap-events`: tap loaded but no `acdb_ioctl` events were recorded.
- `acdbtap-events-no-4916`: `acdb_ioctl` events exist, but no target
  `out_len == 4916` payload was captured.

A SELinux denial is evidence, not a fix target for silent bypass. The next live
unit must capture AVC/logcat/dmesg evidence and stop. Any bounded permissive or
`magiskpolicy` assist must be a separate, explicit follow-on design with restore
and cleanup pinned.

## Acceptance for next live unit

The live unit accepts only:

- `acdbtap-events.jsonl` contains at least one call with `out_len == 4916`;
- the matching raw output bytes are pulled privately;
- public report includes only command id, input/output lengths, return code, and
  SHA-256;
- temporary Android/Magisk state is cleaned;
- checked rollback to V2321 ends with final native `selftest fail=0`.

## Boundaries

V2476 and the next live unit remain measurement-only.

Still forbidden in this path:

- native `/dev/msm_audio_cal` calibration ioctl;
- native mixer route write;
- native PCM playback;
- raw ACDB bytes in git;
- silent `setenforce 0` / silent policy relaxation;
- persistent Magisk dependency.

## Validation

Commands run:

```bash
PYTHONPATH=workspace/public/src/scripts/revalidation \
  python3 -m py_compile \
    workspace/public/src/scripts/revalidation/native_audio_acdbtap_live_planner_v2476.py \
    tests/test_native_audio_acdbtap_live_planner_v2476.py

PYTHONPATH=tests:workspace/public/src/scripts/revalidation \
  python3 -m unittest tests.test_native_audio_acdbtap_live_planner_v2476 -v

PYTHONPATH=workspace/public/src/scripts/revalidation \
  python3 workspace/public/src/scripts/revalidation/native_audio_acdbtap_live_planner_v2476.py \
    --stage-private-inputs
```

Results:

- focused V2476 tests: `4` passed;
- private staging/dry-run: OK;
- command-safety: OK;
- future live readiness from interposer/runner perspective: `true`;
- host cross-validation inventory: incomplete as described above.

## Next

The next meaningful unit is a bounded Android-good live run of this plan. It must
stay within the recoverable envelope, use the checked Android handoff and V2321
rollback, and classify the first failure rather than escalating to policy changes
or own-process `acdb_loader_init_v4` guessing.
