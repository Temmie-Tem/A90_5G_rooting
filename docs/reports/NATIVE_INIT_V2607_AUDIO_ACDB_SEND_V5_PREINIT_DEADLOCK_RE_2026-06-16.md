# V2607 — ACDB `send_audio_cal_v5` preinit deadlock RE

Date: 2026-06-16

## Scope

Host-only static RE after V2606. No device handoff, flash, ACDB execution, native replay SET,
speaker write, or raw ACDB payload publication was performed.

The question was whether the V2604 stop inside `send_audio_cal_v5()` should be chased with more
imported-call live tracing. V2606 showed that global `pthread_mutex_*` / `__android_log_print`
interposition destabilizes the own-process helper before the V2604 frontier. V2607 therefore
re-examined `libacdbloader.so` directly.

Private input used:

- `workspace/private/inputs/audio/acdb-deps-v2506/vendor-lib/libacdbloader.so`

## Decision

The V2604 timeout is now best explained as a structural preinit re-entry hazard, not as a missing
ACDB GET argument:

- `acdb_loader_send_audio_cal_v5` begins by taking `loader_mutex`.
- The current V2572/V2603/V2605 route calls it from inside the `acdb_loader_send_common_custom_topology`
  interposer while `acdb_loader_init_v3` is still active.
- If init holds `loader_mutex` across the common-topology call, calling `send_audio_cal_v5` from that
  hook self-deadlocks before the first armed per-device `acdb_ioctl` GET.

This explains V2604 (`before_send_audio_cal_v5`, then timeout, zero `acdb_ioctl` rows) and makes
V2605's live imported-call tracer unnecessary. Do not keep iterating global pthread/log hooks.

## Evidence

`readelf` confirms the relevant symbols in the stock library:

```text
00018a94     4 OBJECT GLOBAL DEFAULT 22 loader_mutex
00009d31   876 FUNC   GLOBAL DEFAULT 14 acdb_loader_send_audio_cal_v5
UND pthread_mutex_lock@LIBC
UND pthread_mutex_unlock@LIBC
UND acdb_ioctl
```

Thumb disassembly of `acdb_loader_send_audio_cal_v5` shows mutex operations at function entry,
before the initialized/path logic and before the per-device GET command setup:

```text
00009d30 acdb_loader_send_audio_cal_v5:
  9d30: push.w {r4, r5, r6, r7, r8, r9, r10, r11, lr}
  9d48: ldr r0, [pc, #760]
  9d4a: add r0, pc
  9d4c: ldr r5, [r0]
  9d4e: mov r0, r5
  9d50: blx ...        ; first imported call, consistent with pthread_mutex_lock(loader_mutex)
  9d54: ldr r0, [pc, #752]
  9d56: add r0, pc
  9d58: ldrb r6, [r0]
  9d5a: str r0, [sp, #36]
  9d5c: mov r0, r5
  9d5e: blx ...        ; second imported call, consistent with pthread_mutex_unlock(loader_mutex)
  9d62: cmp r6, #0
  9d64: beq.w ...      ; initialized gate
```

Later in the same function, the first visible ACDB command setup occurs only after those mutex calls:

```text
  9e74: movs r0, #4
  9e76: movs r2, #4
  9e78: str r0, [sp]
  9e7a: movw r0, #4654
  9e82: movt r0, #1    ; command 0x1122e
  9e86: blx ...        ; imported acdb_ioctl path
```

So a stop before any armed `acdb_ioctl` rows is consistent with never passing the entry mutex region.

## Why V2605 Failed Differently

V2605 added global hooks for `pthread_mutex_lock`, `pthread_mutex_unlock`, and `__android_log_print`.
The live crash mapped to the new tracer resolver:

```text
Fatal signal 11 (SIGSEGV), fault addr 0xff30dff8
#00 pc 00003e38 /data/local/tmp/a90-acdb-ownget/liba90_acdb_combined_preload_v2538.so
00003e38 360 FUNC LOCAL DEFAULT 9 a90_resolve
```

That regression is coherent with unsafe dynamic-linker recursion: the pthread hook calls `dlsym()`
from inside `a90_resolve()`, and `dlsym()` itself can require pthread/loader synchronization before
the real mutex pointers are safely installed.

## Implications

The `send_audio_cal_v5` fallback remains useful only if it is not invoked from inside the preinit
`common_topology` hook while init may still hold `loader_mutex`.

Safe next designs are:

1. **Primary:** direct pure-read per-device GETs (`acdb_loader_store_get_audio_cal`,
   `acdb_loader_get_audio_cal_v2`, or `acdb_loader_adsp_get_audio_cal`) outside the preinit hook.
   This avoids the public send path's mutex and avoids the later real SET path.
2. **Conditional fallback:** restructure the own-process helper so `send_audio_cal_v5` is called only
   after `acdb_loader_init_v3` returns cleanly. That requires first proving a no-send preinit hook can
   skip topology / fake SET / patch init state without hitting the known init-tail SIGSEGV.
3. **Do not:** interpose global `pthread_mutex_*` or `__android_log_print` again in the combined
   preload; V2606 proved that observer is process-destabilizing before the frontier.

## Next Unit

Build V2608 as a host-only design/build unit for one of the two safe paths above. The recommended
first attempt is a no-send post-init discriminator:

- keep fake allocate and armed `acdb_ioctl` capture;
- in the common-topology hook, skip the real topology and patch initialized state, but do **not** call
  `send_audio_cal_v5`;
- return to `acdb_loader_init_v3` and observe whether init returns or crashes;
- only if init returns, call `send_audio_cal_v5` from the helper after init, outside the init-held
  mutex window.

If that discriminator still crashes before init returns, stop the send-v5 fallback and continue with
direct pure-read per-device getters.

## Validation

- Re-read `GOAL.md`, `AGENTS.md`, `CLAUDE.md`, and the ACDB operator spec.
- `readelf -Ws` on the private `libacdbloader.so` confirmed `loader_mutex`,
  `acdb_loader_send_audio_cal_v5`, `pthread_mutex_lock`, `pthread_mutex_unlock`, and `acdb_ioctl`.
- Thumb disassembly was generated with `llvm-objdump --triple=thumbv7a-linux-android` using the
  private toolchain compatibility library path.
- `git diff --check -- docs/reports/NATIVE_INIT_V2607_AUDIO_ACDB_SEND_V5_PREINIT_DEADLOCK_RE_2026-06-16.md`
