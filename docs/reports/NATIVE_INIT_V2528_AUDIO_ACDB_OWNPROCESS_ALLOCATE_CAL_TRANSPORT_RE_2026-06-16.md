# NATIVE_INIT_V2528_AUDIO_ACDB_OWNPROCESS_ALLOCATE_CAL_TRANSPORT_RE_2026-06-16

## Scope

Host-only RE follow-up for the V2524/V2527 own-process ACDB result.

This unit does **not** run a device action and does **not** issue native
`/dev/msm_audio_cal` calibration ioctls.  It explains why the current
own-process helper stops before any `acdb_ioctl` GET rows are emitted, and
selects the next bounded unit.

## Inputs

- V2527 live run: `workspace/private/runs/audio/v2490-acdb-ownprocess-get-20260616-050127`
- Helper source: `workspace/public/src/android/acdb_payload_capture/a90_acdb_ownprocess_get_exec_linked_v2512.c`
- Vendor libs, private/proprietary: `workspace/private/runs/audio/v2324-aud0-inventory/vendor_dump/lib/`
- Replay scaffold constants: `workspace/public/src/native-init/helpers/a90_acdb_replay_scaffold_v2474.c`

## Observed V2527 failure point

V2527 fixed the helper timeout by switching `_start` termination to `exit_group`.
The helper now exits promptly and reproducibly with:

```json
{"event":"error","stage":"acdb_loader_init_v3","code":-12,"pid":3929,"tid":3929}
```

The captured `ACDB-LOADER` log shows that the failure is **after** database and
ACPH/RTAC startup, not at namespace loading, file discovery, or ACPH init:

```text
ACDB -> ACDB_CMD_INITIALIZE_V2
ACDB -> ACPH INIT
[ACPH]->ACPH init success
ACDB -> RTAC INIT
ACDB -> MCS, FTS INIT
ACDB -> ADIE RTAC INIT
ACDB -> Error: Sending AUDIO_ALLOCATE_CALIBRATION, result = -1
ACDB -> allocate_cal_block failed!
ACDB -> Cannot allocate memory!
```

So the live classifier name from V2525 is the right frontier:

```text
init-v3-block-audio-allocate-calibration-failed
```

## Host RE findings

### 1. The allocation path is in `libacdbloader.so`, not `libaudcal.so`

`strings` on `libaudcal.so` has no matching `AUDIO_ALLOCATE` / `allocate_cal` /
`/dev/msm_audio_cal` strings.  The same scan on `libacdbloader.so` finds the
exact failure strings:

```text
ACDB -> Error: Sending AUDIO_ALLOCATE_CALIBRATION, result = %d
ACDB -> Cannot open /dev/msm_audio_cal errno: %d
ACDB -> Cannot allocate memory!
ACDB -> %s: Cannot allocate ION, cal type %d
/dev/msm_audio_cal
allocate_cal_block
ACDB -> allocate_cal_block failed!
```

`readelf -Ws libacdbloader.so` also shows the relevant imports:

```text
UND acdb_ioctl
UND __open_2
UND ion_open
UND ion_alloc_fd
UND ioctl
UND mmap
UND munmap
UND close
UND ion_close
```

This matches the V2474 replay scaffold model: libacdbloader allocates an ION /
dma-buf block, then talks to `/dev/msm_audio_cal` with audio calibration ioctls.

### 2. `init_v3` is not a pure database init

The current helper calls:

```c
init_ret = acdb_loader_init_v3(A90_ACDB_FILES_PATH, A90_DELTA_DIR, 0U);
if (init_ret != 0) {
    a90_write_error_event("acdb_loader_init_v3", init_ret, NULL);
    a90_exit(29);
}
```

So the helper never attempts the pure-read GET matrix after the `-12` return.

Disassembly of `acdb_loader_init_v3` confirms it is a thin wrapper around
`acdb_loader_init_v4` with `version=4`.  In `acdb_loader_init_v4`, after ACDB file
loading and ACPH/RTAC init, the function reaches the calibration allocation
sequence and returns through the observed error path if allocation fails.  The
same `libacdbloader.so` contains the public constants path used later by
`acdb_loader_send_common_custom_topology` and `send_audio_cal_v5`, including the
forbidden direct SET ioctl constant `0xC00461CB`.

Important boundary: the V2528 conclusion is **not** that ACDB GETs failed.  The
current helper never reaches them.  The only proven failure is the full-loader
calibration allocation side effect inside `init_v3`.

### 3. The live failure is not an obvious permission denial

V2527 ran through Magisk/root context and the log does not show an SELinux denial
on `/dev/msm_audio_cal` or ION at the failure point.  The only direct diagnostic
from libacdbloader is the failed `AUDIO_ALLOCATE_CALIBRATION` / `allocate_cal_block`
sequence.

This is consistent with the native ACDB replay boundary: native calibration SET /
ALLOC remains blocked live unless payload bytes, mem-handle policy, and cleanup
policy are pinned.  The own-process capture helper should not try to repair or
execute the allocation path.

## Decision

The next useful unit is **not** another unchanged V2490/V2512 live rerun.  It
would reproduce the same `init_v3` allocation failure and emit zero GET rows.

The next safe unit is a host-only helper variant design/build:

```text
V2529: soft-fail GET after init_v3 allocation failure
```

Behavior:

1. Call `acdb_loader_init_v3` exactly as before.
2. Record the `init_ret` event regardless of value.
3. If `init_ret == 0`, run the existing bounded GET matrix.
4. If `init_ret == -12`, still run the same bounded **pure-read** `acdb_ioctl`
   GET matrix, because the V2527 log proves ACDB DB load + ACPH/RTAC init already
   completed before the allocation failure.
5. Preserve all existing hard stops:
   - no `/dev/msm_audio_cal` open in helper source;
   - no `AUDIO_ALLOCATE_CALIBRATION` / `AUDIO_SET_CALIBRATION` symbols;
   - no `0xC00461CB`;
   - no `acdb_loader_send_common_custom_topology` path;
   - raw output private only.

This tests the narrow question that remains after V2528:

```text
Does the ACDB engine remain initialized enough after init_v3=-12 for direct
pure-read acdb_ioctl GETs to return topology/per-device bytes?
```

If yes, the topology capture can proceed without touching the allocation path.
If no, the next host-only RE step is to identify a true DB-only init entry or a
safe way to call `acdb_ioctl` after partial ACDB initialization, still without
native calibration SET/ALLOC.

## Validation

Host-only RE commands used:

```bash
strings -tx libacdbloader.so | rg -i 'AUDIO_ALLOCATE|allocate_cal|msm_audio_cal|Cannot allocate|ION'
readelf -Ws libacdbloader.so
readelf -rW libacdbloader.so
llvm-objdump -d --triple=thumbv7-linux-android --print-imm-hex libacdbloader.so
```

No device step was run in V2528.  No raw/proprietary bytes are committed.
