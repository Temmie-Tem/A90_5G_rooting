# S22+ FYG8 R4W1-E E1 F1 no-proof close

Date: 2026-07-22 KST
Tier: one approved F1 candidate attempt and mandatory exact rollback
Status: transaction closed, candidate not proven, rollback verified

## Verdict

`NO_PROOF_F1_V2_CANDIDATE_ROLLED_BACK`

Process v2 transferred the exact R4W1-E E1 boot-only candidate once and the
exact Magisk boot-only rollback once. Both Odin invocations completed with
return code zero. The rollback restored healthy FYG8 Android and root, but the
post-rollback retained observer contained no R4W1-E carrier. This is a safe
no-proof result, not an E1 PASS and not proof that E1 failed.

The consumed approval binding cannot be reused. No S22+ F1 run is active.

## Bound execution

- manifest: `s22plus-fyg8-r4w1e-e1-process-v2-ready-1`;
- bundle SHA256:
  `2ec7b037f09a9cb2a6c21880060a0ccf3751bffe97cc4d55a312a7a28888ef00`;
- candidate AP SHA256:
  `ff4e1766b82306005bfa3cbb6280347ad6133bb60801c9d6236d7eaf044bd421`;
- exact Magisk rollback AP SHA256:
  `d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56`.

The candidate and rollback each have one attempt and one
`odin_transfer_completed` receipt. The journal contains 19 records, reaches
`CLOSED`, reports `recovery_required=false`, and contains all canonical events
in order:

`live_session_start`, `candidate_flash_start`, `candidate_flash_done`,
`candidate_boot_ready`, `rollback_flash_start`, `rollback_flash_done`,
`rollback_boot_ready`, `live_session_end`.

## Observation

Two independent `/proc/last_kmsg` reads after rollback were byte-identical:

- 2,097,136 bytes each, read to EOF;
- empty stderr;
- E1 entry-family count: zero;
- exact E1 entry count: zero;
- partial and unterminated E1 family count: zero;
- binary `S22C` checkpoint-slot magic count: zero;
- classification: `CHECKPOINT_ABSENT`;
- accepted: false.

The pre-candidate and post-rollback observer hashes differ, so the final read
is not merely the unchanged preflight file. It contains the prior Android
shutdown log expected from this retained channel, but no E1 carrier bytes.

## Final health

Final verification passed all manifest-bound predicates:

- Android boot completed and boot animation stopped;
- Magisk root verified;
- boot restored to the exact expected rollback identity;
- vendor_boot, DTBO, and recovery retained their expected identities;
- verified-boot state remained orange; and
- no Odin endpoint remained.

No non-boot partition was transferred. The device ended in the known healthy
state.

## What this proves

- Process v2 handled candidate transfer, bounded observation, attended
  recovery, mandatory rollback, and final-health closure without repeating a
  transfer.
- The exact candidate AP was accepted by Odin and transferred.
- The retained observer was complete, stable across two reads, and able to
  classify the expected carrier as absent.
- The rollback and recovery envelope worked.

## What this does not prove

- It does not prove or disprove that the R4W1-E kernel reached the successful
  `kernel_execve("/init")` edge.
- It does not prove userspace `_start`, mounts, child execution, module load,
  quiet park, terminal success, or terminal failure.
- It does not identify which carrier guard returned or prove that carrier bytes
  were never written; complete later loss remains possible.
- Odin success is not candidate execution proof.

## Host-only fault boundary

R4W1-D previously proved the same post-`kernel_execve("/init")` call site with
a 45-byte write immediately behind the Samsung log cursor. R4W1-E adds two
material differences before E1 userspace evidence can exist:

1. a runtime OF/resource target gate checks machine compatibility, log-node
   availability and resource geometry, strategy, partial-memory mode, and the
   reserved-memory phandle; and
2. the retained shape grows to 173 bytes, placing the entry farther behind the
   cursor and adding two slots.

The exact FYG8 source describes the expected `qcom,waipio-mtp` compatible,
enabled `samsung,kernel_log_buf`, strategy 3, partial-memory mode, physical
range, and containing direct-mapped `samsung,carve-out`. That source agreement
does not prove the merged live DT or each runtime OF translation result.

The remaining explanations are therefore bounded to:

- an R4W1-E target/header guard refused carrier initialization;
- the full carrier was written but did not survive or was not exposed through
  the next `/proc/last_kmsg`; or
- the candidate did not reach the already proven post-exec call site.

No retained bytes distinguish those branches. The E1 runtime itself must not
be modified or retried until the carrier boundary is made observable or the
new gates are reduced to predicates already proven by R4W1-D.

## Next unit

P2.12 is H0 only. Compare the exact linked R4W1-E carrier path with R4W1-D,
check the stock DTBO/merged-DT semantics of each added OF/resource predicate,
and design one compact diagnostic that distinguishes initialization refusal
from retention loss. Do not rebuild, prepare D0, request approval, or run a
second candidate in this unit.
