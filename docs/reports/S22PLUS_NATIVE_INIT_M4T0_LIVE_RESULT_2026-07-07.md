# S22+ Native-Init M4T0 Live Result - 2026-07-07

## Scope

One attended S22+ M4 TEST 0 instant-download live gate using the SHA-pinned
boot-only helper path. The candidate touched only the boot partition through
Odin AP flashing. No recovery, vendor_boot, vbmeta, dtbo, BL, CP, CSC, userdata,
EFS, RPMB, keymaster, modem, raw host `dd`, fastboot, Magisk module, format
data, sysfs/configfs mutation, or A90 action was performed.

The run required manual recovery because the candidate did not self-enter
download mode.

## Artifacts

Candidate:

```text
AP.tar.md5 SHA256:
ba445b131fddd79887a4ace357a77a42b1f49367eaeea156a3cfebfd883b1904

padded boot.img SHA256:
4617a8804b93435cd0b6a5307862b4d5f55ca7e25befa0c19b2e7619284979e9

tar members:
boot.img.lz4
```

Rollback:

```text
Magisk boot-only rollback AP SHA256:
d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56

post-rollback live boot partition SHA256:
2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
```

Private evidence:

```text
workspace/private/runs/s22plus_m4t0_instant_download_live_gate_20260706T194910Z/
workspace/private/runs/s22plus_retained_evidence_probe_20260706T195333Z/
```

## Command

```text
python3 workspace/public/src/scripts/revalidation/s22plus_m4t0_instant_download_live_gate.py \
  --serial <redacted> \
  --live \
  --ack S22PLUS-M4T0-INSTANT-DOWNLOAD-LIVE-GATE
```

## Timeline

Preflight passed:

```text
target=SM-S906N/g0q/S906NKSS7FYG8
agents_exception_missing=[]
candidate_sha256=ba445b131fddd79887a4ace357a77a42b1f49367eaeea156a3cfebfd883b1904
candidate_members=['boot.img.lz4']
rollback_magisk_sha256=d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56
android_preflight: boot_completed=1, vbstate=orange, Magisk uid=0
```

Live sequence:

```text
adb_reboot_download_rc=0
candidate Odin wait: one download-mode device appeared
candidate Odin flash rc=0
candidate flash transferred boot.img.lz4 to 100%
original Odin device disconnected after candidate transfer
M4T0 self-download wait: no Odin device and no ADB device appeared
m4t0_self_download_seen=0
helper exit rc=4
```

The operator then put the device into download mode manually. Host-side rollback
used only the pinned Magisk boot-only AP:

```text
manual download-mode recovery: Odin device appeared
Magisk boot-only rollback Odin rc=0
rollback transferred boot.img.lz4 to 100%
```

Post-rollback Android baseline:

```text
boot_completed=1
model=SM-S906N
device=g0q
bootloader=S906NKSS7FYG8
incremental=S906NKSS7FYG8
verifiedbootstate=orange
boot_recovery=0
Magisk root=uid=0(root)
boot SHA256=2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
```

Retained evidence after rollback:

```text
/sys/fs/pstore: empty
/proc/last_kmsg bytes: 2097136
S22_NATIVE_INIT_INSTANT_DOWNLOAD_M4T0: false
S22_NATIVE_INIT_FAST_DWELL_M4A: false
S22_NATIVE_INIT_MARKER_ONLY_M32: false
S22_NATIVE_INIT_OBSERVABLE_M3: false
S22_NATIVE_INIT_DIRECT_P3: false
S22_NATIVE_INIT_MAGISK_CHAINLOAD: false
```

## Interpretation

M4T0 removed marker writes, dwell, watchdog handling, USB/NCM, module insertion,
configfs, Android handoff, and Magisk handoff from the candidate. Its first
candidate action was the `download` reboot syscall. The live result is therefore
a useful negative floor result:

- the boot-only candidate Odin transfer succeeded;
- the original Odin device disconnected, so the phone left the original download
  session;
- the candidate did not self-enter download mode within the bounded window;
- no retained `S22_NATIVE_INIT` marker survived;
- manual download-mode recovery plus pinned Magisk boot rollback restored the
  rooted Android baseline.

This does not prove pstore silence means `/init` never ran. It does prove that
M4T0 did not successfully execute the intended first-action download path. The
next unit should not add more marker/dwell/watchdog logic on this branch.

## Next

Proceed to the already defined next rung:

1. minimal-delta boot comparison, focused on boot-image/ramdisk/init execution
   mechanics rather than native feature bring-up; or
2. UART once hardware is available, because it is the decisive real-time channel
   for this bootloop class.

No further S22+ boot candidate is authorized by this result. A new live unit
requires a fresh SHA-pinned `AGENTS.md` exception, guarded helper, dry-run, and
rollback plan.
