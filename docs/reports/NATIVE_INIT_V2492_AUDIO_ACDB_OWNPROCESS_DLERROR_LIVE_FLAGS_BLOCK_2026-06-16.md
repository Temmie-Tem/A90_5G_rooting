# NATIVE_INIT V2492 — audio ACDB own-process dlerror live result

Date: 2026-06-16

## Decision

`v2492-ownprocess-dlerror-live-invalid-dlopen-flags`

The V2491 dlerror-instrumented helper was run through the existing checked
Android handoff runner. The run stayed inside the recoverable envelope and rolled
back to V2321 with final native selftest `fail=0`.

The first live loadability blocker is now concrete:

```json
{"event":"error","stage":"dlopen-libaudcal","code":-1,"detail":"dlopen failed: invalid flags to dlopen: 102"}
```

`102` is the linker-reported flag word for the helper's current
`RTLD_NOW | RTLD_GLOBAL` open mode (`0x102`). The next fix should remove
`RTLD_GLOBAL` and use the minimal `RTLD_NOW` mode first. This is a helper flag
compatibility issue, not an ACDB namespace or missing-library result yet.

## Live run

Private run directory:

- `workspace/private/runs/audio/v2490-acdb-ownprocess-get-20260616-013710`

The runner name/build tag still says V2490 because the live harness is reused;
the helper artifact was the V2491 rebuild:

- helper SHA256: `57797e74856724aa7cd8bf6add679e6e3069c8a7cd4a8d38f5f2f63e586a313e`

High-level result:

- Android flash through checked helper: pass
- Android boot/root settle: pass
- helper push/chmod: pass
- helper execution: completed and wrote error event
- artifact pull: pass
- `/data/local/tmp/a90-acdb-ownget` cleanup: pass
- rollback to V2321: pass
- final native version: `0.9.285 (v2321-usb-clean-identity-rodata)`
- final native selftest: `fail=0`

Captured private event set:

- `error_count=1`
- `row_count=0`
- `raw_file_count=0`
- `target_4916_count=0`
- stage: `dlopen-libaudcal`
- detail: `dlopen failed: invalid flags to dlopen: 102`

No ACDB GET calls ran, and no raw ACDB payload bytes were captured.

## Boundary

The run did not use the in-HAL injection line. It did not install a Magisk
module, restart the audio HAL, play AudioTrack, touch native speaker route state,
or issue `/dev/msm_audio_cal` calibration SET ioctls.

This result does count as meaningful evidence for the own-process path because it
turns V2490's generic `dlopen-libaudcal` failure into a specific bionic linker
flag rejection. It should not be treated as evidence that `/vendor/lib` deps are
unloadable from the own-process helper; that question is still behind the flag
fix.

## Validation

Post-run native checks:

```bash
python3 workspace/public/src/scripts/revalidation/a90ctl.py version
python3 workspace/public/src/scripts/revalidation/a90ctl.py selftest verbose
```

Result: V2321 resident, selftest `pass=11 warn=1 fail=0`.

## Next

V2493 should be host-only: change the helper's `dlopen()` mode from
`RTLD_NOW | RTLD_GLOBAL` to `RTLD_NOW`, update the build verifier/tests, rebuild,
and then rerun the same live handoff. If `RTLD_NOW` passes `libaudcal.so`, the
next blocker will finally classify actual vendor namespace/dependency behavior.
