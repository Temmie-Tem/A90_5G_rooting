# NATIVE_INIT V2610 — ACDB init_v3 meta-list crash RE

Date: 2026-06-16

## Scope

Host-only reverse-engineering follow-up to V2609. No device action, Android handoff,
native replay `SET`, speaker write, or raw payload publication was performed.

Inputs:

- V2609 live result:
  `workspace/private/runs/audio/v2609-acdb-postinit-send-v5-live-20260616-183824/`
- pulled `libacdbloader.so` and V2608 combined preload from the same private run
- private LLVM objdump:
  `workspace/private/inputs/toolchains/llvm-arm-toolchain-ship-10.0/bin/llvm-objdump`
  with `LD_LIBRARY_PATH=workspace/private/inputs/toolchains/compat-libs`

## Decision

- decision: `v2610-init-v3-arg3-is-meta-list-head-not-zero-scalar`
- V2609's SIGSEGV is explained by the helper passing `0` as the third
  `acdb_loader_init_v3()` argument.
- `init_v3` stores that argument at the `init_v4` argument struct offset `+8`.
  The `init_v4` tail later treats `arg0+8` as a circular-list head pointer, not as
  a harmless scalar.
- The immediate next route is not another V2608 rerun. Build a V2611 helper that
  passes a process-local empty circular meta-list head as `init_v3` arg3, then
  reuses the post-init arm/send path.

## Evidence

V2609 crashed before the helper could log `init_v3_return`:

```text
Fatal signal 11 (SIGSEGV), code 1 (SEGV_MAPERR), fault addr 0x0
#00 pc 00008b30  /data/local/tmp/a90-acdb-ownget/libacdbloader.so
#01 pc 00003904  /data/local/tmp/a90-acdb-ownget/liba90_acdb_combined_preload_v2538.so
```

The pulled `libacdbloader.so` maps `0x8b30` inside `acdb_loader_init_v4`:

```text
0000808c acdb_loader_init_v4:
    8b20: b6 f1 ff 3f    cmp.w   r6, #4294967295
    8b24: b5 dd          ble     ...
    8b26: 0d f0 34 e8    blx     ...
    8b2a: 08 98          ldr     r0, [sp, #32]
    8b2c: d0 f8 08 80    ldr.w   r8, [r0, #8]
    8b30: d8 f8 00 70    ldr.w   r7, [r8]
    8b34: 47 45          cmp     r7, r8
    8b36: 22 d0          beq     ...
```

The fault address was `0x0`, so `r8 == 0` at `ldr.w r7, [r8]`.

The `init_v3` wrapper constructs the `init_v4` argument struct on its stack and
stores its third argument (`r2`) into `arg0+8`:

```text
00009784 acdb_loader_init_v3:
    9786: 86 b0          sub     sp, #24
    9794: cd e9 03 23    strd    r2, r3, [sp, #12]  ; +8 = r2, +12 = 0
    9798: cd e9 01 10    strd    r1, r0, [sp, #4]   ; +0 = delta, +4 = acdb path
    979c: 01 a8          add     r0, sp, #4
    979e: 04 21          movs    r1, #4
    97a0: ...            call    acdb_loader_init_v4
```

Therefore, the V2608 helper call shape:

```c
acdb_loader_init_v3(A90_ACDB_FILES_PATH, A90_DELTA_DIR, 0U);
```

directly created the null pointer that `init_v4` dereferenced after the
common-topology hook returned.

## Re-interpretation

The earlier working assumption that `init_v3` arg3 was a scalar
`meta_info_type == 0` is incomplete for this post-common-topology path. In the
observed stock loader, the value at `init_v4_arg+8` is a list head:

- `r8 = *(arg0 + 8)`
- `r7 = *(r8)`
- `r7 == r8` is the empty-list condition
- non-empty entries are walked via `r7 = *(r7)` and use `*(r7 + 8)`

So the minimal no-entry form is a process-local circular head, e.g. a static
word whose value is its own address.

## Implication for the Operator Handover

The operator's "arm after init" structure is still the right direction, but
V2609 shows that `init_v3` will not return unless the meta-list argument is made
non-null. The fix is to satisfy the loader's empty-list invariant, not to keep
rerunning the same `arg3=0` helper or to return into the init tail unchanged.

## Recommended Next Unit

V2611 should be build-only:

1. add a new helper variant that initializes a static empty circular meta-list
   head and passes its address as `acdb_loader_init_v3(..., meta_head_ptr)`;
2. keep the V2608 combined-preload behavior:
   - fake `AUDIO_ALLOCATE_CALIBRATION`,
   - skip real common topology,
   - patch the initialized flag,
   - do not arm during init-time calls;
3. arm capture only after `init_v3` returns;
4. call `acdb_loader_send_audio_cal_v5(15, 1, 0x11135, 48000, 0, 48000, 1)`;
5. exit after banking real `ret==0` non-zero out-buffers, preserving the
   V2530 zero-buffer discriminator.

Future live execution stays measurement-only:

- no native replay `SET`,
- no speaker write,
- no real `AUDIO_SET_CALIBRATION`,
- raw buffers private only,
- checked rollback to V2321.

## Validation

Host commands used:

```bash
LD_LIBRARY_PATH=workspace/private/inputs/toolchains/compat-libs \
  workspace/private/inputs/toolchains/llvm-arm-toolchain-ship-10.0/bin/llvm-objdump \
  -d --triple=thumbv7a-linux-android --start-address=0x8a80 --stop-address=0x8b70 \
  workspace/private/runs/audio/v2609-acdb-postinit-send-v5-live-20260616-183824/ownget-device-artifacts/libacdbloader.so

LD_LIBRARY_PATH=workspace/private/inputs/toolchains/compat-libs \
  workspace/private/inputs/toolchains/llvm-arm-toolchain-ship-10.0/bin/llvm-objdump \
  -d --triple=thumbv7a-linux-android --start-address=0x9784 --stop-address=0x9840 \
  workspace/private/runs/audio/v2609-acdb-postinit-send-v5-live-20260616-183824/ownget-device-artifacts/libacdbloader.so

git diff --check
```
