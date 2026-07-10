# V3433 S22+ V3432 PID1 Keystone Live Gate Armed

## Verdict

`READY FOR CONNECTED READ-ONLY PREFLIGHT; EXACT ONE-SHOT LIVE EXCEPTION ACTIVE`.

The V3433 helper wraps the exact V3432 boot-only artifact in the previously
proved attended Odin departure, manual RDX/Download, mandatory Magisk rollback,
first-boot health, and double-read collection envelope. The operator explicitly
approved live progression on 2026-07-11. No live invocation, reboot, Odin
transfer, partition write, or flash has occurred in this preparation unit.

## Pins

```text
helper_sha256         9578ddbdef80d6607384cfdd4b8edffffcf2693bea81d9a9af4874e92650770d
run_id                db4d3b66480bec29158c9ac9bfede880
manifest_sha256       f90f97476736cd4d7059652b4293d0b1a69b27c83925c07e499857357fe66a3b
marker_manifest       489d6fff3e96471db2f7beb2191b8d4136dec274bf2b9ca8847731313728fe4d
candidate_AP          264acafa1320e6faee1f6b3a569c6de1742ca6712e61003d114ec4a6d549bf34
candidate_boot        67075d7f26486c3e4130dc6a935c5ed98ded8b817d9d5ec4beeddd05bef7f232
candidate_boot_lz4    c698d5acf84ea10c5cf8ed8e95ed101a59483abf38b7977d16a2af0c95f67d5b
keystone_contract     686207c75d2530f90049de6b6945fbd3134019ca402f84cb97418c43804a4ca5
transition_contract   426aa2bb50f6e73e153f5f5dc9cde59ddf37ab315f46860c1dc0bd0b3e810734
Magisk_rollback_AP    d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56
stock_fallback_AP     2f6a8ac093587a0f03c423d8e21f65c6fe3a8d2ce9915297170cdaa2cac37c94
```

The candidate AP contains exactly `boot.img.lz4`. The helper pins the candidate
file by device/inode/size/mtime after hashing and rechecks it immediately before
transfer. Both rollback files are pinned the same way.

## New Preflight Gate

V3433 closes the V3430 preflight omission. Before any reboot or write it must
observe all of:

1. Exact `SM-S906N/g0q/S906NKSS7FYG8` Android identity and completed boot.
2. Orange verified-boot state and root.
3. Exact Magisk boot SHA256.
4. Exact live osrelease
   `5.10.226-android12-9-30958166-abS906NKSS7FYG8`.
5. Stock `sec_log_buf` module Live, exact driver bind, and both proc nodes.
6. Current run absent from fresh `/proc/ap_klog` and `/proc/last_kmsg` reads.
7. Full FYG8 stock evidence and both rollback APs present and exact.

Connected dry-run is read-only and cannot reboot or flash.

## Live And Classification

After preflight, the helper may perform one Android `adb reboot download`, one
candidate boot-only Odin transfer, at least 60 seconds quiet observation, and
attended manual RDX/Download within the hard 180-second transition deadline.
It must then restore the exact Magisk boot-only AP before reading retained
evidence.

The first rooted rollback boot must pass exact health. Two EOF-complete
`/proc/last_kmsg` reads must be byte-identical. Classification is:

```text
PASS     PASS_PID1_EXECUTION_AND_OBSERVER_LOAD
NO_PROOF NO_PROOF_PID1_VS_OBSERVER_UNRESOLVED_STOP
FAIL     FAIL_STOP for malformed, duplicate, wrong PID, or wrong identity
```

Non-EOF, invalid size, or double-read mismatch is `UNAVAILABLE_STOP` rather
than evidence classification.

## Validation

```text
V3433 focused tests                    14/14 PASS
candidate marker roundtrip             PASS
exact positive classifier              PASS
absence classifier                     NO_PROOF
duplicate classifier                   FAIL_STOP
non-EOF/double-read mismatch            UNAVAILABLE_STOP
bad live acknowledgement               stops before policy/device
canonical eight-event timeline          pinned
active AGENTS exception markers         PASS
```

The next action is the connected read-only dry-run. Actual live invocation may
proceed only if that gate passes unchanged.
