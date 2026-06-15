# NATIVE_INIT_V2459_AUDIO_ACDB_MSM_AUDIO_CAL_MECHANISM_ANALYSIS_2026-06-15

## Summary

V2459 is a host-only mechanism analysis of the V2458 Android-good ACDB
measurement. It does not touch the device.

The main result is a correction to the V2458 interpretation:

- V2458 did prove Android-good speaker playback reaches the stock ACDB edge.
- V2458 did not capture `/dev/msm_audio_cal` payload bytes.
- The stronger V2458 statement that the traced audio HAL process made no ioctl
  syscalls is not proven. The current ptrace helper only recognizes the
  AArch64 ioctl syscall number (`29`), while the relevant stock audio HAL path
  is 32-bit ARM and uses the compat ioctl syscall number (`54`).

Therefore the next useful unit is not native ACDB replay. It is V2460:
host-only compat-ARM ioctl observer support, followed by a bounded Android-good
rerun only after the observer can count and decode 32-bit ioctl entries.

## Scope And Safety

- Host-only source and artifact analysis.
- No flash, reboot, live Android handoff, native audio write, mixer write, PCM
  playback, or calibration ioctl.
- Private artifacts remain under `workspace/private/`.
- No raw ACDB payload bytes are committed.

## Inputs

- V2458 private run:
  `workspace/private/runs/audio/v2458-acdb-m1-hybrid-late-observer-20260615-182052`
- Stock vendor dump:
  `workspace/private/runs/audio/v2324-aud0-inventory/vendor_dump`
- Kernel source mirror:
  `tmp/wifi/v766-icnss-qcacld-patch-apply-build/source`
- Current Android-side ptrace helper source:
  `workspace/public/src/android/acdb_payload_capture/a90_acdb_ioctl_capture_diag_v2449.c`
- Prior V2458 report:
  `docs/reports/NATIVE_INIT_V2458_AUDIO_ACDB_M1_HYBRID_LIVE_RESULT_2026-06-15.md`

## V2458 Android-Good Facts

The V2458 Android-good playback window is still valid evidence:

- the run rolled back to V2321 with final `selftest fail=0`;
- Android framework `AudioTrack` playback completed with
  `A90_AUDIO_STIMULUS_FINISH rc=0`;
- logcat showed the speaker route ACDB edge:
  - `send_app_type_cfg_for_device PLAYBACK app_type 69941, acdb_dev_id 15`;
  - `ACDB -> send_audio_cal, acdb_id = 15, path = 0`;
  - `ACDB -> allocate_cal_block: mmap`;
  - `AUDIO_SET_AUDPROC_CAL cal_type[11] acdb_id[15] app_type[69941]`;
  - `AUDIO_SET_VOL_CAL cal type = 12`;
  - `AUDIO_SET_AFE_CAL cal_type[16] acdb_id[15]`.

The relevant traced process evidence remains:

- process `12816` had `/dev/msm_audio_cal` open as fd `13`;
- the same process had `/dev/ion` open as fd `16`;
- it also had many `/dmabuf:dmabuf*` fds;
- clone-follow attached the ACDB worker TID `15644`;
- p12816 helper terminal counters were `syscall_stop_count=5203`,
  `syscall_entry_count=2608`, `tracees=13`, and `ioctl_any_entry_count=0`;
- p12819 helper terminal counters included `ioctl_any_entry_count=492`, all
  unmatched against `/dev/msm_audio_cal`.

The p12816 counters prove ptrace was active on the target process. They do not
prove that no ioctl happened, because the syscall number decoder was ABI-narrow.

## Userspace Mechanism Facts

The stock audio stack used by this device is the 32-bit vendor HAL path:

- `vendor_dump/lib/hw/audio.primary.msmnile.so` is a 32-bit ARM Android shared
  object;
- `vendor_dump/lib/libacdbloader.so` is a 32-bit ARM Android shared object;
- `vendor_dump/lib64/hw/audio.primary.default.so` is a 64-bit default HAL, not
  the `msmnile` HAL observed in this path.

The 32-bit `libacdbloader.so` imports and/or references the expected ACDB
mechanism:

- imports `__open_2`, `ioctl`, `mmap`, `munmap`, `ion_open`,
  `ion_alloc_fd`, `ion_close`, and `acdb_ioctl`;
- contains `/dev/msm_audio_cal`;
- logs `ACDB -> allocate_cal_block: mmap`;
- logs `AUDIO_SET_AUDPROC_CAL`, `AUDIO_SET_VOL_CAL`, and `AUDIO_SET_AFE_CAL`.

The 32-bit `audio.primary.msmnile.so` references:

- `libacdbloader.so`;
- `acdb_loader_init_v4`;
- `acdb_loader_send_audio_cal_v4`;
- `platform_send_audio_calibration`;
- `send_app_type_cfg_for_device`;
- `opened mmap_shared_memory_fd` / `closing mmap_shared_memory_fd`.

This makes the likely Android-good transport model:

1. HAL selects the speaker device and app type.
2. `libacdbloader.so` opens `/dev/msm_audio_cal`.
3. `libacdbloader.so` allocates/mmaps ION or dmabuf-backed calibration memory.
4. It passes the shared-memory fd as `mem_handle` inside compat
   `/dev/msm_audio_cal` calibration ioctls.
5. The kernel imports the fd and maps/sends calibration blocks to Q6/ADSP.

## Kernel ABI Facts

The kernel UAPI defines the public calibration ioctls:

- `AUDIO_ALLOCATE_CALIBRATION` number `200`;
- `AUDIO_DEALLOCATE_CALIBRATION` number `201`;
- `AUDIO_PREPARE_CALIBRATION` number `202`;
- `AUDIO_SET_CALIBRATION` number `203`;
- `AUDIO_GET_CALIBRATION` number `204`;
- `AUDIO_POST_CALIBRATION` number `205`.

The relevant payload structs include `struct audio_cal_header` and
`struct audio_cal_data`; `audio_cal_data` carries both `cal_size` and
`mem_handle`.

The `/dev/msm_audio_cal` driver dispatches only those public calibration
commands through `audio_cal_shared_ioctl()` and then calls:

- `call_allocs()`;
- `call_deallocs()`;
- `call_pre_cals()`;
- `call_set_cals()`;
- `call_get_cals()`;
- `call_post_cals()`.

The file operations include `.unlocked_ioctl` and `.compat_ioctl`; they do not
include `.mmap`. This is important: the `allocate_cal_block: mmap` log is not a
direct mmap of `/dev/msm_audio_cal`. It is almost certainly userspace mmap of an
ION/dmabuf allocation used as calibration shared memory.

The calibration utils confirm the shared-memory contract:

- `create_cal_block()` stores `basic_cal->cal_data.mem_handle` in
  `ion_map_handle`;
- if `mem_handle > 0`, `cal_block_ion_alloc()` imports it through
  `msm_audio_ion_import()`;
- `cal_utils_alloc_cal()` rejects negative `mem_handle`, creates/remaps a
  block, then calls `map_memory()`;
- `cal_utils_set_cal()` rejects `mem_handle > 0` if a prior allocation block
  does not exist.

This explains the earlier native failure shape: writing only route controls and
App Type is not enough. Q6 later needs initialized AFE/ADM/ASM calibration
blocks, and those blocks are populated through the ACDB shared-memory ioctl
path.

## Crucial Observer ABI Finding

The current helper source has an AArch64-only ioctl syscall filter:

- it defines `__NR_ioctl` as `29`;
- it reads `regs.regs[8]` as the syscall number;
- it increments `ioctl_any_entry_count` only when that number equals `29`;
- it then reads fd/request/argp from `regs[0]`, `regs[1]`, and `regs[2]`.

The kernel source shows:

- AArch64 generic ioctl syscall number: `29`;
- 32-bit ARM ioctl syscall number: `54`.

The V2458 target process is the 32-bit Android audio service path. Therefore a
32-bit HAL ioctl entry can be invisible to the helper's `ioctl_any_entry_count`
even while ptrace syscall stops are being collected.

This invalidates the strong V2458 inference:

> "the traced process made no ioctl syscalls"

The safer corrected inference is:

> "the V2449/V2458 helper did not recognize any AArch64-numbered ioctl syscall
> from p12816; this does not rule out 32-bit compat ioctls from the stock
> 32-bit audio HAL."

## Native Replay Status

Native ACDB replay remains blocked.

Still missing:

- exact compat ioctl command order;
- decoded `audio_cal_header` / `audio_cal_data` fields;
- private payload hashes;
- `mem_handle` allocation and lifetime policy;
- calibration block cleanup/deallocation policy;
- proof that native can reproduce the loader's ION/dmabuf shared-memory
  contract safely.

Do not attempt native `AUDIO_ALLOCATE_CALIBRATION` or `AUDIO_SET_CALIBRATION`
until V2460 or a later unit pins those facts.

## Next Unit

V2460 should be host-only implementation/design first:

1. Extend the Android-side ptrace observer to recognize the 32-bit ARM ioctl
   syscall number (`54`) in addition to AArch64 `29`.
2. Verify the compat tracee register layout used by `PTRACE_GETREGSET
   NT_PRSTATUS` before assuming argument positions.
3. Preserve fd-owner mapping by TGID so `/dev/msm_audio_cal` matches process
   `12816` even when worker TIDs issue syscalls.
4. Capture only private/redacted metadata in public reports; raw payload bytes
   stay private.
5. Optionally add metadata-only observation for open/close/mmap/munmap around
   `/dev/ion`, dmabuf fds, and `/dev/msm_audio_cal`.

Only after that host-only observer fix is statically validated should another
bounded Android-good measurement run be considered.

## Validation

- Host-only analysis only.
- Re-read `GOAL.md`, `AGENTS.md`, and `CLAUDE.md`.
- Inspected current V2458 private artifacts, vendor binaries, kernel source,
  and helper source.
- No device action was performed.
