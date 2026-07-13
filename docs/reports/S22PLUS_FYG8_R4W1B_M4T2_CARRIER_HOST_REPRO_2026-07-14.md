# S22+ FYG8 R4W1-B M4T2 Carrier Host Reproduction

Date: 2026-07-14 KST

Target: `SM-S906N/g0q/S906NKSS7FYG8`

Scope: host-only reproduction of the historical M4T2 carrier. No device was
contacted, enumerated, rebooted, or flashed. The generated files remained under
`/tmp/s22plus_r4w1b_probe_20260713` and are not candidate promotion artifacts.

## Command

The existing checked builder was rerun with its normal pinned inputs and a
temporary output directory:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/build_s22plus_inplace_m4t2_park.py \
  --out /tmp/s22plus_r4w1b_probe_20260713/m4t2-rebuild
```

The raw `/init` was also independently rebuilt and disassembled with the same
GCC/binutils path used by the builder. Its complete entrypoint decoded to:

```text
4000b0: d503205f  wfe
4000b4: 17ffffff  b 4000b0
```

## Pinned Inputs And Tools

```text
M4T2 builder
  f44f3f606011994c8adaea11ddc133ea98beb7f4b3d349d83b407b1ae4d1bb68
direct-P3 packaging helper
  f747f1c12a7bba8712e1468a0600ab5e4bf913ce9cbfda3a9d80fa7a0657b0d6
M4T1 MagiskBoot helper
  13f37b8686bf361c0e4400a92473755c0093ba74ef66a80843c36877ece0638f
M4T2 source
  d5ec47527dae3d94e88ca8555e7efd96048de3ea87a3a136b50ad5a8be301551
known Magisk base boot
  2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
MagiskBoot
  a18ecbd7981179494b7d281453d6c4e25b5c719e7d2ef7f6eba3c6be3043c58e
Python 3.14.4
  b8d8288faefdd300201f43fcf00f6f539a27218eeed3a3dff5ab10b9c4c99700
aarch64-linux-gnu-gcc 15.2.0
  50d0961827e521a7c06d7794d4b15282559a117d365a149aaca5726917ab1603
aarch64-linux-gnu-strip 2.46
  9c0b60a5e8a918a7ad2f212c9b36a74b7f0604e8cbe94b0b4f4f731b32df1308
aarch64-linux-gnu-readelf 2.46
  b4bb1bf2d6b2d3a309a281a920f0203d68e512e610a4f075cf0ed23e8976b795
GNU tar 1.35
  c2a35025aa251cea611d6d8c160c87c12b3cd394421edfb3a773b44235f69554
Odin4
  6754aa54f2abe6e99ece32414cd34c8b23b28dbddde537a33203036813637c3b
```

LZ4 packaging does not depend on a host `lz4` executable. The pinned direct-P3
helper emits and decodes a deterministic stored-block LZ4 frame in Python.

## Reproduced Outputs

The builder generated manifest timestamp was `2026-07-13T14:58:30Z`.

```text
raw /init size             544
raw /init SHA256           b8371e3ac671ff71e9be752b8ff1087a4f20811c871a43ca8e698eee47783d12
raw boot size              100663296
raw boot SHA256            8103bce76fb3e41d71b64735a64d2f2f29431a44ea1c9a85dc0bc151d71afd15
boot.img.lz4 SHA256        8db75e0cce8a8bea69c05e7747f4690fed19e51ddbc0f81dc06e1f4621be6265
AP tar SHA256              c07bd72a5f84af41ca7fa5006120d357f25a0a51a9eefa806b7030a79e69086f
AP.tar.md5 SHA256          66d7f24b348702f58efbe1945b0d2751052ed27f6ce1f6fc4e5da63f3a585b24
AP members                 [boot.img.lz4]
no-change base repack      byte-identical
```

The raw boot and AP.tar.md5 hashes exactly match the historical M4T2 live pins.
The builder plus the independent disassembly verified a static AArch64 ELF,
absent `PT_INTERP`, mode `0750`, no syscall instruction in the two-instruction
entrypoint, exact single-member AP packaging, and host-only/no-live safety
metadata.

## Interpretation

This closes the durability gap in the carrier-selection claim: the current host
can reproduce the exact historical M4T2 raw boot and AP with pinned tools. It
does not promote a new kernel, R4W1-B boot image, helper, policy exception, or
live action. The future R4W1-B builder must still independently reproduce the
carrier, audit generic plus stock-vendor ramdisk ownership of `/init`, and pass
the complete design contract before candidate construction is considered.

Verdict:

`PASS_R4W1B_M4T2_CARRIER_HOST_REPRO; NO_LIVE_AUTHORIZATION`
