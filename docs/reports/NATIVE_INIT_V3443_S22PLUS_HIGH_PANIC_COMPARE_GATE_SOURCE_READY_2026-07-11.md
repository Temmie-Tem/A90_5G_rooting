# Native-init V3443 S22+ HIGH Panic Comparison Gate Source Ready

Date: 2026-07-11 KST

## Verdict

`HOST_SOURCE_READY_NO_LIVE_AUTHORIZATION`

V3443 is the smallest discriminator for whether accepted Samsung HIGH changes
retained panic visibility or the locked S-Boot RDX preamble gate. It reuses the
existing V3440 MID panic as a pinned control and therefore does not spend a
second MID panic.

## Pinned MID Control

Run: `workspace/private/runs/s22plus_v3440_rdx_20260711T000711Z/`

| Evidence | SHA256 / value |
|---|---|
| `result.json` | `62a6d12adb5ab33f39d9d44078de09f6180a39980b417dadf1fe9a598acd7dbe` |
| `post_recovery_last_kmsg.bin` | `a397d9688e740bc03bead8c4fd2fcc667910cfe98d2f92252a36b474e66a5b04` |
| `sboot_preamble_response.bin` | `3a4a3980e7835ebb77c927b99863e01847086171bdb81773e81e06f2192ab60c` |
| retained size / lines | `2097136` bytes / `20381` lines |
| preamble result | exact `NegativeAck`; probe and transfer false |

The verifier additionally requires the V3440 run marker, SysRq panic, `RDX is
locked`, and kernel-panic upload cause inside the retained log.

## Candidate Contract

1. Require exact MID Android/Magisk and partition identities.
2. Verify the exact V3442 setter and pinned V3440 control.
3. Dispatch HIGH once and require exact `18760` / `0x4948`.
4. Emit one run marker and trigger exactly one SysRq panic.
5. Observe exact `04e8:685d`; send only `PrEaMbLe\0` once.
6. Record positive, negative, malformed, or I/O result and always stop before
   any probe or transfer.
7. After physical RDX EXIT, collect HIGH `/proc/last_kmsg` and compare identical
   metrics against MID.
8. Dispatch MID once and require exact final MID baseline.

The source contains no probe-table parser and no binary payload for `PrObE` or
`DaTaXfEr`. Even a positive acknowledgement is classified
`POSITIVE_ACK_STOPPED_BEFORE_PROBE`.

## Comparison Output

The durable result records:

- preamble classification and response hash;
- retained byte and line deltas;
- count deltas for run marker, panic, RDX lock, upload cause, ramdump,
  minidump, sec_debug, and reset-exception strings;
- whether all core HIGH evidence is present;
- exact final MID and partition identities.

Raw retained logs and raw USB response remain private. Counts are evidence of
a delta, not by themselves proof that every changed line is a new HIGH-only
capability.

## Recovery Envelope

Normal recovery is zero-flash physical RDX EXIT followed by setter-driven MID
restore. If Android does not return, the separately acknowledged continuation
uses only the already-pinned V3441 MID rescue boot, then exact Magisk boot
rollback, with stock boot fallback for cleanup. No emergency path reissues
HIGH or panic.

## Static Validation

- helper SHA256:
  `9e5e561bc39019b7ec5ebe1a79c3a24fa89803bca568c7aec6d5308a1a35f6a9`
- focused tests: `9/9 PASS`
- policy: `DRAFT_INACTIVE`
- device actions during source preparation: `0`

The final safety pass additionally proves emergency modes verify all recovery
artifacts before action and that failed HIGH evidence collection cannot bypass
the mandatory MID restoration attempt.

Next: commit this source-ready checkpoint, independently review the exact
helper and inactive exception, then require a fresh explicit operator approval
before policy activation or connected dry-run.
