# Native Init V3355 §0.2 Write-Probe E5 Full Source Build

- Cycle: `V3355`
- Decision: `v3355-boot-write-e5-full-source-build-pass`
- Init: `A90 Linux init 0.11.119 (v3355-boot-write-e5-full)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3355_boot_write_e5_full.img`
- Boot SHA256: `ed7aa46f9abc3d1a34c1d0eede247e58219b77375028b2f8bacd070454b1362c`
- Helper SHA256: `fa395d3ecb6944a57487f3966948a634596157e4de3fdc39575a2fc502d1ceef`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v3335_gpu_z3_primary_setcrtc.img`

## Change

- Adds `boot-write-e5 <token>` after the V3354 E4 live pass. E5 streams the entire 64MiB boot partition back to itself in 1MiB identity chunks.
- Before any write, the command verifies Android boot magic/header parse, computes an O_DIRECT full-partition SHA, computes a normal-read source SHA, and requires those SHAs to match. It then performs 64 identity `pwrite` calls, fsyncs once, and compares the O_DIRECT full-partition SHA after the write.
- This is the highest-consequence identity rung. It still changes no bytes on completion, but an interrupted write can corrupt any boot LBA; rollback/recovery remains external and boot-only.

## Validation Contract

- PASS requires post-flash `selftest fail=0`, `version` 0.11.119, and after `hide`, `boot-write-e5 BOOT-WRITE-PROBE-E5-FULL-IDENTITY` emitting `target_off=0`, `len=67108864`, `expected_chunks=64`, `source_match_before=1`, `pwrite_count=64`, `region_match_all=1`, `full_match=1`, then rollback to `v2321` with `selftest fail=0`.
- This is a source-build preparation only; no live V3355 write is claimed here.

## Metadata

- Helper flags: `-DA90_WIFI_TEST_BOOT_SERVICE_OBJECT_POST_FW_READY_FWCLASS_BRIDGE=1`
- Init extra flags: ``
- Candidate type: `boot-write-e5-full-candidate`.
