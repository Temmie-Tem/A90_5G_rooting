# S22+ FYG8-Derived Disabled Vbmeta Preflight - 2026-07-06

## Scope

Build a disabled-vbmeta payload from the exact stock FYG8 `vbmeta.img`, package it
as a single-member Odin AP, and gate a bounded live flash. This unit is limited to
Samsung S22+ `SM-S906N` / `g0q` on `S906NKSS7FYG8`.

No boot, recovery, vendor_boot, bootloader, modem, EFS, RPMB, keymaster, userdata,
or full-firmware payload is included in the candidate AP.

## Why This Direction

The prior generic disabled vbmeta payload was not FYG8-derived and carried stale
metadata. Flashing stock FYG8 vbmeta-only AP recovered Android normal boot, so the
next safe test is to preserve the FYG8 vbmeta image and change only the AVB header
flags.

External references checked during design:

- AOSP AVB README: top-level `AVB_VBMETA_IMAGE_FLAGS_HASHTREE_DISABLED` sets
  `androidboot.veritymode=disabled`.
  <https://android.googlesource.com/platform/external/avb/+/master/README.md>
- AOSP `avb_vbmeta_image.h`: `HASHTREE_DISABLED = 1`, `VERIFICATION_DISABLED = 2`,
  serialized fields are network byte order, and `flags` is at header offset 120.
  <https://android.googlesource.com/platform/external/avb/+/refs/heads/master/libavb/avb_vbmeta_image.h>
- `libxzr/vbmeta-disable-verification`: direct local vbmeta patching is intended
  to match `fastboot --disable-verity --disable-verification flash vbmeta`.
  <https://github.com/libxzr/vbmeta-disable-verification>
- Public Samsung guides/threads consistently say to extract vbmeta from the exact
  firmware build before patching, rather than mixing a generic vbmeta.
  <https://xdaforums.com/t/guide-vbmeta-disabled-working-twrp-for-samsung-galaxy-with-the-latest-fw.4762670/>

## Inputs

- Stock FYG8 raw vbmeta:
  `workspace/private/inputs/s22plus_firmware/S906NKSS7FYG8_SKC/extracted-images/raw/vbmeta.img`
- Stock raw SHA256:
  `1031323af6c69c6894bb00ca5895463ea3f00066ec4d5eacc2bb58b0b2c6047b`
- Stock FYG8 vbmeta rollback AP:
  `workspace/private/outputs/s22plus_stock_vbmeta_rollback/AP.tar.md5`
- Rollback AP SHA256:
  `fdf42fb913ac82bba7414d41a2995300c9bc56d31e7cddf907b487e7b2ae707b`

## Patch Method

Tool:

- `workspace/public/src/scripts/revalidation/s22plus_patch_vbmeta_flags.py`

Command:

```bash
python3 workspace/public/src/scripts/revalidation/s22plus_patch_vbmeta_flags.py \
  --src workspace/private/inputs/s22plus_firmware/S906NKSS7FYG8_SKC/extracted-images/raw/vbmeta.img \
  --dst workspace/private/outputs/s22plus_fyg8_disabled_vbmeta/vbmeta.img \
  --expect-src-sha256 1031323af6c69c6894bb00ca5895463ea3f00066ec4d5eacc2bb58b0b2c6047b \
  --expect-old-flags 0 \
  --flags 3
```

Result:

```text
size=10176
old_flags=0
new_flags=3
changed_offsets=123
dst_sha256=9c0e5b9615f8dac2a902f709927ff3fccaa4e074b34adbd0f8cd7498db78ba13
```

`cmp -l` confirms the raw image differs at exactly one 1-based byte position:

```text
124   0   3
```

This corresponds to the low byte of the big-endian u32 flags field at header
offset 120.

## Static Validation

`avbtool.py info_image` on the patched output reports:

- Minimum libavb version: `1.0`
- Header block: `256 bytes`
- Authentication block: `576 bytes`
- Auxiliary block: `8832 bytes`
- Algorithm: `SHA256_RSA4096`
- Public key sha1: `e03300ab66600a17e63d91ad7f2357380a46a65c`
- Rollback index: `0`
- Flags: `3`
- Release string: `avbtool 1.3.0`

The FYG8 descriptors/properties remain present, including the FYG8 `2025-08-01`
security patch properties and chained partitions `recovery`, `dtbo`, `prism`, and
`optics`.

Python validation:

```bash
PYTHONPYCACHEPREFIX=/tmp/a90_pycache \
  python3 -m py_compile workspace/public/src/scripts/revalidation/s22plus_patch_vbmeta_flags.py
```

## Odin AP

The candidate uses the Odin4-compatible profile already proven on this device:
modern LZ4 frame, `--content-size -B6`, single tar member.

- Raw patched vbmeta SHA256:
  `9c0e5b9615f8dac2a902f709927ff3fccaa4e074b34adbd0f8cd7498db78ba13`
- `vbmeta.img.lz4` SHA256:
  `6ad2df2b899b195512e2ceb9831909c282f891fe007f3246ec91a72a2e665a9a`
- Candidate AP:
  `workspace/private/outputs/s22plus_fyg8_disabled_vbmeta/AP.tar.md5`
- Candidate AP SHA256:
  `804ff43b9f68278b026bd31d7703ca778518bb53a08e336e18b5016e3d2a2b4b`
- Tar member:
  `vbmeta.img.lz4`
- `vbmeta.img.lz4` roundtrip decode SHA256:
  `9c0e5b9615f8dac2a902f709927ff3fccaa4e074b34adbd0f8cd7498db78ba13`

## Live Gate

Authorized live command shape:

```bash
odin4 --reboot \
  -a workspace/private/outputs/s22plus_fyg8_disabled_vbmeta/AP.tar.md5
```

Expected validation after boot:

1. Android ADB returns `device`.
2. `sys.boot_completed=1`.
3. Build remains `S906NKSS7FYG8`.
4. `ro.boot.verifiedbootstate` / `ro.boot.veritymode` are recorded.
5. If recovery validation is run, `adb reboot recovery` reaches TWRP and the
   vbmeta prefix readback matches the patched raw vbmeta SHA above.
6. Reboot back to Android once after any recovery validation.

Failure action:

```bash
odin4 --reboot \
  -a workspace/private/outputs/s22plus_stock_vbmeta_rollback/AP.tar.md5
```

Then stop after Android boot validation. No repeated experimental flashes.
