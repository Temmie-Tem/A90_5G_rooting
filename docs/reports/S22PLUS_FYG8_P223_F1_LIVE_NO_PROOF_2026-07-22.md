# S22+ FYG8 P2.23 F1 live no-proof close

Date: 2026-07-22 KST
Tier: F1, one boot-only candidate attempt plus mandatory rollback
Status: `NO_PROOF_F1_V2_CANDIDATE_ROLLED_BACK`
Final state: `CLOSED`

## Result

Process v2 executed the exact P2.21 candidate bound by the P2.22 ready
manifest and fresh P2.23 approval. Odin completed one candidate boot transfer.
After the bounded 120-second observation closed, the operator entered physical
Download mode and the runner completed one transfer of the exact preapproved
Magisk boot rollback.

The final Android boot completed, the boot animation stopped, Magisk root was
available, the expected boot image was restored, all three supporting
partition identities matched the target profile, and the Download endpoint was
absent. Recovery is not required.

## Observation

After rollback the runner captured `/proc/last_kmsg` twice to EOF. Both reads
were 2,097,136 bytes and byte-identical. The P2.19 same-ring decoder found:

- ENTRY count: 0
- USERSPACE count: 0
- UNSAT count: 0
- long-family count: 0
- UNSAT-family count: 0
- malformed, partial, foreign, or integrity findings: 0

The durable classification is `ZERO_AMBIGUOUS`. It is not accepted evidence of
the requested userspace callback and does not prove that the candidate Image
executed.

## Proven And Not Proven

Proven:

- the exact candidate and rollback APs passed their immutable Process v2 pins;
- each AP transferred exactly once through the measured boot-only path;
- the complete eight-event timeline and 19-record journal reopen cleanly;
- the rollback and final Android/root/supporting-partition health passed; and
- the two final retained reads are complete and byte-identical.

Not proven:

- candidate kernel selection or the post-exec hook;
- valid Samsung retained-ring magic at the hook;
- a retained index of at least 24 bytes;
- successful UNSAT, ENTRY, or USERSPACE store and persistence; or
- userspace `_start`, proc mount, child execution, module load, driver bind,
  UDC, or USB operation.

The zero result remains compatible with candidate non-selection, guard
rejection, invalid magic, `idx < 24`, store/readback/header-stability failure,
or later overwrite/loss. No one of those explanations is promoted over the
others by this run.

## Boundary And Next Step

The exact approval binding is consumed and cannot be reused. F1 is inactive.
No second candidate attempt is authorized by this run.

The next bounded unit is P2.24, H0 only: compare the P2.23 retained geometry,
kernel-side guard path, boot selection evidence, and Samsung ring lifecycle to
design a discriminator that can separate at least candidate non-selection,
guard rejection, and retained-store loss before another candidate is built.
