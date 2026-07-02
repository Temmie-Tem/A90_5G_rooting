# Native Init V3355 §0.2 Write-Probe E5 Full-Partition Live

- Cycle: `V3355`
- Decision: `v3355-boot-write-e5-full-live-pass`
- Candidate: `A90 Linux init 0.11.119 (v3355-boot-write-e5-full)`
- Candidate boot SHA256: `ed7aa46f9abc3d1a34c1d0eede247e58219b77375028b2f8bacd070454b1362c`
- Private run log: `workspace/private/runs/self-dd-v3355-e5-live-20260702T010700Z/`
- Final state: rolled back to `v2321-usb-clean-identity-rodata`, final `selftest fail=0`.

## Gate

- Rollback images were present and SHA-confirmed before flash: v2321, v2237, and v48.
- Pre-flash resident was v2321 with `selftest fail=0`.
- Candidate flash used the checked helper `native_init_flash.py` with expected SHA and version guard.
- Candidate helper readback matched the V3355 boot SHA, then native boot verified `version/status`.
- Candidate selftest passed after a fresh client retry: `selftest: pass=12 warn=1 fail=0`.

## E5 Probe Result

Command:

```text
boot-write-e5 BOOT-WRITE-PROBE-E5-FULL-IDENTITY
```

Observed E5 output:

```text
A90BWE5 boot_header=ok version=1 page_size=4096 used_len=62644224
A90BWE5 full_sha_before=fa1deeae1ff724c44d6102c5685764e01863ec5a163ca97b4aba6e397f4d4eea
A90BWE5 source_sha=fa1deeae1ff724c44d6102c5685764e01863ec5a163ca97b4aba6e397f4d4eea source_match_before=1
A90BWE5 target_off=0 len=67108864 chunk_len=1048576 expected_chunks=64
A90BWE5 pwrite0_rc=1048576
...
A90BWE5 pwrite63_rc=1048576
A90BWE5 pwrite_count=64 pwrite=ok fsync=ok
A90BWE5 full_sha_after=fa1deeae1ff724c44d6102c5685764e01863ec5a163ca97b4aba6e397f4d4eea
A90BWE5 full_match=1
A90BWE5 region_match_all=1
A90BWE5 result=ok pwrite-permitted-identity-verified
A90BWE5 end rc=0
A90P1 END seq=7 cmd=boot-write-e5 rc=0 errno=0 duration_ms=3527 flags=0x4 status=ok
```

This proves normal-boot PID1 can stream-read the full 64MiB boot partition and write the identical
bytes back to every boot LBA in 64 one-megabyte `pwrite` calls. The normal-read source SHA matched
the O_DIRECT full-partition SHA before writing, every chunk write returned the full chunk length, and
the O_DIRECT full-partition SHA stayed unchanged after fsync.

## Health And Rollback

- Post-probe status: `selftest fail=0`, pstore entries `0`.
- Post-probe selftest: `pass=12 warn=1 fail=0`.
- Rollback flash used v2321 SHA
  `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`; readback SHA matched.
- Final v2321 version: `0.9.285 build=v2321-usb-clean-identity-rodata`.
- Final v2321 selftest: `pass=11 warn=1 fail=0`.
- Final pstore summary after `hide`: `entries=0`.

Two host-side `a90ctl` attempts produced no command output and were terminated host-side: the first
candidate selftest attempt and the first final version attempt. Fresh clients immediately passed
`version`/`selftest`; no device-side command failure was observed. The first final pstore query was
blocked by the auto-menu, then passed after `hide`.

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

## Conclusion

V3355 E5 passed. The self-dd identity ladder now proves normal-boot PID1 can complete identity writes
from the tail-slack sector through the entire 64MiB boot partition while preserving readback and
full-partition SHA, with clean v2321 rollback. This still does not prove a real fast-flash update:
content-changing new-image self-write remains a separate risk class and must be gated as its own rung.
