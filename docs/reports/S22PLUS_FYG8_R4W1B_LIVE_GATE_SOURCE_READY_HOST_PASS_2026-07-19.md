# S22+ FYG8 R4W1-B Live Gate Source-Ready Host PASS

Date: 2026-07-19 KST

Target: `SM-S906N/g0q/S906NKSS7FYG8`

Scope: host-only design, implementation, adversarial review, and offline
qualification of the reusable boot-only live core and the R4W1-B target helper.
No device was contacted or enumerated. No ADB, Download transition, Odin
transfer, flash, connected PASS, consumed state, or policy activation occurred.

## Result

The source checkpoint is ready for an exact-commit delta review:

`PASS_R4W1B_LIVE_GATE_SOURCE_READY_HOST_ONLY`

Policy remains inactive. This verdict authorizes no connected or live action.

## Architecture

The implementation has two layers:

- `s22plus_boot_only_live_core.py` owns only durable state, canonical timeline,
  private run directories, stable reads, bounded true-EOF ADB capture, and
  delimiter-anchored marker mechanics;
- `s22plus_fyg8_r4w1b_live_gate.py` owns the target, every artifact and source
  pin, observer meaning, transition, verdict, policy sentinel, and
  acknowledgement.

The target helper exposes exactly four modes: inert offline qualification,
connected read-only rehearsal, one-shot live execution, and consumed-state-only
rollback from Download. The candidate and both rollback APs are required to
contain exactly one regular `boot.img.lz4` member.

## Adversarial Review

Claude Opus 4.8 high-effort review in conversation
`c7d10391-7bb6-4274-9e49-076007945b03` returned
`GO_WITH_MUST_FIX` for host source-readiness and explicitly authorized no device
contact. It found no HIGH issue and two MEDIUM robustness gaps:

1. emergency rollback depended on the live ACTIVE sentinel and current helper
   hash after the candidate had already been consumed;
2. connected read-only mode read `/proc/last_kmsg` once while the load-bearing
   live path requires two byte-identical EOF-complete reads.

Both are closed. Recovery now requires the exact recovery acknowledgement, a
valid consumed record with well-formed recorded helper SHA, exact boot-only
rollback artifacts, one Odin endpoint, and temporal normal-Download
confirmation, but not an ACTIVE sentinel or equality to later helper source.
This relaxation applies only to restoration after consumption and cannot
authorize another candidate run. Connected mode now reads `/proc/ap_klog` once
and `/proc/last_kmsg` twice, rejects nonidentical reads, and reopens the complete
receipt contract from its exclusive PASS record.

The review's LOW observations are also closed or pinned explicitly:

- historical `[[S22R4W1|` is a deliberately disjoint namespace that is counted
  but neither contaminates nor satisfies R4W1-B;
- observer capture/EOF/identity failures use
  `FAIL_R4W1B_OBSERVER_CAPTURE`, distinct from marker integrity;
- the fresh static checker is documented as a deterministic byte-identity and
  empty-stderr hard gate;
- full-tail exact markers, exact-plus-tail-partial, and delimiter mismatch now
  have direct regression tests.

## Exact Source Pins

```text
target helper       734693c456d482e6a09360129ba74e9123017b5c42829518a23870d07465a95d
target helper test  87de80150d1962c5804471a8037657144a4c394cd8cba5c596947c0723be42c1
reusable core       9bcade2532e77d538112836ebe9903bab832c1f2250151d3635260b6fd013725
core test           b55db8579115ec437e7fe63b6a3b6ecef0d8cbcac54110599e85f310f3b2fd9d
inactive draft      a757eb46d5adb9e77e42fc6290656f9b56e1d6c33ec5e0cba6930bcf8fb557e2
```

## Artifact Gate

The complete offline helper gate reopened all pins, reran the independent
static checker, and returned `PASS_R4W1B_LIVE_GATE_OFFLINE_CHECK`:

```text
candidate raw boot  100663296  69690e6832bab2a422979054b51ad279222c14cbc369517433b55a785ed3d44d
candidate LZ4        27055052  be2265ae72c584553945a82cdabc1ce36cc59cf6ee065c9675b97df9fc209c9a
candidate AP         27064361  ae26340d69f7208ae3a8c0d135e3f65317b4d16b539d4e19c1613b7f15f0f2c5
static result           30004  969b4a5d94660fb07abba95fe2386cb9327c2a0e97167e153a895619c4385d47
full FYG8 ZIP       9680091538  f831e5fb8abe1c7a9d8c38fe9c033a3fce7e77651776383641c385c2bb85a2c8
Magisk rollback AP    23367721  d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56
stock cleanup AP     100669481  2f6a8ac093587a0f03c423d8e21f65c6fe3a8d2ce9915297170cdaa2cac37c94
Odin4                  3746744  6754aa54f2abe6e99ece32414cd34c8b23b28dbddde537a33203036813637c3b
```

Fresh checker output was exactly 30,004 bytes with the pinned SHA, schema
`s22plus_fyg8_r4w1b_candidate_static_checker_v1`, verdict
`PASS_R4W1B_CANDIDATE_THREE_REPRO_STATIC_CONTRACT`, and no blockers.

## Validation

```text
focused core + helper tests              38 passed
pipeline + core + helper tests           72 passed
py_compile                               PASS
complete offline artifact gate           PASS
connected policy                         inactive
live policy                              inactive
connected PASS                           absent
candidate consumed state                 absent
device contact/write/flash               false/false/false
```

## Next Gate

Commit this exact host-only checkpoint, run one bounded independent delta review
against the commit and current hashes, and close any findings. Only then may a
separate commit bind the connected-read-only ACTIVE clause. Connected execution
still requires the exact fresh acknowledgement
`S22PLUS-FYG8-R4W1B-CONNECTED-READ-ONLY-DRY-RUN`. Live policy activation remains
a later gate bound to the resulting exact connected PASS.
