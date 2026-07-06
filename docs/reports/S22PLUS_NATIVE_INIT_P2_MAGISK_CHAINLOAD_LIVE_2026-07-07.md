# S22+ Native-Init P2 Magisk Chainload Live Attempt

Date: 2026-07-07 KST

Target:
- Samsung Galaxy S22+ `SM-S906N` / `g0q`
- Build: `S906NKSS7FYG8`

Scope:
- First live boot-only flash of the P1 Magisk-chainload native-init wrapper.
- Boot partition only.
- No vbmeta, recovery, vendor_boot, modem, EFS, bootloader, RPMB, or other
  forbidden partition write.

Private run:

```text
workspace/private/runs/s22plus_p2_magisk_chainload_live_20260706T153319Z
```

## Gate State

Git HEAD at preflight:

```text
cb778812 Authorize S22+ P2 boot-only first-light gate
```

Preflight confirmed:

```text
candidate AP.tar.md5:
4790b8a82e38081ed20e50d9bbbeee29f3821cfbf7b52e2d51da8f17f028ee40

candidate padded boot.img:
da9e2f5f71a396f40824493dd8acb9f7404623df075c21fb47f5ecee6f4c2645

candidate Odin payload:
boot.img.lz4 only

stock boot-only rollback AP.tar.md5:
1ee92a86f30e4acb12509272630e1bef5215d1a12686ac69a3b399b43740535e

full stock firmware zip:
f831e5fb8abe1c7a9d8c38fe9c033a3fce7e77651776383641c385c2bb85a2c8
```

Before flash, Android was booted, USB debugging was available, Magisk root was
working, verified boot state was `orange`, flash lock was `0`, warranty bit was
`1`, and package counts were stable at 116 enabled user-0 packages and 0 disabled
user-0 packages.

## Live Action

The device was rebooted into download mode from Android, then flashed with the
exact SHA-pinned P1 candidate through Odin4.

Odin4 candidate flash result:

```text
Reboot into normal mode
Check file : workspace/private/outputs/s22plus_native_init/magisk_chainload_v0_1/odin4/AP.tar.md5
Setup Connection
initializeConnection
Receive PIT Info
success getpit
Upload Binaries
boot.img.lz4
(31%)
(62%)
(93%)
(100%)
Close Connection
odin_exit=0
```

Interpretation: Odin accepted the package and transferred the boot-only payload.

## Post-Flash Observation

Android ADB did not return during the bounded boot poll after the flash. The
poll repeatedly observed:

```text
List of devices attached

adb: no devices/emulators found
```

After the poll window elapsed, the host still observed:

```text
adb devices -l:
List of devices attached

odin4 -l:
<no device listed>
```

USB enumeration also did not show a Samsung device at the time this report was
written.

## Recovery/TWRP Observation

After the initial no-ADB/no-Odin window, the operator entered TWRP recovery.
TWRP ADB was visible to the host as recovery mode:

```text
product:twrp_g0q model:SM_S906E device:g0q
```

TWRP reported:

```text
ro.boot.bootloader: S906NKSS7FYG8
ro.boot.verifiedbootstate: orange
ro.twrp.version: 3.7.0_12-1_afaneh92
```

Read-only partition hashes from TWRP showed the failed P1 boot candidate was
still installed on `boot`, while the other observed boot-surface partitions were
unchanged:

```text
boot:
da9e2f5f71a396f40824493dd8acb9f7404623df075c21fb47f5ecee6f4c2645

recovery:
153373cd6c1efda2a9b57f91fac761ff92d515ae604cd3d22f97877759e51f18

vendor_boot:
096e433e049fb088cd956e083d5a1039b33cdf0ca907e713bba7feaaf1b080b7

vbmeta:
79edc1de4bf12853fc0cf9438efdd64f04e48241cab77137826fe1e1cc6f0b0e
```

No `S22_NATIVE_INIT_MAGISK_CHAINLOAD` proof marker was found in the bounded
recovery-side evidence capture. The clearest current interpretation is that the
Magisk-chainload boot candidate did not hand off to rooted Android; the failure
is confined to the boot candidate path, not recovery/vendor_boot/vbmeta.

## Rollback Status

Automatic rollback was initially blocked because the host did not see Android
ADB or Odin/download-mode USB transport. Once TWRP ADB became available, the
device was commanded from TWRP to download mode:

```text
adb reboot download
```

The pinned stock boot-only rollback AP used for recovery was:

```text
workspace/private/outputs/s22plus_native_init/odin4_stock_rollback_short/AP.tar.md5
```

Expected rollback AP SHA256:

```text
1ee92a86f30e4acb12509272630e1bef5215d1a12686ac69a3b399b43740535e
```

A guarded rollback helper was added after the failed first-light attempt:

```text
workspace/public/src/scripts/revalidation/s22plus_p2_stock_boot_rollback_guard.py
```

Validation:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/s22plus_p2_stock_boot_rollback_guard.py

python3 workspace/public/src/scripts/revalidation/s22plus_p2_stock_boot_rollback_guard.py --odin /usr/bin/odin4
```

Dry-run result:

```text
dry-run ok: package verified; no Odin download device detected
```

The helper verified the rollback AP SHA256 and confirmed the AP tar contains
exactly one member, `boot.img.lz4`. It did not call live Odin because no
download-mode device was visible.

After TWRP recovery became available, the guarded live rollback command was run:

```text
python3 workspace/public/src/scripts/revalidation/s22plus_p2_stock_boot_rollback_guard.py \
  --odin /usr/bin/odin4 \
  --wait-sec 120 \
  --live \
  --ack S22PLUS-P2-STOCK-BOOT-ROLLBACK
```

Result:

```text
rollback odin rc=0; android_boot_completed=1
```

Post-rollback Android validation:

```text
sys.boot_completed: 1
ro.product.model: SM-S906N
ro.product.device: g0q
ro.product.name: g0qksx
ro.boot.bootloader: S906NKSS7FYG8
ro.boot.verifiedbootstate: orange
persist.sys.safemode: <empty>
user-0 package count: 116
disabled user-0 package count: 0
su: inaccessible or not found
```

Interpretation: the device is back to stock-boot Android, but Magisk root is no
longer present because the authorized rollback AP is stock boot-only.

## Result

FAIL / ROLLED BACK: P2 first-light was not proven, and the device was recovered
to booting Android via the pinned stock boot-only rollback AP.

The S22+ experimental base is therefore not complete yet. P0 recon, P1 host
candidate construction, and P2 SHA-pinned flash authorization are in place, and
the candidate was transferred successfully, but the required post-flash evidence
was missing:

- no rooted Android return
- no readable `S22_NATIVE_INIT_MAGISK_CHAINLOAD` marker
- no successful Magisk handoff from the P1 boot candidate

Stop condition for this exact P2 candidate: do not retry it. The next S22+
native-init unit should first re-establish the Magisk root baseline if rooted
Android observation is still desired, then redesign P1 rather than looping on
the same boot image.
