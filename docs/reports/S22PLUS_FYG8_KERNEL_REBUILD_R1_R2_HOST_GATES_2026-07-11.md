# S22+ FYG8 Kernel Rebuild R1/R2 Host Gates

Date: 2026-07-11 KST
Target: `SM-S906N/g0q/S906NKSS7FYG8`
Scope: host-only source provenance, complete module-corpus, and static ABI gates

## Verdict

**R1 Full-LTO buildability and R2 static stock-equivalence PASS on the
controlled Debian 13 FX-8300 32 GiB host.**

> **Superseded correction, 2026-07-12:** R1 Full-LTO buildability remains
> proved, but reproducible R1 and strict R2 are reopened. The generated banner
> timestamp is `Sun Jul 12 07:16:46 UTC 2026`; exact FYG8 stock is
> `Fri Aug 1 05:55:56 UTC 2025`. R2 v1 did not compare the full banner. See
> `S22PLUS_FYG8_R1_R2_TIMESTAMP_GATE_POSTMORTEM_2026-07-12.md`. The original
> verdict below is retained as a historical account, not a current R3 gate.

No boot image was packaged, no device was contacted, and no flash or partition
write occurred.

## R1 Preflight v2

`s22plus_fyg8_kernel_build.py` now performs the source audit inside each
preflight instead of trusting a prior manifest. The live host run rehashed the
pinned FYD9 base plus FYG8 delta and matched all 166,037 resident members with
zero missing or mismatched files.

The wrapper now:

- starts from a minimal host environment allowlist and a pinned PATH;
- rejects ambient compiler flags and shell hooks;
- verifies all four exact tool repositories and Clang `r416183b` identity;
- requires Image, Image.lz4, vmlinux, System.map, vmlinux.symvers,
  modules.builtin, modules.builtin.modinfo, and `.config`;
- fails a zero-return build when no generated `.ko` exists;
- hashes every generated module and symvers file into the result.

All source, toolchain, isolation, disk, and host-tool gates pass. The original
15.2 GiB host still fails closed on physical RAM; the transferred Debian 13
host exposes 33,662,164,992 bytes and passes the 30 GiB Full-LTO floor.

## R1/R2 Remote Close

The first clean Full-LTO compile produced all eight owned kernel outputs in
33:15 wall time with peak RSS 24,252,992 KiB and zero swap. That invocation
failed only after compilation in host-side dist handling. The fixes were
bounded and source-neutral: correct Samsung release suffix composition, GNU
`tar`/`xargs` selection, kernel-only output routing, and exact removal of two
generated read-only dist copies before an incremental retry.

The final R1 invocation returned zero in 3:31 while reusing that preserved
output tree. All eight core output hashes are identical between the clean
compile attempt and final PASS. The final result owns 2,397 generated `.ko`
paths, 15 symvers files, and an explicit provider closure for dataipa and
datarmnet SHS, which Samsung's six-entry `KBUILD_EXT_MODULES` list omits even
though the shipped complete corpus consumes their exports.

| Evidence | Result |
|---|---|
| R1 result SHA256 | `027d0104ea0640b4d7faca1607dcaae4d0b1bb6af403725c9bd85e524f54b18f` |
| Required R1 outputs | 8/8 |
| Provider closure | dataipa + datarmnet SHS PASS |
| Generated symvers files | 15 |
| R2 result SHA256 | `66c76073881752752c8a0eeddee03e8d6f8d63dc84109441616eda7386dea4cf` |
| Consumer CRC rows | 25,864 |
| Provider symbols | 10,511 |
| Missing / mismatched / conflicting CRCs | 0 / 0 / 0 |
| Image release/compiler | exact FYG8 match |
| Config delta | one allowlisted absolute whitelist path only |
| Boot-layout capacity | PASS |

The remote evidence is mirrored privately under
`workspace/private/outputs/s22plus_fyg8_kernel_rebuild_r0/remote-fx8300-r1`
and `remote-fx8300-r2`.

## Exact Super Layout

The stock AP's `super.img.lz4` expands to an Android sparse image of
10,352,130,812 bytes, SHA256
`f418abff8cf0612d7c145d6f6de0ac6a13bbdd8b5a6458b5ae8c18f2bf8243c8`.
The raw logical image is 12,475,957,248 bytes, SHA256
`63061c093dce2e1f0a3df41bf0a960b72f221ecca8277c9f2fcc20a3e8e8f4ae`.

Primary geometry, metadata-header, and table SHA256 checksums all pass. The
partition set is exactly:

```text
system odm product system_ext vendor vendor_dlkm
```

There is no `system_dlkm` or `odm_dlkm` logical partition. Recursive read-only
F2FS walks found zero `.ko` files in `system`, `vendor`, and `odm`.

The parser follows the official Android `liblp` metadata format and the
official `lpunpack` extent model:

- https://android.googlesource.com/platform/system/core/+/master/fs_mgr/liblp/include/liblp/metadata_format.h
- https://android.googlesource.com/platform/system/extras/+/master/partition_tools/lpunpack.cc

## Complete Module Corpus

The exact `vendor_dlkm` partition is 57,610,240 bytes, SHA256
`e5386d68ccf9ad1a12cfa4cf447e704bddcef94b0442e61765f3dba580186b26`.
Its F2FS `/lib/modules` contains 356 modules and five depmod metadata files.

The host reader reconstructs compressed F2FS clusters directly. It parses the
inode/direct-node address maps, validates the LZ4 compressed length, expands
each cluster with `LZ4_decompress_safe`, truncates to the inode size, then runs
modinfo and modversion inspection on the recovered ELF.

Directory/inode metadata came from `dump.f2fs 1.16.0`; the locally extracted
multicall binary SHA256 is
`66db38ca0ea8239cab0c335e142ee34751824352eaa494b3654fa7d663b86669`.
Compressed file content is reconstructed by the project reader rather than
trusted to `dump.f2fs`, because that tool's inode dump does not expand these
compressed clusters.

Corpus result:

| Measure | Count |
|---|---:|
| Vendor-ramdisk modules | 441 |
| vendor_dlkm modules | 356 |
| Names present in both | 306 |
| Overlap byte-identical | 306 |
| vendor_dlkm-only | 50 |
| Vendor-ramdisk-only | 135 |
| Complete unique union | 491 |

There are zero overlapping content mismatches. The complete consumer contract
contains 25,864 module/symbol CRC rows over 4,619 unique symbols.

## ThinLTO Diagnostic

The old diagnostic is deliberately non-R1: its release is only
`5.10.226-android12-9`, it uses ThinLTO, and vendor module modpost did not
finish. The new R2 auditor nevertheless gives useful bounded evidence:

| Measure | Result |
|---|---:|
| Consumer CRC rows | 25,864 |
| Rows satisfied by GKI symvers | 22,600 |
| Missing module-provider rows | 3,264 |
| Unique missing symbols | 1,743 |
| CRC mismatches | 0 |
| Generated Image fits stock boot layout | yes |

The missing rows do not prove a KMI break. They are unresolved until the Full
LTO vendor build returns its provider symvers. The zero mismatch among all
present providers is positive diagnostic evidence only.

## Remaining Gate

The 2026-07-12 correction reopens reproducible R1 and strict R2. Run R1 v3 and
R2 v2 with exact stock-banner equality before considering R3. R3 packaging or
device work also remains unauthorized until a fresh boot-only policy exception
is added with exact artifact pins and explicit operator approval.
