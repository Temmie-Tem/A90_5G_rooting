# Native Init V3358 Self-dd F1 Roundtrip Live

- Cycle: `V3358`
- Decision: `v3358-self-dd-f1-roundtrip-live-pass`
- Candidate: `A90 Linux init 0.11.121 (v3358-self-dd-f1-roundtrip)`
- Candidate boot SHA256: `106f797df52bc1c1ca887069dee0d01d3b0a20e00439711f6854520efce7723e`
- Planned source candidate: V3355 `A90 Linux init 0.11.119 (v3355-boot-write-e5-full)`
- Planned source candidate SHA256: `ed7aa46f9abc3d1a34c1d0eede247e58219b77375028b2f8bacd070454b1362c`
- Policy gate: `AGENTS.md` + design §12.1 amended in commit `2e71af94` for V3358 F1 only.
- Private run log: `workspace/private/runs/self-dd-v3358-f1-live-20260702T104030Z/`
- Final state: rolled back to `v2321-usb-clean-identity-rodata`, final `selftest fail=0`.

## Gate

- Rollback images were present and SHA-confirmed before flash: v2321, v2237, and v48.
- Pre-flash resident was v2321 with `selftest fail=0`.
- V3358 was flashed only through `native_init_flash.py`; pushed-image and boot readback SHA matched
  `106f797df52bc1c1ca887069dee0d01d3b0a20e00439711f6854520efce7723e`.
- V3358 boot verified `version/status`; independent selftest passed:
  `selftest: pass=12 warn=1 fail=0`.
- The staged V3355 candidate file existed in `/mnt/sdext/a90/flash-staging/`, and device-side
  SHA256 matched `ed7aa46f9abc3d1a34c1d0eede247e58219b77375028b2f8bacd070454b1362c`.
- No retained `/mnt/sdext/a90/flash-staging/boot-flash-f1-before.full` snapshot was present before
  the run.

## F0 Preflight

Command:

```text
boot-flash-plan /mnt/sdext/a90/flash-staging/boot_linux_v3355_boot_write_e5_full.img ed7aa46f9abc3d1a34c1d0eede247e58219b77375028b2f8bacd070454b1362c 0.11.119
```

Observed F0 output:

```text
A90BWF0 before_full_sha=a549fa7168f81a11d47000b5dcc7962ccd8cc193d01c115b31e59e1da7830c6a
A90BWF0 candidate_sha=ed7aa46f9abc3d1a34c1d0eede247e58219b77375028b2f8bacd070454b1362c expected_sha_match=1
A90BWF0 expected_version=0.11.119 version_marker_found=1
A90BWF0 current_stream_sha=a549fa7168f81a11d47000b5dcc7962ccd8cc193d01c115b31e59e1da7830c6a current_match_before=1
A90BWF0 target_full_sha=fa1deeae1ff724c44d6102c5685764e01863ec5a163ca97b4aba6e397f4d4eea
A90BWF0 changed_chunks=5 changed_bytes=1431428 chunk_len=1048576
A90BWF0 result=ok source-plan-only
A90P1 END seq=8 cmd=boot-flash-plan rc=0 errno=0 duration_ms=2914 flags=0x0 status=ok
```

## F1 Roundtrip Result

Command:

```text
boot-flash-f1 BOOT-FLASH-F1-PAIRED-ROUNDTRIP /mnt/sdext/a90/flash-staging/boot_linux_v3355_boot_write_e5_full.img ed7aa46f9abc3d1a34c1d0eede247e58219b77375028b2f8bacd070454b1362c 0.11.119
```

Observed F1 output:

```text
A90BWF1 token=accepted mode=paired-content-roundtrip reboot_candidate=0
A90BWF1 before_full_sha=a549fa7168f81a11d47000b5dcc7962ccd8cc193d01c115b31e59e1da7830c6a
A90BWF1 candidate_sha=ed7aa46f9abc3d1a34c1d0eede247e58219b77375028b2f8bacd070454b1362c expected_sha_match=1
A90BWF1 expected_version=0.11.119 version_marker_found=1
A90BWF1 target_full_sha=fa1deeae1ff724c44d6102c5685764e01863ec5a163ca97b4aba6e397f4d4eea
A90BWF1 changed_chunks=5 changed_bytes=1431428 chunk_len=1048576
A90BWF1 snapshot_sha=a549fa7168f81a11d47000b5dcc7962ccd8cc193d01c115b31e59e1da7830c6a snapshot_match_before=1
A90BWF1 snapshot_reopen_sha=a549fa7168f81a11d47000b5dcc7962ccd8cc193d01c115b31e59e1da7830c6a snapshot_reopen_match_before=1
A90BWF1 target_pwrite_count=64 target_fsync=ok
A90BWF1 target_full_sha_after=fa1deeae1ff724c44d6102c5685764e01863ec5a163ca97b4aba6e397f4d4eea target_full_match=1
A90BWF1 restore_pwrite_count=64 restore_fsync=ok
A90BWF1 restore_full_sha_after=a549fa7168f81a11d47000b5dcc7962ccd8cc193d01c115b31e59e1da7830c6a restore_full_match=1
A90BWF1 target_written=1 restore_attempted=1
A90BWF1 snapshot_cleaned=1
A90BWF1 result=ok paired-roundtrip-restored
A90P1 END seq=9 cmd=boot-flash-f1 rc=0 errno=0 duration_ms=7914 flags=0x4 status=ok
```

This proves the first content-changing self-dd rung: normal-boot native-init wrote the planned
content-changing 64MiB `target.full` to boot, verified the full boot partition SHA against the target
digest, restored the captured `before.full`, and verified the full boot partition SHA returned to the
before digest, all before any reboot into the changed target.

## Health And Rollback

- Post-F1 selftest: `pass=12 warn=1 fail=0`.
- Post-F1 status: `selftest fail=0`, pstore entries `0`.
- Post-F1 pstore summary: `entries=0`.
- Rollback flash used v2321 SHA
  `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`; pushed-image and readback
  SHA matched.
- Final v2321 version: `0.9.285 build=v2321-usb-clean-identity-rodata`.
- Final v2321 status: `selftest fail=0`, pstore entries `0`.
- Final independent v2321 selftest: `pass=11 warn=1 fail=0`.
- Final pstore summary after `hide`: `entries=0`.

## Serial Notes

Before F1, the managed serial bridge was restarted and all critical commands were sent with
`--input-mode slow`. F1 itself completed cleanly. After rollback, two independent final post-checks
were mistakenly launched in parallel; that caused host-side serial lock/input corruption
(`selfteAst`, `pstr sAT`). Restarting the managed bridge and running checks sequentially immediately
confirmed final v2321 `version`, `selftest fail=0`, and pstore `entries=0`.

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

It also records optional `source_plan_done`, `self_write_done`, and `readback_verified` events. The
timing aggregator accepted the timeline set with `invalid_timelines=[]`.

## Conclusion

V3358 F1 passed live. The device accepted a content-changing boot self-write and then restored the
exact previous full boot image before reboot, with clean post-probe health and clean v2321 rollback.
This closes F1 only. F2, F3, F4, and production self-write integration remain blocked until a future
explicit policy amendment.
