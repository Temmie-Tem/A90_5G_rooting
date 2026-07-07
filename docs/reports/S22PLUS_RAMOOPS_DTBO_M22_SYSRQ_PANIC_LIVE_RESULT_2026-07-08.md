# S22+ Ramoops DTBO + M22 Sysrq Panic Live Result (2026-07-08)

## Scope

Attended S22+ DTBO-enabled M22 sysrq-panic retained-console gate after explicit
operator approval. This report is redacted and metadata-only; raw logs,
host observations, and retained log captures remain under `workspace/private/runs/`.

## Pre-Live Gates

- Host-only M21A retirement and M22 readiness audit were committed first.
- `AGENTS.md` policy was promoted only after operator live approval.
- Active-policy readiness passed with `agents.complete=true`.
- Pre-live dry-run passed before any write: Android/root stability, current
  Magisk boot hash, current stock DTBO hash, and live
  `ramoops_region/status=disabled` were verified.

## Live Sequence

The active ack-gated helper was run once:

```text
s22plus_ramoops_dtbo_m22_sysrq_panic_live_gate.py --live --ack <active-token>
```

Observed flow:

```text
dtbo_candidate_odin_rc=0
patched_dtbo_hash_rc=0
patched_ramoops_status=okay
m22_candidate_odin_rc=0
m22_result=odin_seen
magisk_boot_rollback_odin_rc=0
post_m22_boot_rollback_pstore_files=[]
post_m22_boot_rollback_last_kmsg_bytes=2097136
post_m22_boot_rollback_pstore_marker_found=0
post_m22_boot_rollback_last_kmsg_marker_found=0
m22_retained_marker_found=0
stock_dtbo_rollback_odin_rc=0
stock_restore_dtbo_hash_rc=0
stock_restore_ramoops_status=disabled
live_rc=10
```

Interpretation: the DTBO enable path worked and the M22 boot candidate Odin
flash returned success. The device then entered a bootloop/Download path; the
operator manually entered Download mode, which the helper observed and used for
rollback. The expected M22 retained marker was not found in pstore or retained
last_kmsg.

`rc=10` is the helper's "rollback/restore completed but expected M22 marker was
not found" result, not a rollback failure.

## Rollback And Cleanup

The helper restored the pinned Magisk boot baseline through Download mode, waited
for Android/root to return, collected pstore and retained last_kmsg, rebooted to
Download again, restored stock DTBO, then waited for Android/root again.

Final read-only baseline preflight passed:

```text
boot_hash=2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
dtbo_hash=97a4864fee4e61892d733962d1ec76f8d14b52bc19e6f47440bc27d9dfc4bd0c
ramoops_status=disabled
root_available=true
boot_completed=true
result=pass
```

After the run, `AGENTS.md` was retired again: the active M22 live/rollback ack
strings and M22-specific marker/source/artifact strings were removed from the
active policy surface. The readiness auditor now reports inactive policy and the
default M22 helper execution fails closed at the AGENTS marker gate.

## Result

Live result: **NO-HIT for M22 retained-console marker**.

Clean-state result: **PASS**. The device is back on the Magisk boot baseline
with stock DTBO, Android/root available, and live ramoops disabled.

## Next Direction

Do not rerun the same M22 path under the consumed gate. The DTBO half remains
proven, but mainline ramoops/pstore did not retain the intentional M22 marker.
The strongest current retained-console evidence remains Samsung sec_debug MID
`/proc/last_kmsg` from the Android sysrq positive control; native-init fault
capture should either use that proven channel with a new candidate design or
move to a separate observability path with fresh gates.
