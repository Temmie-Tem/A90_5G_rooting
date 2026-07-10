# V3433 S22+ V3432 PID1 Keystone Live No-Proof Result

## Verdict

`NO_PROOF_PID1_VS_OBSERVER_UNRESOLVED_STOP`.

The exact V3432 boot-only candidate transferred successfully and departed the
original Odin endpoint. The operator observed Samsung's custom/non-official
image warning followed by reboot/bootloop behavior. Attended manual RDX/Download
returned within the bounded window, the exact Magisk boot-only rollback
completed, and the first rooted rollback boot passed every health and identity
gate. Two complete identical retained-ring reads contained no current-run
marker, malformed issue, or raw token.

This is not proof that `/init` did not run and not proof that the retained
transition failed. Under the V3431 contract, absence cannot distinguish kernel
or PID1 non-entry, a pre-marker candidate failure, observer load/probe failure,
marker write failure, or transition loss.

## Live Pins

- Pre-live commits: `6974f08f`, `ef752969`
- Helper SHA256:
  `9578ddbdef80d6607384cfdd4b8edffffcf2693bea81d9a9af4874e92650770d`
- Candidate AP SHA256:
  `264acafa1320e6faee1f6b3a569c6de1742ca6712e61003d114ec4a6d549bf34`
- Candidate boot SHA256:
  `67075d7f26486c3e4130dc6a935c5ed98ded8b817d9d5ec4beeddd05bef7f232`
- Run ID: `db4d3b66480bec29158c9ac9bfede880`
- Keystone contract:
  `686207c75d2530f90049de6b6945fbd3134019ca402f84cb97418c43804a4ca5`
- Transition contract:
  `426aa2bb50f6e73e153f5f5dc9cde59ddf37ab315f46860c1dc0bd0b3e810734`
- Magisk rollback AP:
  `d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56`
- Focused plus V3426-V3433 regression before live: 113 tests PASS
- V3426-V3433 regression after result recording: 113 tests PASS

Private evidence:
`workspace/private/runs/s22plus_v3433_pid1_keystone_20260710T205924Z/`.

## Timeline

```text
live_session_start       2026-07-10T20:59:50.013849Z
candidate_flash_start    2026-07-10T21:00:01.625558Z
candidate_flash_done     2026-07-10T21:00:03.137573Z  Odin rc=0
candidate_boot_ready     2026-07-10T21:00:03.402580Z  departure only
rollback_flash_start     2026-07-10T21:01:18.686598Z
rollback_flash_done      2026-07-10T21:01:20.096052Z  Odin rc=0
rollback_boot_ready      2026-07-10T21:02:04.369080Z
live_session_end         2026-07-10T21:02:05.220982Z
```

Manual transition elapsed: 75.272123 seconds. The canonical eight-event
timeline is complete.

## Preflight And Recovery

Connected read-only preflight passed before any write:

```text
target                    SM-S906N/g0q/S906NKSS7FYG8
boot SHA256               2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
live osrelease            5.10.226-android12-9-30958166-abS906NKSS7FYG8
sec_log_buf               Live, exact bind, both proc nodes
baseline ap_klog          2097136 bytes, current run absent
baseline last_kmsg        2097136 bytes, current run absent
```

After rollback, model/device/build, boot completion, orange vbstate, Magisk
root, and exact boot SHA all passed. An independent post-helper read reconfirmed
Android boot complete, root, and the same Magisk boot SHA.

## Retained Evidence

Both first-boot reads were exactly 2,097,136 bytes and byte-identical:

```text
ea9030d4f9d8b5f781079a98db8f77b818f95a1b2fb78b90a09b8e15eeb8239f
```

Classifier result:

```text
valid current-run markers     0
current-run malformed issues  0
raw current-run tokens        0
foreign markers               0
verdict                       NO_PROOF_PID1_VS_OBSERVER_UNRESOLVED_STOP
```

Evidence hashes:

- `result.json`:
  `200422088d81672a28c0141094baefed1fc3ee7d29e5c63ac36435301691809c`
- `timeline.json`:
  `a1391c7171dec12c26a8a6807501b29bedd0d3838befc35b5fc261d29f9e48b5`
- `first_boot_classification.json`:
  `988aa6fd791e3bf7ab9e4cd4484b06d07442c65b36103ee456428b935ba9586f`
- kernel-journal observer:
  `bd1dd9762443499fc508d6f510045d5b7bcf33d3906e4ba965997b3d3010ff9f`
- udev observer:
  `3d4629303f92e628b0b631f0d66a8f257b428807811a85c0189d63297ff2f340`

## Operator Observation And ABL Evidence

The operator reported the non-official image screen followed by reboot/bootloop.
Retained ABL material contains:

```text
[AuthSignatureOnBoot] Custom binary(boot) by verifystatus(2)
Device is unlocked, Skipping boot verification
```

Therefore the screen is consistent with the expected custom-boot warning on an
unlocked device. The available evidence does not show ABL refusing to boot the
candidate. It also does not show the candidate kernel reaching `/init`; ABL
continuation cannot be promoted to kernel/PID1 proof.

## Stop And Next Direction

The V3433 one-shot exception is consumed and rollback is complete. Do not repeat
V3432 or widen the candidate. The same direct-PID1 retained-marker approach has
again produced an absence result despite removing V3429's known pre-module gate.
Per the fails-twice and anti-expansion rules, the next unit must be host-only
postmortem/design. It should identify a witness available before userspace
observer loading or a stock-first-stage overlay path that preserves an already
active observation channel. No new direct-PID1 live flash is authorized.
