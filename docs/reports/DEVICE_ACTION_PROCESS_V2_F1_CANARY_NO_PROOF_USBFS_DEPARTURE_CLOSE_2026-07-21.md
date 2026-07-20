# Process v2 F1 Canary No-Proof and USBFS Departure Close

Date: 2026-07-21 KST

Verdict: `NO_PROOF_F1_V2_CANDIDATE_ROLLED_BACK`

The first Process v2 canary to begin a device session completed one exact
candidate boot-only transfer and one exact Magisk boot-only rollback. The
append-only journal closed at `CLOSED` with all eight canonical timeline
events. Final health proved normal FYG8 Android, stopped boot animation,
Magisk root, the exact known Magisk boot, stock supporting partitions, orange
verified-boot state, and no Odin endpoint.

The run did not prove native PID 1. Two EOF-complete `/proc/last_kmsg` reads
were byte-identical at 2,097,136 bytes. They contained one R4W1-B family prefix
but no complete exact record:

`[[S22R4W1B|id=36dc5462adedcf136176f2ddcfee08a8|phase=DIRECT_INIT_EXEC_AC`

Warm-reset output begins immediately afterward. The operator also reported
that the first physical Download entry was incomplete and caused one extra
boot before the successful Download entry and rollback. That intermediate boot
can overwrite retained-ring bytes, so the partial prefix is candidate-specific
corroboration but not load-bearing proof. It is not reinterpreted as PASS.

The candidate transfer completed before the Odin endpoint disappeared. The
shared observer then treated that expected disappearance during post-receipt
absence polling as endpoint identity failure. The remediation is deliberately
narrow:

- a non-empty live receipt may revalidate as the exact unchanged usbfs
  inventory or as removal of every measured live Odin node and nothing else;
- enumeration-time membership changes remain fatal;
- unrelated additions or removals remain fatal;
- same-path replacement and immutable identity changes remain fatal;
- ticket revalidation, ambiguity checks, and terminal absence remain strict;
  and
- no retry path advances the journal or reuses an approval.

Validation passed:

- USBFS/Odin focused tests: 82;
- USBFS/Odin plus Process v2 F1/D0/document tests: 151;
- `git diff --check` and Python compilation; and
- independent `gpt-5.6-sol` high-effort delta review: `GO`, no findings.

The review first rejected a broader draft because it retried unrelated USB
membership changes. That draft was removed before this close. The committed
shape permits only exact measured endpoint departure.

This report grants no D0 or F1 authority. The completed binding is spent. A
future candidate requires a new host-qualified artifact, new D0 preparation,
and fresh exact-binding approval.
