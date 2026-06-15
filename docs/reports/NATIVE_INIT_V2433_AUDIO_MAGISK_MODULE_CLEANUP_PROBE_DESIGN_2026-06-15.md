# NATIVE_INIT V2433 — Magisk Module Staging Cleanup Probe Design

Date: 2026-06-15

## Purpose

Design the next safe step after V2432 re-opened the Magisk module namespace. V2432 proved
that corrected `adb shell "su -c '<script>'"` and `su -mm -c` probes execute as Magisk root
and can read `/data/adb/modules` without root permission-denied lines. The next question is
not whether to activate M1 immediately; it is whether a targeted module-namespace write can
be cleaned up deterministically with no residue.

This V2433 unit is host-only design. It performs no Android boot, no `/data/adb` write, no
module install, no playback, and no calibration ioctl.

## Direction

Magisk modules remain useful for this project in the same way they were useful during Wi-Fi
handoffs: as a rollbackable Android-good measurement capsule. They are not a native-init runtime
dependency and should not become one.

The corrected direction is:

1. Use direct Magisk-root staging with the fixed remote-shell quoting style.
2. First prove create/remove cleanup on an inert unique path.
3. Only then retry M1 `service.sh` activation for early Android-good ACDB payload capture.
4. Keep `magisk --install-module` as a fallback only if direct targeted staging/cleanup fails,
   because installer cleanup semantics are broader and less targeted.

## Proposed Future Live Gate

Future exact phrase for the create/remove probe:

```text
AUD-5I-magisk-cleanup-probe go: rollbackable Android Magisk module namespace create-remove probe, inert unique directory only, no module.prop, no service.sh, no reboot before cleanup, rollback to V2321
```

This phrase is intentionally distinct from the V2432 read-only gate and from any later M1
activation gate.

## Probe Shape

The future live runner should boot pinned Android through the checked helper and roll back to
V2321 exactly as V2432 did. The only new action is a single bounded write/cleanup probe under
`/data/adb/modules`.

Candidate probe root:

```text
/data/adb/modules/.a90_v2433_cleanup_probe_<run_stamp>
```

Rationale:

- It is unique per run.
- It is hidden and intentionally not a Magisk module ID.
- It contains no `module.prop`, `service.sh`, `post-fs-data.sh`, `system.prop`, `sepolicy.rule`,
  or executable payload.
- It is never rebooted into existence; cleanup must complete before Android reboot/recovery.

Future live sequence:

1. Android handoff and Magisk root settle through the checked helper.
2. `su -c id` and `su -mm -c id` must both show `uid=0(root)` / `u:r:magisk:s0`.
3. Abort if any existing path matches `/data/adb/modules/.a90_v2433_cleanup_probe_*`.
4. Abort if `/data/adb/modules` is not owned by root or cannot be read by Magisk root.
5. Create exactly one unique directory at the candidate path.
6. Create exactly one marker file such as `.probe` containing a non-secret run tag.
7. Read back `ls -ldZ`, `stat`, and marker content through `su -c` and optionally `su -mm -c`.
8. Remove exactly that candidate path.
9. Verify the candidate path and marker are absent.
10. Verify no `.a90_v2433_cleanup_probe_*` residue remains under `/data/adb/modules`.
11. Only after cleanup proof, reboot Android to recovery and flash V2321 with the checked helper.
12. Verify final native `selftest fail=0`.

## Hard Stops

The future runner must reject or avoid:

- `magisk --install-module`
- `magisk --remove-modules`
- any reboot before cleanup proof
- `module.prop`
- `service.sh`
- `post-fs-data.sh`
- `system.prop`
- `sepolicy.rule`
- executable payloads
- `chmod +x`
- broad `rm -rf /data/adb/modules` style paths
- glob-driven cleanup
- playback, mixer, PCM, `/dev/msm_audio_cal`, calibration ioctls, or ACDB replay
- raw partition writes, fastboot, or any non-boot partition write

The only allowed write path is the exact generated probe directory and marker file. All cleanup
commands must use an exact quoted path built from a fixed prefix and a runner-generated safe run tag.

## Cleanup Policy

Cleanup proof is the purpose of the probe, not a best-effort afterthought. The future runner should
record:

- pre-existing probe-residue check result,
- exact created path,
- marker file content/hash,
- root identity for the create/remove commands,
- post-remove absence check,
- final residue scan result,
- rollback and final selftest result.

If cleanup fails after one primary removal and one final exact-path cleanup attempt, classify the run
as an incident, do not proceed to M1 activation, and record the residue path. The residue is designed
to be inert because it lacks `module.prop` and boot scripts, but it is still not acceptable as a
normal outcome.

## Why Not `magisk --install-module` First

V2432 proved direct Magisk root can access the module namespace. Therefore the lowest-risk next
measurement is a targeted direct create/remove probe. `magisk --install-module ZIP` may create
`modules_update`, use internal install staging, and alter cleanup semantics beyond the one exact path
we want to validate. Keep it as a fallback only after direct targeted cleanup is disproven.

## Next Step

Implement V2434 as a source/test-only exact-gated runner for this V2433 design. The V2434 dry-run
must expose command safety metadata and focused tests must prove:

- wrong approval refuses before device action,
- generated probe path has the fixed safe prefix,
- no module activation files appear in the command plan,
- cleanup uses an exact quoted path and no broad glob,
- rollback command remains the checked V2321 helper path.

Only after that source/test unit passes should a live create/remove probe be run.
