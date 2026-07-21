# S22+ FYG8 R4W1-E0 F1 live no-proof result

Date: 2026-07-22 KST
Scope: one approved Process v2 F1 candidate and mandatory rollback
Status: candidate not proven; rollback and final health verified

## Verdict

`NO_PROOF_F1_V2_CANDIDATE_ROLLED_BACK`

The exact R4W1-E0 candidate AP and exact Magisk rollback AP each completed one
Odin transfer. The durable journal reached `CLOSED`, all eight canonical
timeline events are present in order, rollback is verified, and no recovery is
required. The consumed binding cannot authorize another attempt.

## Exact execution

- bundle SHA256:
  `f1c2715dc244c9a6822aed19a8bc1e28a40a118ba4a073bf66d8b7dd74ee191a`;
- candidate AP SHA256:
  `9b5ed2295ef9217746ba5e422acd54d13cfbc2daddcf35804ebaa08b9303ac08`;
- rollback AP SHA256:
  `d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56`;
- approval binding SHA256:
  `808b1990918020ec388fd282c9ac5bff162e9e760fceed1107990e1b1da105b8`;
- live result SHA256:
  `d9c9b060da6b9bbb1f781957f7d211302a199774efb2d9dcc6fd1fe8bd854968`.

The operator observed a completed boot without a boot loop during the bounded
candidate window. That sensory observation does not identify the booted kernel
or prove native PID1 execution.

## Retained observation

The two post-rollback `/proc/last_kmsg` reads were byte-identical:

- size: 2,097,136 bytes each;
- SHA256:
  `50fa24704f45f256a768fe5f4a4766963ca7b33af49317bdab739fcbf9379401`;
- read to EOF: true; stderr bytes: zero;
- ENTRY count: zero;
- USERSPACE count: zero;
- E0 family count: zero;
- classification: `PID1_USERSPACE_ABSENT`.

No complete or partial `[[S22P1...` record was present. Strict result reopening
revalidated the journal chain, transfer receipts, raw retained bytes, typed
classification, final target continuity, and canonical timeline.

## Recovery

Final Android boot completion, stopped boot animation, Magisk root, FYG8 kernel
release, expected supporting-partition identities, orange verified-boot state,
and absence of an Odin endpoint all passed. Candidate and rollback transfer
classifications are both `odin_transfer_completed`; final verification is true.

## Interpretation boundary

The result proves the Process v2 execution and recovery envelope. It does not
prove that the candidate kernel was selected, that `kernel_execve("/init")`
succeeded, or that the E0 runtime reached `_start`.

Static inspection still shows that ENTRY is written only after successful
`/init` exec on PID 1 and only when the retained magic is exact and the index is
at least one payload. The 2,097,136-byte baseline is consistent with a full
retained payload but is not a candidate-time header/index capture. If ENTRY was
written, the result also cannot distinguish later overwrite or retention loss.

Post-recovery read-only inspection found no debugfs or module parameter that
exposes the retained header/index directly. The remaining source-backed causes
are therefore limited to:

1. the transferred candidate was not the booted kernel/ramdisk path, or it did
   not reach successful `/init` exec;
2. the candidate-time retained magic/index gate refused ENTRY; or
3. ENTRY was written but was not visible in the next stock `/proc/last_kmsg`.

## Next bounded unit

Stop live retries. The next unit is H0 only: add one discriminating observation
for candidate boot-path selection versus retained-gate refusal, using the
existing runner and boot-only boundary. No new F1 binding is prepared until
that observation is statically validated.
