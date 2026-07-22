# S22+ FYG8 P2.29 F1 duplicate-userspace no-proof close

Date: 2026-07-22 KST
Tier: F1, one boot-only candidate attempt plus mandatory rollback
Status: `NO_PROOF_F1_V2_CANDIDATE_ROLLED_BACK`
Final state: `CLOSED`

## Result

Process v2 executed the exact P2.26 candidate bound by the P2.27 evidence and
P2.28 connected preparation. Odin completed one candidate transfer. After the
bounded 120-second observation, the operator entered physical Download mode
and Odin completed one transfer of the exact preapproved Magisk boot rollback.

The original execute process ended after the durable `ROLLBACK_FLASHED`
transition and before final-health collection. The common `--recover` path
reopened that journal, did not attempt the candidate or rollback again, and
completed final Android health plus retained observation. The transaction
closed with the canonical eight-event timeline and 19 journal records.

Android boot completed, the boot animation stopped, Magisk root was available,
the expected boot image was restored, the Download endpoint was absent, and
the recovery, vendor_boot, and DTBO identities remained exact. Recovery is not
required.

## Baseline And Observation

Both the preparation baseline and the execute-time recheck read
`/proc/last_kmsg` completely. They were byte-identical and contained zero
ENTRY, USERSPACE, UNSAT, long-family, or short-family records.

After rollback, two complete reads were again byte-identical. The fixed P2.19
decoder found:

- ENTRY count: 0
- USERSPACE count: 2
- UNSAT count: 0
- long-family count: 2
- foreign, malformed, partial, or delimiter findings: 0

The two exact USERSPACE records occurred at different retained offsets,
348,291 bytes apart. Each is adjacent to a different warm-reset XBL generation
in the retained stream. The kernel implementation can replace ENTRY with
USERSPACE only once per boot because `userspace_proven` rejects a second write.

After the run closed, the operator confirmed that the first physical Download
entry attempt was missed and the still-installed candidate booted twice before
Download mode was reached. This accounts exactly for the two retained records:
one USERSPACE replacement per candidate boot. The duplicate is therefore an
operator-confirmed multi-boot recovery artifact, not an unexplained duplicate
write within one boot.

## Verdict Boundary

The immutable manifest required exactly one candidate USERSPACE record. Two
records therefore classify as `AMBIGUOUS_INTEGRITY_FAILURE`, and Process v2
correctly emitted:

```text
NO_PROOF_F1_V2_CANDIDATE_ROLLED_BACK
```

This verdict is not changed retroactively. The clean baseline, two exact
candidate-bound USERSPACE records, one-write-per-boot source guard, distinct
warm-reset contexts, and operator-confirmed two candidate boots establish that
the PID 1 userspace callback ran once in each boot. They are not an F1 PASS
under the predeclared exact-cardinality contract.

The run does not establish any E1 stage after the first procfs checkpoint. It
also does not prove USB or a host control path.

## Next Unit

The approval binding is consumed and F1 is inactive. No retry is authorized.

P2.30 is H0 only: model the operator-confirmed recovery multi-boot case and
choose the smallest reviewed discriminator that preserves a clean
pre-candidate baseline,
candidate-specific identity, no foreign or malformed family, and fail-closed
handling while allowing one or more identical USERSPACE records to mean
"callback reached on at least one candidate boot." The archived P2.29 verdict
must remain immutable. Any classifier or manifest-schema change requires the
independent review mandated by `AGENTS.md` before another candidate is built.
