# V3429 S22+ Direct-PID1 Phase Observer Host Build Pass

## Verdict

`HOST_BUILD_PASS_NO_LIVE_AUTHORIZATION`.

V3429 implements the V3426 Stage-A phase observer as a minimal direct-PID1
candidate and packages it by replacing only the known-booting Magisk ramdisk
`/init`. The build is deterministic through the final one-member Odin AP, the
runtime ELF is static AArch64 with no exit/reboot/clone path, and the V3426-V3429
contract suite passes.

This is a host-only result. No device contact, reboot, module insertion, image
write, Odin transfer, or flash occurred. No active exception authorizes this
artifact for live use.

## Artifact Pins

- Target: `SM-S906N/g0q/S906NKSS7FYG8`
- Run ID: `f1613e72912b63f030c25a6bd7fd072e`
- Source SHA256: `311a44deecbd0d0148c7624929f173c44500cf714c4f2a8dd8b5e6acd856db59`
- Expected-marker manifest SHA256: `b05615527be5e78b4c095153b7b104522436b91d3197c127f278867baf5acd54`
- Generated header SHA256: `90d53531d12ca6a2927ded8cabdd59129289cc591ebddb6d87cec8b33ce7f102`
- Static `/init` SHA256: `4e58721e21efa42e7d4529d9aa3a0c60d0724b56cf8fc171fc85e82c4d3a17ea`
- Candidate `boot.img` SHA256: `93eef3b07bfbeb2154ecc9bfddfdeed682d83d950ca5e6032b7cfd75e4c9a428`
- `boot.img.lz4` SHA256: `3eccf17ce7b22cb8c6f29ce31e24e33513d46d878ab0076528a91df4f4b957d8`
- `AP.tar` SHA256: `068bcfe3ee9ccfb24910020f27272ce484100ed3b46fe2c0e05ad982b293cff5`
- `AP.tar.md5` SHA256: `d6b2a430b2f5d21a7bdefe5b7db050c9e627d30ef5ecdee77ee44bd764579b4f`
- AP members: exactly `boot.img.lz4`
- Base Magisk boot SHA256: `2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e`
- Preserved kernel SHA256: `bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff`
- Observer contract SHA256: `cba82ce1bae23f56bcad57876f5d647e31a37a36d7bc9b477de57b1f85b3babf`
- Transition contract SHA256: `426aa2bb50f6e73e153f5f5dc9cde59ddf37ab315f46860c1dc0bd0b3e810734`
- V3428R report SHA256: `21e233829a583b186377cb9aa0b330821e928fa41d13a7ab965cf6e06254ea3d`

Private build manifest:
`workspace/private/outputs/s22plus_native_init/v3429_phase_observer_v0_1/manifest.json`.

## Runtime Contract

The 6,088-byte freestanding PID1 performs only this bounded sequence:

1. Mount volatile `proc` and `sysfs`, and create `/dev/kmsg` if needed.
2. Require exact FYG8 kernel release and stream-verify the pinned
   `sec_log_buf.ko` size and SHA256.
3. Call `finit_module` once for that module, then require exactly one anchored
   `sec_log_buf` line in `/proc/modules` with fifth field `Live`.
4. Require the exact platform-driver bind symlink and both `/proc/ap_klog` and
   `/proc/last_kmsg`.
5. Read `/proc/ap_klog` to true EOF with a one-byte overflow probe; require a
   current-run negative baseline.
6. Write one exact PRECHECK frame, re-read and require counts `1/0/raw1`.
7. Write one exact FINAL frame, re-read and require counts `1/1/raw2` with
   PRECHECK before FINAL.
8. Park forever. Every failure also parks after one run-bound diagnostic when
   `/dev/kmsg` is available.

The runtime has no USB/configfs setup, sysfs write, sec_debug, sysrq, watchdog,
panic, block-device access, persistent mount, Android handoff, or transition.
Static ELF inspection found only the expected raw syscalls and no interpreter,
undefined symbol, `exit_group`, reboot, or clone path.

## Validation

- SHA256 known-vector selftest under `qemu-aarch64`: PASS
- Failure renderer exact full-string selftest under `qemu-aarch64`: PASS
- 64-byte failure-buffer fail-closed selftest: PASS
- No-change MagiskBoot unpack/repack equals the base boot byte-for-byte: PASS
- Patched boot preserves the kernel and extracts the exact built `/init`: PASS
- Independent second build is byte-identical for generated header, expected
  markers, init, ramdisk, kernel, boot image, LZ4, AP tar, and AP.tar.md5: PASS
- V3426-V3429 focused tests: 56/56 PASS

## Review Status

Persistent Claude Opus session `10a19d6c-d0ef-4659-af34-dfd6472c7eb6`
previously returned architecture GO and then implementation NO-GO for one HIGH
finding: a 64-byte failure buffer truncated the current raw run token, so a
post-FINAL self-gate failure could fail to poison a false positive.

That finding is closed in the current artifact: failure rendering uses a
128-byte buffer, returns zero when the complete diagnostic cannot fit, and its
QEMU selftest requires the exact complete failure line, exactly one full raw run
token, and rejection with a 64-byte buffer. A same-session Opus delta re-review
was attempted after the fix but the external CLI returned HTTP 429 with a
session-limit reset at 00:20 KST. Therefore this report does not claim a final
Opus GO; the current PASS is based on the completed implementation, independent
local source/ELF audit, deterministic rebuild, and tests above.

## Next Gate

Before any live run, add a fresh narrow SHA-pinned one-shot `AGENTS.md`
exception and a dedicated helper that verifies normal Android identity, this
exact candidate, both pinned boot-only rollback APs, one target transport, and
canonical timeline/first-rollback classification. Operator approval must be
explicit after those pins exist. Absence of the exact pair remains
`NO_PROOF/STOP`; it must not be reported as proof that PID1 did not execute.
