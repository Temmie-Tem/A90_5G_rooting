# NATIVE_INIT_V2519_AUDIO_ACDB_OWNPROCESS_LIVE_SHELL_CONTEXT_CONFIRMED_2026-06-16

## Scope

- Unit: V2519 live rerun of the V2490 own-process ACDB capture path after V2518 identity observability.
- Goal: determine whether the V2517 `/dev/msm_audio_cal` denial was due to actual helper execution context.
- Boundary: measurement-only; no HAL injection, no Magisk module install, no HAL restart, no playback, no native speaker write, and no `/dev/msm_audio_cal` SET ioctl.

## Inputs

- Runner: `workspace/public/src/scripts/revalidation/native_audio_acdb_ownprocess_get_live_handoff_v2490.py`
- Helper: `workspace/private/builds/audio/v2512-acdb-ownprocess-exec-linked-host-only/bin/a90_acdb_ownprocess_get_exec_linked_v2512`
- Helper SHA-256: `aab66000e12d6c976a96b3d73d603e6bb9c935dcd5dc801d3f25410f46887dc6`
- Private run: `workspace/private/runs/audio/v2490-acdb-ownprocess-get-20260616-043151`

## Result

- Decision: `v2490-init-v3-block-msm-audio-cal-open-denied-before-rollback-rollback-pass`
- Runner outcome: `ok=true`, `rolled_back=true`, `partial_success=false`, `target_4916_success=false`
- ACDB rows: `row_count=0`, `raw_file_count=0`, `target_4916_count=0`
- Helper event: `acdb_loader_init_v3` returned `-19`
- Classification: `init-v3-block-msm-audio-cal-open-denied`

## New Evidence

- Root precheck is valid for simple commands:
  - `adb shell su -c id` returned `uid=0(root)` with `context=u:r:magisk:s0`.
- The multi-line helper command path is not executing as root:
  - `ownget-exec-context.txt` reports `uid=2000(shell)` and `context=u:r:shell:s0`.
  - `ownget-run-context.txt` reports the same `uid=2000(shell)` and `context=u:r:shell:s0` immediately before helper execution.
- `/dev/msm_audio_cal` metadata is:
  - owner/group `system:audio`
  - label `u:object_r:audio_device:s0`
  - mode `crw-rw----`
- The vendor audio property file probe is denied from shell:
  - `/dev/__properties__/u:object_r:vendor_audio_prop:s0: Permission denied`
- Runtime logs still show:
  - `Access denied finding property "persist.vendor.audio.calfile0"`
  - ACDB file load succeeds
  - ACPH init succeeds
  - `Cannot open /dev/msm_audio_cal errno: 13`

## Interpretation

- The live blocker is no longer speculative SELinux or ACDB loader behavior. The helper is actually running under shell uid/domain due to the runner's multi-line `adb shell su -c <script>` command construction.
- The V2517 and V2519 `errno=13` result is expected from `u:r:shell:s0` with no effective capabilities and no membership in the `audio` group for `/dev/msm_audio_cal`.
- This is a runner invocation bug, not an ACDB data-load failure and not an own-process VNDK namespace failure.
- The next unit should fix the runner's `adb_su()` construction so multi-line scripts are quoted as one command evaluated by `su`, then dry-run and test the generated command strings before another live attempt.

## Rollback

- Android capture path completed cleanup, rebooted to recovery, and flashed back to V2321 through `native_init_flash.py`.
- Final serial verification:
  - `version`: `A90 Linux init 0.9.285 (v2321-usb-clean-identity-rodata)`
  - `selftest verbose`: `fail=0`

## Next Unit

- V2520 should be host-only:
  - change V2490 `adb_su()` to send one safely quoted remote command string, not raw multi-line argv after `su -c`;
  - add a focused test that multi-line `su` commands are wrapped/quoted and cannot fall through to the outer shell;
  - preserve the read-only identity probes and the `/dev/msm_audio_cal` SET-path blocklist.
- Only after V2520 static validation should the same V2490 live path be rerun.

