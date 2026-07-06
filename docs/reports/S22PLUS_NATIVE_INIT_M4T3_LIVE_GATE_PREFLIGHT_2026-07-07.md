# S22+ Native-Init M4T3 Live Gate Preflight - 2026-07-07

## Scope

Prepared and dry-ran the guarded M4T3 raw-reboot native-init live gate. No live
flash, reboot, Odin transfer to the phone, partition write, recovery action, or
connected-device mutation was performed.

M4T3 is the next discriminator after M4T2's positive raw-PID1 park proof. Its
future live signal is three-way:

- self-download after candidate flash: raw `reboot(..., "download")` syscall
  works from custom PID1;
- no transport but stable park: raw PID1 survived and the syscall returned or
  was rejected;
- fast bootloop: raw reboot syscall path or immediate PID1 action is unstable.

## Added Gate

Helper:

```text
workspace/public/src/scripts/revalidation/s22plus_m4t3_raw_reboot_live_gate.py
```

Updated `AGENTS.md` with the SHA-pinned M4T3 boot-only live exception and
matching Odin-path exception.

Live ack token:

```text
S22PLUS-M4T3-RAW-REBOOT-LIVE-GATE
```

Manual rollback-only ack token:

```text
S22PLUS-M4T3-ROLLBACK-FROM-DOWNLOAD
```

## Dry-Run

Command:

```bash
python3 workspace/public/src/scripts/revalidation/s22plus_m4t3_raw_reboot_live_gate.py \
  --run-dir workspace/private/runs/s22plus_m4t3_raw_reboot_live_gate_dryrun_20260707T0540Z
```

Result:

```text
dry-run ok: M4T3 candidate, rollback APs, AGENTS exception, and Android preflight verified
```

Run log:

```text
workspace/private/runs/s22plus_m4t3_raw_reboot_live_gate_dryrun_20260707T0540Z/s22plus_m4t3_raw_reboot_live_gate.txt
```

## Verified Inputs

AGENTS exception:

```text
agents_exception_missing=[]
```

Candidate:

```text
AP.tar.md5  f0a26bb95a091070713f8d736419cbe60974195bb59509cb1fd7cc28a0b1a907
boot.img    d5e0371c6cb68af8990ce3ac4701ad4e0e487dbe54f4702dae29e21d86f4b92a
base boot   2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
kernel      bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff
raw /init   e975a973395fd1bfe2fee0dccb9d47400e6746d62b508cd139b49c551b9aa67c
```

The candidate AP contains exactly:

```text
boot.img.lz4
```

Manifest safety checked by the helper:

```text
construction=magiskboot unpack/repack; replace only ramdisk /init
mkbootimg_from_scratch=false
first_candidate_action=raw-reboot-download-syscall
libc=false
intended_syscalls=["reboot"]
intended_syscall_count=1
reboot_request=download
marker_write=false
module_insertions=false
configfs_runtime_gadget=false
watchdog=not-touched
on_reboot_syscall_return=infinite-park
```

Rollback APs:

```text
Magisk boot-only rollback AP  d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56
stock boot-only fallback AP   1ee92a86f30e4acb12509272630e1bef5215d1a12686ac69a3b399b43740535e
```

Each rollback AP contains exactly:

```text
boot.img.lz4
```

Current Android preflight:

```text
model=SM-S906N
device=g0q
bootloader=S906NKSS7FYG8
incremental=S906NKSS7FYG8
verifiedbootstate=orange
boot_recovery=0
boot_completed=1
su_id=uid=0(root) gid=0(root) groups=0(root) context=u:r:magisk:s0
```

Host snapshot showed no Odin/download-mode device during dry-run:

```text
label=dryrun_current
adb_devices_l rc=0
odin_l rc=0 bytes=0
```

## Live Command

Do not run unattended. If the operator chooses to run the attended live gate:

```bash
python3 workspace/public/src/scripts/revalidation/s22plus_m4t3_raw_reboot_live_gate.py \
  --live \
  --ack S22PLUS-M4T3-RAW-REBOOT-LIVE-GATE
```

If M4T3 parks and no self-download appears, enter download mode manually and
rollback through:

```bash
python3 workspace/public/src/scripts/revalidation/s22plus_m4t3_raw_reboot_live_gate.py \
  --rollback-from-download \
  --ack S22PLUS-M4T3-ROLLBACK-FROM-DOWNLOAD
```

## Status

M4T3 is live-gate-ready but not live-run. The next step is an attended operator
decision: run the M4T3 live command above, or stop here and inspect the gate
diff first.
