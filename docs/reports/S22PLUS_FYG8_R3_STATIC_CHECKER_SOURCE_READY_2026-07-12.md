# S22+ FYG8 R3 Static Checker Source Ready

Date: 2026-07-12 KST
Target: `SM-S906N/g0q/S906NKSS7FYG8`
Scope: host-only checker implementation and read-only input audit; no boot/AP
construction, device contact, Odin invocation, or flash

## Result

`s22plus_fyg8_r3_static_checker.py` now implements the corrected R3C0/R3C1
contract. Its exact pinned `inputs` stage passed against the locally retained
FYG8 evidence:

```text
schema=s22plus_fyg8_r3_static_checker_v1
stage=inputs
verdict=PASS_R3_INPUTS_READY
full_firmware_evidence=extracted-six-file-set
device_contact=false
image_construction=false
ap_construction=false
odin_invocation=false
flash_authorized=false
```

This closes checker-source readiness and current-input readiness only. It does
not create, authorize, or prove an R3C0/R3C1 artifact.

## Source Pins

| File | Size | SHA256 |
|---|---:|---|
| `workspace/public/src/scripts/revalidation/s22plus_fyg8_r3_static_checker.py` | 46,207 | `917b12f82dc5525b84cf2627379a80e49d921b6c33ca79fe3fc5c6a9ece6a514` |
| `tests/test_s22plus_fyg8_r3_static_checker.py` | 10,389 | `0a4671a08c256e0a7a8cd8a31321a43570de48ba5908a1368ee4b69e7e97429b` |

The final private `/tmp` audit JSON was 11,413 bytes with SHA256
`40ae3e81e100e5a7cb7201bc46d59611487f2a7443e4d772d4fdf31fc37d1199`.
It is evidence for this run, not a repository artifact or future live pin.

## Stage Contract

The checker has three mutually constrained stages:

- `inputs`: exact R1/R2, R2 Image, stock boot/LZ4, rollback boots/APs,
  DTBO/recovery, tools, and full firmware evidence only;
- `r3c0`: all input checks plus separately supplied exact SHA pins for one
  normalized control raw boot and AP;
- `r3c1`: all R3C0 checks plus separately supplied exact SHA pins for one
  kernel-only candidate raw boot and AP.

Supplying artifact arguments to a stage that does not consume them is an error.
R3C0/R3C1 missing pins fail before the expensive full-firmware audit.

## Enforced Boot Contract

The checker:

- parses the full 100,663,296-byte boot as 11 contiguous regions;
- pins the exact 528-byte stock `SignerVer02` record;
- derives R3C0 only as the exact 16-byte `SEANDROIDENFORCE` normalization plus
  the single AVB `original_image_size` update;
- requires exact stock kernel and ramdisk in R3C0;
- requires R3C1 to equal R3C0 except for the exact R2 Image kernel range;
- explicitly requires stock vbmeta bytes and geometry in R3C0 and identical
  R3C0 vbmeta/footer in R3C1;
- requires exact ARM64 header equivalence and the exact FYG8 Linux banner;
- distinguishes stock full AVB verification from the future expected stale
  payload digest in R3C0/R3C1.

`avbtool` receives the already-hashed boot bytes through a sealed Linux memfd
and an ephemeral `boot` symlink. It never re-opens the user-provided path. This
closes the post-hash path-substitution gap found during independent review.

## Enforced AP Contract

The checker parses AP bytes directly rather than trusting `tarfile` member
names. It requires:

- exact lowercase 41-byte `md5  AP.tar\n` trailer and matching tar-prefix MD5;
- canonical POSIX ustar header checksum;
- exactly one raw regular member named `boot.img.lz4`;
- no PAX/GNU extension, link, device, duplicate, extra member, path traversal,
  nonzero data padding, or nonzero data after terminal tar blocks;
- deterministic mode/owner/time metadata for R3C0/R3C1 APs;
- one standard LZ4 frame, valid reserved-bit shape, exact declared
  100,663,296-byte content size, bounded AP size, and no trailing/concatenated
  frame;
- external pinned-LZ4 decompression that equals the exact expected raw boot.

The resulting `flash_member_set` is exactly `["boot.img.lz4"]`; DTBO,
recovery, vendor_boot, and every other partition member are structurally
excluded.

## Validation

```text
py_compile: PASS
new R3 checker tests: 14 PASS
related Magisk boot audit tests: 7 PASS
related R2 audit tests: 6 PASS
focused total: 27 PASS
git diff --check: PASS
```

Final exact-input run:

```text
elapsed=23.83s
max_rss=755048 KiB
exit_status=0
verdict=PASS_R3_INPUTS_READY
stock_avb_input_transport=sealed-memfd
stock_avb_signature_verified=true
stock_avb_payload_hash_verified=true
```

The run streamed and rehashed the 11.5GB stock AP in the accepted six-file
firmware evidence set. All three retained LZ4 inputs declared and decoded to
exactly 100,663,296 bytes.

## Independent Review

Claude Opus reviewed the uncommitted checker and tests read-only against the
carrier audit and R3 design. It returned **GO to commit checker source** and
unchanged NO-GO for artifact generation/AP/flash/device work.

Review disposition:

- valid: `avbtool` originally re-opened a path after hashing; fixed with a
  sealed memfd and revalidated live against stock AVB;
- defense-in-depth: explicit vbmeta-size/blob/footer assertions were added even
  though the full expected-byte comparison already covered them;
- defense-in-depth: output now states the exact one-member boot-only flash set;
- clarified: the LZ4 BD reserved-bit test was rewritten as separate high-bit
  and low-nibble checks;
- accepted fail-closed behavior: exact `AP.tar` trailer naming remains the
  project format used by all pinned APs.

Usage was checked before and after as requested. Before: current session 0%,
weekly all-model 48%, reset 01:50 KST. After: current session 10%, weekly 48%,
cost `$3.25`, API duration 57 seconds, wall duration 6m28s. The long interactive
reasoning was interrupted and constrained to findings only; no edits or device
actions were delegated.

## Remaining Boundary

No R3C0 or R3C1 raw boot/AP exists. The next unit is separately authorized
artifact construction and independent reproduction for R3C0 only. R3C1 remains
blocked until a future attended R3C0 live PASS and mandatory rollback. Neither
artifact construction nor live work is authorized by this report.
