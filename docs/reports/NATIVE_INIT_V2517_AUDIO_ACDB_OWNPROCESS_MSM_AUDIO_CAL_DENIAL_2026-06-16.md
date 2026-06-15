# NATIVE_INIT_V2517_AUDIO_ACDB_OWNPROCESS_MSM_AUDIO_CAL_DENIAL_2026-06-16

## Scope

- Unit: V2517 live rerun of the own-process ACDB GET helper after V2514 logcat observability and V2516 Android-settle retry hardening.
- Goal: capture ACDB `out_len>0` records, especially the `4916` byte topology payload, using the own-process ARM32 helper only.
- Boundary: measurement-only; no HAL injection, no Magisk wrapper-exec iteration, no AudioTrack playback, no native speaker write, and no `/dev/msm_audio_cal` SET ioctl.

## Inputs

- Runner: `workspace/public/src/scripts/revalidation/native_audio_acdb_ownprocess_get_live_handoff_v2490.py`
- Helper: `workspace/private/builds/audio/v2512-acdb-ownprocess-exec-linked-host-only/bin/a90_acdb_ownprocess_get_exec_linked_v2512`
- Helper SHA-256: `aab66000e12d6c976a96b3d73d603e6bb9c935dcd5dc801d3f25410f46887dc6`
- Private run: `workspace/private/runs/audio/v2490-acdb-ownprocess-get-20260616-041955`
- Rollback target: `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`

## Result

- Decision: `v2490-init-v3-block-avc-denial-before-rollback-rollback-pass`
- Runner outcome: `ok=true`, `rolled_back=true`, `partial_success=false`, `target_4916_success=false`
- ACDB rows: `row_count=0`, `raw_file_count=0`, `target_4916_count=0`
- Helper event: `acdb_loader_init_v3` returned `-19`
- Helper rc: `29`
- Android-settle retry hardening was present but did not need to recover a transport flap; post-handoff settle and root recheck completed before helper staging.

## Evidence

- ACDB database loading succeeded far enough to load the vendor ACDB set and run `ACDB_CMD_INITIALIZE_V2`.
- ACPH initialization succeeded: the logs contain `Online service registered with ACPH` and `ACPH init success`.
- The blocker occurs after ACPH init, when ACDB tries to open `/dev/msm_audio_cal` and logs `Cannot open /dev/msm_audio_cal errno: 13`.
- The helper process ran in the Android shell SELinux domain and uid/euid `2000`, based on the audit record for the helper executable.
- The filtered logs also show denied access to the vendor audio property backing `persist.vendor.audio.calfile0`.
- No `acdb_ioctl` output records were emitted, so no raw ACDB payloads were generated or pulled.

## Interpretation

- This is not the V2513 `.acdb` path/load failure hypothesis: file loading progressed.
- This is not an ACPH init failure: ACPH registration completed.
- The remaining live blocker is process identity/domain for the own-process helper:
  - vendor audio property access is denied from `u:r:shell:s0`;
  - `/dev/msm_audio_cal` open from the same execution context returns `EACCES`.
- The runner currently invokes the helper through `adb shell su -c`, but the audit record still attributes the helper to shell uid/domain. The next unit should verify the actual execution identity immediately before `execve`, rather than assuming `su -c` produced the intended root/vendor-audio context.

## Rollback

- Android was rebooted to recovery and V2321 was flashed back through `native_init_flash.py`.
- Final serial verification after rollback:
  - `version`: `A90 Linux init 0.9.285 (v2321-usb-clean-identity-rodata)`
  - `selftest verbose`: `fail=0`

## Next Unit

- V2518 should be host-only runner hardening before another live attempt:
  - capture `id`, `id -Z`, `ps -AZ`, and `/proc/self/status` from the exact shell that will `execve` the helper;
  - capture labels/permissions for `/dev/msm_audio_cal` and the vendor audio property file;
  - classify the current result as `init-v3-block-msm-audio-cal-open-denied` instead of generic `init-v3-block-avc-denial`;
  - evaluate a bounded execution-domain fix explicitly, without silently disabling SELinux enforcing.

