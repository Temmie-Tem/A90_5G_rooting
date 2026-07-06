# S22+ Native-Init P1 Magisk Chainload Host Build

Date: 2026-07-07 KST

Device target:
- Samsung Galaxy S22+ `SM-S906N` / `g0q`
- Build: `S906NKSS7FYG8`

Scope:
- Host-only P1 candidate construction for the S22+ native-init PID1 epic.
- No S22+ reboot, Odin transfer, partition write, module load/unload, or live
  boot validation was performed.
- This stops at the P2 flash boundary. A new SHA-pinned S22+ boot-only
  `AGENTS.md` exception is required before flashing this candidate.

## Why This Candidate Replaces The Earlier Chainload Direction

The previous S22+ chainload attempts wrapped the stock Android `/init`. They
booted Android in some cases, but did not produce a readable native-init proof
marker.

The P0 recon and final root checkpoint changed the right base image:

- current live `boot` is Magisk-patched, not stock:
  `2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e`
- stock `boot` is:
  `4150b962314e6136acba61b20f471d6ee1c418b83cf8c3ee4d9cf7c91a3640ae`
- rooted Android can read proof channels such as `dmesg` after boot.

Unpacking the current Magisk boot showed:

```text
Magisk ramdisk:
  /init                       199960 bytes, Magisk init
  /overlay.d/sbin/init-ld.xz
  /overlay.d/sbin/magisk.xz
  /overlay.d/sbin/stub.xz

Stock ramdisk:
  /init                       3140920 bytes, stock Android init
```

Magisk also modified the kernel by 9 bytes and added the `proca_magisk` string:

```text
Magisk kernel sha256:
bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff

Stock kernel sha256:
027d4ab6f39d4544f87d33b219bb7877ab9b662b40434bfb96464c1193aeb69d
```

Therefore the next first-light proof should preserve the Magisk-patched kernel
and Magisk ramdisk path, not return to stock boot.

## Wrapper Source

New source:

```text
workspace/public/src/native-init/s22plus_init_magisk_chainload.c
```

Behavior:

1. Runs as `/init` from the Magisk-patched boot ramdisk.
2. Emits kmsg proof marker:

```text
S22_NATIVE_INIT_MAGISK_CHAINLOAD version=0.1 restore=/init.magisk->/init action=exec proof=kmsg-rooted-android-dmesg
```

3. Writes non-persistent initramfs marker files:

```text
/s22_native_init_magisk_chainload_ran
/debug_ramdisk/s22_native_init_magisk_chainload_ran
```

4. Restores the initramfs path layout so Magisk still sees itself at `/init`:

```text
/init -> /init.s22-wrapper
/init.magisk -> /init
execve("/init", argv, envp)
```

5. Falls back to `execve("/init.magisk", ...)` if path restoration fails, then
   parks only if both exec paths fail.

The path-restore step is deliberate: Magiskinit contains strings that reference
`/init` and can inspect or patch that path. Leaving the wrapper at `/init` while
execing `/init.magisk` would be a weaker compatibility model.

## Host Build

Private output:

```text
workspace/private/outputs/s22plus_native_init/magisk_chainload_v0_1
```

Build/packaging steps:

```text
aarch64-linux-gnu-gcc -static -Os -Wall -Wextra -Werror
aarch64-linux-gnu-strip
cp Magisk ramdisk root
mv init init.magisk
cp wrapper init
cpio newc --owner=0:0
lz4 legacy ramdisk compression
mkbootimg header_version=4 os_version=12.0.0 os_patch_level=2025-08
pad boot image to 100663296 bytes
lz4 --content-size -B6 boot.img for Odin4
tar AP with exactly boot.img.lz4
append md5sum-style AP.tar.md5 trailer
```

## Candidate Hashes

```text
wrapper:
8610c616204b881a0e304bcd1b3b5b97b103ed98669d9891cca8120cbff96078

preserved Magisk init as init.magisk:
383670a7ba3a6a4b79e5f3467e1da4b66a5df66a9b356ab9f70916854dd6b468

ramdisk_magisk_chainload.lz4:
3b0f2ca5d97cd833d6acdcc813e2bf307b3f14cb488a7b49d56444f2282049fc

padded boot.img:
da9e2f5f71a396f40824493dd8acb9f7404623df075c21fb47f5ecee6f4c2645

odin4 boot.img.lz4:
a208f8049646ee960008298e863c057d32b9e428668e77b1b3b4562b80874b4c

odin4 AP.tar:
d28252c0b914f588286a8fc26bb913ec70bd3ce0babce4d4d151090dfcdaad4b

odin4 AP.tar.md5:
4790b8a82e38081ed20e50d9bbbeee29f3821cfbf7b52e2d51da8f17f028ee40
```

## Static Validation

Wrapper binary:

```text
ELF 64-bit LSB executable, ARM aarch64, statically linked, stripped
```

Candidate boot unpack:

```text
boot magic: ANDROID!
kernel_size: 41490944
ramdisk size: 674772
os version: 12.0.0
os patch level: 2025-08
boot image header version: 4
command line args:
boot.img signature size: 0
```

Verified candidate ramdisk contents:

```text
/init           wrapper sha256 8610c616204b881a0e304bcd1b3b5b97b103ed98669d9891cca8120cbff96078
/init.magisk    Magisk init sha256 383670a7ba3a6a4b79e5f3467e1da4b66a5df66a9b356ab9f70916854dd6b468
/overlay.d/sbin/init-ld.xz
/overlay.d/sbin/magisk.xz
/overlay.d/sbin/stub.xz
```

Verified kernel preservation:

```text
candidate kernel sha256:
bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff

Magisk source kernel sha256:
bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff
```

Verified Odin payload:

```text
AP.tar contents:
boot.img.lz4

boot.img.lz4 roundtrip sha256:
da9e2f5f71a396f40824493dd8acb9f7404623df075c21fb47f5ecee6f4c2645
```

Odin4 invalid-device parse gate:

```text
Check file : workspace/private/outputs/s22plus_native_init/magisk_chainload_v0_1/odin4/AP.tar.md5
/dev/bus/usb/999/999
No such file or directory
usb device Fail
```

Interpretation: Odin4 parsed the package and reached the intentionally invalid
transport path. This is a package-shape proof, not a flash proof.

## P2 Flash Boundary

Do not flash this candidate until `AGENTS.md` has a new S22+ boot-only exception
pinning at least:

```text
target: SM-S906N / g0q / S906NKSS7FYG8
candidate AP.tar.md5 sha256:
4790b8a82e38081ed20e50d9bbbeee29f3821cfbf7b52e2d51da8f17f028ee40

candidate padded boot.img sha256:
da9e2f5f71a396f40824493dd8acb9f7404623df075c21fb47f5ecee6f4c2645

stock boot-only rollback AP sha256:
1ee92a86f30e4acb12509272630e1bef5215d1a12686ac69a3b399b43740535e

full stock FYG8 firmware sha256:
f831e5fb8abe1c7a9d8c38fe9c033a3fce7e77651776383641c385c2bb85a2c8
```

The live validation command after boot should search rooted Android `dmesg` for:

```text
S22_NATIVE_INIT_MAGISK_CHAINLOAD
```

Expected pass condition for first-light:

```text
Android returns or TWRP/download recovery remains reachable.
Magisk root still works if Android returns.
Rooted dmesg contains S22_NATIVE_INIT_MAGISK_CHAINLOAD.
boot readback prefix matches the candidate boot image if checked.
```

## Result

PASS: P1 host-only Magisk-preserving first-light candidate is built and
statically validated.

Not complete: S22+ native-init first-light is not live-proven. The next action is
operator-authorized P2 boot-only flash after adding the SHA-pinned `AGENTS.md`
exception above.
