# V3415 S22+ O3F Freestanding ACM Host Build

## Verdict

`HOST BUILD PASS`. O3F is a reproducible boot-only artifact that tests the
bounded startup discriminator left by the O3 live miss. It preserves the O3
module, bind, gadget, and protocol contract while replacing static glibc PID1
plus an exec'd daemon with one freestanding raw-syscall PID1.

No device command, reboot, flash, module insertion, sysfs/configfs write, or
partition write occurred in this unit. The manifest remains
`live_flash_authorized=false`; no active O3F exception exists.

## Bounded Delta

O3F keeps:

1. The exact pinned 59-module O2 hard+soft dependency plan.
2. Fail-stop `finit_module` handling and EOF `/proc/modules` verification.
3. Eight ordered functional bind gates.
4. One generic `acm.usb0` configuration.
5. Only `a600000.ssusb/mode=peripheral` as a runtime sysfs write.
6. Only `a600000.dwc3` as UDC bind target, with exact readback.
7. O0-compatible CRC frames, 128 echoes, sequence continuity, host reopen, and
   `O3 STATUS` in the same PID1 process.

O3F removes static glibc CRT startup, the separate 597,840-byte control daemon,
and PID1 `execve`. The old O3 init was 598,160 bytes; the complete O3F init is
65,984 bytes. This is a discriminator, not proof that glibc caused the O3 miss.

Review also fixed close/reopen semantics before pinning. A ttyGS0
`read()==0` is treated as host EOF: the device fd is closed, receive state is
cleared, and the endpoint is reopened. `EAGAIN` remains a nonblocking idle.

## Static Safety Contract

The final init is stripped static AArch64 with raw `_start`, no `PT_INTERP`, no
dynamic section, no undefined symbol, and no reboot or execve syscall path. It
contains no Android/Magisk handoff, Samsung `ss_acm`, FunctionFS, MTP/ADB, NCM,
max77705/charger/altmode manipulation, EUD enable, sysrq/sec_debug trigger,
persistent mount, block write, or PMIC/Type-C power write.

The builder pins FYG8 module metadata and the known-booting Magisk boot. A
no-change MagiskBoot unpack/repack is byte-identical. The patched boot changes
only ramdisk `/init`, preserves the kernel, injects no module binary, adds no
ramdisk entry, and packages exactly one Odin member: `boot.img.lz4`.

## Exact Artifact

Output:

```text
workspace/private/outputs/s22plus_native_init/o3f_freestanding_acm_v0_1
```

```text
source_sha256=2018eacff28dd6e897e9d6f4d6eabd712b74f076ecdbb6192f03c59455ccfa38
protocol_header_sha256=3a53ebb9788b0ff23982ca2ed2bfc19cd27c5504f650660877868b588651403a
loader_header_sha256=c4f5dd0f1bac4e4d614ae683b1bab7f1908dd337f5c0e244cab424c4cea556e8
plan_tsv_sha256=a34ebbad3b5d770f133e37a450cc3007e4a84ab831788484680e88aad6b3d534
plan_header_sha256=45727cff30952096d9604682a3ba3d284807a75e6622ed4c8ae57bc153d5b863
o3f_init_sha256=d181cee7818cdf0566a8f618d1f861b0bdabb36501ca95e87ad3681a370d2a16
ramdisk_after_sha256=db95044ab34ce088befb51ba934400059071c73be534be89249e64853d1052cd
kernel_sha256=bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff
boot_img_sha256=c09ef0e8cbcb3b53c8ba22d76fce47cc03607ad416b0b8f2faf2adf1f18e9f70
boot_img_lz4_sha256=b25fff7af1d07fd0fd7799aac4ad1c8076f4fed7b7d8c64974cba5a2f5ecc922
ap_tar_sha256=067c658a3651239ba7b645ffb9fcfc674200e917bcacf9b1babfa7ceffda6c2c
ap_tar_md5_sha256=73d0a03c066b236e8ebea07c03affda4c5b94633cc34dd2ca413ce8697eb8725
tar_members=boot.img.lz4
```

## Reproducibility And Tests

An independent build under `/tmp/s22plus_o3f_repro2` reproduced all 17 pinned
source, protocol, loader, plan, init, ramdisk, kernel, header, boot, LZ4, tar,
and AP hashes exactly.

The host protocol core passed empty, normal, and maximum payload roundtrips and
rejected CRC, type, length, short-frame, and response-capacity errors. The
focused O3F/O2 suite passed 22 tests. The O0, O1, O1.1, O2, old O3, old O3
gate, and O3F regression set passed 62 tests.

## Next Gate

Create a separate checked O3F live helper that pins the hashes above, exact
serial `S22O3FACM01`, the 128-frame/reopen/status proof, continuous USB
observers, current rooted Android boot SHA, and both Magisk and stock boot-only
rollback APs. Run artifact-only offline validation and connected read-only
preflight. Only then add a fresh one-shot exact `AGENTS.md` exception and use
the operator's live approval for one attended boot-only flash followed by
mandatory manual-Download Magisk rollback.
