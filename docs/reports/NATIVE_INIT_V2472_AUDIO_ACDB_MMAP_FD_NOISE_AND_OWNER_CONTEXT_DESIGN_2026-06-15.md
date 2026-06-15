# NATIVE_INIT_V2472_AUDIO_ACDB_MMAP_FD_NOISE_AND_OWNER_CONTEXT_DESIGN_2026-06-15

## Scope

Host-only cleanup and next-method design after V2471.

V2471 showed that the early dmabuf fd duplication path did run, but procfs fd
reopen fails with `ENXIO` even at `mmap_entry` time. It also exposed residual
noise: 64-bit anonymous mmap entries can carry fd value `0xffffffff`, which was
being logged as fd `4294967295`.

V2472 fixes the residual noise and records the next capture direction. No device
step ran.

## Change

`mmap_fd_arg()` now handles anonymous mmap fd values for both traced ABIs:

```c
static long mmap_fd_arg(const struct syscall_frame *frame) {
    if (!frame || !frame->abi) return -1;
    if (!strcmp(frame->abi, "aarch32")) return (int32_t)((uint32_t)frame->args[4]);
    if (!strcmp(frame->abi, "aarch64")) {
        unsigned long raw = frame->args[4];
        if (raw == 0xffffffffUL || raw == (unsigned long)-1L) return -1;
        return (long)raw;
    }
    return (long)frame->args[4];
}
```

The existing `fd < 0 || length == 0` filter then suppresses:

- AArch32 `mmap2(fd=-1)`;
- AArch64 `mmap(fd=0xffffffff)`;
- AArch64 `mmap(fd=-1)` if sign-extended.

The planner source-state contract and tests now assert the AArch64 anonymous
mmap filter exists.

## Validation

Host-only validation:

- AArch64 static helper build:
  - `aarch64-linux-gnu-gcc -O2 -static -s -Wall -Wextra`
  - output: `workspace/private/builds/audio/v2472-aarch64-mmap-fd-filter/a90_acdb_ioctl_capture_diag_v2449`
  - `file`: AArch64 static executable
- `python3 -m py_compile`
  - V2449 planner
  - focused ACDB observer tests
- Focused unittest:
  - `tests.test_native_audio_acdb_m1_diag_observer_planner_v2449`
  - result: `6` tests OK
- Materialized private module dry-run:
  - `future_live_ready=true`
  - `future_live_blockers=[]`
  - `command_safety_ok=true`
  - `contains_signed_mmap_fd_filter=true`
  - `contains_aarch64_anonymous_mmap_fd_filter=true`
  - `contains_early_dmabuf_fd_duplication=true`
  - `helper_ok=true`
  - `module_ok=true`

## Frontier after V2471

The dmabuf path is now characterized:

- target fd is visible as `/dmabuf:*` by `readlink()` at successful
  `mmap2(len=4916)` entry;
- procfs fd reopen fails with `ENXIO` at mmap-entry time;
- later SET_CAL procfs fd reopen also fails with `ENXIO`;
- cross-process owner-VA reads fail with `EIO`.

Therefore, another unchanged dmabuf-fd live rerun is low value.

## Next capture direction

Prefer a lower-risk source-buffer capture before in-process instrumentation:

1. extend the Android-good observer to trace regular-file source reads/mappings
   from ACDB data paths and audio calibration libraries;
2. capture private buffers for `read`/`pread64`/regular-file `mmap` events whose
   fd target is under `/vendor/etc/acdbdata` or otherwise known ACDB data;
3. correlate candidate buffers by size and timing against the later
   custom-topology SET_CAL edge (`cal_type=39`, `cal_size=4916`);
4. publish only private hashes/lengths and decoded metadata.

Only if source-buffer capture fails should the loop design a more invasive
Android-side owner-context instrumentation capsule. That would require a
separate host-only design and must remain a temporary Android measurement
capsule, not a native-init runtime dependency.

Native `/dev/msm_audio_cal` calibration ioctls remain blocked.

