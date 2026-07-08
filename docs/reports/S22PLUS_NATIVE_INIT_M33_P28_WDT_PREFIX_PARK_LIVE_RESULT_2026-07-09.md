# S22+ M33 P28 Watchdog Prefix-Park Live Result

Date: 2026-07-09 03:23 KST / 2026-07-08 18:23 UTC

## Verdict

PASS: M33 P28 survived the full observation window and rollback completed.

The P28 one-shot live gate is consumed and retired. `AGENTS.md` no longer
contains the active P28 live/rollback tokens, so default helper execution must
fail closed again.

## Candidate

Helper:

`workspace/public/src/scripts/revalidation/s22plus_m33_p28_wdt_prefix_park_live_gate.py`

Run log:

`workspace/private/runs/s22plus_m33_p28_wdt_prefix_park_live_gate_20260708T181752Z/s22plus_m33_p28_wdt_prefix_park_live_gate.txt`

Candidate AP:

`workspace/private/outputs/s22plus_native_init/m33_wdt_prefix_park_matrix_v0_1/P28/odin4/AP.tar.md5`

Pinned hashes:

- AP.tar.md5: `4c76ef4df814356a7acfa9ce9a00c2fe003208ff8289c2874535e26b7e1c3f07`
- boot.img: `3bc59d6df58b5c7130e6ca531a6a6cd3a4d35e14ff7fd6667da72e2bd40e9e29`
- `/init`: `2ef661b9e5a1496674b6cc457c9b0e84c60ae7af01914c2403db602c6ebe84b1`
- module list: `ef57a00fbef4b9c89936b30fc5c001974fbe9c2ece590c6a6984cb4695318a8f`
- generated source: `8d752ade0ee5100b5f91cb7fb15c09d24652a97e03721fb8c4d784d1f419f289`
- preserved kernel: `bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff`
- base Magisk boot: `2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e`

## Result

- Candidate Odin flash: pass.
- Original Download endpoint disconnected after flash: pass.
- Observation window: 90 seconds.
- Host observed no ADB endpoint during the window.
- Host observed no Odin/Download endpoint during the window.
- Helper result: `m33_p28_survival_window_pass=1`.
- Helper result: `m33_p28_result=survived-observation-window-manual-download-required`.
- After survival proof, operator reported RDX/PMIC while entering manual
  recovery.
- Manual Download endpoint appeared later and rollback ran from that endpoint.
- Magisk boot rollback Odin flash: pass.
- Android boot after rollback: pass.
- Final boot partition SHA256:
  `2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e`.

Final Android baseline:

- `sys.boot_completed=1`
- `init.svc.bootanim=stopped`
- `ro.boot.verifiedbootstate=orange`
- Magisk root: `uid=0(root) ... context=u:r:magisk:s0`
- bootloader/build: `S906NKSS7FYG8`

## Timing

From `timeline.json`:

- live session: 267.482 s
- candidate flash: 1.491 s
- candidate boot-ready to rollback flash start: 207.431 s
- rollback flash: 1.368 s
- rollback flash done to Android boot-ready: 45.114 s

Timeline events use the standard single `events:[{name,timestamp_utc}]` schema.

## Retained Evidence

Collected files:

- `android_pstore/post_m33_p28_manual_after_survival_rollback_last_kmsg.bin`
- host observation snapshots under `host_observation/`
- `timeline.json`

Retained evidence summary:

- pstore files: none
- `/proc/last_kmsg`: readable, 2,097,136 bytes
- P28 marker in pstore/last_kmsg: absent
- `/proc/last_kmsg` contains `collect_rr_data : upload_cause = PMIC abnormal
  reset`, `RDX is locked`, `PonReason.HARD_RESET = 1`, and XBL/PMIC
  `boot_update_abnormal_reset_status` material, consistent with the operator's
  RDX/PMIC observation, but not a P28 marker.

## Interpretation

P28 adds `dwc3-msm.ko` and monitor gadget dependencies while still excluding
`usb_f_ss_acm.ko` and runtime configfs/ACM setup. Because it survived the 90
second window, the DWC3-without-ACM prefix is not the M32 no-ACM/bootloop
failure boundary.

Next high-information live target is P30, which adds the ACM function module
while still doing no runtime configfs/ACM setup. P40 is source-ready but lower
priority because P30 and P40 have the same module-list SHA256, so P40 adds less
boundary information unless a non-module runtime reason appears.
