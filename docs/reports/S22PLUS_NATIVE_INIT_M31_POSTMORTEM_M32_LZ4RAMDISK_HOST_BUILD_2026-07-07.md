# S22+ Native-Init M3.1 Postmortem And M3.2 LZ4-Ramdisk Host Build - 2026-07-07

## Scope

Host-only postmortem after the M3.1 marker-only live result, followed by a
host-only M3.2 candidate build. No flash, reboot, Odin live transfer, partition
write, module load/unload, Android sysfs/configfs change, or recovery action was
performed in this unit.

## Postmortem Input

M3.1 live result:

```text
docs/reports/S22PLUS_NATIVE_INIT_M31_LIVE_RESULT_2026-07-07.md
```

M3.1 result classification:

- boot-only candidate flash succeeded;
- Magisk boot-only rollback succeeded;
- Android/Magisk returned cleanly;
- no ADB appeared during the candidate window;
- post-rollback `/sys/fs/pstore` was empty;
- `S22_NATIVE_INIT_MARKER_ONLY_M31` was not found;
- download mode returned around 31 seconds after observation began, not as a
  clean proof of the intended 10-second marker path.

## Host-Side Finding

The strongest host-visible packaging delta is the boot ramdisk compression
format.

Stock and earlier chainload-family images use legacy LZ4 ramdisks:

```text
stock boot ramdisk:        LZ4 compressed data, magic 02214c18
chainload_v0_2 ramdisk:   LZ4 compressed data, magic 02214c18
magisk_chainload ramdisk: LZ4 compressed data, magic 02214c18
```

The failed direct-PID1 family used uncompressed `newc` ramdisks:

```text
direct_p3 ramdisk: ASCII cpio archive
observable_m3 ramdisk: ASCII cpio archive
marker_m31 ramdisk: ASCII cpio archive
```

Unpacking M3.1 confirms the boot image carried an uncompressed ramdisk:

```text
boot image header version: 4
kernel_size: 41490944
ramdisk size: 3741696
command line args:
boot.img signature size: 0
ramdisk: ASCII cpio archive
```

This does not prove that uncompressed `newc` is rejected by the S22+ kernel or
boot chain. Linux can support uncompressed initramfs. It does prove that every
failed direct-PID1 candidate diverged from the stock/chainload ramdisk format,
while at least one earlier chainload-family candidate reached Android with a
legacy-LZ4 ramdisk. Before another direct native-init live attempt, this
packaging variable should be removed.

## M3.2 Design

M3.2 keeps M3.1's marker-only behavior and changes only the ramdisk packaging:

- direct `/init` static AArch64 binary;
- create `/dev/kmsg` and fallback `/dev/pmsg0`;
- write `S22_NATIVE_INIT_MARKER_ONLY_M32`;
- no USB modules;
- no configfs;
- no display;
- no Android/Magisk handoff;
- no persistent partition mount;
- 10-second dwell, then `download` reboot attempt;
- ramdisk passed to `mkbootimg` as stock-style legacy LZ4.

Added public files:

```text
workspace/public/src/native-init/s22plus_init_marker_m32.c
workspace/public/src/scripts/revalidation/build_s22plus_marker_m32_boot.py
```

## Built Candidate

Generated private AP package:

```text
workspace/private/outputs/s22plus_native_init/marker_m32_lz4ramdisk_v0_1/odin4/AP.tar.md5
```

Hashes:

```text
source=41b693c0d4d0f2d5db55f5fe00e0b252e5055feea06874c1c760eb944acf16b5
stock_kernel=027d4ab6f39d4544f87d33b219bb7877ab9b662b40434bfb96464c1193aeb69d
marker_init=4502815c6e92e14863bccbc0eeab9cd66879dee64a38db96fe547c9e871c0b19
ramdisk_cpio=7cdbe0532f5cc167b78dc23f9ae6e2602e828b155ba403ac58470beeda8a48fd
ramdisk_lz4=59fed4ae209a394e8f9bc9decf75aef2e3f7a6f9bd2feb0d1aae2a61fe589ad0
boot_img=0bb1ef280e42aa2c6069538e77fc21b5330cf9419a19785f79d05da8429bf1fc
boot_img_lz4=604af0547b9b11cedaa4eab35ed2edf60c9297a6062349570d673259f3a366ad
ap_tar_md5=6073e4988a98f741fa207df4efb8a05e144ad16b3a90f43db2ec408657936fc2
```

Sizes:

```text
marker_init=597920
ramdisk_cpio=3741696
ramdisk_lz4=1972893
boot_unpadded=43470848
boot_img=100663296
boot_img_lz4=100663699
ap_tar_md5=100669481
```

## Validation

Commands:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/build_s22plus_marker_m32_boot.py

aarch64-linux-gnu-gcc -static -Os -Wall -Wextra -Werror \
  -o /tmp/s22plus_init_marker_m32_test \
  workspace/public/src/native-init/s22plus_init_marker_m32.c

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/build_s22plus_marker_m32_boot.py --force
```

Results:

```text
py_compile: pass
AArch64 static compile: pass
legacy-LZ4 ramdisk compression: pass
legacy-LZ4 ramdisk decompression roundtrip: pass
AP tar members: ['boot.img.lz4']
Odin invalid-device parse gate: reached intentionally invalid transport path
```

Unpacked M3.2 boot image:

```text
boot image header version: 4
kernel_size: 41490944
ramdisk size: 1972893
command line args:
boot.img signature size: 0
ramdisk: LZ4 compressed data
ramdisk magic: 02214c18
```

Required strings present:

```text
S22_NATIVE_INIT_MARKER_ONLY_M32
ramdisk_format=legacy-lz4
fallback_pmsg_major=507
no_usb_modules=1
no_configfs=1
download_reboot_after_sec=10
```

Negative checks:

```text
S22_NATIVE_INIT_MARKER_ONLY_M31: absent
S22_NATIVE_INIT_OBSERVABLE_M3: absent
ncm.0: absent
finit_rc: absent
lib/modules: absent from M3.2 init strings
```

## Boundary

M3.2 is built and statically validated only. It is not live-authorized. Before
any live use, add a fresh SHA-pinned `AGENTS.md` boot-only exception and a
guarded dry-run/live helper for this exact AP and boot image hash.

The next live question, if the operator chooses to run it later, is narrow:

```text
Does direct /init reach the earliest M32 marker when the ramdisk format matches stock legacy LZ4?
```

