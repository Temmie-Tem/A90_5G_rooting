# V2547 — ACDB indirect topology payload capture

Date: 2026-06-16

## Scope

Capture the ACDB `CORE_CUSTOM_TOPOLOGIES` payload from the own-process Android ACDB path without
HAL injection, real calibration SET, speaker playback, or native speaker writes.

This unit keeps the V2540/V2541 own-process handoff shape and changes only the `acdb_ioctl`
interposer behavior needed to capture the topology bytes:

- Resolve the real `acdb_ioctl` from `libaudcal.so` first, falling back to `RTLD_NEXT`.
- Keep capture unarmed through initialization; auto-arm only after successful
  `ACDB_CMD_INITIALIZE_V2` (`0x0001138c`) return.
- Log call-phase metadata while armed.
- Recognize `ACDB_CMD_GET_AVCS_CUSTOM_TOPO_INFO_V3` (`0x00013296`) as an indirect ABI where
  `in_buf` contains `{uint32_t len, uint32_t ptr}` and dump that pointed buffer.
- Exit immediately after the first successful, non-zero, 4916-byte topology capture.

Raw payload bytes remain private under `workspace/private/` and are not committed.

## Implementation

Touched public sources:

- `workspace/public/src/android/acdb_payload_capture/libacdbtap_v2475.c`
- `workspace/public/src/scripts/revalidation/build_android_acdb_armed_combined_preload_v2540.py`

Private build artifact used for the live run:

- Build dir: `workspace/private/builds/audio/v2547-acdb-indirect-topology-host-only/`
- Preload: `bin/liba90_acdb_armed_combined_preload_v2540.so`
- SHA256: `b2943f41776d84cc6946f29140bd1f0cf8bc9dc51ae26d8b7213a26ffa4bca74`

Existing helper reused:

- Helper: `workspace/private/builds/audio/v2540-acdb-armed-topology-host-only/bin/a90_acdb_armed_topology_exec_linked_v2540`
- SHA256: `b471fe9209d212097bd501699f8da3fe77ea8ca189b00bf368252d201cd6d1b0`

## Why V2547 was needed

The immediately preceding units narrowed the ABI problem:

- V2542/V2538-style armed capture hung before events at the first initialization call.
- V2543 fixed the resolver by explicitly resolving `acdb_ioctl` from `libaudcal.so`; init no longer
  hung, but the helper later exited before useful capture.
- V2544 armed only after successful initialization and captured valid small ACDB records, but no
  direct `out_len==4916` record.
- V2546 call-phase logging showed the topology command uses an indirect output pointer:
  `cmd=0x00013296`, actual `out_len=0x00000004`, `in_word0=0x00001334`, `in_word1=<payload VA>`.

Therefore the previous direct-`out_buf` classifier was looking at the wrong ABI field for the 4916-byte
record. V2547 dumps the indirect buffer instead.

## Live result

Run directory:

- `workspace/private/runs/audio/v2490-acdb-ownprocess-get-20260616-080716`

Runner decision:

- `v2490-acdbtap-success-4916-before-helper-exit-before-rollback-rollback-pass`
- `ok=true`
- `counts_toward_fails_twice=false`

Captured ordered `acdb_ioctl` records with `ret==0` and non-zero output:

| seq | cmd | in_len | captured_len | sha256 | note |
| --- | --- | --- | --- | --- | --- |
| `0x00000000` | `0x000131de` | `0x00000000` | `0x00000010` | `25513169f466cb63e98fe30731e7c577f76cb6b58283d4041b1c650d0bf0915c` | init-adjacent small record |
| `0x00000001` | `0x00013262` | `0x00000008` | `0x00000004` | `fb5e512425fc9449316ec95969ebe71e2d576dbab833d61e2a5b9330fd70ee02` | size/query record |
| `0x00000002` | `0x00013297` | `0x00000000` | `0x00000004` | `57e0c8cd1fbd539454489e739d06a59027fab0432f6f7187b7a39bb76ffc2bae` | size/query record |
| `0x00000003` | `0x00013296` | `0x00000008` | `0x00001334` | `7c5d45efa40944bc23dcc83af9f0046249499bb13d1a03c3470c287127992b89` | topology payload |

Topology payload verification:

- Raw private file: `workspace/private/runs/audio/v2490-acdb-ownprocess-get-20260616-080716/ownget-device-artifacts/acdbtap/acdbtap-00000003-cmd-00013296-len-00001334.bin`
- Size: `4916` bytes
- SHA256: `7c5d45efa40944bc23dcc83af9f0046249499bb13d1a03c3470c287127992b89`
- All-zero check: `false`

The `0x13296` call-phase metadata confirms the direct fifth-argument `out_len` stayed `0x00000004`,
while `in_word0` supplied the indirect length `0x00001334` and `in_word1` supplied the source pointer.
The captured 4916-byte payload is therefore the indirect topology buffer, not an unwritten direct
zero buffer.

## Rollback / health

The handoff rolled back to V2321 through the checked flash helper:

- Rollback image: `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`
- Expected SHA256: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- Final serial selftest: `fail=0`

Latest explicit post-run selftest:

```text
selftest: pass=11 warn=1 fail=0 duration=53ms entries=12
```

## Decision

`V2547` is a successful ACDB topology capture. The real `CORE_CUSTOM_TOPOLOGIES` payload is now
privately banked with a stable SHA-256 and can feed the V2474/V2462 native replay scaffold.

Do not commit the raw payload. Native calibration SET/replay remains a separate gate: the next replay
unit should consume only the pinned private payload path/SHA and must keep the existing cleanup and
rollback policy.
