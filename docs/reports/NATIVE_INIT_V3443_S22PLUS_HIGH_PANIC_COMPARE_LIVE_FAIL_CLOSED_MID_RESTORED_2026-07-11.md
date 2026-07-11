# Native-init V3443 HIGH Panic Comparison Live Fail-closed

Date: 2026-07-11 KST

## Verdict

`FAIL_CLOSED_NO_PANIC_ARGV_QUOTING_BUG_HIGH_DISPATCH_CONSUMED_MID_RESTORED`

V3443 did not produce a HIGH-versus-MID panic comparison. HIGH was applied
successfully, but the panic command was split at the ADB shell boundary and the
privileged writes did not execute. The one-shot policy is consumed and retired.

## Proven Sequence

1. Connected dry-run passed exact MID `18765` / `0x494d`, Android/Magisk root,
   known boot, stock DTBO/recovery, pinned MID control, setter, recovery
   artifacts, and PyUSB.
2. The exact setter dispatched HIGH once.
3. Android returned at exact HIGH `18760` / `0x4948`; boot, DTBO, and recovery
   hashes remained exact.
4. The helper marked `panic_attempted=true`, but ADB remained connected for the
   full bounded confirmation window and it stopped before USB observation.
5. An authorized mandatory cleanup used the same verified setter to dispatch
   MID exactly once.
6. Android returned at MID `18765` / `0x494d` with Magisk root and exact
   boot/DTBO/recovery hashes. Flash count was zero.

## Root Cause

The helper invoked ADB as separate arguments equivalent to:

```text
adb shell su -c "set -eu; marker-write; sysrq-enable; sysrq-c"
```

ADB did not preserve the final argument as one remote shell word. `su -c`
received only the first command token; subsequent commands were parsed by the
unprivileged Android shell. A harmless read-only reproduction was decisive:

```text
split argv:             first id uid=0, second id uid=2000
quoted single shell arg: first id uid=0, second id uid=0
```

The corrected construction must send one remote shell string with the complete
compound command protected by `shlex.quote`, matching the proven V3440 style.
A pre-panic harmless two-command root quotation control must also pass before
any future SysRq arm.

## Retained Negative Evidence

Post-cleanup `/proc/last_kmsg` was captured privately:

```text
bytes                         2097136
lines                         18592
sha256                        1ad451372ad5bf72fab681656249f07b4451df3255bd3a642759c4cbf5297df1
current-run marker            0
SysRq panic                   0
RDX is locked                 0
kernel-panic upload cause     0
```

Therefore this was not an unobserved panic. No RDX endpoint appeared, no
`PrEaMbLe`, `PrObE`, `DaTaXfEr`, qdl, dump transfer, flash, or partition write
occurred.

## Durable State

Private run:
`workspace/private/runs/s22plus_v3443_high_panic_20260711T014605Z/`

The result records the root cause and exact final baseline. `timeline.json` has
the single `events:[{name,timestamp_utc}]` schema with all eight mandatory phase
names. The original active helper SHA was
`9e5e561bc39019b7ec5ebe1a79c3a24fa89803bca568c7aec6d5308a1a35f6a9`.

## Decision

Retire V3443. Do not reuse its approval. A corrected V3443R source may be
prepared host-only, but another HIGH dispatch or panic requires a new exact
helper SHA, inactive policy draft, focused quotation tests, independent review,
and fresh explicit operator approval.
