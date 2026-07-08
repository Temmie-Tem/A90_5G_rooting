# S22+ M24 PMSG-Steps Live Result - 2026-07-08

## Verdict

M24 was live-flashed once under the SHA-pinned boot-only exception, then rolled
back successfully to the known Magisk boot baseline. The candidate did not
expose the expected M24 ACM/ADB control path. The operator observed a bootloop
and manually entered Download mode; the helper detected Odin, restored the
pinned Magisk boot AP, and collected retained surfaces.

The pmsg-step hypothesis did not yield a retained progress marker in this run:
pstore was empty, `/proc/last_kmsg` contained no M24 marker, and the extracted
`A90_STEP:M24:` list was empty.

## Artifacts

- Run directory:
  `workspace/private/runs/s22plus_m24_pmsg_steps_live_gate_20260708T112123Z`
- Candidate AP SHA256:
  `e09538024abe89585486d54856a5c86bef666da456f314084d4d4d8bb6553fe8`
- Candidate boot SHA256:
  `0cccc003687227c4265081fa59d440f4be3e7f40fbb64aca2a3930ca7d5ca3df`
- Candidate `/init` SHA256:
  `4086d18f453980893fa1b8022f93991775b0ee28a6088f1216de82b74cbaf341`
- Rollback AP SHA256:
  `d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56`

## Live Evidence

- `m24_candidate_odin_rc=0`
- `m24_odin_returned=1 device=/dev/bus/usb/002/010`
- `magisk_boot_rollback_odin_rc=0`
- `post_m24_boot_rollback_pstore_files=[]`
- `post_m24_boot_rollback_pstore_marker_found=0`
- `post_m24_boot_rollback_last_kmsg_bytes=2097136`
- `post_m24_boot_rollback_last_kmsg_marker_found=0`
- `m24_capture_pstore_pmsg_prefix_found=0`
- `post_m24_boot_rollback_pmsg_step_count=0`
- `m24_reset_reason_result=pass`
- `/proc/reset_reason`: `NPON`
- `/proc/reset_rwc`: `0`
- `/proc/store_lastkmsg`: `0`
- `/proc/reset_summary`: `cat: /proc/reset_summary: No such file or directory`
- `/proc/reset_klog`: `cat: /proc/reset_klog: No such file or directory`
- `/proc/reset_history`: `cat: /proc/reset_history: No such file or directory`
- `/proc/reset_tzlog`: `cat: /proc/reset_tzlog: No such file or directory`

Final Android/Magisk baseline was re-verified after rollback:

- `sys.boot_completed=1`
- `ro.boot.verifiedbootstate=orange`
- `ro.boot.boot_recovery=0`
- Magisk root `uid=0(root)`
- boot SHA256:
  `2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e`
- vendor_boot SHA256:
  `096e433e049fb088cd956e083d5a1039b33cdf0ca907e713bba7feaaf1b080b7`

## Timing

Canonical timing is present at `timeline.json` with a single top-level
`events` schema:

- `live_session_start -> candidate_flash_start`: 10.780s
- `candidate_flash_start -> candidate_flash_done`: 1.490s
- `candidate_flash_done -> candidate_boot_ready`: 55.727s
- `candidate_boot_ready -> rollback_flash_start`: 0.000s
- `rollback_flash_start -> rollback_flash_done`: 1.331s
- `rollback_flash_done -> rollback_boot_ready`: 44.700s
- `rollback_boot_ready -> live_session_end`: 10.450s
- total: 124.479s

## Interpretation

M24 did not prove the DTS-exact QMP/DWC3 substrate and did not produce retained
pmsg localization. The result is narrower than "M24 init never ran": absence of
`A90_STEP:M24:` means no marker survived in the current retained channels. That
can be because the candidate failed before the first retained pmsg write, or
because `/dev/pmsg0`/pstore-pmsg is not a reliable retention path for this
native-init warm-reset class.

The consumed M24 `AGENTS.md` exception and paired Odin path were retired after
the run, so the same helper now fails closed without a fresh exception. Do not
repeat M24 unchanged. The next bounded unit should either change the observation
path with a positive control for pmsg retention at native-init timing, or move
to the separately mentioned watchdog-dump precondition variant such as a
freshly gated `qcom_wdt_core` path.
