# NATIVE_INIT V2567 — ACDB post-topology init crash localization

Date: 2026-06-16

## Scope

Host-only localization of the V2566 SIGSEGV. No device action, Android boot, native replay, speaker write, or calibration ioctl was performed.

Input evidence:

- `workspace/private/runs/audio/v2566-acdb-toposkip-export-fixed-20260616-114048/`
- V2565 fixed the preload export.
- V2566 confirmed the topology-skip interposer ran, then the helper still crashed before `acdb_loader_init_v3()` returned.

## Finding

The crash is not a dynamic-export problem anymore. It is the same `libacdbloader.so` post-topology init-tail crash seen before V2565, now reached after the short-circuit marker.

V2566 tombstone:

```text
Fatal signal 11 (SIGSEGV), code 1 (SEGV_MAPERR), fault addr 0x0
#00 pc 00008b30  /data/local/tmp/a90-acdb-ownget/libacdbloader.so
#01 pc 00003368  /data/local/tmp/a90-acdb-ownget/liba90_acdb_combined_preload_v2538.so (acdb_loader_send_common_custom_topology+184)
```

V2564 had the same top frame before the export fix:

```text
#00 pc 00008b30  /data/local/tmp/a90-acdb-ownget/libacdbloader.so
#01 pc 00009195  /data/local/tmp/a90-acdb-ownget/libacdbloader.so
```

So V2565/V2566 changed the caller frame from the real common-topology function to the preload short-circuit, but did not remove the downstream init-tail null dereference.

## Disassembly

Thumb decode of `libacdbloader.so` at the crash PC:

```text
0000808c acdb_loader_init_v4:
    8b20: cmp.w   r6, #4294967295
    8b24: ble     #...
    8b26: blx     #...
    8b2a: ldr     r0, [sp, #32]
    8b2c: ldr.w   r8, [r0, #8]
    8b30: ldr.w   r7, [r8]
    8b34: cmp     r7, r8
```

The fault address is `0x0`, so `r8 == NULL` at `ldr.w r7, [r8]`. This is a null list-head dereference in the `acdb_loader_init_v4()` tail, after the common-topology phase.

The init success flag is set only after this list walk:

```text
0000808c acdb_loader_init_v4:
    8b7e: movs    r0, #1
    8b80: movs    r6, #0
    8b82: strb    r0, [r5]
```

`acdb_loader_send_audio_cal_v5()` reads the same flag near its entry:

```text
00009d30 acdb_loader_send_audio_cal_v5:
    9d58: ldrb    r6, [r0]
    9d62: cmp     r6, #0
    9d64: beq.w   #...   ; not-initialized path
```

Therefore, simply calling `send_audio_cal_v5()` after the common-topology short-circuit is not enough unless the init-tail null dereference is avoided and the initialized state is handled deliberately.

## Interpretation

V2566 proved:

- `acdb_loader_send_common_custom_topology()` interposition is live-effective.
- The known topology payload is already pinned.
- The next blocker is the `acdb_loader_init_v4()` post-topology tail at `pc=0x8b30`.
- The current helper cannot reach its post-`init_v3` `send_audio_cal_v5()` call because `init_v3` never returns.

The correct next strategy is not another unchanged V2564/V2566 rerun.

## Next Unit

Design a crash-before-return capture path:

1. Keep the common-topology interposer active.
2. Do not wait for `acdb_loader_init_v3()` to return.
3. Either:
   - invoke the needed per-device GETs before returning to the crashing init tail, or
   - safely bypass/neutralize the post-topology list walk and initialized-state gate.
4. Exit immediately after banking the needed ordered ACDB records.

The next implementation must stay measurement-only:

- no native replay,
- no speaker write,
- no real `AUDIO_SET_CALIBRATION`,
- raw buffers private only,
- rollback to V2321 for any future live run.

## Decision

`v2567-post-topology-init-tail-null-deref-localized-host-only` is complete.

The V2566 live result should be treated as an informative partial success. It does not count as a dead retry, but the exact same topology-skip per-device live route must not be retried unchanged.
