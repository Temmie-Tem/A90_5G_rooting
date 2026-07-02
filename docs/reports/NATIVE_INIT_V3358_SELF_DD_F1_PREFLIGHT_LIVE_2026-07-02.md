# Native Init V3358 Self-dd F1 Preflight Live

- Cycle: `V3358`
- Decision: `v3358-self-dd-f1-preflight-live-pass-f1-write-not-executed`
- Candidate: `A90 Linux init 0.11.121 (v3358-self-dd-f1-roundtrip)`
- Candidate boot SHA256: `106f797df52bc1c1ca887069dee0d01d3b0a20e00439711f6854520efce7723e`
- Planned source candidate: V3355 `A90 Linux init 0.11.119 (v3355-boot-write-e5-full)`
- Planned source candidate SHA256: `ed7aa46f9abc3d1a34c1d0eede247e58219b77375028b2f8bacd070454b1362c`
- Private run log: `workspace/private/runs/self-dd-v3358-f1-preflight-live-20260702T101022Z/`
- Final state: rolled back to `v2321-usb-clean-identity-rodata`, final `selftest fail=0`.

## Gate

- Rollback images were present and SHA-confirmed before flash: v2321, v2237, and v48.
- Pre-flash resident was v2321 with `selftest fail=0`; pstore entries were `0`.
- Candidate flash used the checked helper `native_init_flash.py` with expected SHA and version guard.
- Candidate helper readback matched the V3358 boot SHA, then native boot verified `version/status`.
- Candidate selftest passed: `selftest: pass=12 warn=1 fail=0`.

## Staging

The first F0 attempt on V3358 reached the command correctly but found the planned candidate missing
from SD staging:

```text
A90BWF0 before_full_sha=a549fa7168f81a11d47000b5dcc7962ccd8cc193d01c115b31e59e1da7830c6a
A90BWF0 candidate_open=fail errno=2 (No such file or directory)
A90BWF0 stop=candidate-open
```

The host `tcpctl_host.py` install allowlist was extended to include the design-approved SD staging
root `/mnt/sdext/a90/flash-staging/`. The first upload attempt used the old default
`/cache/bin/toybox` and failed before transfer because that path was absent. Retrying with
`--toybox /bin/toybox` succeeded and device-side SHA matched:

```text
62644224 bytes (60 M) copied
ed7aa46f9abc3d1a34c1d0eede247e58219b77375028b2f8bacd070454b1362c  /mnt/sdext/a90/flash-staging/.boot_linux_v3355_boot_write_e5_full.img.tmp...
installed /mnt/sdext/a90/flash-staging/boot_linux_v3355_boot_write_e5_full.img
```

## F0 Preflight Result

Command:

```text
boot-flash-plan /mnt/sdext/a90/flash-staging/boot_linux_v3355_boot_write_e5_full.img ed7aa46f9abc3d1a34c1d0eede247e58219b77375028b2f8bacd070454b1362c 0.11.119
```

Observed F0 output:

```text
A90BWF0 mode=read-only-source-plan would_write=0
A90BWF0 target_node=/dev/block/sda24 resolve=sysfs-partname
A90BWF0 current_boot_header=ok version=1 page_size=4096 used_len=62644224
A90BWF0 before_full_sha=a549fa7168f81a11d47000b5dcc7962ccd8cc193d01c115b31e59e1da7830c6a
A90BWF0 candidate_path=/mnt/sdext/a90/flash-staging/boot_linux_v3355_boot_write_e5_full.img
A90BWF0 candidate_size=62644224
A90BWF0 candidate_header=ok version=1 page_size=4096 used_len=62644224
A90BWF0 candidate_used_within_file=1
A90BWF0 candidate_sha=ed7aa46f9abc3d1a34c1d0eede247e58219b77375028b2f8bacd070454b1362c expected_sha_match=1
A90BWF0 expected_version=0.11.119 version_marker_found=1
A90BWF0 current_stream_sha=a549fa7168f81a11d47000b5dcc7962ccd8cc193d01c115b31e59e1da7830c6a current_match_before=1
A90BWF0 target_full_sha=fa1deeae1ff724c44d6102c5685764e01863ec5a163ca97b4aba6e397f4d4eea
A90BWF0 changed_chunks=5 changed_bytes=1431428 chunk_len=1048576
A90BWF0 would_write=0
A90BWF0 result=ok source-plan-only
A90BWF0 end rc=0
A90P1 END seq=12 cmd=boot-flash-plan rc=0 errno=0 duration_ms=2909 flags=0x0 status=ok
```

This proves the V3358 F1-capable image boots cleanly and still computes the read-only source-plan
against the approved staged candidate. The planned target full-partition SHA remains
`fa1deeae1ff724c44d6102c5685764e01863ec5a163ca97b4aba6e397f4d4eea`; `changed_bytes` differs from
V3357 because the current resident before-image is V3358 rather than V3357.

## Health And Rollback

- Post-probe selftest: `pass=12 warn=1 fail=0`.
- Post-probe status: `selftest fail=0`, pstore entries `0`.
- Rollback flash used v2321 SHA
  `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`; readback SHA matched.
- Final v2321 version: `0.9.285 build=v2321-usb-clean-identity-rodata`.
- Final v2321 status: `selftest fail=0`, pstore entries `0`.
- Final standalone selftest returned `pass=11 warn=1 fail=0`.

## Serial Notes

One long normal-mode F0 command was corrupted on the serial input path before execution and returned
no `A90P1 END`; the visible command text was mangled. Restarting the managed bridge and switching to
`--input-mode slow` restored clean command framing. The final standalone selftest also had a noisy
echo, but the protocol trailer reported `cmd=selftest rc=0 status=ok`.

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

The timing aggregator accepted the timeline set with `timelines_found=7`, `runs_used=7`, and
`invalid_timelines=[]`.

## Conclusion

V3358 passed live boot and read-only F0 preflight. No `boot-flash-f1` command was run, and no
content-changing self-write to the boot partition was executed. The device ended in clean v2321
state. F1 execution remains blocked until the policy gate in `AGENTS.md` / design section 12.1 is
deliberately amended.
