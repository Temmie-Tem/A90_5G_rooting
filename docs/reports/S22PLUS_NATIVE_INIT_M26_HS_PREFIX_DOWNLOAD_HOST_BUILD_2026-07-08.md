# S22+ Native-Init M26 HS Prefix-Download Host Build (2026-07-08)

## Verdict

PASS: host-only M26 prefix/download discriminator matrix built and statically
validated. No flash, reboot, rollback, partition write, sysfs write, or device
action was performed.

M26 takes the M25 HS-only USB2 module closure and changes the proof shape from
ACM park to checkpoint/download. Each generated candidate loads the first `N`
modules from the M25 list, then deliberately requests Download mode. A future
live hit means the selected prefix reached the checkpoint; a no-download loop
means reset occurred before that checkpoint or the reboot path failed.

## Public Source

- Builder:
  `workspace/public/src/scripts/revalidation/build_s22plus_m26_hs_prefix_download.py`
- Runtime source:
  `workspace/public/src/native-init/s22plus_init_m26_hs_prefix_download.c`
- Tests:
  `tests/test_s22plus_m26_hs_prefix_download_build.py`

## Private Output

- Output directory:
  `workspace/private/outputs/s22plus_native_init/m26_hs_prefix_download_v0_1`
- Matrix manifest:
  `workspace/private/outputs/s22plus_native_init/m26_hs_prefix_download_v0_1/manifest.json`

Every generated Odin AP contains exactly one tar member:

```text
boot.img.lz4
```

## M25 Input Context

The builder verifies the M25 manifest and private output before generating M26:

- M25 module list SHA256:
  `00607484b7b777ee5cb54d7657f0cb554b9b66c42fec0e414d0544c0735d6496`
- module count: `40`
- QMP excluded: `phy-msm-ssusb-qmp.ko` is not in the subset
- DTBO high-speed candidate AP SHA256:
  `35afd774444066fd8e2ffe831da11dd73ee47dce3bdd5b1e37675f82344e56b6`
- patched raw DTBO SHA256:
  `8962cbbded722c85dbdebfbdc2eba5476b9a64e2a2933888b81f947159eddc17`
- stock DTBO rollback AP SHA256:
  `6f397421bee84f4ea0c80a8519be0f6f6af84119794970e8a1faaa05f261caaa`
- stock raw DTBO SHA256:
  `97a4864fee4e61892d733962d1ec76f8d14b52bc19e6f47440bc27d9dfc4bd0c`

Both DTBO APs were checked as `dtbo.img.lz4`-only tar payloads.

## Candidate Matrix

| Label | Prefix | AP.tar.md5 SHA256 | boot.img SHA256 | /init SHA256 | Next module |
| --- | ---: | --- | --- | --- | --- |
| P00 | 0 | `1f8763c5f08461bb351f1b461898bf568652e292c79aef9e1f46fb9af4bbd79b` | `76a0f5a40dd67db051c60af8fee367594a8580840853b34b3b3e16fe3f47b707` | `1bd912f2732a975d5ed91e442d4def661e515bed9c87d6bd313d22b898ca08fc` | `clk-rpmh.ko` |
| P24 | 24 | `7e9a3fafdbeeda8c92cfab9b4ae73d2c2b2a4821a48d537e6ba5e35b34018029` | `ff231f7fdb410a8fa3489cd63bc8d2f9f539dc823a4086f5917e75a1b24b7af8` | `7e188e760040073ee28708a17e66b4c7b096f91f4f41319083ae51bf2b98f2da` | `arm_smmu.ko` |
| P25 | 25 | `dca2ae41e2008a9b0af4ef9595d989e72b8c60ba35bfd68fbdd9115d738c7b09` | `2226877ea57ef995b54c57b4d13da908b33145760353cd52ef898e7518fd48b4` | `1bf4cb5099357993d5d085bf617ea9d829c5bc220c87e0c94986dc0644814462` | `phy-msm-snps-hs.ko` |
| P27 | 27 | `19014f494444e3fce3127ac142bc30f622feb96bd08a1f2031e2f14a0a380341` | `38e819de865d0a979446d04521373343f53d3ab8bae461cbb05b94190d2873b3` | `5289ef3bdb344fa09e8a18d0183b8d7d4ce5c98d4eb83fe0f68813d5bf444a22` | `dwc3-msm.ko` |
| P28 | 28 | `c61fbec079aa1545819654b4f2bf5e33fba8bdc31a41585320f0abbed989a601` | `544e41cc80e6fb01ab5d72a45cc1e882b933009bc1ad070110493fc3114a99ad` | `f39c1e11840a6d191176ed949fe08895022e19e1599b8f286f4979342c187a3e` | `usb_f_ss_mon_gadget.ko` |
| P30 | 30 | `a4510148c14652ffd87c8c0c6dd2ec1b127a36136ed1d28849bba04028ea8c9c` | `3f952b45b8d339112fe6c25acc94f83257c21520c370559a37ad1a80f1016990` | `fc99836944f0ac3373b45e8dc0523bc475ecd77cb5661dff77fbaf885a32aedf` | `repeater.ko` |
| P33 | 33 | `d038e4b2362d2e4c175cebd45ee02f17a987f340fd654736c9ce72deaf2b487e` | `7ad2948bab2ad9b53bb51d9ec92d6f2f49ed89d5008eac620c9556a6fb8e61eb` | `037c12757e231e299a3a866bcf51a8f83ce4324f22abc226cf9452ccd348f3de` | `switch_class.ko` |
| P40 | 40 | `68ef6dcbf40393c7926a73e1138d501fa3dc23c889ce9c748d3082bb4e6b770f` | `88ddad620966aa7d94c49e62ca4a148f766f88dc273d8049f390aa039dad59a6` | `f83dc5b81586b80bb3f3f8c5c5eccaa67f0b949d560eb9ea336986a51afecc56` | none |

## Runtime Shape

Each M26 `/init` is freestanding raw-syscall PID1 and contains:

```text
S22_NATIVE_INIT_M26_HS_PREFIX_DOWNLOAD
modules_hs_only_usb2=/s22plus_m26_hs_only_usb2.modules
module_count=40
maximum_speed_dtbo=high-speed
qmp_excluded=1
observation=prefix-download
reboot_request=download
```

The runtime intentionally does not create configfs, does not bind UDC, does not
probe `ttyGS0`, and does not attempt ACM. It only mounts minimal pseudo-fs,
loads the bounded prefix, then calls `reboot(..., "download")`.

Forbidden-string scan over all generated `/init` binaries found no:

```text
ld-linux
libc.so
/vendor_dlkm
ttyGS0
ss_acm.0
/config
```

## Validation

Commands:

```bash
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/build_s22plus_m26_hs_prefix_download.py \
  tests/test_s22plus_m26_hs_prefix_download_build.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_s22plus_m26_hs_prefix_download_build

aarch64-linux-gnu-gcc -fsyntax-only -nostdlib -static -ffreestanding \
  -fno-builtin -fno-stack-protector -Os -Wall -Wextra -Werror \
  -DM26_PREFIX_LIMIT=30 -DM26_PREFIX_LABEL='"P30"' \
  workspace/public/src/native-init/s22plus_init_m26_hs_prefix_download.c

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/build_s22plus_m26_hs_prefix_download.py --force

git diff --check
```

Results:

- Python bytecode compile passed.
- Unit tests passed: `Ran 3 tests ... OK`.
- AArch64 freestanding syntax check passed.
- Host builder generated all 8 candidates.
- AP member check passed for every candidate: `["boot.img.lz4"]`.
- Manifest safety is host-only: `live_flash_authorized=false`,
  `device_action=false`.

## Next

No live flash is authorized by this report. The next live-capable unit should
add a fresh SHA-pinned `AGENTS.md` exception and guarded live helper for a small
attended M26 batch. A conservative first live batch is P00, P24, P27, and P30
under the already proven M25 DTBO high-speed cap plus mandatory Magisk-boot and
stock-DTBO rollback gates.
