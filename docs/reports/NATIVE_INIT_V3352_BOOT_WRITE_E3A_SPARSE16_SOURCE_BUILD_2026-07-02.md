# Native Init V3352 §0.2 Write-Probe E3a Sparse16 Source Build

- Cycle: `V3352`
- Decision: `v3352-boot-write-e3a-sparse16-source-build-pass`
- Init: `A90 Linux init 0.11.116 (v3352-boot-write-e3a-sparse16)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3352_boot_write_e3a_sparse16.img`
- Boot SHA256: `7eea6580236dff3fcd38e5e19689873da2e140d001edf6f5f53fca9d0b579cd8`
- Helper SHA256: `fa395d3ecb6944a57487f3966948a634596157e4de3fdc39575a2fc502d1ceef`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v3335_gpu_z3_primary_setcrtc.img`

## Change

- Adds `boot-write-e3a <token>` after the V3351 E2 live pass. E3a is the sparse confirmed-zero expansion rung: sixteen 4096B sectors selected from the observed all-zero tail-slack population.
- E3a deliberately avoids the original contiguous 1MiB E3 assumption because V3351 found only 26 all-zero sectors in the scanned slack window. It scales write count and loop exposure while keeping every selected sector in confirmed-zero padding.
- The safety envelope is unchanged: `CMD_DANGEROUS`, no auto-menu execution, O_NOFOLLOW + identity on every fd, one fsync after the sixteen identity pwrite calls, O_DIRECT per-target readback, and O_DIRECT full-partition SHA before/after.

## Validation Contract

- PASS requires post-flash `selftest fail=0`, `version` 0.11.116, and after `hide`, `boot-write-e3a BOOT-WRITE-PROBE-E3A-SPARSE-TAILSLACK` emitting `zero_candidates>=16`, sixteen `selectedN_off`/`targetN_off` lines, `pwrite_count=16` (or a clean refusal), `region_match_all=1`, `full_match=1`, then rollback to `v2321` with `selftest fail=0`.
- This is a source-build preparation only; no live V3352 write is claimed here.

## Metadata

- Helper flags: `-DA90_WIFI_TEST_BOOT_SERVICE_OBJECT_POST_FW_READY_FWCLASS_BRIDGE=1`
- Init extra flags: ``
- Candidate type: `boot-write-e3a-sparse16-candidate`.
