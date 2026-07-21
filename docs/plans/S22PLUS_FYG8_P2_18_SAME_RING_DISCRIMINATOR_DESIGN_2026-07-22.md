# S22+ FYG8 P2.18 Same-Ring Discriminator Design

- Date: 2026-07-22 KST
- Tier: H0, host-only design
- Status: `DESIGN_COMPLETE_IMPLEMENTED_IN_P219_REVIEW_PENDING`
- Live authority: none

P2.19 subsequently implemented this design host-only. The implementation is
recorded in
`docs/reports/S22PLUS_FYG8_P219_SAME_RING_IMPLEMENTATION_HOST_PASS_2026-07-22.md`;
its independent safety review and every candidate artifact step remain open.

## Question

The R4W1-E0 candidate and rollback transferred once, but the later stock
observer found no ENTRY or USERSPACE record. Exact FYG8 source modeling now
shows that E0's `idx >= payload_size` guard was unnecessarily strong: a
contiguous no-index-mutation record of `L` bytes is visible when valid magic is
present and `idx >= L`.

There is no independent candidate-selection witness in the current safety
envelope. The next carrier therefore cannot make every zero result unique. It
must add the most information possible without weakening the physical-layout,
magic, rollback, or Process v2 gates.

## Decision

Keep the proven 45-byte ENTRY/USERSPACE wire shape and add one shorter,
candidate-bound `UNSAT` record:

```text
ENTRY or USERSPACE (45 bytes)
  "\n[[S22P1U|" + state_tag.hex()[32 ASCII bytes] + "]]\n"

UNSAT (24 bytes)
  "S22UNS1|" [8 bytes] + unsat_tag [16 raw bytes]
```

All tags are the first 16 bytes of a SHA-256 digest with explicit state-domain
separation. This retains the existing 128-bit proof binding. The 8-byte UNSAT
prefix carries namespace, state, and format version; the size is fixed by the
decoder. A CRC and length field are unnecessary because the candidate performs
exact immediate readback, the observer matches the complete candidate-specific
24 bytes, and baseline/family cardinality is fail-closed.

This is the smallest selected format under the non-negotiable requirements of
a 128-bit candidate binding and a versioned state namespace. It is not a claim
that 24 bytes is an information-theoretic minimum.

## Candidate Binding

The record cannot contain the final Image or AP SHA-256 directly because doing
so would be self-referential. The future implementation must use this
transitive binding:

1. Build a canonical immutable candidate descriptor containing the target,
   base-source pins, config identity, `/init` identity, exact userspace request,
   target/layout constraints, record format version, and exact semantics. The
   descriptor cannot contain its own final patch or artifact digest.
2. Derive each 128-bit state tag from that descriptor with state-domain
   separation.
3. Verify that the compiled Image contains exactly the expected candidate
   records and no foreign family instance.
4. Pin the resulting Image, boot image, boot-only AP, run manifest, and static
   checker result by full SHA-256. Pin the instantiated source patch separately
   by full SHA-256 as part of the static checker closure.
5. Bind the fresh Process v2 approval to the exact AP, rollback AP, manifest,
   and runner version as usual.

The short tag identifies the compiled candidate contract. The full artifact
hashes in Process v2 identify the exact transferred bytes. Neither substitutes
for the other.

The executable H0 model uses an explicit model-only descriptor. Its generated
bytes are not candidate identities and must never be copied into a live
manifest.

## Candidate State Machine

The hook remains after successful `kernel_execve("/init")` and requires PID 1.
Before any physical write it must validate the exact target and physical
layout, then sample the Samsung header. It must not load `sec_log_buf.ko` or
change ring metadata.

| Post-exec state | Candidate action | Userspace callback |
|---|---|---|
| path `/init`, PID 1, valid magic, `idx >= 45` | write the 45-byte ENTRY immediately before the frozen cursor; memory barrier; exact readback; recheck magic, `idx`, and `boot_cnt` | arm only after all checks; exact request overwrites the same 45 bytes with USERSPACE |
| path `/init`, PID 1, valid magic, `24 <= idx < 45` | write the 24-byte UNSAT immediately before the frozen cursor; memory barrier; exact readback; recheck header | do not arm; this branch is diagnostic only |
| invalid magic or `idx < 24` | write nothing | do not arm |
| wrong path/PID or post-exec hook not reached | write nothing | unavailable |
| header drift, readback mismatch, or placement mismatch | do not arm and make no success claim | unavailable |

The candidate must never update `magic`, `idx`, `prev_idx`, or `boot_cnt`.
Header stability is checked immediately before and after the payload write.
The actual FYG8 payload is much larger than twice the longest record, so the
source-backed pre-cursor placement is contiguous in both prefix and rotated
snapshot branches.

UNSAT is deliberately not overwritten by a compact userspace record. Adding a
second compact state would enlarge the changed kernel and observer closure
without answering the immediate discriminator question.

## Observer Contract

The pre-candidate complete baseline must contain neither the long family
`[[S22P1U|` nor the short family `S22UNS1|`, including recognizable edge
fragments. The post-rollback observer classifies raw bytes before any text
conversion:

| Exact post-rollback bytes | Classification | What it proves | F1 acceptance |
|---|---|---|---|
| one candidate USERSPACE record only | `USERSPACE_CALLBACK_REACHED` | candidate post-exec hook and first PID1 proc request both reached | yes, subject to rollback and final health |
| one candidate ENTRY record only | `ENTRY_ONLY` | candidate reached the post-exec PID1 hook; userspace checkpoint not proven | no |
| one candidate UNSAT record only | `UNSAT_VALID_MAGIC_ENTRY_DID_NOT_FIT` | candidate reached the post-exec PID1 hook with valid magic and sampled `24 <= idx < 45` | no |
| no family or exact record | `ZERO_AMBIGUOUS` | no positive inference | no |
| duplicate, mixed, foreign, malformed, or edge-partial family | `AMBIGUOUS_INTEGRITY_FAILURE` | observer integrity is insufficient | no |

`ZERO_AMBIGUOUS` intentionally combines candidate nonselection, hook/path/PID
failure, invalid magic, valid magic with `idx < 24`, store/readback/header
failure, and later overwrite/loss/observer failure. A same-ring design cannot
separate those cases without a new independent channel or a forbidden write
before the magic guard.

The future observer must use a new allowlisted typed evidence kind and decoder.
It must not relax or reinterpret the immutable E0 decoder. The common runner
may dispatch the new kind, but `accepted=true` remains exclusive to the exact
USERSPACE state.

## Boundary Matrix

The executable contract covers these exact boundaries against the FYG8 stock
snapshot model:

| Index | Expected state |
|---:|---|
| `0`, `23` | `ZERO_AMBIGUOUS` |
| `24`, `44` | `UNSAT_VALID_MAGIC_ENTRY_DID_NOT_FIT` |
| `45` | `ENTRY_ONLY` |
| `payload_size - 1` | `ENTRY_ONLY`, prefix branch |
| `payload_size` | `ENTRY_ONLY`, full prefix branch |
| `payload_size + 1`, `UINT32_MAX` | `ENTRY_ONLY`, rotated-full branch |

Invalid magic at an otherwise sufficient index and candidate nonselection are
both required negative controls and remain `ZERO_AMBIGUOUS`.

Executable contract:

`workspace/public/src/scripts/revalidation/s22plus_fyg8_p218_same_ring_discriminator.py`

Focused tests:

`tests/test_s22plus_fyg8_p218_same_ring_discriminator.py`

## Next Changed Closure

P2.18 stops at design and executable modeling. P2.19 may implement and
statically validate only this changed closure host-only:

1. a new kernel patch implementing the corrected 45/24 thresholds and stable
   pre/post header checks;
2. candidate descriptor/tag generation plus Image/boot/AP static verification;
3. a new typed evidence schema and raw-byte classifier for ENTRY, USERSPACE,
   UNSAT, ZERO, and integrity failure;
4. focused runner dispatch for that new kind, without changing transport,
   Odin, rollback, recovery, journal, or final-health logic; and
5. proof that the implementation creates no candidate, manifest readiness, or
   F1 authority.

One independent safety review then covers the actual execution-critical diff,
not another abstract design ladder. Candidate build is forbidden until that
review closes. Candidate build, D0 preparation, and F1 approval remain later
and separate.

## Non-Goals

- no device contact;
- no kernel or `/init` build;
- no image generation or repacking;
- no manifest promotion or approval token;
- no modification of Process v2 transport or rollback machinery;
- no independent-witness claim; and
- no inference from an all-zero result.
