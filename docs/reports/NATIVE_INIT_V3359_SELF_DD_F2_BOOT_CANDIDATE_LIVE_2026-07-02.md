# Native Init V3359 Self-dd F2 Boot Candidate Live

- Cycle: `V3359`
- Decision: `v3359-self-dd-f2-boot-candidate-live-pass`
- Candidate: `A90 Linux init 0.11.122 (v3359-self-dd-f2-boot-candidate)`
- Candidate boot SHA256: `4f51a7a325c014b80571fd1f8982f0510c48ea8b7c666721d4667a54626fd8c9`
- Planned source candidate: V3355 `A90 Linux init 0.11.119 (v3355-boot-write-e5-full)`
- Planned source candidate SHA256: `ed7aa46f9abc3d1a34c1d0eede247e58219b77375028b2f8bacd070454b1362c`
- Policy gate: `AGENTS.md` + design §12.1 amended in commit `4f32c053` for V3359 F2 only.
- Private run log: `workspace/private/runs/self-dd-v3359-f2-live-20260702T110655Z/`
- Final state: rolled back to `v2321-usb-clean-identity-rodata`, final `selftest fail=0`.

## Gate

- Rollback images were present and SHA-confirmed before flash: v2321, v2237, and v48.
- Pre-flash resident was v2321 with `selftest fail=0` and pstore entries `0`.
- V3359 was flashed only through `native_init_flash.py`; pushed-image and boot readback SHA matched
  `4f51a7a325c014b80571fd1f8982f0510c48ea8b7c666721d4667a54626fd8c9`.
- V3359 boot verification used raw version fallback after the helper missed a cmdv1 END marker, then
  the bridge was restarted and normal cmdv1 health passed:
  `0.11.122 build=v3359-self-dd-f2-boot-candidate`, `selftest fail=0`, pstore entries `0`.
- The staged V3355 candidate file existed in `/mnt/sdext/a90/flash-staging/`, and device-side
  SHA256 matched `ed7aa46f9abc3d1a34c1d0eede247e58219b77375028b2f8bacd070454b1362c`.

## F0 Preflight

Command:

```text
boot-flash-plan /mnt/sdext/a90/flash-staging/boot_linux_v3355_boot_write_e5_full.img ed7aa46f9abc3d1a34c1d0eede247e58219b77375028b2f8bacd070454b1362c 0.11.119
```

Observed key output:

```text
A90BWF0 before_full_sha=60544a9ceadf1457535ffa5d51c7510a8fba8eab695433c1dfce55aad96917b3
A90BWF0 candidate_sha=ed7aa46f9abc3d1a34c1d0eede247e58219b77375028b2f8bacd070454b1362c expected_sha_match=1
A90BWF0 expected_version=0.11.119 version_marker_found=1
A90BWF0 target_full_sha=fa1deeae1ff724c44d6102c5685764e01863ec5a163ca97b4aba6e397f4d4eea
A90BWF0 changed_chunks=5 changed_bytes=1439248 chunk_len=1048576
A90BWF0 result=ok source-plan-only
A90P1 END seq=9 cmd=boot-flash-plan rc=0 errno=0 duration_ms=3000 flags=0x0 status=ok
```

## F2 Boot Candidate Result

Command:

```text
boot-flash-f2 BOOT-FLASH-F2-BOOT-CANDIDATE /mnt/sdext/a90/flash-staging/boot_linux_v3355_boot_write_e5_full.img ed7aa46f9abc3d1a34c1d0eede247e58219b77375028b2f8bacd070454b1362c 0.11.119
```

Observed key output:

```text
A90BWF2 token=accepted mode=boot-candidate-write reboot_candidate=host-controlled
A90BWF2 before_full_sha=60544a9ceadf1457535ffa5d51c7510a8fba8eab695433c1dfce55aad96917b3
A90BWF2 candidate_sha=ed7aa46f9abc3d1a34c1d0eede247e58219b77375028b2f8bacd070454b1362c expected_sha_match=1
A90BWF2 expected_version=0.11.119 version_marker_found=1
A90BWF2 target_full_sha=fa1deeae1ff724c44d6102c5685764e01863ec5a163ca97b4aba6e397f4d4eea
A90BWF2 snapshot_sha=60544a9ceadf1457535ffa5d51c7510a8fba8eab695433c1dfce55aad96917b3 snapshot_match_before=1
A90BWF2 snapshot_reopen_sha=60544a9ceadf1457535ffa5d51c7510a8fba8eab695433c1dfce55aad96917b3 snapshot_reopen_match_before=1
A90BWF2 target_pwrite_count=64 target_fsync=ok
A90BWF2 target_full_sha_after=fa1deeae1ff724c44d6102c5685764e01863ec5a163ca97b4aba6e397f4d4eea target_full_match=1
A90BWF2 restore_skipped=target-verified-host-reboot-required
A90BWF2 target_written=1 restore_attempted=0
A90BWF2 snapshot_retained=/mnt/sdext/a90/flash-staging/boot-flash-f2-before.full
A90BWF2 reboot_required=1 host_must_reboot_now=1
A90BWF2 result=ok target-written-ready-to-reboot
A90P1 END seq=10 cmd=boot-flash-f2 rc=0 errno=0 duration_ms=7101 flags=0x4 status=ok
```

The host immediately sent `reboot`. That command synced and restarted before returning an END marker,
which is expected for the reboot command itself.

## Self-Written Candidate Boot

- The device booted the self-written V3355 candidate:
  `0.11.119 build=v3355-boot-write-e5-full`.
- Candidate status passed with `selftest fail=0`.
- Independent candidate selftest passed: `pass=12 warn=1 fail=0`.
- Candidate pstore summary reported `entries=0`.
- The F2 `before.full` snapshot was retained on SD at size `67108864` until rollback completed.

## Rollback And Cleanup

- Rollback flash used v2321 SHA
  `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`; pushed-image and readback
  SHA matched.
- Rollback boot verification used raw version fallback after the helper missed a cmdv1 END marker,
  then the bridge was restarted and normal cmdv1 final health passed.
- Final v2321 version: `0.9.285 build=v2321-usb-clean-identity-rodata`.
- Final v2321 status: `selftest fail=0`, pstore entries `0`.
- Final independent v2321 selftest: `pass=11 warn=1 fail=0`.
- The retained F2 snapshot was deleted after rollback; staging now contains only the V3355 candidate.

## Timeline

Private `timeline.json` uses the canonical single top-level `events` schema and contains the required
phase events:

```text
candidate_flash_start
candidate_flash_done
candidate_boot_ready
live_session_start
live_session_end
rollback_flash_start
rollback_flash_done
rollback_boot_ready
```

It also records optional `source_plan_done`, `self_write_done`, `readback_verified`,
`self_written_candidate_reboot_requested`, `self_written_candidate_boot_ready`, and
`final_health_done` events. The timing aggregator accepted the timeline set with
`invalid_timelines=[]`.

## Conclusion

V3359 F2 passed live. Normal-boot native-init wrote the planned content-changing 64MiB `target.full`
to boot, verified the full boot partition SHA against the target digest, rebooted into that
self-written candidate, confirmed candidate health, and rolled back cleanly to v2321. This closes F2
only. F3, F4, and production self-write integration remain blocked until a future explicit policy
amendment.
