# V3441 S22+ Debug MID Rescue Live Pass

## Verdict

`PASS_RESCUE_BOOT_AND_MAGISK_ROLLBACK_MID`.

The exact V3441 boot-only rescue candidate was flashed once. The original Odin
endpoint disconnected, the operator observed the expected boot loop, then
physically entered Download mode. The checked helper restored the exact Magisk
boot-only AP and verified the complete Android/Magisk/MID baseline. The
one-shot exception is consumed and retired.

## Exact Artifacts

```text
helper              7cbfa449f8ce0c1f27f97455f0b796e15b4cea28c2f8d4139c11187d2ee4d5d7
candidate AP        25a8a5b5cfdeeebd47525c236d975561da8492bb08df5716cfa9da15e00ecfd6
candidate boot      a41fa0be63628f04b8a832ab9c54cb943ed2ab379a4a58da79ef17904dff2295
raw rescue /init    ea25969efca9308a28f18d8702465651205d7ee7503413ea40ab4396f01e6dda
Magisk rollback AP  d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56
stock fallback AP   2f6a8ac093587a0f03c423d8e21f65c6fe3a8d2ce9915297170cdaa2cac37c94
```

The stock fallback was not used.

## Timeline

```text
live_session_start     2026-07-11T01:03:59.838751Z
candidate_flash_start  2026-07-11T01:04:11.451431Z
candidate_flash_done   2026-07-11T01:04:13.017751Z
candidate_boot_ready   2026-07-11T01:04:13.285864Z
rollback_flash_start   2026-07-11T01:04:45.377319Z
rollback_flash_done    2026-07-11T01:04:46.780867Z
rollback_boot_ready    2026-07-11T01:05:22.217502Z
live_session_end       2026-07-11T01:05:22.234642Z
```

Candidate transfer took about 1.57 seconds. The attended manual Download
transition appeared about 32.09 seconds after candidate boot-ready. Magisk
rollback transfer took about 1.40 seconds, and verified Android return took
about 35.44 seconds. Total live session time was about 82.40 seconds.

## Final Baseline

```text
model             SM-S906N
device            g0q
bootloader        S906NKSS7FYG8
boot_completed    1
root              uid=0(root)
debug_level       18765 / 0x494d / MID
boot_sha256       2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
dtbo_sha256       97a4864fee4e61892d733962d1ec76f8d14b52bc19e6f47440bc27d9dfc4bd0c
recovery_sha256   93fac06ca79bf4b365b25a8d49902bc41aba112ea253c30880c90e314d7895d4
```

The standardized timeline contains exactly the eight required events. Private
run evidence is under
`workspace/private/runs/s22plus_v3441_debug_mid_rescue_20260711T010359Z/`.

## Interpretation

V3441 proves the rescue AP boots far enough to produce the expected loop, the
operator can recover physical Download mode from it, and the pinned Magisk AP
restores the full baseline. Because the rehearsal started and ended at MID, it
does not directly prove that the same command will demote a persisted HIGH
state. A HIGH experiment therefore remains a separate risk class and requires
its own exact setting method, observation plan, rollback gate, and fresh
one-shot authorization.
