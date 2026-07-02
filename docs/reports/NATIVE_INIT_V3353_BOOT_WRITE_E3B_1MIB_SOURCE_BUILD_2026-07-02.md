# Native Init V3353 §0.2 Write-Probe E3b 1MiB Source Build

- Cycle: `V3353`
- Decision: `v3353-boot-write-e3b-1mib-source-build-pass`
- Init: `A90 Linux init 0.11.117 (v3353-boot-write-e3b-1mib)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3353_boot_write_e3b_1mib.img`
- Boot SHA256: `a4cc3c93a37ba350ed7b0fd94503e82fae8f8169dc3ddaa76a9256bac5257091`
- Helper SHA256: `fa395d3ecb6944a57487f3966948a634596157e4de3fdc39575a2fc502d1ceef`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v3335_gpu_z3_primary_setcrtc.img`

## Change

- Adds `boot-write-e3b <token>` after the V3352 sparse16 live pass. E3b writes one contiguous 1MiB block in parsed tail slack, using the exact bytes read from the device.
- Unlike the zero-only rungs, E3b requires the 1MiB source block to contain non-zero bytes. This proves a non-zero write buffer and TWRP-sized chunk while keeping the offset outside the parsed boot image body and at least 1MiB before the partition end.
- The safety envelope remains guarded: `CMD_DANGEROUS`, no auto-menu execution, O_NOFOLLOW + identity on every fd, one fsync after the identity pwrite, O_DIRECT 1MiB readback, and O_DIRECT full-partition SHA before/after.

## Validation Contract

- PASS requires post-flash `selftest fail=0`, `version` 0.11.117, and after `hide`, `boot-write-e3b BOOT-WRITE-PROBE-E3B-1MIB-SLACK` emitting positive `nonzero_bytes`, `pwrite_count=1`, `region_match_all=1`, `full_match=1`, then rollback to `v2321` with `selftest fail=0`.
- This is a source-build preparation only; no live V3353 write is claimed here.

## Metadata

- Helper flags: `-DA90_WIFI_TEST_BOOT_SERVICE_OBJECT_POST_FW_READY_FWCLASS_BRIDGE=1`
- Init extra flags: ``
- Candidate type: `boot-write-e3b-1mib-candidate`.
