# S22+ Ramoops Vendor-Boot Enable Host Build (2026-07-08)

## Verdict

HOST-ONLY BUILD PASS, LIVE NOT AUTHORIZED.

Codex built a `vendor_boot`-only private AP that directly patches the stock
FYG8 vendor_boot DTB so every `/reserved-memory/ramoops_region` node has:

```text
status = "okay"
```

No flash, reboot, Odin live action, or device write was run in this unit.

## Why This Differs From The Prior DTBO Attempt

The prior DTBO path patched a Samsung overlay. The new steer asked for direct
vendor_boot DTB patching. Current local evidence shows the exact direct shape:

- stock vendor_boot DTB contains 4 concatenated FDT blobs;
- every blob already contains `/reserved-memory/ramoops_region`;
- none of those nodes has a `status` property;
- therefore the direct vendor_boot patch is **not** `disabled -> okay`;
- it is `add status = "okay"` to the existing node in each of the 4 blobs.

## Builder

Source:

`workspace/public/src/scripts/revalidation/build_s22plus_ramoops_vendor_boot_enable.py`

Private output:

`workspace/private/outputs/s22plus_ramoops_vendor_boot_enable_v0_1`

The builder:

- verifies the stock FYG8 `vendor_boot.img` SHA256 before patching;
- unpacks vendor_boot with `magiskboot unpack -n -h`;
- patches only the DTB structure blocks in memory;
- repacks with `magiskboot repack -n`;
- builds a candidate Odin AP with one member, `vendor_boot.img.lz4`;
- builds a stock vendor_boot rollback AP with one member,
  `vendor_boot.img.lz4`;
- runs the Odin invalid-device parse gate for both APs.

## Hashes

```text
stock_vendor_boot       096e433e049fb088cd956e083d5a1039b33cdf0ca907e713bba7feaaf1b080b7
source_dtb              2cd64d43a4f6b89a7c5523f3ef73fbb84dcad92c6d857e649cd1f0baa7c0080e
patched_dtb             b862359dc65adb1eb9f5f17f1b8be637eb0135e88a681d779f9cbeda3ae5a3ec
nochange_repack         f8a798ebdb940935fbc73c652e8283bb919ff1dc3798f1d10f7b459e192c7921
patched_vendor_boot     7110a7f910e55e48ddb944275ce44a5b8dfe19ca5940743b88066c3288fb8163
candidate AP.tar.md5    f7c4c245f2fe92435a743bf718a31f0508b0fd13f173f3288627c5ce436c1de1
rollback AP.tar.md5     2f9075fe609e7aa66c2ec88a2bd0223d6a9d7ff23d8bab0f7c4eb44633f480bb
```

AP members:

```text
candidate: vendor_boot.img.lz4
rollback:  vendor_boot.img.lz4
```

## Patch Evidence

The DTB patch applies one FDT property insertion per vendor DTB blob:

```text
blob_count=4
insert_len=20 per blob
dtb_size_delta=80
status_after:
  blob 0: okay
  blob 1: okay
  blob 2: okay
  blob 3: okay
```

Independent extraction from the patched vendor_boot image re-read the DTB and
confirmed:

```text
blob 0: status = "okay"
blob 1: status = "okay"
blob 2: status = "okay"
blob 3: status = "okay"
```

## Important Risk Note

`magiskboot repack -n` for vendor_boot is **not byte-identical** even with no
DTB changes:

```text
nochange_repack_byte_identical=false
nochange_repack_changed_byte_count=3458
```

This is likely AVB/footer/signature/header-tail churn from the repacker, but it
is still a live-gate risk. A future live unit must explicitly accept this
repack drift or replace the repack path with a stronger byte-preserving
vendor_boot packer. Do not treat the candidate as "only 80 bytes changed in the
partition image"; the direct DTB payload change is 80 bytes, but the final
vendor_boot image also includes repacker drift.

## Safety State

The manifest records:

```text
host_only=true
touches_connected_device=false
live_flash_authorized=false
partition_scope_if_later_authorized=vendor_boot only
requires_new_sha_pinned_vendor_boot_exception_before_flash=true
current_agents_does_not_authorize_this_live_flash=true
rollback_ap_built=true
stock_vendor_boot_available=true
nochange_repack_byte_identical=false
```

## Validation

Commands:

```bash
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/build_s22plus_ramoops_vendor_boot_enable.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/build_s22plus_ramoops_vendor_boot_enable.py \
  --force
```

Additional extraction check:

```bash
workspace/private/tools/magisk-v30.7/magiskboot unpack -n -h \
  workspace/private/outputs/s22plus_ramoops_vendor_boot_enable_v0_1/build/vendor_boot.ramoops_status_okay.img
```

Result:

- `py_compile`: pass.
- Host build: pass.
- Candidate and rollback APs have exactly one `vendor_boot.img.lz4` member.
- Patched vendor_boot extraction confirms all 4 ramoops nodes have
  `status = "okay"`.
- Odin invalid-device parse gate parsed both APs and failed only on the
  intentionally nonexistent USB path.

## Next

Do not live flash this candidate yet. The next unit should be a live-gate design
review/preflight that decides whether the `magiskboot repack -n` drift is
acceptable or whether a byte-preserving vendor_boot packer is required first.

If live is later authorized, it must be a new SHA-pinned vendor_boot-only
exception with:

- candidate AP SHA256
  `f7c4c245f2fe92435a743bf718a31f0508b0fd13f173f3288627c5ce436c1de1`;
- stock vendor_boot rollback AP SHA256
  `2f9075fe609e7aa66c2ec88a2bd0223d6a9d7ff23d8bab0f7c4eb44633f480bb`;
- attended ack;
- positive control first on the known parking M13 boot candidate;
- stock vendor_boot restore when done.
