# S22+ Native-Init M4T1 Live Gate Preflight - 2026-07-07

## Scope

Prepared and dry-ran the guarded M4T1 in-place MagiskBoot native-init live
gate. No live flash, reboot, Odin transfer, partition write, recovery action,
or rollback action was performed.

## Public Changes

Added the guarded helper:

```text
workspace/public/src/scripts/revalidation/s22plus_m4t1_inplace_live_gate.py
```

Added a SHA-pinned `AGENTS.md` M4T1 boot-only exception and matching Odin path
exception for the exact candidate and rollback APs below.

## Candidate

M4T1 is the M4T0 instant-download behavior rebuilt through the in-place
MagiskBoot path:

- base is the known-booting Magisk boot;
- no-change `magiskboot unpack/repack` is byte-identical;
- only ramdisk entry `/init` is replaced;
- candidate first action is `reboot(..., "download")`;
- no marker is written before that reboot syscall.

Exact candidate hashes:

```text
AP.tar.md5  9f5b4c48b95b710f742d5ea8c7f16ef4802cf27e78469381073d460361d0451c
boot.img    9ce597e4ba920f1331937dbe4736f923728ff5502b02c02dea8357b3a9d5b9d1
base boot   2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
kernel      bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff
```

The AP contains exactly:

```text
boot.img.lz4
```

No recovery, vendor_boot, vbmeta, vbmeta_system, dtbo, BL, CP, CSC, super,
persist, userdata, EFS, RPMB, keymaster, modem, or any other partition payload
is present.

## Dry-Run

Command:

```bash
python3 workspace/public/src/scripts/revalidation/s22plus_m4t1_inplace_live_gate.py \
  --run-dir workspace/private/runs/s22plus_m4t1_inplace_live_gate_dryrun_20260707T0512Z
```

Result:

```text
dry-run ok: M4T1 candidate, rollback APs, AGENTS exception, and Android preflight verified
```

Dry-run gates:

```text
agents_exception_missing=[]
m4t1_candidate_sha256=9f5b4c48b95b710f742d5ea8c7f16ef4802cf27e78469381073d460361d0451c
m4t1_candidate_members=['boot.img.lz4']
magisk_boot_rollback_sha256=d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56
magisk_boot_rollback_members=['boot.img.lz4']
stock_boot_fallback_sha256=1ee92a86f30e4acb12509272630e1bef5215d1a12686ac69a3b399b43740535e
stock_boot_fallback_members=['boot.img.lz4']
```

Manifest safety gates:

```text
construction=magiskboot unpack/repack; replace only ramdisk /init
mkbootimg_from_scratch=false
first_candidate_action=reboot-download
marker_before_reboot=false
module_insertions=false
configfs_runtime_gadget=false
watchdog=not-touched
nochange_repack_byte_identical=true
replaced_entry=init
```

Current Android preflight, redacted:

```text
model=SM-S906N
device=g0q
bootloader=S906NKSS7FYG8
incremental=S906NKSS7FYG8
vbstate=orange
boot_recovery=0
boot_completed=1
su_id=uid=0(root) gid=0(root) groups=0(root) context=u:r:magisk:s0
```

## Live Boundary

The live command is now gated but was not executed:

```bash
python3 workspace/public/src/scripts/revalidation/s22plus_m4t1_inplace_live_gate.py \
  --live \
  --ack S22PLUS-M4T1-INPLACE-LIVE-GATE
```

Expected discriminator:

- fast self-download after candidate flash: boot image is accepted and custom
  `/init` ran;
- no self-download / manual recovery required: the in-place construction did
  not clear the acceptance or early handoff fault, so the next evidence path
  should be UART or deeper boot-chain inspection, not more marker/dwell logic.

Rollback remains mandatory after any successful self-download proof, using the
pinned Magisk boot-only AP first and the pinned stock boot-only AP as fallback.
