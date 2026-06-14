# Native Init V2253 Firmware Class Boundary Stack Live

## Summary

- Cycle: `V2253`
- Type: rollbackable live validation of the V2252 firmware_class before/after feed stack observer.
- Decision: `v2253-fwclass-boundary-stack-live-pass-target-stack-visible-before-feed`
- Result: `PASS`
- Reason: V2252 boundary stack artifacts were collected and classified; rollback selftest fail=0 passed
- Execute mode: `True`
- Evidence: `workspace/private/runs/kernel/v2253-fwclass-boundary-stack-live-20260612-132714`
- Track: T1 kernel observation; no downgrade to T2/T3.

## Images

- Test image: `workspace/private/inputs/boot_images/boot_linux_v2252_fwclass_boundary_stack.img`
- Test SHA256: `4ce33e0c1b2b542d9b5d043a3c120d74f657208c803860ad228957162c8634d4`
- Test version: `A90 Linux init 0.9.271 (v2252-fwclass-boundary-stack)`
- Rollback image: `workspace/private/inputs/boot_images/boot_linux_v2237_supplicant_terminate_poll.img`
- Rollback SHA256: `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`
- Rollback version: `A90 Linux init 0.9.268 (v2237-supplicant-terminate-poll)`

## Live Evidence

- Preflight baseline verified: `True` selftest fail=0: `True`
- V2252 flash OK: `True`
- V2252 health: version=`True` status=`True` selftest_fail0=`True`
- Rollback OK: `True` via `from-native`
- Rollback health: version=`True` status=`True` selftest_fail0=`True`
- Boundary phase count: `2`
- Ordering class: `target-stack-visible-before-feed`
- Feeder: seen=`1` fed=`1` timed_out=`1`
- Helper result: supervisor=`wlan0-ready` exit=`0` timed_out=`0` wlan0_present=`1`

## Boundary Classification

- Request `0` `WCNSS_qcom_cfg.ini`: seen=`1` fed=`1` final_seen=`1` final_fed=`1` bytes=`13343`
  - before_feed: boundary=`1` target_hits=`1` samples=`5` symbols=`7/7` full=`True`
  - after_feed: boundary=`1` target_hits=`1` samples=`5` symbols=`0/7` full=`False`
- Request `1` `bdwlan.bin`: seen=`None` fed=`None` final_seen=`0` final_fed=`0` bytes=`None`
  - before_feed: boundary=`None` target_hits=`None` samples=`None` symbols=`0/7` full=`False`
  - after_feed: boundary=`None` target_hits=`None` samples=`None` symbols=`0/7` full=`False`
- Request `2` `regdb.bin`: seen=`None` fed=`None` final_seen=`0` final_fed=`0` bytes=`None`
  - before_feed: boundary=`None` target_hits=`None` samples=`None` symbols=`0/7` full=`False`
  - after_feed: boundary=`None` target_hits=`None` samples=`None` symbols=`0/7` full=`False`

## Interpretation

- The full V2246 firmware_class/qcacld-HDD whitelist stack was visible before the `WCNSS_qcom_cfg.ini` userspace fallback feed.
- The matching after-feed snapshot no longer contained the seven whitelist symbols; the sampled worker had moved to a later wait state.
- `bdwlan.bin` and `regdb.bin` were not requested through this bounded userspace fallback path in the captured boot.
- Conclusion: the post-FWREADY tail path definitely executes, and the V2250 generic CPU-clock zero-hit result was a sampler-miss artifact, not function absence.
- Next loop should not spend another iteration on generic CPU-clock tuning for this tail. Re-evaluate T1 for a new independent kernel-observation question; if none is meaningful, record the drop trigger and proceed to T2 WLAN surface/cleanup work.

## Safety Scope

- Flash path is limited to boot partition via `native_init_flash.py`.
- Rollback target is V2237, with post-rollback `version`/`status`/`selftest fail=0` verification.
- Collection uses read-only `cat` through the native bridge after the helper window.
- This run does not use Wi-Fi scan/connect, credentials, DHCP/routes, external ping, `probe_write_user`, tracefs control writes, eSoC/PCIe/GDSC/PMIC/GPIO paths, platform bind/unbind, or `sda29` writes.
- The only non-read-only target-side operation inside V2252 is the pre-existing bounded firmware_class userspace fallback feed for `WCNSS_qcom_cfg.ini`, `bdwlan.bin`, and `regdb.bin`.
