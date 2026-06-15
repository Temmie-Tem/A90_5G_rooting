# NATIVE_INIT V2540 — ACDB armed-after-init topology capture path

Date: 2026-06-16
Scope: host implementation + one bounded live attempt for the own-process ACDB topology capture path.
Boundary: measurement-only; no speaker playback, no HAL injection, no real `AUDIO_SET_CALIBRATION`, raw captured bytes private only.

## Context

V2538 proved that a generic `acdb_ioctl` interposer can destabilize `acdb_loader_init_v3()` at the first init-time `acdb_ioctl` call. The operator handover changed the design: keep the combined preload, but make `acdb_ioctl` pass through silently until ACDB init completes. The helper then arms capture and calls `acdb_loader_send_common_custom_topology()`, whose size and 4916-byte GET happen before downstream allocate/memcpy/SET work.

## Implementation

Public source changes:

- `workspace/public/src/android/acdb_payload_capture/libacdbtap_v2475.c`
  - Added `A90_ACDBTAP_ARMED_CAPTURE` mode.
  - Added exported `a90_arm_capture()`.
  - Unarmed `acdb_ioctl` path only resolves/calls the real symbol; it performs no dump, hash, or file I/O.
  - Armed path dumps every `out_len > 0` buffer and adds `all_zero` metadata.
  - First `ret == 0`, non-all-zero `out_len == 4916` record triggers `exit_group(0)` after the raw file and event record are written.
- `workspace/public/src/android/acdb_payload_capture/a90_acdb_armed_topology_exec_linked_v2540.c`
  - New minimal ARM32 PIE helper: `init_v3()` → `a90_arm_capture()` → `acdb_loader_send_common_custom_topology()`.
  - Does not call direct GET matrices, does not open `/dev/msm_audio_cal`, and does not issue audio calibration ioctls.
- `workspace/public/src/scripts/revalidation/build_android_acdb_armed_combined_preload_v2540.py`
  - Builds the armed combined preload with `-DA90_ACDBTAP_ARMED_CAPTURE=1`.
- `workspace/public/src/scripts/revalidation/build_android_acdb_armed_topology_exec_linked_v2540.py`
  - Builds the minimal topology helper against the staged stock ACDB library closure.

## Host validation

Commands run:

```bash
python3 -m py_compile \
  workspace/public/src/scripts/revalidation/build_android_acdb_armed_combined_preload_v2540.py \
  workspace/public/src/scripts/revalidation/build_android_acdb_armed_topology_exec_linked_v2540.py \
  workspace/public/src/scripts/revalidation/native_audio_acdb_ownprocess_get_live_handoff_v2490.py
python3 workspace/public/src/scripts/revalidation/build_android_acdb_armed_combined_preload_v2540.py --build
python3 workspace/public/src/scripts/revalidation/build_android_acdb_armed_topology_exec_linked_v2540.py --build
```

Private build artifacts:

| Artifact | Path | SHA-256 | Result |
| --- | --- | --- | --- |
| armed combined preload | `workspace/private/builds/audio/v2540-acdb-armed-combined-preload-host-only/bin/liba90_acdb_armed_combined_preload_v2540.so` | `fbc4d92185a282fbcce534e843843d54a3dc58fa51e8e8c98cb7d90f5803ac69` | 32-bit ARM shared object; exports `acdb_ioctl`, `ioctl`, `a90_arm_capture` |
| topology helper | `workspace/private/builds/audio/v2540-acdb-armed-topology-host-only/bin/a90_acdb_armed_topology_exec_linked_v2540` | `b471fe9209d212097bd501699f8da3fe77ea8ca189b00bf368252d201cd6d1b0` | 32-bit ARM PIE; `_start`; DT_NEEDED closure present; weak `a90_arm_capture` unresolved for LD_PRELOAD resolution |

Dry-run with the V2490 live runner reported `live_ready=true`, no live blockers, V2321 rollback image present, and command safety clean.

## Live attempt

Command class:

```bash
python3 workspace/public/src/scripts/revalidation/native_audio_acdb_ownprocess_get_live_handoff_v2490.py \
  --use-combined-preload \
  --fake-audio-cal-allocate \
  --helper-path <V2540 topology helper> \
  --helper-sha256 b471fe9209d212097bd501699f8da3fe77ea8ca189b00bf368252d201cd6d1b0 \
  --combined-preload-so <V2540 armed combined preload> \
  --combined-preload-sha256 fbc4d92185a282fbcce534e843843d54a3dc58fa51e8e8c98cb7d90f5803ac69 \
  --helper-timeout 45 \
  --run-live
```

Private run directory:

`workspace/private/runs/audio/v2490-acdb-ownprocess-get-20260616-073017`

Result:

- Decision: `v2490-acdb-ownprocess-get-live-started-rollback-pass`.
- Capture did **not** reach Android helper staging or ACDB execution.
- Failure was before helper execution: `native_init_flash.py` timed out waiting for recovery ADB while flashing the Android boot handoff image.
- Error from `flash-android.stderr.txt`: `ADB state timeout; wanted=['recovery'] last=<none>` after `wait_recovery_adb` timed out at 180.844s.
- Runner recovered through the native bridge fallback and reflashed V2321.
- Final V2321 health: `A90 Linux init 0.9.285 (v2321-usb-clean-identity-rodata)`, `selftest fail=0`.

This run is a transport/handoff failure, not an ACDB negative result. No `acdbtap` payload evidence was produced.

## Classification

`v2540-armed-topology-ready-live-not-exercised`

The new capture path is implemented and build-validated. The only live attempt did not exercise it because Android handoff failed before staging. Per the flash gate, the device is back on V2321 with `selftest fail=0`; do not count this as an ACDB capture failure.

## Next step

Do not retry blindly. The next meaningful unit is a small Android-handoff preflight or runner fix focused on why `native_init_flash.py` timed out waiting for recovery ADB during the Android boot handoff. Once handoff is healthy again, rerun the same V2540 artifacts without rebuilding.
