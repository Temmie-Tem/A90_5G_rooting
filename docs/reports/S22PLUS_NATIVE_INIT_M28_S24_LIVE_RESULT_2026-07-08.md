# S22+ Native-Init M28 S24 Live Result (2026-07-08)

## Verdict

LIVE CONSUMED / S24 NOT CLEAN / FINAL BASELINE CLEAN.

The authorized M28 `S24` run flashed and rolled back successfully, but it is not
a clean S24 self-download proof because the operator reported bootloop
observation followed by manual Download-mode entry during the S24 observation
window. Treat the helper's `result=self-download` as manual-download
contaminated.

Do not run `F43` under the consumed M28 exception.

## Scope Run

Command executed:

```bash
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_m28_dep_complete_live_gate.py \
  --serial <S22_SERIAL_REDACTED> \
  --variant S24 \
  --live \
  --ack S22PLUS-M28-DEP-COMPLETE-LIVE-GATE
```

Run directory:

```text
workspace/private/runs/s22plus_m28_dep_complete_live_gate_20260708T143115Z/
```

No `F43` candidate was run.

## What Happened

Timeline:

```text
live_session_start          2026-07-08T14:31:27Z
dtbo_candidate_flash_start  2026-07-08T14:31:39Z
dtbo_candidate_flash_done   2026-07-08T14:31:39Z
dtbo_candidate_boot_ready   2026-07-08T14:32:25Z
S24_candidate_flash_start   2026-07-08T14:32:37Z
S24_candidate_flash_done    2026-07-08T14:32:38Z
S24_candidate_boot_ready    2026-07-08T14:33:15Z
S24_rollback_flash_start    2026-07-08T14:33:15Z
S24_rollback_flash_done     2026-07-08T14:33:16Z
S24_rollback_boot_ready     2026-07-08T14:34:01Z
dtbo_rollback_flash_start   2026-07-08T14:34:13Z
dtbo_rollback_flash_done    2026-07-08T14:34:14Z
dtbo_rollback_boot_ready    2026-07-08T14:34:59Z
live_session_end            2026-07-08T14:34:59Z
```

Host samples showed no Odin through `m28_S24_self_download_032`; Odin appeared
at sample `033`:

```text
m28_S24_self_download_033-odin devices=['/dev/bus/usb/002/036']
m28_S24_result=self-download
```

However the operator reported:

```text
부트 루프 관측됨 수동 다운로드 모드 진입
```

Therefore the sample-033 Odin endpoint is operator-corrected as manual Download
contamination, not clean S24 self-download proof.

## Retained Evidence

Post-rollback retained capture:

```text
post_m28_S24_rollback_pstore_files=[]
post_m28_S24_rollback_last_kmsg_rc=0
post_m28_S24_rollback_last_kmsg_bytes=2097136
post_m28_S24_rollback_last_kmsg_marker_found=0
post_m28_S24_rollback_retained_marker_found=0
m28_S24_capture_marker_found=0
```

The retained last_kmsg blob is present in the private run directory:

```text
workspace/private/runs/s22plus_m28_dep_complete_live_gate_20260708T143115Z/android_pstore/post_m28_S24_rollback_last_kmsg.bin
```

This report records the live result only. The next unit should be a host-only
postmortem of that retained log and the M28 module load sequence before any new
flash policy.

## Rollback And Final Baseline

The helper flashed the pinned Magisk boot rollback AP and then restored stock
DTBO:

```text
S24_magisk_boot_rollback_odin_rc=0
stock_dtbo_rollback_odin_rc=0
```

Independent final verification after helper exit:

```text
boot_completed=1
bootanim=stopped
vbstate=orange
bootloader=S906NKSS7FYG8
sys.boot.reason=reboot,download
Magisk root: uid=0(root) context=u:r:magisk:s0

boot        2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
dtbo        97a4864fee4e61892d733962d1ec76f8d14b52bc19e6f47440bc27d9dfc4bd0c
vendor_boot 096e433e049fb088cd956e083d5a1039b33cdf0ca907e713bba7feaaf1b080b7
```

## Decision

- M28 S24 is a no-proof/manual-download-contaminated result.
- The M28 one-shot exception is consumed and must not be reused.
- `F43` is not authorized because `S24` was not clean.
- Next work: host-only postmortem from retained last_kmsg and run logs, then
  design a fresh M29 only after a concrete failure mechanism is identified.
